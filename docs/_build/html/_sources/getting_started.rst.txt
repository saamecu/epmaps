Getting Started
===============

Installation
~~~~~~~~~~~~

Prerequisites
~~~~~~~~~~~~~

- Python 3.10+
- pip

Setup Steps
~~~~~~~~~~~

1. **Clone the repository**

   .. code-block:: bash

      git clone <repository-url>
      cd epmaps

2. **Create and activate virtual environment**

   .. code-block:: bash

      python3 -m venv .venv
      source .venv/bin/activate

3. **Install dependencies**

   For development (includes testing and documentation tools):

   .. code-block:: bash

      pip install -r requirements-dev.txt

   For production only:

   .. code-block:: bash

      pip install -r requirements.txt

Verifying Installation
~~~~~~~~~~~~~~~~~~~~~~

Test that everything is set up correctly:

.. code-block:: bash

   # Run tests
   pytest tests/

   # Check version
   python -c "import pandas; print(pandas.__version__)"

First Steps with EPMaps
~~~~~~~~~~~~~~~~~~~~~~~

Basic Data Reading
^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from src.data_reader import DataReader

   # Initialize reader with your data file
   reader = DataReader("datos/Datalle 0125.txt")

   # Get file information
   info = reader.get_file_info()
   print(f"File: {info['path']}")
   print(f"Size: {info['size_mb']} MB")

   # Get column names
   columns = reader.get_columns()
   print(f"Columns: {columns}")

Reading Full File
^^^^^^^^^^^^^^^^^

.. code-block:: python

   # Read the entire file into memory
   df = reader.read_full()
   print(df.head())
   print(f"Total rows: {len(df)}")

Reading in Chunks (Recommended for Large Files)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   # Process file in chunks to save memory
   for chunk in reader.read_chunks(chunksize=50000):
       print(f"Processing chunk with {len(chunk)} rows")
       # Do your analysis here
       result = chunk.groupby("RUBRO")["PRECIO_TOTAL"].sum()
       print(result)

Working with Data
~~~~~~~~~~~~~~~~~

Once you have data loaded, you can use pandas for analysis:

.. code-block:: python

   import pandas as pd
   from src.data_reader import DataReader

   reader = DataReader("datos/Datalle 0125.txt")
   df = reader.read_full()

   # Basic statistics
   print(df.describe())

   # Group by rubro (category)
   by_rubro = df.groupby("RUBRO")["PRECIO_TOTAL"].sum()
   print(by_rubro)

   # Filter data
   admin_data = df[df["RUBRO"] == "AM01"]
   print(f"Administration charges: {len(admin_data)} rows")

Next Steps
~~~~~~~~~~

- Review :doc:`development` for code style and testing guidelines
- Check :doc:`api/index` for detailed API documentation
- Run existing tests to familiarize yourself with the codebase: ``pytest tests/ -v``

Troubleshooting
~~~~~~~~~~~~~~~

**ModuleNotFoundError: No module named 'pandas'**

Make sure you've activated the virtual environment:

.. code-block:: bash

   source .venv/bin/activate
   pip install -r requirements-dev.txt

**File not found error**

Ensure your data file exists and the path is correct:

.. code-block:: bash

   ls -lh datos/
   python -c "from pathlib import Path; print(Path('datos/Datalle 0125.txt').exists())"
