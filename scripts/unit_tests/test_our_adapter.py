# scripts/testing_modules/test_our_adapter.py
#!/usr/bin/env python3
"""
ПОЛНЫЙ тест адаптера для нашей реализации Демпстера-Шейфера
Тестирует ВСЕ методы адаптера с валидацией и записью результатов
"""

import sys
import os
import json
import time
import math
from datetime import datetime
from typing import Dict, Any, List

# Добавляем src в путь
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.adapters.our_adapter import OurImplementationAdapter
from src.generators.validator import DassValidator


class OurAdapterTester:
    """Полный тестер адаптера нашей реализации"""
    
    def __init__(self, output_dir: str = "results/unit_tests/our_adapter_test"):
        """Инициализация тестера"""
        self.adapter = OurImplementationAdapter()
        self.output_dir = output_dir
        self.results = {
            "metadata": {
                "test_name": "OurAdapter_Full_Test",
                "timestamp": datetime.now().isoformat(),
                "adapter_version": "1.0",
                "description": "Полное тестирование адаптера нашей реализации Демпстера-Шейфера"
            },
            "tests": {},
            "summary": {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "errors": []
            }
        }
        
        # Создаем директорию для результатов
        os.makedirs(output_dir, exist_ok=True)
    
    def _assert_equal(self, actual, expected, tolerance=1e-10, message=""):
        """Проверка равенства с учетом погрешности"""
        if isinstance(actual, float) and isinstance(expected, float):
            is_equal = math.isclose(actual, expected, rel_tol=tolerance, abs_tol=tolerance)
        else:
            is_equal = actual == expected
        
        if not is_equal:
            error_msg = f"{message}: ожидалось {expected}, получено {actual}"
            print(f"❌ {error_msg}")
            self.results["summary"]["errors"].append(error_msg)
            return False
        
        return True
    
    def _run_test(self, test_name: str, test_func) -> bool:
        """Запуск одного теста с обработкой ошибок"""
        self.results["summary"]["total_tests"] += 1
        
        try:
            print(f"\n{'='*60}")
            print(f"🧪 Тест: {test_name}")
            print(f"{'='*60}")
            
            result = test_func()
            if result:
                self.results["summary"]["passed"] += 1
                print(f"✅ Тест '{test_name}' пройден успешно")
            else:
                self.results["summary"]["failed"] += 1
            
            return result
        except Exception as e:
            self.results["summary"]["failed"] += 1
            error_msg = f"Ошибка в тесте '{test_name}': {str(e)}"
            print(f"❌ {error_msg}")
            self.results["summary"]["errors"].append(error_msg)
            import traceback
            traceback.print_exc()
            return False
    
    def _create_test_dass(self) -> Dict[str, Any]:
        """Создание тестовых данных в формата DASS"""
        return {
            "metadata": {
                "format": "DASS",
                "version": "1.0",
                "description": "Тестовые данные для проверки адаптера",
                "generated_at": datetime.now().isoformat(),
                "test_type": "adapter_validation"
            },
            "frame_of_discernment": ["A", "B", "C"],
            "bba_sources": [
                {
                    "id": "source_1",
                    "description": "Первый источник - простое распределение",
                    "bba": {
                        "{}": 0.0,
                        "{A}": 0.3,
                        "{B}": 0.3,
                        "{C}": 0.1,
                        "{A,B}": 0.2,
                        "{B,C}": 0.1
                    }
                },
                {
                    "id": "source_2",
                    "description": "Второй источник - частичный конфликт",
                    "bba": {
                        "{}": 0.1,
                        "{A}": 0.2,
                        "{B}": 0.2,
                        "{A,B}": 0.3,
                        "{A,B,C}": 0.2
                    }
                }
            ]
        }
    
    def test_01_load_from_dass(self) -> bool:
        """Тест загрузки данных из DASS формата"""
        test_dass = self._create_test_dass()
        
        # Загружаем данные
        data = self.adapter.load_from_dass(test_dass)
        
        # Проверяем структуру
        checks = [
            ("data содержит frame", "frame" in data),
            ("data содержит bpas", "bpas" in data),
            ("data содержит original_dass", "original_dass" in data),
            ("bpas это список", isinstance(data.get("bpas"), list)),
            ("frame это set", isinstance(data.get("frame"), set)),
            ("2 источника", len(data.get("bpas", [])) == 2)
        ]
        
        all_ok = True
        for msg, condition in checks:
            if condition:
                print(f"   ✓ {msg}")
            else:
                print(f"   ❌ {msg}")
                all_ok = False
        
        # Дополнительная проверка
        frame = self.adapter.get_frame_of_discernment(data)
        print(f"   ✓ Фрейм различения: {frame}")
        
        sources_count = self.adapter.get_sources_count(data)
        print(f"   ✓ Количество источников: {sources_count}")
        
        # Проверяем BPA первого источника
        if data["bpas"]:
            first_bpa = data["bpas"][0]
            print(f"   ✓ Первый BPA содержит {len(first_bpa)} подмножеств")
            
            # Проверяем, что сумма масс = 1.0
            total_mass = sum(first_bpa.values())
            all_ok = self._assert_equal(
                total_mass, 1.0, 
                message="Сумма масс BPA != 1.0"
            )
        
        return all_ok
    
    def test_02_calculate_plausibility(self) -> bool:
        """Тест вычисления функции правдоподобия (только для одиночных элементов)"""
        test_dass = self._create_test_dass()
        data = self.adapter.load_from_dass(test_dass)
        
        # Берем первый источник
        if not data["bpas"]:
            return False
        
        source_data = {"frame": data["frame"], "bpa": data["bpas"][0]}
        
        # Тестируем только одиночные элементы и универсум
        test_cases = [
            # (событие, ожидаемый plausibility, описание)
            ("{A}", 0.5, "Pl({A}) = m({A}) + m({A,B}) = 0.3 + 0.2"),
            ("{B}", 0.6, "Pl({B}) = m({B}) + m({A,B}) + m({B,C}) = 0.3 + 0.2 + 0.1"),
            ("{C}", 0.2, "Pl({C}) = m({C}) + m({B,C}) = 0.1 + 0.1"),
            ("{A,B,C}", 1.0, "Pl(Ω) всегда 1.0"),
        ]
        
        all_ok = True
        for event_str, expected_pl, description in test_cases:
            actual_pl = self.adapter.calculate_plausibility(source_data, event_str)
            
            ok = self._assert_equal(
                actual_pl, expected_pl, 
                tolerance=1e-8,
                message=f"{description}"
            )
            
            if ok:
                print(f"   ✓ {description}: {actual_pl:.6f} ≈ {expected_pl:.6f}")
            else:
                print(f"   ❌ {description}: {actual_pl:.6f} != {expected_pl:.6f}")
                all_ok = False
        
        # Проверяем свойство: Pl(A) ≥ m(A) для одиночных элементов
        print(f"\n   Проверка свойства Pl(A) ≥ m(A):")
        single_elements = ["{A}", "{B}", "{C}"]
        for event_str in single_elements:
            # Получаем базовую вероятность назначения
            event_set = self.adapter._parse_event(event_str)
            m_value = data["bpas"][0].get(frozenset(event_set), 0.0)
            
            pl = self.adapter.calculate_plausibility(source_data, event_str)
            
            if pl >= m_value - 1e-10:
                print(f"   ✓ Свойство Pl{event_str} ≥ m{event_str} выполняется: {pl:.6f} ≥ {m_value:.6f}")
            else:
                print(f"   ❌ Нарушено свойство Pl{event_str} ≥ m{event_str}: {pl:.6f} < {m_value:.6f}")
                all_ok = False
        
        return all_ok
    
    def test_03_combine_sources_dempster(self) -> bool:
        """Тест комбинирования по Демпстеру"""
        test_dass = self._create_test_dass()
        data = self.adapter.load_from_dass(test_dass)
        
        print("   Комбинируем 2 источника по правилу Демпстера...")
        
        # Комбинируем все источники
        combined = self.adapter.combine_sources_dempster(data)
        
        # Проверяем результат
        checks = [
            ("Результат - словарь", isinstance(combined, dict)),
            ("Результат не пустой", len(combined) > 0),
            ("Сумма масс ≈ 1.0", math.isclose(sum(combined.values()), 1.0, rel_tol=1e-10))
        ]
        
        all_ok = True
        for msg, condition in checks:
            if condition:
                print(f"   ✓ {msg}")
            else:
                print(f"   ❌ {msg}")
                all_ok = False
        
        # Выводим результат
        print(f"   ✓ Результат содержит {len(combined)} подмножеств:")
        for subset, mass in sorted(combined.items(), key=lambda x: x[1], reverse=True):
            if mass > 0.001:  # Показываем только значимые
                print(f"       {subset}: {mass:.6f}")
        
        # Проверяем Plausibility для одиночных элементов после комбинирования
        print(f"\n   Plausibility после комбинирования Демпстера:")
        single_elements = ["{A}", "{B}", "{C}"]
        combined_data = {"frame": data["frame"], "bpa": self._convert_bpa_to_frozenset(combined)}
        
        for event_str in single_elements:
            pl = self.adapter.calculate_plausibility(combined_data, event_str)
            print(f"       {event_str}: Pl={pl:.6f}")
        
        return all_ok
    
    def test_04_apply_discounting(self) -> bool:
        """Тест дисконтирования"""
        test_dass = self._create_test_dass()
        data = self.adapter.load_from_dass(test_dass)
        
        alpha = 0.1  # Коэффициент дисконтирования
        
        print(f"   Применяем дисконтирование с α={alpha}...")
        
        # Дисконтируем каждый источник
        discounted_list = self.adapter.apply_discounting(data, alpha)
        
        # Проверяем результат
        checks = [
            ("Результат - список", isinstance(discounted_list, list)),
            ("Столько же источников", len(discounted_list) == len(data["bpas"])),
        ]
        
        all_ok = True
        for msg, condition in checks:
            if condition:
                print(f"   ✓ {msg}")
            else:
                print(f"   ❌ {msg}")
                all_ok = False
        
        # Проверяем каждый дисконтированный BPA
        for i, (original_bpa, discounted_bpa) in enumerate(zip(data["bpas"], discounted_list)):
            total_mass = sum(discounted_bpa.values())
            if math.isclose(total_mass, 1.0, rel_tol=1e-10):
                print(f"   ✓ Источник {i+1}: сумма масс = {total_mass:.10f}")
            else:
                print(f"   ❌ Источник {i+1}: сумма масс = {total_mass:.10f}")
                all_ok = False
        
        # ВЫВОД ВСЕХ ВЕРОЯТНОСТЕЙ ДО И ПОСЛЕ ДИСКОНТИРОВАНИЯ
        print(f"\n   Подробное сравнение вероятностей до/после дисконтирования:")
        
        for source_idx, (original_bpa, discounted_bpa) in enumerate(zip(data["bpas"], discounted_list)):
            print(f"\n   ═══════════════════════════════════════════════════")
            print(f"   Источник {source_idx + 1}:")
            print(f"   ═══════════════════════════════════════════════════")
            
            # Конвертируем оригинальный BPA в строковый формат для сравнения
            original_bpa_str = self._convert_frozenset_bpa_to_string(original_bpa)
            
            # Собираем все подмножества из обоих BPA
            all_subsets = set(original_bpa_str.keys()) | set(discounted_bpa.keys())
            
            # Сортируем подмножества для удобства сравнения
            sorted_subsets = sorted(all_subsets, key=lambda x: (len(x), x))
            
            print(f"   {'Подмножество':15} | {'До (m)':>10} | {'После (mα)':>10} | {'Ожидаемое':>10} | {'Разница':>10}")
            print(f"   {'-'*15}-+-{'-'*10}-+-{'-'*10}-+-{'-'*10}-+-{'-'*10}")
            
            for subset_str in sorted_subsets:
                # Получаем значения до дисконтирования
                original_mass = original_bpa_str.get(subset_str, 0.0)
                
                # Получаем значения после дисконтирования
                discounted_mass = discounted_bpa.get(subset_str, 0.0)
                
                # Вычисляем ожидаемое значение по формуле дисконтирования
                # Для универсального множества: mα(Ω) = m(Ω) + α * (1 - m(Ω))
                # Для остальных: mα(A) = (1 - α) * m(A)
                
                if subset_str == "{A,B,C}":  # Универсальное множество
                    expected_mass = original_mass + alpha * (1.0 - original_mass)
                else:
                    expected_mass = (1 - alpha) * original_mass
                
                # Проверяем корректность
                is_correct = math.isclose(discounted_mass, expected_mass, rel_tol=1e-8)
                
                # Вычисляем разницу
                diff = discounted_mass - expected_mass
                
                # Форматируем вывод
                status = "✓" if is_correct else "✗"
                original_fmt = f"{original_mass:.6f}" if original_mass > 0 else "0.0"
                discounted_fmt = f"{discounted_mass:.6f}" if discounted_mass > 0 else "0.0"
                expected_fmt = f"{expected_mass:.6f}" if expected_mass > 0 else "0.0"
                diff_fmt = f"{diff:+.6f}" if abs(diff) > 1e-10 else "0.0"
                
                print(f"   {subset_str:15} | {original_fmt:>10} | {discounted_fmt:>10} | {expected_fmt:>10} | {diff_fmt:>10} {status}")
                
                if not is_correct:
                    all_ok = False
        
        # Проверяем, что масса универсального множества увеличилась
        print(f"\n   Проверка изменения массы универсума:")
        for i, (original_bpa, discounted_bpa) in enumerate(zip(data["bpas"], discounted_list)):
            # Находим массу универсального множества
            omega_key = "{A,B,C}"
            
            # Конвертируем оригинальный BPA в строковый формат
            original_bpa_str = self._convert_frozenset_bpa_to_string(original_bpa)
            
            omega_original = original_bpa_str.get(omega_key, 0.0)
            omega_discounted = discounted_bpa.get(omega_key, 0.0)
            
            print(f"       Источник {i+1}: Ω масса была {omega_original:.6f}, стала {omega_discounted:.6f}")
            
            # После дисконтирования часть массы переходит в Ω
            # Ω_новый = Ω_старый + α * (1 - Ω_старый)
            expected_omega = omega_original + alpha * (1.0 - omega_original)
            
            if math.isclose(omega_discounted, expected_omega, rel_tol=1e-8):
                print(f"       ✓ Ω масса корректна: {omega_discounted:.6f} ≈ {expected_omega:.6f}")
            else:
                print(f"       ❌ Ω масса некорректна: {omega_discounted:.6f} != {expected_omega:.6f}")
                all_ok = False
        
        # Проверяем сохранение суммы вероятностей
        print(f"\n   Проверка сохранения суммы вероятностей:")
        for i, (original_bpa, discounted_bpa) in enumerate(zip(data["bpas"], discounted_list)):
            total_original = sum(self._convert_frozenset_bpa_to_string(original_bpa).values())
            total_discounted = sum(discounted_bpa.values())
            
            if math.isclose(total_original, 1.0, rel_tol=1e-10) and math.isclose(total_discounted, 1.0, rel_tol=1e-10):
                print(f"       ✓ Источник {i+1}: сумма сохранена (1.0)")
            else:
                print(f"       ❌ Источник {i+1}: сумма нарушена (было {total_original:.6f}, стало {total_discounted:.6f})")
                all_ok = False
        
        return all_ok

    def test_05_combine_sources_yager(self) -> bool:
        """Тест комбинирования по Ягеру"""
        test_dass = self._create_test_dass()
        data = self.adapter.load_from_dass(test_dass)
        
        print("   Комбинируем 2 источника по правилу Ягера...")
        
        # Комбинируем все источники
        combined = self.adapter.combine_sources_yager(data)
        
        # Проверяем результат
        checks = [
            ("Результат - словарь", isinstance(combined, dict)),
            ("Результат не пустой", len(combined) > 0),
            ("Сумма масс ≈ 1.0", math.isclose(sum(combined.values()), 1.0, rel_tol=1e-10))
        ]
        
        all_ok = True
        for msg, condition in checks:
            if condition:
                print(f"   ✓ {msg}")
            else:
                print(f"   ❌ {msg}")
                all_ok = False
        
        # ВЫВОД КОМБИНИРОВАННЫХ ЗНАЧЕНИЙ
        print(f"\n   ═══════════════════════════════════════════════════")
        print(f"   КОМБИНИРОВАННЫЕ ЗНАЧЕНИЯ (Ягер):")
        print(f"   ═══════════════════════════════════════════════════")
        
        # Сортируем результаты по убыванию массы
        sorted_results = sorted(combined.items(), key=lambda x: x[1], reverse=True)
        
        total_mass = 0.0
        for subset_str, mass in sorted_results:
            if mass > 0.000001:  # Показываем только ненулевые
                print(f"   {subset_str:15}: {mass:.6f}")
                total_mass += mass
        
        # Проверяем сумму
        if math.isclose(total_mass, 1.0, rel_tol=1e-10):
            print(f"   {'Сумма':15}: {total_mass:.6f} ✓")
        else:
            print(f"   {'Сумма':15}: {total_mass:.6f} ✗ (должна быть 1.0)")
            all_ok = False
        
        # ВЫЧИСЛЕНИЕ Pl ДЛЯ ОТДЕЛЬНЫХ СОБЫТИЙ
        print(f"\n   ═══════════════════════════════════════════════════")
        print(f"   PLAUSIBILITY ДЛЯ ОТДЕЛЬНЫХ СОБЫТИЙ (Ягер):")
        print(f"   ═══════════════════════════════════════════════════")
        
        # Конвертируем combined в формат для вычислений
        combined_data = {"frame": data["frame"], "bpa": self._convert_bpa_to_frozenset(combined)}
        
        # Вычисляем Pl для одиночных элементов
        single_events = ["{A}", "{B}", "{C}"]
        
        print(f"   {'Событие':10} | {'Pl(событие)':>12} | {'Формула расчета'}")
        print(f"   {'-'*10}-+-{'-'*12}-+-{'-'*40}")
        
        for event_str in single_events:
            pl = self.adapter.calculate_plausibility(combined_data, event_str)
            
            # Формируем формулу расчета
            if event_str == "{A}":
                formula = "m({A}) + m({A,B}) + m({A,B,C})"
            elif event_str == "{B}":
                formula = "m({B}) + m({A,B}) + m({B,C}) + m({A,B,C})"
            elif event_str == "{C}":
                formula = "m({C}) + m({B,C}) + m({A,B,C})"
            else:
                formula = ""
            
            print(f"   {event_str:10} | {pl:12.6f} | {formula}")
        
        # Вычисляем Pl для универсума (всегда 1.0)
        pl_omega = self.adapter.calculate_plausibility(combined_data, "{A,B,C}")
        print(f"\n   Pl(Ω): {pl_omega:.6f}")
        
        if math.isclose(pl_omega, 1.0, rel_tol=1e-10):
            print(f"   ✓ Pl(Ω) = 1.0 (корректно)")
        else:
            print(f"   ❌ Pl(Ω) = {pl_omega:.6f} ≠ 1.0 (ошибка)")
            all_ok = False
        
        # ПРОВЕРКА КОРРЕКТНОСТИ РАСЧЕТОВ
        print(f"\n   ═══════════════════════════════════════════════════")
        print(f"   ПРОВЕРКА КОРРЕКТНОСТИ РАСЧЕТОВ:")
        print(f"   ═══════════════════════════════════════════════════")
        
        print(f"   1. Проверка формулы Pl(A):")
        
        for event_str in single_events + ["{A,B,C}"]:
            event_set = self.adapter._parse_event(event_str)
            
            # Вычисляем Pl вручную через формулу
            manual_pl = 0.0
            contributing_subsets = []
            
            for subset_str, mass in combined.items():
                subset = self.adapter._parse_subset_str(subset_str)
                if subset.intersection(event_set):
                    manual_pl += mass
                    if mass > 0.000001:
                        contributing_subsets.append((subset_str, mass))
            
            # Получаем Pl через адаптер
            adapter_pl = self.adapter.calculate_plausibility(combined_data, event_str)
            
            # Проверяем корректность
            is_correct = math.isclose(manual_pl, adapter_pl, rel_tol=1e-10)
            
            if is_correct:
                print(f"   ✓ Pl{event_str} = {adapter_pl:.6f}")
                if contributing_subsets and event_str != "{A,B,C}":
                    contributions = ", ".join([f"{s}:{m:.3f}" for s, m in contributing_subsets])
                    print(f"     Вклады: {contributions}")
            else:
                print(f"   ❌ Pl{event_str}: ручной={manual_pl:.6f}, адаптер={adapter_pl:.6f}")
                all_ok = False
        
        # Проверка специфичного для Ягера свойства
        print(f"\n   2. Проверка специфичного для Ягера свойства:")
        omega_mass = combined.get("{A,B,C}", 0.0)
        
        if omega_mass > 0:
            print(f"   ✓ Масса Ω = {omega_mass:.6f} > 0 (по Ягеру конфликт идет в Ω)")
            
            # Проверяем, что это действительно конфликт
            # Если есть подмножества с нулевой массой после комбинирования, значит был конфликт
            zero_mass_subsets = []
            for subset_str in ["{A}", "{B}", "{C}", "{A,B}", "{B,C}", "{}"]:
                if combined.get(subset_str, 0.0) == 0:
                    zero_mass_subsets.append(subset_str)
            
            if zero_mass_subsets:
                print(f"   ⚠️  Нулевые массы: {', '.join(zero_mass_subsets)} (возможный конфликт)")
        else:
            print(f"   ⚠️  Масса Ω = 0 (может быть при полном согласии источников)")
        
        return all_ok
    
    def test_06_edge_cases(self) -> bool:
        """Тест граничных случаев"""
        all_ok = True
        
        print("   Тестируем граничные случаи...")
        
        # 1. Один элемент фрейма
        print("   1. Фрейм из одного элемента...")
        single_dass = {
            "frame_of_discernment": ["A"],
            "bba_sources": [{"id": "single", "bba": {"{A}": 1.0}}]
        }
        
        try:
            data = self.adapter.load_from_dass(single_dass)
            pl = self.adapter.calculate_plausibility(data, "{A}")
            if math.isclose(pl, 1.0, rel_tol=1e-10):
                print(f"   ✓ Pl({{A}}) = 1.0 для фрейма из одного элемента")
            else:
                print(f"   ❌ Pl({{A}}) = {pl}, ожидалось 1.0")
                all_ok = False
        except Exception as e:
            print(f"   ❌ Ошибка с фреймом из одного элемента: {e}")
            all_ok = False
        
        # 2. Максимальный конфликт
        print("   2. Максимальный конфликт...")
        conflict_dass = {
            "frame_of_discernment": ["A", "B"],
            "bba_sources": [
                {"id": "conflict1", "bba": {"{A}": 1.0}},
                {"id": "conflict2", "bba": {"{B}": 1.0}}
            ]
        }
        
        try:
            data = self.adapter.load_from_dass(conflict_dass)
            combined = self.adapter.combine_sources_dempster(data)
            
            # При максимальном конфликте должно быть исключение
            print(f"   ❌ Ожидалось исключение при полном конфликте, но его не было")
            all_ok = False
            
        except ValueError as e:
            if "Полный конфликт" in str(e) or "конфликт" in str(e).lower():
                print(f"   ✓ Корректное исключение при полном конфликте: {e}")
            else:
                print(f"   ❌ Неожиданное исключение: {e}")
                all_ok = False
        except Exception as e:
            print(f"   ❌ Ошибка при максимальном конфликте: {e}")
            all_ok = False
        
        # 3. Идентичные источники (ИСПРАВЛЕННЫЙ ТЕСТ)
        print("   3. Идентичные источники...")
        identical_dass = {
            "frame_of_discernment": ["A", "B"],
            "bba_sources": [
                {"id": "source1", "bba": {"{A}": 0.3, "{B}": 0.7}},
                {"id": "source2", "bba": {"{A}": 0.3, "{B}": 0.7}}
            ]
        }
        
        try:
            data = self.adapter.load_from_dass(identical_dass)
            combined = self.adapter.combine_sources_dempster(data)
            
            # При комбинировании идентичных источников результат НЕ будет тем же самым
            # Рассчитываем ожидаемый результат по формуле Демпстера:
            # m12(A) = [m1(A)*m2(A) + m1(A)*m2(Ω) + m1(Ω)*m2(A)] / (1 - K)
            # где Ω = {A,B}, m(Ω) = 0 (в нашем случае)
            # K = m1(A)*m2(B) + m1(B)*m2(A) = 0.3*0.7 + 0.7*0.3 = 0.42
            # m12(A) = (0.3*0.3) / (1 - 0.42) = 0.09 / 0.58 = 0.155172...
            # m12(B) = (0.7*0.7) / (1 - 0.42) = 0.49 / 0.58 = 0.844827...
            
            expected_a = (0.3 * 0.3) / (1 - (0.3*0.7 + 0.7*0.3))  # 0.09 / 0.58
            expected_b = (0.7 * 0.7) / (1 - (0.3*0.7 + 0.7*0.3))  # 0.49 / 0.58
            
            # Конвертируем результат для сравнения
            combined_converted = self._convert_string_bpa_to_dict(combined)
            
            # Проверяем, что массы близки к ожидаемым
            actual_a = combined_converted.get("{A}", 0.0)
            actual_b = combined_converted.get("{B}", 0.0)
            
            print(f"   Расчет ожидаемых значений:")
            print(f"     Конфликт K = m1(A)*m2(B) + m1(B)*m2(A) = 0.3*0.7 + 0.7*0.3 = 0.42")
            print(f"     Нормализующий множитель = 1 - K = 0.58")
            print(f"     m12(A) = (0.3*0.3) / 0.58 = {expected_a:.6f}")
            print(f"     m12(B) = (0.7*0.7) / 0.58 = {expected_b:.6f}")
            print(f"\n   Проверка результатов:")
            
            if math.isclose(actual_a, expected_a, rel_tol=1e-6):
                print(f"   ✓ {{A}}: {actual_a:.6f} ≈ {expected_a:.6f}")
            else:
                print(f"   ❌ {{A}}: {actual_a:.6f} ≠ {expected_a:.6f}")
                all_ok = False
            
            if math.isclose(actual_b, expected_b, rel_tol=1e-6):
                print(f"   ✓ {{B}}: {actual_b:.6f} ≈ {expected_b:.6f}")
            else:
                print(f"   ❌ {{B}}: {actual_b:.6f} ≠ {expected_b:.6f}")
                all_ok = False
            
            # Дополнительная проверка: сумма должна быть 1.0
            total = sum(combined_converted.values())
            if math.isclose(total, 1.0, rel_tol=1e-10):
                print(f"   ✓ Сумма масс: {total:.6f} = 1.0")
            else:
                print(f"   ❌ Сумма масс: {total:.6f} ≠ 1.0")
                all_ok = False
            
        except Exception as e:
            print(f"   ❌ Ошибка с идентичными источниками: {e}")
            all_ok = False
        
        # 4. Три идентичных источника (дополнительная проверка)
        print("\n   4. Три идентичных источника...")
        triple_dass = {
            "frame_of_discernment": ["A", "B"],
            "bba_sources": [
                {"id": "source1", "bba": {"{A}": 0.4, "{B}": 0.6}},
                {"id": "source2", "bba": {"{A}": 0.4, "{B}": 0.6}},
                {"id": "source3", "bba": {"{A}": 0.4, "{B}": 0.6}}
            ]
        }
        
        try:
            data = self.adapter.load_from_dass(triple_dass)
            combined = self.adapter.combine_sources_dempster(data)
            
            # Проверяем корректность результата
            combined_converted = self._convert_string_bpa_to_dict(combined)
            
            actual_a = combined_converted.get("{A}", 0.0)
            actual_b = combined_converted.get("{B}", 0.0)
            total = sum(combined_converted.values())
            
            # Хотя мы не знаем точное ожидаемое значение для 3 источников,
            # мы можем проверить некоторые свойства
            print(f"   Проверка свойств для 3 источников:")
            
            if 0 < actual_a < 1 and 0 < actual_b < 1:
                print(f"   ✓ 0 < m(A)={actual_a:.6f} < 1")
                print(f"   ✓ 0 < m(B)={actual_b:.6f} < 1")
            else:
                print(f"   ❌ Значения вышли за пределы (0,1)")
                all_ok = False
            
            if math.isclose(total, 1.0, rel_tol=1e-10):
                print(f"   ✓ Сумма масс: {total:.6f} = 1.0")
            else:
                print(f"   ❌ Сумма масс: {total:.6f} ≠ 1.0")
                all_ok = False
            
            # Масса A должна быть меньше исходной 0.4, т.к. есть конфликт
            if actual_a < 0.4:
                print(f"   ✓ m(A)={actual_a:.6f} < 0.4 (уменьшилась из-за конфликта)")
            else:
                print(f"   ⚠️  m(A)={actual_a:.6f} ≥ 0.4 (неожиданно)")
            
            # Масса B должна быть больше исходной 0.6, т.к. конфликт в пользу B
            if actual_b > 0.6:
                print(f"   ✓ m(B)={actual_b:.6f} > 0.6 (увеличилась из-за конфликта)")
            else:
                print(f"   ⚠️  m(B)={actual_b:.6f} ≤ 0.6 (неожиданно)")
            
        except Exception as e:
            print(f"   ❌ Ошибка с тремя идентичными источниками: {e}")
            all_ok = False
        
        return all_ok
        
    def test_07_helper_methods(self) -> bool:
        """Тест вспомогательных методов"""
        test_dass = self._create_test_dass()
        data = self.adapter.load_from_dass(test_dass)
        
        all_ok = True
        
        # 1. Парсинг событий
        print("   1. Тест парсинга событий...")
        test_cases = [
            ("{A}", {"A"}),
            ("{A,B}", {"A", "B"}),
            ("{}", set()),
            (["A", "B"], {"A", "B"})
        ]
        
        for input_val, expected_set in test_cases:
            try:
                result = self.adapter._parse_event(input_val)
                if result == expected_set:
                    print(f"   ✓ Парсинг {input_val} -> {result}")
                else:
                    print(f"   ❌ Парсинг {input_val}: получено {result}, ожидалось {expected_set}")
                    all_ok = False
            except Exception as e:
                print(f"   ❌ Ошибка парсинга {input_val}: {e}")
                all_ok = False
        
        # 2. Форматирование подмножеств
        print("   2. Тест форматирования подмножеств...")
        test_cases = [
            (frozenset({"A"}), "{A}"),
            (frozenset({"A", "B"}), "{A,B}"),
            (frozenset(), "{}"),
            (frozenset({"C", "A", "B"}), "{A,B,C}")  # Проверка сортировки
        ]
        
        for subset, expected_str in test_cases:
            result = self.adapter._format_subset(subset)
            if result == expected_str:
                print(f"   ✓ Форматирование {subset} -> {result}")
            else:
                print(f"   ❌ Форматирование {subset}: получено {result}, ожидалось {expected_str}")
                all_ok = False
        
        # 3. Извлечение BPA из данных
        print("   3. Тест извлечения BPA из данных...")
        try:
            bpa = self.adapter._extract_bpa_from_data(data)
            if isinstance(bpa, dict) and len(bpa) > 0:
                print(f"   ✓ BPA извлечен, содержит {len(bpa)} подмножеств")
            else:
                print(f"   ❌ Не удалось извлечь BPA")
                all_ok = False
        except Exception as e:
            print(f"   ❌ Ошибка извлечения BPA: {e}")
            all_ok = False
        
        # 4. Получение фрейма различения
        print("   4. Тест получения фрейма различения...")
        try:
            frame = self.adapter.get_frame_of_discernment(data)
            if isinstance(frame, list) and len(frame) == 3:
                print(f"   ✓ Фрейм получен: {frame}")
            else:
                print(f"   ❌ Неверный фрейм: {frame}")
                all_ok = False
        except Exception as e:
            print(f"   ❌ Ошибка получения фрейма: {e}")
            all_ok = False
        
        # 5. Получение количества источников
        print("   5. Тест получения количества источников...")
        try:
            count = self.adapter.get_sources_count(data)
            if count == 2:
                print(f"   ✓ Количество источников: {count}")
            else:
                print(f"   ❌ Неверное количество источников: {count}")
                all_ok = False
        except Exception as e:
            print(f"   ❌ Ошибка получения количества источников: {e}")
            all_ok = False
        
        return all_ok
    
    # ==================== ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ====================
    
    def _convert_bpa_to_frozenset(self, bpa: Dict[str, float]) -> Dict[frozenset, float]:
        """Конвертирует BPA из строкового формата во frozenset"""
        converted = {}
        for subset_str, mass in bpa.items():
            subset = self.adapter._parse_subset_str(subset_str)
            converted[subset] = mass
        return converted
    
    def _convert_frozenset_bpa_to_string(self, bpa: Dict[frozenset, float]) -> Dict[str, float]:
        """Конвертирует BPA из frozenset формата в строковый"""
        converted = {}
        for subset, mass in bpa.items():
            subset_str = self.adapter._format_subset(subset)
            converted[subset_str] = mass
        return converted
    
    def _convert_string_bpa_to_dict(self, bpa: Dict[str, float]) -> Dict[str, float]:
        """Конвертирует BPA к единому строковому формату (сортировка элементов)"""
        converted = {}
        for subset_str, mass in bpa.items():
            # Парсим и снова форматируем для единообразия
            subset = self.adapter._parse_subset_str(subset_str)
            formatted = self.adapter._format_subset(subset)
            converted[formatted] = mass
        return converted
    
    def run_all_tests(self) -> bool:
        """Запуск всех тестов"""
        print("\n" + "="*70)
        print("🚀 ПОЛНЫЙ ТЕСТ АДАПТЕРА НАШЕЙ РЕАЛИЗАЦИИ")
        print("="*70)
        
        start_time = time.time()
        
        # Запускаем все тесты (убрали тест 02)
        tests = [
            ("01. Загрузка из DASS", self.test_01_load_from_dass),
            ("02. Plausibility функция", self.test_02_calculate_plausibility),
            ("03. Комбинирование Демпстера", self.test_03_combine_sources_dempster),
            ("04. Дисконтирование", self.test_04_apply_discounting),
            ("05. Комбинирование Ягера", self.test_05_combine_sources_yager),
            ("06. Граничные случаи", self.test_06_edge_cases),
            ("07. Вспомогательные методы", self.test_07_helper_methods),
        ]
        
        for test_name, test_func in tests:
            self.results["tests"][test_name] = {
                "timestamp": datetime.now().isoformat(),
                "passed": self._run_test(test_name, test_func)
            }
        
        # Сохраняем результаты
        self._save_results()
        
        # Выводим итоги
        elapsed_time = time.time() - start_time
        self._print_summary(elapsed_time)
        
        # Возвращаем общий результат
        return self.results["summary"]["failed"] == 0
    
    def _save_results(self):
        """Сохранение результатов в файл"""
        # Генерируем имя файла с временной меткой
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"our_adapter_test_{timestamp}.json"
        filepath = os.path.join(self.output_dir, filename)
        
        # Сохраняем JSON
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        # Также сохраняем краткий отчет в текстовом виде
        txt_filename = f"our_adapter_test_{timestamp}.txt"
        txt_filepath = os.path.join(self.output_dir, txt_filename)
        
        with open(txt_filepath, 'w', encoding='utf-8') as f:
            f.write("="*70 + "\n")
            f.write("ОТЧЕТ О ТЕСТИРОВАНИИ АДАПТЕРА\n")
            f.write("="*70 + "\n\n")
            
            f.write(f"Тест: {self.results['metadata']['test_name']}\n")
            f.write(f"Время: {self.results['metadata']['timestamp']}\n\n")
            
            summary = self.results["summary"]
            f.write(f"ИТОГИ:\n")
            f.write(f"  Всего тестов: {summary['total_tests']}\n")
            f.write(f"  Пройдено: {summary['passed']}\n")
            f.write(f"  Не пройдено: {summary['failed']}\n")
            success_rate = summary['passed'] / max(summary['total_tests'], 1) * 100
            f.write(f"  Успешность: {success_rate:.1f}%\n\n")
            
            if summary['errors']:
                f.write(f"ОШИБКИ:\n")
                for i, error in enumerate(summary['errors'], 1):
                    f.write(f"  {i}. {error}\n")
            
            # Детальные результаты тестов
            f.write("\nДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ:\n")
            for test_name, test_info in self.results["tests"].items():
                status = "✓ ПРОЙДЕН" if test_info["passed"] else "✗ НЕ ПРОЙДЕН"
                f.write(f"  {test_name}: {status}\n")
            
            f.write("\n" + "="*70 + "\n")
            f.write("Детальные результаты в JSON файле\n")
            f.write(f"Файл: {filename}\n")
        
        print(f"\n📁 Результаты сохранены:")
        print(f"   JSON: {filepath}")
        print(f"   TXT:  {txt_filepath}")
    
    def _print_summary(self, elapsed_time: float):
        """Вывод итогов в консоль"""
        print("\n" + "="*70)
        print("📊 ИТОГИ ТЕСТИРОВАНИЯ")
        print("="*70)
        
        summary = self.results["summary"]
        
        print(f"\n📈 СТАТИСТИКА:")
        print(f"  Всего тестов: {summary['total_tests']}")
        print(f"  Пройдено:     {summary['passed']}")
        print(f"  Не пройдено:  {summary['failed']}")
        
        success_rate = summary['passed'] / max(summary['total_tests'], 1) * 100
        print(f"  Успешность:   {success_rate:.1f}%")
        print(f"  Время:        {elapsed_time:.2f} секунд")
        
        if summary['failed'] == 0:
            print(f"\n✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        else:
            print(f"\n⚠️  НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОЙДЕНЫ")
            
            if summary['errors']:
                print(f"\n❌ ОШИБКИ:")
                for i, error in enumerate(summary['errors'], 1):
                    print(f"  {i}. {error}")


def main():
    """Основная функция"""
    # Создаем тестер
    tester = OurAdapterTester()
    
    # Запускаем все тесты
    success = tester.run_all_tests()
    
    # Возвращаем код выхода
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)