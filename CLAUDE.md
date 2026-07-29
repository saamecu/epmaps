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
├── datos/              # Data directory (ignored by git)
├── .venv/              # Python virtual environment
├── src/                # Source code (to be created)
├── tests/              # Test files (to be created)
├── CLAUDE.md          # This file
├── README.md
├── LICENSE
├── .gitignore
└── requirements.txt    # Python dependencies (to be created)
```

## Data Management

- **Location**: All project data goes in the `datos/` directory
- **Git**: The entire `datos/` folder is ignored by `.gitignore` to prevent large files from being committed
- **Structure**: Organize data files by type or experiment within `datos/` subdirectories as the project grows

## Common Development Tasks

### Running Python Code

```bash
python script.py
```

### Running Tests (when added)

```bash
pytest tests/
pytest tests/test_specific.py  # Run specific test file
```

### Code Quality (when tools are added)

```bash
black src/             # Format code
pylint src/            # Lint code
mypy src/              # Type checking
```

## Next Steps

As the project grows, add:
- `requirements.txt` with dependencies
- `requirements-dev.txt` with development tools (pytest, black, etc.)
- Source code in `src/` directory
- Tests in `tests/` directory
- Documentation in README.md
