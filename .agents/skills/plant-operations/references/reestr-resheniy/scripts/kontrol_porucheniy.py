#!/usr/bin/env python3
"""Контроль исполнения поручений ГД: просрочки, ближайшие сроки, исполнительская дисциплина по ответственным.

Вход: реестр поручений CSV/XLSX.
Колонки: №; Дата; Источник; Поручение; Ответственный; Срок; Статус; Дата исполнения; Переносов
  Статус: в работе / исполнено / перенесено / отменено. Дата исполнения — для исполненных.

Запуск:  python3 kontrol_porucheniy.py --input реестр.csv [--na-datu 06.10.2026] [--otvetstvennyy Иванов] [--poisk лом] [--out отчет.md]
         python3 kontrol_porucheniy.py --sample
"""
import argparse
import os
import sys
from collections import defaultdict
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tablio import read_table, get, num, to_date, fmt, pct, md_table, write_sample, emit  # noqa: E402

SAMPLE = """№;Дата;Источник;Поручение;Ответственный;Срок;Статус;Дата исполнения;Переносов
1;01.09.2026;Совещание по производству;Представить план сокращения внеплановых простоев стана 900;Главный механик;15.09.2026;исполнено;14.09.2026;0
2;01.09.2026;Совещание по производству;Согласовать второго поставщика электродов и провести испытания;Директор по закупкам;30.09.2026;в работе;;1
3;08.09.2026;Итоги августа;Разобрать рост расхода электроэнергии на ДСП (+4 % к норме);Начальник ЭСПЦ;22.09.2026;исполнено;29.09.2026;0
4;08.09.2026;Итоги августа;Подготовить предложения по снижению ДЗ свыше 90 дней;Финансовый директор;30.09.2026;в работе;;0
5;15.09.2026;Совещание по ОТ;Провести внеплановую проверку знаний по наряд-допускам в ПЦ;Начальник ПЦ;05.10.2026;в работе;;0
6;15.09.2026;Совещание по ОТ;Обновить карты оценки профрисков на участке отделки;Начальник ООТиПБ;10.10.2026;в работе;;0
7;22.09.2026;Совещание по качеству;Внедрить 8D по претензии покупателя по швеллеру 20П;Директор по качеству;06.10.2026;в работе;;0
8;22.09.2026;Совещание по качеству;Пересмотреть ТИ по нагреву заготовки;Главный технолог;20.10.2026;в работе;;0
9;29.09.2026;Совещание по сбыту;Подготовить прайс на IV квартал;Коммерческий директор;03.10.2026;исполнено;02.10.2026;0
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input")
    ap.add_argument("--out")
    ap.add_argument("--sample", action="store_true")
    ap.add_argument("--na-datu")
    ap.add_argument("--otvetstvennyy")
    ap.add_argument("--poisk")
    ap.add_argument("--gorizont", type=int, default=7, help="дней вперёд для ближайших сроков")
    a = ap.parse_args()
    path = write_sample(SAMPLE, "porucheniya_sample.csv") if a.sample else a.input
    if not path:
        ap.error("укажите --input или --sample")
    today = to_date(a.na_datu) if a.na_datu else (date(2026, 10, 6) if a.sample else date.today())
    rows = read_table(path)

    items = []
    for r in rows:
        it = dict(n=get(r, "№", "номер", default=""), d=to_date(get(r, "дата")), src=get(r, "источник", default=""),
                  text=str(get(r, "поручение", "решение", default="")).strip(),
                  who=str(get(r, "ответственный", default="—")).strip(), due=to_date(get(r, "срок")),
                  st=str(get(r, "статус", default="в работе")).strip().lower(), done=to_date(get(r, "дата исполнения")),
                  moves=int(num(get(r, "переносов"), 0) or 0))
        if a.otvetstvennyy and a.otvetstvennyy.lower() not in it["who"].lower():
            continue
        if a.poisk and a.poisk.lower() not in (it["text"] + " " + str(it["src"])).lower():
            continue
        items.append(it)

    act = [i for i in items if i["st"] not in ("исполнено", "отменено")]
    overdue = sorted([i for i in act if i["due"] and i["due"] < today], key=lambda i: i["due"])
    soon = sorted([i for i in act if i["due"] and 0 <= (i["due"] - today).days <= a.gorizont], key=lambda i: i["due"])
    no_due = [i for i in act if not i["due"]]

    out = [f"# Контроль исполнения поручений на {today.strftime('%d.%m.%Y')}", ""]
    out.append(f"Всего: {len(items)}; в работе: {len(act)}; **просрочено: {len(overdue)}**; срок в ближайшие {a.gorizont} дн.: {len(soon)}.")
    out.append("")
    if overdue:
        out.append("## Просроченные")
        out.append(md_table(["№", "Поручение", "Ответственный", "Срок", "Просрочка, дн", "Переносов"],
                            [[i["n"], i["text"], i["who"], i["due"].strftime("%d.%m.%Y"), (today - i["due"]).days, i["moves"]]
                             for i in overdue]))
        out.append("")
    if soon:
        out.append(f"## Срок в ближайшие {a.gorizont} дней")
        out.append(md_table(["№", "Поручение", "Ответственный", "Срок"],
                            [[i["n"], i["text"], i["who"], i["due"].strftime("%d.%m.%Y")] for i in soon]))
        out.append("")
    if no_due:
        out.append("## Без срока (нарушение правила реестра)")
        out.extend(f"- №{i['n']} {i['text']} — {i['who']}" for i in no_due)
        out.append("")

    by = defaultdict(lambda: {"all": 0, "done": 0, "intime": 0, "late_days": [], "over": 0, "moves": 0})
    for i in items:
        b = by[i["who"]]
        if i["st"] == "отменено":
            continue
        b["all"] += 1
        b["moves"] += i["moves"]
        if i["st"] == "исполнено":
            b["done"] += 1
            if i["due"] and i["done"]:
                if i["done"] <= i["due"]:
                    b["intime"] += 1
                else:
                    b["late_days"].append((i["done"] - i["due"]).days)
        elif i["due"] and i["due"] < today:
            b["over"] += 1
    out.append("## Исполнительская дисциплина по ответственным")
    t = []
    for who, b in sorted(by.items(), key=lambda x: (-x[1]["over"], x[0])):
        closed_or_over = b["done"] + b["over"]
        disc = b["intime"] / closed_or_over if closed_or_over else None
        t.append([who, b["all"], b["done"], b["intime"], b["over"], b["moves"],
                  fmt(sum(b["late_days"]) / len(b["late_days"]), 0) if b["late_days"] else "—", pct(disc, 0)])
    out.append(md_table(["Ответственный", "Всего", "Исполнено", "В срок", "Просрочено", "Переносов", "Ср. опоздание, дн",
                         "Дисциплина"], t))
    out.append("")
    out.append("_Дисциплина = исполнено в срок / (исполнено + просрочено на дату). Поручения с переносом срока ≥ 2 раз "
               "выносить на совещание отдельно._")
    emit("\n".join(out), a.out)


if __name__ == "__main__":
    main()
