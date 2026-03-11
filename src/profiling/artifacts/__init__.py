# src/profiling/artifacts/__init__.py
"""
Пакет для управления артефактами профилирования.
"""

from .artifact_manager import ArtifactManager, create_artifact_manager, get_latest_artifact_dir
from .test_metadata import TestMetadata, collect_test_metadata, collect_basic_metadata
from .structure import create_artifact_structure, validate_artifact_structure, get_artifact_summary

__all__ = [
    'ArtifactManager',
    'create_artifact_manager',
    'get_latest_artifact_dir',
    'TestMetadata',
    'collect_test_metadata',
    'collect_basic_metadata',
    'create_artifact_structure',
    'validate_artifact_structure',
    'get_artifact_summary'
]