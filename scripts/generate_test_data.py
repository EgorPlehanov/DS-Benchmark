#!/usr/bin/env python3
"""
ОПТИМИЗИРОВАННЫЙ генератор тестовых данных для бенчмарков.
Генерирует меньше тестов, но более качественных и с гарантированной корректностью.
"""

import os
import json
import random
from datetime import datetime
from typing import List, Dict, Any
import sys

# Добавляем путь для импорта
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.generators.dass_generator import DassGenerator
from src.generators.validator import DassValidator


class OptimizedTestDataGenerator:
    """Оптимизированный генератор тестовых данных"""
    
    def __init__(self):
        self.alphabet = [chr(ord('A') + i) for i in range(26)]  # A-Z
    
    def generate_optimized_test_suite(self) -> Dict[str, List[Dict]]:
        """
        Генерирует оптимизированный набор тестов
        
        Всего: 30 тестов (вместо 110), но все тщательно валидированы
        """
        print("🚀 ОПТИМИЗИРОВАННАЯ генерация тестовых данных")
        print("=" * 70)
        
        test_suite = {
            "tiny": self._generate_tiny_tests(5),       # 5 тестов: 2-3 элемента
            "small": self._generate_small_tests(7),     # 7 тестов: 4-6 элементов
            "medium": self._generate_medium_tests(6),   # 6 тестов: 7-10 элементов
            "large": self._generate_large_tests(4),     # 4 теста: 11-15 элементов
            "xlarge": self._generate_xlarge_tests(3),   # 3 теста: 16-20 элементов
            "stress": self._generate_stress_tests(2),   # 2 теста: 21-26 элементов
        }
        
        # Специальные тесты
        special_tests = self._generate_special_cases()
        test_suite["special"] = special_tests
        
        return test_suite
    
    def _generate_tiny_tests(self, count: int) -> List[Dict]:
        """Маленькие тесты (2-3 элемента)"""
        tests = []
        for i in range(1, count + 1):
            n_elements = random.choice([2, 3])
            n_sources = random.choice([2, 3])
            
            test = self._generate_validated_test(
                n_elements=n_elements,
                n_sources=n_sources,
                group="tiny",
                test_id=f"tiny_{i:03d}"
            )
            tests.append(test)
        
        print(f"  ✓ tiny: {count} тестов (2-3 элемента)")
        return tests
    
    def _generate_small_tests(self, count: int) -> List[Dict]:
        """Маленькие тесты (4-6 элементов)"""
        tests = []
        for i in range(1, count + 1):
            n_elements = random.choice([4, 5, 6])
            n_sources = random.choice([2, 3, 4])
            
            test = self._generate_validated_test(
                n_elements=n_elements,
                n_sources=n_sources,
                group="small",
                test_id=f"small_{i:03d}"
            )
            tests.append(test)
        
        print(f"  ✓ small: {count} тестов (4-6 элементов)")
        return tests
    
    def _generate_medium_tests(self, count: int) -> List[Dict]:
        """Средние тесты (7-10 элементов)"""
        tests = []
        for i in range(1, count + 1):
            n_elements = random.randint(7, 10)
            n_sources = random.choice([2, 3, 4])
            
            test = self._generate_validated_test(
                n_elements=n_elements,
                n_sources=n_sources,
                group="medium",
                test_id=f"medium_{i:03d}"
            )
            tests.append(test)
        
        print(f"  ✓ medium: {count} тестов (7-10 элементов)")
        return tests
    
    def _generate_large_tests(self, count: int) -> List[Dict]:
        """Большие тесты (11-15 элементов)"""
        tests = []
        for i in range(1, count + 1):
            n_elements = random.randint(11, 15)
            n_sources = random.choice([2, 3])
            
            test = self._generate_validated_test(
                n_elements=n_elements,
                n_sources=n_sources,
                group="large",
                test_id=f"large_{i:03d}"
            )
            tests.append(test)
        
        print(f"  ✓ large: {count} тестов (11-15 элементов)")
        return tests
    
    def _generate_xlarge_tests(self, count: int) -> List[Dict]:
        """Очень большие тесты (16-20 элементов)"""
        tests = []
        for i in range(1, count + 1):
            n_elements = random.randint(16, 20)
            n_sources = 2  # Только 2 источника
            
            test = self._generate_validated_test(
                n_elements=n_elements,
                n_sources=n_sources,
                group="xlarge",
                test_id=f"xlarge_{i:03d}"
            )
            tests.append(test)
        
        print(f"  ✓ xlarge: {count} тестов (16-20 элементов)")
        return tests
    
    def _generate_stress_tests(self, count: int) -> List[Dict]:
        """Экстремальные тесты (21-26 элементов)"""
        tests = []
        for i in range(1, count + 1):
            n_elements = random.randint(21, 26)
            n_sources = 2  # Только 2 источника
            
            test = self._generate_validated_test(
                n_elements=n_elements,
                n_sources=n_sources,
                group="stress",
                test_id=f"stress_{i:03d}"
            )
            tests.append(test)
        
        print(f"  ✓ stress: {count} тестов (21-26 элементов)")
        return tests
    
    def _generate_validated_test(self, n_elements: int, n_sources: int, 
                               group: str, test_id: str, max_attempts: int = 5) -> Dict:
        """
        Генерирует и валидирует один тест.
        Повторяет попытки до получения валидного теста.
        """
        attempts = 0
        while attempts < max_attempts:
            attempts += 1
            
            # Генерируем элементы
            elements = self.alphabet[:n_elements]
            
            # Генерируем тест
            test_data = DassGenerator.generate_simple(
                elements=elements,
                n_sources=n_sources,
                density=self._get_optimal_density(n_elements),
                include_empty=random.choice([True, False])
            )
            
            # Валидируем
            is_valid, errors = DassValidator.validate_data(test_data)
            
            if is_valid:
                # Добавляем метаданные
                test_data["metadata"].update({
                    "description": f"{group.capitalize()} тест: {n_elements} элементов, {n_sources} источников",
                    "test_group": group,
                    "test_id": test_id,
                    "validation_attempts": attempts
                })
                return test_data
            else:
                # Если последняя попытка, выводим ошибку
                if attempts == max_attempts:
                    print(f"    ⚠️  Тест {test_id}: не удалось сгенерировать валидный тест после {max_attempts} попыток")
                    print(f"       Последняя ошибка: {errors[0] if errors else 'неизвестно'}")
        
        # Если не удалось, возвращаем простейший валидный тест
        return self._create_minimal_valid_test(n_elements, n_sources, group, test_id)
    
    def _get_optimal_density(self, n_elements: int) -> float:
        """Возвращает оптимальную плотность для заданного размера фрейма"""
        if n_elements <= 3:
            return 0.4
        elif n_elements <= 6:
            return 0.3
        elif n_elements <= 10:
            return 0.2
        elif n_elements <= 15:
            return 0.1
        elif n_elements <= 20:
            return 0.05
        else:
            return 0.03
    
    def _create_minimal_valid_test(self, n_elements: int, n_sources: int,
                                 group: str, test_id: str) -> Dict:
        """Создает минимальный валидный тест"""
        elements = self.alphabet[:n_elements]
        
        # Минимальный валидный BPA: все масса на одном элементе
        minimal_bba = {f"{{{elements[0]}}}": 1.0}
        
        test_data = {
            "metadata": {
                "format": "DASS",
                "version": "1.0",
                "description": f"Минимальный {group} тест: {n_elements} элементов, {n_sources} источников",
                "test_group": group,
                "test_id": test_id,
                "is_minimal_fallback": True,
                "generated_at": datetime.now().isoformat()
            },
            "frame_of_discernment": elements,
            "bba_sources": []
        }
        
        # Создаем источники
        for i in range(n_sources):
            test_data["bba_sources"].append({
                "id": f"source_{i+1}",
                "bba": minimal_bba
            })
        
        return test_data
    
    def _generate_special_cases(self) -> List[Dict]:
        """Генерирует специальные тестовые случаи"""
        print("  ✓ special: 5 специальных тестов")
        
        special_tests = [
            self._generate_conflict_case(),
            self._generate_agreement_case(),
            self._generate_many_sources_case(),
            self._generate_focused_case(),
            self._generate_diffuse_case()
        ]
        
        # Валидируем специальные тесты
        validated = []
        for test in special_tests:
            is_valid, errors = DassValidator.validate_data(test)
            if is_valid:
                validated.append(test)
            else:
                print(f"    ⚠️  Специальный тест невалиден: {errors[0] if errors else 'неизвестно'}")
        
        return validated
    
    def _generate_conflict_case(self) -> Dict:
        """Случай с максимальным конфликтом"""
        test_data = {
            "metadata": {
                "description": "Максимальный конфликт между источниками",
                "test_group": "special",
                "test_id": "special_conflict",
                "type": "high_conflict"
            },
            "frame_of_discernment": ["A", "B", "C"],
            "bba_sources": [
                {"id": "source_conflict_1", "bba": {"{A}": 0.9, "{B}": 0.1}},
                {"id": "source_conflict_2", "bba": {"{B}": 0.9, "{C}": 0.1}},
                {"id": "source_conflict_3", "bba": {"{C}": 0.9, "{A}": 0.1}}
            ]
        }
        
        # Нормализуем BPA
        for source in test_data["bba_sources"]:
            source["bba"] = DassValidator.normalize_bba(source["bba"])
        
        return test_data
    
    def _generate_agreement_case(self) -> Dict:
        """Случай с полным согласием"""
        test_data = {
            "metadata": {
                "description": "Полное согласие между источниками",
                "test_group": "special",
                "test_id": "special_agreement",
                "type": "full_agreement"
            },
            "frame_of_discernment": ["A", "B", "C", "D"],
            "bba_sources": [
                {"id": "source_agree_1", "bba": {"{A}": 0.4, "{B}": 0.3, "{C}": 0.2, "{D}": 0.1}},
                {"id": "source_agree_2", "bba": {"{A}": 0.4, "{B}": 0.3, "{C}": 0.2, "{D}": 0.1}},
                {"id": "source_agree_3", "bba": {"{A}": 0.4, "{B}": 0.3, "{C}": 0.2, "{D}": 0.1}}
            ]
        }
        
        # Нормализуем BPA
        for source in test_data["bba_sources"]:
            source["bba"] = DassValidator.normalize_bba(source["bba"])
        
        return test_data
    
    def _generate_many_sources_case(self) -> Dict:
        """Много источников"""
        n_sources = 5  # Уменьшили с 10 до 5 для скорости
        bba_sources = []
        
        base_bba = {"{A}": 0.3, "{B}": 0.3, "{C}": 0.2, "{A,B,C}": 0.2}
        base_bba = DassValidator.normalize_bba(base_bba)
        
        for i in range(n_sources):
            bba_sources.append({
                "id": f"source_many_{i+1}",
                "bba": base_bba
            })
        
        return {
            "metadata": {
                "description": f"Много источников ({n_sources})",
                "test_group": "special",
                "test_id": "special_many_sources",
                "type": "many_sources"
            },
            "frame_of_discernment": ["A", "B", "C"],
            "bba_sources": bba_sources
        }
    
    def _generate_focused_case(self) -> Dict:
        """Фокусные BPA"""
        test_data = {
            "metadata": {
                "description": "Фокусные BPA (только одиночные элементы)",
                "test_group": "special",
                "test_id": "special_focused",
                "type": "focused_bpa"
            },
            "frame_of_discernment": ["A", "B", "C", "D", "E"],
            "bba_sources": [
                {"id": "source_focused_1", "bba": {"{A}": 0.2, "{B}": 0.2, "{C}": 0.2, "{D}": 0.2, "{E}": 0.2}},
                {"id": "source_focused_2", "bba": {"{A}": 0.3, "{B}": 0.2, "{C}": 0.2, "{D}": 0.2, "{E}": 0.1}}
            ]
        }
        
        # Нормализуем BPA
        for source in test_data["bba_sources"]:
            source["bba"] = DassValidator.normalize_bba(source["bba"])
        
        return test_data
    
    def _generate_diffuse_case(self) -> Dict:
        """Диффузные BPA"""
        test_data = {
            "metadata": {
                "description": "Диффузные BPA (много составных подмножеств)",
                "test_group": "special",
                "test_id": "special_diffuse",
                "type": "diffuse_bpa"
            },
            "frame_of_discernment": ["A", "B", "C", "D"],
            "bba_sources": [
                {"id": "source_diffuse_1", "bba": {"{A,B}": 0.25, "{B,C}": 0.25, "{C,D}": 0.25, "{A,D}": 0.25}},
                {"id": "source_diffuse_2", "bba": {"{A,B,C}": 0.3, "{B,C,D}": 0.3, "{A,C,D}": 0.2, "{A,B,D}": 0.2}}
            ]
        }
        
        # Нормализуем BPA
        for source in test_data["bba_sources"]:
            source["bba"] = DassValidator.normalize_bba(source["bba"])
        
        return test_data


def save_tests(test_suite: Dict[str, List[Dict]], output_dir: str):
    """Сохраняет все тесты в файлы"""
    os.makedirs(output_dir, exist_ok=True)
    
    total_saved = 0
    all_tests = []
    
    # Сохраняем по группам
    for group_name, tests in test_suite.items():
        group_dir = os.path.join(output_dir, group_name)
        os.makedirs(group_dir, exist_ok=True)
        
        group_count = 0
        for test in tests:
            test_id = test["metadata"]["test_id"]
            filename = os.path.join(group_dir, f"{test_id}.json")
            
            # Дополнительная валидация перед сохранением
            is_valid, errors = DassValidator.validate_data(test)
            if not is_valid:
                print(f"    ⚠️  Тест {test_id} невалиден при сохранении: {errors[0] if errors else 'неизвестно'}")
                continue
            
            # Сохраняем
            if DassGenerator.save_to_file(test, filename):
                group_count += 1
                total_saved += 1
                all_tests.append(test)
            else:
                print(f"    ⚠️  Ошибка сохранения теста {test_id}")
        
        print(f"    💾 {group_name}: {group_count} тестов сохранено")
    
    return total_saved, all_tests


def create_statistics(all_tests: List[Dict], output_dir: str):
    """Создает статистику по тестам"""
    stats = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "total_tests": len(all_tests),
            "description": "Статистика оптимизированного тестового набора"
        },
        "by_group": {},
        "by_size": {},
        "quality_metrics": {
            "valid_tests": len(all_tests),
            "invalid_tests": 0,
            "minimal_fallbacks": sum(1 for t in all_tests if t["metadata"].get("is_minimal_fallback", False))
        }
    }
    
    # Статистика по группам
    groups = {}
    sizes = {}
    
    for test in all_tests:
        group = test["metadata"]["test_group"]
        n_elements = len(test["frame_of_discernment"])
        
        # По группам
        if group not in groups:
            groups[group] = 0
        groups[group] += 1
        
        # По размеру
        if n_elements not in sizes:
            sizes[n_elements] = 0
        sizes[n_elements] += 1
    
    stats["by_group"] = groups
    stats["by_size"] = sizes
    
    # Анализ сложности
    if all_tests:
        total_elements = sum(len(test["frame_of_discernment"]) for test in all_tests)
        total_sources = sum(len(test["bba_sources"]) for test in all_tests)
        
        stats["complexity_analysis"] = {
            "avg_elements": total_elements / len(all_tests),
            "avg_sources": total_sources / len(all_tests),
            "max_elements": max(len(test["frame_of_discernment"]) for test in all_tests),
            "min_elements": min(len(test["frame_of_discernment"]) for test in all_tests),
        }
    
    # Сохраняем статистику
    stats_file = os.path.join(output_dir, "statistics.json")
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    
    return stats


def save_last_generation_path(output_dir: str):
    """Сохраняет путь к последней генерации тестов"""
    last_gen_file = "data/generated/last_generation.txt"
    
    os.makedirs(os.path.dirname(last_gen_file), exist_ok=True)
    
    # Получаем только имя папки
    folder_name = os.path.basename(output_dir)
    
    with open(last_gen_file, 'w', encoding='utf-8') as f:
        f.write(folder_name)


def get_last_generation_path() -> str | None:
    """Получает путь к последней генерации тестов"""
    last_gen_file = "data/generated/last_generation.txt"
    
    if os.path.exists(last_gen_file):
        with open(last_gen_file, 'r', encoding='utf-8') as f:
            folder_name = f.read().strip()
        
        return os.path.join("data/generated", folder_name)
    
    return None


def main():
    """Основная функция"""
    print("🔬 ОПТИМИЗИРОВАННЫЙ ГЕНЕРАТОР ТЕСТОВЫХ ДАННЫХ")
    print("Быстро генерирует 30+ качественных, валидированных тестов")
    print("=" * 70)
    
    # Создаем уникальное имя папки
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"data/generated/tests_{timestamp}"
    
    print(f"📁 Тесты будут сохранены в: {output_dir}")
    
    # Генерируем тесты
    generator = OptimizedTestDataGenerator()
    test_suite = generator.generate_optimized_test_suite()
    
    # Сохраняем
    print(f"\n💾 Сохранение тестов...")
    total_saved, all_tests = save_tests(test_suite, output_dir)
    
    # Статистика
    print(f"\n📈 Создание статистики...")
    stats = create_statistics(all_tests, output_dir)
    
    # Сохраняем путь к последней генерации
    save_last_generation_path(output_dir)
    
    # Вывод итогов
    print(f"\n✅ Готово! Создано {total_saved} валидных тестовых файлов")
    print(f"\n📊 Статистика:")
    print(f"  Всего тестов: {stats['metadata']['total_tests']}")
    print(f"  Валидных тестов: {stats['quality_metrics']['valid_tests']}")
    print(f"  Резервных тестов: {stats['quality_metrics']['minimal_fallbacks']}")
    
    print(f"\n  По группам:")
    for group, count in sorted(stats["by_group"].items()):
        print(f"    {group:10}: {count:3} тестов")
    
    print(f"\n  По размеру фрейма:")
    for size in sorted(stats["by_size"].keys()):
        count = stats["by_size"][size]
        print(f"    {size:2} элементов: {count:3} тестов")
    
    if "complexity_analysis" in stats:
        complexity = stats["complexity_analysis"]
        print(f"\n  Анализ сложности:")
        print(f"    Средний размер фрейма: {complexity['avg_elements']:.1f} элементов")
        print(f"    Среднее число источников: {complexity['avg_sources']:.1f}")
        print(f"    Максимальный размер фрейма: {complexity['max_elements']} элементов")
    
    # Показываем путь к последней генерации
    last_gen = get_last_generation_path()
    if last_gen:
        print(f"\n📁 Для запуска тестов используйте:")
        print(f"  python scripts/profile_benchmark.py --library our --tests last --profiling off")
        print(f"  python scripts/profile_benchmark.py --library our --tests {last_gen} --profiling off")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
