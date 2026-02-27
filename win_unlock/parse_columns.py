import re
from typing import Optional

COLUMNS_RE = re.compile(r'(?<=\s)(?=[A-Z])')

def parse_columns(input: str) -> tuple[list[str], list[list[str]], Optional[int]]:
    lines = input.splitlines()
    if not lines:
        return [], [], None

    header_line = lines[0]

    columns_list = COLUMNS_RE.split(header_line)
    column_names = [col.strip() for col in columns_list]

    column_ranges = []
    i = 0
    for col in columns_list:
        start = i
        end = start + len(col)
        column_ranges.append((start, end))
        i = end
    column_ranges[-1] = (column_ranges[-1][0], None)

    active_index = None
    has_active_column = False

    if columns_list[0] == ' ':
        has_active_column = True

    data = []
    for i, line in enumerate(lines[1:]):
        row = []
        for start, end in column_ranges:
            cell = line[start:end].strip() if end is not None else line[start:].strip()
            row.append(cell)
        data.append(row)

        if has_active_column and row[0] == '>':
            active_index = i

    return column_names, data, active_index
