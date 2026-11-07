#!/usr/bin/env python3
"""FMEA процесса (ПЧР, приоритет мер) и матрица рисков 5×5.

Режим fmea — анализ видов и последствий отказов процесса (ГОСТ Р 27.303-2021 / IEC 60812).
  Колонки: Процесс; Вид отказа; Последствие; S; Причина; O; Текущий контроль; D; Мера; Ответственный; Срок; S после; O после; D после
  S — значимость последствия, O — возникновение причины, D — обнаружение (10 = не обнаруживается), шкалы 1–10.
  python3 pfmea.py fmea --input fmea.csv [--porog-pchr 200] [--out отчет.md]

Режим matrica — реестр рисков с оценкой вероятность × тяжесть (1–5), для п. 6.1 ГОСТ Р ИСО 9001 и рисков предприятия.
  Колонки: Риск; Категория; Вероятность; Тяжесть; Владелец; Мера
  python3 pfmea.py matrica --input риски.csv [--out отчет.md]

Пример: python3 pfmea.py fmea --sample ;  python3 pfmea.py matrica --sample
"""
import argparse
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tablio import read_table, get, num, fmt, md_table, write_sample, emit  # noqa: E402

SAMPLE_FMEA = """Процесс;Вид отказа;Последствие;S;Причина;O;Текущий контроль;D;Мера;Ответственный;Срок;S после;O после;D после
Разливка на МНЛЗ;Продольные трещины заготовки;Брак проката, рекламация;8;Износ гильзы кристаллизатора сверх нормы;6;Визуальный осмотр заготовки;6;Учёт стойкости в АСУ, запрет работы сверх нормы;Главный механик;30.11.2026;8;2;3
Разливка на МНЛЗ;Прорыв металла под кристаллизатором;Авария, угроза жизни, простой 2–5 сут;10;Нарушение режима вторичного охлаждения;3;Сигнализация расхода воды;4;Резервирование насосов, блокировка по расходу;Главный энергетик;31.12.2026;;;
Выплавка в ДСП;Превышение серы в плавке;Переназначение марки, потеря маржи;6;Засор лома, нет учёта в шихтовке;5;Анализ ЦЗЛ по ходу плавки;3;;;;;;
Нагрев в методической печи;Перегрев/пережог заготовки;Брак, трещины при прокатке;7;Отказ термопары, нарушение режима;4;Контроль температуры пирометром;5;;;;;;
Прокатка на стане 900;Отклонение размеров профиля;Рекламация, пересортица;7;Износ калибров, неверная настройка;5;Замер калибром по ходу прокатки;4;Регламент перевалок по тоннажу;Начальник СПЦ;15.11.2026;;;
Отделка и отгрузка;Пересортица марок;Рекламация, претензия покупателя;8;Ошибка маркировки пачек;3;Сверка бирок при отгрузке;5;Штрихкодирование бирок;Начальник ОТК;31.03.2027;;;
"""

SAMPLE_MATR = """Риск;Категория;Вероятность;Тяжесть;Владелец;Мера
Авария стана 900 с простоем > 7 сут;Производство;2;5;Главный механик;Страховой запас критичных узлов
Рост цены лома > 15 %;Рынок;3;4;Директор по закупкам;Долгосрочные договоры, второй регион поставки
Уход покупателя с долей 22 % выручки;Продажи;2;4;Коммерческий директор;Диверсификация портфеля
Срыв поставки электродов;Закупки;3;4;Директор по закупкам;Второй поставщик, запас 30 суток
Предписание Ростехнадзора с остановкой ОПО;Промбезопасность;1;5;Главный инженер;Производственный контроль, экспертиза ПБ
Отток сталеваров и вальцовщиков;Персонал;3;3;Директор по персоналу;Программа удержания, обучение резерва
Ошибки в маркировке продукции;Качество;3;2;Директор по качеству;Штрихкодирование
"""


def fmea(a):
    path = write_sample(SAMPLE_FMEA, "fmea_sample.csv") if a.sample else a.input
    if not path:
        sys.exit("укажите --input или --sample")
    rows = read_table(path)
    items = []
    for r in rows:
        S, O, D = (int(num(get(r, k), 0) or 0) for k in ("s", "o", "d"))
        S2, O2, D2 = (num(get(r, k)) for k in ("s после", "o после", "d после"))
        rpn = S * O * D
        if S >= 9 or rpn >= a.porog_pchr:
            pr = "ВЫСОКИЙ"
        elif rpn >= a.porog_pchr / 2 or (S >= 7 and O >= 4):
            pr = "СРЕДНИЙ"
        else:
            pr = "НИЗКИЙ"
        items.append(dict(p=get(r, "процесс", default="—"), f=get(r, "вид отказа", default="—"),
                          e=get(r, "последствие", default=""), c=get(r, "причина", default=""),
                          S=S, O=O, D=D, rpn=rpn, pr=pr, m=str(get(r, "мера", default="")).strip(),
                          who=get(r, "ответственный", default=""), due=get(r, "срок", default=""),
                          rpn2=int(S2 * O2 * D2) if None not in (S2, O2, D2) else None))
    order = {"ВЫСОКИЙ": 0, "СРЕДНИЙ": 1, "НИЗКИЙ": 2}
    items.sort(key=lambda i: (order[i["pr"]], -i["S"], -i["rpn"]))
    out = ["# FMEA процесса", ""]
    out.append(f"Строк: {len(items)}. Высокий приоритет: {sum(i['pr'] == 'ВЫСОКИЙ' for i in items)}, "
               f"средний: {sum(i['pr'] == 'СРЕДНИЙ' for i in items)}, низкий: {sum(i['pr'] == 'НИЗКИЙ' for i in items)}.")
    out.append("")
    out.append(md_table(["Процесс", "Вид отказа", "Причина", "S", "O", "D", "ПЧР", "Приоритет", "Мера", "Отв.", "Срок", "ПЧР после"],
                        [[i["p"], i["f"], i["c"], i["S"], i["O"], i["D"], f"**{i['rpn']}**", i["pr"], i["m"] or "**НЕТ**",
                          i["who"], i["due"], i["rpn2"] if i["rpn2"] is not None else "—"] for i in items]))
    out.append("")
    nomeas = [i for i in items if i["pr"] != "НИЗКИЙ" and not i["m"]]
    if nomeas:
        out.append("## Требуют меры, но мера не назначена")
        out.extend(f"- {i['p']}: {i['f']} (S={i['S']}, ПЧР={i['rpn']})" for i in nomeas)
        out.append("")
    by = defaultdict(int)
    for i in items:
        by[i["p"]] += i["rpn"]
    out.append("## Суммарный ПЧР по процессам (где сосредоточен риск)")
    out.append(md_table(["Процесс", "Σ ПЧР"], [[p, v] for p, v in sorted(by.items(), key=lambda x: -x[1])]))
    out.append("")
    out.append(f"_Приоритет: ВЫСОКИЙ — S ≥ 9 (безопасность, авария) независимо от ПЧР, или ПЧР ≥ {a.porog_pchr:g}; "
               f"СРЕДНИЙ — ПЧР ≥ {a.porog_pchr / 2:g} или S ≥ 7 при O ≥ 4. При S ≥ 9 в первую очередь снижать O (устранять причину), "
               "а не улучшать обнаружение. Пороги — внутренняя договорённость предприятия, их можно изменить._")
    emit("\n".join(out), a.out)


LEVEL = {}
for p in range(1, 6):
    for s in range(1, 6):
        v = p * s
        LEVEL[(p, s)] = "КРИТИЧЕСКИЙ" if (v >= 15 or (s == 5 and p >= 3)) else ("ВЫСОКИЙ" if v >= 8 or s == 5 else ("СРЕДНИЙ" if v >= 4 else "НИЗКИЙ"))


SHORT = {"КРИТИЧЕСКИЙ": "Крит", "ВЫСОКИЙ": "Выс", "СРЕДНИЙ": "Сред", "НИЗКИЙ": "Низ"}


def matrica(a):
    path = write_sample(SAMPLE_MATR, "riski_sample.csv") if a.sample else a.input
    if not path:
        sys.exit("укажите --input или --sample")
    rows = read_table(path)
    items = []
    for r in rows:
        p = max(1, min(5, int(num(get(r, "вероятность"), 1) or 1)))
        s = max(1, min(5, int(num(get(r, "тяжесть"), 1) or 1)))
        items.append(dict(n=get(r, "риск", default="—"), c=get(r, "категория", default=""), p=p, s=s, lv=LEVEL[(p, s)],
                          who=get(r, "владелец", default=""), m=str(get(r, "мера", default="")).strip()))
    order = {"КРИТИЧЕСКИЙ": 0, "ВЫСОКИЙ": 1, "СРЕДНИЙ": 2, "НИЗКИЙ": 3}
    items.sort(key=lambda i: (order[i["lv"]], -i["p"] * i["s"]))
    out = ["# Реестр рисков: матрица 5×5", ""]
    grid = [["**Вероятность ↓ / Тяжесть →**", "1", "2", "3", "4", "5"]]
    for p in range(5, 0, -1):
        line = [str(p)]
        for s in range(1, 6):
            names = [str(idx + 1) for idx, i in enumerate(items) if i["p"] == p and i["s"] == s]
            line.append(SHORT[LEVEL[(p, s)]] + (" [" + ",".join(names) + "]" if names else ""))
        grid.append(line)
    out.append(md_table(grid[0], grid[1:]))
    out.append("")
    out.append(md_table(["#", "Риск", "Категория", "В", "Т", "Уровень", "Владелец", "Мера"],
                        [[k + 1, i["n"], i["c"], i["p"], i["s"], i["lv"], i["who"], i["m"] or "**НЕТ**"] for k, i in enumerate(items)]))
    out.append("")
    out.append("_Уровни: КРИТИЧЕСКИЙ — немедленные меры и контроль ГД; ВЫСОКИЙ — план снижения с владельцем и сроком; "
               "СРЕДНИЙ — мониторинг, меры по возможности; НИЗКИЙ — принять, регистрировать. Тяжесть 5 (гибель людей, авария, "
               "остановка завода) всегда не ниже ВЫСОКОГО._")
    emit("\n".join(out), a.out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="mode", required=True)
    f = sp.add_parser("fmea")
    f.add_argument("--input")
    f.add_argument("--out")
    f.add_argument("--sample", action="store_true")
    f.add_argument("--porog-pchr", type=float, default=200)
    m = sp.add_parser("matrica")
    m.add_argument("--input")
    m.add_argument("--out")
    m.add_argument("--sample", action="store_true")
    a = ap.parse_args()
    fmea(a) if a.mode == "fmea" else matrica(a)


if __name__ == "__main__":
    main()
