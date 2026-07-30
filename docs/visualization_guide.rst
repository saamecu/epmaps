Data Visualization Guide
========================

EPMaps provides interactive visualizations using Plotly for analyzing invoice data.

Overview
~~~~~~~~

The visualization module creates professional, interactive HTML charts that can be:

- Displayed in your browser
- Saved as standalone HTML files
- Embedded in reports
- Used for presentations

All charts are interactive with hover information, zoom, and export options.

Chart Types
~~~~~~~~~~~

Bar Chart
^^^^^^^^^

Shows the top N items grouped by category.

**Command:**

.. code-block:: bash

   python main.py chart-bar <FILE_PATH> [OPTIONS]

**Options:**

- ``-g, --group-by``: Column to group by (default: RUBRO)
- ``-v, --value-column``: Column with values (default: PRECIO_TOTAL)
- ``-n, --number``: Number of top items (default: 10)
- ``-o, --output``: Save chart to HTML file

**Example:**

.. code-block:: bash

   # Show top 10 rubros in browser
   python main.py chart-bar datos/Datalle\ 0125.txt

   # Save top 5 to file
   python main.py chart-bar datos/Datalle\ 0125.txt -n 5 -o top_rubros.html

   # Group by different column
   python main.py chart-bar datos/Datalle\ 0125.txt -g MANDT -v CANTIDAD

Line Chart
^^^^^^^^^^

Shows trends over time/periods.

**Command:**

.. code-block:: bash

   python main.py chart-trend <FILE_PATH> [OPTIONS]

**Options:**

- ``-p, --period-column``: Period column (default: MONTH)
- ``-v, --value-column``: Column with values (default: PRECIO_TOTAL)
- ``-o, --output``: Save chart to HTML file

**Example:**

.. code-block:: bash

   # Show trend by month
   python main.py chart-trend datos/Datalle\ 0125.txt

   # Save trend to file
   python main.py chart-trend datos/Datalle\ 0125.txt -o trend.html

   # View trend by quantity
   python main.py chart-trend datos/Datalle\ 0125.txt -v CANTIDAD

Pie Chart
^^^^^^^^^

Shows distribution by category.

**Command:**

.. code-block:: bash

   python main.py chart-pie <FILE_PATH> [OPTIONS]

**Options:**

- ``-g, --group-by``: Column to group by (default: RUBRO)
- ``-v, --value-column``: Column with values (default: PRECIO_TOTAL)
- ``-o, --output``: Save chart to HTML file

**Example:**

.. code-block:: bash

   # Show distribution by rubro
   python main.py chart-pie datos/Datalle\ 0125.txt

   # Save with custom grouping
   python main.py chart-pie datos/Datalle\ 0125.txt -g MANDT -o distribution.html

Comparison Chart
^^^^^^^^^^^^^^^^

Compares values between two periods side by side.

**Command:**

.. code-block:: bash

   python main.py chart-compare <FILE_PATH> <PERIOD1> <PERIOD2> [OPTIONS]

**Options:**

- ``-p, --period-column``: Period column (default: MONTH)
- ``-g, --group-by``: Category column (default: RUBRO)
- ``-v, --value-column``: Values to compare (default: PRECIO_TOTAL)
- ``-o, --output``: Save chart to HTML file

**Example:**

.. code-block:: bash

   # Compare months 001 vs 002
   python main.py chart-compare datos/Datalle\ 0125.txt 001 002

   # Save comparison to file
   python main.py chart-compare datos/Datalle\ 0125.txt 001 002 -o comparison.html

   # Compare by quantity
   python main.py chart-compare datos/Datalle\ 0125.txt 001 002 -v CANTIDAD

Summary Dashboard
^^^^^^^^^^^^^^^^^

Comprehensive dashboard with multiple visualizations.

**Command:**

.. code-block:: bash

   python main.py dashboard <FILE_PATH> [OPTIONS]

**Options:**

- ``-v, --value-column``: Column with values (default: PRECIO_TOTAL)
- ``-o, --output``: Save dashboard to HTML file

**Includes:**

- Top 5 items bar chart
- Total vs Average comparison
- Distribution pie chart
- Key statistics indicator

**Example:**

.. code-block:: bash

   # Open dashboard in browser
   python main.py dashboard datos/Datalle\ 0125.txt

   # Save dashboard to file
   python main.py dashboard datos/Datalle\ 0125.txt -o dashboard.html

Python API
~~~~~~~~~~

You can also create visualizations programmatically:

.. code-block:: python

   from src.visualizer import DataVisualizer

   # Create visualizer
   visualizer = DataVisualizer.from_file("datos/Datalle 0125.txt")

   # Generate bar chart
   fig = visualizer.bar_chart_by_category(
       category_column="RUBRO",
       value_column="PRECIO_TOTAL",
       n_top=10
   )

   # Save to file
   visualizer.save_chart(fig, "chart.html")

   # Display in browser
   visualizer.show_chart(fig)

Advanced Examples
~~~~~~~~~~~~~~~~~

Create and Save Multiple Charts
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   # Top items
   python main.py chart-bar datos/Datalle\ 0125.txt -n 15 -o top_15.html

   # Trends
   python main.py chart-trend datos/Datalle\ 0125.txt -o trends.html

   # Distribution
   python main.py chart-pie datos/Datalle\ 0125.txt -o distribution.html

   # Comparison
   python main.py chart-compare datos/Datalle\ 0125.txt 001 002 -o comparison.html

   # Dashboard
   python main.py dashboard datos/Datalle\ 0125.txt -o summary.html

Compare Different Categories
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   # Compare by quantity instead of price
   python main.py chart-compare datos/Datalle\ 0125.txt 001 002 -v CANTIDAD

   # Trend of costs
   python main.py chart-trend datos/Datalle\ 0125.txt -v PRECIO_TOTAL

   # Distribution by branch
   python main.py chart-pie datos/Datalle\ 0125.txt -g MANDT

Analyze Different Periods
^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   # Compare quarters (if data available)
   python main.py chart-compare datos/Datalle\ 0125.txt Q1 Q2 -p QUARTER

   # Year-over-year comparison
   python main.py chart-compare datos/Datalle\ 0125.txt 2025 2026 -p YEAR

Tips & Tricks
~~~~~~~~~~~~~

Interactive Features
^^^^^^^^^^^^^^^^^^^^

All Plotly charts include:

- **Hover**: Mouse over to see exact values
- **Zoom**: Click and drag to zoom in on specific areas
- **Pan**: Hold shift and drag to move around
- **Legend**: Click legend items to hide/show series
- **Download**: Camera icon in top right saves as PNG
- **Export**: Save data as CSV via chart menu

Browser Tips
^^^^^^^^^^^^

- Open charts in Chrome or Firefox for best results
- Charts work offline (no internet required after saved)
- Combine multiple charts for presentations
- Use browser print-to-PDF for archiving

Report Generation
^^^^^^^^^^^^^^^^^

Combine charts with data in reports:

.. code-block:: bash

   # Create all charts
   python main.py chart-bar datos/Datalle\ 0125.txt -n 10 -o top_10.html
   python main.py chart-trend datos/Datalle\ 0125.txt -o trend.html
   python main.py chart-pie datos/Datalle\ 0125.txt -o distribution.html
   python main.py report datos/Datalle\ 0125.txt -o summary_report.txt

   # Open all files in browser
   open top_10.html trend.html distribution.html summary_report.txt

Performance Notes
~~~~~~~~~~~~~~~~~

- Large datasets (>1M rows) may take time to load
- Use filtering/chunking for faster processing
- Consider grouping by higher levels (e.g., by month instead of day)
- Charts are stored locally and don't require server resources

Troubleshooting
~~~~~~~~~~~~~~~

Chart Not Displaying
^^^^^^^^^^^^^^^^^^^^

- Ensure you have the latest Plotly version: ``pip install --upgrade plotly``
- Check browser console for errors (F12 in most browsers)
- Try a different browser
- Verify file path and data format are correct

Chart Looks Wrong
^^^^^^^^^^^^^^^^^

- Check column names are correct with ``python main.py info``
- Ensure value column contains numeric data
- Try specifying explicit value and category columns

Memory Issues
^^^^^^^^^^^^^

- Use chart commands on subsets of data
- Process large files with chunking
- Save charts instead of displaying (uses less memory)

Missing Data in Chart
^^^^^^^^^^^^^^^^^^^^

- Filter data before visualizing
- Check for null values: ``python main.py stats``
- Ensure date/period format is consistent
