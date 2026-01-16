# src/adapters/our_adapter.py
"""
Адаптер для нашей реализации Демпстера-Шейфера
Реализует интерфейс BaseDempsterShaferAdapter
"""

import json
from typing import Dict, List, Any, Tuple, Set
from .base_adapter import BaseDempsterShaferAdapter
from ..core.dempster_core import DempsterShafer


class OurImplementationAdapter(BaseDempsterShaferAdapter):
    """Адаптер для нашей реализации - реализует общий интерфейс"""
    
    def __init__(self):
        self.ds = None  # Инициализируется после загрузки данных
        
    def load_from_dass(self, dass_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Загружает данные из DASS формата в нашу структуру
        
        Args:
            dass_data: данные в формате DASS
            
        Returns:
            Словарь с подготовленными данными
        """
        # Извлекаем фрейм
        frame_elements = dass_data["frame_of_discernment"]
        frame = set(frame_elements)
        
        # Инициализируем нашу реализацию
        self.ds = DempsterShafer(frame)
        
        # Преобразуем BPA из DASS формата в наш формат
        bpas = []
        for source in dass_data["bba_sources"]:
            bpa_dict = {}
            for subset_str, mass in source["bba"].items():
                # Конвертируем "{A,B}" -> frozenset(["A", "B"])
                subset = self._parse_subset_str(subset_str)
                bpa_dict[subset] = mass
            bpas.append(bpa_dict)
        
        return {
            "frame": frame,
            "bpas": bpas,
            "metadata": dass_data.get("metadata", {}),
            "original_data": dass_data
        }
    
    def combine_all_dempster(self, data: Dict[str, Any]) -> Dict[frozenset, float]:
        """
        Комбинирует все источники по правилу Демпстера
        """
        if not self.ds:
            raise ValueError("Данные не загружены. Сначала вызовите load_from_dass()")
        
        bpas = data["bpas"]
        
        if len(bpas) == 0:
            return {}
        elif len(bpas) == 1:
            return bpas[0]
        
        # Комбинируем все BPA последовательно
        result = bpas[0]
        for bpa in bpas[1:]:
            result = self.ds.dempster_combine(result, bpa)
        
        return result
    
    def combine_dempster_pair(self, bpa1: Dict[frozenset, float], 
                            bpa2: Dict[frozenset, float]) -> Dict[frozenset, float]:
        """
        Комбинирует два BPA по правилу Демпстера
        """
        if not self.ds:
            raise ValueError("Демпстер-Шейфер не инициализирован")
        
        return self.ds.dempster_combine(bpa1, bpa2)
    
    def validate_bpa(self, bpa: Dict[frozenset, float]) -> Tuple[bool, float]:
        """
        Проверяет корректность BPA: сумма масс должна быть 1
        
        Returns:
            (валидно ли, сумма масс)
        """
        total = sum(bpa.values())
        return (abs(total - 1.0) < 1e-10, total)
    
    # ДОПОЛНИТЕЛЬНЫЕ МЕТОДЫ (не обязательные для интерфейса, но полезные)
    
    def combine_all_yager(self, data: Dict[str, Any]) -> Dict[frozenset, float]:
        """
        Комбинирует все источники по правилу Ягера
        (опциональный метод)
        """
        if not self.ds:
            raise ValueError("Данные не загружены. Сначала вызовите load_from_dass()")
        
        bpas = data["bpas"]
        
        if len(bpas) == 0:
            return {}
        elif len(bpas) == 1:
            return bpas[0]
        
        result = bpas[0]
        for bpa in bpas[1:]:
            result = self.ds.yager_combine(result, bpa)
        
        return result
    
    def compute_belief(self, data: Dict[str, Any], event_str: str) -> float:
        """
        Вычисляет Belief для события
        """
        if not self.ds:
            raise ValueError("Данные не загружены. Сначала вызовите load_from_dass()")
        
        event = self._parse_subset_str(event_str)
        bpa = self.combine_all_dempster(data)
        
        return self.ds.belief(set(event), bpa)
    
    def compute_plausibility(self, data: Dict[str, Any], event_str: str) -> float:
        """
        Вычисляет Plausibility для события
        """
        if not self.ds:
            raise ValueError("Данные не загружены. Сначала вызовите load_from_dass()")
        
        event = self._parse_subset_str(event_str)
        bpa = self.combine_all_dempster(data)
        
        return self.ds.plausibility(set(event), bpa)
    
    # ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ
    
    def _parse_subset_str(self, subset_str: str) -> frozenset:
        """Парсит строку множества в frozenset"""
        if subset_str == "{}":
            return frozenset()
        
        elements_str = subset_str.strip("{}")
        if not elements_str:
            return frozenset()
        
        elements = elements_str.split(",")
        return frozenset(elements)
    
    def format_subset(self, subset: frozenset) -> str:
        """Форматирует frozenset в строку множества"""
        if not subset:
            return "{}"
        
        sorted_elements = sorted(subset)
        return "{" + ",".join(sorted_elements) + "}"
    
    def format_result(self, result: Dict[frozenset, float]) -> Dict[str, float]:
        """Форматирует результат для сохранения в JSON"""
        formatted = {}
        for subset, mass in result.items():
            subset_str = self.format_subset(subset)
            formatted[subset_str] = round(mass, 6)
        return formatted
    
    def discount_bpa(self, data: Dict[str, Any], source_index: int, 
                    alpha: float) -> Dict[frozenset, float]:
        """
        Применяет дисконтирование к указанному источнику
        
        Args:
            data: подготовленные данные
            source_index: индекс источника (0-based)
            alpha: коэффициент дисконтирования (0=надежный, 1=ненадежный)
            
        Returns:
            Дисконтированное BPA
        """
        if not self.ds:
            raise ValueError("Данные не загружены. Сначала вызовите load_from_dass()")
        
        if source_index >= len(data["bpas"]):
            raise ValueError(f"Нет источника с индексом {source_index}")
        
        bpa = data["bpas"][source_index]
        return self.ds.discount(bpa, alpha)