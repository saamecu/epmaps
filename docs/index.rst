EPMaps Documentation
====================

Welcome to EPMaps! A Python-based data analysis and comparison tool for invoice data.

This project provides tools to read, analyze, and compare large datasets of invoice information across multiple time periods.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   getting_started
   cli_guide
   api/index
   development

Getting Started
===============

Installation
~~~~~~~~~~~~

1. Clone the repository
2. Activate virtual environment: ``source .venv/bin/activate``
3. Install dependencies: ``pip install -r requirements-dev.txt``

Running Tests
~~~~~~~~~~~~~

.. code-block:: bash

   pytest tests/
   pytest tests/ --cov=src  # With coverage report

Building Documentation
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   cd docs
   make html

The built documentation will be in ``docs/_build/html/``

Quick Start
===========

Reading Data
~~~~~~~~~~~~

.. code-block:: python

   from src.data_reader import DataReader

   # Read entire file
   reader = DataReader("datos/Datalle 0125.txt")
   df = reader.read_full()

   # Or read in chunks for large files
   for chunk in reader.read_chunks(chunksize=50000):
       print(f"Processing {len(chunk)} rows...")

File Information
~~~~~~~~~~~~~~~~

.. code-block:: python

   reader = DataReader("datos/Datalle 0125.txt")

   # Get file metadata
   info = reader.get_file_info()
   print(f"File size: {info['size_mb']} MB")

   # Get column names
   columns = reader.get_columns()
   print(f"Columns: {columns}")

Analyzing Data
~~~~~~~~~~~~~~

.. code-block:: python

   from src.analyzer import DataAnalyzer

   # Create analyzer from file
   analyzer = DataAnalyzer.from_file("datos/Datalle 0125.txt")

   # Get summary statistics
   stats = analyzer.get_summary_stats(value_column="PRECIO_TOTAL")
   print(f"Total: ${stats['sum']:.2f}")
   print(f"Average: ${stats['mean']:.2f}")

   # Group by category (rubro)
   by_rubro = analyzer.group_by_column("RUBRO", value_column="PRECIO_TOTAL")
   print(by_rubro)

   # Extract month from invoice
   df_with_month = analyzer.extract_month()

   # Compare periods
   comparison = analyzer.compare_periods("MONTH", "001", "002")
   print(f"Period 1 Total: ${comparison['period1_total']:.2f}")
   print(f"Period 2 Total: ${comparison['period2_total']:.2f}")
   print(f"Change: {comparison['percentage_change']}%")

   # Get top items
   top_rubros = analyzer.top_by_value("RUBRO", n=5)
   print(top_rubros)

API Documentation
==================

.. autosummary::
   :toctree: api

   src.data_reader
