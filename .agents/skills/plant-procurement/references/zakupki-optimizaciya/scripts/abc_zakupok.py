#!/usr/bin/env python3
"""ABC-анализ закупок: концентрация затрат по категориям и поставщикам,
рост к прошлому периоду, монозависимость, «хвост» мелких поставщиков.

Вход: CSV/XLSX со строками закупок (выгрузка 1С «Анализ закупок» / оборотка по 60 счёту).
Колонки: Поставщик; Категория; Номенклатура; Сумма; Сумма пред. период; Единственный источник; Критичность
  Сумма — руб. без НДС за анализируемый период; Критичность: 1 — остановка производства, 2 — есть обход, 3 — некритично.

Запуск:  python3 abc_zakupok.py --input закупки.csv [--out отчет.md]
         python3 abc_zakupok.py --sample
"""
import argparse
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tablio import read_table, get, num, fmt, pct, md_table, write_sample, emit  # noqa: E402

SAMPLE = """Поставщик;Категория;Номенклатура;Сумма;Сумма пред. период;Единственный источник;Критичность
ООО Ломсервис;Металлолом;Лом 3А;412000000;350000000;нет;1
ООО ВторМет;Металлолом;Лом 3А;298000000;310000000;нет;1
АО Энергосбыт;Электроэнергия;Электроэнергия;365000000;330000000;да;1
ООО Электродный завод;Графитированные электроды;Электрод 600 мм;118000000;84000000;да;1
ООО ФерроСплав;Ферросплавы;ФС65;74000000;69000000;нет;1
ООО Огнеупор-Трейд;Огнеупоры;Кирпич периклазоуглеродистый;52000000;47000000;нет;1
ООО Валки;Валки прокатные;Валок чугунный;39000000;22000000;да;1
ООО Подшипник-СПб;Подшипники;Подшипник 3003;6200000;5100000;нет;2
ООО Техснаб;Подшипники;Подшипник 3626;2100000;1900000;нет;2
ИП Смирнов;Подшипники;Подшипник 22320;900000;0;нет;2
ООО РТИ-Сервис;РТИ и уплотнения;Манжета;1800000;1600000;нет;3
ООО Спецодежда;СИЗ;Костюм сварщика;4100000;3900000;нет;3
ООО СИЗ-Профи;СИЗ;Перчатки;1200000;1300000;нет;3
ИП Козлов;СИЗ;Каски;350000;0;нет;3
ООО Канцлер;Канцтовары;Бумага;400000;380000;нет;3
ООО Газпром межрегионгаз;Природный газ;Газ;88000000;81000000;да;1
ООО Кислород;Технические газы;Кислород;27000000;24000000;да;1
"""


def abc_class(cum_share):
    return "A" if cum_share <= 0.80 else ("B" if cum_share <= 0.95 else "C")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input")
    ap.add_argument("--out")
    ap.add_argument("--sample", action="store_true", help="запуск на встроенном примере")
    a = ap.parse_args()
    path = write_sample(SAMPLE, "abc_zakupok_sample.csv") if a.sample else a.input
    if not path:
        ap.error("укажите --input или --sample")
    rows = read_table(path)

    cat = defaultdict(lambda: {"s": 0.0, "p": 0.0, "sup": defaultdict(float), "crit": 3, "single": False})
    sup = defaultdict(float)
    total = prev_total = 0.0
    for r in rows:
        s = num(get(r, "сумма", "сумма, руб", "сумма без ндс"), 0.0)
        p = num(get(r, "сумма пред. период", "сумма пред период", "прошлый период"), 0.0)
        c = str(get(r, "категория", default="Без категории")).strip()
        v = str(get(r, "поставщик", "контрагент", default="—")).strip()
        k = int(num(get(r, "критичность"), 3) or 3)
        single = str(get(r, "единственный источник", default="")).strip().lower() in ("да", "1", "yes", "true")
        cat[c]["s"] += s
        cat[c]["p"] += p
        cat[c]["sup"][v] += s
        cat[c]["crit"] = min(cat[c]["crit"], k)
        cat[c]["single"] = cat[c]["single"] or single
        sup[v] += s
        total += s
        prev_total += p

    out = ["# ABC-анализ закупок", ""]
    out.append(f"Итого закупок: **{fmt(total / 1e6, 1)} млн руб.**"
               + (f", прошлый период {fmt(prev_total / 1e6, 1)} млн руб. ({pct(total / prev_total - 1)})" if prev_total else ""))
    out.append(f"Категорий: {len(cat)}, поставщиков: {len(sup)}.")
    out.append("")

    # ABC по категориям
    cum = 0.0
    trows = []
    counts = defaultdict(int)
    for c, d in sorted(cat.items(), key=lambda x: -x[1]["s"]):
        cum += d["s"]
        cl = abc_class(cum / total if total else 1)
        counts[cl] += 1
        g = (d["s"] / d["p"] - 1) if d["p"] else None
        trows.append([c, cl, fmt(d["s"] / 1e6, 1), pct(d["s"] / total), pct(g) if g is not None else "нов.",
                      len(d["sup"]), d["crit"]])
    out.append("## 1. ABC по категориям")
    out.append(f"A: {counts['A']} кат. (≈80 % затрат), B: {counts['B']}, C: {counts['C']}.")
    out.append("")
    out.append(md_table(["Категория", "ABC", "млн руб.", "Доля", "Δ к пред.", "Поставщ.", "Критичн."], trows))
    out.append("")

    # Рост
    growth = [(c, d["s"] - d["p"], d) for c, d in cat.items() if d["p"]]
    growth.sort(key=lambda x: -x[1])
    if growth:
        out.append("## 2. Драйверы роста затрат (топ-5, абсолютный прирост)")
        out.append(md_table(["Категория", "Прирост, млн руб.", "Рост, %"],
                            [[c, fmt(dlt / 1e6, 1), pct(d["s"] / d["p"] - 1)] for c, dlt, d in growth[:5]]))
        out.append("")

    # Монозависимость
    risks = []
    for c, d in cat.items():
        if not d["s"]:
            continue
        top_v, top_s = max(d["sup"].items(), key=lambda x: x[1])
        share = top_s / d["s"]
        if d["crit"] == 1 and (d["single"] or share >= 0.7):
            risks.append([c, top_v, pct(share), "да" if d["single"] else "нет", fmt(d["s"] / 1e6, 1)])
    out.append("## 3. Монозависимость в критичных категориях (критичность 1, доля поставщика ≥ 70 % или единственный источник)")
    out.append(md_table(["Категория", "Основной поставщик", "Доля", "Единств. источник", "млн руб."], risks)
               if risks else "Не выявлено.")
    out.append("Для каждой строки нужен план на случай срыва поставки на 72 часа (резервный поставщик, страховой запас, аналог).")
    out.append("")

    # Хвост
    cum = 0.0
    tail = []
    for v, s in sorted(sup.items(), key=lambda x: -x[1]):
        cum += s
        if total and cum / total > 0.95:
            tail.append((v, s))
    out.append("## 4. «Хвост» поставщиков (группа C)")
    if tail:
        ts = sum(s for _, s in tail)
        out.append(f"{len(tail)} из {len(sup)} поставщиков ({pct(len(tail) / len(sup), 0)}) дают {pct(ts / total)} затрат.")
    frag = [[c, len(d["sup"]), fmt(d["s"] / 1e6, 2)] for c, d in cat.items() if len(d["sup"]) >= 3 and d["crit"] >= 2]
    if frag:
        out.append("Категории-кандидаты на консолидацию (≥ 3 поставщиков, некритичные):")
        out.append(md_table(["Категория", "Поставщиков", "млн руб."], frag))
    out.append("")
    out.append("_Примечание: ABC считается по сумме без НДС. Критичность и признак единственного источника задаёт пользователь, "
               "скрипт их не выводит из сумм._")
    emit("\n".join(out), a.out)


if __name__ == "__main__":
    main()
