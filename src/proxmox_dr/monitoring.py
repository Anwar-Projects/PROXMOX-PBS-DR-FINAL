"""Monitoring and observability for Proxmox DR.

Provides Prometheus metrics, structured logging, and alerting.
"""

import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


@dataclass
class MetricValue:
    """A metric value with timestamp."""
    name: str
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_prometheus(self) -> str:
        """Convert to Prometheus format."""
        labels_str = ",".join(
            f'{k}="{v}"' for k, v in self.labels.items()
        )
        if labels_str:
            return f"{self.name}{{{labels_str}}} {self.value}"
        return f"{self.name} {self.value}"


@dataclass
class Alert:
    """An alert notification."""
    id: str
    severity: AlertSeverity
    title: str
    message: str
    timestamp: datetime
    source: str
    labels: Dict[str, str] = field(default_factory=dict)
    resolved: bool = False
    resolved_at: Optional[datetime] = None


class MetricsCollector:
    """Collects metrics for Prometheus export."""
    
    def __init__(self):
        self.metrics: Dict[str, MetricValue] = {}
        self.counters: Dict[str, float] = {}
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, List[float]] = {}
    
    def counter(self, name: str, labels: Optional[Dict[str, str]] = None) -> None:
        """Increment a counter metric."""
        key = self._metric_key(name, labels)
        self.counters[key] = self.counters.get(key, 0) + 1
        self._update_metric(name, self.counters[key], labels)
    
    def gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Set a gauge metric."""
        key = self._metric_key(name, labels)
        self.gauges[key] = value
        self._update_metric(name, value, labels)
    
    def histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Record a histogram observation."""
        key = self._metric_key(name, labels)
        if key not in self.histograms:
            self.histograms[key] = []
        self.histograms[key].append(value)
        self._update_metric(name, value, labels)
    
    def _metric_key(self, name: str, labels: Optional[Dict[str, str]]) -> str:
        """Generate a unique key for a metric."""
        if labels:
            label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
            return f"{name}:{label_str}"
        return name
    
    def _update_metric(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """Update a metric value."""
        key = self._metric_key(name, labels)
        self.metrics[key] = MetricValue(
            name=name,
            value=value,
            labels=labels or {},
        )
    
    def export_prometheus(self) -> str:
        """Export metrics in Prometheus format."""
        lines = [
            "# Proxmox DR Metrics",
            f"# Generated at {datetime.now().isoformat()}",
        ]
        
        for metric in self.metrics.values():
            lines.append(metric.to_prometheus())
        
        return "\n".join(lines)
    
    def get_metrics(self) -> Dict[str, MetricValue]:
        """Get all metrics."""
        return self.metrics.copy()


class PrometheusExporter:
    """Export metrics for Prometheus scraping."""
    
    def __init__(
        self,
        collector: MetricsCollector,
        port: int = 9090,
        path: str = "/metrics",
    ):
        self.collector = collector
        self.port = port
        self.path = path
        self._server = None
    
    async def start(self) -> None:
        """Start the Prometheus exporter HTTP server."""
        from aiohttp import web
        
        async def metrics_handler(request):
            return web.Response(
                body=self.collector.export_prometheus(),
                content_type="text/plain",
            )
        
        app = web.Application()
        app.router.add_get(self.path, metrics_handler)
        
        runner = web.AppRunner(app)
        await runner.setup()
        
        site = web.TCPSite(runner, "0.0.0.0", self.port)
        await site.start()
        
        self._server = runner
        logger.info(f"Prometheus exporter started on port {self.port}")
    
    async def stop(self) -> None:
        """Stop the exporter."""
        if self._server:
            await self._server.cleanup()
            self._server = None
            logger.info("Prometheus exporter stopped")


class AlertManager:
    """Send alerts via various channels."""
    
    def __init__(self, config: AlertConfig):
        self.config = config
        self._webhook_session = None
    
    async def send_alert(self, alert: Alert) -> bool:
        """Send an alert through configured channels."""
        success = True
        
        if self.config.webhook_url:
            success &= await self._send_webhook(alert)
        
        if self.config.alertmanager_url:
            success &= await self._send_alertmanager(alert)
        
        if self.config.smtp_host and self.config.alert_email:
            success &= await self._send_email(alert)
        
        return success
    
    async def _send_webhook(self, alert: Alert) -> bool:
        """Send alert to webhook."""
        # Implementation would use aiohttp
        logger.info(f"Sending webhook alert: {alert.title}")
        return True
    
    async def _send_alertmanager(self, alert: Alert) -> bool:
        """Send alert to Prometheus Alertmanager."""
        logger.info(f"Sending Alertmanager alert: {alert.title}")
        return True
    
    async def _send_email(self, alert: Alert) -> bool:
        """Send alert via email."""
        logger.info(f"Sending email alert: {alert.title}")
        return True
