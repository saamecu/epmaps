# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**epmaps** is a Python-based project for data analysis and mapping. The project is in early development stages.

## Setup

### Activate Virtual Environment

```bash
source .venv/bin/activate
```

### Install Dependencies

When a `requirements.txt` is created, install with:

```bash
pip install -r requirements.txt
```

For development dependencies:

```bash
pip install -r requirements-dev.txt
```

## Project Structure

```
epmaps/
├── datos/                 # Data directory (ignored by git, protected by GitHub Action)
├── .venv/                 # Python virtual environment
├── .github/workflows/     # GitHub Actions (CI/CD)
├── src/                   # Source code
├── tests/                 # Unit and integration tests
├── CLAUDE.md              # This file
├── README.md
├── LICENSE
├── .gitignore             # Git exclusions
├── .coveragerc            # Test coverage configuration
├── pytest.ini             # Pytest configuration
├── requirements.txt       # Production dependencies
└── requirements-dev.txt   # Development dependencies
```

## Data Management

- **Location**: All project data goes in the `datos/` directory
- **Git**: The entire `datos/` folder is ignored by `.gitignore` to prevent large files from being committed
- **Structure**: Organize data files by type or experiment within `datos/` subdirectories as the project grows

## Common Development Tasks

### Activate Environment
```bash
source .venv/bin/activate
```

### Running Tests
```bash
pytest                              # Run all tests
pytest tests/                       # Run tests from directory
pytest tests/test_analyzer.py       # Run specific test file
pytest tests/ -v                    # Verbose output
pytest tests/ --cov=src             # With coverage report
pytest tests/ -m unit               # Run only unit tests
```

### Code Quality

```bash
black src/ tests/       # Format code
pylint src/             # Lint code
mypy src/               # Type checking
```

## Testing Guidelines

- **Create tests for every new feature** (required)
- Tests go in `tests/` directory with naming pattern: `test_<module>.py`
- Use pytest markers for organization: `@pytest.mark.unit`, `@pytest.mark.integration`
- Coverage goal: Maintain high test coverage for all new code
- Test files follow same structure as source: `src/analyzer.py` → `tests/test_analyzer.py`

## Data Management

- **Location**: All project data goes in the `datos/` directory
- **Git Protection**: 
  - `.gitignore` prevents local commits
  - GitHub Action (`protect-data-folder.yml`) blocks any push attempts
  - **The `datos/` folder will NEVER be committed to cloud**
- **Structure**: Organize data files by type or experiment within `datos/` subdirectories
