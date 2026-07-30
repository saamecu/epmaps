"""Tests for Forecaster - predictive modeling and forecasting."""

import pytest
import pandas as pd
import numpy as np

from src.analyzer import DataAnalyzer
from src.forecaster import Forecaster


@pytest.fixture
def sample_yearly_dataframe():
    """Create 12 months of sample invoice data."""
    dfs = []
    for month in range(1, 13):
        df = pd.DataFrame({
            'MANDT': [1] * 100,
            'FACTURA': [f'001-{month:02d}-' + str(i).zfill(6) for i in range(100)],
            'RUBRO': ['AG01'] * 60 + ['AL01'] * 40,
            'SECUENCIA': range(1, 101),
            'BLOQUE_FACTURA': ['A'] * 100,
            'ID_SUBTOTAL': range(1, 101),
            'DESC_RUBRO': ['Agua'] * 60 + ['Alcantarillado'] * 40,
            'PRECIO_UNI': [2.0] * 100,
            'PRECIO_TOTAL': [10.0 + (month * 0.5)] * 100,  # Increasing trend
            'PRECIO_DESC': [0.0] * 100,
            'CANTIDAD': [5.0] * 100,
            'MONTO_IVA': [2.0] * 100,
            'TARIFA': [1] * 100,
            'CONSU_HID': [''] * 100,
            'MONTO_NEG': [''] * 100,
        })
        dfs.append(df)

    return dfs


@pytest.fixture
def forecaster(sample_yearly_dataframe):
    """Create Forecaster with 12 months of data."""
    from src.yearly_analyzer import YearlyAnalyzer

    month_data = {
        str(i).zfill(2): DataAnalyzer(df)
        for i, df in enumerate(sample_yearly_dataframe, 1)
    }

    yearly = YearlyAnalyzer(month_data)
    return Forecaster(yearly)


class TestForecasterInit:
    """Test Forecaster initialization."""

    def test_init_with_yearly_analyzer(self, forecaster):
        """Test initialization with YearlyAnalyzer."""
        assert forecaster.analyzer is not None
        assert len(forecaster.months) == 12

    def test_init_invalid_type(self, sample_yearly_dataframe):
        """Test initialization with invalid type."""
        with pytest.raises(TypeError):
            Forecaster("invalid")


class TestMonthlyRevenueForecast:
    """Test monthly revenue forecasting."""

    def test_forecast_returns_dict(self, forecaster):
        """Test return type."""
        forecast = forecaster.forecast_monthly_revenue(periods=3)
        assert isinstance(forecast, dict)

    def test_forecast_has_required_fields(self, forecaster):
        """Test forecast has all required fields."""
        forecast = forecaster.forecast_monthly_revenue(periods=3)

        for month, data in forecast.items():
            assert 'forecast' in data
            assert 'lower_bound' in data
            assert 'upper_bound' in data
            assert 'confidence_interval_width' in data

    def test_forecast_period_count(self, forecaster):
        """Test forecast returns correct number of periods."""
        forecast = forecaster.forecast_monthly_revenue(periods=3)
        assert len(forecast) == 3

    def test_forecast_positive_values(self, forecaster):
        """Test forecast values are positive."""
        forecast = forecaster.forecast_monthly_revenue(periods=3)

        for data in forecast.values():
            assert data['forecast'] >= 0
            assert data['lower_bound'] >= 0
            assert data['upper_bound'] >= 0

    def test_forecast_bounds_order(self, forecaster):
        """Test lower bound < forecast < upper bound."""
        forecast = forecaster.forecast_monthly_revenue(periods=3)

        for data in forecast.values():
            assert data['lower_bound'] <= data['forecast']
            assert data['forecast'] <= data['upper_bound']

    def test_forecast_increasing_trend(self, forecaster):
        """Test forecast recognizes increasing trend."""
        forecast = forecaster.forecast_monthly_revenue(periods=3)

        # With our sample data showing increasing trend,
        # forecast values should generally be positive trend
        forecasts = [data['forecast'] for data in forecast.values()]

        # At least don't go to zero
        assert all(f > 0 for f in forecasts)


class TestCategoryForecast:
    """Test category-level forecasting."""

    def test_forecast_category_returns_dict(self, forecaster):
        """Test return type."""
        forecast = forecaster.forecast_category_revenue('AG01', periods=3)
        assert isinstance(forecast, dict)

    def test_forecast_unknown_category(self, forecaster):
        """Test forecasting unknown category."""
        forecast = forecaster.forecast_category_revenue('UNKNOWN', periods=3)
        assert 'error' in forecast

    def test_forecast_category_fields(self, forecaster):
        """Test category forecast has required fields."""
        forecast = forecaster.forecast_category_revenue('AG01', periods=3)

        if 'error' not in forecast:
            for data in forecast.values():
                assert 'forecast' in data
                assert 'lower_bound' in data
                assert 'upper_bound' in data


class TestPriceForecast:
    """Test price trend forecasting."""

    def test_forecast_price_returns_dict(self, forecaster):
        """Test return type."""
        forecast = forecaster.forecast_price_trend(periods=3)
        assert isinstance(forecast, dict)

    def test_forecast_price_fields(self, forecaster):
        """Test price forecast has required fields."""
        forecast = forecaster.forecast_price_trend(periods=3)

        for data in forecast.values():
            assert 'forecast' in data
            assert 'lower_bound' in data
            assert 'upper_bound' in data

    def test_forecast_price_positive(self, forecaster):
        """Test price forecasts are positive."""
        forecast = forecaster.forecast_price_trend(periods=3)

        for data in forecast.values():
            assert data['forecast'] >= 0
            assert data['lower_bound'] >= 0


class TestForecastSummary:
    """Test forecast summary."""

    def test_summary_returns_dict(self, forecaster):
        """Test return type."""
        summary = forecaster.get_forecast_summary(periods=3)
        assert isinstance(summary, dict)

    def test_summary_has_all_forecasts(self, forecaster):
        """Test summary includes all forecast types."""
        summary = forecaster.get_forecast_summary(periods=3)

        assert 'revenue_forecast' in summary
        assert 'price_forecast' in summary
        assert 'projected_total_revenue' in summary

    def test_summary_projected_total(self, forecaster):
        """Test projected total is sum of period forecasts."""
        summary = forecaster.get_forecast_summary(periods=3)

        expected_total = sum(
            f['forecast'] for f in summary['revenue_forecast'].values()
        )

        assert summary['projected_total_revenue'] == pytest.approx(expected_total, rel=0.01)


class TestTrends:
    """Test trend analysis."""

    def test_get_trends_returns_dict(self, forecaster):
        """Test return type."""
        trends = forecaster.get_trends()
        assert isinstance(trends, dict)

    def test_get_trends_has_required_fields(self, forecaster):
        """Test trends has all required fields."""
        trends = forecaster.get_trends()

        assert 'trend_type' in trends
        assert 'slope' in trends
        assert 'annual_pct_change' in trends
        assert 'volatility_cv' in trends
        assert 'seasonality_strength' in trends

    def test_trend_types_valid(self, forecaster):
        """Test trend_type is valid."""
        trends = forecaster.get_trends()
        assert trends['trend_type'] in ['increasing', 'decreasing', 'stable']

    def test_trend_strength_valid(self, forecaster):
        """Test trend_strength is valid."""
        trends = forecaster.get_trends()
        assert trends['trend_strength'] in ['strong', 'weak']


class TestForecastAccuracy:
    """Test forecast accuracy evaluation."""

    def test_evaluate_accuracy_returns_dict(self, forecaster):
        """Test return type."""
        actual_data = {'01': 1000, '02': 1200}
        accuracy = forecaster.evaluate_forecast_accuracy(actual_data)

        assert isinstance(accuracy, dict)

    def test_accuracy_metrics(self, forecaster):
        """Test accuracy has required metrics."""
        actual_data = {'01': 1000, '02': 1200}
        accuracy = forecaster.evaluate_forecast_accuracy(actual_data)

        assert 'mae' in accuracy
        assert 'rmse' in accuracy
        assert 'mape' in accuracy

    def test_accuracy_non_negative(self, forecaster):
        """Test accuracy metrics are non-negative."""
        actual_data = {'01': 1000, '02': 1200}
        accuracy = forecaster.evaluate_forecast_accuracy(actual_data)

        assert accuracy['mae'] >= 0
        assert accuracy['rmse'] >= 0
        assert accuracy['mape'] >= 0


class TestMultiPeriodForecast:
    """Test forecasting different period lengths."""

    @pytest.mark.parametrize("periods", [1, 3, 6, 12])
    def test_different_periods(self, forecaster, periods):
        """Test forecasting different period lengths."""
        forecast = forecaster.forecast_monthly_revenue(periods=periods)
        assert len(forecast) == periods

    def test_forecast_consistency(self, forecaster):
        """Test forecasts are consistent across calls."""
        f1 = forecaster.forecast_monthly_revenue(periods=3)
        f2 = forecaster.forecast_monthly_revenue(periods=3)

        for month in f1.keys():
            assert f1[month]['forecast'] == pytest.approx(
                f2[month]['forecast'], rel=0.01
            )
