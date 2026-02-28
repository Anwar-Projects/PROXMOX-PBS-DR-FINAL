#!/bin/bash
# Smoke tests for Proxmox PBS DR scripts

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && cd .. && pwd)"
FAILED=0
PASSED=0

log_info() { echo "[TEST] $*"; }
log_pass() { echo "[PASS] $*"; ((PASSED++)) || true; }
log_fail() { echo "[FAIL] $*"; ((FAILED++)) || true; }

test_file_exists() {
  local file="$1"
  if [[ -f "$file" ]]; then
    log_pass "File exists: $file"
    return 0
  else
    log_fail "File missing: $file"
    return 1
  fi
}

test_dir_exists() {
  local dir="$1"
  if [[ -d "$dir" ]]; then
    log_pass "Directory exists: $dir"
    return 0
  else
    log_fail "Directory missing: $dir"
    return 1
  fi
}

test_file_executable() {
  local file="$1"
  if [[ -x "$file" ]]; then
    log_pass "File is executable: $(basename "$file")"
    return 0
  else
    log_fail "File not executable: $(basename "$file")"
    return 1
  fi
}

test_script_syntax() {
  local script="$1"
  if bash -n "$script" 2>/dev/null; then
    log_pass "Syntax OK: $(basename "$script")"
    return 0
  else
    log_fail "Syntax error: $(basename "$script")"
    return 1
  fi
}

main() {
  log_info "Starting smoke tests..."
  log_info "======================================"
  
  # Test directory structure
  log_info "Testing directory structure..."
  test_dir_exists "$SCRIPT_DIR/scripts"
  test_dir_exists "$SCRIPT_DIR/cron"
  test_dir_exists "$SCRIPT_DIR/docs"
  test_dir_exists "$SCRIPT_DIR/tests"
  
  # Test scripts exist
  log_info "Testing scripts..."
  test_file_exists "$SCRIPT_DIR/scripts/rebuilt-proxmox-run-on-pbs-first.sh"
  test_file_exists "$SCRIPT_DIR/scripts/rebuilt-proxmox-run-on-proxmox-second.sh"
  test_file_exists "$SCRIPT_DIR/scripts/mirror-pbs-main-policy-to-pbs-truenas.sh"
  
  # Test scripts are executable
  log_info "Testing executability..."
  test_file_executable "$SCRIPT_DIR/scripts/rebuilt-proxmox-run-on-pbs-first.sh"
  test_file_executable "$SCRIPT_DIR/scripts/rebuilt-proxmox-run-on-proxmox-second.sh"
  test_file_executable "$SCRIPT_DIR/scripts/mirror-pbs-main-policy-to-pbs-truenas.sh"
  
  # Test script syntax
  log_info "Testing script syntax..."
  test_script_syntax "$SCRIPT_DIR/scripts/rebuilt-proxmox-run-on-pbs-first.sh"
  test_script_syntax "$SCRIPT_DIR/scripts/rebuilt-proxmox-run-on-proxmox-second.sh"
  test_script_syntax "$SCRIPT_DIR/scripts/mirror-pbs-main-policy-to-pbs-truenas.sh"
  
  # Test config files
  log_info "Testing configuration files..."
  test_file_exists "$SCRIPT_DIR/.shellcheckrc"
  test_file_exists "$SCRIPT_DIR/Makefile"
  test_file_exists "$SCRIPT_DIR/cron/pbs-policy-mirror.cron"
  
  log_info "======================================"
  log_info "Results: $PASSED passed, $FAILED failed"
  
  if [[ $FAILED -gt 0 ]]; then
    echo ""
    log_fail "SOME TESTS FAILED"
    exit 1
  else
    echo ""
    log_pass "ALL TESTS PASSED"
    exit 0
  fi
}

main
