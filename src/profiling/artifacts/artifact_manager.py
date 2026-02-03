# src/profiling/artifacts/artifact_manager.py
"""
ArtifactManager - управление артефактами профилирования.
Безопасная версия с обработкой ошибок ввода-вывода.
"""

import json
import os
import platform
import psutil
import subprocess
import pickle
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
import tempfile

class ArtifactManager:
    """
    Управляет структурой папок и сохранением артефактов.
    Каждый запуск создает новую папку artifacts/YYYYMMDD_HHMMSS/
    """
    
    def __init__(self, base_dir: Union[str, Path] = "artifacts", 
                 session_id: Optional[str] = None):
        """
        Инициализация менеджера артефактов.
        
        Args:
            base_dir: Базовая директория для артефактов
            session_id: Идентификатор сессии (если None, генерируется)
        """
        self.base_dir = Path(base_dir)
        
        # Генерируем уникальный ID сессии
        if session_id is None:
            self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        else:
            self.session_id = session_id
            
        self.session_path = self.base_dir / self.session_id
        
        # Определяем структуру папок
        self.paths = {
            'meta': self.session_path / 'meta.json',
            'config': self.session_path / 'config.json',
            'input': self.session_path / 'input',
            'profilers': self.session_path / 'profilers',
            'scalene': self.session_path / 'profilers' / 'scalene',
            'cprofile': self.session_path / 'profilers' / 'cprofile',
            'system': self.session_path / 'profilers' / 'system',
            'test_results': self.session_path / 'test_results',
            'logs': self.session_path / 'logs',
            'temp': self.session_path / 'temp'
        }
        
        # Создаем все директории
        self._create_directories()
        
        print(f"📁 ArtifactManager создан: {self.session_path}")
    
    def _create_directories(self):
        """Создает все необходимые директории."""
        for path in self.paths.values():
            try:
                path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                print(f"⚠️  Ошибка создания директории {path}: {e}")
    
    def get_session_info(self) -> Dict[str, Any]:
        """Возвращает информацию о текущей сессии."""
        return {
            'session_id': self.session_id,
            'session_path': str(self.session_path),
            'timestamp': datetime.now().isoformat(),
            'paths': {k: str(v) for k, v in self.paths.items()}
        }
    
    def save_profiler_data(self, 
                          profiler_name: str, 
                          test_name: str, 
                          step_name: str, 
                          data: Dict[str, Any],
                          iteration: int = 1) -> Optional[Path]:
        """
        Сохраняет данные профилировщика.
        
        Args:
            profiler_name: Имя профилировщика (system, scalene, cprofile)
            test_name: Имя теста
            step_name: Имя шага (step1, step2, etc.)
            data: Данные профилирования
            iteration: Номер итерации
            
        Returns:
            Путь к сохраненному файлу или None при ошибке
        """
        try:
            # Определяем директорию для профилировщика
            if profiler_name not in self.paths:
                profiler_dir = self.paths['profilers'] / profiler_name
                profiler_dir.mkdir(parents=True, exist_ok=True)
            else:
                profiler_dir = self.paths[profiler_name]
            
            # Создаем имя файла с итерацией
            if iteration > 1:
                filename = f"{test_name}_iter{iteration}_{step_name}.json"
            else:
                filename = f"{test_name}_{step_name}.json"
            
            filepath = profiler_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return filepath
        except Exception as e:
            print(f"❌ Ошибка сохранения данных профилировщика {profiler_name}: {e}")
            return None
    
    def save_binary_data(self, 
                        data_type: str,
                        test_name: str,
                        step_name: str,
                        binary_data: bytes,
                        iteration: int = 1) -> Optional[Path]:
        """
        Сохраняет бинарные данные (например, .prof файлы).
        
        Args:
            data_type: Тип данных (cprofile_prof, memray_bin, etc.)
            test_name: Имя теста
            step_name: Имя шага
            binary_data: Бинарные данные
            iteration: Номер итерации
            
        Returns:
            Путь к сохраненному файлу или None при ошибке
        """
        try:
            # Создаем директорию для типа данных
            data_dir = self.session_path / 'binary_data' / data_type
            data_dir.mkdir(parents=True, exist_ok=True)
            
            # Создаем имя файла
            if iteration > 1:
                filename = f"{test_name}_iter{iteration}_{step_name}.bin"
            else:
                filename = f"{test_name}_{step_name}.bin"
            
            filepath = data_dir / filename
            
            with open(filepath, 'wb') as f:
                f.write(binary_data)
            
            return filepath
        except Exception as e:
            print(f"❌ Ошибка сохранения бинарных данных: {e}")
            return None
    
    def log_message(self, message: str, level: str = "INFO") -> bool:
        """
        Сохраняет сообщение в лог.
        
        Args:
            message: Текст сообщения
            level: Уровень логирования (INFO, WARNING, ERROR)
            
        Returns:
            True если успешно, False если ошибка
        """
        try:
            log_file = self.paths['logs'] / 'run.log'
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"{timestamp} [{level}] {message}\n"
            
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
            
            return True
        except Exception as e:
            print(f"❌ Ошибка записи в лог: {e}")
            return False
    
    def cleanup_temp_files(self):
        """Очищает временные файлы."""
        temp_dir = self.paths['temp']
        
        if temp_dir.exists():
            try:
                import shutil
                shutil.rmtree(temp_dir)
                temp_dir.mkdir(parents=True, exist_ok=True)
                print(f"🧹 Временные файлы очищены: {temp_dir}")
            except Exception as e:
                print(f"⚠️  Ошибка очистки временных файлов: {e}")
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Возвращает сводку по сессии."""
        summary = {
            'session_id': self.session_id,
            'start_time': self._parse_session_time(),
            'artifacts_count': self._count_artifacts(),
            'disk_usage_mb': self._get_disk_usage(),
            'status': 'active'
        }
        
        return summary
    
    def _parse_session_time(self) -> str:
        """Парсит время из session_id."""
        try:
            date_str = self.session_id[:8]  # YYYYMMDD
            time_str = self.session_id[9:]   # HHMMSS
            return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]} {time_str[:2]}:{time_str[2:4]}:{time_str[4:6]}"
        except:
            return self.session_id
    
    def _count_artifacts(self) -> Dict[str, int]:
        """Подсчитывает количество артефактов по типам."""
        counts = {}
        
        for key, path in self.paths.items():
            if path.exists() and path.is_dir():
                try:
                    file_count = sum(1 for _ in path.rglob('*') if _.is_file())
                    counts[key] = file_count
                except:
                    counts[key] = 0
        
        return counts
    
    def _get_disk_usage(self) -> float:
        """Возвращает использование диска в МБ."""
        total_size = 0
        
        for path in self.paths.values():
            if path.exists():
                try:
                    if path.is_file():
                        total_size += path.stat().st_size
                    else:
                        total_size += sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
                except:
                    pass
        
        return total_size / (1024 * 1024)  # МБ
    
    def _safe_write_json(self, filepath: Path, data: Dict[str, Any]) -> bool:
        """
        Безопасно записывает JSON данные в файл.
        
        Args:
            filepath: Путь к файлу
            data: Данные для записи
            
        Returns:
            True если успешно, False если ошибка
        """
        try:
            # Создаем временный файл, потом переименовываем
            temp_file = filepath.with_suffix('.tmp')
            
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Пытаемся переименовать (атомарная операция)
            temp_file.replace(filepath)
            return True
            
        except PermissionError as e:
            print(f"⚠️  Permission denied for {filepath}: {e}")
            # Попробуем записать напрямую
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                return True
            except Exception as e2:
                print(f"❌ Финальная ошибка записи {filepath}: {e2}")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка записи {filepath}: {e}")
            return False
        
    def _atomic_write_json(self, filepath: Path, data: Dict[str, Any]) -> bool:
        """
        Атомарная запись JSON файла с защитой от сбоев.
        
        Args:
            filepath: Путь к файлу
            data: Данные для записи
            
        Returns:
            True если успешно, False если ошибка
        """
        try:
            # Создаем временный файл в той же директории
            temp_dir = filepath.parent
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            # Создаем временный файл
            with tempfile.NamedTemporaryFile(
                mode='w', 
                encoding='utf-8',
                dir=temp_dir,
                suffix='.tmp',
                delete=False
            ) as tmp_file:
                json.dump(data, tmp_file, indent=2, ensure_ascii=False)
                tmp_path = Path(tmp_file.name)
            
            # Атомарное переименование (работает на всех ОС)
            try:
                # На Windows может потребоваться несколько попыток
                for attempt in range(3):
                    try:
                        tmp_path.replace(filepath)
                        break
                    except PermissionError:
                        if attempt < 2:
                            import time
                            time.sleep(0.1)
                        else:
                            raise
                
                return True
                
            except Exception as e:
                # Если переименование не удалось, удаляем временный файл
                try:
                    tmp_path.unlink(missing_ok=True)
                except:
                    pass
                raise e
                
        except PermissionError as e:
            print(f"⚠️  Отказано в доступе для {filepath}: {e}")
            return False
            
        except Exception as e:
            print(f"❌ Ошибка записи {filepath}: {e}")
            return False
    
    def save_metadata(self, metadata: Dict[str, Any]) -> bool:
        """
        Сохраняет метаданные сессии.
        """
        success = self._atomic_write_json(self.paths['meta'], metadata)
        if success:
            print(f"💾 Метаданные сохранены: {self.paths['meta']}")
        return success
    
    def save_config(self, config: Dict[str, Any]) -> bool:
        """
        Сохраняет конфигурацию тестирования.
        """
        success = self._atomic_write_json(self.paths['config'], config)
        if success:
            print(f"⚙️  Конфигурация сохранена: {self.paths['config']}")
        return success
    
    # Обновляем другие методы save_* для консистентности:
    
    def save_test_input(self, test_name: str, test_data: Dict[str, Any]) -> bool:
        """
        Сохраняет входные данные теста.
        """
        filepath = self.paths['input'] / f"{test_name}.json"
        success = self._atomic_write_json(filepath, test_data)
        if success:
            print(f"📄 Тест сохранен: {filepath}")
        return success
    
    def save_test_results(self, test_name: str, results: Dict[str, Any]) -> bool:
        """
        Сохраняет результаты теста.
        """
        filepath = self.paths['test_results'] / f"{test_name}_results.json"
        success = self._atomic_write_json(filepath, results)
        if success:
            print(f"💾 Результаты теста сохранены: {filepath}")
        return success