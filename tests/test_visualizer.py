"""Unit tests for the DataVisualizer module."""

import pytest
import tempfile
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go

from src.analyzer import DataAnalyzer
from src.visualizer import DataVisualizer


class TestDataVisualizerInitialization:
    """Tests for DataVisualizer initialization."""

    def test_init_with_analyzer(self, sample_invoice_df):
        """Test initialization with DataAnalyzer."""
        analyzer = DataAnalyzer(sample_invoice_df)
        visualizer = DataVisualizer(analyzer)
        assert isinstance(visualizer, DataVisualizer)
        assert visualizer.analyzer is analyzer

    def test_init_with_non_analyzer(self):
        """Test initialization fails with non-analyzer input."""
        with pytest.raises(TypeError, match="must be a DataAnalyzer instance"):
            DataVisualizer("not an analyzer")

    def test_from_file_creates_visualizer(self, sample_data_file):
        """Test creating visualizer from file."""
        visualizer = DataVisualizer.from_file(sample_data_file)
        assert isinstance(visualizer, DataVisualizer)


class TestBarChart:
    """Tests for bar chart visualization."""

    def test_bar_chart_returns_figure(self, sample_invoice_df):
        """Test that bar chart returns a Plotly Figure."""
        analyzer = DataAnalyzer(sample_invoice_df)
        visualizer = DataVisualizer(analyzer)
        fig = visualizer.bar_chart_by_category()
        assert isinstance(fig, go.Figure)

    def test_bar_chart_has_data(self, sample_invoice_df):
        """Test that bar chart contains data."""
        analyzer = DataAnalyzer(sample_invoice_df)
        visualizer = DataVisualizer(analyzer)
        fig = visualizer.bar_chart_by_category()
        assert len(fig.data) > 0

    def test_bar_chart_with_custom_columns(self, sample_invoice_df):
        """Test bar chart with custom category column."""
        analyzer = DataAnalyzer(sample_invoice_df)
        visualizer = DataVisualizer(analyzer)
        fig = visualizer.bar_chart_by_category(category_column="RUBRO")
        assert isinstance(fig, go.Figure)

    def test_bar_chart_with_title(self, sample_invoice_df):
        """Test bar chart with custom title."""
        analyzer = DataAnalyzer(sample_invoice_df)
        visualizer = DataVisualizer(analyzer)
        title = "Custom Title"
        fig = visualizer.bar_chart_by_category(title=title)
        assert fig.layout.title.text == title

    def test_bar_chart_invalid_category_column(self, sample_invoice_df):
        """Test bar chart with invalid category column."""
        analyzer = DataAnalyzer(sample_invoice_df)
        visualizer = DataVisualizer(analyzer)
        with pytest.raises(ValueError, match="not found"):
            visualizer.bar_chart_by_category(category_column="NONEXISTENT")

    def test_bar_chart_invalid_value_column(self, sample_invoice_df):
        """Test bar chart with invalid value column."""
        analyzer = DataAnalyzer(sample_invoice_df)
        visualizer = DataVisualizer(analyzer)
        with pytest.raises(ValueError, match="not found"):
            visualizer.bar_chart_by_category(value_column="NONEXISTENT")


class TestLineChart:
    """Tests for line chart visualization."""

    def test_line_chart_returns_figure(self, multi_month_df):
        """Test that line chart returns a Plotly Figure."""
        analyzer = DataAnalyzer(multi_month_df)
        visualizer = DataVisualizer(analyzer)
        fig = visualizer.line_chart_trend()
        assert isinstance(fig, go.Figure)

    def test_line_chart_has_data(self, multi_month_df):
        """Test that line chart contains data."""
        analyzer = DataAnalyzer(multi_month_df)
        visualizer = DataVisualizer(analyzer)
        fig = visualizer.line_chart_trend()
        assert len(fig.data) > 0

    def test_line_chart_with_title(self, multi_month_df):
        """Test line chart with custom title."""
        analyzer = DataAnalyzer(multi_month_df)
        visualizer = DataVisualizer(analyzer)
        title = "Custom Trend Title"
        fig = visualizer.line_chart_trend(title=title)
        assert fig.layout.title.text == title

    def test_line_chart_invalid_period_column(self, multi_month_df):
        """Test line chart with invalid period column."""
        analyzer = DataAnalyzer(multi_month_df)
        visualizer = DataVisualizer(analyzer)
        with pytest.raises(ValueError, match="not found"):
            visualizer.line_chart_trend(period_column="NONEXISTENT")


class TestPieChart:
    """Tests for pie chart visualization."""

    def test_pie_chart_returns_figure(self, sample_invoice_df):
        """Test that pie chart returns a Plotly Figure."""
        analyzer = DataAnalyzer(sample_invoice_df)
        visualizer = DataVisualizer(analyzer)
        fig = visualizer.pie_chart_distribution()
        assert isinstance(fig, go.Figure)

    def test_pie_chart_has_data(self, sample_invoice_df):
        """Test that pie chart contains data."""
        analyzer = DataAnalyzer(sample_invoice_df)
        visualizer = DataVisualizer(analyzer)
        fig = visualizer.pie_chart_distribution()
        assert len(fig.data) > 0

    def test_pie_chart_with_title(self, sample_invoice_df):
        """Test pie chart with custom title."""
        analyzer = DataAnalyzer(sample_invoice_df)
        visualizer = DataVisualizer(analyzer)
        title = "Custom Pie Title"
        fig = visualizer.pie_chart_distribution(title=title)
        assert fig.layout.title.text == title

    def test_pie_chart_invalid_column(self, sample_invoice_df):
        """Test pie chart with invalid column."""
        analyzer = DataAnalyzer(sample_invoice_df)
        visualizer = DataVisualizer(analyzer)
        with pytest.raises(ValueError, match="not found"):
            visualizer.pie_chart_distribution(category_column="NONEXISTENT")


class TestComparisonChart:
    """Tests for comparison chart visualization."""

    def test_comparison_chart_returns_figure(self, multi_month_df):
        """Test that comparison chart returns a Plotly Figure."""
        analyzer = DataAnalyzer(multi_month_df)
        visualizer = DataVisualizer(analyzer)
        fig = visualizer.comparison_bar_chart(period1="001", period2="002")
        assert isinstance(fig, go.Figure)

    def test_comparison_chart_has_data(self, multi_month_df):
        """Test that comparison chart contains data."""
        analyzer = DataAnalyzer(multi_month_df)
        visualizer = DataVisualizer(analyzer)
        fig = visualizer.comparison_bar_chart(period1="001", period2="002")
        assert len(fig.data) > 0

    def test_comparison_chart_missing_periods(self, multi_month_df):
        """Test comparison chart without specifying periods."""
        analyzer = DataAnalyzer(multi_month_df)
        visualizer = DataVisualizer(analyzer)
        with pytest.raises(ValueError, match="must be specified"):
            visualizer.comparison_bar_chart()

    def test_comparison_chart_invalid_period(self, multi_month_df):
        """Test comparison chart with invalid period."""
        analyzer = DataAnalyzer(multi_month_df)
        visualizer = DataVisualizer(analyzer)
        with pytest.raises(ValueError, match="No data found"):
            visualizer.comparison_bar_chart(period1="001", period2="999")


class TestSummaryDashboard:
    """Tests for summary dashboard."""

    def test_dashboard_returns_figure(self, sample_invoice_df):
        """Test that dashboard returns a Plotly Figure."""
        analyzer = DataAnalyzer(sample_invoice_df)
        visualizer = DataVisualizer(analyzer)
        fig = visualizer.summary_dashboard()
        assert isinstance(fig, go.Figure)

    def test_dashboard_has_subplots(self, sample_invoice_df):
        """Test that dashboard has multiple subplots."""
        analyzer = DataAnalyzer(sample_invoice_df)
        visualizer = DataVisualizer(analyzer)
        fig = visualizer.summary_dashboard()
        # Dashboard should have 4 subplots minimum
        assert len(fig.data) >= 2


class TestChartSaving:
    """Tests for saving charts."""

    def test_save_chart(self, sample_invoice_df):
        """Test saving chart to HTML file."""
        analyzer = DataAnalyzer(sample_invoice_df)
        visualizer = DataVisualizer(analyzer)
        fig = visualizer.bar_chart_by_category()

        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
            temp_path = f.name

        try:
            visualizer.save_chart(fig, temp_path)
            assert Path(temp_path).exists()
            content = Path(temp_path).read_text()
            assert "plotly" in content.lower()
        finally:
            Path(temp_path).unlink()


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
        "PRECIO_TOTAL": [10.0, 10.0, 10.0, 20.0, 20.0],
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
        "RUBRO": ["AM01", "OT01", "AM01", "OT01", "AM01"],
        "PRECIO_TOTAL": [10.0, 20.0, 15.0, 25.0, 20.0],
        "CANTIDAD": [1.0] * 5,
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_data_file():
    """Create a temporary sample data file."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    ) as f:
        f.write("MANDT|FACTURA|RUBRO|CANTIDAD|PRECIO_TOTAL|MONTH\n")
        f.write("300|001-012-057647312|AM01|1.0|10.00|1\n")
        f.write("300|001-012-057647313|AM01|1.0|10.00|1\n")
        f.write("300|001-012-057647314|OT01|1.0|20.00|1\n")
        temp_path = f.name

    yield temp_path
    Path(temp_path).unlink()
