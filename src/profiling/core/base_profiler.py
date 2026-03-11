# src/profiling/core/base_profiler.py
"""
Базовый класс для всех сборщиков данных профилирования.
Все сборщики должны наследоваться от этого класса.
"""

import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class ProfilerState(Enum):
    """Состояние профилировщика"""
    IDLE = "idle"
    RUNNING = "running"
    STOPPED = "stopped"


@dataclass
class ProfileResult:
    """Результат профилирования"""
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    duration_seconds: float


class BaseProfiler(ABC):
    """Абстрактный базовый класс для всех профилировщиков"""
    
    def __init__(self, name: str, enabled: bool = True):
        self.name = name
        self.enabled = enabled
        self.state = ProfilerState.IDLE
        self.start_time: Optional[float] = None
        self.results: Optional[ProfileResult] = None
        
    def __enter__(self):
        """Поддержка контекстного менеджера"""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Поддержка контекстного менеджера"""
        self.stop()
        
    def start(self) -> None:
        """Начать сбор данных"""
        if not self.enabled:
            return
            
        if self.state == ProfilerState.RUNNING:
            raise RuntimeError(f"Profiler {self.name} is already running")
            
        self.state = ProfilerState.RUNNING
        self.start_time = time.perf_counter()
        self._on_start()
        
    def stop(self) -> ProfileResult:
        """Остановить сбор данных и вернуть результаты"""
        if not self.enabled:
            return ProfileResult({}, {}, 0.0)
            
        if self.state != ProfilerState.RUNNING:
            raise RuntimeError(f"Profiler {self.name} is not running")
            
        end_time = time.perf_counter()
        duration = end_time - (self.start_time or end_time)
        
        # Собираем данные
        profiler_data = self._on_stop()
        
        # Создаем результат
        self.results = ProfileResult(
            data=profiler_data,
            metadata={
                'profiler_name': self.name,
                'duration_seconds': duration,
                'start_time': self.start_time,
                'end_time': end_time,
            },
            duration_seconds=duration
        )
        
        self.state = ProfilerState.STOPPED
        return self.results
    
    def profile(self, func, *args, **kwargs):
        """Профилировать выполнение функции"""
        if not self.enabled:
            return func(*args, **kwargs)
            
        self.start()
        try:
            result = func(*args, **kwargs)
        finally:
            self.stop()
            
        return result, self.results
    
    @abstractmethod
    def _on_start(self) -> None:
        """Вызывается при старте профилирования (реализация специфична)"""
        pass
    
    @abstractmethod
    def _on_stop(self) -> Dict[str, Any]:
        """Вызывается при остановке профилирования, возвращает данные"""
        pass
    
    def get_summary(self) -> Dict[str, Any]:
        """Краткое описание профилировщика"""
        return {
            'name': self.name,
            'enabled': self.enabled,
            'state': self.state.value,
            'has_results': self.results is not None
        }
    
    def cleanup(self) -> None:
        """Очистка ресурсов профилировщика.
        Должен быть переопределен в подклассах при необходимости.
        """
        pass  # Базовая реализация ничего не делает