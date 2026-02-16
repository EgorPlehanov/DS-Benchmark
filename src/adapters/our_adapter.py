# adapters/our_adapter.py
"""
Адаптер для нашей реализации Демпстера-Шейфера (dempster_core.py)
Stateless реализация - не хранит состояние.
"""

from typing import Dict, List, Any, Union, Set
from .base_adapter import BaseDempsterShaferAdapter

# Импортируем нашу реализацию
from ..core.dempster_core import DempsterShafer


class OurImplementationAdapter(BaseDempsterShaferAdapter):
    """
    Stateless адаптер для нашей реализации.
    Не хранит состояние между вызовами.
    """
    
    def __init__(self):
        """Инициализация адаптера (без состояния)."""
        self._ensure_backend()

    def _ensure_backend(self) -> None:
        """Проверяет доступность нашей backend-реализации."""
        if DempsterShafer is None:  # pragma: no cover
            raise ImportError("Не удалось импортировать внутреннюю реализацию DempsterShafer.")
    
    def load_from_dass(self, dass_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Загружает данные из DASS формата.
        Возвращает словарь с конвертированными данными.
        """
        # Извлекаем фрейм
        frame_elements = dass_data["frame_of_discernment"]
        frame = set(frame_elements)
        
        # Конвертируем BPA из DASS формата в наш формат
        bpas = []
        for source in dass_data["bba_sources"]:
            bpa_dict = {}
            for subset_str, mass in source["bba"].items():
                subset = self._parse_subset_str(subset_str)
                bpa_dict[subset] = mass
            bpas.append(bpa_dict)
        
        return {
            'frame': frame,
            'frame_elements': frame_elements,
            'bpas': bpas,
            'original_dass': dass_data  # Сохраняем оригинал на всякий случай
        }
    
    def get_frame_of_discernment(self, data: Any) -> List[str]:
        """Возвращает элементы фрейма различения."""
        if isinstance(data, dict) and 'frame_elements' in data:
            return data['frame_elements']
        return []
    
    def get_sources_count(self, data: Any) -> int:
        """Возвращает количество источников."""
        if isinstance(data, dict) and 'bpas' in data:
            return len(data['bpas'])
        return 0
    
    def calculate_belief(self, data: Any, event: Union[str, List[str]]) -> float:
        """
        Вычисляет функцию доверия Bel(A) для события.
        
        Args:
            data: Должен содержать 'frame' и 'bpa' 
                 или быть BPA напрямую
            event: Событие
            
        Returns:
            Значение Belief
        """
        # Получаем BPA из data
        bpa = self._extract_bpa_from_data(data)
        
        # Создаем экземпляр DempsterShafer
        frame = self._extract_frame_from_data(data)
        ds = DempsterShafer(frame)
        
        # Парсим событие
        event_set = self._parse_event(event)
        
        # Вычисляем Belief
        return ds.belief(event_set, bpa)
    
    def calculate_plausibility(self, data: Any, event: Union[str, List[str]]) -> float:
        """
        Вычисляет функцию правдоподобия Pl(A) для события.
        """
        # Получаем BPA из data
        bpa = self._extract_bpa_from_data(data)
        
        # Создаем экземпляр DempsterShafer
        frame = self._extract_frame_from_data(data)
        ds = DempsterShafer(frame)
        
        # Парсим событие
        event_set = self._parse_event(event)
        
        # Вычисляем Plausibility
        return ds.plausibility(event_set, bpa)
    
    def combine_sources_dempster(self, data: Any) -> Dict[str, float]:
        """
        Комбинирует все источники по правилу Демпстера.
        
        Args:
            data: Должен содержать 'frame' и 'bpas'
            
        Returns:
            BPA после комбинирования в строковом формате
        """
        # Извлекаем данные
        frame = self._extract_frame_from_data(data)
        bpas = self._extract_bpas_from_data(data)
        
        if not bpas:
            return {}
        
        # Создаем экземпляр DempsterShafer
        ds = DempsterShafer(frame)
        
        # Комбинируем все BPA
        if len(bpas) == 1:
            result = bpas[0]
        else:
            result = bpas[0]
            for bpa in bpas[1:]:
                result = ds.dempster_combine(result, bpa)
        
        # Конвертируем в строковый формат
        return self._format_bpa(result)
    
    def apply_discounting(self, data: Any, alpha: float) -> List[Dict[str, float]]:
        """
        Применяет дисконтирование ко всем источникам.
        
        Args:
            data: Должен содержать 'frame' и 'bpas'
            alpha: Коэффициент дисконтирования
            
        Returns:
            Список BPA после дисконтирования в строковом формате
        """
        # Извлекаем данные
        frame = self._extract_frame_from_data(data)
        bpas = self._extract_bpas_from_data(data)
        
        # Создаем экземпляр DempsterShafer
        ds = DempsterShafer(frame)
        
        # Применяем дисконтирование к каждому BPA
        discounted_bpas = []
        for bpa in bpas:
            discounted = ds.discount(bpa, alpha)
            discounted_bpas.append(self._format_bpa(discounted))
        
        return discounted_bpas
    
    def combine_sources_yager(self, data: Any) -> Dict[str, float]:
        """
        Комбинирует все источники по правилу Ягера.
        
        Args:
            data: Должен содержать 'frame' и 'bpas'
            
        Returns:
            BPA после комбинирования в строковом формате
        """
        # Извлекаем данные
        frame = self._extract_frame_from_data(data)
        bpas = self._extract_bpas_from_data(data)
        
        if not bpas:
            return {}
        
        # Создаем экземпляр DempsterShafer
        ds = DempsterShafer(frame)
        
        # Комбинируем все BPA
        if len(bpas) == 1:
            result = bpas[0]
        else:
            result = bpas[0]
            for bpa in bpas[1:]:
                result = ds.yager_combine(result, bpa)
        
        # Конвертируем в строковый формат
        return self._format_bpa(result)
    
    # ==================== ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ====================
    
    def _extract_frame_from_data(self, data: Any) -> Set[str]:
        """Извлекает фрейм из данных."""
        if isinstance(data, dict) and 'frame' in data:
            return data['frame']
        # Если data это BPA напрямую, пытаемся извлечь элементы
        elif isinstance(data, dict):
            # Это может быть BPA {frozenset: float}
            elements = set()
            for subset in data.keys():
                if isinstance(subset, frozenset):
                    elements.update(subset)
            return elements
        return set()
    
    def _extract_bpa_from_data(self, data: Any) -> Dict:
        """Извлекает BPA из данных."""
        # Если data это BPA напрямую
        if isinstance(data, dict):
            # Проверяем, похоже ли на BPA {frozenset: float}
            if data and isinstance(next(iter(data.keys())), frozenset):
                return data
            # Или data содержит 'bpa'
            elif 'bpa' in data:
                return data['bpa']
            # Или это первый BPA из списка
            elif 'bpas' in data and data['bpas']:
                return data['bpas'][0]
        return {}
    
    def _extract_bpas_from_data(self, data: Any) -> List[Dict]:
        """Извлекает список BPA из данных."""
        if isinstance(data, dict) and 'bpas' in data:
            return data['bpas']
        return []
    
    def _parse_event(self, event: Union[str, List[str]]) -> set:
        """Парсит событие в множество."""
        if isinstance(event, str):
            return set(self._parse_subset_str(event))
        elif isinstance(event, list):
            return set(event)
        else:
            raise TypeError(f"Не поддерживаемый тип события: {type(event)}")
    
    def _parse_subset_str(self, subset_str: str) -> frozenset:
        """Парсит строку множества в frozenset."""
        if subset_str == "{}":
            return frozenset()
        
        elements = subset_str.strip("{}").split(",")
        if elements == ['']:
            return frozenset()
        
        return frozenset(elements)
    
    def _format_subset(self, subset) -> str:
        """Форматирует множество в строку."""
        if not subset:
            return "{}"
        
        return "{" + ",".join(sorted(subset)) + "}"
    
    def _format_bpa(self, bpa: Dict) -> Dict[str, float]:
        """Конвертирует BPA в строковый формат."""
        formatted = {}
        for subset, mass in bpa.items():
            subset_str = self._format_subset(subset)
            formatted[subset_str] = round(mass, 10)
        return formatted
