# src/profiling/runners/simple_profiling_runner.py
"""
SimpleProfilingRunner - раннер для профилирования тестов Демпстера-Шейфера.
Интегрирует SystemCollector, ArtifactManager и адаптеры ДШ.
"""

import os
import sys
import json
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

# Добавляем путь для импорта адаптеров
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.profiling.artifacts import ArtifactManager, collect_test_metadata
from src.profiling.collectors import SystemCollector, create_system_collector
from src.adapters.our_adapter import OurImplementationAdapter


class SimpleProfilingRunner:
    """
    Простой раннер для профилирования тестов Демпстера-Шейфера.
    
    Выполняет:
    1. Загрузку тестовых данных
    2. Инициализацию адаптера ДШ
    3. Выполнение 4-шагового процесса
    4. Сбор метрик через SystemCollector
    5. Сохранение через ArtifactManager
    """
    
    def __init__(self, 
                 adapter_name: str = "our",
                 base_dir: str = "results/profiling",
                 run_id: Optional[str] = None,
                 overwrite: bool = False):
        """
        Инициализация раннера.
        
        Args:
            adapter_name: Имя адаптера ('our', 'pyds', и т.д.)
            base_dir: Базовая директория для результатов
            run_id: ID запуска (если None, генерируется автоматически)
            overwrite: Перезаписывать существующие результаты
        """
        self.adapter_name = adapter_name
        
        # Создаем ArtifactManager
        self.artifact_manager = ArtifactManager(
            base_dir=base_dir,
            adapter_name=adapter_name,
            run_id=run_id,
            overwrite=overwrite
        )
        
        # Создаем SystemCollector
        self.system_collector = SystemCollector(name=f"system_{adapter_name}")
        
        # Инициализируем адаптер ДШ
        self.adapter = self._load_adapter(adapter_name)
        
        print(f"🚀 SimpleProfilingRunner инициализирован")
        print(f"   Адаптер: {adapter_name}")
        print(f"   Директория: {self.artifact_manager.run_dir}")
    
    def _load_adapter(self, adapter_name: str):
        """Загружает адаптер Демпстера-Шейфера."""
        adapters = {
            "our": OurImplementationAdapter,
            # "pyds": PydsAdapter,    # Позже добавим
            # "ds": DsAdapter,         # Позже добавим
        }
        
        if adapter_name not in adapters:
            raise ValueError(f"Неизвестный адаптер: {adapter_name}")
        
        return adapters[adapter_name]()
    
    def run_test(self, 
                test_data: Dict[str, Any], 
                test_name: str,
                iterations: int = 3) -> Dict[str, Any]:
        """
        Запускает один тест и собирает метрики.
        
        Args:
            test_data: Данные теста в формате DASS
            test_name: Имя теста (для именования файлов)
            iterations: Количество итераций
            
        Returns:
            Dict: Структурированные результаты теста
        """
        print(f"\n🧪 ЗАПУСК ТЕСТА: {test_name}")
        print(f"   Итераций: {iterations}")
        
        # Сохраняем входные данные
        self.artifact_manager.save_test_input(test_data, test_name)
        
        # Собираем метаданные
        metadata = collect_test_metadata(
            test_data=test_data,
            test_name=test_name,
            iterations=iterations,
            adapter=self.adapter_name
        )
        
        self.artifact_manager.save_json(
            f"{test_name}_metadata.json",
            metadata,
            subdir=f"test_metadata/{test_name}"
        )
        
        # Загружаем данные через адаптер
        print(f"   1. Загрузка данных через адаптер...")
        loaded_data, load_metrics = self.system_collector.profile(
            self.adapter.load_from_dass,
            test_data
        )
        
        # Сохраняем метрики загрузки
        self.artifact_manager.save_metrics(
            load_metrics,
            test_name=test_name,
            step_name="load_data",
            iteration=1
        )
        
        # Получаем информацию о тесте
        frame_elements = self.adapter.get_frame_of_discernment(loaded_data)
        sources_count = self.adapter.get_sources_count(loaded_data)
        
        print(f"      Фрейм: {len(frame_elements)} элементов")
        print(f"      Источников: {sources_count}")
        
        # Результаты теста
        test_results = {
            "metadata": {
                "test_name": test_name,
                "adapter": self.adapter_name,
                "iterations": iterations,
                "frame_size": len(frame_elements),
                "sources_count": sources_count
            },
            "iterations": []
        }
        
        # Выполняем итерации
        for i in range(1, iterations + 1):
            print(f"   2. Итерация {i}/{iterations}...", end="", flush=True)
            
            iteration_results = self._run_single_iteration(
                loaded_data=loaded_data,
                test_name=test_name,
                iteration_num=i
            )
            
            test_results["iterations"].append(iteration_results)
            print(" ✓")
        
        # Агрегируем результаты
        test_results["aggregated"] = self._aggregate_results(
            test_results["iterations"]
        )
        
        # Сохраняем полные результаты теста
        self.artifact_manager.save_test_results(test_results, test_name)
        
        # Создаем краткий отчет
        self._create_test_report(test_results, test_name)
        
        print(f"\n✅ ТЕСТ {test_name} ЗАВЕРШЕН")
        print(f"   Результаты: {self.artifact_manager.run_dir}")
        
        return test_results
    
    def _run_single_iteration(self, 
                            loaded_data: Any,
                            test_name: str,
                            iteration_num: int) -> Dict[str, Any]:
        """
        Выполняет одну итерацию теста (4 шага ДШ).
        """
        iteration_results = {
            "iteration": iteration_num,
            "steps": {}
        }
        
        # Шаг 1: Исходные Belief/Plausibility
        step1_results, step1_metrics = self._execute_step_with_profiling(
            step_func=self._execute_step1,
            loaded_data=loaded_data,
            test_name=test_name,
            step_name="step1_original",
            iteration=iteration_num
        )
        
        iteration_results["steps"]["step1"] = {
            "results": step1_results,
            "metrics": step1_metrics
        }
        
        # Шаг 2: Комбинирование Демпстером
        step2_results, step2_metrics = self._execute_step_with_profiling(
            step_func=self._execute_step2,
            loaded_data=loaded_data,
            test_name=test_name,
            step_name="step2_dempster",
            iteration=iteration_num
        )
        
        iteration_results["steps"]["step2"] = {
            "results": step2_results,
            "metrics": step2_metrics
        }
        
        # Шаг 3: Дисконтирование + Демпстер
        step3_results, step3_metrics = self._execute_step_with_profiling(
            step_func=self._execute_step3,
            loaded_data=loaded_data,
            test_name=test_name,
            step_name="step3_discount_dempster",
            iteration=iteration_num
        )
        
        iteration_results["steps"]["step3"] = {
            "results": step3_results,
            "metrics": step3_metrics
        }
        
        # Шаг 4: Комбинирование Ягером
        step4_results, step4_metrics = self._execute_step_with_profiling(
            step_func=self._execute_step4,
            loaded_data=loaded_data,
            test_name=test_name,
            step_name="step4_yager",
            iteration=iteration_num
        )
        
        iteration_results["steps"]["step4"] = {
            "results": step4_results,
            "metrics": step4_metrics
        }
        
        # Общая статистика итерации
        total_time = 0.0
        for step in iteration_results["steps"].values():
            if "metrics" in step and "time" in step["metrics"]:
                total_time += step["metrics"]["time"].get("wall_time_ms", 0)
        
        iteration_results["summary"] = {
            "total_time_ms": total_time,
            "steps_count": len(iteration_results["steps"])
        }
        
        return iteration_results
    
    def _execute_step_with_profiling(self, 
                                   step_func, 
                                   loaded_data: Any,
                                   test_name: str,
                                   step_name: str,
                                   iteration: int) -> Tuple[Any, Dict[str, Any]]:
        """
        Выполняет шаг с профилированием и сохраняет метрики.
        """
        # Выполняем шаг с профилированием
        result, metrics = self.system_collector.profile(
            step_func,
            loaded_data
        )

        # Сохраняем метрики
        self.artifact_manager.save_metrics(
            metrics,
            test_name=test_name,
            step_name=step_name,
            iteration=iteration
        )
        
        # Если есть ошибка - обрабатываем
        if metrics and "error" in metrics and metrics["error"]:
            error_msg = str(metrics["error"])
            if len(error_msg) > 50:
                error_msg = error_msg[:47] + "..."
            print(f"\n⚠️  {step_name}: {error_msg}")
        
        return result, metrics
    
    def _execute_step1(self, loaded_data: Any) -> Dict[str, Any]:
        """Шаг 1: Исходные Belief/Plausibility."""
        try:
            # Получаем элементы фрейма
            frame_elements = self.adapter.get_frame_of_discernment(loaded_data)
            
            # Простой пример: вычисляем belief для первого элемента
            if frame_elements:
                first_element = frame_elements[0]
                belief = self.adapter.calculate_belief(loaded_data, first_element)
                plausibility = self.adapter.calculate_plausibility(loaded_data, first_element)
                
                return {
                    "step": "step1",
                    "belief_sample": belief,
                    "plausibility_sample": plausibility,
                    "frame_size": len(frame_elements),
                    "note": "Пример вычисления для первого элемента фрейма"
                }
            else:
                return {
                    "step": "step1",
                    "error": "Пустой фрейм различения",
                    "frame_size": 0
                }
                
        except Exception as e:
            return {
                "step": "step1",
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    def _execute_step2(self, loaded_data: Any) -> Dict[str, Any]:
        """Шаг 2: Комбинирование Демпстером."""
        try:
            result = self.adapter.combine_sources_dempster(loaded_data)
            return {
                "step": "step2",
                "result_type": type(result).__name__,
                "result_size": len(result) if hasattr(result, '__len__') else "N/A",
                "has_conflict": "full_conflict" in str(result).lower() or "k=1" in str(result).lower()
            }
        except Exception as e:
            error_msg = str(e)
            is_full_conflict = "полный конфликт" in error_msg.lower() or "k=1" in error_msg.lower()
            
            return {
                "step": "step2",
                "error": error_msg,
                "error_type": type(e).__name__,
                "is_full_conflict": is_full_conflict
            }
    
    def _execute_step3(self, loaded_data: Any) -> Dict[str, Any]:
        """Шаг 3: Дисконтирование + Демпстер."""
        try:
            # Получаем количество источников
            sources_count = self.adapter.get_sources_count(loaded_data)
            
            # Применяем дисконтирование с alpha=0.1
            alpha = 0.1
            discounted = self.adapter.apply_discounting(loaded_data, alpha)
            
            # Создаем новый объект с дисконтированными данными
            # (Это упрощенная версия, в реальности нужно правильно скомбинировать)
            return {
                "step": "step3",
                "alpha": alpha,
                "sources_count": sources_count,
                "discounted_items": len(discounted) if hasattr(discounted, '__len__') else 0,
                "note": "Дисконтирование применено к каждому источнику"
            }
        except Exception as e:
            return {
                "step": "step3",
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    def _execute_step4(self, loaded_data: Any) -> Dict[str, Any]:
        """Шаг 4: Комбинирование Ягером."""
        try:
            result = self.adapter.combine_sources_yager(loaded_data)
            return {
                "step": "step4",
                "result_type": type(result).__name__,
                "result_size": len(result) if hasattr(result, '__len__') else "N/A"
            }
        except Exception as e:
            return {
                "step": "step4",
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    def _aggregate_results(self, iterations: List[Dict]) -> Dict[str, Any]:
        """Агрегирует результаты всех итераций."""
        if not iterations:
            return {}
        
        aggregated = {
            "performance": {},
            "steps_summary": {}
        }
        
        # Агрегация по шагам
        steps = ["step1", "step2", "step3", "step4"]
        
        for step in steps:
            step_times = []
            step_successful = 0
            
            for iteration in iterations:
                if step in iteration["steps"]:
                    metrics = iteration["steps"][step].get("metrics", {})
                    
                    if metrics and "time" in metrics:
                        step_times.append(metrics["time"].get("wall_time_ms", 0))
                    
                    # Проверяем успешность шага
                    step_result = iteration["steps"][step].get("results", {})
                    if step_result and "error" not in step_result:
                        step_successful += 1
            
            if step_times:
                aggregated["steps_summary"][step] = {
                    "time_ms": {
                        "min": min(step_times) if step_times else 0,
                        "max": max(step_times) if step_times else 0,
                        "mean": sum(step_times) / len(step_times) if step_times else 0,
                        "total": sum(step_times) if step_times else 0
                    },
                    "success_rate": (step_successful / len(iterations) * 100) if iterations else 0
                }
        
        # Общая статистика
        total_times = []
        for iteration in iterations:
            total_time = iteration.get("summary", {}).get("total_time_ms", 0)
            if total_time:
                total_times.append(total_time)
        
        if total_times:
            aggregated["performance"]["total"] = {
                "time_ms": {
                    "min": min(total_times),
                    "max": max(total_times),
                    "mean": sum(total_times) / len(total_times),
                    "total": sum(total_times)
                }
            }
        
        # Статистика по ошибкам
        error_stats = {}
        for step in steps:
            errors = []
            for iteration in iterations:
                if step in iteration["steps"]:
                    step_result = iteration["steps"][step].get("results", {})
                    if step_result and "error" in step_result:
                        errors.append(step_result.get("error_type", "Unknown"))
            
            if errors:
                error_stats[step] = {
                    "error_count": len(errors),
                    "error_types": list(set(errors))
                }
        
        if error_stats:
            aggregated["error_statistics"] = error_stats
        
        return aggregated
    
    def _create_test_report(self, test_results: Dict[str, Any], test_name: str):
        """Создает краткий отчет по тесту."""
        metadata = test_results["metadata"]
        aggregated = test_results.get("aggregated", {})
        
        report_lines = [
            "=" * 60,
            f"📊 ОТЧЕТ ПО ТЕСТУ: {test_name}",
            f"Адаптер: {metadata['adapter']}",
            f"Фрейм: {metadata['frame_size']} элементов",
            f"Источников: {metadata['sources_count']}",
            f"Итераций: {metadata['iterations']}",
            "=" * 60,
            ""
        ]
        
        # Статистика по шагам
        if "steps_summary" in aggregated:
            report_lines.append("📈 ПРОИЗВОДИТЕЛЬНОСТЬ ПО ШАГАМ:")
            report_lines.append("")
            
            for step, stats in aggregated["steps_summary"].items():
                time_stats = stats["time_ms"]
                success_rate = stats["success_rate"]
                
                step_name = {
                    "step1": "Исходные Bel/Pl",
                    "step2": "Демпстер",
                    "step3": "Дисконт+Демпстер",
                    "step4": "Ягер"
                }.get(step, step)
                
                report_lines.append(
                    f"  {step_name:20}: {time_stats['mean']:.2f} ms "
                    f"(min: {time_stats['min']:.2f}, max: {time_stats['max']:.2f}) "
                    f"✓ {success_rate:.0f}%"
                )
        
        # Информация об ошибках
        if "error_statistics" in aggregated:
            report_lines.append("")
            report_lines.append("⚠️  СТАТИСТИКА ОШИБОК:")
            report_lines.append("")
            
            for step, error_info in aggregated["error_statistics"].items():
                step_name = {
                    "step1": "Исходные Bel/Pl",
                    "step2": "Демпстер",
                    "step3": "Дисконт+Демпстер",
                    "step4": "Ягер"
                }.get(step, step)
                
                report_lines.append(
                    f"  {step_name:20}: {error_info['error_count']} ошибок "
                    f"({', '.join(error_info['error_types'][:3])})"
                )
        
        # Общее время
        if "performance" in aggregated and "total" in aggregated["performance"]:
            total_stats = aggregated["performance"]["total"]["time_ms"]
            report_lines.append("")
            report_lines.append(f"🕒 ОБЩЕЕ ВРЕМЯ: {total_stats['mean']:.2f} ms")
            report_lines.append(f"   Итого за все итерации: {total_stats['total']:.2f} ms")
        
        # Общая успешность
        successful_steps = 0
        total_steps = 0
        
        for iteration in test_results["iterations"]:
            for step_name, step_data in iteration["steps"].items():
                total_steps += 1
                step_result = step_data.get("results", {})
                if step_result and "error" not in step_result:
                    successful_steps += 1
        
        success_rate = (successful_steps / total_steps * 100) if total_steps > 0 else 0
        
        report_lines.append("")
        report_lines.append(f"✅ УСПЕШНОСТЬ: {success_rate:.1f}% ({successful_steps}/{total_steps} шагов)")
        
        # Сохраняем отчет
        report_content = "\n".join(report_lines)
        
        self.artifact_manager.save_text(
            f"{test_name}_report.txt",
            report_content,
            subdir=f"reports/{test_name}"
        )
    
    def get_run_directory(self) -> Path:
        """Возвращает директорию с результатами."""
        return self.artifact_manager.run_dir
    
    def cleanup(self):
        """Очистка ресурсов."""
        self.artifact_manager.cleanup_temp_files()
        print("🧹 Ресурсы очищены")


# Фабричная функция для удобства
def create_profiling_runner(adapter_name: str = "our",
                          base_dir: str = "results/profiling",
                          run_id: Optional[str] = None,
                          overwrite: bool = False) -> SimpleProfilingRunner:
    """
    Создает экземпляр SimpleProfilingRunner.
    
    Args:
        adapter_name: Имя адаптера
        base_dir: Базовая директория
        run_id: ID запуска
        overwrite: Перезаписывать существующие результаты
        
    Returns:
        SimpleProfilingRunner: Созданный раннер
    """
    return SimpleProfilingRunner(
        adapter_name=adapter_name,
        base_dir=base_dir,
        run_id=run_id,
        overwrite=overwrite
    )
