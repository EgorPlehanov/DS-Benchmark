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
        
        Args:
            test_data: Данные теста в формате DASS
            test_name: Имя теста (для сохранения)
            iterations: Количество итераций
            alphas: Коэффициенты дисконтирования для каждого источника
            
        Returns:
            Результаты теста
        """
        print(f"\n🧪 Запуск теста: {test_name}")
        print(f"   Итераций: {iterations}")
        
        # Инициализация результатов
        test_results = {
            "metadata": {
                "test_name": test_name,
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
        
        # Определяем коэффициенты дисконтирования (по умолчанию 0.1 для всех)
        if alphas is None:
            sources_count = self.adapter.get_sources_count(loaded_data)
            alphas = [0.1] * sources_count  # По умолчанию все 0.1
        
        # Выполняем итерации
        for i in range(iterations):
            print(f"   Итерация {i+1}/{iterations}...", end="", flush=True)
            
            iteration_results = self._run_single_iteration(
                loaded_data=loaded_data,
                test_data=test_data,
                iteration_num=i+1,
                alphas=alphas
            )
            
            test_results["iterations"].append(iteration_results)
            print(" ✓")
        
        # Агрегируем результаты итераций
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
                            alphas: List[float]) -> Dict[str, Any]:
        """
        Выполняет одну итерацию теста.
        
        Returns:
            Результаты итерации с метриками производительности
        """
        iteration_results = {
            "iteration": iteration_num,
            "performance": {}
        }
        
        # === ШАГ 1: Исходные Belief/Plausibility ===
        step1_results, step1_metrics = self._measure_performance(
            self._execute_step1,
            loaded_data,
            step_name="step1_original"
        )
        iteration_results["step1"] = step1_results
        iteration_results["performance"]["step1"] = step1_metrics
        
        # === ШАГ 2: Комбинирование Демпстером ===
        step2_results, step2_metrics = self._measure_performance(
            self._execute_step2,
            loaded_data,
            step_name="step2_dempster"
        )
        iteration_results["step2"] = step2_results
        iteration_results["performance"]["step2"] = step2_metrics
        
        # === ШАГ 3: Дисконтирование + Демпстер ===
        step3_results, step3_metrics = self._measure_performance(
            self._execute_step3,
            loaded_data,
            alphas,
            step_name="step3_discount_dempster"
        )
        iteration_results["step3"] = step3_results
        iteration_results["performance"]["step3"] = step3_metrics
        
        # === ШАГ 4: Комбинирование Ягером ===
        step4_results, step4_metrics = self._measure_performance(
            self._execute_step4,
            loaded_data,
            step_name="step4_yager"
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
        
        Returns:
            (результат_функции, метрики_производительности)
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
        except Exception as e:
            # Сохраняем ошибку в метриках
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
        metrics["time_ms"] = (end_time - start_time) * 1000  # миллисекунды
        
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
        
        # Проверяем наличие ошибок
        has_errors = False
        for iteration in test_results.get("iterations", []):
            for step in ["step1", "step2", "step3", "step4"]:
                if step in iteration.get("performance", {}) and "error" in iteration["performance"][step]:
                    has_errors = True
                    report_lines.append(f"❌ Ошибка в {step}: {iteration['performance'][step]['error']}")
        
        if has_errors:
            report_lines.append("\n📈 ПРОИЗВОДИТЕЛЬНОСТЬ (если доступно):")
        else:
            report_lines.append("📈 ПРОИЗВОДИТЕЛЬНОСТЬ:")
        
        report_lines.append("")
        
        # Добавляем метрики по шагам
        perf = aggregated.get("performance", {})
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
        
        Args:
            test_dir: Директория с тестовыми файлами (.json)
            iterations: Количество итераций для каждого теста
            max_tests: Максимальное количество тестов для запуска
            
        Returns:
            Агрегированные результаты по всем тестам
        """
        print(f"\n🚀 ЗАПУСК НАБОРА ТЕСТОВ")
        print(f"📁 Директория: {test_dir}")
        print(f"🔄 Итераций на тест: {iterations}")
        
        # Находим все JSON файлы
        test_files = []
        for root, dirs, files in os.walk(test_dir):
            for file in files:
                if file.endswith('.json') and file != "statistics.json":  # Пропускаем файл статистики
                    test_files.append(os.path.join(root, file))
        
        # Ограничиваем количество тестов если нужно
        if max_tests and max_tests < len(test_files):
            test_files = test_files[:max_tests]
        
        print(f"📄 Найдено тестов: {len(test_files)}")
        
        # Запускаем каждый тест
        successful_tests = 0
        failed_tests = 0
        
        for i, test_file in enumerate(test_files, 1):
            test_name = os.path.splitext(os.path.basename(test_file))[0]
            print(f"\n[{i}/{len(test_files)}] Тест: {test_name}")
            
            try:
                # Загружаем тестовые данные
                with open(test_file, 'r', encoding='utf-8') as f:
                    test_data = json.load(f)
                
                # Проверяем обязательные поля
                if "frame_of_discernment" not in test_data or "bba_sources" not in test_data:
                    print(f"   ❌ Неверный формат теста {test_name}")
                    failed_tests += 1
                    continue
                
                # Определяем alphas для каждого источника
                sources_count = len(test_data.get("bba_sources", []))
                alphas = [0.1] * sources_count  # По умолчанию 0.1 для всех
                
                # Запускаем тест
                self.run_test(
                    test_data=test_data,
                    test_name=test_name,
                    iterations=iterations,
                    alphas=alphas
                )
                
                successful_tests += 1
                
            except json.JSONDecodeError as e:
                print(f"   ❌ Ошибка JSON в файле {test_name}: {e}")
                failed_tests += 1
            except KeyError as e:
                print(f"   ❌ Отсутствует поле в тесте {test_name}: {e}")
                failed_tests += 1
            except Exception as e:
                print(f"   ❌ Ошибка при выполнении теста {test_name}: {e}")
                failed_tests += 1
        
        # Создаем итоговый отчет по всем тестам
        summary = self._create_summary_report()
        
        print(f"\n✅ ВЫПОЛНЕНИЕ ЗАВЕРШЕНО")
        print(f"📊 Успешных тестов: {successful_tests}/{len(test_files)}")
        print(f"📊 Неудачных тестов: {failed_tests}/{len(test_files)}")
        print(f"📊 Результаты сохранены в: {self.run_dir}")
        
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
            "statistics": {}
        }
        
        # Собираем статистику по всем тестам
        frame_sizes = []
        source_counts = []
        step_times = {
            "step1": [],
            "step2": [],
            "step3": [],
            "step4": [],
            "total": []
        }
        
        successful_tests = 0
        
        for test_result in self.results:
            metadata = test_result["metadata"]
            aggregated = test_result.get("aggregated", {})
            perf = aggregated.get("performance", {})
            
            # Проверяем, был ли тест успешным
            test_successful = True
            for iteration in test_result.get("iterations", []):
                for step in ["step1", "step2", "step3", "step4"]:
                    if step in iteration.get("performance", {}) and "error" in iteration["performance"][step]:
                        test_successful = False
                        break
                if not test_successful:
                    break
            
            if test_successful:
                successful_tests += 1
            
            # Добавляем информацию о тесте
            test_info = {
                "test_name": metadata["test_name"],
                "frame_size": metadata["frame_size"],
                "sources_count": metadata["sources_count"],
                "successful": test_successful,
                "performance": perf
            }
            summary["tests"].append(test_info)
            
            # Собираем статистику только для успешных тестов
            if test_successful:
                frame_sizes.append(metadata["frame_size"])
                source_counts.append(metadata["sources_count"])
                
                # Время по шагам
                for step in step_times.keys():
                    if step in perf:
                        time_data = perf[step].get("time_ms", {})
                        if "mean" in time_data:
                            step_times[step].append(time_data["mean"])
        
        # Вычисляем статистику
        summary["statistics"] = {
            "successful_tests": successful_tests,
            "total_tests": len(self.results),
            "success_rate": successful_tests / len(self.results) * 100 if self.results else 0,
            "frame_size": {
                "min": min(frame_sizes) if frame_sizes else 0,
                "max": max(frame_sizes) if frame_sizes else 0,
                "mean": statistics.mean(frame_sizes) if frame_sizes else 0
            },
            "sources_count": {
                "min": min(source_counts) if source_counts else 0,
                "max": max(source_counts) if source_counts else 0,
                "mean": statistics.mean(source_counts) if source_counts else 0
            },
            "performance": {}
        }
        
        # Статистика по времени
        for step, times in step_times.items():
            if times:
                summary["statistics"]["performance"][step] = {
                    "time_ms": {
                        "min": min(times),
                        "max": max(times),
                        "mean": statistics.mean(times),
                        "median": statistics.median(times),
                        "std": statistics.stdev(times) if len(times) > 1 else 0
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
        """Создает финальный текстовый отчет."""
        metadata = summary["metadata"]
        stats = summary["statistics"]
        
        report_lines = [
            "=" * 70,
            f"📊 ИТОГОВЫЙ ОТЧЕТ ПО БЕНЧМАРКУ",
            f"📅 Время: {metadata['timestamp']}",
            f"📚 Адаптер: {metadata['adapter']}",
            f"🧪 Всего тестов: {metadata['total_tests']}",
            f"✅ Успешных тестов: {stats.get('successful_tests', 0)}",
            f"📈 Успешность: {stats.get('success_rate', 0):.1f}%",
            "=" * 70,
            "",
            "📈 СТАТИСТИКА:",
            ""
        ]
        
        # Статистика по фреймам
        frame_stats = stats.get("frame_size", {})
        report_lines.append(f"  Размер фрейма (успешные тесты):")
        report_lines.append(f"    Минимальный: {frame_stats.get('min', 0)}")
        report_lines.append(f"    Максимальный: {frame_stats.get('max', 0)}")
        report_lines.append(f"    Средний: {frame_stats.get('mean', 0):.1f}")
        
        # Статистика по источникам
        source_stats = stats.get("sources_count", {})
        report_lines.append(f"\n  Количество источников (успешные тесты):")
        report_lines.append(f"    Минимальное: {source_stats.get('min', 0)}")
        report_lines.append(f"    Максимальное: {source_stats.get('max', 0)}")
        report_lines.append(f"    Среднее: {source_stats.get('mean', 0):.1f}")
        
        # Производительность по шагам
        perf_stats = stats.get("performance", {})
        if perf_stats:
            report_lines.append(f"\n  ПРОИЗВОДИТЕЛЬНОСТЬ (среднее время, мс):")
            
            step_names = {
                "step1": "Исходные Bel/Pl",
                "step2": "Демпстер",
                "step3": "Дисконт+Демпстер",
                "step4": "Ягер",
                "total": "ИТОГО"
            }
            
            for step, step_name in step_names.items():
                if step in perf_stats:
                    time_data = perf_stats[step].get("time_ms", {})
                    mean_time = time_data.get("mean", 0)
                    report_lines.append(f"    {step_name:20}: {mean_time:.2f} мс")
        
        # Сохраняем отчет
        report_file = os.path.join(self.run_dir, "aggregated", "final_report.txt")
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(report_lines))
        
        # Также выводим в консоль
        print("\n" + "\n".join(report_lines))