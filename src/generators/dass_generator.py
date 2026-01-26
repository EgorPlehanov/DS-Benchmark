# src/generators/dass_generator.py
"""
БЫСТРЫЙ генератор тестовых данных в формате DASS
Оптимизирован для генерации больших фреймов без генерации всех подмножеств
"""

import json
import random
import math
from typing import List, Dict, Any, Optional
from datetime import datetime

from .validator import DassValidator


class DassGenerator:
    """Быстрый генератор DASS тестовых данных"""
    
    @staticmethod
    def generate_simple(
        elements: List[str],
        n_sources: int = 2,
        density: float = 0.3,
        include_empty: bool = True
    ) -> Dict[str, Any]:
        """
        Генерирует простые тестовые данные
        
        Args:
            elements: Список элементов фрейма
            n_sources: Количество источников
            density: Плотность BBA (0-1)
            include_empty: Включать ли пустое множество
        
        Returns:
            Словарь с данными в формате DASS
        """
        data = {
            "metadata": {
                "format": "DASS",
                "version": "1.0",
                "description": f"Сгенерированные тестовые данные: {len(elements)} элементов, {n_sources} источников",
                "generated_at": datetime.now().isoformat(),
                "generated_by": "DS-Benchmark Generator"
            },
            "frame_of_discernment": elements,
            "bba_sources": []
        }
        
        # Генерируем каждый источник
        for i in range(n_sources):
            source_id = f"source_{i+1}"
            bba = DassGenerator._generate_fast_random_bba(
                elements=elements,
                target_subsets=min(8, max(3, int(len(elements) * density))),  # Ограничиваем подмножества
                include_empty=include_empty
            )
            
            # Нормализуем BPA
            bba = DassValidator.normalize_bba(bba)
            
            data["bba_sources"].append({
                "id": source_id,
                "bba": bba
            })
        
        return data
    
    @staticmethod
    def _generate_fast_random_bba(
        elements: List[str],
        target_subsets: int = 5,
        include_empty: bool = True
    ) -> Dict[str, float]:
        """
        БЫСТРАЯ генерация случайного BPA БЕЗ создания всех подмножеств
        
        Args:
            elements: Элементы фрейма
            target_subsets: Целевое количество подмножеств
            include_empty: Включать ли пустое множество
        
        Returns:
            Словарь: строка множества -> масса
        """
        bba = {}
        n_elements = len(elements)
        
        # Определяем, сколько подмножеств каждого типа генерировать
        if target_subsets <= 0:
            target_subsets = 5
        
        # 1. Всегда добавляем 1-3 одиночных элемента
        n_singles = min(random.randint(1, 3), n_elements)
        singles = random.sample(elements, n_singles)
        
        # 2. Добавляем составные подмножества (2-4 элемента)
        n_composite = max(0, target_subsets - n_singles - (1 if include_empty else 0))
        n_composite = min(n_composite, 3)  # Не более 3 составных
        
        # 3. Генерируем подмножества
        all_subsets = []
        
        # Одиночные элементы
        for elem in singles:
            all_subsets.append({elem})
        
        # Составные подмножества (без генерации всех!)
        for _ in range(n_composite):
            # Генерируем случайный размер (2-4 элемента)
            subset_size = random.randint(2, min(4, n_elements))
            # Выбираем случайные элементы
            subset = set(random.sample(elements, subset_size))
            # Проверяем, что подмножество уникально
            if subset not in all_subsets:
                all_subsets.append(subset)
        
        # Пустое множество
        if include_empty and random.random() < 0.3:  # 30% chance
            all_subsets.append(set())
        
        # Ограничиваем общее количество
        if len(all_subsets) > target_subsets:
            all_subsets = all_subsets[:target_subsets]
        
        # 4. Генерируем массы с использованием экспоненциального распределения
        # Это дает более естественное распределение масс
        masses = []
        for i in range(len(all_subsets)):
            # Экспоненциальное распределение с разными параметрами
            mass = random.expovariate(random.uniform(0.5, 2.0))
            masses.append(mass)
        
        # 5. Нормализуем массы
        total = sum(masses)
        if total > 0:
            masses = [m / total for m in masses]
        else:
            masses = [1.0 / len(all_subsets)] * len(all_subsets)
        
        # 6. Собираем BPA
        for subset, mass in zip(all_subsets, masses):
            subset_str = DassValidator.format_subset(subset)
            bba[subset_str] = mass
        
        return bba
    
    @staticmethod
    def _smart_generate_subsets(elements: List[str], target_count: int) -> List[set]:
        """
        Умная генерация подмножеств без полного перебора
        
        Использует стратегию:
        1. Одиночные элементы
        2. Пары элементов
        3. Тройки элементов
        4. И т.д., пока не достигнем target_count
        """
        n_elements = len(elements)
        all_subsets = []
        
        # Если фрейм маленький, используем старый метод
        if n_elements <= 10:
            return DassGenerator._generate_all_subsets_safe(elements, target_count)
        
        # Для больших фреймов - умная генерация
        
        # 1. Одиночные элементы (всегда берем подмножество)
        n_singles = min(target_count // 2, n_elements)
        singles = random.sample(elements, n_singles)
        for elem in singles:
            all_subsets.append({elem})
        
        remaining = target_count - len(all_subsets)
        if remaining <= 0:
            return all_subsets[:target_count]
        
        # 2. Пары (если осталось место)
        n_pairs = min(remaining, n_elements * (n_elements - 1) // 2)
        pairs_generated = 0
        attempts = 0
        max_attempts = n_pairs * 10
        
        while pairs_generated < n_pairs and attempts < max_attempts:
            pair = set(random.sample(elements, 2))
            if pair not in all_subsets:
                all_subsets.append(pair)
                pairs_generated += 1
            attempts += 1
        
        remaining = target_count - len(all_subsets)
        if remaining <= 0:
            return all_subsets[:target_count]
        
        # 3. Тройки (если осталось место и достаточно элементов)
        if n_elements >= 3:
            n_triples = min(remaining, n_elements * (n_elements - 1) * (n_elements - 2) // 6)
            triples_generated = 0
            attempts = 0
            max_attempts = n_triples * 10
            
            while triples_generated < n_triples and attempts < max_attempts:
                triple = set(random.sample(elements, 3))
                if triple not in all_subsets:
                    all_subsets.append(triple)
                    triples_generated += 1
                attempts += 1
        
        return all_subsets[:target_count]
    
    @staticmethod
    def _generate_all_subsets_safe(elements: List[str], max_subsets: int = 100) -> List[set]:
        """
        Безопасная генерация подмножеств для маленьких фреймов
        """
        n = len(elements)
        all_subsets = []
        
        # Ограничиваем максимальное количество
        max_possible = 1 << n
        actual_max = min(max_possible, max_subsets)
        
        # Генерируем подмножества до достижения лимита
        for mask in range(1, max_possible):
            if len(all_subsets) >= actual_max:
                break
                
            subset = set()
            for i in range(n):
                if mask & (1 << i):
                    subset.add(elements[i])
            all_subsets.append(subset)
        
        return all_subsets
    
    @staticmethod
    def generate_test_suite() -> Dict[str, Dict[str, Any]]:
        """Генерирует набор тестовых данных разных размеров"""
        test_suite = {}
        
        # Тест 1: Маленький
        test_suite["small"] = DassGenerator.generate_simple(
            elements=["A", "B", "C"],
            n_sources=2,
            density=0.1
        )
        
        # Тест 2: Средний
        test_suite["medium"] = DassGenerator.generate_simple(
            elements=["A", "B", "C", "D", "E"],
            n_sources=3,
            density=0.05
        )
        
        # Тест 3: Большой
        test_suite["large"] = DassGenerator.generate_simple(
            elements=["A", "B", "C", "D", "E", "F", "G"],
            n_sources=2,
            density=0.02
        )
        
        return test_suite
    
    @staticmethod
    def save_to_file(data: Dict[str, Any], filepath: str) -> bool:
        """Сохраняет данные в JSON файл"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Ошибка сохранения файла {filepath}: {e}")
            return False
    
    @staticmethod
    def load_from_file(filepath: str) -> Optional[Dict[str, Any]]:
        """Загружает данные из JSON файла"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Ошибка загрузки файла {filepath}: {e}")
            return None