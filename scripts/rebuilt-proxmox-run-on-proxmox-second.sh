#!/bin/bash
# rebuilt-proxmox-run-on-proxmox-second.sh - Interactive Proxmox recovery script

set -euo pipefail

readonly RECOVERY_DIR="${1:-/tmp/proxmox-recovery}"
readonly PBS_REPOSITORY="${PBS_REPOSITORY:-root@pam@pbs-truenas:pbs-replica}"

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
    log_error "proxmox-backup-client not installed"
    return 1
  fi
  log_info "Prerequisites OK"
}

show_menu() {
  echo ""
  echo "======================================"
  echo "  Proxmox Recovery Wizard"
  echo "======================================"
  echo "  1) OS-only recovery"
  echo "  2) Full VM restore"
  echo "  3) List available backups"
  echo "  4) Exit"
  echo "======================================"
}

list_backups() {
  log_info "Listing available backups from $PBS_REPOSITORY..."
  proxmox-backup-client list --repository "$PBS_REPOSITORY" || log_error "Failed to list backups"
}

os_recovery() {
  log_info "Starting OS-only recovery..."
  read -rp "Continue? (yes/no): " confirm
  [[ "$confirm" == "yes" ]] || { log_info "Aborted"; return 0; }
  list_backups
  read -rp "Enter backup snapshot to restore: " backup_id
  [[ -n "$backup_id" ]] || { log_error "No backup specified"; return 1; }
  log_info "OS recovery completed (simulation mode)"
}

vm_recovery() {
  log_info "Starting full VM restore..."
  read -rp "Continue? (yes/no): " confirm
  [[ "$confirm" == "yes" ]] || { log_info "Aborted"; return 0; }
  list_backups
  read -rp "Enter VM backup snapshot to restore: " backup_id
  [[ -n "$backup_id" ]] || { log_error "No backup specified"; return 1; }
  log_info "VM restore completed (simulation mode)"
}

main() {
  log_info "Proxmox Recovery Script"
  check_prerequisites
  
  while true; do
    show_menu
    read -rp "Enter choice [1-4]: " choice
    case $choice in
      1) os_recovery ;;
      2) vm_recovery ;;
      3) list_backups ;;
      4) log_info "Exiting"; exit 0 ;;
      *) log_error "Invalid choice: $choice" ;;
    esac
  done
}

main "$@"
