"""Tests for PatternAnalyzer extended methods (compare_with, get_summary_stats)."""

import pytest
import pandas as pd

from src.analyzer import DataAnalyzer
from src.pattern_analyzer import PatternAnalyzer


@pytest.fixture
def sample_dataframe():
    """Create sample invoice data for testing."""
    return pd.DataFrame({
        'MANDT': [1] * 100,
        'FACTURA': ['001-01-' + str(i).zfill(6) for i in range(100)],
        'RUBRO': ['AG01'] * 50 + ['AL01'] * 50,
        'SECUENCIA': range(1, 101),
        'BLOQUE_FACTURA': ['A'] * 100,
        'ID_SUBTOTAL': range(1, 101),
        'DESC_RUBRO': ['Agua'] * 50 + ['Alcantarillado'] * 50,
        'PRECIO_UNI': [2.0] * 100,
        'PRECIO_TOTAL': [10.0] * 100,
        'PRECIO_DESC': [0.0] * 100,
        'CANTIDAD': [5.0] * 100,
        'MONTO_IVA': [2.0] * 100,
        'TARIFA': [1] * 100,
        'CONSU_HID': [''] * 100,
        'MONTO_NEG': [''] * 100,
    })


class TestPatternAnalyzerCompareWith:
    """Test PatternAnalyzer.compare_with() method."""

    def test_compare_with_returns_dict(self, sample_dataframe):
        """Test return type."""
        analyzer1 = PatternAnalyzer(DataAnalyzer(sample_dataframe))
        analyzer2 = PatternAnalyzer(DataAnalyzer(sample_dataframe))

        result = analyzer1.compare_with(analyzer2)
        assert isinstance(result, dict)

    def test_compare_with_includes_revenue_comparison(self, sample_dataframe):
        """Test revenue comparison data."""
        analyzer1 = PatternAnalyzer(DataAnalyzer(sample_dataframe))
        analyzer2 = PatternAnalyzer(DataAnalyzer(sample_dataframe))

        result = analyzer1.compare_with(analyzer2)
        assert 'revenue_comparison' in result
        assert 'self' in result['revenue_comparison']
        assert 'other' in result['revenue_comparison']
        assert 'change' in result['revenue_comparison']
        assert 'direction' in result['revenue_comparison']

    def test_compare_with_includes_records_comparison(self, sample_dataframe):
        """Test records comparison data."""
        analyzer1 = PatternAnalyzer(DataAnalyzer(sample_dataframe))
        analyzer2 = PatternAnalyzer(DataAnalyzer(sample_dataframe))

        result = analyzer1.compare_with(analyzer2)
        assert 'records_comparison' in result
        assert 'self' in result['records_comparison']
        assert 'other' in result['records_comparison']
        assert 'change' in result['records_comparison']

    def test_compare_with_includes_price_comparison(self, sample_dataframe):
        """Test price comparison data."""
        analyzer1 = PatternAnalyzer(DataAnalyzer(sample_dataframe))
        analyzer2 = PatternAnalyzer(DataAnalyzer(sample_dataframe))

        result = analyzer1.compare_with(analyzer2)
        assert 'price_comparison' in result
        assert 'self_avg' in result['price_comparison']
        assert 'other_avg' in result['price_comparison']
        assert 'change' in result['price_comparison']

    def test_compare_with_identifies_increase(self, sample_dataframe):
        """Test that increases are correctly identified."""
        df1 = sample_dataframe.copy()
        df1['PRECIO_TOTAL'] = 10.0

        df2 = sample_dataframe.copy()
        df2['PRECIO_TOTAL'] = 15.0  # 50% increase

        analyzer1 = PatternAnalyzer(DataAnalyzer(df1))
        analyzer2 = PatternAnalyzer(DataAnalyzer(df2))

        result = analyzer2.compare_with(analyzer1)
        assert result['revenue_comparison']['change'] == pytest.approx(50.0, abs=0.1)
        assert result['revenue_comparison']['direction'] == '↑'

    def test_compare_with_identifies_decrease(self, sample_dataframe):
        """Test that decreases are correctly identified."""
        df1 = sample_dataframe.copy()
        df1['PRECIO_TOTAL'] = 10.0

        df2 = sample_dataframe.copy()
        df2['PRECIO_TOTAL'] = 5.0  # 50% decrease

        analyzer1 = PatternAnalyzer(DataAnalyzer(df1))
        analyzer2 = PatternAnalyzer(DataAnalyzer(df2))

        result = analyzer2.compare_with(analyzer1)
        assert result['revenue_comparison']['change'] == pytest.approx(-50.0, abs=0.1)
        assert result['revenue_comparison']['direction'] == '↓'

    def test_compare_with_no_change(self, sample_dataframe):
        """Test when both periods are identical."""
        analyzer1 = PatternAnalyzer(DataAnalyzer(sample_dataframe))
        analyzer2 = PatternAnalyzer(DataAnalyzer(sample_dataframe))

        result = analyzer1.compare_with(analyzer2)
        assert result['revenue_comparison']['change'] == pytest.approx(0.0, abs=0.1)

    def test_compare_with_different_record_counts(self, sample_dataframe):
        """Test comparison with different number of records."""
        df1 = sample_dataframe.copy()
        df2 = sample_dataframe.head(50)  # Half the records

        analyzer1 = PatternAnalyzer(DataAnalyzer(df1))
        analyzer2 = PatternAnalyzer(DataAnalyzer(df2))

        result = analyzer1.compare_with(analyzer2)
        # df1 has 100, df2 has 50, so 100% more
        assert result['records_comparison']['change'] == pytest.approx(100.0, abs=0.1)

    def test_compare_with_price_comparison(self, sample_dataframe):
        """Test price comparison calculation."""
        df1 = sample_dataframe.copy()
        df1['PRECIO_TOTAL'] = 10.0

        df2 = sample_dataframe.copy()
        df2['PRECIO_TOTAL'] = 12.0  # df2 is higher

        analyzer1 = PatternAnalyzer(DataAnalyzer(df1))
        analyzer2 = PatternAnalyzer(DataAnalyzer(df2))

        # analyzer1 (10.0) compared with analyzer2 (12.0)
        # Change = (10 - 12) / 12 * 100 = -16.67%
        result = analyzer1.compare_with(analyzer2)
        assert 'price_comparison' in result
        assert result['price_comparison']['change'] == pytest.approx(-16.67, abs=0.1)


class TestPatternAnalyzerGetSummaryStats:
    """Test PatternAnalyzer.get_summary_stats() method."""

    def test_get_summary_stats_returns_dict(self, sample_dataframe):
        """Test return type."""
        analyzer = PatternAnalyzer(DataAnalyzer(sample_dataframe))
        stats = analyzer.get_summary_stats()

        assert isinstance(stats, dict)

    def test_get_summary_stats_includes_records(self, sample_dataframe):
        """Test records count included."""
        analyzer = PatternAnalyzer(DataAnalyzer(sample_dataframe))
        stats = analyzer.get_summary_stats()

        assert 'records' in stats
        assert stats['records'] == 100

    def test_get_summary_stats_includes_invoices(self, sample_dataframe):
        """Test invoice count included."""
        analyzer = PatternAnalyzer(DataAnalyzer(sample_dataframe))
        stats = analyzer.get_summary_stats()

        assert 'invoices' in stats
        assert stats['invoices'] > 0

    def test_get_summary_stats_includes_revenue(self, sample_dataframe):
        """Test revenue calculation."""
        analyzer = PatternAnalyzer(DataAnalyzer(sample_dataframe))
        stats = analyzer.get_summary_stats()

        assert 'revenue' in stats
        expected_revenue = 10.0 * 100  # PRECIO_TOTAL * count
        assert stats['revenue'] == pytest.approx(expected_revenue, abs=0.1)

    def test_get_summary_stats_includes_prices(self, sample_dataframe):
        """Test price statistics."""
        analyzer = PatternAnalyzer(DataAnalyzer(sample_dataframe))
        stats = analyzer.get_summary_stats()

        assert 'avg_price' in stats
        assert 'median_price' in stats
        assert stats['avg_price'] > 0
        assert stats['median_price'] > 0

    def test_get_summary_stats_includes_lines_per_invoice(self, sample_dataframe):
        """Test lines per invoice calculation."""
        analyzer = PatternAnalyzer(DataAnalyzer(sample_dataframe))
        stats = analyzer.get_summary_stats()

        assert 'lines_per_invoice' in stats
        assert stats['lines_per_invoice'] > 0

    def test_get_summary_stats_includes_categories(self, sample_dataframe):
        """Test category count."""
        analyzer = PatternAnalyzer(DataAnalyzer(sample_dataframe))
        stats = analyzer.get_summary_stats()

        assert 'categories' in stats
        assert stats['categories'] == 2  # AG01 and AL01

    def test_get_summary_stats_includes_dominant_category(self, sample_dataframe):
        """Test dominant category identification."""
        analyzer = PatternAnalyzer(DataAnalyzer(sample_dataframe))
        stats = analyzer.get_summary_stats()

        assert 'dominant_category' in stats
        assert stats['dominant_category'] in ['AG01', 'AL01']

    def test_get_summary_stats_all_required_keys(self, sample_dataframe):
        """Test that all expected keys are present."""
        analyzer = PatternAnalyzer(DataAnalyzer(sample_dataframe))
        stats = analyzer.get_summary_stats()

        required_keys = [
            'records',
            'invoices',
            'revenue',
            'avg_price',
            'median_price',
            'lines_per_invoice',
            'categories',
            'dominant_category',
        ]

        for key in required_keys:
            assert key in stats, f"Missing key: {key}"

    def test_get_summary_stats_with_different_data(self):
        """Test with different data configuration."""
        df = pd.DataFrame({
            'MANDT': [1] * 50,
            'FACTURA': ['001-02-' + str(i).zfill(6) for i in range(50)],
            'RUBRO': ['AM01'] * 50,  # Single category
            'SECUENCIA': range(1, 51),
            'BLOQUE_FACTURA': ['A'] * 50,
            'ID_SUBTOTAL': range(1, 51),
            'DESC_RUBRO': ['Admin'] * 50,
            'PRECIO_UNI': [1.5] * 50,
            'PRECIO_TOTAL': [7.5] * 50,
            'PRECIO_DESC': [0.0] * 50,
            'CANTIDAD': [5.0] * 50,
            'MONTO_IVA': [1.5] * 50,
            'TARIFA': [1] * 50,
            'CONSU_HID': [''] * 50,
            'MONTO_NEG': [''] * 50,
        })

        analyzer = PatternAnalyzer(DataAnalyzer(df))
        stats = analyzer.get_summary_stats()

        assert stats['records'] == 50
        assert stats['categories'] == 1  # Only AM01
        assert stats['dominant_category'] == 'AM01'
        assert stats['revenue'] == pytest.approx(375.0, abs=0.1)  # 7.5 * 50


class TestIntegration:
    """Integration tests for extended PatternAnalyzer methods."""

    def test_compare_with_and_summary_stats(self, sample_dataframe):
        """Test using both methods together."""
        df1 = sample_dataframe.copy()
        df1['PRECIO_TOTAL'] = 10.0

        df2 = sample_dataframe.copy()
        df2['PRECIO_TOTAL'] = 12.0

        analyzer1 = PatternAnalyzer(DataAnalyzer(df1))
        analyzer2 = PatternAnalyzer(DataAnalyzer(df2))

        stats1 = analyzer1.get_summary_stats()
        stats2 = analyzer2.get_summary_stats()
        comparison = analyzer1.compare_with(analyzer2)

        # Stats should match comparison
        assert stats1['records'] == comparison['records_comparison']['self']
        assert stats2['records'] == comparison['records_comparison']['other']

    def test_month_to_month_comparison_workflow(self, sample_dataframe):
        """Test realistic month-to-month comparison."""
        # January data
        df_jan = sample_dataframe.copy()
        df_jan['FACTURA'] = df_jan['FACTURA'].str.replace('01', '01')
        df_jan['PRECIO_TOTAL'] = 10.0

        # February data (10% more expensive)
        df_feb = sample_dataframe.copy()
        df_feb['FACTURA'] = df_feb['FACTURA'].str.replace('01', '02')
        df_feb['PRECIO_TOTAL'] = 11.0

        jan = PatternAnalyzer(DataAnalyzer(df_jan))
        feb = PatternAnalyzer(DataAnalyzer(df_feb))

        # Get month summaries
        jan_stats = jan.get_summary_stats()
        feb_stats = feb.get_summary_stats()

        # Compare months
        feb_vs_jan = feb.compare_with(jan)

        assert jan_stats['revenue'] == pytest.approx(1000.0, abs=0.1)
        assert feb_stats['revenue'] == pytest.approx(1100.0, abs=0.1)
        assert feb_vs_jan['revenue_comparison']['change'] == pytest.approx(10.0, abs=0.1)
        assert feb_vs_jan['revenue_comparison']['direction'] == '↑'
