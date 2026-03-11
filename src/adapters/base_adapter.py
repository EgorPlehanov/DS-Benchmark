# adapters/base_adapter.py
"""
Базовый абстрактный класс адаптера для теории Демпстера-Шейфера.
Определяет единый интерфейс для всех реализаций.
Только абстрактные методы - без реализации.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Union


class BaseDempsterShaferAdapter(ABC):
    """
    Абстрактный базовый класс для адаптеров теории Демпстера-Шейфера.
    
    Все конкретные адаптеры должны наследоваться от этого класса
    и реализовывать все абстрактные методы.
    """
    
    # ==================== ИНИЦИАЛИЗАЦИЯ И ЗАГРУЗКА ====================

    @property
    def benchmark_name(self) -> str:
        """Каноническое имя адаптера для CLI/папок результатов."""
        return self.__class__.__name__.replace("Adapter", "").lower()


    @abstractmethod
    def _ensure_backend(self) -> None:
        """Проверяет доступность backend-зависимостей адаптера."""
        pass
    
    @abstractmethod
    def load_from_dass(self, dass_data: Dict[str, Any]) -> Any:
        """
        Загружает данные из DASS формата в объект библиотеки.
        
        Args:
            dass_data: Словарь с данными в формате DASS
            
        Returns:
            Объект библиотеки с загруженными данными
        """
        pass
    
    @abstractmethod
    def get_frame_of_discernment(self, data: Any) -> List[str]:
        """
        Возвращает элементы фрейма различения.
        
        Args:
            data: Объект с загруженными данными
            
        Returns:
            Список элементов фрейма
        """
        pass
    
    @abstractmethod
    def get_sources_count(self, data: Any) -> int:
        """
        Возвращает количество источников (BPA).
        
        Args:
            data: Объект с загруженными данными
            
        Returns:
            Количество источников
        """
        pass
    
    # ==================== ОСНОВНЫЕ ФУНКЦИИ ====================
    
    @abstractmethod
    def calculate_belief(self, data: Any, event: Union[str, List[str]]) -> float:
        """
        Вычисляет функцию доверия Bel(A) для события.
        
        Args:
            data: Объект с загруженными данными
            event: Событие в виде строки "{A,B}" или списка ["A", "B"]
            
        Returns:
            Значение Belief (0..1)
        """
        pass
    
    @abstractmethod
    def calculate_plausibility(self, data: Any, event: Union[str, List[str]]) -> float:
        """
        Вычисляет функцию правдоподобия Pl(A) для события.
        
        Args:
            data: Объект с загруженными данными
            event: Событие в виде строки "{A,B}" или списка ["A", "B"]
            
        Returns:
            Значение Plausibility (0..1)
        """
        pass
    
    # ==================== КОМБИНИРОВАНИЕ ДЕМПСТЕРА ====================
    
    @abstractmethod
    def combine_sources_dempster(self, data: Any) -> Dict[str, float]:
        """
        Комбинирует все источники по правилу Демпстера.
        
        Args:
            data: Объект с загруженными данными (несколько источников)
            
        Returns:
            Словарь BPA после комбинирования: подмножество (строка) -> масса
        """
        pass
    
    # ==================== ДИСКОНТИРОВАНИЕ ====================
    
    @abstractmethod
    def apply_discounting(self, data: Any, alpha: float) -> List[Dict[str, float]]:
        """
        Применяет дисконтирование ко всем источникам.
        
        Args:
            data: Объект с загруженными данными
            alpha: Коэффициент дисконтирования (0..1)
            
        Returns:
            Список словарей BPA после дисконтирования для каждого источника
        """
        pass
    
    # ==================== КОМБИНИРОВАНИЕ ЯГЕРА ====================
    
    @abstractmethod
    def combine_sources_yager(self, data: Any) -> Dict[str, float]:
        """
        Комбинирует все источники по правилу Ягера.
        
        Args:
            data: Объект с загруженными данными (несколько источников)
            
        Returns:
            Словарь BPA после комбинирования: подмножество (строка) -> масса
        """
        pass
