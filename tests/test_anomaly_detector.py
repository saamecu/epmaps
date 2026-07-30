"""Tests for AnomalyDetector - anomaly detection and alerting."""

import pytest
import pandas as pd
import numpy as np

from src.analyzer import DataAnalyzer
from src.anomaly_detector import AnomalyDetector


@pytest.fixture
def sample_yearly_dataframe():
    """Create 12 months of sample invoice data with anomalies."""
    dfs = []
    for month in range(1, 13):
        # Normal month
        revenue = 10.0 + (month * 0.5)

        # Inject anomaly in July (month 07)
        if month == 7:
            revenue = 5.0  # Sudden drop - anomaly

        df = pd.DataFrame({
            'MANDT': [1] * 100,
            'FACTURA': [f'001-{month:02d}-' + str(i).zfill(6) for i in range(100)],
            'RUBRO': ['AG01'] * 60 + ['AL01'] * 40,
            'SECUENCIA': range(1, 101),
            'BLOQUE_FACTURA': ['A'] * 100,
            'ID_SUBTOTAL': range(1, 101),
            'DESC_RUBRO': ['Agua'] * 60 + ['Alcantarillado'] * 40,
            'PRECIO_UNI': [2.0] * 100,
            'PRECIO_TOTAL': [revenue] * 100,
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
def detector(sample_yearly_dataframe):
    """Create AnomalyDetector with 12 months of data."""
    from src.yearly_analyzer import YearlyAnalyzer

    month_data = {
        str(i).zfill(2): DataAnalyzer(df)
        for i, df in enumerate(sample_yearly_dataframe, 1)
    }

    yearly = YearlyAnalyzer(month_data)
    return AnomalyDetector(yearly, z_threshold=2.0)


class TestAnomalyDetectorInit:
    """Test AnomalyDetector initialization."""

    def test_init_with_yearly_analyzer(self, detector):
        """Test initialization with YearlyAnalyzer."""
        assert detector.analyzer is not None
        assert detector.z_threshold == 2.0

    def test_init_custom_threshold(self, sample_yearly_dataframe):
        """Test initialization with custom threshold."""
        from src.yearly_analyzer import YearlyAnalyzer

        month_data = {
            str(i).zfill(2): DataAnalyzer(df)
            for i, df in enumerate(sample_yearly_dataframe, 1)
        }

        yearly = YearlyAnalyzer(month_data)
        detector = AnomalyDetector(yearly, z_threshold=1.5)

        assert detector.z_threshold == 1.5

    def test_init_invalid_type(self):
        """Test initialization with invalid type."""
        with pytest.raises(TypeError):
            AnomalyDetector("invalid")


class TestRevenueAnomalies:
    """Test revenue anomaly detection."""

    def test_detect_revenue_anomalies_returns_dict(self, detector):
        """Test return type."""
        result = detector.detect_revenue_anomalies()
        assert isinstance(result, dict)

    def test_revenue_anomalies_has_fields(self, detector):
        """Test result has required fields."""
        result = detector.detect_revenue_anomalies()

        assert 'method' in result
        assert 'threshold' in result
        assert 'mean' in result
        assert 'std' in result
        assert 'anomalies' in result
        assert 'anomaly_count' in result

    def test_revenue_anomalies_detected(self, detector):
        """Test that anomalies are detected."""
        result = detector.detect_revenue_anomalies()

        # Our sample data has July with anomaly
        assert result['anomaly_count'] > 0

    def test_revenue_anomaly_structure(self, detector):
        """Test anomaly entries have correct structure."""
        result = detector.detect_revenue_anomalies()

        for month, anom in result['anomalies'].items():
            assert 'revenue' in anom
            assert 'z_score' in anom
            assert 'severity' in anom
            assert 'anomaly' in anom


class TestPriceAnomalies:
    """Test price anomaly detection."""

    def test_detect_price_anomalies_returns_dict(self, detector):
        """Test return type."""
        result = detector.detect_price_anomalies()
        assert isinstance(result, dict)

    def test_price_anomalies_fields(self, detector):
        """Test required fields."""
        result = detector.detect_price_anomalies()

        assert 'method' in result
        assert 'mean' in result
        assert 'std' in result
        assert 'anomalies' in result


class TestVolumeAnomalies:
    """Test volume anomaly detection."""

    def test_detect_volume_anomalies_returns_dict(self, detector):
        """Test return type."""
        result = detector.detect_volume_anomalies()
        assert isinstance(result, dict)

    def test_volume_anomalies_fields(self, detector):
        """Test required fields."""
        result = detector.detect_volume_anomalies()

        assert 'mean' in result
        assert 'std' in result
        assert 'anomalies' in result


class TestCategoryAnomalies:
    """Test category anomaly detection."""

    def test_detect_category_anomalies_returns_dict(self, detector):
        """Test return type."""
        result = detector.detect_category_anomalies()
        assert isinstance(result, dict)

    def test_category_anomalies_fields(self, detector):
        """Test required fields."""
        result = detector.detect_category_anomalies()

        assert 'method' in result
        assert 'categories_with_anomalies' in result
        assert 'anomalies' in result


class TestMultivariateAnomalies:
    """Test multivariate anomaly detection."""

    def test_detect_multivariate_anomalies_returns_dict(self, detector):
        """Test return type."""
        result = detector.detect_multivariate_anomalies()
        assert isinstance(result, dict)

    def test_multivariate_anomalies_fields(self, detector):
        """Test required fields."""
        result = detector.detect_multivariate_anomalies()

        assert 'method' in result
        assert 'contamination' in result
        assert 'anomalies' in result
        assert 'anomaly_count' in result


class TestOverallAnomalyReport:
    """Test comprehensive anomaly report."""

    def test_overall_report_returns_dict(self, detector):
        """Test return type."""
        report = detector.get_overall_anomaly_report()
        assert isinstance(report, dict)

    def test_overall_report_fields(self, detector):
        """Test report has all required fields."""
        report = detector.get_overall_anomaly_report()

        assert 'total_anomalies_detected' in report
        assert 'risk_score' in report
        assert 'risk_level' in report
        assert 'revenue_anomalies' in report
        assert 'price_anomalies' in report
        assert 'volume_anomalies' in report
        assert 'category_anomalies' in report
        assert 'multivariate_anomalies' in report
        assert 'summary' in report

    def test_risk_score_range(self, detector):
        """Test risk score is between 0 and 100."""
        report = detector.get_overall_anomaly_report()

        assert 0 <= report['risk_score'] <= 100

    def test_risk_level_valid(self, detector):
        """Test risk level is valid."""
        report = detector.get_overall_anomaly_report()

        assert report['risk_level'] in ['low', 'medium', 'high']

    def test_summary_structure(self, detector):
        """Test summary has correct structure."""
        report = detector.get_overall_anomaly_report()

        assert 'high_severity_months' in report['summary']
        assert 'affected_categories' in report['summary']


class TestAlerts:
    """Test alert generation."""

    def test_get_alerts_returns_list(self, detector):
        """Test return type."""
        alerts = detector.get_alerts(severity="high")
        assert isinstance(alerts, list)

    def test_alert_structure(self, detector):
        """Test alert entries have correct structure."""
        alerts = detector.get_alerts(severity="high")

        for alert in alerts:
            assert 'type' in alert
            assert 'severity' in alert
            assert 'message' in alert

    def test_alerts_severity_filtering(self, detector):
        """Test severity filtering works."""
        high_alerts = detector.get_alerts(severity="high")
        all_alerts = detector.get_alerts(severity="all")

        # High alerts should be subset of all alerts
        assert len(high_alerts) <= len(all_alerts)

    def test_alert_types_valid(self, detector):
        """Test alert types are valid."""
        alerts = detector.get_alerts(severity="all")

        valid_types = {"revenue", "price", "category"}
        for alert in alerts:
            assert alert["type"] in valid_types


class TestThresholdVariations:
    """Test detector behavior with different thresholds."""

    def test_low_threshold_more_anomalies(self, sample_yearly_dataframe):
        """Test that lower threshold detects more anomalies."""
        from src.yearly_analyzer import YearlyAnalyzer

        month_data = {
            str(i).zfill(2): DataAnalyzer(df)
            for i, df in enumerate(sample_yearly_dataframe, 1)
        }

        yearly = YearlyAnalyzer(month_data)

        detector_high = AnomalyDetector(yearly, z_threshold=3.0)
        detector_low = AnomalyDetector(yearly, z_threshold=1.0)

        high_count = detector_high.get_overall_anomaly_report()['total_anomalies_detected']
        low_count = detector_low.get_overall_anomaly_report()['total_anomalies_detected']

        # Lower threshold should detect more or equal anomalies
        assert low_count >= high_count


class TestEdgeCases:
    """Test edge cases."""

    def test_constant_revenue(self):
        """Test detection with constant revenue (no variation)."""
        from src.yearly_analyzer import YearlyAnalyzer

        dfs = []
        for month in range(1, 13):
            df = pd.DataFrame({
                'MANDT': [1] * 100,
                'FACTURA': [f'001-{month:02d}-' + str(i).zfill(6) for i in range(100)],
                'RUBRO': ['AG01'] * 100,
                'SECUENCIA': range(1, 101),
                'BLOQUE_FACTURA': ['A'] * 100,
                'ID_SUBTOTAL': range(1, 101),
                'DESC_RUBRO': ['Agua'] * 100,
                'PRECIO_UNI': [2.0] * 100,
                'PRECIO_TOTAL': [10.0] * 100,  # Constant
                'PRECIO_DESC': [0.0] * 100,
                'CANTIDAD': [5.0] * 100,
                'MONTO_IVA': [2.0] * 100,
                'TARIFA': [1] * 100,
                'CONSU_HID': [''] * 100,
                'MONTO_NEG': [''] * 100,
            })
            dfs.append(df)

        month_data = {
            str(i).zfill(2): DataAnalyzer(df)
            for i, df in enumerate(dfs, 1)
        }

        yearly = YearlyAnalyzer(month_data)
        detector = AnomalyDetector(yearly)

        report = detector.get_overall_anomaly_report()
        # With constant data, should detect no anomalies
        assert report['anomaly_count'] == 0 or report['risk_level'] == 'low'
