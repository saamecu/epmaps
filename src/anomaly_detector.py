"""Anomaly detection module for identifying unusual patterns in invoice data."""

from typing import Dict, List, Tuple
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest

from src.yearly_analyzer import YearlyAnalyzer


class AnomalyDetector:
    """Detects anomalies in invoice data using statistical methods.

    Detection methods:
    - Z-score based detection
    - Isolation Forest for multivariate analysis
    - Threshold-based alerts
    """

    def __init__(self, yearly_analyzer: YearlyAnalyzer, z_threshold: float = 2.0) -> None:
        """Initialize AnomalyDetector with historical data.

        Args:
            yearly_analyzer: YearlyAnalyzer with loaded monthly data.
            z_threshold: Z-score threshold for anomalies (default: 2.0).
        """
        if not isinstance(yearly_analyzer, YearlyAnalyzer):
            raise TypeError("yearly_analyzer must be a YearlyAnalyzer instance")

        self.analyzer = yearly_analyzer
        self.z_threshold = z_threshold
        self.metrics = yearly_analyzer.yearly_metrics()
        self.monthly_metrics = self.metrics['monthly_metrics']
        self.months = yearly_analyzer.months

    @classmethod
    def from_directory(cls, directory: str, z_threshold: float = 2.0):
        """Create AnomalyDetector from directory of data files.

        Args:
            directory: Path to directory with monthly data files.
            z_threshold: Z-score threshold for anomalies.

        Returns:
            AnomalyDetector instance.
        """
        analyzer = YearlyAnalyzer.from_directory(directory)
        return cls(analyzer, z_threshold=z_threshold)

    def detect_revenue_anomalies(self) -> Dict:
        """Detect anomalies in monthly revenue.

        Returns:
            Dictionary with anomalies and severity.
        """
        revenues = np.array([self.monthly_metrics[m]['revenue'] for m in self.months])

        # Z-score method
        mean_revenue = np.mean(revenues)
        std_revenue = np.std(revenues)

        z_scores = (revenues - mean_revenue) / std_revenue if std_revenue > 0 else np.zeros_like(revenues)

        anomalies = {}
        for i, month in enumerate(self.months):
            z_score = z_scores[i]
            is_anomaly = abs(z_score) > self.z_threshold

            if is_anomaly or abs(z_score) > 1.0:  # Include mild anomalies too
                severity = "high" if abs(z_score) > self.z_threshold else "medium"

                anomalies[month] = {
                    "revenue": float(revenues[i]),
                    "z_score": float(z_score),
                    "deviation_from_mean_pct": float((revenues[i] - mean_revenue) / mean_revenue * 100),
                    "severity": severity,
                    "anomaly": is_anomaly,
                }

        return {
            "method": "z_score",
            "threshold": self.z_threshold,
            "mean": float(mean_revenue),
            "std": float(std_revenue),
            "anomalies": anomalies,
            "anomaly_count": sum(1 for a in anomalies.values() if a['anomaly']),
        }

    def detect_price_anomalies(self) -> Dict:
        """Detect anomalies in average prices.

        Returns:
            Dictionary with price anomalies.
        """
        price_data = self.analyzer.price_evolution()
        prices = np.array([price_data[m]['avg'] for m in self.months])

        mean_price = np.mean(prices)
        std_price = np.std(prices)

        z_scores = (prices - mean_price) / std_price if std_price > 0 else np.zeros_like(prices)

        anomalies = {}
        for i, month in enumerate(self.months):
            z_score = z_scores[i]
            is_anomaly = abs(z_score) > self.z_threshold

            if is_anomaly or abs(z_score) > 1.0:
                severity = "high" if abs(z_score) > self.z_threshold else "medium"

                anomalies[month] = {
                    "avg_price": float(prices[i]),
                    "z_score": float(z_score),
                    "deviation_from_mean_pct": float((prices[i] - mean_price) / mean_price * 100),
                    "severity": severity,
                    "anomaly": is_anomaly,
                }

        return {
            "method": "z_score",
            "threshold": self.z_threshold,
            "mean": float(mean_price),
            "std": float(std_price),
            "anomalies": anomalies,
            "anomaly_count": sum(1 for a in anomalies.values() if a['anomaly']),
        }

    def detect_volume_anomalies(self) -> Dict:
        """Detect anomalies in transaction volume (records count).

        Returns:
            Dictionary with volume anomalies.
        """
        volumes = np.array([self.monthly_metrics[m]['records'] for m in self.months])

        mean_volume = np.mean(volumes)
        std_volume = np.std(volumes)

        z_scores = (volumes - mean_volume) / std_volume if std_volume > 0 else np.zeros_like(volumes)

        anomalies = {}
        for i, month in enumerate(self.months):
            z_score = z_scores[i]
            is_anomaly = abs(z_score) > self.z_threshold

            if is_anomaly or abs(z_score) > 1.0:
                severity = "high" if abs(z_score) > self.z_threshold else "medium"

                anomalies[month] = {
                    "records": int(volumes[i]),
                    "z_score": float(z_score),
                    "deviation_from_mean_pct": float((volumes[i] - mean_volume) / mean_volume * 100),
                    "severity": severity,
                    "anomaly": is_anomaly,
                }

        return {
            "method": "z_score",
            "threshold": self.z_threshold,
            "mean": float(mean_volume),
            "std": float(std_volume),
            "anomalies": anomalies,
            "anomaly_count": sum(1 for a in anomalies.values() if a['anomaly']),
        }

    def detect_category_anomalies(self) -> Dict:
        """Detect anomalies in category distribution.

        Returns:
            Dictionary with category anomalies.
        """
        top_cats = self.analyzer.top_categories_yearly(top_n=5)

        anomalies = {}

        for category, data in top_cats.items():
            monthly_rev = data['monthly_revenue']
            revenues = np.array([monthly_rev.get(m, 0) for m in self.months])

            if np.sum(revenues) == 0:
                continue

            mean_rev = np.mean(revenues)
            std_rev = np.std(revenues)

            if std_rev == 0:
                continue

            z_scores = (revenues - mean_rev) / std_rev

            category_anomalies = {}
            for i, month in enumerate(self.months):
                z_score = z_scores[i]
                if abs(z_score) > self.z_threshold or abs(z_score) > 1.5:
                    category_anomalies[month] = {
                        "revenue": float(revenues[i]),
                        "z_score": float(z_score),
                        "severity": "high" if abs(z_score) > self.z_threshold else "medium",
                    }

            if category_anomalies:
                anomalies[category] = {
                    "mean": float(mean_rev),
                    "std": float(std_rev),
                    "anomalies": category_anomalies,
                    "anomaly_count": len(category_anomalies),
                }

        return {
            "method": "category_zscore",
            "threshold": self.z_threshold,
            "categories_with_anomalies": len(anomalies),
            "anomalies": anomalies,
        }

    def detect_multivariate_anomalies(self) -> Dict:
        """Detect anomalies using Isolation Forest (multivariate).

        Returns:
            Dictionary with multivariate anomalies.
        """
        # Build feature matrix
        features = []
        for month in self.months:
            metrics = self.monthly_metrics[month]
            price_data = self.analyzer.price_evolution()

            features.append([
                metrics['revenue'],
                metrics['records'],
                metrics['invoices'],
                price_data[month]['avg'],
            ])

        X = np.array(features)

        # Isolation Forest
        iso_forest = IsolationForest(contamination=0.1, random_state=42)
        predictions = iso_forest.fit_predict(X)

        anomalies = {}
        for i, month in enumerate(self.months):
            if predictions[i] == -1:  # -1 indicates anomaly
                anomalies[month] = {
                    "revenue": float(X[i][0]),
                    "records": int(X[i][1]),
                    "invoices": int(X[i][2]),
                    "avg_price": float(X[i][3]),
                    "anomaly_score": float(iso_forest.score_samples(X[i:i+1])[0]),
                }

        return {
            "method": "isolation_forest",
            "contamination": 0.1,
            "anomalies": anomalies,
            "anomaly_count": len(anomalies),
            "anomaly_percentage": float(len(anomalies) / len(self.months) * 100),
        }

    def get_overall_anomaly_report(self) -> Dict:
        """Generate comprehensive anomaly report.

        Returns:
            Dictionary with all anomaly detections and summary.
        """
        revenue_anom = self.detect_revenue_anomalies()
        price_anom = self.detect_price_anomalies()
        volume_anom = self.detect_volume_anomalies()
        category_anom = self.detect_category_anomalies()
        multivariate_anom = self.detect_multivariate_anomalies()

        # Calculate risk score
        total_anomalies = (
            revenue_anom['anomaly_count'] +
            price_anom['anomaly_count'] +
            volume_anom['anomaly_count'] +
            multivariate_anom['anomaly_count']
        )

        risk_score = min(100, (total_anomalies / len(self.months)) * 50)  # Max 100

        return {
            "z_threshold": self.z_threshold,
            "total_anomalies_detected": total_anomalies,
            "risk_score": float(risk_score),
            "risk_level": "high" if risk_score > 50 else "medium" if risk_score > 20 else "low",
            "revenue_anomalies": revenue_anom,
            "price_anomalies": price_anom,
            "volume_anomalies": volume_anom,
            "category_anomalies": category_anom,
            "multivariate_anomalies": multivariate_anom,
            "summary": {
                "high_severity_months": [m for a in [revenue_anom, price_anom, volume_anom]
                                         for m, data in a.get('anomalies', {}).items()
                                         if data.get('severity') == 'high'],
                "affected_categories": list(category_anom['anomalies'].keys()),
            }
        }

    def get_alerts(self, severity: str = "high") -> List[Dict]:
        """Generate actionable alerts based on anomalies.

        Args:
            severity: Minimum severity level ("high", "medium", "all").

        Returns:
            List of alerts.
        """
        report = self.get_overall_anomaly_report()
        alerts = []

        # Revenue alerts
        for month, anom in report['revenue_anomalies'].get('anomalies', {}).items():
            if severity == "all" or anom.get('severity') == severity:
                alerts.append({
                    "type": "revenue",
                    "month": month,
                    "severity": anom['severity'],
                    "message": f"Revenue in {month} is {anom['deviation_from_mean_pct']:.1f}% "
                              f"from average (Z-score: {anom['z_score']:.2f})",
                })

        # Price alerts
        for month, anom in report['price_anomalies'].get('anomalies', {}).items():
            if severity == "all" or anom.get('severity') == severity:
                alerts.append({
                    "type": "price",
                    "month": month,
                    "severity": anom['severity'],
                    "message": f"Average price in {month} is {anom['deviation_from_mean_pct']:.1f}% "
                              f"from average (Z-score: {anom['z_score']:.2f})",
                })

        # Category alerts
        for category, cat_data in report['category_anomalies'].get('anomalies', {}).items():
            for month, anom in cat_data.get('anomalies', {}).items():
                if severity == "all" or anom.get('severity') == severity:
                    alerts.append({
                        "type": "category",
                        "category": category,
                        "month": month,
                        "severity": anom['severity'],
                        "message": f"Category {category} in {month} shows unusual revenue "
                                  f"(Z-score: {anom['z_score']:.2f})",
                    })

        return alerts
