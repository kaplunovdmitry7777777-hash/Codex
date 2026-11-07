#!/usr/bin/env python3
"""Анализ цикла закупки по категориям: где заявки «стоят» (теория ограничений).

Вход: CSV/XLSX по заявкам/заказам поставщику.
Колонки: № заявки; Категория; Дата заявки; Дата согласования; Дата заказа; Дата поставки; Дата оплаты; Согласующих
Даты в формате ДД.ММ.ГГГГ или ГГГГ-ММ-ДД. Пустые даты допускаются.

Запуск:  python3 cikl_zakupok.py --input заявки.csv [--out отчет.md]
         python3 cikl_zakupok.py --sample
"""
import argparse
import os
import statistics
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tablio import read_table, get, num, to_date, fmt, md_table, percentile, write_sample, emit  # noqa: E402

SAMPLE = """№ заявки;Категория;Дата заявки;Дата согласования;Дата заказа;Дата поставки;Дата оплаты;Согласующих
1;Подшипники;01.07.2026;03.07.2026;08.07.2026;22.07.2026;15.08.2026;3
2;Подшипники;05.07.2026;06.07.2026;10.07.2026;30.07.2026;20.08.2026;3
3;Подшипники;10.07.2026;20.07.2026;28.07.2026;15.08.2026;10.09.2026;4
4;Валки прокатные;01.06.2026;25.06.2026;20.07.2026;15.09.2026;01.10.2026;6
5;Валки прокатные;15.06.2026;20.07.2026;10.08.2026;01.10.2026;;6
6;СИЗ;01.07.2026;02.07.2026;04.07.2026;10.07.2026;30.07.2026;2
7;СИЗ;12.07.2026;13.07.2026;15.07.2026;20.07.2026;10.08.2026;2
8;Огнеупоры;03.07.2026;10.07.2026;17.07.2026;10.08.2026;01.09.2026;4
9;Огнеупоры;20.07.2026;28.07.2026;05.08.2026;30.08.2026;20.09.2026;4
10;Запчасти импортные;01.05.2026;10.06.2026;01.07.2026;20.09.2026;;7
11;Запчасти импортные;15.05.2026;25.06.2026;20.07.2026;;;7
"""


def days(a, b):
    return (b - a).days if a and b else None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input")
    ap.add_argument("--out")
    ap.add_argument("--sample", action="store_true")
    a = ap.parse_args()
    path = write_sample(SAMPLE, "cikl_zakupok_sample.csv") if a.sample else a.input
    if not path:
        ap.error("укажите --input или --sample")
    rows = read_table(path)

    by = defaultdict(lambda: {"sogl": [], "zakaz": [], "postavka": [], "total": [], "hops": [], "n": 0, "open": 0})
    all_total = []
    for r in rows:
        c = str(get(r, "категория", default="Без категории")).strip()
        d0 = to_date(get(r, "дата заявки"))
        d1 = to_date(get(r, "дата согласования"))
        d2 = to_date(get(r, "дата заказа", "дата договора"))
        d3 = to_date(get(r, "дата поставки", "дата поступления"))
        b = by[c]
        b["n"] += 1
        for key, val in (("sogl", days(d0, d1)), ("zakaz", days(d1, d2)), ("postavka", days(d2, d3)), ("total", days(d0, d3))):
            if val is not None:
                b[key].append(val)
        if days(d0, d3) is not None:
            all_total.append(days(d0, d3))
        else:
            b["open"] += 1
        h = num(get(r, "согласующих", "число согласующих"))
        if h is not None:
            b["hops"].append(h)

    med_all = statistics.median(all_total) if all_total else None
    out = ["# Цикл закупки по категориям", ""]
    out.append(f"Заявок: {sum(b['n'] for b in by.values())}. Медиана полного цикла «заявка → поставка» по всем категориям: "
               f"**{fmt(med_all)} дн.**")
    out.append("")
    t = []
    bott = []
    for c, b in sorted(by.items(), key=lambda x: -(statistics.median(x[1]["total"]) if x[1]["total"] else 0)):
        m = lambda xs: fmt(statistics.median(xs)) if xs else "—"  # noqa: E731
        mt = statistics.median(b["total"]) if b["total"] else None
        flag = ""
        if mt is not None and med_all and mt > 2 * med_all:
            flag = "УЗКОЕ МЕСТО"
            stages = {"согласование": b["sogl"], "размещение заказа": b["zakaz"], "поставка": b["postavka"]}
            worst = max(stages.items(), key=lambda x: statistics.median(x[1]) if x[1] else -1)[0]
            bott.append(f"- **{c}**: медиана {fmt(mt)} дн. (> 2× общей), основная задержка — этап «{worst}».")
        t.append([c, b["n"], m(b["sogl"]), m(b["zakaz"]), m(b["postavka"]), m(b["total"]),
                  fmt(percentile(b["total"], 0.9)), m(b["hops"]), b["open"], flag])
    out.append(md_table(["Категория", "Заявок", "Согласов., дн", "До заказа, дн", "Поставка, дн", "Итого медиана",
                         "Итого P90", "Согласующих", "Не закрыто", "Флаг"], t))
    out.append("")
    out.append("## Узкие места")
    out.extend(bott or ["Категорий с циклом > 2× общей медианы нет."])
    out.append("")
    out.append("_P90 — срок, в который укладываются 90 % заявок. Сравнивайте медиану и P90: большой разрыв означает "
               "нестабильный процесс, а не просто медленный._")
    emit("\n".join(out), a.out)


if __name__ == "__main__":
    main()
