"""Reusable chart primitives for terminal rendering with Rich.

Provides vertical bar charts, horizontal bar charts, and a single-bar
renderer using Unicode block characters for sub-character precision.
All rendering uses Rich Text objects — no raw ANSI escape codes.
"""

from __future__ import annotations

from rich.console import Console
from rich.text import Text

# 9 levels: empty through full block (8 steps per character row)
BLOCKS = [' ', '▁', '▂', '▃', '▄', '▅', '▆', '▇', '█']

# Doubled versions for vertical bar columns (each bar is 2 chars wide)
PARTIAL_BARS = ['  ', '▁▁', '▂▂', '▃▃', '▄▄', '▅▅', '▆▆', '▇▇']


def bar_str(value: float, max_value: float, width: int, color: str = 'cyan') -> Text:
    """Render a single horizontal bar using Unicode block characters.

    Returns a Rich Text object with fractional-block precision.
    At ``width=30`` each bar has 240 possible lengths (30 * 8 sub-steps).

    Args:
        value: The data value to represent.
        max_value: The value that maps to full ``width``.
        width: Maximum bar length in characters.
        color: Rich color name for the bar fill.
    """
    if max_value <= 0 or value <= 0:
        return Text('')
    ratio = min(value / max_value, 1.0)
    full_blocks = int(ratio * width)
    remainder = (ratio * width) - full_blocks
    partial = BLOCKS[int(remainder * 8)]
    bar = '█' * full_blocks + partial
    result = Text()
    result.append(bar, style=color)
    return result


def format_axis_label(value: float) -> str:
    """Format a Y-axis value with K/M suffixes for compact display."""
    if value >= 1_000_000:
        return f'{value / 1_000_000:.1f}M'
    if value >= 1_000:
        return f'{value / 1_000:.0f}k'
    if value == int(value):
        return str(int(value))
    return f'{value:.1f}'


def vertical_bars(
    title: str,
    labels: list[str],
    values: list[float],
    *,
    color: str = 'cyan',
    height: int = 12,
    second_values: list[float] | None = None,
    second_color: str = 'magenta',
    console: Console | None = None,
) -> None:
    """Render a vertical bar chart with optional dual series.

    Each bar is 2 characters wide with 8-level partial blocks for the
    topmost row, giving effective vertical resolution of ``height * 8``.

    Args:
        title: Chart title (supports Rich markup).
        labels: X-axis labels (one per bar).
        values: Primary series data values.
        color: Rich color for the primary series.
        height: Number of character rows for the tallest bar.
        second_values: Optional second series (rendered adjacent).
        second_color: Rich color for the second series.
        console: Rich Console to print to (created if not provided).
    """
    con = console or Console()
    all_vals = values.copy()
    if second_values:
        all_vals.extend(second_values)
    max_val = max(all_vals) if all_vals else 0
    if max_val <= 0:
        return

    con.print(f'\n  [bold]{title}[/bold]')

    for row in range(height, 0, -1):
        # Y-axis label at top, middle, and bottom
        if row == height:
            label = format_axis_label(max_val)
        elif row == height // 2:
            label = format_axis_label(max_val / 2)
        elif row == 1:
            label = '0'
        else:
            label = ''

        line = Text(f'  {label:>5} │ ', style='dim')

        for i, v in enumerate(values):
            _append_bar_cell(line, v, max_val, height, row, color)

            if second_values:
                _append_bar_cell(line, second_values[i], max_val, height, row, second_color)

            line.append(' ')

        con.print(line)

    # X-axis line
    bar_width = 3 if not second_values else 5
    axis_width = len(values) * bar_width + len(values) - 1
    con.print(f'        └{"─" * (axis_width + 2)}')

    # X-axis labels
    label_line = Text('         ')
    for lbl in labels:
        short = lbl[:4]
        if second_values:
            label_line.append(f'{short:<5}', style='dim')
        else:
            label_line.append(f'{short:<3}', style='dim')
    con.print(label_line)


def horizontal_bars(
    title: str,
    labels: list[str],
    values: list[float],
    *,
    color: str = 'yellow',
    bar_width: int = 35,
    value_format: str = '.1f',
    value_suffix: str = '',
    console: Console | None = None,
) -> None:
    """Render horizontal bars with labels and value annotations.

    Args:
        title: Chart title (supports Rich markup).
        labels: Row labels (left-aligned to the longest).
        values: Data values (one per row).
        color: Rich color for bar fill.
        bar_width: Maximum bar width in characters.
        value_format: Format spec for the value annotation.
        value_suffix: Suffix appended to each value (e.g. "s", "%").
        console: Rich Console to print to (created if not provided).
    """
    con = console or Console()
    max_val = max(values) if values else 0
    max_label_len = max((len(lbl) for lbl in labels), default=0)

    con.print(f'\n  [bold]{title}[/bold]')
    for label, value in zip(labels, values, strict=False):
        line = Text(f'    {label:>{max_label_len}}  ')
        line.append_text(bar_str(value, max_val, bar_width, color))
        line.append(f'  {value:{value_format}}{value_suffix}', style='dim')
        con.print(line)


def _append_bar_cell(
    line: Text,
    value: float,
    max_val: float,
    height: int,
    row: int,
    color: str,
) -> None:
    """Append one 2-char-wide bar cell to a Text line for a given row."""
    bar_height = (value / max_val) * height
    if bar_height >= row:
        line.append('██', style=color)
    elif bar_height > row - 1:
        frac = bar_height - (row - 1)
        idx = min(int(frac * 8), 7)
        line.append(PARTIAL_BARS[idx], style=color)
    else:
        line.append('  ')
