#!/usr/bin/env python3
"""Рейтинг поставщиков 0–100 по 5 критериям и вердикт ОСТАВИТЬ / РАЗОБРАТЬ / ЗАМЕНИТЬ.

Вход: CSV/XLSX, одна строка на поставщика за период (квартал/год).
Колонки: Поставщик; Категория; Критичность; Сумма; Поставок всего; Поставок в срок;
         Партий с несоответствием; Претензий; Отклонение цены, %; Отсрочка, дн; Риск контрагента; Договор до
  Отклонение цены, % — цена поставщика к рыночной/лучшей альтернативе (+ дороже, − дешевле).
  Риск контрагента — по заключению СБ: низкий / средний / высокий.

Веса по умолчанию: срок 30, качество 30, цена 20, оплата 10, надёжность 10.
Изменить: --vesa 25,35,20,10,10

Запуск:  python3 reiting_postavschikov.py --input поставщики.csv [--out отчет.md] [--na-datu 2026-10-01]
         python3 reiting_postavschikov.py --sample
"""
import argparse
import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tablio import read_table, get, num, to_date, fmt, md_table, write_sample, emit  # noqa: E402

SAMPLE = """Поставщик;Категория;Критичность;Сумма;Поставок всего;Поставок в срок;Партий с несоответствием;Претензий;Отклонение цены, %;Отсрочка, дн;Риск контрагента;Договор до
ООО Ломсервис;Металлолом;1;412000000;380;361;19;4;-1;15;низкий;31.12.2026
ООО ВторМет;Металлолом;1;298000000;290;232;41;9;-3;30;средний;30.11.2026
ООО Электродный завод;Графитированные электроды;1;118000000;24;23;0;0;6;45;низкий;31.03.2027
ООО Огнеупор-Трейд;Огнеупоры;1;52000000;18;12;2;2;2;30;низкий;31.12.2026
ООО Валки;Валки прокатные;1;39000000;6;3;1;1;12;0;высокий;31.10.2026
ООО Подшипник-СПб;Подшипники;2;6200000;40;38;1;0;-4;30;низкий;30.06.2027
ИП Смирнов;Подшипники;2;900000;8;5;2;1;-8;0;высокий;
ООО Спецодежда;СИЗ;3;4100000;12;12;0;0;0;60;низкий;31.12.2026
"""

RISK = {"низкий": 100, "средний": 60, "высокий": 10}


def lin(x, x0, y0, x1, y1):
    """Линейная шкала с ограничением."""
    if x is None:
        return None
    if x0 == x1:
        return y0
    t = (x - x0) / (x1 - x0)
    t = max(0.0, min(1.0, t))
    return y0 + (y1 - y0) * t


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input")
    ap.add_argument("--out")
    ap.add_argument("--sample", action="store_true")
    ap.add_argument("--vesa", default="30,30,20,10,10", help="веса: срок,качество,цена,оплата,надёжность")
    ap.add_argument("--na-datu", help="дата анализа (по умолчанию сегодня)")
    a = ap.parse_args()
    path = write_sample(SAMPLE, "postavschiki_sample.csv") if a.sample else a.input
    if not path:
        ap.error("укажите --input или --sample")
    w = [float(x) for x in a.vesa.split(",")]
    if len(w) != 5:
        ap.error("--vesa: нужно 5 чисел")
    today = to_date(a.na_datu) if a.na_datu else date.today()
    rows = read_table(path)

    res = []
    for r in rows:
        name = str(get(r, "поставщик", "контрагент", default="—")).strip()
        total = num(get(r, "поставок всего"), 0)
        ontime = num(get(r, "поставок в срок"))
        nc = num(get(r, "партий с несоответствием"), 0)
        s_srok = lin(ontime / total if total and ontime is not None else None, 0.70, 0, 0.98, 100)
        s_kach = lin(nc / total if total else None, 0.10, 0, 0.0, 100)
        s_cena = lin(num(get(r, "отклонение цены, %", "отклонение цены")), 10, 0, -5, 100)
        s_opl = lin(num(get(r, "отсрочка, дн", "отсрочка")), 0, 20, 60, 100)
        rk = str(get(r, "риск контрагента", default="")).strip().lower()
        s_nad = RISK.get(rk)
        parts = [s_srok, s_kach, s_cena, s_opl, s_nad]
        ws = sum(wi for wi, p in zip(w, parts) if p is not None)
        score = sum(wi * p for wi, p in zip(w, parts) if p is not None) / ws if ws else None
        crit = int(num(get(r, "критичность"), 3) or 3)
        flags = []
        if crit == 1 and rk == "высокий":
            flags.append("критичный + высокий риск СБ")
        if s_kach is not None and s_kach < 50:
            flags.append("качество")
        if s_srok is not None and s_srok < 50:
            flags.append("сроки")
        dend = to_date(get(r, "договор до"))
        if dend and (dend - today).days <= 90:
            flags.append(f"договор истекает {dend.strftime('%d.%m.%Y')}")
        if not dend:
            flags.append("нет срока договора")
        verdict = "—" if score is None else ("ОСТАВИТЬ" if score >= 75 else ("РАЗОБРАТЬ" if score >= 50 else "ЗАМЕНИТЬ"))
        res.append(dict(name=name, cat=get(r, "категория", default="—"), crit=crit, score=score, parts=parts,
                        verdict=verdict, flags=flags, claims=int(num(get(r, "претензий"), 0)),
                        summa=num(get(r, "сумма"), 0)))

    res.sort(key=lambda x: (x["score"] is None, -(x["score"] or 0)))
    f = lambda v: "—" if v is None else fmt(v)  # noqa: E731
    out = ["# Рейтинг поставщиков", "",
           f"Веса: своевременность {w[0]:g}, качество {w[1]:g}, цена {w[2]:g}, условия оплаты {w[3]:g}, надёжность {w[4]:g}. "
           f"Дата анализа: {today.strftime('%d.%m.%Y')}.", ""]
    out.append(md_table(["Поставщик", "Категория", "Крит.", "млн руб.", "Срок", "Качество", "Цена", "Оплата", "Надёжн.",
                         "**Итог**", "Вердикт", "Претензий", "Флаги"],
                        [[x["name"], x["cat"], x["crit"], fmt(x["summa"] / 1e6, 1)] + [f(p) for p in x["parts"]]
                         + [f"**{f(x['score'])}**", x["verdict"], x["claims"], "; ".join(x["flags"])] for x in res]))
    out.append("")
    for v, title in (("ЗАМЕНИТЬ", "Искать альтернативу сейчас, не продлевать автоматически"),
                     ("РАЗОБРАТЬ", "Встреча с поставщиком, план улучшений с контрольными сроками")):
        lst = [x["name"] for x in res if x["verdict"] == v]
        if lst:
            out.append(f"**{v}** ({title}): " + ", ".join(lst))
    crit_risk = [x["name"] for x in res if "критичный + высокий риск СБ" in x["flags"]]
    if crit_risk:
        out.append("")
        out.append("**Внимание:** критичные поставщики с высоким риском по заключению СБ: " + ", ".join(crit_risk)
                   + ". Нужен резервный поставщик и проверка СБ до продления договора.")
    out.append("")
    out.append("_Шкалы: срок 98 % в срок = 100, 70 % = 0; качество 0 % партий с несоответствием = 100, 10 % = 0; "
               "цена −5 % к рынку = 100, +10 % = 0; отсрочка 60 дн = 100, 0 дн = 20; риск СБ низкий/средний/высокий = 100/60/10. "
               "Порог: ≥ 75 ОСТАВИТЬ, 50–74 РАЗОБРАТЬ, < 50 ЗАМЕНИТЬ._")
    emit("\n".join(out), a.out)


if __name__ == "__main__":
    main()
