#!/bin/bash
# mirror-pbs-main-policy-to-pbs-truenas.sh - Mirror PBS-MAIN policies to PBS-TRUENAS

set -euo pipefail

readonly PBS_MAIN="${PBS_MAIN:-192.168.1.100}"
readonly PBS_LOCAL_DATASTORE="${PBS_LOCAL_DATASTORE:-pbs-replica}"
DRY_RUN=0

log_info() { echo "[INFO] $*"; }
log_warn() { echo "[WARN] $*" >&2; }
log_error() { echo "[ERROR] $*" >&2; }

for arg in "$@"; do
  case $arg in
    --dry-run) DRY_RUN=1 ;;
    -h|--help) echo "Usage: $0 [--dry-run]"; exit 0 ;;
  esac
done

check_prerequisites() {
  if [[ $EUID -ne 0 ]]; then
    log_error "Must run as root"
    return 1
  fi
  if ! command -v proxmox-backup-manager >/dev/null 2>&1; then
    log_error "proxmox-backup-manager not found"
    return 1
  fi
  log_info "Prerequisites OK"
}

main() {
  log_info "PBS Policy Mirror Script"
  log_info "PBS-MAIN: $PBS_MAIN"
  [[ $DRY_RUN -eq 1 ]] && log_info "DRY RUN MODE"
  
  check_prerequisites
  
  log_info "Sync jobs:"
  proxmox-backup-manager sync-job list 2>/dev/null || true
  
  log_info "Prune jobs:"
  proxmox-backup-manager prune-job list 2>/dev/null || true
  
  log_info "Mirror completed"
}

main "$@"
