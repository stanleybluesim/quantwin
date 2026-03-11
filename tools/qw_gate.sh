#!/usr/bin/env bash
# qw_gate.sh - QuantWin Delivery Gate (MRE: compileall + pytest + ruff)
# Traceability: run_id | trace_id | audit_id

set -euo pipefail

# === Traceability IDs ===
RUN_ID="${RUN_ID:-$(date +%Y%m%d%H%M%S)}"
TRACE_ID="${TRACE_ID:-$(uuidgen 2>/dev/null || echo "${RUN_ID}-$(shuf -i 1000-9999 -n 1)}")}"
AUDIT_ID="${AUDIT_ID:-${RUN_ID}}"

# === Configuration ===
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
LOG_DIR="${PROJECT_ROOT}/.gate_logs"
TIMESTAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

# === Logging ===
log() {
    echo "[${TIMESTAMP}] [run:${RUN_ID}] [trace:${TRACE_ID}] [audit:${AUDIT_ID}] $*"
}

log_audit() {
    local level="$1"; shift
    echo "[${TIMESTAMP}] [${level}] [run:${RUN_ID}] [trace:${TRACE_ID}] [audit:${AUDIT_ID}] $*" | tee -a "${LOG_DIR}/gate_audit.log"
}

# === Setup ===
setup() {
    log "Initializing gate run..."
    mkdir -p "${LOG_DIR}"
    
    # Write run metadata
    cat > "${LOG_DIR}/run_${RUN_ID}.meta" <<EOF
run_id=${RUN_ID}
trace_id=${TRACE_ID}
audit_id=${AUDIT_ID}
timestamp=${TIMESTAMP}
project_root=${PROJECT_ROOT}
EOF
    
    log_audit "INFO" "Gate session initialized"
}

# === Gate Checks (MRE) ===
gate_compileall() {
    log "Running compileall check..."
    cd "${PROJECT_ROOT}"
    
    if python -m compileall -q . 2>&1; then
        log_audit "INFO" "compileall: PASS"
        return 0
    else
        log_audit "ERROR" "compileall: FAIL"
        return 1
    fi
}

gate_pytest() {
    log "Running pytest check..."
    cd "${PROJECT_ROOT}"
    
    if pytest -q --tb=short 2>&1; then
        log_audit "INFO" "pytest: PASS"
        return 0
    else
        log_audit "ERROR" "pytest: FAIL"
        return 1
    fi
}

gate_ruff() {
    log "Running ruff check..."
    cd "${PROJECT_ROOT}"
    
    if command -v ruff &>/dev/null; then
        if ruff check . --quiet 2>&1; then
            log_audit "INFO" "ruff: PASS"
            return 0
        else
            log_audit "ERROR" "ruff: FAIL"
            return 1
        fi
    else
        log_audit "WARN" "ruff not installed, skipping..."
        return 0
    fi
}

# === Main Gate ===
main() {
    setup
    
    local exit_code=0
    
    gate_compileall || exit_code=1
    gate_pytest || exit_code=1
    gate_ruff || exit_code=1
    
    if [[ ${exit_code} -eq 0 ]]; then
        log_audit "INFO" "Gate PASSED - All checks successful"
        echo "${TRACE_ID}" > "${LOG_DIR}/last_passed_trace"
    else
        log_audit "ERROR" "Gate FAILED - One or more checks failed"
    fi
    
    # Write final audit record
    cat >> "${LOG_DIR}/gate_audit.log" <<EOF
---
run_id=${RUN_ID}
trace_id=${TRACE_ID}
audit_id=${AUDIT_ID}
exit_code=${exit_code}
timestamp_end=$(date -u +%Y-%m-%dT%H:%M:%SZ)
---
EOF
    
    return ${exit_code}
}

main "$@"
