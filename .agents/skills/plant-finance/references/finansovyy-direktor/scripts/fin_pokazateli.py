#!/usr/bin/env python3
"""Финансовые расчёты для металлургического завода.

Режим marzha — маржинальный доход по продуктам (марка/профиль), точка безубыточности, запас прочности.
  Вход CSV/XLSX: Продукт; Объём, т; Цена, руб/т; Переменные затраты, руб/т
  Цена без НДС, франко-завод (без логистики). Переменные: металлошихта, ферросплавы, электроэнергия, электроды,
  огнеупоры, газ, прочие переменные на тонну.
  python3 fin_pokazateli.py marzha --input продукты.csv --postoyannye 450000000 [--out отчет.md]

Режим obkap — оборотный капитал и финансовый цикл.
  python3 fin_pokazateli.py obkap --vyruchka 2400000000 --sebest 2100000000 --dz 520000000 \
      --zapasy 610000000 --kz 380000000 --dney 90 [--celevoy-cikl 45]
  Значения: выручка и себестоимость за период --dney; ДЗ, запасы, КЗ — на конец периода (или средние).

Пример: python3 fin_pokazateli.py marzha --sample ;  python3 fin_pokazateli.py obkap --sample
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tablio import read_table, get, num, fmt, pct, md_table, write_sample, emit  # noqa: E402

SAMPLE = """Продукт;Объём, т;Цена, руб/т;Переменные затраты, руб/т
Арматура А500С 12-16;18000;52000;41500
Арматура А500С 25-40;9000;53500;41800
Уголок 100-160;7000;61000;44800
Швеллер 16-24;5500;63500;45900
Заготовка 150х150 (на сторону);6000;43000;39200
Круг 40Х;2500;78000;52100
"""


def marzha(a):
    path = write_sample(SAMPLE, "marzha_sample.csv") if a.sample else a.input
    if not path:
        sys.exit("укажите --input или --sample")
    fixed = a.postoyannye if a.postoyannye is not None else (450_000_000 if a.sample else None)
    rows = read_table(path)
    items = []
    for r in rows:
        q = num(get(r, "объём, т", "объем, т", "объём", "объем"), 0)
        p = num(get(r, "цена, руб/т", "цена"), 0)
        v = num(get(r, "переменные затраты, руб/т", "переменные затраты"), 0)
        items.append(dict(n=get(r, "продукт", "марка", "профиль", default="—"), q=q, p=p, v=v, md=p - v))
    Q = sum(i["q"] for i in items)
    R = sum(i["q"] * i["p"] for i in items)
    MD = sum(i["q"] * i["md"] for i in items)
    items.sort(key=lambda i: -i["md"])
    out = ["# Маржинальный доход по продуктам", ""]
    out.append(md_table(["Продукт", "Объём, т", "Цена, руб/т", "Перем., руб/т", "МД, руб/т", "МД, %", "МД, млн руб.", "Доля в МД"],
                        [[i["n"], fmt(i["q"]), fmt(i["p"]), fmt(i["v"]), f"**{fmt(i['md'])}**",
                          pct(i["md"] / i["p"] if i["p"] else None), fmt(i["q"] * i["md"] / 1e6, 1),
                          pct(i["q"] * i["md"] / MD if MD else None)] for i in items]))
    out.append("")
    out.append(f"Итого: {fmt(Q)} т, выручка {fmt(R / 1e6, 1)} млн руб., маржинальный доход **{fmt(MD / 1e6, 1)} млн руб.** "
               f"({pct(MD / R if R else None)}), средний МД {fmt(MD / Q if Q else 0)} руб/т.")
    neg = [i["n"] for i in items if i["md"] <= 0]
    if neg:
        out.append(f"**Отрицательный или нулевой МД:** {', '.join(neg)} — каждая тонна увеличивает убыток.")
    if fixed:
        ebit = MD - fixed
        be_t = fixed / (MD / Q) if MD > 0 else None
        out.append("")
        out.append("## Безубыточность (при текущей структуре сортамента)")
        out.append(md_table(["Показатель", "Значение"], [
            ["Постоянные затраты за период, млн руб.", fmt(fixed / 1e6, 1)],
            ["Операционная прибыль (МД − постоянные), млн руб.", f"**{fmt(ebit / 1e6, 1)}**"],
            ["Точка безубыточности, т", fmt(be_t)],
            ["Запас финансовой прочности", pct(1 - be_t / Q) if be_t and Q else "—"],
            ["Операционный рычаг (МД / прибыль)", fmt(MD / ebit, 2) if ebit > 0 else "прибыль ≤ 0"],
        ]))
        if ebit > 0:
            out.append(f"Рычаг {fmt(MD / ebit, 1)}: снижение выпуска на 10 % при прочих равных уменьшает прибыль на {fmt(MD / ebit * 10, 0)} %.")
    out.append("")
    out.append("_При ограничении мощности ранжировать продукты по МД на час работы узкого места (руб/т × т/ч), а не по МД на тонну._")
    emit("\n".join(out), a.out)


def obkap(a):
    if a.sample:
        a.vyruchka, a.sebest, a.dz, a.zapasy, a.kz, a.dney = 2.4e9, 2.1e9, 5.2e8, 6.1e8, 3.8e8, 90
    for k in ("vyruchka", "sebest", "dz", "zapasy", "kz"):
        if getattr(a, k) is None:
            sys.exit(f"не указан --{k}")
    dso = a.dz / a.vyruchka * a.dney
    dio = a.zapasy / a.sebest * a.dney
    dpo = a.kz / a.sebest * a.dney
    cycle = dso + dio - dpo
    day_rev = a.vyruchka / a.dney
    day_cost = a.sebest / a.dney
    out = ["# Оборотный капитал и финансовый цикл", ""]
    out.append(md_table(["Показатель", "Дней", "Сумма, млн руб.", "1 день = млн руб."], [
        ["Оборачиваемость ДЗ (DSO)", fmt(dso, 1), fmt(a.dz / 1e6, 1), fmt(day_rev / 1e6, 2)],
        ["Оборачиваемость запасов (DIO)", fmt(dio, 1), fmt(a.zapasy / 1e6, 1), fmt(day_cost / 1e6, 2)],
        ["Оборачиваемость КЗ (DPO)", fmt(dpo, 1), fmt(a.kz / 1e6, 1), fmt(day_cost / 1e6, 2)],
        ["**Финансовый цикл (DSO + DIO − DPO)**", f"**{fmt(cycle, 1)}**", fmt((a.dz + a.zapasy - a.kz) / 1e6, 1), ""],
    ]))
    out.append("")
    out.append(f"Сокращение ДЗ на 5 дней высвобождает ≈ {fmt(5 * day_rev / 1e6, 1)} млн руб.; запасов на 5 дней — "
               f"≈ {fmt(5 * day_cost / 1e6, 1)} млн руб.; увеличение отсрочки поставщикам на 5 дней — ≈ {fmt(5 * day_cost / 1e6, 1)} млн руб.")
    if a.celevoy_cikl is not None:
        gap = cycle - a.celevoy_cikl
        if gap > 0:
            out.append(f"До целевого цикла {fmt(a.celevoy_cikl)} дн. не хватает {fmt(gap, 1)} дн. ≈ {fmt(gap * day_cost / 1e6, 1)} млн руб. "
                       "денег, замороженных в обороте.")
    out.append("")
    out.append("_Запасы и КЗ отнесены к себестоимости, ДЗ — к выручке. Для точности использовать средние остатки за период._")
    emit("\n".join(out), a.out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="mode", required=True)
    m = sp.add_parser("marzha")
    m.add_argument("--input")
    m.add_argument("--postoyannye", type=float, help="постоянные затраты за период, руб")
    m.add_argument("--out")
    m.add_argument("--sample", action="store_true")
    o = sp.add_parser("obkap")
    for k in ("vyruchka", "sebest", "dz", "zapasy", "kz"):
        o.add_argument("--" + k, type=float)
    o.add_argument("--dney", type=float, default=30)
    o.add_argument("--celevoy-cikl", type=float)
    o.add_argument("--out")
    o.add_argument("--sample", action="store_true")
    a = ap.parse_args()
    marzha(a) if a.mode == "marzha" else obkap(a)


if __name__ == "__main__":
    main()
