# src/profiling/artifacts/metadata_collector.py
"""
Сбор метаданных об окружении и системе.
Максимально упрощенная версия без сложных зависимостей.
"""

import json
import sys
import platform
import psutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Union
import socket
import os

class MetadataCollector:
    """
    Упрощенный сборщик метаданных.
    Использует только стандартные библиотеки и psutil.
    """
    
    def __init__(self):
        self.metadata = {}
    
    def collect_all(self) -> Dict[str, Any]:
        """
        Собирает все возможные метаданные.
        
        Returns:
            Полный словарь метаданных
        """
        self.metadata = {
            'timestamp': datetime.now().isoformat(),
            'system': self._collect_system_info(),
            'python': self._collect_python_info(),
            'hardware': self._collect_hardware_info(),
            'dependencies': self._collect_dependencies(),
        }
        
        return self.metadata
    
    def _collect_system_info(self) -> Dict[str, Any]:
        """Собирает информацию о системе."""
        system_info = {}
        
        try:
            system_info['platform'] = platform.platform()
            system_info['system'] = platform.system()
            system_info['release'] = platform.release()
            system_info['architecture'] = platform.architecture()[0]
            system_info['processor'] = platform.processor()
            system_info['machine'] = platform.machine()
            system_info['node'] = platform.node()
            system_info['timezone'] = datetime.now().astimezone().tzname()
        except Exception as e:
            system_info['error'] = f"System info error: {e}"
        
        return system_info
    
    def _collect_python_info(self) -> Dict[str, Any]:
        """Собирает информацию о Python."""
        python_info = {}
        
        try:
            python_info['version'] = sys.version
            python_info['implementation'] = platform.python_implementation()
            python_info['compiler'] = platform.python_compiler()
            python_info['executable'] = sys.executable
        except Exception as e:
            python_info['error'] = f"Python info error: {e}"
        
        return python_info
    
    def _collect_hardware_info(self) -> Dict[str, Any]:
        """Собирает информацию о железе."""
        hardware_info = {}
        
        # CPU информация
        try:
            cpu_info = {}
            try:
                cpu_info['count_physical'] = psutil.cpu_count(logical=False)
                cpu_info['count_logical'] = psutil.cpu_count(logical=True)
            except:
                pass
                
            hardware_info['cpu'] = cpu_info
                
        except Exception as e:
            hardware_info['cpu_error'] = f'CPU info error: {e}'
        
        # Память
        try:
            memory = psutil.virtual_memory()
            hardware_info['memory'] = {
                'total_gb': memory.total / (1024**3),
                'available_gb': memory.available / (1024**3),
                'percent': memory.percent,
            }
        except Exception as e:
            hardware_info['memory_error'] = f'Memory info error: {e}'
        
        return hardware_info
    
    def _collect_dependencies(self) -> Dict[str, Any]:
        """Собирает информацию о зависимостях."""
        dependencies = {
            'collection_method': 'pip_freeze'
        }
        
        # Версия pip
        try:
            pip_version = subprocess.check_output(
                [sys.executable, '-m', 'pip', '--version'],
                text=True,
                stderr=subprocess.DEVNULL,
                shell=True if platform.system() == "Windows" else False
            ).strip()
            dependencies['pip'] = pip_version
        except:
            dependencies['pip'] = 'Unknown'
        
        # pip freeze
        try:
            freeze_output = subprocess.check_output(
                [sys.executable, '-m', 'pip', 'freeze'],
                text=True,
                stderr=subprocess.DEVNULL,
                shell=True if platform.system() == "Windows" else False
            )
            
            # Ищем ключевые пакеты
            key_packages = ['psutil', 'numpy', 'pandas', 'matplotlib']
            found_packages = {}
            
            for line in freeze_output.strip().split('\n'):
                if line and '==' in line:
                    package, version = line.split('==', 1)
                    if package in key_packages:
                        found_packages[package] = version
            
            for package in key_packages:
                dependencies[package] = found_packages.get(package, 'Not installed')
            
        except Exception as e:
            dependencies['error'] = f'Failed to run pip freeze: {str(e)}'
        
        return dependencies
    
    def save_to_file(self, filepath: Union[str, Path]):
        """
        Сохраняет метаданные в файл.
        
        Args:
            filepath: Путь для сохранения
        """
        filepath = Path(filepath)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, indent=2, ensure_ascii=False)