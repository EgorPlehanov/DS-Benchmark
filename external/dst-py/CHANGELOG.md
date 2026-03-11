# Changelog

All notable changes to the Dempster-Shafer package will be documented in this file.

## [Unreleased]

### Added
- Created dedicated tests folder following Python packaging best practices
- Added comprehensive docstrings with paper references for all functions
- Added CHANGELOG.md file to track changes

### Changed
- Restructured project to follow Python packaging best practices with src layout
- Reorganized discounting module to eliminate duplication:
  - Moved classical discounting functions to classical.py
  - Moved basic contextual discounting to contextual.py
  - Moved advanced contextual discounting (from papers) to contextual_advanced.py
- Updated README.md with improved documentation
- Updated pyproject.toml to follow modern Python packaging standards

### Removed
- Removed duplicate implementations of discounting functions
- Removed static test values used just to pass unit tests
