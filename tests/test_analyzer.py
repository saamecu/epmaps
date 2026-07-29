"""Unit tests for the DataAnalyzer module."""

import pytest
import pandas as pd
import numpy as np

from src.analyzer import DataAnalyzer


class TestDataAnalyzerInitialization:
    """Tests for DataAnalyzer initialization."""

    def test_init_with_valid_dataframe(self, sample_invoice_df):
        """Test successful initialization with valid DataFrame."""
        analyzer = DataAnalyzer(sample_invoice_df)
        assert isinstance(analyzer.df, pd.DataFrame)
        assert len(analyzer.df) > 0

    def test_init_with_empty_dataframe(self):
        """Test initialization fails with empty DataFrame."""
        empty_df = pd.DataFrame()
        with pytest.raises(ValueError, match="cannot be empty"):
            DataAnalyzer(empty_df)

    def test_init_with_non_dataframe(self):
        """Test initialization fails with non-DataFrame input."""
        with pytest.raises(TypeError, match="must be a pandas DataFrame"):
            DataAnalyzer([1, 2, 3])

    def test_init_makes_copy(self, sample_invoice_df):
        """Test that initialization creates a copy of the DataFrame."""
        analyzer = DataAnalyzer(sample_invoice_df)
        sample_invoice_df.loc[0, "PRECIO_TOTAL"] = 999
        assert analyzer.df.loc[0, "PRECIO_TOTAL"] != 999


class TestDataAnalyzerFromFile:
    """Tests for creating analyzer from file."""

    def test_from_file_creates_analyzer(self, sample_data_file):
        """Test creating analyzer from file."""
        analyzer = DataAnalyzer.from_file(sample_data_file)
        assert isinstance(analyzer, DataAnalyzer)
        assert len(analyzer.df) > 0

    def test_from_file_with_chunksize(self, sample_data_file):
        """Test creating analyzer from file with chunks."""
        analyzer = DataAnalyzer.from_file(sample_data_file, chunksize=2)
        assert isinstance(analyzer, DataAnalyzer)
        assert len(analyzer.df) > 0


class TestExtractMonth:
    """Tests for month extraction."""

    def test_extract_month_creates_column(self, sample_invoice_df):
        """Test that extract_month creates MONTH column."""
        analyzer = DataAnalyzer(sample_invoice_df)
        result = analyzer.extract_month()
        assert "MONTH" in result.columns

    def test_extract_month_extracts_correctly(self, sample_invoice_df):
        """Test that month is extracted correctly from invoice."""
        analyzer = DataAnalyzer(sample_invoice_df)
        result = analyzer.extract_month()
        # Expected format: 001-012-057647312 -> month is "012"
        expected_month = "012"
        assert result["MONTH"].iloc[0] == expected_month

    def test_extract_month_invalid_column(self, sample_invoice_df):
        """Test extract_month with invalid column."""
        analyzer = DataAnalyzer(sample_invoice_df)
        with pytest.raises(ValueError, match="not found"):
            analyzer.extract_month(factura_column="NONEXISTENT")

    def test_extract_month_returns_dataframe(self, sample_invoice_df):
        """Test that extract_month returns a DataFrame."""
        analyzer = DataAnalyzer(sample_invoice_df)
        result = analyzer.extract_month()
        assert isinstance(result, pd.DataFrame)


class TestSummaryStats:
    """Tests for summary statistics."""

    def test_get_summary_stats_returns_dict(self, sample_invoice_df):
        """Test that summary stats returns a dictionary."""
        analyzer = DataAnalyzer(sample_invoice_df)
        stats = analyzer.get_summary_stats()
        assert isinstance(stats, dict)

    def test_summary_stats_has_required_keys(self, sample_invoice_df):
        """Test that summary stats includes all required keys."""
        analyzer = DataAnalyzer(sample_invoice_df)
        stats = analyzer.get_summary_stats()
        required_keys = ["count", "sum", "mean", "median", "std", "min", "max"]
        assert all(key in stats for key in required_keys)

    def test_summary_stats_values_are_numeric(self, sample_invoice_df):
        """Test that all stat values are numeric."""
        analyzer = DataAnalyzer(sample_invoice_df)
        stats = analyzer.get_summary_stats()
        for key, value in stats.items():
            if key != "count":
                assert isinstance(value, (int, float))

    def test_summary_stats_invalid_column(self, sample_invoice_df):
        """Test summary stats with invalid column."""
        analyzer = DataAnalyzer(sample_invoice_df)
        with pytest.raises(ValueError, match="not found"):
            analyzer.get_summary_stats(value_column="NONEXISTENT")


class TestGroupByColumn:
    """Tests for grouping data."""

    def test_group_by_returns_dataframe(self, sample_invoice_df):
        """Test that group_by returns a DataFrame."""
        analyzer = DataAnalyzer(sample_invoice_df)
        result = analyzer.group_by_column("RUBRO")
        assert isinstance(result, pd.DataFrame)

    def test_group_by_has_expected_columns(self, sample_invoice_df):
        """Test that result has GROUP and aggregation columns."""
        analyzer = DataAnalyzer(sample_invoice_df)
        result = analyzer.group_by_column("RUBRO")
        assert "RUBRO" in result.columns
        assert "SUM" in result.columns

    def test_group_by_different_aggregations(self, sample_invoice_df):
        """Test group_by with different aggregation types."""
        analyzer = DataAnalyzer(sample_invoice_df)
        for agg in ["sum", "mean", "count", "min", "max"]:
            result = analyzer.group_by_column("RUBRO", aggregation=agg)
            assert isinstance(result, pd.DataFrame)
            assert len(result) > 0

    def test_group_by_invalid_aggregation(self, sample_invoice_df):
        """Test group_by with invalid aggregation."""
        analyzer = DataAnalyzer(sample_invoice_df)
        with pytest.raises(ValueError, match="Invalid aggregation"):
            analyzer.group_by_column("RUBRO", aggregation="invalid")

    def test_group_by_invalid_group_column(self, sample_invoice_df):
        """Test group_by with invalid group column."""
        analyzer = DataAnalyzer(sample_invoice_df)
        with pytest.raises(ValueError, match="not found"):
            analyzer.group_by_column("NONEXISTENT")

    def test_group_by_invalid_value_column(self, sample_invoice_df):
        """Test group_by with invalid value column."""
        analyzer = DataAnalyzer(sample_invoice_df)
        with pytest.raises(ValueError, match="not found"):
            analyzer.group_by_column("RUBRO", value_column="NONEXISTENT")


class TestComparePeriods:
    """Tests for period comparison."""

    def test_compare_periods_returns_dict(self, multi_month_df):
        """Test that compare_periods returns a dictionary."""
        analyzer = DataAnalyzer(multi_month_df)
        result = analyzer.compare_periods("MONTH", "001", "002")
        assert isinstance(result, dict)

    def test_compare_periods_has_required_keys(self, multi_month_df):
        """Test that comparison includes required keys."""
        analyzer = DataAnalyzer(multi_month_df)
        result = analyzer.compare_periods("MONTH", "001", "002")
        required_keys = [
            "period1",
            "period2",
            "period1_total",
            "period2_total",
            "difference",
            "percentage_change",
        ]
        assert all(key in result for key in required_keys)

    def test_compare_periods_calculates_correctly(self, multi_month_df):
        """Test that period comparison calculations are correct."""
        analyzer = DataAnalyzer(multi_month_df)
        result = analyzer.compare_periods("MONTH", "001", "002")
        # Month 001: 2 rows * 10 = 20, Month 002: 3 rows * 10 = 30
        assert result["period1_total"] == 20.0
        assert result["period2_total"] == 30.0
        assert result["difference"] == 10.0
        assert result["percentage_change"] == 50.0

    def test_compare_periods_invalid_column(self, multi_month_df):
        """Test compare_periods with invalid column."""
        analyzer = DataAnalyzer(multi_month_df)
        with pytest.raises(ValueError, match="not found"):
            analyzer.compare_periods("NONEXISTENT", "001", "002")

    def test_compare_periods_missing_period(self, multi_month_df):
        """Test compare_periods with missing period."""
        analyzer = DataAnalyzer(multi_month_df)
        with pytest.raises(ValueError, match="No data found"):
            analyzer.compare_periods("MONTH", "001", "999")


class TestTopByValue:
    """Tests for top values."""

    def test_top_by_value_returns_dataframe(self, sample_invoice_df):
        """Test that top_by_value returns a DataFrame."""
        analyzer = DataAnalyzer(sample_invoice_df)
        result = analyzer.top_by_value("RUBRO", n=5)
        assert isinstance(result, pd.DataFrame)

    def test_top_by_value_respects_n(self, sample_invoice_df):
        """Test that top_by_value returns at most n results."""
        analyzer = DataAnalyzer(sample_invoice_df)
        result = analyzer.top_by_value("RUBRO", n=3)
        assert len(result) <= 3

    def test_top_by_value_sorted_descending(self, sample_invoice_df):
        """Test that results are sorted descending by value."""
        analyzer = DataAnalyzer(sample_invoice_df)
        result = analyzer.top_by_value("RUBRO", n=5)
        values = result["SUM"].values
        assert all(values[i] >= values[i + 1] for i in range(len(values) - 1))

    def test_top_by_value_invalid_n(self, sample_invoice_df):
        """Test top_by_value with invalid n."""
        analyzer = DataAnalyzer(sample_invoice_df)
        with pytest.raises(ValueError, match="must be positive"):
            analyzer.top_by_value("RUBRO", n=0)


class TestUtilityMethods:
    """Tests for utility methods."""

    def test_get_row_count(self, sample_invoice_df):
        """Test get_row_count returns correct count."""
        analyzer = DataAnalyzer(sample_invoice_df)
        assert analyzer.get_row_count() == len(sample_invoice_df)

    def test_get_columns(self, sample_invoice_df):
        """Test get_columns returns all columns."""
        analyzer = DataAnalyzer(sample_invoice_df)
        columns = analyzer.get_columns()
        assert isinstance(columns, list)
        assert len(columns) > 0
        assert all(col in columns for col in sample_invoice_df.columns)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_invoice_df():
    """Create a sample invoice DataFrame for testing."""
    data = {
        "MANDT": [300] * 5,
        "FACTURA": [
            "001-012-057647312",
            "001-012-057647313",
            "001-012-057647314",
            "001-012-057647320",
            "001-012-057647321",
        ],
        "RUBRO": ["AM01"] * 3 + ["OT01"] * 2,
        "PRECIO_TOTAL": [2.10, 2.10, 2.10, 5.00, 5.00],
        "CANTIDAD": [1.0] * 5,
    }
    return pd.DataFrame(data)


@pytest.fixture
def multi_month_df():
    """Create a DataFrame with multiple months for comparison tests."""
    data = {
        "MONTH": ["001", "001", "002", "002", "002"],
        "FACTURA": [
            "001-001-001",
            "001-001-002",
            "001-002-001",
            "001-002-002",
            "001-002-003",
        ],
        "RUBRO": ["AM01"] * 5,
        "PRECIO_TOTAL": [10.0] * 5,
        "CANTIDAD": [1.0] * 5,
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_data_file():
    """Create a temporary sample data file."""
    import tempfile
    from pathlib import Path

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    ) as f:
        f.write("MANDT|FACTURA|RUBRO|CANTIDAD|PRECIO_TOTAL\n")
        f.write("300|001-012-057647312|AM01|1.0|2.10\n")
        f.write("300|001-012-057647313|AM01|1.0|2.10\n")
        f.write("300|001-012-057647314|OT01|1.0|5.00\n")
        temp_path = f.name

    yield temp_path
    Path(temp_path).unlink()
