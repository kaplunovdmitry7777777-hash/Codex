#!/usr/bin/env python3
"""Сценарная модель «что если» для металлургического завода (месячная экономика).

Считает EBITDA и денежный запас для базового сценария, каждой переменной риска отдельно,
их попарных сочетаний и полного сочетания (до 3 переменных), плюс чувствительность ±10 % по каждому фактору.

Вход: JSON
{
  "baza": {"vypusk_t": 48000, "cena_rub_t": 55000, "lom_t_na_t": 1.12, "cena_loma": 28000,
           "ee_kvtch_na_t": 650, "tarif_ee": 6.2, "prochie_perem_rub_t": 6500,
           "postoyannye_mes": 450000000, "ostatok_deneg": 900000000, "platezhi_mes": 120000000},
  "peremennye": [
     {"nazvanie": "Цена проката −12 %", "izmeneniya": {"cena_rub_t": -0.12}, "veroyatnost": 0.3},
     {"nazvanie": "Лом +15 %", "izmeneniya": {"cena_loma": 0.15}, "veroyatnost": 0.25},
     {"nazvanie": "Авария стана 900, −20 % выпуска на месяц", "izmeneniya": {"vypusk_t": -0.20}, "veroyatnost": 0.1}
  ]
}
  izmeneniya — относительные изменения (−0.12 = −12 %). platezhi_mes — CAPEX, проценты и погашение долга в месяц.

Запуск:  python3 scenarnaya_model.py --input scenarii.json [--out отчет.md]
         python3 scenarnaya_model.py --sample
"""
import argparse
import itertools
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tablio import fmt, pct, md_table, emit  # noqa: E402

SAMPLE = {
    "baza": {"vypusk_t": 48000, "cena_rub_t": 55000, "lom_t_na_t": 1.12, "cena_loma": 28000, "ee_kvtch_na_t": 650,
             "tarif_ee": 6.2, "prochie_perem_rub_t": 6500, "postoyannye_mes": 450000000,
             "ostatok_deneg": 900000000, "platezhi_mes": 120000000},
    "peremennye": [
        {"nazvanie": "Цена проката −12 %", "izmeneniya": {"cena_rub_t": -0.12}, "veroyatnost": 0.3},
        {"nazvanie": "Лом +15 %", "izmeneniya": {"cena_loma": 0.15}, "veroyatnost": 0.25},
        {"nazvanie": "Авария стана 900: выпуск −20 %", "izmeneniya": {"vypusk_t": -0.20}, "veroyatnost": 0.1},
    ],
}

NAMES = {"vypusk_t": "Выпуск, т", "cena_rub_t": "Цена реализации", "lom_t_na_t": "Расход лома, т/т",
         "cena_loma": "Цена лома", "ee_kvtch_na_t": "Расход э/э, кВт·ч/т", "tarif_ee": "Тариф э/э",
         "prochie_perem_rub_t": "Прочие переменные", "postoyannye_mes": "Постоянные затраты"}


def ebitda(b):
    var_t = b["lom_t_na_t"] * b["cena_loma"] + b["ee_kvtch_na_t"] * b["tarif_ee"] + b["prochie_perem_rub_t"]
    return b["vypusk_t"] * (b["cena_rub_t"] - var_t) - b["postoyannye_mes"]


def apply(b, ch):
    n = dict(b)
    for k, v in ch.items():
        if k in n:
            n[k] = n[k] * (1 + v)
    return n


def months_cash(b, e):
    flow = e - b.get("platezhi_mes", 0)
    cash = b.get("ostatok_deneg")
    if cash is None:
        return None, flow
    if flow >= 0:
        return float("inf"), flow
    return cash / -flow, flow


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input")
    ap.add_argument("--out")
    ap.add_argument("--sample", action="store_true")
    a = ap.parse_args()
    if a.sample:
        data = SAMPLE
    elif a.input:
        data = json.load(open(a.input, encoding="utf-8-sig"))
    else:
        ap.error("укажите --input или --sample")
    b = data["baza"]
    pv = data.get("peremennye", [])[:3]
    e0 = ebitda(b)
    m0, f0 = months_cash(b, e0)

    out = ["# Сценарный анализ «что если»", ""]
    out.append(f"Базовый месяц: EBITDA **{fmt(e0 / 1e6, 1)} млн руб.**, свободный поток после платежей {fmt(f0 / 1e6, 1)} млн руб./мес.")
    out.append("")

    rows = []
    combos = []
    for k in range(1, len(pv) + 1):
        for c in itertools.combinations(pv, k):
            ch = {}
            p = 1.0
            for v in c:
                for kk, vv in v["izmeneniya"].items():
                    ch[kk] = (1 + ch.get(kk, 0)) * (1 + vv) - 1
                p *= v.get("veroyatnost", 1)
            nb = apply(b, ch)
            e = ebitda(nb)
            m, f = months_cash(nb, e)
            level = "Базовый (1 фактор)" if k == 1 else ("Стресс (2 фактора)" if k == 2 else "Тяжёлый (3 фактора)")
            combos.append((level, " + ".join(v["nazvanie"] for v in c), e, f, m, p))
    for level, name, e, f, m, p in combos:
        rows.append([level, name, f"**{fmt(e / 1e6, 1)}**", fmt((e - e0) / 1e6, 1), fmt(f / 1e6, 1),
                     "не уходит в минус" if m in (None, float("inf")) else f"{fmt(m, 1)} мес.", pct(p, 1)])
    out.append("## Сценарии")
    out.append(md_table(["Уровень", "Сочетание", "EBITDA, млн/мес", "Δ к базе", "Поток после платежей", "Деньги закончатся через",
                         "Вероятн.*"], rows))
    out.append("")
    out.append("\\* Вероятность сочетания посчитана как произведение, то есть в предположении независимости факторов. "
               "На практике падение цены проката и рост цены лома часто связаны: уточнить вручную.")
    out.append("")

    sens = []
    for k in NAMES:
        if k not in b:
            continue
        up = ebitda(apply(b, {k: 0.10})) - e0
        sens.append((NAMES[k], up))
    sens.sort(key=lambda x: -abs(x[1]))
    out.append("## Чувствительность EBITDA к изменению фактора на +10 %")
    out.append(md_table(["Фактор", "Δ EBITDA, млн руб./мес", "Δ, % от базы"],
                        [[n, fmt(d / 1e6, 1), pct(d / e0 if e0 else None)] for n, d in sens]))
    out.append("")
    out.append("_Модель линейная, месячная, без эффектов второго порядка (рост ДЗ при падении рынка, штрафы покупателей при аварии, "
               "налоговые эффекты). Каскадные последствия описывать в отчёте отдельно._")
    emit("\n".join(out), a.out)


if __name__ == "__main__":
    main()
