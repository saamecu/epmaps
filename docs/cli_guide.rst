CLI Guide
=========

The EPMaps command-line interface provides powerful tools for analyzing invoice data.

Installation
~~~~~~~~~~~~

The CLI is available after installing the project:

.. code-block:: bash

   pip install -r requirements.txt
   python main.py --help

Quick Reference
~~~~~~~~~~~~~~~

.. code-block:: bash

   # File information
   python main.py info datos/Datalle\ 0125.txt

   # Summary statistics
   python main.py stats datos/Datalle\ 0125.txt

   # Group by category
   python main.py group datos/Datalle\ 0125.txt -g RUBRO

   # Top items
   python main.py top datos/Datalle\ 0125.txt -n 10

   # Compare periods
   python main.py compare datos/Datalle\ 0125.txt 001 002

   # Generate report
   python main.py report datos/Datalle\ 0125.txt -o report.txt

Commands
~~~~~~~~

info
^^^^

Display information about a data file.

.. code-block:: bash

   python main.py info <FILE_PATH>

Shows:

- File path
- File size in MB
- Number of columns
- Column names

Example:

.. code-block:: bash

   python main.py info datos/Datalle\ 0125.txt

stats
^^^^^

Display summary statistics for a data file.

.. code-block:: bash

   python main.py stats <FILE_PATH> [OPTIONS]

Options:

- ``-c, --column`` TEXT: Column to calculate statistics on (default: PRECIO_TOTAL)

Shows:

- Count: Number of values
- Sum: Total of all values
- Mean: Average value
- Median: Middle value
- Std: Standard deviation
- Min: Minimum value
- Max: Maximum value

Example:

.. code-block:: bash

   python main.py stats datos/Datalle\ 0125.txt -c PRECIO_TOTAL

group
^^^^^

Group and aggregate data by a column.

.. code-block:: bash

   python main.py group <FILE_PATH> [OPTIONS]

Options:

- ``-g, --group-by`` TEXT: Column to group by (default: RUBRO)
- ``-v, --value-column`` TEXT: Column with values to aggregate (default: PRECIO_TOTAL)
- ``-a, --aggregation`` [sum|mean|count|min|max]: Aggregation method (default: sum)

Shows a table with grouped results.

Example:

.. code-block:: bash

   python main.py group datos/Datalle\ 0125.txt -g RUBRO -a sum

top
^^^

Display top N items by value.

.. code-block:: bash

   python main.py top <FILE_PATH> [OPTIONS]

Options:

- ``-g, --group-by`` TEXT: Column to group by (default: RUBRO)
- ``-v, --value-column`` TEXT: Column with values to sort by (default: PRECIO_TOTAL)
- ``-n, --number`` INTEGER: Number of top items (default: 10)

Shows a ranked table with top N items.

Example:

.. code-block:: bash

   python main.py top datos/Datalle\ 0125.txt -n 15 -g RUBRO

compare
^^^^^^^

Compare data between two periods.

.. code-block:: bash

   python main.py compare <FILE_PATH> <PERIOD1> <PERIOD2> [OPTIONS]

Options:

- ``-p, --period-column`` TEXT: Period column name (default: MONTH)
- ``-v, --value-column`` TEXT: Column to compare (default: PRECIO_TOTAL)

Shows:

- Total for each period
- Absolute difference
- Percentage change

Example:

.. code-block:: bash

   # Compare months 001 and 002
   python main.py compare datos/Datalle\ 0125.txt 001 002

   # Compare using custom period column
   python main.py compare datos/Datalle\ 0125.txt Q1 Q2 -p QUARTER

report
^^^^^^

Generate a comprehensive analysis report.

.. code-block:: bash

   python main.py report <FILE_PATH> [OPTIONS]

Options:

- ``-o, --output`` PATH: Output file path (optional)

Includes:

- File metadata
- Summary statistics
- Top 5 categories by total

If no output file is specified, the report is printed to console.

Example:

.. code-block:: bash

   # Print report to console
   python main.py report datos/Datalle\ 0125.txt

   # Save report to file
   python main.py report datos/Datalle\ 0125.txt -o report.txt

Global Options
~~~~~~~~~~~~~~

.. code-block:: bash

   python main.py --version    # Show version
   python main.py --help       # Show help
   python main.py <command> --help  # Help for specific command

Examples
~~~~~~~~

Analyze Invoice Data
^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   # 1. Check file info
   python main.py info datos/Datalle\ 0125.txt

   # 2. Get statistics
   python main.py stats datos/Datalle\ 0125.txt

   # 3. See breakdown by rubro (category)
   python main.py group datos/Datalle\ 0125.txt -g RUBRO -a sum

   # 4. Get top 5 categories
   python main.py top datos/Datalle\ 0125.txt -n 5

Compare Months
^^^^^^^^^^^^^^

.. code-block:: bash

   # Compare month 001 vs 002
   python main.py compare datos/Datalle\ 0125.txt 001 002

   # Check which month had more sales in a specific category
   python main.py group datos/Datalle\ 0125.txt -g RUBRO -v CANTIDAD -a sum

Generate Reports
^^^^^^^^^^^^^^^^

.. code-block:: bash

   # Create summary report and save to file
   python main.py report datos/Datalle\ 0125.txt -o analysis_report.txt

   # Create report with custom aggregation
   python main.py top datos/Datalle\ 0125.txt -n 20 > top_items.txt

Troubleshooting
~~~~~~~~~~~~~~~

File Not Found
^^^^^^^^^^^^^^

**Error:** ``Error: Invalid value for 'FILE_PATH': Path 'datos/file.txt' does not exist.``

**Solution:** Make sure the file path is correct and the file exists:

.. code-block:: bash

   ls -la datos/

Column Not Found
^^^^^^^^^^^^^^^^

**Error:** ``Error: Column 'NONEXISTENT' not found``

**Solution:** Use the ``info`` command to see available columns:

.. code-block:: bash

   python main.py info datos/Datalle\ 0125.txt

Invalid Period
^^^^^^^^^^^^^^

**Error:** ``Error: No data found for MONTH=999``

**Solution:** Use the ``compare`` command with periods that exist in the data:

.. code-block:: bash

   # First check what periods exist
   python main.py group datos/Datalle\ 0125.txt -g MONTH -a count

Tips
~~~~

- Use ``| grep`` or ``> filename.txt`` to save command output
- Use ``-c`` flag in stats to analyze different columns
- Use different aggregations (sum, mean, count) for different insights
- Save reports with ``-o`` flag for documentation and sharing
- Use ``--help`` on any command for detailed information
