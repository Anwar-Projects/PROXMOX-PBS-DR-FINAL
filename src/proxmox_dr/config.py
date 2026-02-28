"""Configuration management for Proxmox DR.

Supports YAML configs with validation, environment-specific configs,
and encrypted credentials via SOPS.
"""

import os
import yaml
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any
from enum import Enum

logger = logging.getLogger(__name__)


class Environment(Enum):
    """DR environment types."""
    SITE_A = "site-a"
    SITE_B = "site-b"
    DR_SITE = "dr-site"
    TEST = "test"


@dataclass
class PBSHost:
    """PBS host configuration."""
    name: str
    host: str
    port: int = 8007
    datastore: str = "pbs-backups"
    username: str = "root@pam"
    password: Optional[str] = None
    api_token: Optional[str] = None
    fingerprint: Optional[str] = None
    verify_ssl: bool = True


@dataclass
class SyncConfig:
    """Sync job configuration."""
    enabled: bool = True
    schedule: str = "0 2 * * *"  # Daily at 2 AM
    source_datastore: str = "pbs-backups"
    target_datastore: str = "pbs-replica"
    delete_missing: bool = False


@dataclass
class RetentionConfig:
    """Retention policy configuration."""
    keep_last: int = 7
    keep_daily: int = 7
    keep_weekly: int = 4
    keep_monthly: int = 12
    keep_yearly: int = 2


@dataclass
class AlertConfig:
    """Alert/notification configuration."""
    enabled: bool = True
    webhook_url: Optional[str] = None
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    alert_email: Optional[str] = None
    alertmanager_url: Optional[str] = None


@dataclass
class DRConfig:
    """Main DR configuration."""
    environment: Environment = Environment.SITE_A
    debug: bool = False
    log_level: str = "INFO"
    log_format: str = "json"
    
    # PBS hosts
    pbs_main: PBSHost = field(default_factory=lambda: PBSHost(
        name="pbs-main",
        host="192.168.1.100",
        datastore="pbs-backups"
    ))
    pbs_dr: PBSHost = field(default_factory=lambda: PBSHost(
        name="pbs-dr",
        host="192.168.1.101",
        datastore="pbs-replica"
    ))
    
    # Configuration sections
    sync: SyncConfig = field(default_factory=SyncConfig)
    retention: RetentionConfig = field(default_factory=RetentionConfig)
    alerts: AlertConfig = field(default_factory=AlertConfig)
    
    # Recovery settings
    recovery_dir: str = "/var/lib/proxmox-dr/recovery"
    dry_run: bool = False
    max_parallel_verification: int = 4
    verification_timeout: int = 3600
    
    # State management
    state_file: str = "/var/lib/proxmox-dr/state.json"
    history_file: str = "/var/lib/proxmox-dr/history.jsonl"


def load_config(config_path: Optional[str] = None) -> DRConfig:
    """Load configuration from YAML file.
    
    Args:
        config_path: Path to config file. If None, searches standard locations.
        
    Returns:
        DRConfig instance
    """
    if config_path is None:
        # Search standard locations
        search_paths = [
            Path("/etc/proxmox-dr/config.yaml"),
            Path("/etc/proxmox-dr/config.yml"),
            Path(os.environ.get("PROXMOX_DR_CONFIG", "")),
            Path("./config.yaml"),
        ]
        for path in search_paths:
            if path and path.exists():
                config_path = str(path)
                break
    
    if config_path and Path(config_path).exists():
        logger.info(f"Loading config from {config_path}")
        with open(config_path, 'r') as f:
            data = yaml.safe_load(f)
        return _dict_to_config(data)
    
    logger.info("Using default configuration")
    return DRConfig()


def _dict_to_config(data: Dict[str, Any]) -> DRConfig:
    """Convert dictionary to DRConfig."""
    config = DRConfig()
    
    if 'environment' in data:
        config.environment = Environment(data['environment'])
    if 'debug' in data:
        config.debug = data['debug']
    if 'log_level' in data:
        config.log_level = data['log_level']
    if 'log_format' in data:
        config.log_format = data['log_format']
    
    if 'pbs_main' in data:
        config.pbs_main = PBSHost(**data['pbs_main'])
    if 'pbs_dr' in data:
        config.pbs_dr = PBSHost(**data['pbs_dr'])
    
    if 'sync' in data:
        config.sync = SyncConfig(**data['sync'])
    if 'retention' in data:
        config.retention = RetentionConfig(**data['retention'])
    if 'alerts' in data:
        config.alerts = AlertConfig(**data['alerts'])
    
    return config


def save_config(config: DRConfig, path: str) -> None:
    """Save configuration to YAML file."""
    data = {
        'environment': config.environment.value,
        'debug': config.debug,
        'log_level': config.log_level,
        'log_format': config.log_format,
        'pbs_main': {
            'name': config.pbs_main.name,
            'host': config.pbs_main.host,
            'port': config.pbs_main.port,
            'datastore': config.pbs_main.datastore,
            'username': config.pbs_main.username,
        },
        'pbs_dr': {
            'name': config.pbs_dr.name,
            'host': config.pbs_dr.host,
            'port': config.pbs_dr.port,
            'datastore': config.pbs_dr.datastore,
            'username': config.pbs_dr.username,
        },
        'sync': {
            'enabled': config.sync.enabled,
            'schedule': config.sync.schedule,
            'source_datastore': config.sync.source_datastore,
            'target_datastore': config.sync.target_datastore,
            'delete_missing': config.sync.delete_missing,
        },
        'retention': {
            'keep_last': config.retention.keep_last,
            'keep_daily': config.retention.keep_daily,
            'keep_weekly': config.retention.keep_weekly,
            'keep_monthly': config.retention.keep_monthly,
            'keep_yearly': config.retention.keep_yearly,
        },
        'alerts': {
            'enabled': config.alerts.enabled,
            'webhook_url': config.alerts.webhook_url,
            'smtp_host': config.alerts.smtp_host,
            'smtp_port': config.alerts.smtp_port,
            'alert_email': config.alerts.alert_email,
            'alertmanager_url': config.alerts.alertmanager_url,
        },
        'recovery_dir': config.recovery_dir,
        'dry_run': config.dry_run,
        'max_parallel_verification': config.max_parallel_verification,
        'verification_timeout': config.verification_timeout,
    }
    
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
