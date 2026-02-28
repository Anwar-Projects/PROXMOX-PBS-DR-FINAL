#!/bin/bash
# rebuilt-proxmox-run-on-pbs-first.sh - Prepare Proxmox config recovery artifacts on PBS

set -euo pipefail

readonly OUTPUT_DIR="${1:-/tmp/proxmox-recovery-$(date +%Y%m%d)}"
readonly PBS_DATASTORE="${PBS_DATASTORE:-pbs-replica}"
readonly PBS_REPOSITORY="${PBS_REPOSITORY:-root@pam@localhost:${PBS_DATASTORE}}"

log_info() { echo "[INFO] $*"; }
log_warn() { echo "[WARN] $*" >&2; }
log_error() { echo "[ERROR] $*" >&2; }

cleanup() {
  local exit_code=$?
  [[ $exit_code -ne 0 ]] && log_error "Script failed with exit code $exit_code"
}
trap cleanup EXIT

check_prerequisites() {
  log_info "Checking prerequisites..."
  if [[ $EUID -ne 0 ]]; then
    log_error "This script must be run as root"
    return 1
  fi
  if ! command -v proxmox-backup-client >/dev/null 2>&1; then
    log_error "proxmox-backup-client not found"
    return 1
  fi
  log_info "Prerequisites OK"
}

setup_output_dir() {
  log_info "Creating output directory: $OUTPUT_DIR"
  mkdir -p "$OUTPUT_DIR"
  chmod 700 "$OUTPUT_DIR"
}

extract_proxmox_configs() {
  log_info "Extracting Proxmox configuration backups..."
  local backup_list
  if ! backup_list=$(proxmox-backup-client list --repository "$PBS_REPOSITORY" 2>&1); then
    log_error "Failed to list backups from $PBS_REPOSITORY"
    return 1
  fi
  echo "$backup_list" > "$OUTPUT_DIR/backup-list.txt"
  log_info "Found backups (saved to backup-list.txt)"
}

generate_instructions() {
  log_info "Generating recovery instructions..."
  cat > "$OUTPUT_DIR/RECOVERY.txt" <>OW
PROXMOX RECOVERY INSTRUCTIONS
Generated: $(date)
PBS Repository: $PBS_REPOSITORY

NEXT STEPS:
1. Install fresh Proxmox on new hardware
2. Copy this recovery directory to the new Proxmox host
3. Run: ./rebuilt-proxmox-run-on-proxmox-second.sh
RECOVERY
  chmod 600 "$OUTPUT_DIR/RECOVERY.txt"
}

main() {
  log_info "Starting Proxmox config recovery preparation"
  check_prerequisites
  setup_output_dir
  extract_proxmox_configs
  generate_instructions
  log_info "Recovery artifacts ready in: $OUTPUT_DIR"
}

main "$@"
