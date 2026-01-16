"""
Генератор тестовых данных в формате DASS
"""

import json
import random
from typing import List, Dict, Any, Optional
from datetime import datetime

# Импортируем из того же пакета
from .validator import DassValidator

class DassGenerator:
    """Генератор DASS тестовых данных"""
    
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
            density: Плотность BBA (0-1), какая доля всех возможных подмножеств используется
            include_empty: Включать ли пустое множество
        
        Returns:
            Словарь с данными в формате DASS
        """
        # Генерируем все возможные непустые подмножества
        all_subsets = DassGenerator._generate_all_subsets(elements)
        
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
            bba = DassGenerator._generate_random_bba(
                elements,  # Передаем элементы, а не все подмножества
                density=density,
                include_empty=include_empty
            )
            
            data["bba_sources"].append({
                "id": source_id,
                "bba": bba
            })
        
        return data
    
    @staticmethod
    def _generate_all_subsets(elements: List[str]) -> List[set]:
        """Генерирует все возможные подмножества (кроме пустого)"""
        n = len(elements)
        all_subsets = []
        
        # Используем битовую маску для генерации всех подмножеств
        for mask in range(1, 1 << n):  # Пропускаем 0 (пустое множество)
            subset = set()
            for i in range(n):
                if mask & (1 << i):
                    subset.add(elements[i])
            all_subsets.append(subset)
        
        return all_subsets
    
    @staticmethod
    def _generate_random_bba(
        elements: List[str],  # Изменили: передаем элементы, а не все подмножества
        density: float = 0.3,
        include_empty: bool = True
    ) -> Dict[str, float]:
        """
        Генерирует случайное BBA
        
        Args:
            elements: Элементы фрейма
            density: Какая доля подмножеств будет использована
            include_empty: Включать ли пустое множество
        
        Returns:
            Словарь: строка множества -> масса
        """
        # Генерируем подмножества проще: только одиночные элементы и 1-2 составных
        bba = {}
        
        # 1. Всегда добавляем несколько одиночных элементов
        single_elements = elements.copy()
        random.shuffle(single_elements)
        
        # Сколько одиночных элементов взять (1-3)
        n_single = random.randint(1, min(3, len(elements)))
        selected_singles = single_elements[:n_single]
        
        # 2. Может добавить 0-2 составных подмножества
        all_subsets = DassGenerator._generate_all_subsets(elements)
        composite_subsets = [s for s in all_subsets if len(s) > 1]
        
        n_composite = random.randint(0, min(2, len(composite_subsets)))
        selected_composites = random.sample(composite_subsets, n_composite) if composite_subsets else []
        
        # 3. Собираем все выбранные подмножества
        selected_subsets = []
        
        # Добавляем одиночные как множества
        for elem in selected_singles:
            selected_subsets.append({elem})
        
        # Добавляем составные
        selected_subsets.extend(selected_composites)
        
        # 4. Добавляем пустое множество если нужно
        if include_empty and random.random() < 0.3:  # 30% chance
            selected_subsets.append(set())
        
        # 5. Генерируем массы (не более 5-7 подмножеств в сумме)
        if len(selected_subsets) > 7:
            selected_subsets = selected_subsets[:7]
        
        masses = [random.random() for _ in selected_subsets]
        total = sum(masses)
        masses = [m / total for m in masses]
        
        # 6. Собираем BBA
        for subset, mass in zip(selected_subsets, masses):
            subset_str = DassValidator.format_subset(subset)
            bba[subset_str] = round(mass, 4)
        
        return bba
    
    @staticmethod
    def generate_test_suite() -> Dict[str, Dict[str, Any]]:
        """Генерирует набор тестовых данных разных размеров"""
        test_suite = {}
        
        # Тест 1: Маленький - ПРОСТОЙ
        test_suite["small"] = DassGenerator.generate_simple(
            elements=["A", "B", "C"],
            n_sources=2,
            density=0.1  # Уменьшили плотность
        )
        
        # Тест 2: Средний - УМЕРЕННЫЙ
        test_suite["medium"] = DassGenerator.generate_simple(
            elements=["A", "B", "C", "D", "E"],
            n_sources=3,
            density=0.05  # Уменьшили плотность
        )
        
        # Тест 3: Большой - СЛОЖНЫЙ, но не перегруженный
        test_suite["large"] = DassGenerator.generate_simple(
            elements=["A", "B", "C", "D", "E", "F", "G"],
            n_sources=2,  # Уменьшили количество источников
            density=0.02   # Сильно уменьшили плотность
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