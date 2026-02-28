"""Unit tests for configuration module."""

import os
import tempfile
import pytest
from pathlib import Path

from proxmox_dr.config import (
    DRConfig,
    load_config,
    save_config,
    PBSHost,
    Environment,
    SyncConfig,
    RetentionConfig,
)


class TestDRConfig:
    """Tests for DRConfig dataclass."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = DRConfig()
        assert config.environment == Environment.SITE_A
        assert config.log_level == "INFO"
        assert config.dry_run is False
        assert config.max_parallel_verification == 4
    
    def test_pbs_host_defaults(self):
        """Test PBS host default values."""
        host = PBSHost(name="test", host="192.168.1.1")
        assert host.port == 8007
        assert host.datastore == "pbs-backups"
        assert host.username == "root@pam"
        assert host.verify_ssl is True
    
    def test_sync_config_defaults(self):
        """Test sync config defaults."""
        sync = SyncConfig()
        assert sync.enabled is True
        assert sync.schedule == "0 2 * * *"
        assert sync.delete_missing is False
    
    def test_retention_config(self):
        """Test retention config."""
        retention = RetentionConfig()
        assert retention.keep_last == 7
        assert retention.keep_weekly == 4


class TestConfigLoading:
    """Tests for configuration loading."""
    
    def test_load_default_config(self):
        """Test loading default config."""
        config = load_config()
        assert isinstance(config, DRConfig)
    
    def test_load_from_yaml(self, tmp_path):
        """Test loading from YAML file."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
environment: site-b
debug: true
log_level: DEBUG
pbs_main:
  name: test-main
  host: 10.0.0.1
""")
        config = load_config(str(config_file))
        assert config.environment == Environment.SITE_B
        assert config.debug is True
        assert config.log_level == "DEBUG"
        assert config.pbs_main.host == "10.0.0.1"
    
    def test_save_and_load_config(self, tmp_path):
        """Test saving and loading config."""
        config_file = tmp_path / "saved.yaml"
        original = DRConfig()
        original.environment = Environment.DR_SITE
        original.pbs_main.host = "10.0.0.100"
        
        save_config(original, str(config_file))
        loaded = load_config(str(config_file))
        
        assert loaded.environment == Environment.DR_SITE
        assert loaded.pbs_main.host == "10.0.0.100"


class TestEnvironment:
    """Tests for environment types."""
    
    def test_environment_enum(self):
        """Test environment enum values."""
        assert Environment.SITE_A.value == "site-a"
        assert Environment.SITE_B.value == "site-b"
        assert Environment.DR_SITE.value == "dr-site"
        assert Environment.TEST.value == "test"
