"""
Ядро теории Демпстера-Шейфера - реализация основных функций из главы 2
"""
import itertools
from typing import Set, Dict, List, FrozenSet

class DempsterShafer:
    """Реализация основных функций теории Демпстера-Шейфера"""
    
    def __init__(self, frame_of_discernment: Set[str]):
        self.frame = frame_of_discernment

    @staticmethod    
    def _generate_all_subsets(elements: List[str]) -> List[FrozenSet]:
        """Генерирует все подмножества фрейма"""
        subsets = []
        for r in range(len(elements) + 1):
            for combo in itertools.combinations(elements, r):
                subsets.append(frozenset(combo))
        return subsets
    
    def calculate_bpa(self, data: Dict[str, int]) -> Dict[FrozenSet, float]:
        """Вычисляет BPA по формуле (2.1) из книги"""
        total = sum(data.values())
        bpa = {}
        
        for subset_str, count in data.items():
            # Конвертируем строку "{1,2}" в frozenset
            elements = subset_str.strip("{}").split(",")
            subset = frozenset() if elements == [''] else frozenset(elements)
            bpa[subset] = count / total
            
        return bpa
    
    def belief(self, event: Set[str], bpa: Dict[FrozenSet, float]) -> float:
        """Функция доверия Bel(A) - формула (2.2)"""
        event_fs = frozenset(event)
        return sum(mass for subset, mass in bpa.items() if subset.issubset(event_fs))
    
    def plausibility(self, event: Set[str], bpa: Dict[FrozenSet, float]) -> float:
        """Функция правдоподобия Pl(A) - формула (2.2)"""
        event_fs = frozenset(event)
        return sum(mass for subset, mass in bpa.items() if subset.intersection(event_fs))
    
    def dempster_combine(self, bpa1: Dict[FrozenSet, float], bpa2: Dict[FrozenSet, float]) -> Dict[FrozenSet, float]:
        """Правило комбинирования Демпстера - раздел 2.6.1"""
        # Вычисляем конфликт K
        conflict = 0.0
        for s1, m1 in bpa1.items():
            for s2, m2 in bpa2.items():
                if s1.isdisjoint(s2):
                    conflict += m1 * m2
        
        if conflict == 1:
            raise ValueError("Полный конфликт между источниками!")
        
        # Комбинируем
        combined = {}
        for s1, m1 in bpa1.items():
            for s2, m2 in bpa2.items():
                intersection = s1 & s2
                if not intersection:
                    continue
                if intersection not in combined:
                    combined[intersection] = 0.0
                combined[intersection] += m1 * m2
        
        # Нормализуем
        z = 1 - conflict
        for key in combined:
            combined[key] /= z
        
        # combined[frozenset()] = 0.0  # Не добавляем служебный ключ пустого множества в результат
        return combined
    
    def dempster_combine_multiple(self, *bpas: Dict[FrozenSet, float]) -> Dict[FrozenSet, float]:
        """
        Правило комбинирования Демпстера для произвольного числа источников
        Использует ассоциативное свойство: m12...n = ((m1 ⊕ m2) ⊕ m3) ⊕ ... ⊕ mn
        """
        if len(bpas) == 0:
            return {}
        elif len(bpas) == 1:
            return bpas[0]
        
        # Начинаем с первого источника
        result = bpas[0]
        
        # Последовательно комбинируем с остальными источниками
        for bpa in bpas[1:]:
            result = self.dempster_combine(result, bpa)
        
        return result
    
    def discount(self, bpa: Dict[FrozenSet, float], alpha: float) -> Dict[FrozenSet, float]:
        """Правило дисконтирования - раздел 2.6.2"""
        discounted = {}
        for subset, mass in bpa.items():
            discounted[subset] = (1 - alpha) * mass
        
        # Добавляем массу для универсального множества
        omega = frozenset(self.frame)
        discounted[omega] = discounted.get(omega, 0.0) + alpha
        return discounted
    
    def yager_combine(self, bpa1: Dict[FrozenSet, float], bpa2: Dict[FrozenSet, float]) -> Dict[FrozenSet, float]:
        """Правило комбинирования Ягера - раздел 2.6.3"""
        combined = {}
        conflict = 0.0
        
        # Вычисляем q(A) для всех пересечений
        for s1, m1 in bpa1.items():
            for s2, m2 in bpa2.items():
                intersection = s1 & s2

                if not intersection:
                    conflict += m1 * m2
                    continue

                if intersection not in combined:
                    combined[intersection] = 0.0
                combined[intersection] += m1 * m2
        
        # Переносим конфликт в универсальное множество
        omega = frozenset(self.frame)
        combined[omega] = combined.get(omega, 0.0) + conflict
        
        # Убеждаемся, что пустое множество = 0
        # combined[frozenset()] = 0.0  # Не добавляем служебный ключ пустого множества в результат
        
        return combined
    
    def yager_combine_multiple(self, *bpas: Dict[FrozenSet, float]) -> Dict[FrozenSet, float]:
        """
        Правило комбинирования Ягера для произвольного числа источников
        """
        if len(bpas) == 0:
            return {}
        elif len(bpas) == 1:
            return bpas[0]
        
        # Начинаем с первого источника
        result = bpas[0]
        
        # Последовательно комбинируем с остальными источниками
        for bpa in bpas[1:]:
            result = self.yager_combine(result, bpa)
        
        return result
