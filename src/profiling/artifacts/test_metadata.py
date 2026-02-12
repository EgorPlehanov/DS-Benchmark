# src/profiling/artifacts/test_metadata.py
"""
TestMetadata - сбор метаданных теста и окружения.
Рабочая версия без проблемных зависимостей.
"""

import sys
import platform
import json
import socket
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Union
import subprocess  # Будем использовать для получения информации о пакетах


class TestMetadata:
    """Сборщик метаданных о тесте и окружении."""
    
    def __init__(self):
        self.metadata = {}
    
    def collect_all(self) -> Dict[str, Any]:
        """Собирает все метаданные."""
        self.metadata = {
            "timestamp": datetime.now().isoformat(),
            "environment": self._collect_environment(),
            "python": self._collect_python_info(),
            "packages": self._collect_packages_info_safe(),
            "test_info": {},
            "performance_limits": self._collect_performance_limits()
        }
        
        # Пытаемся собрать системную информацию, если доступны модули
        try:
            import psutil
            self.metadata["system"] = self._collect_system_info()
        except ImportError:
            self.metadata["system"] = {"note": "psutil not installed"}
        
        return self.metadata
    
    def _collect_environment(self) -> Dict[str, Any]:
        """Собирает информацию об окружении."""
        return {
            "platform": sys.platform,
            "platform_version": platform.version(),
            "platform_release": platform.release(),
            "platform_system": platform.system(),
            "platform_machine": platform.machine(),
            "processor": platform.processor(),
            "hostname": socket.gethostname(),
            "username": self._get_username(),
            "working_directory": str(Path.cwd().absolute())
        }
    
    def _get_username(self) -> str:
        """Получает имя пользователя."""
        try:
            import getpass
            return getpass.getuser()
        except (ImportError, OSError):
            return "unknown"
    
    def _collect_system_info(self) -> Dict[str, Any]:
        """Собирает системную информацию (только если psutil доступен)."""
        try:
            import psutil
            
            cpu_info = {}
            try:
                cpu_freq = psutil.cpu_freq()
                if hasattr(cpu_freq, 'current'):
                    cpu_info["current"] = cpu_freq.current
                if hasattr(cpu_freq, 'max'):
                    cpu_info["max"] = cpu_freq.max
            except (AttributeError, TypeError):
                cpu_info["current"] = None
                cpu_info["max"] = None
            
            return {
                "cpu_count": psutil.cpu_count(),
                "cpu_freq": cpu_info,
                "memory_total_gb": psutil.virtual_memory().total / (1024**3),
                "memory_available_gb": psutil.virtual_memory().available / (1024**3),
                "disk_usage": {
                    "total_gb": psutil.disk_usage('/').total / (1024**3),
                    "free_gb": psutil.disk_usage('/').free / (1024**3)
                }
            }
        except Exception as e:
            return {"error": str(e), "note": "psutil error"}
    
    def _collect_python_info(self) -> Dict[str, Any]:
        """Собирает информацию о Python."""
        return {
            "version": sys.version,
            "version_info": list(sys.version_info),
            "implementation": platform.python_implementation(),
            "compiler": platform.python_compiler(),
            "executable": sys.executable,
            "path": sys.path[:10]  # Ограничиваем для читаемости
        }
    
    def _collect_packages_info_safe(self) -> Dict[str, Any]:
        """
        Безопасный сбор информации о пакетах.
        Использует pip list если доступен.
        """
        packages_info = {
            "method": "unknown",
            "packages": {}
        }
        
        # Способ 1: pip list (надежный)
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "list", "--format=json"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False
            )
            
            if result.returncode == 0:
                packages = json.loads(result.stdout)
                packages_info["method"] = "pip_list"
                packages_info["packages"] = {
                    pkg["name"]: pkg["version"] for pkg in packages
                }
                return packages_info
        except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception):
            pass
        
        # Способ 2: sys.modules (ограниченный)
        packages_info["method"] = "sys_modules"
        for module_name in sorted(sys.modules.keys()):
            if not module_name.startswith('_') and '.' not in module_name:
                module = sys.modules[module_name]
                if hasattr(module, '__version__'):
                    packages_info["packages"][module_name] = module.__version__
                elif hasattr(module, 'version'):
                    packages_info["packages"][module_name] = module.version
        
        return packages_info
    
    def _collect_performance_limits(self) -> Dict[str, Any]:
        """Собирает информацию о лимитах производительности."""
        float_info_dict = {
            "max": sys.float_info.max,
            "max_exp": sys.float_info.max_exp,
            "max_10_exp": sys.float_info.max_10_exp,
            "min": sys.float_info.min,
            "min_exp": sys.float_info.min_exp,
            "min_10_exp": sys.float_info.min_10_exp,
            "dig": sys.float_info.dig,
            "mant_dig": sys.float_info.mant_dig,
            "epsilon": sys.float_info.epsilon,
            "radix": sys.float_info.radix,
            "rounds": sys.float_info.rounds
        }
        
        result = {
            "recursion_limit": sys.getrecursionlimit(),
            "maxsize": sys.maxsize,
            "float_info": float_info_dict
        }
        
        if hasattr(sys, 'int_info'):
            result["int_info"] = {
                "bits_per_digit": sys.int_info.bits_per_digit,
                "sizeof_digit": sys.int_info.sizeof_digit
            }
        
        return result
    
    def add_test_info(self, test_data: Dict[str, Any]) -> None:
        """Добавляет информацию о тесте."""
        self.metadata["test_info"] = {
            "frame_size": len(test_data.get("frame_of_discernment", [])),
            "sources_count": len(test_data.get("bba_sources", [])),
            "test_description": test_data.get("metadata", {}).get("description", ""),
            "test_id": test_data.get("metadata", {}).get("test_id", "")
        }
    
    def add_run_parameters(self, **kwargs) -> None:
        """Добавляет параметры запуска."""
        if "run_parameters" not in self.metadata:
            self.metadata["run_parameters"] = {}
        self.metadata["run_parameters"].update(kwargs)
    
    def to_dict(self) -> Dict[str, Any]:
        """Возвращает метаданные в виде словаря."""
        return self.metadata.copy()
    
    def save(self, filepath: Union[str, Path]) -> None:
        """Сохраняет метаданные в файл."""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, indent=2, ensure_ascii=False)


# Фабричные функции
def collect_test_metadata(test_data: Optional[Dict[str, Any]] = None,
                         **run_params) -> Dict[str, Any]:
    """
    Собирает все метаданные теста.
    
    Args:
        test_data: Данные теста (опционально)
        **run_params: Параметры запуска
        
    Returns:
        Dict[str, Any]: Собранные метаданные
    """
    metadata = TestMetadata()
    metadata.collect_all()
    
    if test_data:
        metadata.add_test_info(test_data)
    
    if run_params:
        metadata.add_run_parameters(**run_params)
    
    return metadata.to_dict()


def collect_basic_metadata(test_data: Optional[Dict[str, Any]] = None,
                          **run_params) -> Dict[str, Any]:
    """
    Собирает только базовые метаданные (без внешних зависимостей).
    """
    metadata = TestMetadata()
    
    # Собираем только то, что не требует внешних модулей
    metadata.metadata = {
        "timestamp": datetime.now().isoformat(),
        "environment": metadata._collect_environment(),
        "python": metadata._collect_python_info(),
        "performance_limits": metadata._collect_performance_limits(),
        "packages": {"method": "basic", "packages": {}},
        "system": {"note": "basic mode - no psutil"}
    }
    
    if test_data:
        metadata.add_test_info(test_data)
    
    if run_params:
        metadata.add_run_parameters(**run_params)
    
    return metadata.to_dict()
