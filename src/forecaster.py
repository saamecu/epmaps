"""Forecasting module for predicting future invoice data trends."""

from typing import Dict, List, Tuple
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.yearly_analyzer import YearlyAnalyzer


class Forecaster:
    """Forecasts future invoice data based on historical patterns.

    Provides:
    - Monthly revenue forecasts
    - Category-level predictions
    - Price trend forecasts
    - Confidence intervals
    """

    def __init__(self, yearly_analyzer: YearlyAnalyzer) -> None:
        """Initialize Forecaster with historical data.

        Args:
            yearly_analyzer: YearlyAnalyzer with loaded monthly data.
        """
        if not isinstance(yearly_analyzer, YearlyAnalyzer):
            raise TypeError("yearly_analyzer must be a YearlyAnalyzer instance")

        self.analyzer = yearly_analyzer
        self.metrics = yearly_analyzer.yearly_metrics()
        self.monthly_metrics = self.metrics['monthly_metrics']
        self.months = yearly_analyzer.months

    @classmethod
    def from_directory(cls, directory: str, exclude_v02: bool = True):
        """Create Forecaster from directory of data files.

        Args:
            directory: Path to directory with monthly data files.
            exclude_v02: Skip V02 files (default: True).

        Returns:
            Forecaster instance.
        """
        analyzer = YearlyAnalyzer.from_directory(directory, exclude_v02=exclude_v02)
        return cls(analyzer)

    def forecast_monthly_revenue(self, periods: int = 3) -> Dict:
        """Forecast monthly revenue for next N periods.

        Uses simple trend analysis with seasonal adjustment.

        Args:
            periods: Number of months to forecast (default: 3 for Q1).

        Returns:
            Dictionary with forecasts and confidence intervals.
        """
        # Extract historical revenues
        revenues = [self.monthly_metrics[m]['revenue'] for m in self.months]
        months_numeric = [int(m) for m in self.months]

        # Calculate trend using linear regression
        x = np.array(months_numeric).reshape(-1, 1)
        y = np.array(revenues)

        # Simple linear trend
        coefficients = np.polyfit(months_numeric, revenues, 1)
        trend_line = np.poly1d(coefficients)

        # Calculate seasonal factors
        mean_revenue = np.mean(revenues)
        seasonal_factors = [rev / mean_revenue for rev in revenues]

        # Forecast
        forecasts = {}
        for i in range(1, periods + 1):
            next_month = (int(self.months[-1]) + i - 1) % 12 + 1
            month_str = str(next_month).zfill(2)

            # Trend prediction
            next_numeric = int(self.months[-1]) + i
            trend_pred = trend_line(next_numeric)

            # Seasonal adjustment (use corresponding month from history if available)
            if next_month <= len(self.months):
                season_idx = next_month - 1
                seasonal_factor = seasonal_factors[season_idx]
            else:
                seasonal_factor = np.mean(seasonal_factors)

            # Final forecast
            forecast = trend_pred * seasonal_factor
            forecast = max(forecast, 0)  # Ensure non-negative

            # Confidence interval (±20% based on historical std)
            std_revenue = np.std(revenues)
            lower_bound = max(0, forecast - 1.96 * std_revenue / np.sqrt(len(revenues)))
            upper_bound = forecast + 1.96 * std_revenue / np.sqrt(len(revenues))

            forecasts[month_str] = {
                "month": month_str,
                "forecast": float(forecast),
                "lower_bound": float(lower_bound),
                "upper_bound": float(upper_bound),
                "confidence_interval_width": float(upper_bound - lower_bound),
            }

        return forecasts

    def forecast_category_revenue(self, category: str, periods: int = 3) -> Dict:
        """Forecast revenue for specific category.

        Args:
            category: Category code (e.g., 'AG01').
            periods: Number of months to forecast.

        Returns:
            Dictionary with category forecasts.
        """
        category_data = self.analyzer.top_categories_yearly(top_n=20)

        if category not in category_data:
            return {"error": f"Category {category} not found in data"}

        cat_monthly = category_data[category]['monthly_revenue']
        revenues = [cat_monthly.get(m, 0) for m in self.months]

        if all(r == 0 for r in revenues):
            return {"error": f"No data for category {category}"}

        # Same forecast logic as monthly_revenue
        months_numeric = [int(m) for m in self.months]
        coefficients = np.polyfit(months_numeric, revenues, 1)
        trend_line = np.poly1d(coefficients)

        mean_revenue = np.mean([r for r in revenues if r > 0]) or 1
        seasonal_factors = [r / mean_revenue if r > 0 else 1 for r in revenues]

        forecasts = {}
        for i in range(1, periods + 1):
            next_month = (int(self.months[-1]) + i - 1) % 12 + 1
            month_str = str(next_month).zfill(2)

            next_numeric = int(self.months[-1]) + i
            trend_pred = trend_line(next_numeric)

            if next_month <= len(self.months):
                seasonal_factor = seasonal_factors[next_month - 1]
            else:
                seasonal_factor = np.mean(seasonal_factors)

            forecast = max(0, trend_pred * seasonal_factor)

            std_revenue = np.std([r for r in revenues if r > 0]) or forecast * 0.2
            lower = max(0, forecast - 1.96 * std_revenue / np.sqrt(max(len(revenues), 1)))
            upper = forecast + 1.96 * std_revenue / np.sqrt(max(len(revenues), 1))

            forecasts[month_str] = {
                "month": month_str,
                "forecast": float(forecast),
                "lower_bound": float(lower),
                "upper_bound": float(upper),
            }

        return forecasts

    def forecast_price_trend(self, periods: int = 3) -> Dict:
        """Forecast average price trends.

        Args:
            periods: Number of months to forecast.

        Returns:
            Dictionary with price forecasts.
        """
        price_data = self.analyzer.price_evolution()
        avg_prices = [price_data[m]['avg'] for m in self.months]

        months_numeric = [int(m) for m in self.months]
        coefficients = np.polyfit(months_numeric, avg_prices, 1)
        trend_line = np.poly1d(coefficients)

        forecasts = {}
        for i in range(1, periods + 1):
            next_month = (int(self.months[-1]) + i - 1) % 12 + 1
            month_str = str(next_month).zfill(2)

            next_numeric = int(self.months[-1]) + i
            forecast = trend_line(next_numeric)
            forecast = max(0, forecast)

            std_price = np.std(avg_prices)
            lower = max(0, forecast - 1.96 * std_price / np.sqrt(len(self.months)))
            upper = forecast + 1.96 * std_price / np.sqrt(len(self.months))

            forecasts[month_str] = {
                "month": month_str,
                "forecast": float(forecast),
                "lower_bound": float(lower),
                "upper_bound": float(upper),
            }

        return forecasts

    def get_forecast_summary(self, periods: int = 3) -> Dict:
        """Get comprehensive forecast summary.

        Args:
            periods: Number of periods to forecast.

        Returns:
            Dictionary with all forecasts and analysis.
        """
        revenue_forecast = self.forecast_monthly_revenue(periods)
        price_forecast = self.forecast_price_trend(periods)

        # Calculate projected total
        projected_total = sum(f['forecast'] for f in revenue_forecast.values())

        return {
            "forecast_period": f"Next {periods} months",
            "base_period": f"Months {self.months[0]}-{self.months[-1]}",
            "historical_avg_monthly": self.metrics['avg_monthly_revenue'],
            "historical_std_monthly": self.metrics['std_monthly_revenue'],
            "projected_total_revenue": float(projected_total),
            "projected_avg_monthly": float(projected_total / periods),
            "revenue_forecast": revenue_forecast,
            "price_forecast": price_forecast,
            "forecast_confidence": 0.95,  # 95% confidence interval
        }

    def evaluate_forecast_accuracy(self, actual_data: Dict) -> Dict:
        """Evaluate forecast accuracy against actual data.

        Args:
            actual_data: Dictionary with actual monthly data {month: revenue}.

        Returns:
            Dictionary with accuracy metrics.
        """
        # Calculate MAE, RMSE, MAPE
        errors = {}
        for month, actual in actual_data.items():
            # Assuming we have forecast for this month
            if month in self.monthly_metrics:
                forecast = self.monthly_metrics[month]['revenue']
                error = actual - forecast
                pct_error = (error / actual * 100) if actual != 0 else 0

                errors[month] = {
                    "actual": actual,
                    "forecast": forecast,
                    "error": error,
                    "pct_error": pct_error,
                }

        mae = np.mean([abs(e['error']) for e in errors.values()]) if errors else 0
        rmse = np.sqrt(np.mean([e['error'] ** 2 for e in errors.values()])) if errors else 0
        mape = np.mean([abs(e['pct_error']) for e in errors.values()]) if errors else 0

        return {
            "mae": float(mae),
            "rmse": float(rmse),
            "mape": float(mape),
            "sample_size": len(errors),
            "errors_by_month": errors,
        }

    def get_trends(self) -> Dict:
        """Analyze trends in historical data.

        Returns:
            Dictionary with trend analysis.
        """
        revenues = [self.monthly_metrics[m]['revenue'] for m in self.months]
        months_numeric = [int(m) for m in self.months]

        # Linear trend
        coefficients = np.polyfit(months_numeric, revenues, 1)
        slope = coefficients[0]

        # Trend interpretation
        if slope > 0:
            trend_type = "increasing"
            pct_change = (slope / np.mean(revenues) * 100)
        elif slope < 0:
            trend_type = "decreasing"
            pct_change = (slope / np.mean(revenues) * 100)
        else:
            trend_type = "stable"
            pct_change = 0

        # Volatility
        std_revenue = np.std(revenues)
        cv = (std_revenue / np.mean(revenues) * 100)

        # Seasonality
        first_half = np.mean(revenues[:6])
        second_half = np.mean(revenues[6:])
        seasonality_strength = abs(first_half - second_half) / np.mean(revenues) * 100

        return {
            "trend_type": trend_type,
            "slope": float(slope),
            "annual_pct_change": float(pct_change),
            "volatility_cv": float(cv),
            "seasonality_strength": float(seasonality_strength),
            "trend_strength": "strong" if abs(pct_change) > 10 else "weak",
        }
