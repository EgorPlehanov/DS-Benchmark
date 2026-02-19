# Postprocessing analysis of profiling runs
_Постобработка результатов профилирования_

Reference library: `our`
Path filter mode: `library_only`
Support source: `derived_from_test_results:results\profiling\our\20260219_061335`

## CPU
_Процессорное время (CPU)_

### Stage timings from CPU profiler metadata (mean per repeat, ms)
_Тайминги этапов из метаданных CPU-профайлера (среднее на повтор, мс)_

| Library | Step1 | Step2 | Step3 | Step4 |
|---|---:|---:|---:|---:|
| dstpy | 93.46 | 41.39 | 88.91 | 52.02 |
| dstz | 70.97 | 112.05 | 334.88 | n/s |
| our | 46.16 | 19.91 | 38.45 | 23.48 |
| pyds | 40.89 | 44.55 | n/s | n/s |

### Mean step repeat count captured from CPU metadata
_Среднее число повторов этапа из метаданных CPU_

| Library | Step1 | Step2 | Step3 | Step4 |
|---|---:|---:|---:|---:|
| dstpy | 100.00 | 100.00 | 100.00 | 100.00 |
| dstz | 100.00 | 100.00 | 100.00 | n/s |
| our | 100.00 | 100.00 | 100.00 | 100.00 |
| pyds | 100.00 | 100.00 | n/s | n/s |

### Relative speedup vs reference (reference_time / lib_time)
_Относительное ускорение относительно эталона (time_ref / time_lib)_

| Library | Step1 | Step2 | Step3 | Step4 |
|---|---:|---:|---:|---:|
| dstpy | 0.49x | 0.48x | 0.43x | 0.45x |
| dstz | 0.65x | 0.18x | 0.11x | n/s |
| our | 1.00x | 1.00x | 1.00x | 1.00x |
| pyds | 1.13x | 0.45x | n/s | n/s |

## Memory
_Память_

### Peak memory by stage (MB)
_Пиковое потребление памяти по этапам (МБ)_

| Library | Step1 | Step2 | Step3 | Step4 |
|---|---:|---:|---:|---:|
| dstpy | 0.14 | 0.16 | 0.21 | 0.15 |
| dstz | 0.14 | 0.19 | 0.22 | n/s |
| our | 0.13 | 0.13 | 0.20 | 0.14 |
| pyds | 0.13 | 0.15 | n/s | n/s |

### Relative memory vs reference (lib_peak / ref_peak)
_Относительная память относительно эталона (peak_lib / peak_ref)_

| Library | Step1 | Step2 | Step3 | Step4 |
|---|---:|---:|---:|---:|
| dstpy | 1.05x | 1.18x | 1.08x | 1.11x |
| dstz | 1.10x | 1.40x | 1.09x | n/s |
| our | 1.00x | 1.00x | 1.00x | 1.00x |
| pyds | 0.97x | 1.15x | n/s | n/s |

## Line
_Построчный профиль (line profiler)_

### Bottlenecks from line profiler (filtered, supported stages only)
_Узкие места из line profiler (после фильтрации, только поддерживаемые этапы)_

| Library | Stage | File:Line | Total time (s) | Hits | Code |
|---|---|---|---:|---:|---|
| dstpy | step1 | `external/dst-py/src/dempster_shafer/core/mass_function.py:75` | 40.8034 | 365800 | `self[_convert_to_frozenset(h)] = float(v)` |
| dstpy | step1 | `external/dst-py/src/dempster_shafer/core/mass_function.py:191` | 24.8572 | 514200 | `return sum(m for h, m in self.items() if h.intersection(hypothesis))` |
| dstpy | step1 | `external/dst-py/src/dempster_shafer/core/mass_function.py:171` | 23.4059 | 500400 | `return sum(m for h, m in self.items() if h.issubset(hypothesis))` |
| dstpy | step1 | `external/dst-py/src/dempster_shafer/core/mass_function.py:85` | 12.6073 | 128400 | `if not self.is_normalized():` |
| dstpy | step1 | `external/dst-py/src/dempster_shafer/core/mass_function.py:66` | 12.2406 | 128400 | `self.frame = Frame(frame)` |
| dstpy | step2 | `external/dst-py/src/dempster_shafer/core/mass_function.py:75` | 12.7219 | 112400 | `self[_convert_to_frozenset(h)] = float(v)` |
| dstpy | step2 | `external/dst-py/src/dempster_shafer/core/mass_function.py:236` | 12.1647 | 5200 | `return combine_conjunctive(self, other, normalization=normalization)` |
| dstpy | step2 | `external/dst-py/src/dempster_shafer/core/mass_function.py:191` | 7.0122 | 146200 | `return sum(m for h, m in self.items() if h.intersection(hypothesis))` |
| dstpy | step2 | `external/dst-py/src/dempster_shafer/core/mass_function.py:171` | 6.7314 | 143100 | `return sum(m for h, m in self.items() if h.issubset(hypothesis))` |
| dstpy | step2 | `external/dst-py/src/dempster_shafer/core/mass_function.py:66` | 6.4797 | 66300 | `self.frame = Frame(frame)` |
| dstpy | step3 | `external/dst-py/src/dempster_shafer/core/mass_function.py:75` | 59.3468 | 528700 | `self[_convert_to_frozenset(h)] = float(v)` |
| dstpy | step3 | `external/dst-py/src/dempster_shafer/core/mass_function.py:236` | 22.7718 | 5200 | `return combine_conjunctive(self, other, normalization=normalization)` |
| dstpy | step3 | `external/dst-py/src/dempster_shafer/core/mass_function.py:191` | 19.9308 | 391200 | `return sum(m for h, m in self.items() if h.intersection(hypothesis))` |
| dstpy | step3 | `external/dst-py/src/dempster_shafer/core/mass_function.py:86` | 19.1483 | 34300 | `self.normalize()` |
| dstpy | step3 | `external/dst-py/src/dempster_shafer/core/mass_function.py:171` | 16.8649 | 345900 | `return sum(m for h, m in self.items() if h.issubset(hypothesis))` |
| dstpy | step4 | `external/dst-py/src/dempster_shafer/core/mass_function.py:75` | 25.7727 | 229100 | `self[_convert_to_frozenset(h)] = float(v)` |
| dstpy | step4 | `external/dst-py/src/dempster_shafer/core/mass_function.py:191` | 11.7893 | 236300 | `return sum(m for h, m in self.items() if h.intersection(hypothesis))` |
| dstpy | step4 | `external/dst-py/src/dempster_shafer/combination/advanced.py:75` | 11.5754 | 5200 | `combined = combine_conjunctive(m1, m2, normalization=False)` |
| dstpy | step4 | `external/dst-py/src/dempster_shafer/core/mass_function.py:171` | 9.8620 | 207000 | `return sum(m for h, m in self.items() if h.issubset(hypothesis))` |
| dstpy | step4 | `external/dst-py/src/dempster_shafer/core/mass_function.py:73` | 7.3590 | 306800 | `for h, v in masses.items():` |
| dstz | step1 | `external/dstz/dstz/core/distribution.py:74` | 53.1509 | 103400 | `return super(Evidence, self).__getitem__(item)` |
| dstz | step1 | `external/dstz/dstz/math/func.py:19` | 41.1665 | 62100 | `res += ev[key]` |
| dstz | step1 | `external/dstz/dstz/math/func.py:63` | 27.5114 | 41300 | `res += ev[key]` |
| dstz | step1 | `external/dstz/dstz/core/atom.py:68` | 22.1566 | 103400 | `if not isinstance(value, Hashable):` |
| dstz | step1 | `external/dstz/dstz/core/atom.py:91` | 12.9608 | 152200 | `super(Element, self).__init__()` |
| dstz | step2 | `external/dstz/dstz/evpiece/dual.py:33` | 88.3769 | 28100 | `res[key] += ev1[key1] * ev2[key2]` |
| dstz | step2 | `external/dstz/dstz/core/distribution.py:74` | 86.7367 | 154500 | `return super(Evidence, self).__getitem__(item)` |
| dstz | step2 | `external/dstz/dstz/core/distribution.py:55` | 79.8889 | 136000 | `super(Evidence, self).__setitem__(key, value)` |
| dstz | step2 | `external/dstz/dstz/core/atom.py:68` | 73.2297 | 340000 | `if not isinstance(value, Hashable):` |
| dstz | step2 | `external/dstz/dstz/core/atom.py:66` | 38.0905 | 680000 | `for attr in self.idattr:` |
| dstz | step3 | `external/dstz/dstz/core/distribution.py:55` | 350.7114 | 637000 | `super(Evidence, self).__setitem__(key, value)` |
| dstz | step3 | `external/dstz/dstz/core/atom.py:68` | 244.6474 | 1149300 | `if not isinstance(value, Hashable):` |
| dstz | step3 | `external/dstz/dstz/core/distribution.py:74` | 221.5527 | 401400 | `return super(Evidence, self).__getitem__(item)` |
| dstz | step3 | `external/dstz/dstz/evpiece/dual.py:33` | 180.6948 | 57200 | `res[key] += ev1[key1] * ev2[key2]` |
| dstz | step3 | `external/dstz/dstz/core/atom.py:66` | 130.7635 | 2298600 | `for attr in self.idattr:` |
| our | step1 | `src/core/dempster_core.py:43` | 24.6947 | 514200 | `return sum(mass for subset, mass in bpa.items() if subset.intersection(event_fs))` |
| our | step1 | `src/core/dempster_core.py:38` | 23.3717 | 500400 | `return sum(mass for subset, mass in bpa.items() if subset.issubset(event_fs))` |
| our | step1 | `src/core/dempster_core.py:11` | 3.2167 | 152200 | `self.frame = frame_of_discernment` |
| our | step1 | `src/core/dempster_core.py:10` | 2.4285 | 152200 | `def __init__(self, frame_of_discernment: Set[str]):` |
| our | step1 | `src/core/dempster_core.py:42` | 1.7541 | 76100 | `event_fs = frozenset(event)` |
| our | step2 | `src/core/dempster_core.py:43` | 6.5144 | 136600 | `return sum(mass for subset, mass in bpa.items() if subset.intersection(event_fs))` |
| our | step2 | `src/core/dempster_core.py:38` | 6.1843 | 133500 | `return sum(mass for subset, mass in bpa.items() if subset.issubset(event_fs))` |
| our | step2 | `src/core/dempster_core.py:11` | 1.1821 | 56300 | `self.frame = frame_of_discernment` |
| our | step2 | `src/core/dempster_core.py:60` | 1.0066 | 47300 | `for s2, m2 in bpa2.items():` |
| our | step2 | `src/core/dempster_core.py:50` | 0.9550 | 45700 | `for s2, m2 in bpa2.items():` |
| our | step3 | `src/core/dempster_core.py:43` | 20.1797 | 391200 | `return sum(mass for subset, mass in bpa.items() if subset.intersection(event_fs))` |
| our | step3 | `src/core/dempster_core.py:38` | 17.0100 | 345900 | `return sum(mass for subset, mass in bpa.items() if subset.issubset(event_fs))` |
| our | step3 | `src/core/dempster_core.py:60` | 2.3472 | 106700 | `for s2, m2 in bpa2.items():` |
| our | step3 | `src/core/dempster_core.py:50` | 2.3447 | 108700 | `for s2, m2 in bpa2.items():` |
| our | step3 | `src/core/dempster_core.py:51` | 1.9691 | 84500 | `if s1.isdisjoint(s2):` |
| our | step4 | `src/core/dempster_core.py:43` | 12.1907 | 242500 | `return sum(mass for subset, mass in bpa.items() if subset.intersection(event_fs))` |
| our | step4 | `src/core/dempster_core.py:38` | 10.0091 | 210400 | `return sum(mass for subset, mass in bpa.items() if subset.issubset(event_fs))` |
| our | step4 | `src/core/dempster_core.py:11` | 1.3681 | 63800 | `self.frame = frame_of_discernment` |
| our | step4 | `src/core/dempster_core.py:113` | 1.2364 | 58300 | `for s2, m2 in bpa2.items():` |
| our | step4 | `src/core/dempster_core.py:10` | 0.8356 | 52000 | `def __init__(self, frame_of_discernment: Set[str]):` |
| pyds | step1 | `external/py_dempster_shafer/pyds.py:254` | 8.2220 | 299900 | `return fsum([v for (h, v) in self.items() if h and hypothesis.issuperset(h)])` |
| pyds | step1 | `external/py_dempster_shafer/pyds.py:271` | 8.0857 | 299900 | `return fsum([v for (h, v) in self.items() if hypothesis & h])` |
| pyds | step1 | `external/py_dempster_shafer/pyds.py:267` | 8.0551 | 76100 | `hypothesis = MassFunction._convert(hypothesis)` |
| pyds | step1 | `external/py_dempster_shafer/pyds.py:250` | 7.9338 | 76100 | `hypothesis = MassFunction._convert(hypothesis)` |
| pyds | step1 | `external/py_dempster_shafer/pyds.py:52` | 3.4019 | 152200 | `if isinstance(hypothesis, frozenset):` |
| pyds | step2 | `external/py_dempster_shafer/pyds.py:47` | 35.6693 | 80800 | `self[h] += v` |
| pyds | step2 | `external/py_dempster_shafer/pyds.py:355` | 31.3760 | 94200 | `return self._combine(mass_function, rule=lambda s1, s2: s1 & s2, normalization=normalization, sample_count=sample_count, importance_sampling=importance_sampling)` |
| pyds | step2 | `external/py_dempster_shafer/pyds.py:395` | 22.9827 | 5200 | `combined = combined._combine_deterministic(m, rule)` |
| pyds | step2 | `external/py_dempster_shafer/pyds.py:173` | 21.6365 | 125300 | `return dict.__getitem__(self, MassFunction._convert(hypothesis))` |
| pyds | step2 | `external/py_dempster_shafer/pyds.py:411` | 20.0871 | 44500 | `combined[rule(h1, h2)] += v1 * v2` |

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
| dstpy | cpu | step1 | supported | 32 | 9346.09 | 6547.72 |
| dstpy | cpu | step2 | supported | 32 | 4139.27 | 1517.25 |
| dstpy | cpu | step3 | supported | 32 | 8890.85 | 4387.63 |
| dstpy | cpu | step4 | supported | 32 | 5202.26 | 2156.63 |
| dstpy | line | step1 | supported | 32 | 9921.15 | 6597.21 |
| dstpy | line | step2 | supported | 32 | 4839.73 | 1508.98 |
| dstpy | line | step3 | supported | 32 | 9726.84 | 4389.14 |
| dstpy | line | step4 | supported | 32 | 5881.86 | 2152.09 |
| dstpy | memory | step1 | supported | 32 | 9568.24 | 6558.99 |
| dstpy | memory | step2 | supported | 32 | 4394.12 | 1513.01 |
| dstpy | memory | step3 | supported | 32 | 9168.92 | 4386.43 |
| dstpy | memory | step4 | supported | 32 | 5446.57 | 2153.69 |
| dstpy | scalene | step1 | supported | 0 | 0.00 | 0.00 |
| dstpy | scalene | step2 | supported | 0 | 0.00 | 0.00 |
| dstpy | scalene | step3 | supported | 0 | 0.00 | 0.00 |
| dstpy | scalene | step4 | supported | 0 | 0.00 | 0.00 |
| dstz | cpu | step1 | supported | 32 | 7096.51 | 3080.46 |
| dstz | cpu | step2 | supported | 32 | 11204.69 | 5330.74 |
| dstz | cpu | step3 | supported | 32 | 33488.37 | 16747.47 |
| dstz | cpu | step4 | not_supported (instrumentation only / excluded from comparison) | 32 | 1.04 | 0.17 |
| dstz | line | step1 | supported | 32 | 7716.90 | 3102.87 |
| dstz | line | step2 | supported | 32 | 11944.56 | 5343.15 |
| dstz | line | step3 | supported | 32 | 34352.49 | 16754.78 |
| dstz | line | step4 | not_supported (instrumentation only / excluded from comparison) | 32 | 291.24 | 3.06 |
| dstz | memory | step1 | supported | 32 | 7330.84 | 3080.77 |
| dstz | memory | step2 | supported | 32 | 11480.93 | 5332.44 |
| dstz | memory | step3 | supported | 32 | 33787.46 | 16747.45 |
| dstz | memory | step4 | not_supported (instrumentation only / excluded from comparison) | 32 | 120.43 | 1.93 |
| dstz | scalene | step1 | supported | 0 | 0.00 | 0.00 |
| dstz | scalene | step2 | supported | 0 | 0.00 | 0.00 |
| dstz | scalene | step3 | supported | 0 | 0.00 | 0.00 |
| dstz | scalene | step4 | not_supported (instrumentation only / excluded from comparison) | 0 | 0.00 | 0.00 |
| our | cpu | step1 | supported | 32 | 4616.02 | 2674.08 |
| our | cpu | step2 | supported | 32 | 1990.70 | 1003.42 |
| our | cpu | step3 | supported | 32 | 3845.25 | 1513.99 |
| our | cpu | step4 | supported | 32 | 2348.09 | 1064.97 |
| our | line | step1 | supported | 32 | 5148.88 | 2707.47 |
| our | line | step2 | supported | 32 | 2575.47 | 1029.52 |
| our | line | step3 | supported | 32 | 4578.99 | 1519.41 |
| our | line | step4 | supported | 32 | 2959.71 | 1060.69 |
| our | memory | step1 | supported | 32 | 4821.38 | 2679.97 |
| our | memory | step2 | supported | 32 | 2210.38 | 1010.71 |
| our | memory | step3 | supported | 32 | 4094.36 | 1513.10 |
| our | memory | step4 | supported | 32 | 2576.17 | 1060.84 |
| our | scalene | step1 | supported | 0 | 0.00 | 0.00 |
| our | scalene | step2 | supported | 0 | 0.00 | 0.00 |
| our | scalene | step3 | supported | 0 | 0.00 | 0.00 |
| our | scalene | step4 | supported | 0 | 0.00 | 0.00 |
| pyds | cpu | step1 | supported | 32 | 4089.07 | 2321.28 |
| pyds | cpu | step2 | supported | 32 | 4454.58 | 1469.05 |
| pyds | cpu | step3 | not_supported (instrumentation only / excluded from comparison) | 32 | 1.28 | 0.16 |
| pyds | cpu | step4 | not_supported (instrumentation only / excluded from comparison) | 32 | 0.88 | 0.08 |
| pyds | line | step1 | supported | 32 | 4596.85 | 2347.51 |
| pyds | line | step2 | supported | 32 | 5138.51 | 1476.52 |
| pyds | line | step3 | not_supported (instrumentation only / excluded from comparison) | 32 | 340.75 | 9.66 |
| pyds | line | step4 | not_supported (instrumentation only / excluded from comparison) | 32 | 294.74 | 14.69 |
| pyds | memory | step1 | supported | 32 | 4282.13 | 2324.33 |
| pyds | memory | step2 | supported | 32 | 4703.29 | 1470.25 |
| pyds | memory | step3 | not_supported (instrumentation only / excluded from comparison) | 32 | 140.93 | 4.36 |
| pyds | memory | step4 | not_supported (instrumentation only / excluded from comparison) | 32 | 120.68 | 2.61 |
| pyds | scalene | step1 | supported | 0 | 0.00 | 0.00 |
| pyds | scalene | step2 | supported | 0 | 0.00 | 0.00 |
| pyds | scalene | step3 | not_supported (instrumentation only / excluded from comparison) | 0 | 0.00 | 0.00 |
| pyds | scalene | step4 | not_supported (instrumentation only / excluded from comparison) | 0 | 0.00 | 0.00 |
