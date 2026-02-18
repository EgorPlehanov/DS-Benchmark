# Postprocessing analysis of profiling runs
_Постобработка результатов профилирования_

Reference library: `our`
Path filter mode: `library_only`
Support source: `derived_from_test_results:results\profiling\our\20260218_043814`

## CPU
_Процессорное время (CPU)_

### Stage timings from CPU profiler metadata (mean per repeat, ms)
_Тайминги этапов из метаданных CPU-профайлера (среднее на повтор, мс)_

| Library | Step1 | Step2 | Step3 | Step4 |
|---|---:|---:|---:|---:|
| dstpy | 213.17 | 56.28 | 163.26 | 84.42 |
| dstz | 139.09 | 128.55 | 651.08 | n/s |
| our | 106.54 | 30.78 | 70.58 | 39.18 |
| pyds | 84.16 | 51.32 | n/s | n/s |

### Mean step repeat count captured from CPU metadata
_Среднее число повторов этапа из метаданных CPU_

| Library | Step1 | Step2 | Step3 | Step4 |
|---|---:|---:|---:|---:|
| dstpy | 10.00 | 10.00 | 10.00 | 10.00 |
| dstz | 10.00 | 10.00 | 10.00 | n/s |
| our | 10.00 | 10.00 | 10.00 | 10.00 |
| pyds | 10.00 | 10.00 | n/s | n/s |

### Relative speedup vs reference (reference_time / lib_time)
_Относительное ускорение относительно эталона (time_ref / time_lib)_

| Library | Step1 | Step2 | Step3 | Step4 |
|---|---:|---:|---:|---:|
| dstpy | 0.50x | 0.55x | 0.43x | 0.46x |
| dstz | 0.77x | 0.24x | 0.11x | n/s |
| our | 1.00x | 1.00x | 1.00x | 1.00x |
| pyds | 1.27x | 0.60x | n/s | n/s |

## Memory
_Память_

### Peak memory by stage (MB)
_Пиковое потребление памяти по этапам (МБ)_

| Library | Step1 | Step2 | Step3 | Step4 |
|---|---:|---:|---:|---:|
| dstpy | 0.22 | 0.16 | 0.22 | 0.16 |
| dstz | 0.24 | 0.18 | 0.22 | n/s |
| our | 0.20 | 0.14 | 0.20 | 0.14 |
| pyds | 0.20 | 0.16 | n/s | n/s |

### Relative memory vs reference (lib_peak / ref_peak)
_Относительная память относительно эталона (peak_lib / peak_ref)_

| Library | Step1 | Step2 | Step3 | Step4 |
|---|---:|---:|---:|---:|
| dstpy | 1.08x | 1.16x | 1.08x | 1.11x |
| dstz | 1.19x | 1.32x | 1.09x | n/s |
| our | 1.00x | 1.00x | 1.00x | 1.00x |
| pyds | 0.98x | 1.14x | n/s | n/s |

## Line
_Построчный профиль (line profiler)_

### Bottlenecks from line profiler (filtered, supported stages only)
_Узкие места из line profiler (после фильтрации, только поддерживаемые этапы)_

| Library | Stage | File:Line | Total time (s) | Hits | Code |
|---|---|---|---:|---:|---|
| dstpy | step1 | `external/dst-py/src/dempster_shafer/core/mass_function.py:75` | 0.6601 | 5760 | `self[_convert_to_frozenset(h)] = float(v)` |
| dstpy | step1 | `external/dst-py/src/dempster_shafer/core/mass_function.py:191` | 0.3059 | 6250 | `return sum(m for h, m in self.items() if h.intersection(hypothesis))` |
| dstpy | step1 | `external/dst-py/src/dempster_shafer/core/mass_function.py:171` | 0.2874 | 6040 | `return sum(m for h, m in self.items() if h.issubset(hypothesis))` |
| dstpy | step1 | `external/dst-py/src/dempster_shafer/core/mass_function.py:85` | 0.1942 | 1920 | `if not self.is_normalized():` |
| dstpy | step1 | `external/dst-py/src/dempster_shafer/core/mass_function.py:66` | 0.1904 | 1920 | `self.frame = Frame(frame)` |
| dstpy | step2 | `external/dst-py/src/dempster_shafer/core/mass_function.py:236` | 0.0760 | 40 | `return combine_conjunctive(self, other, normalization=normalization)` |
| dstpy | step2 | `external/dst-py/src/dempster_shafer/core/mass_function.py:66` | 0.0660 | 700 | `self.frame = Frame(frame)` |
| dstpy | step2 | `external/dst-py/src/dempster_shafer/core/mass_function.py:75` | 0.0634 | 590 | `self[_convert_to_frozenset(h)] = float(v)` |
| dstpy | step2 | `external/dst-py/src/dempster_shafer/core/mass_function.py:191` | 0.0502 | 1140 | `return sum(m for h, m in self.items() if h.intersection(hypothesis))` |
| dstpy | step2 | `external/dst-py/src/dempster_shafer/core/mass_function.py:171` | 0.0490 | 1140 | `return sum(m for h, m in self.items() if h.issubset(hypothesis))` |
| dstpy | step3 | `external/dst-py/src/dempster_shafer/core/mass_function.py:75` | 0.8450 | 7550 | `self[_convert_to_frozenset(h)] = float(v)` |
| dstpy | step3 | `external/dst-py/src/dempster_shafer/core/mass_function.py:191` | 0.2594 | 5150 | `return sum(m for h, m in self.items() if h.intersection(hypothesis))` |
| dstpy | step3 | `external/dst-py/src/dempster_shafer/core/mass_function.py:86` | 0.2270 | 320 | `self.normalize()` |
| dstpy | step3 | `external/dst-py/src/dempster_shafer/core/mass_function.py:171` | 0.2226 | 4640 | `return sum(m for h, m in self.items() if h.issubset(hypothesis))` |
| dstpy | step3 | `external/dst-py/src/dempster_shafer/core/mass_function.py:236` | 0.2092 | 40 | `return combine_conjunctive(self, other, normalization=normalization)` |
| dstpy | step4 | `external/dst-py/src/dempster_shafer/core/mass_function.py:75` | 0.3181 | 2880 | `self[_convert_to_frozenset(h)] = float(v)` |
| dstpy | step4 | `external/dst-py/src/dempster_shafer/core/mass_function.py:191` | 0.1305 | 2720 | `return sum(m for h, m in self.items() if h.intersection(hypothesis))` |
| dstpy | step4 | `external/dst-py/src/dempster_shafer/core/mass_function.py:171` | 0.1074 | 2350 | `return sum(m for h, m in self.items() if h.issubset(hypothesis))` |
| dstpy | step4 | `external/dst-py/src/dempster_shafer/core/mass_function.py:73` | 0.0836 | 3620 | `for h, v in masses.items():` |
| dstpy | step4 | `external/dst-py/src/dempster_shafer/core/mass_function.py:21` | 0.0820 | 3520 | `if isinstance(item, frozenset):` |
| dstz | step1 | `external/dstz/dstz/core/distribution.py:74` | 0.4352 | 770 | `return super(Evidence, self).__getitem__(item)` |
| dstz | step1 | `external/dstz/dstz/math/func.py:19` | 0.3571 | 490 | `res += ev[key]` |
| dstz | step1 | `external/dstz/dstz/math/func.py:63` | 0.2064 | 280 | `res += ev[key]` |
| dstz | step1 | `external/dstz/dstz/core/atom.py:68` | 0.1817 | 770 | `if not isinstance(value, Hashable):` |
| dstz | step1 | `external/dstz/dstz/core/atom.py:91` | 0.1804 | 1920 | `super(Element, self).__init__()` |
| dstz | step2 | `external/dstz/dstz/evpiece/dual.py:33` | 0.6910 | 210 | `res[key] += ev1[key1] * ev2[key2]` |
| dstz | step2 | `external/dstz/dstz/core/distribution.py:74` | 0.5464 | 900 | `return super(Evidence, self).__getitem__(item)` |
| dstz | step2 | `external/dstz/dstz/core/distribution.py:55` | 0.4630 | 670 | `super(Evidence, self).__setitem__(key, value)` |
| dstz | step2 | `external/dstz/dstz/core/atom.py:68` | 0.4460 | 1910 | `if not isinstance(value, Hashable):` |
| dstz | step2 | `external/dstz/dstz/core/atom.py:66` | 0.2298 | 3820 | `for attr in self.idattr:` |
| dstz | step3 | `external/dstz/dstz/core/distribution.py:55` | 4.7900 | 8530 | `super(Evidence, self).__setitem__(key, value)` |
| dstz | step3 | `external/dstz/dstz/core/atom.py:68` | 2.9859 | 13580 | `if not isinstance(value, Hashable):` |
| dstz | step3 | `external/dstz/dstz/core/distribution.py:74` | 2.2570 | 3990 | `return super(Evidence, self).__getitem__(item)` |
| dstz | step3 | `external/dstz/dstz/evpiece/dual.py:33` | 1.7857 | 550 | `res[key] += ev1[key1] * ev2[key2]` |
| dstz | step3 | `external/dstz/dstz/core/atom.py:66` | 1.6038 | 27160 | `for attr in self.idattr:` |
| our | step1 | `src/core/dempster_core.py:43` | 0.3550 | 6250 | `return sum(mass for subset, mass in bpa.items() if subset.intersection(event_fs))` |
| our | step1 | `src/core/dempster_core.py:38` | 0.3298 | 6040 | `return sum(mass for subset, mass in bpa.items() if subset.issubset(event_fs))` |
| our | step1 | `src/core/dempster_core.py:11` | 0.0467 | 1920 | `self.frame = frame_of_discernment` |
| our | step1 | `src/core/dempster_core.py:10` | 0.0354 | 1920 | `def __init__(self, frame_of_discernment: Set[str]):` |
| our | step1 | `src/core/dempster_core.py:42` | 0.0140 | 480 | `event_fs = frozenset(event)` |
| our | step2 | `src/core/dempster_core.py:43` | 0.0496 | 1140 | `return sum(mass for subset, mass in bpa.items() if subset.intersection(event_fs))` |
| our | step2 | `src/core/dempster_core.py:38` | 0.0492 | 1140 | `return sum(mass for subset, mass in bpa.items() if subset.issubset(event_fs))` |
| our | step2 | `src/core/dempster_core.py:11` | 0.0129 | 660 | `self.frame = frame_of_discernment` |
| our | step2 | `src/core/dempster_core.py:10` | 0.0106 | 660 | `def __init__(self, frame_of_discernment: Set[str]):` |
| our | step3 | `src/core/dempster_core.py:43` | 0.3143 | 5150 | `return sum(mass for subset, mass in bpa.items() if subset.intersection(event_fs))` |
| our | step3 | `src/core/dempster_core.py:38` | 0.2691 | 4640 | `return sum(mass for subset, mass in bpa.items() if subset.issubset(event_fs))` |
| our | step3 | `src/core/dempster_core.py:50` | 0.0294 | 1200 | `for s2, m2 in bpa2.items():` |
| our | step3 | `src/core/dempster_core.py:60` | 0.0288 | 1200 | `for s2, m2 in bpa2.items():` |
| our | step3 | `src/core/dempster_core.py:51` | 0.0258 | 960 | `if s1.isdisjoint(s2):` |
| our | step4 | `src/core/dempster_core.py:43` | 0.1530 | 2720 | `return sum(mass for subset, mass in bpa.items() if subset.intersection(event_fs))` |
| our | step4 | `src/core/dempster_core.py:38` | 0.1202 | 2350 | `return sum(mass for subset, mass in bpa.items() if subset.issubset(event_fs))` |
| our | step4 | `src/core/dempster_core.py:11` | 0.0146 | 660 | `self.frame = frame_of_discernment` |
| pyds | step1 | `external/py_dempster_shafer/pyds.py:254` | 0.1072 | 3840 | `return fsum([v for (h, v) in self.items() if h and hypothesis.issuperset(h)])` |
| pyds | step1 | `external/py_dempster_shafer/pyds.py:271` | 0.1060 | 3840 | `return fsum([v for (h, v) in self.items() if hypothesis & h])` |
| pyds | step1 | `external/py_dempster_shafer/pyds.py:267` | 0.1032 | 960 | `hypothesis = MassFunction._convert(hypothesis)` |
| pyds | step1 | `external/py_dempster_shafer/pyds.py:250` | 0.1031 | 960 | `hypothesis = MassFunction._convert(hypothesis)` |
| pyds | step1 | `external/py_dempster_shafer/pyds.py:52` | 0.0443 | 1920 | `if isinstance(hypothesis, frozenset):` |
| pyds | step2 | `external/py_dempster_shafer/pyds.py:355` | 0.2003 | 640 | `return self._combine(mass_function, rule=lambda s1, s2: s1 & s2, normalization=normalization, sample_count=sample_count, importance_sampling=importance_sampling)` |
| pyds | step2 | `external/py_dempster_shafer/pyds.py:395` | 0.1469 | 40 | `combined = combined._combine_deterministic(m, rule)` |
| pyds | step2 | `external/py_dempster_shafer/pyds.py:47` | 0.1383 | 320 | `self[h] += v` |
| pyds | step2 | `external/py_dempster_shafer/pyds.py:411` | 0.1278 | 300 | `combined[rule(h1, h2)] += v1 * v2` |
| pyds | step2 | `external/py_dempster_shafer/pyds.py:173` | 0.0990 | 620 | `return dict.__getitem__(self, MassFunction._convert(hypothesis))` |

## Coverage
_Покрытие и валидность сравнений_

### Stage support matrix
_Матрица поддержки этапов_

| Library | Step1 | Step2 | Step3 | Step4 |
|---|---|---|---|---|
| dstpy | supported | supported | supported | supported |
| dstz | supported | supported | supported | not_supported |
| our | supported | supported | supported | supported |
| pyds | supported | supported | not_supported | not_supported |

### Profiler duration coverage (profiling overhead)
_Покрытие длительностей профайлеров (накладные расходы профилирования)_

| Library | Profiler | Stage | Support | Samples | Mean duration (ms) | Std (ms) |
|---|---|---|---|---:|---:|---:|
| dstpy | cpu | step1 | supported | 2 | 2131.66 | 63.49 |
| dstpy | cpu | step2 | supported | 2 | 562.76 | 51.78 |
| dstpy | cpu | step3 | supported | 2 | 1632.62 | 78.19 |
| dstpy | cpu | step4 | supported | 2 | 844.18 | 12.65 |
| dstpy | line | step1 | supported | 2 | 2925.83 | 254.39 |
| dstpy | line | step2 | supported | 2 | 1266.62 | 37.23 |
| dstpy | line | step3 | supported | 2 | 2451.60 | 88.40 |
| dstpy | line | step4 | supported | 2 | 1518.58 | 28.28 |
| dstpy | memory | step1 | supported | 2 | 2410.44 | 114.38 |
| dstpy | memory | step2 | supported | 2 | 825.25 | 37.49 |
| dstpy | memory | step3 | supported | 2 | 1909.22 | 80.15 |
| dstpy | memory | step4 | supported | 2 | 1094.13 | 27.02 |
| dstpy | scalene | step1 | supported | 2 | 0.00 | 0.00 |
| dstpy | scalene | step2 | supported | 2 | 0.00 | 0.00 |
| dstpy | scalene | step3 | supported | 2 | 0.00 | 0.00 |
| dstpy | scalene | step4 | supported | 2 | 0.00 | 0.00 |
| dstz | cpu | step1 | supported | 2 | 1390.93 | 18.90 |
| dstz | cpu | step2 | supported | 2 | 1285.50 | 404.13 |
| dstz | cpu | step3 | supported | 2 | 6510.84 | 417.99 |
| dstz | cpu | step4 | not_supported (instrumentation only / excluded from comparison) | 2 | 1.38 | 0.47 |
| dstz | line | step1 | supported | 2 | 2287.38 | 144.81 |
| dstz | line | step2 | supported | 2 | 2017.76 | 442.68 |
| dstz | line | step3 | supported | 2 | 7389.39 | 411.02 |
| dstz | line | step4 | not_supported (instrumentation only / excluded from comparison) | 2 | 355.62 | 50.84 |
| dstz | memory | step1 | supported | 2 | 1676.95 | 67.08 |
| dstz | memory | step2 | supported | 2 | 1557.49 | 416.79 |
| dstz | memory | step3 | supported | 2 | 6811.68 | 417.01 |
| dstz | memory | step4 | not_supported (instrumentation only / excluded from comparison) | 2 | 151.96 | 22.34 |
| dstz | scalene | step1 | supported | 2 | 0.00 | 0.00 |
| dstz | scalene | step2 | supported | 2 | 0.00 | 0.00 |
| dstz | scalene | step3 | supported | 2 | 0.00 | 0.00 |
| dstz | scalene | step4 | not_supported (instrumentation only / excluded from comparison) | 2 | 0.00 | 0.00 |
| our | cpu | step1 | supported | 2 | 1065.44 | 127.30 |
| our | cpu | step2 | supported | 2 | 307.82 | 1.17 |
| our | cpu | step3 | supported | 2 | 705.76 | 102.30 |
| our | cpu | step4 | supported | 2 | 391.79 | 43.74 |
| our | line | step1 | supported | 2 | 1851.92 | 2.44 |
| our | line | step2 | supported | 2 | 896.22 | 24.16 |
| our | line | step3 | supported | 2 | 1521.86 | 180.94 |
| our | line | step4 | supported | 2 | 1112.68 | 134.49 |
| our | memory | step1 | supported | 2 | 1347.55 | 110.44 |
| our | memory | step2 | supported | 2 | 521.55 | 7.18 |
| our | memory | step3 | supported | 2 | 992.12 | 137.95 |
| our | memory | step4 | supported | 2 | 666.83 | 84.23 |
| our | scalene | step1 | supported | 2 | 0.00 | 0.00 |
| our | scalene | step2 | supported | 2 | 0.00 | 0.00 |
| our | scalene | step3 | supported | 2 | 0.00 | 0.00 |
| our | scalene | step4 | supported | 2 | 0.00 | 0.00 |
| pyds | cpu | step1 | supported | 2 | 841.56 | 36.26 |
| pyds | cpu | step2 | supported | 2 | 513.23 | 114.14 |
| pyds | cpu | step3 | not_supported (instrumentation only / excluded from comparison) | 2 | 1.17 | 0.00 |
| pyds | cpu | step4 | not_supported (instrumentation only / excluded from comparison) | 2 | 0.90 | 0.12 |
| pyds | line | step1 | supported | 2 | 1542.39 | 210.38 |
| pyds | line | step2 | supported | 2 | 1180.13 | 142.79 |
| pyds | line | step3 | not_supported (instrumentation only / excluded from comparison) | 2 | 332.06 | 0.07 |
| pyds | line | step4 | not_supported (instrumentation only / excluded from comparison) | 2 | 286.29 | 0.87 |
| pyds | memory | step1 | supported | 2 | 1079.91 | 88.02 |
| pyds | memory | step2 | supported | 2 | 758.19 | 125.99 |
| pyds | memory | step3 | not_supported (instrumentation only / excluded from comparison) | 2 | 137.31 | 0.40 |
| pyds | memory | step4 | not_supported (instrumentation only / excluded from comparison) | 2 | 118.28 | 0.38 |
| pyds | scalene | step1 | supported | 2 | 0.00 | 0.00 |
| pyds | scalene | step2 | supported | 2 | 0.00 | 0.00 |
| pyds | scalene | step3 | not_supported (instrumentation only / excluded from comparison) | 2 | 0.00 | 0.00 |
| pyds | scalene | step4 | not_supported (instrumentation only / excluded from comparison) | 2 | 0.00 | 0.00 |
