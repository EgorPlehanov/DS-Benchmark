# scripts/list_sessions.py
"""
Утилита для просмотра собранных сессий.
"""

import json
from pathlib import Path
from datetime import datetime

def list_sessions(artifacts_dir: str = "artifacts"):
    """Выводит список всех сессий."""
    base_path = Path(artifacts_dir)
    
    if not base_path.exists():
        print(f"❌ Директория {artifacts_dir} не существует")
        return
    
    sessions = []
    for session_dir in base_path.iterdir():
        if session_dir.is_dir():
            meta_file = session_dir / 'meta.json'
            summary_file = session_dir / 'suite_summary.json'
            
            session_info = {
                'id': session_dir.name,
                'path': str(session_dir),
                'has_meta': meta_file.exists(),
                'has_summary': summary_file.exists(),
                'created': session_dir.name[:8] + ' ' + session_dir.name[9:13] + ':' + session_dir.name[13:15] + ':' + session_dir.name[15:]
            }
            
            # Загружаем метаданные, если есть
            if meta_file.exists():
                try:
                    with open(meta_file, 'r') as f:
                        meta = json.load(f)
                    session_info['adapter'] = meta.get('profiling_runner', {}).get('adapter', 'unknown')
                    session_info['system'] = meta.get('system', {}).get('platform', 'unknown')
                except:
                    session_info['meta_error'] = True
            
            # Загружаем сводку, если есть
            if summary_file.exists():
                try:
                    with open(summary_file, 'r') as f:
                        summary = json.load(f)
                    session_info['tests'] = summary.get('total_tests', 0)
                    session_info['completed'] = summary.get('completed_tests', 0)
                    session_info['duration'] = summary.get('total_execution_time_seconds', 0)
                except:
                    session_info['summary_error'] = True
            
            sessions.append(session_info)
    
    # Сортируем по дате (новые сначала)
    sessions.sort(key=lambda x: x['id'], reverse=True)
    
    print(f"📊 СЕССИИ ПРОФИЛИРОВАНИЯ ({len(sessions)} найдено)")
    print("=" * 100)
    
    for i, session in enumerate(sessions, 1):
        print(f"\n[{i}] {session['id']}")
        print(f"   📅 Создана: {session['created']}")
        
        if 'adapter' in session:
            print(f"   📚 Адаптер: {session['adapter']}")
        
        if 'tests' in session:
            print(f"   🧪 Тестов: {session['tests']} (✅ {session['completed']})")
            print(f"   ⏱️  Время: {session['duration']:.1f}с")
        
        print(f"   📁 Путь: {session['path']}")
        
        if session.get('meta_error'):
            print(f"   ⚠️  Ошибка чтения meta.json")
        if session.get('summary_error'):
            print(f"   ⚠️  Ошибка чтения summary.json")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Просмотр сессий профилирования')
    parser.add_argument('--dir', type=str, default='artifacts',
                       help='Директория с артефактами')
    
    args = parser.parse_args()
    list_sessions(args.dir)