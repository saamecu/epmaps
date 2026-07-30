"""Visualization module for forecasts and anomalies using Plotly."""

from typing import Dict, Optional
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

from src.forecaster import Forecaster
from src.anomaly_detector import AnomalyDetector


class ForecastVisualizer:
    """Creates interactive visualizations for forecasts and anomalies."""

    def __init__(self, forecaster: Forecaster, anomaly_detector: AnomalyDetector) -> None:
        """Initialize ForecastVisualizer.

        Args:
            forecaster: Forecaster instance with predictions.
            anomaly_detector: AnomalyDetector instance with anomalies.
        """
        self.forecaster = forecaster
        self.detector = anomaly_detector

    def plot_revenue_forecast(self, periods: int = 3) -> go.Figure:
        """Create revenue forecast chart with confidence intervals.

        Args:
            periods: Number of periods to forecast.

        Returns:
            Plotly figure with revenue forecast.
        """
        forecast = self.forecaster.forecast_monthly_revenue(periods)
        historical_metrics = self.forecaster.monthly_metrics

        # Historical data
        months = list(self.forecaster.months)
        hist_revenues = [historical_metrics[m]['revenue'] for m in months]

        # Forecast data
        forecast_months = list(forecast.keys())
        forecast_values = [forecast[m]['forecast'] for m in forecast_months]
        lower_bounds = [forecast[m]['lower_bound'] for m in forecast_months]
        upper_bounds = [forecast[m]['upper_bound'] for m in forecast_months]

        # Create figure
        fig = go.Figure()

        # Historical data
        fig.add_trace(go.Scatter(
            x=months,
            y=hist_revenues,
            mode='lines+markers',
            name='Historical',
            line=dict(color='#3b82f6', width=3),
            marker=dict(size=8),
        ))

        # Forecast
        fig.add_trace(go.Scatter(
            x=forecast_months,
            y=forecast_values,
            mode='lines+markers',
            name='Forecast',
            line=dict(color='#10b981', width=3, dash='dash'),
            marker=dict(size=8),
        ))

        # Confidence interval
        fig.add_trace(go.Scatter(
            x=forecast_months + forecast_months[::-1],
            y=upper_bounds + lower_bounds[::-1],
            fill='toself',
            fillcolor='rgba(16, 185, 129, 0.2)',
            line=dict(color='rgba(16, 185, 129, 0)'),
            name='95% Confidence',
            showlegend=True,
        ))

        fig.update_layout(
            title='Revenue Forecast - Q1 2026',
            xaxis_title='Month',
            yaxis_title='Revenue ($)',
            hovermode='x unified',
            template='plotly_white',
            height=500,
            font=dict(size=12),
        )

        return fig

    def plot_anomalies_heatmap(self) -> go.Figure:
        """Create anomaly detection heatmap.

        Returns:
            Plotly figure with anomaly heatmap.
        """
        report = self.detector.get_overall_anomaly_report()

        months = self.forecaster.months
        revenue_anom = report['revenue_anomalies']['anomalies']
        price_anom = report['price_anomalies']['anomalies']
        volume_anom = report['volume_anomalies']['anomalies']

        # Create matrix for heatmap
        anomaly_types = ['Revenue', 'Price', 'Volume']
        data = []

        for month in months:
            row = [
                1 if month in revenue_anom and revenue_anom[month]['anomaly'] else 0,
                1 if month in price_anom and price_anom[month]['anomaly'] else 0,
                1 if month in volume_anom and volume_anom[month]['anomaly'] else 0,
            ]
            data.append(row)

        fig = go.Figure(data=go.Heatmap(
            z=data,
            x=anomaly_types,
            y=months,
            colorscale='RdYlGn_r',
            colorbar=dict(title='Anomaly<br>Detected'),
        ))

        fig.update_layout(
            title='Anomaly Detection Heatmap - 2025',
            xaxis_title='Anomaly Type',
            yaxis_title='Month',
            height=400,
            font=dict(size=12),
        )

        return fig

    def plot_price_forecast(self, periods: int = 3) -> go.Figure:
        """Create price forecast chart.

        Args:
            periods: Number of periods to forecast.

        Returns:
            Plotly figure with price forecast.
        """
        forecast = self.forecaster.forecast_price_trend(periods)
        price_data = self.forecaster.analyzer.price_evolution()

        months = list(self.forecaster.months)
        hist_prices = [price_data[m]['avg'] for m in months]

        forecast_months = list(forecast.keys())
        forecast_prices = [forecast[m]['forecast'] for m in forecast_months]
        lower = [forecast[m]['lower_bound'] for m in forecast_months]
        upper = [forecast[m]['upper_bound'] for m in forecast_months]

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=months,
            y=hist_prices,
            mode='lines+markers',
            name='Historical Avg Price',
            line=dict(color='#3b82f6', width=3),
        ))

        fig.add_trace(go.Scatter(
            x=forecast_months,
            y=forecast_prices,
            mode='lines+markers',
            name='Price Forecast',
            line=dict(color='#06b6d4', width=3, dash='dash'),
        ))

        fig.add_trace(go.Scatter(
            x=forecast_months + forecast_months[::-1],
            y=upper + lower[::-1],
            fill='toself',
            fillcolor='rgba(6, 182, 212, 0.2)',
            line=dict(color='rgba(6, 182, 212, 0)'),
            name='95% CI',
        ))

        fig.update_layout(
            title='Price Trend & Forecast - Q1 2026',
            xaxis_title='Month',
            yaxis_title='Average Price ($)',
            hovermode='x unified',
            template='plotly_white',
            height=500,
        )

        return fig

    def plot_trend_analysis(self) -> go.Figure:
        """Create trend analysis chart.

        Returns:
            Plotly figure with trend analysis.
        """
        trends = self.forecaster.get_trends()
        metrics = self.forecaster.monthly_metrics

        months = list(self.forecaster.months)
        revenues = [metrics[m]['revenue'] for m in months]

        # Calculate trend line
        x_numeric = list(range(len(months)))
        z = [trends['slope'] * x + (sum(revenues) / len(revenues)) for x in x_numeric]

        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=months,
            y=revenues,
            name='Monthly Revenue',
            marker=dict(color='#3b82f6'),
            opacity=0.7,
        ))

        fig.add_trace(go.Scatter(
            x=months,
            y=z,
            mode='lines',
            name='Trend Line',
            line=dict(color='#ef4444', width=3),
        ))

        fig.update_layout(
            title=f'Trend Analysis - {trends["trend_type"].upper()} '
                  f'({trends["annual_pct_change"]:+.1f}%)',
            xaxis_title='Month',
            yaxis_title='Revenue ($)',
            barmode='overlay',
            template='plotly_white',
            height=500,
            annotations=[
                dict(
                    text=f'CV: {trends["volatility_cv"]:.1f}% | '
                         f'Seasonality: {trends["seasonality_strength"]:.1f}%',
                    xref='paper',
                    yref='paper',
                    x=0.5,
                    y=-0.15,
                    showarrow=False,
                    font=dict(size=11),
                )
            ],
        )

        return fig

    def plot_risk_dashboard(self) -> go.Figure:
        """Create risk assessment dashboard.

        Returns:
            Plotly figure with risk dashboard.
        """
        report = self.detector.get_overall_anomaly_report()

        # Create subplots
        fig = make_subplots(
            rows=2,
            cols=2,
            subplot_titles=(
                'Risk Score',
                'Anomalies by Type',
                'Monthly Anomalies',
                'Alert Distribution',
            ),
            specs=[
                [{'type': 'indicator'}, {'type': 'pie'}],
                [{'type': 'bar'}, {'type': 'bar'}],
            ],
        )

        # Risk Score Gauge
        risk_score = report['risk_score']
        fig.add_trace(
            go.Indicator(
                mode='gauge+number+delta',
                value=risk_score,
                title='Risk Score',
                domain={'x': [0, 1], 'y': [0, 1]},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': '#3b82f6'},
                    'steps': [
                        {'range': [0, 33], 'color': '#10b981'},
                        {'range': [33, 67], 'color': '#f59e0b'},
                        {'range': [67, 100], 'color': '#ef4444'},
                    ],
                    'threshold': {
                        'line': {'color': '#000'},
                        'thickness': 0.75,
                        'value': 50,
                    },
                },
            ),
            row=1,
            col=1,
        )

        # Anomalies Pie
        anom_types = [
            report['revenue_anomalies']['anomaly_count'],
            report['price_anomalies']['anomaly_count'],
            report['volume_anomalies']['anomaly_count'],
        ]

        fig.add_trace(
            go.Pie(
                labels=['Revenue', 'Price', 'Volume'],
                values=anom_types,
                marker=dict(colors=['#3b82f6', '#06b6d4', '#10b981']),
            ),
            row=1,
            col=2,
        )

        # Monthly anomalies
        months = list(self.forecaster.months)
        revenue_anom_counts = [
            1 if m in report['revenue_anomalies']['anomalies'] and
                 report['revenue_anomalies']['anomalies'][m]['anomaly']
            else 0
            for m in months
        ]

        fig.add_trace(
            go.Bar(
                x=months,
                y=revenue_anom_counts,
                name='Anomalies',
                marker=dict(color='#ef4444'),
            ),
            row=2,
            col=1,
        )

        # Alerts by severity
        alerts = self.detector.get_alerts(severity='all')
        high_count = sum(1 for a in alerts if a['severity'] == 'high')
        medium_count = sum(1 for a in alerts if a['severity'] == 'medium')

        fig.add_trace(
            go.Bar(
                x=['High', 'Medium'],
                y=[high_count, medium_count],
                marker=dict(color=['#ef4444', '#f59e0b']),
                name='Alerts',
            ),
            row=2,
            col=2,
        )

        fig.update_layout(
            title_text='Risk Assessment Dashboard',
            height=700,
            showlegend=False,
        )

        return fig

    def plot_forecast_comparison(self, periods: int = 3) -> go.Figure:
        """Create comprehensive forecast comparison.

        Args:
            periods: Number of periods to forecast.

        Returns:
            Plotly figure with forecast comparison.
        """
        forecast = self.forecaster.get_forecast_summary(periods)

        fig = make_subplots(
            rows=1,
            cols=2,
            subplot_titles=('Revenue Forecast', 'Price Forecast'),
        )

        # Revenue
        forecast_months = list(forecast['revenue_forecast'].keys())
        revenues = [forecast['revenue_forecast'][m]['forecast'] for m in forecast_months]
        lower_r = [forecast['revenue_forecast'][m]['lower_bound'] for m in forecast_months]
        upper_r = [forecast['revenue_forecast'][m]['upper_bound'] for m in forecast_months]

        fig.add_trace(
            go.Scatter(
                x=forecast_months,
                y=revenues,
                mode='lines+markers',
                name='Revenue',
                line=dict(color='#3b82f6'),
                marker=dict(size=10),
            ),
            row=1,
            col=1,
        )

        fig.add_trace(
            go.Scatter(
                x=forecast_months + forecast_months[::-1],
                y=upper_r + lower_r[::-1],
                fill='toself',
                fillcolor='rgba(59, 130, 246, 0.2)',
                line=dict(color='rgba(59, 130, 246, 0)'),
                name='CI',
            ),
            row=1,
            col=1,
        )

        # Price
        prices = [forecast['price_forecast'][m]['forecast'] for m in forecast_months]
        lower_p = [forecast['price_forecast'][m]['lower_bound'] for m in forecast_months]
        upper_p = [forecast['price_forecast'][m]['upper_bound'] for m in forecast_months]

        fig.add_trace(
            go.Scatter(
                x=forecast_months,
                y=prices,
                mode='lines+markers',
                name='Price',
                line=dict(color='#06b6d4'),
                marker=dict(size=10),
            ),
            row=1,
            col=2,
        )

        fig.add_trace(
            go.Scatter(
                x=forecast_months + forecast_months[::-1],
                y=upper_p + lower_p[::-1],
                fill='toself',
                fillcolor='rgba(6, 182, 212, 0.2)',
                line=dict(color='rgba(6, 182, 212, 0)'),
                name='CI',
            ),
            row=1,
            col=2,
        )

        fig.update_xaxes(title_text='Month', row=1, col=1)
        fig.update_xaxes(title_text='Month', row=1, col=2)
        fig.update_yaxes(title_text='Revenue ($)', row=1, col=1)
        fig.update_yaxes(title_text='Price ($)', row=1, col=2)

        fig.update_layout(
            title_text='Forecast Comparison - Q1 2026',
            height=500,
            showlegend=False,
            hovermode='x unified',
        )

        return fig

    def save_chart(self, fig: go.Figure, filepath: str) -> None:
        """Save chart to HTML file.

        Args:
            fig: Plotly figure to save.
            filepath: Path to save HTML file.
        """
        fig.write_html(filepath)
