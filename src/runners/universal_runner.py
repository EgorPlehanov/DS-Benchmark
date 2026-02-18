"""
Универсальный раннер для бенчмаркинга реализаций теории Демпстера-Шейфера.
Выполняет 4-шаговый процесс тестирования и собирает метрики производительности.
"""

import os
import json
import time
import tracemalloc
import statistics
import sys
import psutil
from typing import Dict, List, Any, Optional, Tuple, Callable
from datetime import datetime
from pathlib import Path

from ..adapters.base_adapter import BaseDempsterShaferAdapter
from ..profiling.artifacts import ArtifactManager


class UniversalBenchmarkRunner:
    """
    Универсальный раннер для тестирования адаптеров теории ДШ.
    
    Выполняет:
    1. Загрузку тестовых данных
    2. Выполнение 4-шагового процесса
    3. Сбор метрик производительности
    4. Сохранение структурированных результатов
    """
    
    def __init__(self, adapter: BaseDempsterShaferAdapter, 
                 results_dir: str = "results/profiling"):
        """
        Инициализация раннера.
        
        Args:
            adapter: Адаптер для тестируемой библиотеки
            results_dir: Директория для сохранения результатов
        """
        self.adapter = adapter
        self.adapter_name = adapter.benchmark_name
        self.results_dir = results_dir
        self.results = []
        
        # Создаем структуру артефактов: results/profiling/<library>/<timestamp>/
        self.run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.artifact_manager = ArtifactManager(
            base_dir=results_dir,
            adapter_name=self.adapter_name,
            run_id=self.run_id,
        )
        self.run_dir = str(self.artifact_manager.run_dir)


        print(f"🚀 Инициализирован раннер для {self.adapter_name}")
        print(f"📁 Результаты будут сохранены в: {self.run_dir}")

    def set_run_parameters(self, **parameters: Any) -> None:
        """Сохраняет параметры запуска только в отдельный файл run_parameters.json."""
        self.artifact_manager.save_run_parameters(parameters)

    def _supports_cr(self) -> bool:
        """Возвращает True, если stdout поддерживает carriage return."""
        return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()

    def _render_inline_progress(self, text: str) -> None:
        """Печатает прогресс в текущей строке или fallback-строкой."""
        if self._supports_cr():
            print(f"\r{text}", end="", flush=True)
            return
        print(text)

    def _finish_inline_progress(self) -> None:
        """Завершает inline-печать переводом строки."""
        if self._supports_cr():
            print()
    
    def run_test(self, test_data: Dict[str, Any], 
             test_name: str,
             iterations: int = 3,
             alphas: Optional[List[float]] = None) -> Dict[str, Any]:
        """
        Запускает один тест.
        """
        print(f"\n🧪 Тест: {test_name} (итераций: {iterations})")
        
        # Инициализация результатов
        test_results = {
            "metadata": {
                "test_name": test_name,  # ✅ СОХРАНЯЕМ ИМЯ ТЕСТА
                "adapter": self.adapter_name,
                "iterations": iterations,
                "timestamp": datetime.now().isoformat(),
                "frame_size": len(test_data.get("frame_of_discernment", [])),
                "sources_count": len(test_data.get("bba_sources", []))
            },
            "iterations": [],
            "aggregated": {}
        }
        
        # Загружаем данные через адаптер
        loaded_data = self.adapter.load_from_dass(test_data)

        # Сохраняем вход теста как артефакт
        self.artifact_manager.save_test_input(test_data, test_name)
        
        # Определяем коэффициенты дисконтирования
        if alphas is None:
            sources_count = self.adapter.get_sources_count(loaded_data)
            alphas = [0.1] * sources_count
        
        # Выполняем итерации
        for i in range(iterations):
            self._render_inline_progress(f"   ↻ Итерация {i+1}/{iterations}")

            iteration_results = self._run_single_iteration(
                loaded_data=loaded_data,
                test_data=test_data,
                iteration_num=i+1,
                alphas=alphas,
                test_name=test_name  # ✅ ПЕРЕДАЕМ ИМЯ ТЕСТА
            )
            
            test_results["iterations"].append(iteration_results)
            self._render_inline_progress(f"   ✅ Итерация {i+1}/{iterations}")
            self._finish_inline_progress()
        
        # Агрегируем результаты
        test_results["aggregated"] = self._aggregate_iteration_results(
            test_results["iterations"]
        )
        
        # Сохраняем сырые результаты
        self._save_test_results(test_results, test_name)
        
        # Добавляем в общие результаты
        self.results.append(test_results)
        
        return test_results
    
    def _run_single_iteration(self, 
                         loaded_data: Any,
                         test_data: Dict[str, Any],
                         iteration_num: int,
                         alphas: List[float],
                         test_name: str = "") -> Dict[str, Any]:  # ✅ ДОБАВЛЯЕМ test_name
        """
        Выполняет одну итерацию теста.
        """
        iteration_results = {
            "iteration": iteration_num,
            "performance": {}
        }
        
        # === ШАГ 1: Исходные Belief/Plausibility ===
        step1_results, step1_metrics = self._measure_performance(
            self._execute_step1,
            loaded_data,
            step_name="step1_original",
            test_name=test_name,           # ✅ ПЕРЕДАЕМ ИМЯ ТЕСТА
            iteration=iteration_num        # ✅ ПЕРЕДАЕМ НОМЕР ИТЕРАЦИИ
        )
        iteration_results["step1"] = step1_results
        iteration_results["performance"]["step1"] = step1_metrics
        
        # === ШАГ 2: Комбинирование Демпстером ===
        step2_results, step2_metrics = self._measure_performance(
            self._execute_step2,
            loaded_data,
            step_name="step2_dempster",
            test_name=test_name,           # ✅ ПЕРЕДАЕМ ИМЯ ТЕСТА
            iteration=iteration_num        # ✅ ПЕРЕДАЕМ НОМЕР ИТЕРАЦИИ
        )
        iteration_results["step2"] = step2_results
        iteration_results["performance"]["step2"] = step2_metrics
        
        # === ШАГ 3: Дисконтирование + Демпстер ===
        step3_results, step3_metrics = self._measure_performance(
            self._execute_step3,
            loaded_data,
            alphas,
            step_name="step3_discount_dempster",
            test_name=test_name,           # ✅ ПЕРЕДАЕМ ИМЯ ТЕСТА
            iteration=iteration_num        # ✅ ПЕРЕДАЕМ НОМЕР ИТЕРАЦИИ
        )
        iteration_results["step3"] = step3_results
        iteration_results["performance"]["step3"] = step3_metrics
        
        # === ШАГ 4: Комбинирование Ягером ===
        step4_results, step4_metrics = self._measure_performance(
            self._execute_step4,
            loaded_data,
            step_name="step4_yager",
            test_name=test_name,           # ✅ ПЕРЕДАЕМ ИМЯ ТЕСТА
            iteration=iteration_num        # ✅ ПЕРЕДАЕМ НОМЕР ИТЕРАЦИИ
        )
        iteration_results["step4"] = step4_results
        iteration_results["performance"]["step4"] = step4_metrics
        
        # Общая статистика по итерации
        iteration_results["performance"]["total"] = {
            "time_total_ms": sum(
                step["time_ms"] for step in iteration_results["performance"].values() 
                if isinstance(step, dict) and "time_ms" in step
            ),
            "memory_peak_mb": max(
                step.get("memory_peak_mb", 0) for step in iteration_results["performance"].values()
                if isinstance(step, dict)
            )
        }
        
        return iteration_results
    
    def _execute_step1(self, loaded_data: Any) -> Dict[str, Any]:
        """Шаг 1: Исходные Belief/Plausibility для каждого источника"""
        frame_elements = self.adapter.get_frame_of_discernment(loaded_data)
        sources_count = self.adapter.get_sources_count(loaded_data)
        
        results = {
            "frame_elements": frame_elements,
            "sources": []
        }
        
        # Для каждого источника вычисляем Belief и Plausibility
        for i in range(sources_count):
            # Получаем данные для конкретного источника
            source_data = self._get_source_data(loaded_data, i)
            
            source_results = {
                "source_id": f"source_{i+1}",
                "beliefs": {},
                "plausibilities": {}
            }
            
            # Для каждого одиночного элемента
            for element in frame_elements:
                belief = self.adapter.calculate_belief(source_data, element)
                plausibility = self.adapter.calculate_plausibility(source_data, element)
                
                source_results["beliefs"][f"{{{element}}}"] = belief
                source_results["plausibilities"][f"{{{element}}}"] = plausibility
            
            # Для всего фрейма (Ω)
            omega = "{" + ",".join(sorted(frame_elements)) + "}"
            source_results["beliefs"][omega] = self.adapter.calculate_belief(source_data, frame_elements)  # Bel(Ω) = 1.0
            source_results["plausibilities"][omega] = self.adapter.calculate_plausibility(source_data, frame_elements)  # Pl(Ω) = 1.0

            results["sources"].append(source_results)
        
        return results
    
    def _execute_step2(self, loaded_data: Any) -> Dict[str, Any]:
        """Шаг 2: Комбинирование всех источников по правилу Демпстера"""
        # Комбинируем все источники
        combined_bpa_str = self.adapter.combine_sources_dempster(loaded_data)
        
        # КОНВЕРТИРУЕМ строковый формат в формат нашего адаптера
        combined_bpa = self._convert_string_bpa_to_frozenset(combined_bpa_str)
        
        # Создаем данные с комбинированным BPA для вычисления Belief/Plausibility
        combined_data = self._create_combined_data(loaded_data, combined_bpa)
        
        frame_elements = self.adapter.get_frame_of_discernment(loaded_data)
        
        results = {
            "combined_bpa": combined_bpa_str,  # Сохраняем в строковом формате
            "beliefs": {},
            "plausibilities": {}
        }
        
        # Для каждого одиночного элемента
        for element in frame_elements:
            belief = self.adapter.calculate_belief(combined_data, element)
            plausibility = self.adapter.calculate_plausibility(combined_data, element)
            
            results["beliefs"][f"{{{element}}}"] = belief
            results["plausibilities"][f"{{{element}}}"] = plausibility
        
        # Для всего фрейма
        omega = "{" + ",".join(sorted(frame_elements)) + "}"
        results["beliefs"][omega] = self.adapter.calculate_belief(combined_data, frame_elements)
        results["plausibilities"][omega] = self.adapter.calculate_plausibility(combined_data, frame_elements)
        
        return results
    
    def _execute_step3(self, loaded_data: Any, alphas: List[float]) -> Dict[str, Any]:
        """Шаг 3: Дисконтирование + комбинирование Демпстером"""
        # Получаем количество источников
        sources_count = self.adapter.get_sources_count(loaded_data)
        
        # Применяем дисконтирование к каждому источнику с его alpha
        discounted_bpas_str = []
        for i in range(sources_count):
            # Получаем данные для конкретного источника
            source_data = self._get_source_data(loaded_data, i)
            
            # Применяем дисконтирование с alpha для этого источника
            alpha = alphas[i] if i < len(alphas) else 0.1
            
            # Для применения дисконтирования к одному источнику
            discounted_list = self.adapter.apply_discounting(source_data, alpha)
            
            if discounted_list and len(discounted_list) > 0:
                discounted_bpas_str.append(discounted_list[0])
            else:
                # Если не получилось, используем оригинальный BPA
                original_bpa = self._extract_bpa_from_source(loaded_data, i)
                discounted_bpas_str.append(original_bpa)
        
        # КОНВЕРТИРУЕМ строковый формат в формат frozenset
        discounted_bpas = [self._convert_string_bpa_to_frozenset(bpa_str) 
                          for bpa_str in discounted_bpas_str]
        
        # Создаем объект с дисконтированными данными
        discounted_data = self._create_discounted_data(loaded_data, discounted_bpas)
        
        # Комбинируем дисконтированные источники
        combined_bpa_str = self.adapter.combine_sources_dempster(discounted_data)
        combined_bpa = self._convert_string_bpa_to_frozenset(combined_bpa_str)
        
        # Создаем данные с комбинированным BPA
        combined_data = self._create_combined_data(discounted_data, combined_bpa)
        
        frame_elements = self.adapter.get_frame_of_discernment(loaded_data)
        
        results = {
            "discounted_bpas": discounted_bpas_str,  # Сохраняем в строковом формате
            "combined_bpa": combined_bpa_str,
            "beliefs": {},
            "plausibilities": {}
        }
        
        # Для каждого элемента
        for element in frame_elements:
            belief = self.adapter.calculate_belief(combined_data, element)
            plausibility = self.adapter.calculate_plausibility(combined_data, element)
            
            results["beliefs"][f"{{{element}}}"] = belief
            results["plausibilities"][f"{{{element}}}"] = plausibility
        
        # Для всего фрейма
        omega = "{" + ",".join(sorted(frame_elements)) + "}"
        results["beliefs"][omega] = self.adapter.calculate_belief(combined_data, frame_elements)
        results["plausibilities"][omega] = self.adapter.calculate_plausibility(combined_data, frame_elements)
        
        return results
    
    def _execute_step4(self, loaded_data: Any) -> Dict[str, Any]:
        """Шаг 4: Комбинирование всех источников по правилу Ягера"""
        # Комбинируем все источники по Ягеру
        combined_bpa_str = self.adapter.combine_sources_yager(loaded_data)
        
        # КОНВЕРТИРУЕМ строковый формат в формат frozenset
        combined_bpa = self._convert_string_bpa_to_frozenset(combined_bpa_str)
        
        # Создаем данные с комбинированным BPA
        combined_data = self._create_combined_data(loaded_data, combined_bpa)
        
        frame_elements = self.adapter.get_frame_of_discernment(loaded_data)
        
        results = {
            "combined_bpa": combined_bpa_str,  # Сохраняем в строковом формате
            "beliefs": {},
            "plausibilities": {}
        }
        
        # Для каждого элемента
        for element in frame_elements:
            belief = self.adapter.calculate_belief(combined_data, element)
            plausibility = self.adapter.calculate_plausibility(combined_data, element)
            
            results["beliefs"][f"{{{element}}}"] = belief
            results["plausibilities"][f"{{{element}}}"] = plausibility
        
        # Для всего фрейма
        omega = "{" + ",".join(sorted(frame_elements)) + "}"
        results["beliefs"][omega] = self.adapter.calculate_belief(combined_data, frame_elements)
        results["plausibilities"][omega] = self.adapter.calculate_plausibility(combined_data, frame_elements)
        
        return results
    
    def _convert_string_bpa_to_frozenset(self, bpa_str: Dict[str, float]) -> Dict[frozenset, float]:
        """Конвертирует BPA из строкового формата в формат frozenset."""
        if not bpa_str:
            return {}
        
        # Проверяем, может уже в нужном формате
        first_key = next(iter(bpa_str.keys()))
        if isinstance(first_key, frozenset):
            return bpa_str # type: ignore
        
        # Конвертируем строки во frozenset
        bpa_frozenset: Dict[frozenset, float] = {}
        for subset_str, mass in bpa_str.items():
            if subset_str == "{}":
                subset = frozenset()
            else:
                elements = subset_str.strip("{}").split(",")
                if elements == ['']:
                    subset = frozenset()
                else:
                    subset = frozenset(elements)
            bpa_frozenset[subset] = mass
        
        return bpa_frozenset
        
    def _is_full_conflict_message(self, message: str) -> bool:
        lowered = str(message).lower()
        return any(keyword in lowered for keyword in ["полный конфликт", "full conflict", "k=1.0", "конфликт между источниками"])

    def _measure_performance(self, func: Callable, *args,
                       step_name: str = "", **kwargs) -> Tuple[Any, Dict[str, Any]]:
        """Измеряет производительность выполнения функции и нормализует статус этапа."""
        metrics: Dict[str, Any] = {
            "status": "success",
            "supported": True,
        }

        tracemalloc.start()
        snapshot1 = tracemalloc.take_snapshot()

        process = psutil.Process()
        cpu_before = process.cpu_percent(interval=None)
        start_time = time.perf_counter()

        try:
            result = func(*args, **kwargs)
        except NotImplementedError as e:
            metrics["status"] = "not_supported"
            metrics["supported"] = False
            metrics["error_type"] = type(e).__name__
            metrics["error"] = str(e)
            result = {"status": "not_supported", "error": str(e)}
        except ValueError as e:
            error_msg = str(e)
            if self._is_full_conflict_message(error_msg):
                metrics["status"] = "full_conflict"
                metrics["warning"] = "Полный конфликт между источниками (K=1.0)"
                metrics["full_conflict"] = True
                result = {"status": "full_conflict", "warning": metrics["warning"]}
            else:
                metrics["status"] = "failed"
                metrics["error_type"] = type(e).__name__
                metrics["error"] = error_msg
                result = {"status": "failed", "error": error_msg}
        except Exception as e:
            metrics["status"] = "failed"
            metrics["error_type"] = type(e).__name__
            metrics["error"] = str(e)
            result = {"status": "failed", "error": str(e)}

        end_time = time.perf_counter()
        cpu_after = process.cpu_percent(interval=None)
        snapshot2 = tracemalloc.take_snapshot()
        tracemalloc.stop()

        metrics["time_ms"] = (end_time - start_time) * 1000
        memory_stats = snapshot2.compare_to(snapshot1, 'lineno')
        memory_usage = sum(stat.size for stat in memory_stats)
        metrics["memory_peak_mb"] = memory_usage / 1024 / 1024
        metrics["cpu_usage_percent"] = max(0, cpu_after - cpu_before)

        return result, metrics
    
    def _get_source_data(self, loaded_data: Any, source_index: int) -> Any:
        """
        Извлекает данные для конкретного источника.
        """
        # Проверяем формат данных нашего адаптера
        if isinstance(loaded_data, dict) and 'bpas' in loaded_data:
            # Создаем данные только с одним BPA
            single_source_data = loaded_data.copy()
            if source_index < len(loaded_data['bpas']):
                single_source_data['bpas'] = [loaded_data['bpas'][source_index]]
            else:
                single_source_data['bpas'] = [{}]
            return single_source_data
        
        # Если адаптер имеет другой формат, оставляем как есть
        return loaded_data
    
    def _extract_bpa_from_source(self, loaded_data: Any, source_index: int) -> Dict[str, float]:
        """Извлекает BPA из источника."""
        source_data = self._get_source_data(loaded_data, source_index)
        
        # Пытаемся извлечь BPA
        if isinstance(source_data, dict) and 'bpas' in source_data and source_data['bpas']:
            bpa = source_data['bpas'][0]
            # Если BPA в формате frozenset, конвертируем в строковый формат
            if bpa and isinstance(next(iter(bpa.keys())), frozenset):
                return self._convert_frozenset_bpa_to_string(bpa)
        
        return {}
    
    def _convert_frozenset_bpa_to_string(self, bpa_frozenset: Dict[frozenset, float]) -> Dict[str, float]:
        """Конвертирует BPA из формата frozenset в строковый формат."""
        if not bpa_frozenset:
            return {}
        
        bpa_str = {}
        for subset, mass in bpa_frozenset.items():
            if not subset:
                subset_str = "{}"
            else:
                subset_str = "{" + ",".join(sorted(subset)) + "}"
            bpa_str[subset_str] = mass
        
        return bpa_str
    
    def _create_combined_data(self, original_data: Any, 
                            combined_bpa: Dict[frozenset, float]) -> Any:
        """Создает объект данных с комбинированным BPA."""
        if isinstance(original_data, dict):
            combined_data = original_data.copy()
            combined_data['bpas'] = [combined_bpa]
            return combined_data
        
        return original_data
    
    def _create_discounted_data(self, original_data: Any,
                              discounted_bpas: List[Dict[frozenset, float]]) -> Any:
        """Создает объект данных с дисконтированными BPA."""
        if isinstance(original_data, dict):
            discounted_data = original_data.copy()
            discounted_data['bpas'] = discounted_bpas
            return discounted_data
        
        return original_data
    
    def _aggregate_iteration_results(self, iterations: List[Dict]) -> Dict[str, Any]:
        """Агрегирует результаты всех итераций."""
        if not iterations:
            return {}
        
        aggregated = {
            "performance": {}
        }
        
        # Агрегация метрик производительности
        for step in ["step1", "step2", "step3", "step4"]:
            step_times = [
                iteration["performance"][step]["time_ms"]
                for iteration in iterations
                if step in iteration.get("performance", {}) and "error" not in iteration["performance"][step]
            ]
            
            if step_times:
                aggregated["performance"][step] = {
                    "time_ms": {
                        "min": min(step_times),
                        "max": max(step_times),
                        "mean": statistics.mean(step_times),
                        "median": statistics.median(step_times),
                        "std": statistics.stdev(step_times) if len(step_times) > 1 else 0
                    }
                }
        
        # Агрегация итогового времени
        total_times = [
            iteration["performance"]["total"]["time_total_ms"]
            for iteration in iterations
            if "total" in iteration.get("performance", {})
        ]
        
        if total_times:
            aggregated["performance"]["total"] = {
                "time_total_ms": {
                    "min": min(total_times),
                    "max": max(total_times),
                    "mean": statistics.mean(total_times),
                    "median": statistics.median(total_times),
                    "std": statistics.stdev(total_times) if len(total_times) > 1 else 0
                }
            }
        
        # Агрегация результатов вычислений
        if iterations:
            aggregated["results"] = iterations[-1]
        
        return aggregated
    
    def _save_test_results(self, test_results: Dict[str, Any], test_name: str):
        """Сохраняет структурированные результаты теста."""
        self.artifact_manager.save_test_results(test_results, test_name)

    def _classify_test_status(self, test_result: Dict[str, Any]) -> str:
        if test_result.get("error"):
            return "failed"

        statuses: list[str] = []
        for iteration in test_result.get("iterations", []):
            perf = iteration.get("performance", {})
            for step in ("step1", "step2", "step3", "step4"):
                step_perf = perf.get(step, {})
                statuses.append(step_perf.get("status", "success"))

        if any(status == "failed" for status in statuses):
            return "failed"
        if any(status == "full_conflict" for status in statuses):
            return "full_conflict"
        if statuses and all(status == "not_supported" for status in statuses):
            return "not_supported"
        return "success"

    def _create_run_summary(self, discovered_tests: int) -> Dict[str, Any]:
        """Создает единый сводный отчет по запуску с учетом всех итераций/повторов."""
        step_map = {
            "step1": "step1_original",
            "step2": "step2_dempster",
            "step3": "step3_discount_dempster",
            "step4": "step4_yager",
        }

        run_summary: Dict[str, Any] = {
            "run_meta": {
                "adapter": self.adapter_name,
                "run_id": self.run_id,
                "generated_at": datetime.now().isoformat(),
                "discovered_tests": discovered_tests,
                "executed_tests": len(self.results),
                "run_dir": self.run_dir,
            },
            "totals": {
                "success": 0,
                "failed": 0,
                "full_conflict": 0,
                "not_supported": 0,
            },
            "tests": [],
            "statistics": {
                "steps": {},
                "total_time_ms": {"sample_count": 0, "mean": 0.0, "min": 0.0, "max": 0.0, "median": 0.0, "std": 0.0},
                "total_time_per_repeat_ms": {"sample_count": 0, "mean": 0.0, "min": 0.0, "max": 0.0, "median": 0.0, "std": 0.0},
                "errors": {},
            },
        }

        step_total_samples: Dict[str, list[float]] = {step: [] for step in step_map}
        step_normalized_samples: Dict[str, list[float]] = {step: [] for step in step_map}
        step_counters: Dict[str, Dict[str, int]] = {
            step: {"applicable": 0, "success": 0, "failed": 0, "full_conflict": 0, "not_supported": 0}
            for step in step_map
        }
        total_times: list[float] = []
        total_per_repeat_times: list[float] = []

        def _stats(values: list[float]) -> Dict[str, float]:
            if not values:
                return {"sample_count": 0, "mean": 0.0, "min": 0.0, "max": 0.0, "median": 0.0, "std": 0.0}
            return {
                "sample_count": len(values),
                "mean": statistics.mean(values),
                "min": min(values),
                "max": max(values),
                "median": statistics.median(values),
                "std": statistics.stdev(values) if len(values) > 1 else 0.0,
            }

        for test_result in self.results:
            metadata = test_result.get("metadata", {})
            test_name = metadata.get("test_name", "unknown")
            iterations = test_result.get("iterations", [])

            test_entry: Dict[str, Any] = {
                "test_name": test_name,
                "status": self._classify_test_status(test_result),
                "frame_size": metadata.get("frame_size"),
                "sources_count": metadata.get("sources_count"),
                "input_ref": f"input/{test_name}_input.json",
                "result_ref": f"test_results/{test_name}_results.json",
                "iterations_count": len(iterations),
                "steps": {},
                "errors": [],
            }

            test_step_total_samples: Dict[str, list[float]] = {step: [] for step in step_map}
            test_step_normalized_samples: Dict[str, list[float]] = {step: [] for step in step_map}
            test_total_samples: list[float] = []
            test_total_per_repeat_samples: list[float] = []

            for iteration in iterations:
                perf = iteration.get("performance", {})
                successful_step_total_times: list[float] = []
                successful_step_normalized_times: list[float] = []

                for step_key, step_name in step_map.items():
                    step_perf = perf.get(step_key, {})
                    status = step_perf.get("status", "success")
                    supported = step_perf.get("supported", status != "not_supported")
                    time_total_ms = float(step_perf.get("time_ms", 0.0) or 0.0)
                    repeat_count = int(step_perf.get("step_repeat_count", metadata.get("step_repeat_count", 1)) or 1)
                    time_per_repeat_ms = float(
                        step_perf.get("time_per_repeat_ms", time_total_ms / max(1, repeat_count))
                    )

                    counters = step_counters[step_key]
                    counters[status if status in counters else "failed"] += 1
                    if status != "not_supported":
                        counters["applicable"] += 1

                    if status == "success":
                        step_total_samples[step_key].append(time_total_ms)
                        step_normalized_samples[step_key].append(time_per_repeat_ms)
                        test_step_total_samples[step_key].append(time_total_ms)
                        test_step_normalized_samples[step_key].append(time_per_repeat_ms)
                        successful_step_total_times.append(time_total_ms)
                        successful_step_normalized_times.append(time_per_repeat_ms)
                    else:
                        error_message = step_perf.get("error") or step_perf.get("warning")
                        if error_message:
                            err_key = f"{step_name}: {error_message}"
                            run_summary["statistics"]["errors"].setdefault(err_key, []).append(test_name)
                            test_entry["errors"].append({
                                "iteration": iteration.get("iteration") or iteration.get("run"),
                                "step": step_name,
                                "status": status,
                                "message": error_message,
                            })

                if len(successful_step_total_times) == 4:
                    test_total = sum(successful_step_total_times)
                    test_total_per_repeat = sum(successful_step_normalized_times)
                    total_times.append(test_total)
                    total_per_repeat_times.append(test_total_per_repeat)
                    test_total_samples.append(test_total)
                    test_total_per_repeat_samples.append(test_total_per_repeat)

            for step_key, step_name in step_map.items():
                test_entry["steps"][step_key] = {
                    "name": step_name,
                    "samples": {
                        "time_total_ms": _stats(test_step_total_samples[step_key]),
                        "time_per_repeat_ms": _stats(test_step_normalized_samples[step_key]),
                    },
                }

            test_entry["total_time_ms"] = _stats(test_total_samples)
            test_entry["total_time_per_repeat_ms"] = _stats(test_total_per_repeat_samples)

            run_summary["tests"].append(test_entry)
            run_summary["totals"][test_entry["status"]] = run_summary["totals"].get(test_entry["status"], 0) + 1

        for step_key, counters in step_counters.items():
            applicable = counters["applicable"]
            success_rate = (counters["success"] / applicable * 100) if applicable else 0.0
            run_summary["statistics"]["steps"][step_key] = {
                "counts": counters,
                "success_rate": success_rate,
                "time_total_ms": _stats(step_total_samples[step_key]),
                "time_per_repeat_ms": _stats(step_normalized_samples[step_key]),
            }

        run_summary["statistics"]["total_time_ms"] = _stats(total_times)
        run_summary["statistics"]["total_time_per_repeat_ms"] = _stats(total_per_repeat_times)
        return run_summary

    def run_test_suite(self, test_dir: str,
                  iterations: int = 3,
                  max_tests: Optional[int] = None) -> Dict[str, Any]:
        """Запускает набор тестов из директории и формирует единый run-summary."""
        print("\n🚀 Запуск набора тестов")
        print(f"📁 Директория: {test_dir}")
        print(f"🔄 Итераций на тест: {iterations}")

        test_files = []
        for root, dirs, files in os.walk(test_dir):
            for file in files:
                if file.endswith('.json') and file != "statistics.json":
                    test_files.append(os.path.join(root, file))

        if max_tests and max_tests < len(test_files):
            test_files = test_files[:max_tests]

        total_tests = len(test_files)
        print(f"📄 Найдено тестов: {total_tests}")
        print("\n📊 Прогресс выполнения:")

        if total_tests == 0:
            print("⚠️  Тесты не найдены — будет сформирован пустой run_summary.")

        for i, test_file in enumerate(test_files, 1):
            test_name = os.path.splitext(os.path.basename(test_file))[0]
            self._render_inline_progress(f"🧪 [{i}/{total_tests}] {test_name} ...")
            try:
                with open(test_file, 'r', encoding='utf-8') as f:
                    test_data = json.load(f)
                if "frame_of_discernment" not in test_data or "bba_sources" not in test_data:
                    raise ValueError("Неверный формат теста")
                sources_count = len(test_data.get("bba_sources", []))
                alphas = [0.1] * sources_count
                self.run_test(test_data=test_data, test_name=test_name, iterations=iterations, alphas=alphas)
                self._render_inline_progress(f"✅ [{i}/{total_tests}] {test_name}")
                self._finish_inline_progress()
            except Exception as e:
                self._render_inline_progress(f"❌ [{i}/{total_tests}] {test_name}: {e}")
                self._finish_inline_progress()
                failed_test_result = {
                    "metadata": {
                        "test_name": test_name,
                        "adapter": self.adapter_name,
                        "timestamp": datetime.now().isoformat(),
                        "status": "failed_to_start"
                    },
                    "iterations": [],
                    "aggregated": {},
                    "error": str(e)
                }
                self._save_test_results(failed_test_result, test_name)
                self.results.append(failed_test_result)

        run_summary = self._create_run_summary(discovered_tests=len(test_files))
        self.artifact_manager.save_json("run_summary.json", run_summary, root_dir=True)
        self._create_final_text_report(run_summary)

        print("\n✅ Выполнение набора тестов завершено")
        return run_summary

    def _create_final_text_report(self, run_summary: Dict[str, Any]):
        """Создает финальный текстовый отчет из run_summary."""
        meta = run_summary.get("run_meta", {})
        totals = run_summary.get("totals", {})
        step_stats = run_summary.get("statistics", {}).get("steps", {})
        total_time = run_summary.get("statistics", {}).get("total_time_ms", {})
        total_time_per_repeat = run_summary.get("statistics", {}).get("total_time_per_repeat_ms", {})

        lines = [
            "=" * 90,
            "📊 RUN SUMMARY",
            f"Adapter: {meta.get('adapter', 'unknown')}",
            f"Run ID: {meta.get('run_id', 'unknown')}",
            f"Generated at: {meta.get('generated_at', '')}",
            f"Discovered tests: {meta.get('discovered_tests', 0)}",
            f"Executed tests: {meta.get('executed_tests', 0)}",
            "=" * 90,
            "",
            "Totals:",
            f"  ✅ success: {totals.get('success', 0)}",
            f"  ⚠️ full_conflict: {totals.get('full_conflict', 0)}",
            f"  🚫 not_supported: {totals.get('not_supported', 0)}",
            f"  ❌ failed: {totals.get('failed', 0)}",
            "",
            "Step statistics:",
        ]

        for step in ("step1", "step2", "step3", "step4"):
            stat = step_stats.get(step, {})
            counts = stat.get("counts", {})
            time_total = stat.get("time_total_ms", {})
            time_per_repeat = stat.get("time_per_repeat_ms", {})
            lines.append(
                f"  {step}: applicable={counts.get('applicable', 0)}, success={counts.get('success', 0)}, "
                f"failed={counts.get('failed', 0)}, full_conflict={counts.get('full_conflict', 0)}, "
                f"not_supported={counts.get('not_supported', 0)}, success_rate={stat.get('success_rate', 0.0):.1f}%"
            )
            lines.append(
                f"      time_total_ms: mean={time_total.get('mean', 0.0):.2f}, min={time_total.get('min', 0.0):.2f}, "
                f"max={time_total.get('max', 0.0):.2f}, sample_count={time_total.get('sample_count', 0)}"
            )
            lines.append(
                f"      time_per_repeat_ms: mean={time_per_repeat.get('mean', 0.0):.2f}, min={time_per_repeat.get('min', 0.0):.2f}, "
                f"max={time_per_repeat.get('max', 0.0):.2f}, sample_count={time_per_repeat.get('sample_count', 0)}"
            )

        lines.extend([
            "",
            "Total test time (only fully successful samples):",
            f"  total_ms: mean={total_time.get('mean', 0.0):.2f}, min={total_time.get('min', 0.0):.2f}, "
            f"max={total_time.get('max', 0.0):.2f}, sample_count={total_time.get('sample_count', 0)}",
            f"  per_repeat_ms: mean={total_time_per_repeat.get('mean', 0.0):.2f}, min={total_time_per_repeat.get('min', 0.0):.2f}, "
            f"max={total_time_per_repeat.get('max', 0.0):.2f}, sample_count={total_time_per_repeat.get('sample_count', 0)}",
            "",
            "Errors:",
        ])

        errors = run_summary.get("statistics", {}).get("errors", {})
        if not errors:
            lines.append("  (none)")
        else:
            for error, tests in errors.items():
                lines.append(f"  - {error}")
                lines.append(f"    tests: {', '.join(sorted(set(tests)))}")

        self.artifact_manager.save_text("final_report.txt", "\n".join(lines), subdir="logs")

    def cleanup(self):
        """Очистка ресурсов раннера.
        Может быть переопределен в подклассах для освобождения ресурсов.
        """
        # Базовая реализация ничего не делает
        # Подклассы могут переопределить для очистки файлов, соединений и т.д.
        pass
