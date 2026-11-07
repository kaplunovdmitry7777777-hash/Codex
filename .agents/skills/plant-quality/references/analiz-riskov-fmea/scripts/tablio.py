"""Общие функции чтения таблиц (CSV из 1С/Excel, XLSX) и форматирования.
Только стандартная библиотека Python; openpyxl используется, если установлен.
"""
import csv
import io
import os
from datetime import date, datetime


def _norm(h):
    return " ".join(str(h or "").replace("﻿", "").strip().lower().replace("ё", "е").split())


def read_table(path):
    """Читает CSV (utf-8 / cp1251, разделитель ; , или TAB) или XLSX. Возвращает список dict."""
    ext = os.path.splitext(path)[1].lower()
    if ext in (".xlsx", ".xlsm"):
        try:
            import openpyxl
        except ImportError:
            raise SystemExit("Для чтения XLSX нужен openpyxl (pip install openpyxl) или сохраните лист как CSV.")
        wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
        ws = wb.active
        rows = [list(r) for r in ws.iter_rows(values_only=True)]
    else:
        raw = open(path, "rb").read()
        text = None
        for enc in ("utf-8-sig", "cp1251"):
            try:
                text = raw.decode(enc)
                break
            except UnicodeDecodeError:
                continue
        if text is None:
            raise SystemExit("Не удалось определить кодировку файла: " + path)
        first = text.splitlines()[0] if text else ""
        delim = max([";", "\t", ","], key=first.count)
        rows = list(csv.reader(io.StringIO(text), delimiter=delim))
    rows = [r for r in rows if any(str(c or "").strip() for c in r)]
    if not rows:
        return []
    head = [_norm(h) for h in rows[0]]
    out = []
    for r in rows[1:]:
        d = {}
        for i, h in enumerate(head):
            if h:
                d[h] = r[i] if i < len(r) else None
        out.append(d)
    return out


def get(row, *names, default=None):
    """Значение по одному из вариантов названия колонки (регистр/ё не важны)."""
    for n in names:
        v = row.get(_norm(n))
        if v is not None and str(v).strip() != "":
            return v
    return default


def num(v, default=None):
    if v is None:
        return default
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).replace("\xa0", "").replace(" ", "").replace("%", "").replace(",", ".").strip()
    if s in ("", "-", "—"):
        return default
    try:
        return float(s)
    except ValueError:
        return default


def to_date(v):
    if v is None:
        return None
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    s = str(v).strip()[:10]
    for f in ("%d.%m.%Y", "%Y-%m-%d", "%d.%m.%y", "%d/%m/%Y"):
        try:
            return datetime.strptime(s, f).date()
        except ValueError:
            continue
    return None


def fmt(x, d=0):
    """Число с пробелами-разделителями тысяч и запятой: 1 234 567,8"""
    if x is None:
        return "—"
    s = f"{x:,.{d}f}".replace(",", " ").replace(".", ",")
    return s


def pct(x, d=1):
    return "—" if x is None else fmt(x * 100, d) + " %"


def md_table(header, rows):
    out = ["| " + " | ".join(header) + " |", "|" + "|".join(["---"] * len(header)) + "|"]
    for r in rows:
        out.append("| " + " | ".join(str(c) for c in r) + " |")
    return "\n".join(out)


def percentile(vals, p):
    vals = sorted(v for v in vals if v is not None)
    if not vals:
        return None
    k = (len(vals) - 1) * p
    f = int(k)
    c = min(f + 1, len(vals) - 1)
    return vals[f] + (vals[c] - vals[f]) * (k - f)


def write_sample(text, name):
    """Сохраняет встроенный пример во временный CSV и возвращает путь."""
    import tempfile
    p = os.path.join(tempfile.gettempdir(), name)
    with open(p, "w", encoding="utf-8-sig") as f:
        f.write(text)
    return p


def emit(text, out_path=None):
    if out_path:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(text)
        print("Отчёт сохранён: " + out_path)
    else:
        print(text)
