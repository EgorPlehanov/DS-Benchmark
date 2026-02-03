# src/profiling/artifacts/__init__.py
"""
Модуль управления артефактами профилирования.
"""

from .artifact_manager import ArtifactManager
from .metadata_collector import MetadataCollector

__all__ = ['ArtifactManager', 'MetadataCollector']