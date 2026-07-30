"""Flask application factory for the EPMaps web dashboard.

Loads yearly data and precomputes every metric, forecast, and chart
exactly once at startup, then serves them from memory. YearlyAnalyzer's
methods scan the full multi-million-row dataset on every call, so
computing them per-request would make each page load take as long as
the initial load — everything expensive happens once in create_app().
"""

from typing import Optional
import plotly.graph_objects as go
from flask import Flask, render_template

from src.yearly_analyzer import YearlyAnalyzer
from src.forecaster import Forecaster
from src.anomaly_detector import AnomalyDetector
from src.forecast_visualizer import ForecastVisualizer


def _chart_html(fig: go.Figure) -> str:
    """Render a Plotly figure to an embeddable HTML div.

    Assumes plotly.js is already loaded once in the page via CDN
    (see base.html), so the library itself is not re-embedded per chart.

    Args:
        fig: Plotly figure to render.

    Returns:
        HTML string containing just the chart div and its data/script.
    """
    return fig.to_html(full_html=False, include_plotlyjs=False, config={"responsive": True})


def _category_bar_chart(top_categories: dict) -> go.Figure:
    """Build a bar chart of total revenue by category.

    Args:
        top_categories: Output of YearlyAnalyzer.top_categories_yearly().

    Returns:
        Plotly figure.
    """
    rubros = list(top_categories.keys())
    revenues = [data["total_revenue"] for data in top_categories.values()]

    fig = go.Figure(
        data=go.Bar(
            x=rubros,
            y=revenues,
            marker=dict(color="#3b82f6"),
            text=[f"${r:,.0f}" for r in revenues],
            textposition="outside",
        )
    )
    fig.update_layout(
        title="Total Revenue by Category",
        xaxis_title="Category",
        yaxis_title="Revenue ($)",
        template="plotly_white",
        height=450,
    )
    return fig


def create_app(
    data_directory: str,
    include_forecast: bool = True,
    include_anomalies: bool = True,
) -> Flask:
    """Create and configure the EPMaps Flask dashboard app.

    Loads all monthly data files and precomputes every metric, forecast,
    and chart once at startup so that individual page requests are cheap
    dict/template lookups instead of full dataset scans.

    Args:
        data_directory: Path to directory with monthly Datalle*.txt files.
        include_forecast: Load Forecaster and enable the Forecast tab.
        include_anomalies: Load AnomalyDetector and enable the Anomalies tab.

    Returns:
        Configured Flask application.
    """
    app = Flask(__name__)

    analyzer = YearlyAnalyzer.from_directory(data_directory)
    forecaster: Optional[Forecaster] = Forecaster(analyzer) if include_forecast else None
    detector: Optional[AnomalyDetector] = AnomalyDetector(analyzer) if include_anomalies else None

    # Fallback instances so ForecastVisualizer (which requires both) can
    # still render pages when only one of the two modules was requested.
    # Built once, alongside everything else below — never per-request.
    fallback_forecaster = forecaster or Forecaster(analyzer)
    fallback_detector = detector or AnomalyDetector(analyzer)

    # --- Precompute everything expensive, exactly once ---------------
    metrics = analyzer.yearly_metrics()
    top_categories_10 = analyzer.top_categories_yearly(top_n=10)
    top_categories_5 = analyzer.top_categories_yearly(top_n=5)
    categories_chart = _chart_html(_category_bar_chart(top_categories_10))

    trend_chart = _chart_html(
        ForecastVisualizer(fallback_forecaster, fallback_detector).plot_trend_analysis()
    )

    forecast_data = None
    if forecaster is not None:
        viz = ForecastVisualizer(forecaster, fallback_detector)
        forecast_data = {
            "summary": forecaster.get_forecast_summary(periods=3),
            "trends": forecaster.get_trends(),
            "revenue_chart": _chart_html(viz.plot_revenue_forecast(periods=3)),
            "price_chart": _chart_html(viz.plot_price_forecast(periods=3)),
        }

    anomaly_data = None
    if detector is not None:
        viz = ForecastVisualizer(fallback_forecaster, detector)
        anomaly_data = {
            "report": detector.get_overall_anomaly_report(),
            "alerts": detector.get_alerts(severity="all"),
            "heatmap_chart": _chart_html(viz.plot_anomalies_heatmap()),
            "risk_chart": _chart_html(viz.plot_risk_dashboard()),
        }
    # -------------------------------------------------------------------

    app.config["EPMAPS_DATA_DIR"] = data_directory
    app.config["EPMAPS_HAS_FORECAST"] = forecaster is not None
    app.config["EPMAPS_HAS_ANOMALIES"] = detector is not None

    @app.context_processor
    def inject_nav_flags():
        return {
            "has_forecast": app.config["EPMAPS_HAS_FORECAST"],
            "has_anomalies": app.config["EPMAPS_HAS_ANOMALIES"],
        }

    @app.route("/")
    def overview():
        return render_template(
            "overview.html",
            active_page="overview",
            metrics=metrics,
            top_categories=top_categories_5,
            trend_chart=trend_chart,
            data_directory=data_directory,
        )

    @app.route("/categories")
    def categories():
        return render_template(
            "categories.html",
            active_page="categories",
            categories=top_categories_10,
            chart=categories_chart,
        )

    @app.route("/forecast")
    def forecast():
        if forecast_data is None:
            return render_template("disabled.html", active_page="forecast", feature="Forecast"), 404

        return render_template(
            "forecast.html",
            active_page="forecast",
            summary=forecast_data["summary"],
            trends=forecast_data["trends"],
            revenue_chart=forecast_data["revenue_chart"],
            price_chart=forecast_data["price_chart"],
        )

    @app.route("/anomalies")
    def anomalies():
        if anomaly_data is None:
            return render_template("disabled.html", active_page="anomalies", feature="Anomalies"), 404

        return render_template(
            "anomalies.html",
            active_page="anomalies",
            report=anomaly_data["report"],
            alerts=anomaly_data["alerts"],
            heatmap_chart=anomaly_data["heatmap_chart"],
            risk_chart=anomaly_data["risk_chart"],
        )

    return app
