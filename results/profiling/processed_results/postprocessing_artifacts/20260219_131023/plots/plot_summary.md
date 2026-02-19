# Profiling plots summary / Сводка графиков профилирования

Source analysis directory / Исходная директория анализа: `results/profiling/processed_results/postprocessing_analysis/20260219_074831`

## English
Generated plots:
- `cpu_absolute_heatmap.png` — absolute CPU stage timings (ms).
- `cpu_relative_heatmap.png` — relative CPU speedup vs reference (x).
- `speedup_grouped_bar.png` — grouped speedup bars by stage (CPU).
- `memory_absolute_heatmap.png` — absolute memory peak by stage (MB).
- `memory_relative_heatmap.png` — relative memory ratio vs reference (x).
- `memory_efficiency_grouped_bar.png` — grouped memory efficiency bars (`ref/lib`).
- `line_bottlenecks_library_sorted_by_line.png` — line bottlenecks for selected library, sorted by stage → file → line, with stage colors and full code line labels.
- `line_timing_by_library_subplots.png` — one subplot per library, sorted by stage → file → line with code labels.
- Line-library focus: `our`.

## Русский
Сформированные графики:
- `cpu_absolute_heatmap.png` — абсолютные CPU-тайминги по этапам (мс).
- `cpu_relative_heatmap.png` — относительное ускорение CPU относительно эталона (x).
- `speedup_grouped_bar.png` — группированный график ускорения по этапам (CPU).
- `memory_absolute_heatmap.png` — абсолютные пиковые значения памяти по этапам (МБ).
- `memory_relative_heatmap.png` — относительное потребление памяти к эталону (x).
- `memory_efficiency_grouped_bar.png` — группированный график эффективности памяти (`ref/lib`).
- `line_bottlenecks_library_sorted_by_line.png` — узкие места по строкам для выбранной библиотеки: цвет зависит от этапа, подпись содержит полный код строки, сортировка: этап → файл → строка.
- `line_timing_by_library_subplots.png` — отдельные подграфики по библиотекам, сортировка: этап → файл → строка, с подписями строк кода.
- Фокус по библиотеке для строк: `our`.
