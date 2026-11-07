#!/usr/bin/env python3
"""Риск-ориентированная программа внутренних аудитов СМК (ГОСТ Р ИСО 9001-2015 п. 9.2, ГОСТ Р ИСО 19011-2021).

Вход: CSV/XLSX — перечень процессов СМК.
Колонки: Процесс; Пункты ISO 9001; Владелец; Риск; Последний аудит; Открытых несоответствий; Изменения
  Риск: высокий / средний / низкий.  Пункты ISO 9001: через запятую, например «8.5, 8.7».
  Изменения: да — процесс существенно менялся (новое оборудование, оргструктура, ТИ).
Периодичность: высокий — 6 мес, средний — 12 мес, низкий — 24 мес. Открытые несоответствия или изменения
повышают уровень на одну ступень.

Запуск:  python3 programma_auditov.py --input процессы.csv [--god 2027] [--na-datu 06.10.2026] [--out отчет.md]
         python3 programma_auditov.py --sample
"""
import argparse
import os
import sys
from collections import defaultdict
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tablio import read_table, get, num, to_date, md_table, write_sample, emit  # noqa: E402

SAMPLE = """Процесс;Пункты ISO 9001;Владелец;Риск;Последний аудит;Открытых несоответствий;Изменения
Анализ требований заказчика и договоры;8.2;Коммерческий директор;средний;15.03.2026;0;нет
Закупки и оценка поставщиков;8.4;Директор по закупкам;высокий;10.02.2026;1;нет
Выплавка и внепечная обработка стали;8.1, 8.5.1, 8.5.2;Начальник ЭСПЦ;высокий;20.05.2026;0;да
Прокатное производство;8.5.1, 8.5.2, 8.5.4;Начальник СПЦ;высокий;12.11.2025;2;нет
Технический контроль и испытания;8.6, 8.7;Директор по качеству;высокий;01.04.2026;0;нет
Метрологическое обеспечение;7.1.5;Главный метролог;средний;18.09.2025;1;нет
ТОиР оборудования;7.1.3;Главный механик;средний;05.06.2025;0;да
Управление персоналом и компетентность;7.1.2, 7.2, 7.3;Директор по персоналу;низкий;10.10.2024;0;нет
Управление документированной информацией;7.5;Директор по качеству;низкий;15.01.2026;0;нет
Корректирующие действия и улучшения;10.1, 10.2, 10.3;Директор по качеству;высокий;20.03.2026;0;нет
Анализ со стороны руководства;5.1, 6.1, 6.2, 9.3;Генеральный директор;средний;25.02.2026;0;нет
Внутренние аудиты;9.2;Директор по качеству;низкий;01.12.2025;0;нет
Удовлетворённость потребителей;9.1.2;Коммерческий директор;средний;;0;нет
"""

ALL_CLAUSES = ["4.1", "4.2", "4.3", "4.4", "5.1", "5.2", "5.3", "6.1", "6.2", "6.3", "7.1", "7.2", "7.3", "7.4", "7.5",
               "8.1", "8.2", "8.3", "8.4", "8.5", "8.6", "8.7", "9.1", "9.2", "9.3", "10.1", "10.2", "10.3"]
LEVELS = ["низкий", "средний", "высокий"]
FREQ = {"высокий": 6, "средний": 12, "низкий": 24}


def add_months(d, m):
    y = d.year + (d.month - 1 + m) // 12
    mo = (d.month - 1 + m) % 12 + 1
    return date(y, mo, min(d.day, 28))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input")
    ap.add_argument("--out")
    ap.add_argument("--sample", action="store_true")
    ap.add_argument("--god", type=int)
    ap.add_argument("--na-datu")
    a = ap.parse_args()
    path = write_sample(SAMPLE, "audity_sample.csv") if a.sample else a.input
    if not path:
        ap.error("укажите --input или --sample")
    today = to_date(a.na_datu) if a.na_datu else (date(2026, 10, 6) if a.sample else date.today())
    year = a.god or today.year + 1
    rows = read_table(path)

    items = []
    covered = set()
    for r in rows:
        risk = str(get(r, "риск", default="средний")).strip().lower()
        risk = risk if risk in LEVELS else "средний"
        nc = int(num(get(r, "открытых несоответствий"), 0) or 0)
        ch = str(get(r, "изменения", default="")).strip().lower() == "да"
        eff = risk
        reason = []
        if nc or ch:
            eff = LEVELS[min(2, LEVELS.index(risk) + 1)]
            if nc:
                reason.append(f"{nc} откр. НС")
            if ch:
                reason.append("изменения")
        last = to_date(get(r, "последний аудит"))
        nxt = add_months(last, FREQ[eff]) if last else today
        cl = [c.strip() for c in str(get(r, "пункты iso 9001", "пункты", default="")).replace(";", ",").split(",") if c.strip()]
        for c in cl:
            covered.add(".".join(c.split(".")[:2]))
        items.append(dict(p=get(r, "процесс", default="—"), cl=", ".join(cl), own=get(r, "владелец", default=""), risk=risk,
                          eff=eff, why=", ".join(reason), last=last, nxt=nxt, over=nxt < today))

    items.sort(key=lambda i: i["nxt"])
    out = [f"# Программа внутренних аудитов СМК на {year} год", "", f"Состояние на {today.strftime('%d.%m.%Y')}.", ""]
    over = [i for i in items if i["over"]]
    if over:
        out.append(f"**Просрочены аудиты: {len(over)}** — " + "; ".join(f"{i['p']} (должен был быть до {i['nxt'].strftime('%d.%m.%Y')})"
                                                                   for i in over) + ". Провести в ближайший квартал.")
        out.append("")
    out.append(md_table(["Процесс", "Пункты", "Владелец", "Риск", "Уровень с учётом НС/изменений", "Периодичность, мес",
                         "Последний аудит", "Следующий до"],
                        [[i["p"], i["cl"], i["own"], i["risk"], i["eff"] + (f" ({i['why']})" if i["why"] else ""), FREQ[i["eff"]],
                          i["last"].strftime("%d.%m.%Y") if i["last"] else "не проводился",
                          ("**" + i["nxt"].strftime("%d.%m.%Y") + " — просрочен**") if i["over"] else i["nxt"].strftime("%d.%m.%Y")]
                         for i in items]))
    out.append("")
    plan = defaultdict(list)
    k = 0
    for i in items:
        if i["over"] or not i["last"]:
            # просроченные и не проводившиеся распределяем по ближайшим трём месяцам
            d = add_months(today, 1 + k % 3)
            k += 1
        else:
            d = i["nxt"]
        while d.year <= year:
            if d.year == year:
                plan[d.month].append(i["p"])
            d = add_months(d, FREQ[i["eff"]])
    months = ["январь", "февраль", "март", "апрель", "май", "июнь", "июль", "август", "сентябрь", "октябрь", "ноябрь", "декабрь"]
    out.append(f"## График на {year} год")
    out.append(md_table(["Месяц", "Аудиты"], [[months[m - 1], "; ".join(plan[m])] for m in range(1, 13) if plan[m]]))
    heavy = [months[m - 1] for m in range(1, 13) if len(plan[m]) > 3]
    if heavy:
        out.append(f"Перегруженные месяцы (> 3 аудитов): {', '.join(heavy)} — перенести часть в соседние месяцы.")
    out.append("")
    missing = [c for c in ALL_CLAUSES if c not in covered]
    out.append("## Охват требований ГОСТ Р ИСО 9001-2015")
    out.append("Все пункты 4–10 охвачены программой." if not missing else
               "**Не охвачены пункты:** " + ", ".join(missing) + ". Закрепить их за процессами (обычно 4.x и 5.x — анализ руководством, "
               "7.4 — коммуникации, 8.3 — проектирование, если применимо; неприменимость 8.3 обосновать в области применения СМК).")
    emit("\n".join(out), a.out)


if __name__ == "__main__":
    main()
