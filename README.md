# Proxmox PBS Disaster Recovery

> Enterprise-grade dual Proxmox Backup Server (PBS) disaster recovery automation

## Overview

This repository provides enterprise-grade automation for a dual-PBS disaster recovery
architecture. It handles backup mirroring, Proxmox configuration recovery, full VM
restoration, and comprehensive monitoring.

## Architecture

```
Proxmox VE
  │
  ▼ (scheduled backups)
PBS-MAIN (pbs-backups)
  │
  ▼ (scheduled sync)
PBS-TRUENAS (pbs-replica)
```

## Features

### Core Features
- **Automated policy mirroring**: Sync retention and verify policies from PBS-MAIN to PBS-TRUENAS
- **Interactive recovery wizard**: Step-by-step Proxmox recovery
- **Configuration backup extraction**: Prepare recovery artifacts on PBS
- **Full VM restore support**: Restore VMs and containers from backups
- **Smoke tested**: All scripts verified for syntax and structure

### Advanced Features

#### Async/Concurrency Architecture
- **Parallel backup verification**: Verify multiple backups concurrently
- **Async PBS task monitoring**: Non-blocking task status polling with callbacks
- **Concurrent DR scenario testing**: Run multiple DR tests in parallel
- **Connection pooling**: Efficient PBS API connections

#### Advanced Configuration Management
- **YAML config with validation**: `/etc/proxmox-dr/config.yaml`
- **Environment-specific configs**: site-a, site-b, dr-site, test
- **Hot-reload**: Config changes trigger automatic reloading
- **Encrypted credentials**: Support for SOPS/Mozilla sops

#### Disaster Recovery Orchestration Engine
- **State machine**: detect → decide → failover → verify → restore
- **Workflow DAG**: Complex multi-node recovery with dependencies
- **Automated DR testing**: Chaos engineering style testing
- **Rollback capability**: Automatic rollback on failed recovery

#### Monitoring & Observability
- **Prometheus metrics**: Backup health, sync status, DR events
- **Grafana dashboards**: PBS cluster monitoring dashboards
- **Alertmanager integration**: Multi-channel alerting
- **Structured JSON logging**: With severity levels

#### Testing & Validation
- **Integration tests**: Proxmox API mocks for testing
- **DR scenario simulation**: Dry-run mode for safe testing
- **Backup integrity verification**: Automated integrity checks
- **Coverage reporting**: Code coverage tracking

#### CI/CD & Distribution
- **GitHub Actions**: Automated test, build, release pipeline
- **Debian package (.deb)**: Easy deployment
- **Ansible role**: Cluster-wide DR setup
- **Docker image**: Containerized testing and deployment

## Quick Start

### Installation

#### Via Debian Package
```bash
wget https://github.com/example/proxmox-pbs-dr/releases/latest/download/proxmox-pbs-dr_1.0.0_all.deb
sudo dpkg -i proxmox-pbs-dr_1.0.0_all.deb
sudo apt-get install -f  # Install dependencies
```

#### Via Ansible
```bash
ansible-galaxy install proxmox.dr
ansible-playbook -i inventory site.yml --extra-vars="proxmox_dr_environment=site-a"
```

#### Via Docker
```bash
docker run -v /etc/proxmox-dr:/etc/proxmox-dr \
  ghcr.io/example/proxmox-pbs-dr:latest
```

### Configuration

Create configuration at `/etc/proxmox-dr/config.yaml`:

```yaml
environment: site-a
log_level: INFO
log_format: json

pbs_main:
  name: pbs-main
  host: 192.168.1.100
  port: 8007
  datastore: pbs-backups
  username: root@pam
  # api_token: "root@pam!dr-token"  # Recommended

pbs_dr:
  name: pbs-dr
  host: 192.168.1.101
  port: 8007
  datastore: pbs-replica
  username: root@pam

sync:
  enabled: true
  schedule: "0 2 * * *"

alerts:
  enabled: true
  alertmanager_url: "http://localhost:9093"
```

### Running DR Operations

#### Manual DR Trigger
```bash
proxmox-dr-orchestrator --trigger --config /etc/proxmox-dr/config.yaml
```

#### Parallel Backup Verification
```bash
proxmox-dr-verify --parallel 4 --repository "root@pam@pbs:pbs-replica"
```

#### Run in Dry-Run Mode
```bash
proxmox-dr-orchestrator --trigger --dry-run
```

### Monitoring

#### Prometheus Metrics
Expose metrics on port 9090:
```bash
curl http://localhost:9090/metrics
```

#### Grafana Dashboard
Import `grafana/dashboard.json` into your Grafana instance.

## Scripts & Tools

| Component | Purpose | Command |
|-----------|---------|---------|
| `src/proxmox_dr/` | Python DR Framework | Import as library |
| `scripts/rebuilt-proxmox-run-on-pbs-first.sh` | Extract recovery artifacts | PBS-TRUENAS |
| `scripts/rebuilt-proxmox-run-on-proxmox-second.sh` | Interactive Proxmox recovery | New Proxmox host |
| `scripts/mirror-pbs-main-policy-to-pbs-truenas.sh` | Sync policies PBS-MAIN → PBS-TRUENAS | PBS-TRUENAS |

## Development

### Setup
```bash
# Clone and install
git clone <repository-url>
cd proxmox-pbs-dr
pip install -e .
pip install -r src/requirements.txt
```

### Run Tests
```bash
# All tests
make check

# Unit tests only
make unit-test

# Integration tests
make integration-test

# With coverage
make coverage
```

### Build Package
```bash
# Debian package
make build-deb

# Docker image
make docker
```

## Verification Commands

### Test Advanced Features

#### Test State Machine
```bash
python -c "from proxmox_dr.state_machine import DRStateMachine, DRPhase; \
  sm = DRStateMachine(); print(f'State: {sm.current_phase.value}')"
```

#### Test Async Backup Verification
```bash
python -c "import asyncio; from proxmox_dr.async_ops import PBSClient; \
  print('Async ops module loaded')"
```

#### Test Config Loading
```bash
python -c "from proxmox_dr.config import load_config; \
  c = load_config('config/config.yaml.example'); \
  print(f'Environment: {c.environment.value}')"
```

#### Test Prometheus Metrics
```bash
python -c "from proxmox_dr.monitoring import MetricsCollector; \
  mc = MetricsCollector(); mc.counter('test'); \
  print(mc.export_prometheus())"
```

#### Test Workflow DAG
```bash
python -c "from proxmox_dr.orchestrator import WorkflowDAG, WorkflowNode; \
  w = WorkflowDAG('test'); print('Workflow DAG created')"
```

## Directory Structure

```
.
├── ansible/              # Ansible role for cluster-wide setup
├── config/               # Environment-specific configs
├── debian/               # Debian packaging
├── docker/               # Docker image
├── grafana/              # Grafana dashboards
├── prometheus/           # Prometheus rules
├── scripts/              # Shell scripts
├── src/proxmox_dr/       # Python framework
├── tests/                # Test suites
│   ├── integration/      # Integration tests
│   └── unit/             # Unit tests
└── .github/workflows/    # CI/CD pipelines
```

## Documentation

- [Disaster Recovery Scenarios](docs/DR-SCENARIOS.md)
- [Key Rules](docs/KEY-RULES.md)
- [Configuration Reference](config/config.yaml.example)
- [Monitoring Setup](prometheus/proxmox-dr.rules.yml)

## Requirements

- Proxmox Backup Server 2.x+
- Python 3.8+ (for Python framework)
- bash 4.0+
- root access on PBS and Proxmox hosts
- Prometheus + Grafana (optional, for monitoring)

## License

See [LICENSE](LICENSE)
