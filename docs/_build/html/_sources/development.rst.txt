Development Guide
==================

Code Standards
~~~~~~~~~~~~~~

We maintain high code quality standards. All code must:

- Follow PEP 8 style guide
- Have proper type hints
- Include docstrings for public methods
- Pass all tests before merging

Formatting
^^^^^^^^^^

Use black to format code:

.. code-block:: bash

   source .venv/bin/activate
   black src/ tests/

Linting
^^^^^^^

Use pylint to check code quality:

.. code-block:: bash

   pylint src/

Type Checking
^^^^^^^^^^^^^

Use mypy for static type checking:

.. code-block:: bash

   mypy src/

Testing
~~~~~~~

**All new features must include unit tests.**

Writing Tests
^^^^^^^^^^^^^

1. Create test file in ``tests/`` directory
2. Name it ``test_<module_name>.py``
3. Use pytest for testing framework
4. Include fixtures for common test data

Example test structure:

.. code-block:: python

   """Unit tests for my_module."""

   import pytest
   from src.my_module import MyClass

   class TestMyClass:
       """Tests for MyClass."""

       def test_valid_initialization(self):
           """Test successful initialization."""
           obj = MyClass("test_value")
           assert obj.value == "test_value"

       def test_invalid_input_raises_error(self):
           """Test that invalid input raises ValueError."""
           with pytest.raises(ValueError):
               MyClass(None)

Running Tests
^^^^^^^^^^^^^

.. code-block:: bash

   # Run all tests
   pytest tests/

   # Run specific test file
   pytest tests/test_data_reader.py

   # Run with verbose output
   pytest tests/ -v

   # Run with coverage report
   pytest tests/ --cov=src

   # Run only unit tests
   pytest tests/ -m unit

Test Coverage
^^^^^^^^^^^^^

Check test coverage:

.. code-block:: bash

   pytest tests/ --cov=src --cov-report=html

This generates an HTML report in ``htmlcov/index.html``

Documentation
~~~~~~~~~~~~~

Building Documentation
^^^^^^^^^^^^^^^^^^^^^^^

Documentation is built using Sphinx:

.. code-block:: bash

   cd docs/
   make html

The built documentation appears in ``docs/_build/html/``

Writing Docstrings
^^^^^^^^^^^^^^^^^^^

Use Google-style docstrings for all public functions and classes:

.. code-block:: python

   def process_data(file_path: str, chunk_size: int = 1000) -> pd.DataFrame:
       """Process invoice data from file.

       Reads and processes invoice data from the specified file path.
       Large files are processed in chunks to manage memory usage.

       Args:
           file_path: Path to the data file.
           chunk_size: Number of rows per processing chunk. Defaults to 1000.

       Returns:
           Processed DataFrame containing aggregated data.

       Raises:
           FileNotFoundError: If the file does not exist.
           ValueError: If chunk_size is not positive.

       Example:
           >>> df = process_data("datos/Datalle 0125.txt", chunk_size=50000)
           >>> print(len(df))
           1000
       """

Commit Messages
~~~~~~~~~~~~~~~

Follow these guidelines for commit messages:

- Use clear, descriptive messages
- Start with a verb (Add, Fix, Update, Remove, etc.)
- Keep first line under 70 characters
- Include detailed explanation in body if needed
- Never include AI co-author credits

Example:

.. code-block:: text

   Add DataReader class for reading invoice files

   - Supports pipe-delimited text files
   - Implements chunked reading for large files
   - Includes comprehensive error handling

Git Workflow
~~~~~~~~~~~~

1. Create a new branch for your feature
2. Make changes and commit with descriptive messages
3. Write and run tests for all new features
4. Update documentation as needed
5. Push to repository
6. Create pull request with clear description

The ``datos/`` folder is protected:

- All files in ``datos/`` are ignored by ``.gitignore``
- GitHub Actions block any attempts to commit ``datos/`` files
- **Data files will never be committed to the repository**

Project Structure
~~~~~~~~~~~~~~~~~

.. code-block:: text

   epmaps/
   ├── src/                 # Source code
   │   ├── __init__.py
   │   ├── data_reader.py   # Data reading functionality
   │   └── ...
   ├── tests/               # Unit tests
   │   ├── __init__.py
   │   ├── test_data_reader.py
   │   └── ...
   ├── docs/                # Sphinx documentation
   │   ├── conf.py
   │   ├── index.rst
   │   └── ...
   ├── datos/               # Data files (never committed)
   ├── .github/workflows/   # GitHub Actions
   ├── CLAUDE.md            # Development guidance
   ├── README.md
   ├── requirements.txt
   ├── requirements-dev.txt
   ├── pytest.ini
   ├── .coveragerc
   └── ...

Virtual Environment
~~~~~~~~~~~~~~~~~~~~

Always work in the virtual environment:

.. code-block:: bash

   # Activate
   source .venv/bin/activate

   # Deactivate
   deactivate

CLI Development
~~~~~~~~~~~~~~~

The CLI is built using Click. Commands are defined in ``src/cli.py``.

Adding a New Command
^^^^^^^^^^^^^^^^^^^^

1. Define the command function with ``@click.command()`` decorator
2. Add options with ``@click.option()``
3. Add arguments with ``@click.argument()``
4. Use the Rich library for formatted output
5. Add tests in ``tests/test_cli.py``

Example:

.. code-block:: python

   @cli.command()
   @click.argument("file_path", type=click.Path(exists=True))
   @click.option("-o", "--output", type=click.Path())
   def new_command(file_path: str, output: str) -> None:
       """Description of what this command does."""
       try:
           analyzer = DataAnalyzer.from_file(file_path)
           result = analyzer.some_method()
           console.print(result)
       except Exception as e:
           console.print(f"[bold red]Error:[/bold red] {e}")
           raise click.Abort()

Testing CLI Commands
^^^^^^^^^^^^^^^^^^^^

Use the CliRunner to test commands:

.. code-block:: python

   from click.testing import CliRunner
   from src.cli import cli

   def test_my_command(tmp_path):
       """Test my_command."""
       runner = CliRunner()
       result = runner.invoke(cli, ["my-command", "data.txt"])
       assert result.exit_code == 0
       assert "Expected output" in result.output

Common Tasks
~~~~~~~~~~~~

Clean up Python cache files:

.. code-block:: bash

   find . -type d -name __pycache__ -exec rm -r {} +
   find . -type f -name "*.pyc" -delete

Update dependencies:

.. code-block:: bash

   pip install --upgrade -r requirements-dev.txt

Generate test report:

.. code-block:: bash

   pytest tests/ --cov=src --cov-report=term-missing
