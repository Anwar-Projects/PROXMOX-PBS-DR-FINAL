# Proxmox PBS Disaster Recovery

> Dual Proxmox Backup Server (PBS) disaster recovery automation

## Overview

This repository provides scripts and automation for a dual-PBS disaster recovery
architecture. It handles backup mirroring, Proxmox configuration recovery, and
full VM restoration.

## Architecture

```
Proxmox VE
  │
  ▼ (scheduled backups)
PBS-MAIN (pbs-backups)
  │
  ▼ (scheduled pull sync)
PBS-TRUENAS (pbs-replica)
```

## Features

- **Automated policy mirroring**: Sync retention and verify policies from PBS-MAIN to PBS-TRUENAS
- **Interactive recovery wizard**: Step-by-step Proxmox recovery
- **Configuration backup extraction**: Prepare recovery artifacts on PBS
- **Full VM restore support**: Restore VMs and containers from backups
- **Smoke tested**: All scripts verified for syntax and structure

## Quick Start

### 1. Clone and verify

```bash
git clone <repository-url>
make verify
cd prodmox-pbs-dr
```

### 2. Install

```bash
# Install scripts to /opt/proxmox-pbs-dr/
sudo cp -r scripts/ /opt/proxmox-pbs-dr/

# Install cron job (on PBS-TRUENAS)
sudo cp cron/pbs-policy-mirror.cron /etc/cron.d/
```

### 3. Configure

Set environment variables (optional - defaults work for standard setup):

```bash
export PBS_MAIN="192.168.1.100"          # PBS-MAIN IP
export PBS_LOCAL_DATASTORE="pbs-replica" # Local datastore name
```

### 4. Run

```bash
# Mirror policies from PBS-MAIN (run on PBS-TRUENAS)
sudo ./scripts/mirror-pbs-main-policy-to-pbs-truenas.sh

# Prepare recovery artifacts (if disaster strikes)
sudo ./scripts/rebuilt-proxmox-run-on-pbs-first.sh

# On new Proxmox host, run recovery
sudo ./scripts/rebuilt-proxmox-run-on-proxmox-second.sh
```

## Scripts

| Script | Purpose | Where to Run |
|--------|---------|--------------|
| `rebuilt-proxmox-run-on-pbs-first.sh` | Extract recovery artifacts | PBS-TRUENAS |
| `rebuilt-proxmox-run-on-proxmox-second.sh` | Interactive Proxmox recovery | New Proxmox host |
| `mirror-pbs-main-policy-to-pbs-truenas.sh` | Sync policies PBS-MAIN → PBS-TRUENAS | PBS-TRUENAS |

## Development

```bash
# Run all checks
make check

# Run smoke tests
make test

# Verify structure
make verify

# Clean temp files
make clean
```

## Documentation

- [Disaster Recovery Scenarios](docs/DR-SCENARIOS.md)
- [Key Rules](docs/KEY-RULES.md)

## Requirements

- Proxmox Backup Server 2.x+
- bash 4.0+
- root access on PBS and Proxmox hosts

## License

See [LICENSE](LICENSE)
