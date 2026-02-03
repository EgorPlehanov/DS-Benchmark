"""
Универсальный раннер для бенчмаркинга реализаций теории Демпстера-Шейфера.
Выполняет 4-шаговый процесс тестирования и собирает метрики производительности.
"""

import os
import json
import time
import tracemalloc
import statistics
import psutil
from typing import Dict, List, Any, Optional, Tuple, Callable
from datetime import datetime
from pathlib import Path

from ..adapters.base_adapter import BaseDempsterShaferAdapter


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
                 results_dir: str = "results/benchmark"):
        """
        Инициализация раннера.
        
        Args:
            adapter: Адаптер для тестируемой библиотеки
            results_dir: Директория для сохранения результатов
        """
        self.adapter = adapter
        self.adapter_name = adapter.__class__.__name__.replace('Adapter', '').lower()
        self.results_dir = results_dir
        self.results = []
        
        # Создаем директории для результатов
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.run_id = f"{self.adapter_name}_{timestamp}"
        self.run_dir = os.path.join(results_dir, self.run_id)
        
        os.makedirs(self.run_dir, exist_ok=True)
        os.makedirs(os.path.join(self.run_dir, "raw"), exist_ok=True)
        os.makedirs(os.path.join(self.run_dir, "profiles"), exist_ok=True)
        os.makedirs(os.path.join(self.run_dir, "aggregated"), exist_ok=True)
        
        print(f"🚀 Инициализирован раннер для {self.adapter_name}")
        print(f"📁 Результаты будут сохранены в: {self.run_dir}")
    
    def run_test(self, test_data: Dict[str, Any], 
             test_name: str,
             iterations: int = 3,
             alphas: Optional[List[float]] = None) -> Dict[str, Any]:
        """
        Запускает один тест.
        """
        print(f"\n🧪 Запуск теста: {test_name}")
        print(f"   Итераций: {iterations}")
        
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
        
        # Определяем коэффициенты дисконтирования
        if alphas is None:
            sources_count = self.adapter.get_sources_count(loaded_data)
            alphas = [0.1] * sources_count
        
        # Выполняем итерации
        for i in range(iterations):
            print(f"   Итерация {i+1}/{iterations}...", end="", flush=True)
            
            iteration_results = self._run_single_iteration(
                loaded_data=loaded_data,
                test_data=test_data,
                iteration_num=i+1,
                alphas=alphas,
                test_name=test_name  # ✅ ПЕРЕДАЕМ ИМЯ ТЕСТА
            )
            
            test_results["iterations"].append(iteration_results)
            print(" ✓")
        
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
        
    def _measure_performance(self, func: Callable, *args, 
                       step_name: str = "", **kwargs) -> Tuple[Any, Dict[str, float]]:
        """
        Измеряет производительность выполнения функции.
        """
        metrics = {}
        
        # Начинаем отслеживание памяти
        tracemalloc.start()
        snapshot1 = tracemalloc.take_snapshot()
        
        # Измеряем время CPU
        process = psutil.Process()
        cpu_before = process.cpu_percent(interval=None)
        
        # Время выполнения
        start_time = time.perf_counter()
        
        # Выполняем функцию
        try:
            result = func(*args, **kwargs)
        except ValueError as e:
            # ✅ ОСОБАЯ ОБРАБОТКА ДЛЯ ПОЛНОГО КОНФЛИКТА (единый формат)
            error_msg = str(e)
            if "Полный конфликт" in error_msg or "K=1.0" in error_msg or "конфликт" in error_msg.lower():
                # Стандартизируем сообщение об ошибке
                standard_warning = "Полный конфликт между источниками (K=1.0)"
                result = {"warning": standard_warning, "full_conflict": True}
                metrics["warning"] = standard_warning
                metrics["full_conflict"] = True
            else:
                # Другие ValueError - это ошибки
                result = {"error": error_msg}
                metrics["error"] = error_msg
        except Exception as e:
            # Другие исключения - это ошибки
            result = {"error": str(e)}
            metrics["error"] = str(e)
        
        # Конец измерения времени
        end_time = time.perf_counter()
        
        # Загрузка CPU после выполнения
        cpu_after = process.cpu_percent(interval=None)
        
        # Память после выполнения
        snapshot2 = tracemalloc.take_snapshot()
        tracemalloc.stop()
        
        # Вычисляем метрики
        metrics["time_ms"] = (end_time - start_time) * 1000
        
        # Потребление памяти
        memory_stats = snapshot2.compare_to(snapshot1, 'lineno')
        memory_usage = sum(stat.size for stat in memory_stats)
        metrics["memory_peak_mb"] = memory_usage / 1024 / 1024
        
        # Загрузка CPU
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
        """Сохраняет результаты теста в файлы."""
        # Сохраняем полные результаты
        filename = f"{test_name}_{self.run_id}.json"
        filepath = os.path.join(self.run_dir, "raw", filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(test_results, f, indent=2, ensure_ascii=False)
        
        # Сохраняем краткий отчет
        self._create_short_report(test_results, test_name)
    
    def _create_short_report(self, test_results: Dict[str, Any], test_name: str):
        """Создает краткий текстовый отчет."""
        metadata = test_results["metadata"]
        aggregated = test_results.get("aggregated", {})
        
        report_lines = [
            "=" * 70,
            f"📊 ОТЧЕТ ПО ТЕСТУ: {test_name}",
            f"📅 Время: {metadata['timestamp']}",
            f"📚 Адаптер: {metadata['adapter']}",
            f"🧮 Фрейм: {metadata['frame_size']} элементов",
            f"📈 Источников: {metadata['sources_count']}",
            f"🔄 Итераций: {metadata['iterations']}",
            "=" * 70,
            ""
        ]
        
        # Проверяем наличие полного конфликта
        has_full_conflict = False
        has_other_errors = False
        
        for iteration in test_results.get("iterations", []):
            for step in ["step1", "step2", "step3", "step4"]:
                if step in iteration.get("performance", {}):
                    perf = iteration["performance"][step]
                    if "error" in perf and "Полный конфликт" in perf["error"]:
                        has_full_conflict = True
                        report_lines.append(f"⚠️  {step}: {perf['error']} (K=1.0)")
                    elif "error" in perf:
                        has_other_errors = True
                        report_lines.append(f"❌ Ошибка в {step}: {perf['error']}")
        
        if has_other_errors:
            report_lines.append(f"\n🔴 ТЕСТ СОДЕРЖИТ ОШИБКИ")
        elif has_full_conflict:
            report_lines.append(f"\n⚠️  ТЕСТ ИМЕЕТ ПОЛНЫЙ КОНФЛИКТ (K=1.0)")
            report_lines.append(f"   Это нормальная ситуация в теории Демпстера-Шейфера.")
            report_lines.append(f"   Правило Демпстера неприменимо при K=1.0.")
        else:
            report_lines.append(f"\n✅ ТЕСТ ВЫПОЛНЕН УСПЕШНО")
        
        report_lines.append("")
        
        # Добавляем метрики по шагам (только для успешных шагов)
        perf = aggregated.get("performance", {})
        
        # Сначала выводим шаги без ошибок
        for step_name, step_data in perf.items():
            if step_name == "total":
                continue
                
            time_data = step_data.get("time_ms", {})
            report_lines.append(f"  {step_name.upper():20}:")
            report_lines.append(f"    Время (мс): {time_data.get('mean', 0):.2f} "
                            f"(min: {time_data.get('min', 0):.2f}, "
                            f"max: {time_data.get('max', 0):.2f})")
        
        # Итоговое время
        if "total" in perf:
            total_time = perf["total"].get("time_total_ms", {})
            report_lines.append(f"\n  {'ИТОГО':20}:")
            report_lines.append(f"    Общее время: {total_time.get('mean', 0):.2f} мс")
        
        # Сохраняем отчет
        report_filename = f"{test_name}_{self.run_id}_report.txt"
        report_path = os.path.join(self.run_dir, "raw", report_filename)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(report_lines))
    
    def run_test_suite(self, test_dir: str, 
                  iterations: int = 3,
                  max_tests: Optional[int] = None) -> Dict[str, Any]:
        """
        Запускает набор тестов из директории.
        """
        print(f"\n🚀 ЗАПУСК НАБОРА ТЕСТОВ")
        print(f"📁 Директория: {test_dir}")
        print(f"🔄 Итераций на тест: {iterations}")
        
        # Находим все JSON файлы
        test_files = []
        for root, dirs, files in os.walk(test_dir):
            for file in files:
                if file.endswith('.json') and file != "statistics.json":
                    test_files.append(os.path.join(root, file))
        
        if max_tests and max_tests < len(test_files):
            test_files = test_files[:max_tests]
        
        print(f"📄 Найдено тестов: {len(test_files)}")
        
        # Статистика
        successful_tests = 0
        tests_with_full_conflict = 0
        tests_with_other_errors = 0
        failed_tests = 0
        
        # Списки для детализации
        successful_test_names = []
        conflict_test_names = []
        other_error_test_names = []
        failed_test_names = []
        
        for i, test_file in enumerate(test_files, 1):
            test_name = os.path.splitext(os.path.basename(test_file))[0]
            print(f"\n[{i}/{len(test_files)}] Тест: {test_name}")
            
            try:
                with open(test_file, 'r', encoding='utf-8') as f:
                    test_data = json.load(f)
                
                if "frame_of_discernment" not in test_data or "bba_sources" not in test_data:
                    print(f"   ❌ Неверный формат теста {test_name}")
                    failed_tests += 1
                    failed_test_names.append(test_name)
                    continue
                
                sources_count = len(test_data.get("bba_sources", []))
                alphas = [0.1] * sources_count
                
                # Запускаем тест
                test_result = self.run_test(
                    test_data=test_data,
                    test_name=test_name,
                    iterations=iterations,
                    alphas=alphas
                )
                
                # ✅ ИСПРАВЛЕННЫЙ АНАЛИЗ РЕЗУЛЬТАТОВ
                test_has_full_conflict = False
                test_has_other_errors = False
                
                iterations_data = test_result.get("iterations", [])
                
                for iteration in iterations_data:
                    # Проверяем каждый шаг
                    for step_key in ["step1", "step2", "step3", "step4"]:
                        step_data = iteration.get(step_key, {})
                        
                        # Проверяем step_data на ошибки
                        if isinstance(step_data, dict) and "error" in step_data:
                            error_msg = str(step_data["error"]).lower()
                            if any(keyword in error_msg for keyword in 
                                ["полный конфликт", "full conflict", "k=1.0", "конфликт между источниками"]):
                                test_has_full_conflict = True
                            else:
                                test_has_other_errors = True
                        
                        # Проверяем performance метрики
                        perf_data = iteration.get("performance", {}).get(step_key, {})
                        if isinstance(perf_data, dict):
                            if "error" in perf_data:
                                error_msg = str(perf_data["error"]).lower()
                                if any(keyword in error_msg for keyword in 
                                    ["полный конфликт", "full conflict", "k=1.0", "конфликт между источниками"]):
                                    test_has_full_conflict = True
                                else:
                                    test_has_other_errors = True
                            
                            # Также проверяем warning
                            if "warning" in perf_data:
                                warning_msg = str(perf_data["warning"]).lower()
                                if any(keyword in warning_msg for keyword in 
                                    ["полный конфликт", "full conflict", "k=1.0"]):
                                    test_has_full_conflict = True
                
                # ✅ ПРАВИЛЬНАЯ КЛАССИФИКАЦИЯ ТЕСТА
                if test_has_other_errors:
                    # Другие ошибки (не полный конфликт)
                    print(f"   ❌ Тест {test_name} содержит ошибки")
                    tests_with_other_errors += 1
                    other_error_test_names.append(test_name)
                elif test_has_full_conflict:
                    # ТОЛЬКО полный конфликт
                    print(f"   ⚠️  Тест {test_name} имеет полный конфликт (K=1.0)")
                    successful_tests += 1
                    tests_with_full_conflict += 1
                    conflict_test_names.append(test_name)
                else:
                    # Полностью успешный тест
                    print(f"   ✅ Тест {test_name} выполнен успешно")
                    successful_tests += 1
                    successful_test_names.append(test_name)
                    
            except json.JSONDecodeError as e:
                print(f"   ❌ Ошибка JSON в файле {test_name}: {e}")
                failed_tests += 1
                failed_test_names.append(test_name)
            except KeyError as e:
                print(f"   ❌ Отсутствует поле в тесте {test_name}: {e}")
                failed_tests += 1
                failed_test_names.append(test_name)
            except Exception as e:
                print(f"   ❌ Ошибка при выполнении теста {test_name}: {e}")
                failed_tests += 1
                failed_test_names.append(test_name)
        
        # ✅ ИСПРАВЛЕННАЯ СТАТИСТИКА
        print(f"\n{'='*60}")
        print(f"📊 ПРЕДВАРИТЕЛЬНАЯ СТАТИСТИКА:")
        print(f"{'='*60}")
        print(f"   Всего тестов: {len(test_files)}")
        print(f"   ✅ Успешно выполнено: {successful_tests}")
        if tests_with_full_conflict > 0:
            print(f"   ⚠️  Из них с полным конфликтом: {tests_with_full_conflict}")
        print(f"   ❌ С другими ошибками: {tests_with_other_errors}")
        print(f"   🔴 Не запустились: {failed_tests}")
        
        # Детализация
        if conflict_test_names:
            print(f"\nℹ️  Тесты с полным конфликтом (K=1.0):")
            print(f"   Это нормально для теории Демпстера-Шейфера")
            print(f"   Правило Демпстера неприменимо при K=1.0")
            for name in conflict_test_names:
                print(f"   - {name}")
        
        if other_error_test_names:
            print(f"\n⚠️  Тесты с другими ошибками:")
            for name in other_error_test_names:
                print(f"   - {name}")
        
        if failed_test_names:
            print(f"\n🔴 Тесты, которые не запустились:")
            for name in failed_test_names:
                print(f"   - {name}")
        
        # Создаем итоговый отчет
        summary = self._create_summary_report()
        
        # ✅ ФИНАЛЬНАЯ СТАТИСТИКА
        print(f"\n{'='*60}")
        print(f"📊 ИТОГОВАЯ СТАТИСТИКА:")
        print(f"{'='*60}")
        print(f"Всего тестов: {len(test_files)}")
        print(f"✅ Успешно выполнено: {successful_tests}")
        if tests_with_full_conflict > 0:
            print(f"⚠️  Из них с полным конфликтом: {tests_with_full_conflict}")
        if tests_with_other_errors > 0:
            print(f"❌ С другими ошибками: {tests_with_other_errors}")
        if failed_tests > 0:
            print(f"🔴 Не запустились: {failed_tests}")
        
        print(f"\n✅ ВЫПОЛНЕНИЕ ЗАВЕРШЕНО")
        print(f"📊 Детальный отчет сохранен в: {self.run_dir}/aggregated/final_report.txt")
        
        return summary
    
    def _create_summary_report(self) -> Dict[str, Any]:
        """Создает итоговый отчет по всем выполненным тестам."""
        if not self.results:
            return {}
        
        summary = {
            "metadata": {
                "adapter": self.adapter_name,
                "total_tests": len(self.results),
                "run_id": self.run_id,
                "timestamp": datetime.now().isoformat()
            },
            "tests": [],
            "statistics": {},
            "detailed_analysis": {
                "step_performance": {},
                "step_success_rates": {},
                "failed_steps_by_test": {},
                "error_types": {}
            }
        }
        
        # Собираем статистику по всем тестам (ВСЕ тесты, включая с конфликтами)
        frame_sizes = []
        source_counts = []
        
        # Время по этапам (собираем только успешные выполнения каждого этапа)
        step_times = {
            "step1": [],
            "step2": [],
            "step3": [],
            "step4": [],
            "total": []
        }
        
        # Для анализа успешности этапов (будем считать из ИСХОДНЫХ данных)
        step_success_counts = {
            "step1": 0,
            "step2": 0,
            "step3": 0,
            "step4": 0,
            "total": 0
        }
        
        # Для сбора информации о неудачных этапах
        failed_steps_by_test = {}
        error_types = {}
        
        for test_result in self.results:
            metadata = test_result["metadata"]
            iterations = test_result.get("iterations", [])
            
            # Добавляем информацию о фрейме и источниках (ВСЕ тесты)
            frame_sizes.append(metadata["frame_size"])
            source_counts.append(metadata["sources_count"])
            
            # Добавляем информацию о тесте
            test_info = {
                "test_name": metadata["test_name"],
                "frame_size": metadata["frame_size"],
                "sources_count": metadata["sources_count"],
                "iterations_count": len(iterations)
            }
            summary["tests"].append(test_info)
            
            # ✅ ИСПРАВЛЕННЫЙ ПОДХОД: анализируем исходные итерации, а не агрегированные данные
            test_has_failed_steps = False
            test_failed_steps = []
            
            # Счетчики успешных этапов для этого теста
            test_step_success = {
                "step1": 0,
                "step2": 0,
                "step3": 0,
                "step4": 0
            }
            
            # Анализируем каждую итерацию
            for iteration in iterations:
                perf = iteration.get("performance", {})
                
                # Проверяем каждый этап в этой итерации
                for step in ["step1", "step2", "step3", "step4"]:
                    if step in perf:
                        # Проверяем наличие ошибок/предупреждений
                        has_warning = "warning" in perf[step] and "Полный конфликт" in perf[step]["warning"]
                        has_full_conflict_flag = "full_conflict" in perf[step] and perf[step]["full_conflict"]
                        has_error = "error" in perf[step]
                        
                        if has_warning or has_full_conflict_flag:
                            # Запоминаем только один раз для всего теста
                            if not test_has_failed_steps:
                                error_msg = perf[step].get("warning", "Полный конфликт между источниками (K=1.0)")
                                test_failed_steps.append((step, error_msg))
                                
                                if error_msg not in error_types:
                                    error_types[error_msg] = []
                                error_types[error_msg].append(f"{metadata['test_name']} (шаг {step[-1]})")
                        elif has_error:
                            # Другие ошибки
                            if not test_has_failed_steps:
                                error_msg = perf[step]["error"]
                                test_failed_steps.append((step, error_msg))
                                
                                if error_msg not in error_types:
                                    error_types[error_msg] = []
                                error_types[error_msg].append(f"{metadata['test_name']} (шаг {step[-1]})")
                        else:
                            # Этап успешен в этой итерации
                            test_step_success[step] += 1
                            
                            # Сохраняем время выполнения (только первый раз)
                            if test_step_success[step] == 1 and "time_ms" in perf[step]:
                                if step == "step1":
                                    step_times["step1"].append(perf[step]["time_ms"])
                                elif step == "step2":
                                    step_times["step2"].append(perf[step]["time_ms"])
                                elif step == "step3":
                                    step_times["step3"].append(perf[step]["time_ms"])
                                elif step == "step4":
                                    step_times["step4"].append(perf[step]["time_ms"])
            
            # ✅ Определяем, был ли этап успешен для всего теста
            # Этап считается успешным, если он успешен хотя бы в одной итерации БЕЗ ошибок
            for step in ["step1", "step2", "step3", "step4"]:
                if test_step_success[step] > 0:
                    step_success_counts[step] += 1
                else:
                    # Если ни в одной итерации этап не был успешен, значит он провален
                    if not test_has_failed_steps:
                        # Но мы уже добавили ошибку выше, так что просто отмечаем
                        test_has_failed_steps = True
            
            # Проверяем, полностью ли успешен тест (все этапы успешны)
            if (test_step_success["step1"] > 0 and 
                test_step_success["step2"] > 0 and 
                test_step_success["step3"] > 0 and 
                test_step_success["step4"] > 0):
                step_success_counts["total"] += 1
                
                # Добавляем общее время
                for iteration in iterations:
                    if "total" in iteration.get("performance", {}):
                        total_perf = iteration["performance"]["total"]
                        if "time_total_ms" in total_perf:
                            step_times["total"].append(total_perf["time_total_ms"])
                            break  # Берем только первую итерацию
            
            # Сохраняем информацию о неудачных этапах для этого теста
            if test_has_failed_steps:
                failed_steps_by_test[metadata["test_name"]] = test_failed_steps
        
        # Сохраняем детальный анализ
        summary["detailed_analysis"]["failed_steps_by_test"] = failed_steps_by_test
        summary["detailed_analysis"]["error_types"] = error_types
        
        # Вычисляем статистику успешности этапов
        total_tests = len(self.results)
        for step in step_success_counts:
            success_rate = (step_success_counts[step] / total_tests * 100) if total_tests > 0 else 0
            summary["detailed_analysis"]["step_success_rates"][step] = {
                "successful": step_success_counts[step],
                "total": total_tests,
                "success_rate": success_rate
            }
        
        # Вычисляем общую статистику (ВСЕ тесты)
        summary["statistics"] = {
            "total_tests": total_tests,
            "tests_with_failed_steps": len(failed_steps_by_test),
            # Подсчет тестов с полным конфликтом
            "tests_with_full_conflict": sum(1 for test_name in failed_steps_by_test 
                                        if any("Полный конфликт" in error_msg 
                                                for _, error_msg in failed_steps_by_test[test_name])),
            "frame_size": {
                "min": min(frame_sizes) if frame_sizes else 0,
                "max": max(frame_sizes) if frame_sizes else 0,
                "mean": statistics.mean(frame_sizes) if frame_sizes else 0,
                "median": statistics.median(frame_sizes) if frame_sizes else 0
            },
            "sources_count": {
                "min": min(source_counts) if source_counts else 0,
                "max": max(source_counts) if source_counts else 0,
                "mean": statistics.mean(source_counts) if source_counts else 0,
                "median": statistics.median(source_counts) if source_counts else 0
            },
            "performance": {}
        }
        
        # Статистика производительности по каждому этапу (только по успешным выполнениям)
        for step, times in step_times.items():
            if times:
                step_success_count = step_success_counts.get(step, 0)
                success_rate = (step_success_count / total_tests * 100) if total_tests > 0 else 0
                
                summary["statistics"]["performance"][step] = {
                    "time_ms": {
                        "min": min(times),
                        "max": max(times),
                        "mean": statistics.mean(times),
                        "median": statistics.median(times),
                        "std": statistics.stdev(times) if len(times) > 1 else 0,
                        "sample_count": len(times),
                        "success_count": step_success_count,
                        "success_rate": success_rate
                    }
                }
                summary["detailed_analysis"]["step_performance"][step] = times
            else:
                # Если нет успешных выполнений
                step_success_count = step_success_counts.get(step, 0)
                success_rate = (step_success_count / total_tests * 100) if total_tests > 0 else 0
                
                summary["statistics"]["performance"][step] = {
                    "time_ms": {
                        "min": 0,
                        "max": 0,
                        "mean": 0,
                        "median": 0,
                        "std": 0,
                        "sample_count": 0,
                        "success_count": step_success_count,
                        "success_rate": success_rate
                    }
                }
        
        # Сохраняем итоговый отчет
        summary_file = os.path.join(self.run_dir, "aggregated", "summary.json")
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        # Создаем текстовый отчет
        self._create_final_text_report(summary)
        
        return summary

    def _create_final_text_report(self, summary: Dict[str, Any]):
        """Создает финальный текстовый отчет с детальным анализом."""
        metadata = summary["metadata"]
        stats = summary["statistics"]
        detailed = summary.get("detailed_analysis", {})
        
        # Получаем total_tests из метаданных
        total_tests = metadata['total_tests']
        
        report_lines = [
            "=" * 80,
            f"📊 ИТОГОВЫЙ ОТЧЕТ ПО БЕНЧМАРКУ",
            f"📅 Время: {metadata['timestamp']}",
            f"📚 Адаптер: {metadata['adapter']}",
            f"🧪 Всего тестов: {total_tests}",
            f"⚠️  Тестов с неудачными этапами: {stats.get('tests_with_failed_steps', 0)}",
            f"⚠️  Тестов с полным конфликтом: {stats.get('tests_with_full_conflict', 0)}",
            "=" * 80,
            "",
            "📈 СТАТИСТИКА ПО ВСЕМ ТЕСТАМ:",
            ""
        ]
        
        # Статистика по фреймам (ВСЕ тесты)
        frame_stats = stats.get("frame_size", {})
        report_lines.append(f"  Размер фрейма (все {total_tests} тестов):")
        report_lines.append(f"    Минимальный: {frame_stats.get('min', 0)}")
        report_lines.append(f"    Максимальный: {frame_stats.get('max', 0)}")
        report_lines.append(f"    Средний: {frame_stats.get('mean', 0):.1f}")
        report_lines.append(f"    Медиана: {frame_stats.get('median', 0):.1f}")
        
        # Статистика по источникам (ВСЕ тесты)
        source_stats = stats.get("sources_count", {})
        report_lines.append(f"\n  Количество источников (все {total_tests} тестов):")
        report_lines.append(f"    Минимальное: {source_stats.get('min', 0)}")
        report_lines.append(f"    Максимальное: {source_stats.get('max', 0)}")
        report_lines.append(f"    Среднее: {source_stats.get('mean', 0):.1f}")
        report_lines.append(f"    Медиана: {source_stats.get('median', 0):.1f}")
        
        # Успешность этапов из детальных данных
        success_rates = detailed.get("step_success_rates", {})
        if success_rates:
            report_lines.append(f"\n  УСПЕШНОСТЬ ЭТАПОВ (из исходных данных итераций):")
            
            step_names = {
                "step1": "Исходные Bel/Pl",
                "step2": "Демпстер",
                "step3": "Дисконт+Демпстер",
                "step4": "Ягер",
                "total": "Полностью успешные тесты"
            }
            
            for step, step_name in step_names.items():
                if step in success_rates:
                    rate_info = success_rates[step]
                    successful = rate_info["successful"]
                    total = rate_info["total"]
                    success_rate = rate_info["success_rate"]
                    
                    if step == "total":
                        report_lines.append(f"    {step_name:30}: {successful}/{total} тестов ({success_rate:.1f}%)")
                    else:
                        report_lines.append(f"    {step_name:30}: {successful}/{total} тестов ({success_rate:.1f}%)")
        
        # Производительность по этапам (только успешные выполнения)
        perf_stats = stats.get("performance", {})
        if perf_stats:
            report_lines.append(f"\n  ПРОИЗВОДИТЕЛЬНОСТЬ (среднее время, только успешные выполнения):")
            
            step_names = {
                "step1": "Исходные Bel/Pl",
                "step2": "Демпстер",
                "step3": "Дисконт+Демпстер",
                "step4": "Ягер",
                "total": "ИТОГО (полностью успешные тесты)"
            }
            
            for step, step_name in step_names.items():
                if step in perf_stats:
                    time_data = perf_stats[step]["time_ms"]
                    mean_time = time_data["mean"]
                    sample_count = time_data["sample_count"]
                    success_count = time_data.get("success_count", sample_count)
                    success_rate = time_data["success_rate"]
                    
                    if step == "total":
                        report_lines.append(f"    {step_name:30}: {mean_time:.2f} мс (по {sample_count} тестам, {success_rate:.1f}%)")
                    elif sample_count > 0:
                        # ✅ ИСПРАВЛЕНО: используем total_tests из метаданных
                        report_lines.append(f"    {step_name:30}: {mean_time:.2f} мс (по {sample_count} тестам, {success_count}/{total_tests} успешно, {success_rate:.1f}%)")
                    else:
                        # ✅ ИСПРАВЛЕНО: используем total_tests из метаданных
                        report_lines.append(f"    {step_name:30}: НЕТ УСПЕШНЫХ ВЫПОЛНЕНИЙ (0/{total_tests})")
        
        # ДЕТАЛЬНЫЙ АНАЛИЗ НЕУДАЧНЫХ ЭТАПОВ
        failed_steps = detailed.get("failed_steps_by_test", {})
        error_types = detailed.get("error_types", {})
        
        if failed_steps:
            report_lines.append(f"\n{'='*80}")
            report_lines.append(f"🔍 ДЕТАЛЬНЫЙ АНАЛИЗ НЕУДАЧНЫХ ЭТАПОВ:")
            report_lines.append(f"{'='*80}")
            
            # Группируем по типу ошибки
            if error_types:
                report_lines.append(f"\n  РАСПРЕДЕЛЕНИЕ ОШИБОК ПО ТИПУ:")
                for error_msg, tests in error_types.items():
                    report_lines.append(f"    ❌ '{error_msg}':")
                    # Убираем дубликаты
                    unique_tests = sorted(set(tests))
                    for test_info in unique_tests[:10]:  # Показываем первые 10
                        report_lines.append(f"        - {test_info}")
                    if len(unique_tests) > 10:
                        report_lines.append(f"        ... и еще {len(unique_tests) - 10} тестов")
            
            # По тестам с указанием конкретных этапов
            report_lines.append(f"\n  НЕУДАЧНЫЕ ЭТАПЫ ПО ТЕСТАМ:")
            for test_name, failed_steps_list in failed_steps.items():
                if failed_steps_list:
                    report_lines.append(f"\n    📄 Тест: {test_name}")
                    for step_name, error_msg in failed_steps_list:
                        step_display = {
                            "step1": "Исходные Bel/Pl",
                            "step2": "Демпстер",
                            "step3": "Дисконт+Демпстер",
                            "step4": "Ягер"
                        }.get(step_name, step_name)
                        
                        # Сокращаем длинные сообщения об ошибках
                        if len(error_msg) > 80:
                            error_msg = error_msg[:77] + "..."
                        
                        report_lines.append(f"      ❌ {step_display}: {error_msg}")
        
        elif stats.get('tests_with_failed_steps', 0) == 0:
            report_lines.append(f"\n{'='*80}")
            report_lines.append(f"✅ ВСЕ ЭТАПЫ ВСЕХ ТЕСТОВ ВЫПОЛНЕНЫ УСПЕШНО!")
            report_lines.append(f"{'='*80}")
        
        # Сводка по производительности
        if perf_stats and "step1" in perf_stats and "step2" in perf_stats:
            report_lines.append(f"\n{'='*80}")
            report_lines.append(f"📊 СВОДКА ПО ПРОИЗВОДИТЕЛЬНОСТИ:")
            report_lines.append(f"{'='*80}")
            
            total_mean_time = 0
            total_successful_steps = 0
            
            for step in ["step1", "step2", "step3", "step4"]:
                if step in perf_stats:
                    time_data = perf_stats[step]["time_ms"]
                    if time_data["sample_count"] > 0:
                        total_mean_time += time_data["mean"]
                        total_successful_steps += 1
            
            if total_successful_steps > 0:
                avg_time_per_step = total_mean_time / total_successful_steps
                report_lines.append(f"  Среднее время на успешный этап: {avg_time_per_step:.2f} мс")
            
            # Время для полностью успешных тестов
            if "total" in perf_stats and perf_stats["total"]["time_ms"]["sample_count"] > 0:
                total_time = perf_stats["total"]["time_ms"]["mean"]
                report_lines.append(f"  Среднее время полного теста: {total_time:.2f} мс")
        
        # Заключение
        report_lines.append(f"\n{'='*80}")
        report_lines.append(f"🏁 ЗАКЛЮЧЕНИЕ:")
        report_lines.append(f"{'='*80}")
        
        failed_tests = stats.get('tests_with_failed_steps', 0)
        conflict_tests = stats.get('tests_with_full_conflict', 0)
        successful_tests = total_tests - failed_tests
        
        if failed_tests == 0:
            report_lines.append(f"✅ ВСЕ {total_tests} ТЕСТОВ ВЫПОЛНЕНЫ ПОЛНОСТЬЮ УСПЕШНО!")
        elif conflict_tests > 0 and failed_tests == conflict_tests:
            # Все неудачи - только полные конфликты (это нормально)
            report_lines.append(f"⚠️  НОРМАЛЬНЫЙ РЕЗУЛЬТАТ: {successful_tests}/{total_tests} тестов успешны")
            report_lines.append(f"   {conflict_tests} тестов имеют полный конфликт (K=1.0) - это ожидаемо для Демпстера")
        else:
            success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
            report_lines.append(f"🔴 ТРЕБУЕТСЯ АНАЛИЗ: {success_rate:.1f}% тестов успешны")
            if conflict_tests > 0:
                report_lines.append(f"   Из них {conflict_tests} тестов с полным конфликтом (K=1.0)")
        
        report_lines.append(f"\n📊 Результаты сохранены в: {self.run_dir}")
        
        # Сохраняем отчет
        report_path = os.path.join(self.run_dir, "aggregated", "final_report.txt")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(report_lines))
        
        # Также выводим краткую версию в консоль
        console_lines = [
            "\n" + "=" * 60,
            "📊 ИТОГОВАЯ СТАТИСТИКА:",
            "=" * 60,
            f"Всего тестов: {total_tests}",
            f"Успешных: {successful_tests}",
            f"С полным конфликтом: {conflict_tests}",
            f"С другими ошибками: {failed_tests - conflict_tests}"
        ]
        
        if failed_tests == 0:
            console_lines.append("✅ ВСЕ ТЕСТЫ УСПЕШНЫ!")
        elif conflict_tests > 0:
            console_lines.append(f"⚠️  {conflict_tests} тестов с полным конфликтом (K=1.0)")
        
        print("\n".join(console_lines))

    def cleanup(self):
        """Очистка ресурсов раннера.
        Может быть переопределен в подклассах для освобождения ресурсов.
        """
        # Базовая реализация ничего не делает
        # Подклассы могут переопределить для очистки файлов, соединений и т.д.
        pass