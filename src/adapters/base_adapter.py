# src/adapters/base_adapter.py
"""
Базовый интерфейс для всех адаптеров Демпстера-Шейфера
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple


class BaseDempsterShaferAdapter(ABC):
    """Базовый класс адаптера для всех реализаций"""
    
    @abstractmethod
    def load_from_dass(self, dass_data: Dict[str, Any]) -> Any:
        """
        Загружает данные из DASS формата
        
        Args:
            dass_data: данные в формате DASS
            
        Returns:
            Подготовленные данные в формате библиотеки
        """
        pass
    
    @abstractmethod
    def combine_all_dempster(self, data: Any) -> Dict:
        """
        Комбинирует все источники по правилу Демпстера
        
        Args:
            data: подготовленные данные
            
        Returns:
            Результирующее BPA
        """
        pass
    
    @abstractmethod
    def combine_dempster_pair(self, bpa1: Dict, bpa2: Dict) -> Dict:
        """
        Комбинирует два BPA по правилу Демпстера
        
        Args:
            bpa1: первое BPA
            bpa2: второе BPA
            
        Returns:
            Результирующее BPA
        """
        pass
    
    @abstractmethod
    def validate_bpa(self, bpa: Dict) -> Tuple[bool, float]:
        """
        Проверяет корректность BPA
        
        Args:
            bpa: BPA для проверки
            
        Returns:
            (валидно ли, сумма масс)
        """
        pass
    
    def combine_all_yager(self, data: Any) -> Dict:
        """
        Комбинирует все источники по правилу Ягера
        (опционально)
        """
        raise NotImplementedError("Метод combine_all_yager не реализован")
    
    def compute_belief(self, data: Any, event_str: str) -> float:
        """
        Вычисляет Belief для события
        (опционально)
        """
        raise NotImplementedError("Метод compute_belief не реализован")
    
    def compute_plausibility(self, data: Any, event_str: str) -> float:
        """
        Вычисляет Plausibility для события
        (опционально)
        """
        raise NotImplementedError("Метод compute_plausibility не реализован")