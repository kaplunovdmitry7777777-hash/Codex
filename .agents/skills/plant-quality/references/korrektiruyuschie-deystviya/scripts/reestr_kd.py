#!/usr/bin/env python3
"""Статус и показатели корректирующих действий (КД) по СМК: возраст, просрочки, результативность, повторы.

Вход: реестр КД CSV/XLSX.
Колонки: № КД; Название; Источник; Значимость; Статус; Дата открытия; Плановый срок; Дата закрытия;
         Ответственный; Корневая причина; Результативность; Повтор
  Источник: рекламация / внутренний аудит / внешний аудит / НП (несоответствующая продукция) / анализ данных / ОТ и ПБ
  Значимость: критическое / значительное / незначительное
  Статус: открыто / анализ причин / выполнение / проверка результативности / закрыто
  Результативность: результативно / нерезультативно / (пусто)
  Повтор: да — несоответствие повторилось после закрытия КД

Запуск:  python3 reestr_kd.py --input КД.csv [--na-datu 06.10.2026] [--out отчет.md]
         python3 reestr_kd.py --sample
"""
import argparse
import os
import statistics
import sys
from collections import Counter, defaultdict
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tablio import read_table, get, to_date, fmt, pct, md_table, write_sample, emit  # noqa: E402

SAMPLE = """№ КД;Название;Источник;Значимость;Статус;Дата открытия;Плановый срок;Дата закрытия;Ответственный;Корневая причина;Результативность;Повтор
КД-2026-011;Продольные трещины на заготовке 150х150;НП;значительное;проверка результативности;12.05.2026;30.07.2026;;Начальник ЭСПЦ;Износ гильз кристаллизатора сверх нормы стойкости;;
КД-2026-014;Рекламация: отклонение по прямолинейности швеллера 20П;рекламация;критическое;выполнение;20.08.2026;20.09.2026;;Начальник СПЦ;;;
КД-2026-015;Просрочена поверка весов на складе лома;внутренний аудит;значительное;закрыто;02.06.2026;30.06.2026;25.06.2026;Главный метролог;Нет связи графика поверки с вводом СИ в эксплуатацию;результативно;нет
КД-2026-016;Несоответствие химсостава по сере в плавках;анализ данных;значительное;закрыто;10.04.2026;10.06.2026;05.07.2026;Начальник ЦЗЛ;Шихтовка без учёта засора лома;нерезультативно;да
КД-2026-018;Отсутствуют записи входного контроля огнеупоров;внешний аудит;значительное;анализ причин;01.09.2026;01.11.2026;;Директор по качеству;;;
КД-2026-019;Плёны на поверхности уголка 125;НП;незначительное;открыто;10.06.2026;10.08.2026;;Начальник СПЦ;;;
КД-2026-020;Устаревшая ТИ в обращении на участке отделки;внутренний аудит;незначительное;закрыто;15.07.2026;15.08.2026;10.08.2026;Главный технолог;Нет процедуры изъятия отменённых документов;результативно;нет
"""

BUCKETS = [(30, "0–30 дн: в работе"), (60, "31–60 дн: контроль"), (90, "61–90 дн: эскалация руководству"),
           (10 ** 6, "> 90 дн: вмешательство ГД/ПРК")]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input")
    ap.add_argument("--out")
    ap.add_argument("--sample", action="store_true")
    ap.add_argument("--na-datu")
    a = ap.parse_args()
    path = write_sample(SAMPLE, "kd_sample.csv") if a.sample else a.input
    if not path:
        ap.error("укажите --input или --sample")
    today = to_date(a.na_datu) if a.na_datu else (date(2026, 10, 6) if a.sample else date.today())
    rows = read_table(path)

    items = []
    for r in rows:
        items.append(dict(n=get(r, "№ кд", "№", default="—"), name=get(r, "название", default=""),
                          src=str(get(r, "источник", default="—")).strip(),
                          sev=str(get(r, "значимость", default="—")).strip().lower(),
                          st=str(get(r, "статус", default="открыто")).strip().lower(),
                          o=to_date(get(r, "дата открытия")), due=to_date(get(r, "плановый срок")),
                          c=to_date(get(r, "дата закрытия")), who=get(r, "ответственный", default="—"),
                          rc=str(get(r, "корневая причина", default="")).strip(),
                          eff=str(get(r, "результативность", default="")).strip().lower(),
                          rep=str(get(r, "повтор", default="")).strip().lower() == "да"))
    opn = [i for i in items if i["st"] != "закрыто"]
    cls = [i for i in items if i["st"] == "закрыто"]
    over = [i for i in opn if i["due"] and i["due"] < today]
    cyc = [(i["c"] - i["o"]).days for i in cls if i["c"] and i["o"]]
    verified = [i for i in cls if i["eff"] in ("результативно", "нерезультативно")]
    eff1 = [i for i in verified if i["eff"] == "результативно"]
    reps = [i for i in cls if i["rep"]]

    out = [f"# Корректирующие действия: статус на {today.strftime('%d.%m.%Y')}", ""]
    out.append(md_table(["Показатель", "Значение", "Ориентир"], [
        ["Открыто КД", len(opn), "—"],
        ["Просрочено (от открытых)", f"{len(over)} ({pct(len(over) / len(opn) if opn else None, 0)})", "< 10 %"],
        ["Средний цикл закрытия, дн", fmt(statistics.mean(cyc)) if cyc else "—", "< 60"],
        ["Результативность с первого раза", pct(len(eff1) / len(verified) if verified else None, 0), "> 90 %"],
        ["Повтор после закрытия", pct(len(reps) / len(cls) if cls else None, 0), "< 5 %"],
        ["Открытые без установленной корневой причины старше 30 дн",
         sum(1 for i in opn if not i["rc"] and i["o"] and (today - i["o"]).days > 30), "0"],
    ]))
    out.append("")
    out.append("## Открытые по значимости и статусу")
    sev = Counter(i["sev"] for i in opn)
    st = Counter(i["st"] for i in opn)
    out.append("Значимость: " + ", ".join(f"{k} — {v}" for k, v in sev.most_common()) + ".")
    out.append("Статус: " + ", ".join(f"{k} — {v}" for k, v in st.most_common()) + ".")
    out.append("")
    out.append("## Возраст открытых КД")
    ag = defaultdict(list)
    for i in opn:
        age = (today - i["o"]).days if i["o"] else 0
        for lim, lab in BUCKETS:
            if age <= lim:
                ag[lab].append(i)
                break
    out.append(md_table(["Возраст", "Кол-во", "КД"], [[lab, len(ag[lab]), ", ".join(str(i["n"]) for i in ag[lab])]
                                                       for _, lab in BUCKETS if ag[lab]]))
    out.append("")
    if over:
        out.append("## Просроченные")
        out.append(md_table(["№", "Название", "Значимость", "Статус", "Срок", "Просрочка, дн", "Ответственный"],
                            [[i["n"], i["name"], i["sev"], i["st"], i["due"].strftime("%d.%m.%Y"), (today - i["due"]).days,
                              i["who"]] for i in sorted(over, key=lambda x: x["due"])]))
        out.append("")
    if reps or [i for i in verified if i["eff"] == "нерезультативно"]:
        out.append("## Нерезультативные и повторившиеся (повторный анализ причин)")
        for i in cls:
            if i["rep"] or i["eff"] == "нерезультативно":
                out.append(f"- {i['n']} {i['name']}: причина «{i['rc'] or 'не установлена'}» — устранение не сработало, "
                           "причина определена неверно или не полностью.")
        out.append("")
    out.append("## По источникам")
    src = Counter(i["src"] for i in items)
    out.append(md_table(["Источник", "Всего КД", "Открыто"], [[k, v, sum(1 for i in opn if i["src"] == k)] for k, v in src.most_common()]))
    emit("\n".join(out), a.out)


if __name__ == "__main__":
    main()
