"""Tests for the Flask web dashboard (src.webapp)."""

import pytest
import pandas as pd
from pathlib import Path
from tempfile import TemporaryDirectory

from src.webapp import create_app


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
            'PRECIO_TOTAL': [10.0 + (month * 0.5)] * 100,
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
def data_dir(sample_yearly_dataframe):
    """Write sample dataframes to a temporary directory of monthly files."""
    with TemporaryDirectory() as tmpdir:
        for i, df in enumerate(sample_yearly_dataframe, 1):
            df.to_csv(f"{tmpdir}/Datalle {i:02d}25.txt", sep='|', index=False)
        yield tmpdir


@pytest.fixture
def app(data_dir):
    """Create a fully-featured app (forecast + anomalies enabled)."""
    return create_app(data_dir)


@pytest.fixture
def client(app):
    """Flask test client for the full app."""
    return app.test_client()


class TestAppFactory:
    """Test create_app() configuration."""

    def test_create_app_returns_flask_app(self, app):
        """Test app is a Flask instance with expected config."""
        assert app is not None
        assert app.config["EPMAPS_HAS_FORECAST"] is True
        assert app.config["EPMAPS_HAS_ANOMALIES"] is True

    def test_create_app_stores_data_directory(self, app, data_dir):
        """Test data directory is stored in config."""
        assert app.config["EPMAPS_DATA_DIR"] == data_dir

    def test_create_app_without_forecast(self, data_dir):
        """Test app can be created with forecast disabled."""
        app = create_app(data_dir, include_forecast=False)
        assert app.config["EPMAPS_HAS_FORECAST"] is False
        assert app.config["EPMAPS_HAS_ANOMALIES"] is True

    def test_create_app_without_anomalies(self, data_dir):
        """Test app can be created with anomalies disabled."""
        app = create_app(data_dir, include_anomalies=False)
        assert app.config["EPMAPS_HAS_ANOMALIES"] is False


class TestOverviewRoute:
    """Test the / (overview) route."""

    def test_overview_status_200(self, client):
        """Test overview page loads successfully."""
        resp = client.get("/")
        assert resp.status_code == 200

    def test_overview_contains_revenue(self, client):
        """Test overview page shows total revenue."""
        resp = client.get("/")
        assert b"Total Revenue" in resp.data

    def test_overview_contains_chart(self, client):
        """Test overview page embeds a Plotly chart."""
        resp = client.get("/")
        assert b"plotly" in resp.data.lower()

    def test_overview_contains_nav(self, client):
        """Test overview page has navigation links."""
        resp = client.get("/")
        assert b"Overview" in resp.data
        assert b"Categories" in resp.data
        assert b"Forecast" in resp.data
        assert b"Anomalies" in resp.data


class TestCategoriesRoute:
    """Test the /categories route."""

    def test_categories_status_200(self, client):
        """Test categories page loads successfully."""
        resp = client.get("/categories")
        assert resp.status_code == 200

    def test_categories_shows_rubros(self, client):
        """Test categories page shows category codes."""
        resp = client.get("/categories")
        assert b"AG01" in resp.data or b"AL01" in resp.data

    def test_categories_contains_chart(self, client):
        """Test categories page embeds a chart."""
        resp = client.get("/categories")
        assert b"plotly" in resp.data.lower()


class TestForecastRoute:
    """Test the /forecast route."""

    def test_forecast_status_200_when_enabled(self, client):
        """Test forecast page loads when forecaster is available."""
        resp = client.get("/forecast")
        assert resp.status_code == 200

    def test_forecast_status_404_when_disabled(self, data_dir):
        """Test forecast page returns 404 when forecaster is disabled."""
        app = create_app(data_dir, include_forecast=False)
        client = app.test_client()
        resp = client.get("/forecast")
        assert resp.status_code == 404

    def test_forecast_contains_projected_total(self, client):
        """Test forecast page shows projected revenue."""
        resp = client.get("/forecast")
        assert b"Projected Total" in resp.data

    def test_forecast_contains_two_charts(self, client):
        """Test forecast page embeds revenue and price charts."""
        resp = client.get("/forecast")
        # Two Plotly div containers expected (revenue + price)
        assert resp.data.lower().count(b"plotly-graph-div") >= 2


class TestAnomaliesRoute:
    """Test the /anomalies route."""

    def test_anomalies_status_200_when_enabled(self, client):
        """Test anomalies page loads when detector is available."""
        resp = client.get("/anomalies")
        assert resp.status_code == 200

    def test_anomalies_status_404_when_disabled(self, data_dir):
        """Test anomalies page returns 404 when detector is disabled."""
        app = create_app(data_dir, include_anomalies=False)
        client = app.test_client()
        resp = client.get("/anomalies")
        assert resp.status_code == 404

    def test_anomalies_contains_risk_level(self, client):
        """Test anomalies page shows risk level badge."""
        resp = client.get("/anomalies")
        assert b"Risk Level" in resp.data

    def test_anomalies_contains_two_charts(self, client):
        """Test anomalies page embeds heatmap and risk dashboard."""
        resp = client.get("/anomalies")
        assert resp.data.lower().count(b"plotly-graph-div") >= 2


class TestIntegration:
    """Integration tests across the full dashboard."""

    def test_all_routes_reachable(self, client):
        """Test every nav route returns a successful response."""
        for route in ["/", "/categories", "/forecast", "/anomalies"]:
            resp = client.get(route)
            assert resp.status_code == 200, f"{route} failed with {resp.status_code}"

    def test_minimal_app_overview_still_works(self, data_dir):
        """Test overview works even with forecast/anomalies disabled."""
        app = create_app(data_dir, include_forecast=False, include_anomalies=False)
        client = app.test_client()

        resp = client.get("/")
        assert resp.status_code == 200

        resp_cat = client.get("/categories")
        assert resp_cat.status_code == 200
