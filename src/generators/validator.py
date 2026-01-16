"""
Валидатор DASS файлов
Проверяет корректность входных данных
"""

import json
from typing import Dict, List, Any, Tuple
import re

class DassValidator:
    """Валидатор формата DASS"""
    
    @staticmethod
    def validate_file(filepath: str) -> Tuple[bool, List[str]]:
        """
        Валидирует DASS файл
        Возвращает: (is_valid, список_ошибок)
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return DassValidator.validate_data(data)
        except json.JSONDecodeError as e:
            return False, [f"Ошибка JSON: {str(e)}"]
        except Exception as e:
            return False, [f"Ошибка чтения файла: {str(e)}"]
    
    @staticmethod
    def validate_data(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Валидирует данные в памяти"""
        errors = []
        
        # 1. Проверяем обязательные поля
        required_fields = ["frame_of_discernment", "bba_sources"]
        for field in required_fields:
            if field not in data:
                errors.append(f"Отсутствует обязательное поле: {field}")
        
        if errors:
            return False, errors
        
        frame = data["frame_of_discernment"]
        sources = data["bba_sources"]
        
        # 2. Проверяем фрейм
        if not isinstance(frame, list):
            errors.append("frame_of_discernment должен быть списком")
        elif len(frame) == 0:
            errors.append("frame_of_discernment не может быть пустым")
        elif len(frame) != len(set(frame)):
            errors.append("frame_of_discernment содержит дубликаты")
        
        # 3. Проверяем источники
        if not isinstance(sources, list):
            errors.append("bba_sources должен быть списком")
        elif len(sources) == 0:
            errors.append("bba_sources не может быть пустым")
        
        # 4. Проверяем каждый источник
        for i, source in enumerate(sources):
            source_errors = DassValidator._validate_source(source, frame, i)
            errors.extend(source_errors)
        
        return len(errors) == 0, errors
    
    @staticmethod
    def _validate_source(source: Dict, frame: List[str], index: int) -> List[str]:
        """Валидирует один источник BBA"""
        errors = []
        
        # Проверяем обязательные поля источника
        if "bba" not in source:
            errors.append(f"Источник {index}: отсутствует поле 'bba'")
            return errors
        
        bba = source["bba"]
        
        if not isinstance(bba, dict):
            errors.append(f"Источник {index}: bba должен быть словарем")
            return errors
        
        # Проверяем корректность множеств и масс
        total_mass = 0.0
        valid_subsets = []
        
        for subset_str, mass in bba.items():
            # Проверяем массу
            if not isinstance(mass, (int, float)):
                errors.append(f"Источник {index}: масса для '{subset_str}' должна быть числом")
                continue
            
            if mass < 0 or mass > 1:
                errors.append(f"Источник {index}: масса для '{subset_str}' должна быть между 0 и 1")
            
            total_mass += mass
            
            # Парсим и проверяем множество
            if subset_str == "{}":
                subset = set()
            else:
                # Проверяем формат "{A,B,C}"
                if not re.match(r'^\{[A-Za-z0-9_,]*\}$', subset_str):
                    errors.append(f"Источник {index}: некорректный формат множества: '{subset_str}'")
                    continue
                
                # Извлекаем элементы
                elements = subset_str.strip('{}').split(',')
                if elements == ['']:  # Пустое множество как "{}"
                    subset = set()
                else:
                    subset = set(elements)
                    
                    # Проверяем, что все элементы есть во фрейме
                    for elem in subset:
                        if elem not in frame:
                            errors.append(
                                f"Источник {index}: элемент '{elem}' из '{subset_str}' "
                                f"отсутствует во фрейме"
                            )
            
            valid_subsets.append(subset)
        
        # Проверяем сумму масс (допускаем небольшую погрешность)
        if abs(total_mass - 1.0) > 0.001:
            errors.append(
                f"Источник {index}: сумма масс = {total_mass:.4f}, должна быть 1.0 ±0.001"
            )
        
        return errors
    
    @staticmethod
    def parse_subset(subset_str: str) -> set:
        """Парсит строку множества в set"""
        if subset_str == "{}":
            return set()
        
        elements = subset_str.strip('{}').split(',')
        if elements == ['']:
            return set()
        return set(elements)
    
    @staticmethod
    def format_subset(subset: set) -> str:
        """Форматирует set в строку множества"""
        if not subset:
            return "{}"
        sorted_elements = sorted(subset)
        return "{" + ",".join(sorted_elements) + "}"