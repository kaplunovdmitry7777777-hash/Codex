#!/usr/bin/env python3
"""OEE агрегатов, потери выпуска по видам, загрузка мощностей под план и узкое место цепочки.

Вход: CSV/XLSX, одна строка на агрегат за отчётный период.
Колонки: Агрегат; Передел; Календарное время, ч; Плановые простои, ч; Внеплановые простои, ч;
         Номинальная производительность, т/ч; Выпуск, т; Брак, т; План след. периода, т; Время след. периода, ч
  Плановые простои — ППР, капремонт, плановые перевалки. Внеплановые — аварийные, ожидание металла/валков/энергии.
  План след. периода — в тоннах продукции этого агрегата (с учётом расходных коэффициентов между переделами).

Запуск:  python3 oee_moschnosti.py --input агрегаты.csv [--out отчет.md]
         python3 oee_moschnosti.py --sample
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tablio import read_table, get, num, fmt, pct, md_table, write_sample, emit  # noqa: E402

SAMPLE = """Агрегат;Передел;Календарное время, ч;Плановые простои, ч;Внеплановые простои, ч;Номинальная производительность, т/ч;Выпуск, т;Брак, т;План след. периода, т;Время след. периода, ч
ДСП-1;Сталеплавильный;744;48;62;95;51200;310;56000;720
УПК-1;Сталеплавильный;744;24;20;110;51000;0;56000;720
МНЛЗ-1;Сталеплавильный;744;36;45;100;50300;520;55000;720
Стан 900;Прокатный;744;72;88;75;40100;640;46000;720
Стан 680;Прокатный;744;60;40;40;21500;410;20000;720
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input")
    ap.add_argument("--out")
    ap.add_argument("--sample", action="store_true")
    ap.add_argument("--porog", type=float, default=0.85, help="порог загрузки «зона риска», по умолчанию 0.85")
    a = ap.parse_args()
    path = write_sample(SAMPLE, "oee_sample.csv") if a.sample else a.input
    if not path:
        ap.error("укажите --input или --sample")
    rows = read_table(path)

    res = []
    for r in rows:
        name = str(get(r, "агрегат", default="—")).strip()
        cal = num(get(r, "календарное время, ч", "календарное время"), 0)
        pl = num(get(r, "плановые простои, ч", "плановые простои"), 0)
        vn = num(get(r, "внеплановые простои, ч", "внеплановые простои"), 0)
        nom = num(get(r, "номинальная производительность, т/ч", "номинальная производительность"), 0)
        out_t = num(get(r, "выпуск, т", "выпуск"), 0)
        brak = num(get(r, "брак, т", "брак"), 0)
        plan = num(get(r, "план след. периода, т", "план след периода, т", "план"))
        tnext = num(get(r, "время след. периода, ч", "время след периода, ч"), cal)
        avail_t = cal - pl
        run_t = avail_t - vn
        A = run_t / avail_t if avail_t else 0
        P = out_t / (run_t * nom) if run_t and nom else 0
        Q = (out_t - brak) / out_t if out_t else 0
        oee = A * P * Q
        loss_vn = vn * nom * P
        loss_speed = run_t * nom * (1 - P) if P < 1 else 0
        # эффективная мощность след. периода по фактическим A, P, Q и той же доле плановых простоев
        share_pl = pl / cal if cal else 0
        cap = tnext * (1 - share_pl) * A * P * nom * Q
        load = plan / cap if plan and cap else None
        res.append(dict(name=name, per=get(r, "передел", default="—"), A=A, P=P, Q=Q, oee=oee, out=out_t,
                        loss_vn=loss_vn, loss_speed=loss_speed, brak=brak, cap=cap, plan=plan, load=load))

    out = ["# OEE и загрузка мощностей", ""]
    out.append("## 1. Эффективность оборудования за период")
    out.append(md_table(["Агрегат", "Передел", "Доступность", "Производ.", "Качество", "**OEE**", "Выпуск, т"],
                        [[x["name"], x["per"], pct(x["A"]), pct(x["P"]), pct(x["Q"]), f"**{pct(x['oee'])}**", fmt(x["out"])]
                         for x in res]))
    out.append("")
    out.append("## 2. Потери выпуска, т (где теряем тонны)")
    out.append(md_table(["Агрегат", "Внеплановые простои", "Снижение темпа", "Брак", "Итого потерь"],
                        [[x["name"], fmt(x["loss_vn"]), fmt(x["loss_speed"]), fmt(x["brak"]),
                          f"**{fmt(x['loss_vn'] + x['loss_speed'] + x['brak'])}**"] for x in res]))
    out.append("")
    with_plan = [x for x in res if x["load"] is not None]
    if with_plan:
        out.append("## 3. Загрузка под план следующего периода")
        t = []
        for x in with_plan:
            st = "НЕВЫПОЛНИМ" if x["load"] > 1 else ("РИСК" if x["load"] > a.porog else "норма")
            t.append([x["name"], fmt(x["plan"]), fmt(x["cap"]), f"**{pct(x['load'])}**", st,
                      fmt(max(0, x["plan"] - x["cap"]))])
        out.append(md_table(["Агрегат", "План, т", "Эффект. мощность, т", "Загрузка", "Статус", "Дефицит, т"], t))
        out.append("")
        b = max(with_plan, key=lambda x: x["load"])
        out.append(f"**Узкое место: {b['name']}** — загрузка {pct(b['load'])}. Выпуск всей цепочки определяется этим агрегатом: "
                   "сначала поднимать его доступность (сокращать внеплановые простои и время перевалок), "
                   "потом всё остальное. Прирост на других агрегатах выпуска не добавит.")
        out.append("")
    out.append(f"_Эффективная мощность = время периода × (1 − доля плановых простоев) × доступность × производительность × "
               f"номинал × качество, по факту отчётного периода. Порог «риска» {pct(a.porog, 0)}: выше него любая "
               "внеплановая остановка срывает план._")
    emit("\n".join(out), a.out)


if __name__ == "__main__":
    main()
