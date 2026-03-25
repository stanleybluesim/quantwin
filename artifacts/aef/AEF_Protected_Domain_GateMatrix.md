# AEF_Protected_Domain_GateMatrix

## 1. Formal Object
- task_id: `WP-P1-2`
- task_name: `受保护域边界守卫与门禁代码化`
- owner: `AR / QA / GOV`
- accountable_owner: `GOV`
- scope_layer: `AEF = 工程治理层`
- runtime_layer: `QuantWin = 业务运行层`

## 2. Entry / Exit
### Entry
- Phase 0 completed
- Protected domain, runtime publish boundary, and FastStream-only async constraints must be executable

### Exit
1. `contracts/aef/protected_domain_rules.yaml` landed
2. `tools/aef_boundary_guard.py` landed
3. `artifacts/aef/AEF_Protected_Domain_GateMatrix.md` landed
4. `AEF` MUST NOT directly mutate current live runtime state; this path is explicitly blocked

## 3. Gate Matrix
| Gate | Scope | MUST | Command | Pass Standard | Fail Code |
|---|---|---|---|---|---|
| Gate 0 | Static/Security | Semgrep executable | `semgrep --config ...` | Exit Code = 0 | `AEF-QW-004` |
| Gate 1 | Architecture Contract | executable boundary rules | `python3 tools/aef_boundary_guard.py --rules contracts/aef/protected_domain_rules.yaml --matrix artifacts/aef/AEF_Protected_Domain_GateMatrix.md` | Exit Code = 0 | `AEF-QW-003/004/005/006` |
| Gate-C7 | Traceability | `trace_id/run_id/audit_id` required; `report_id` report-chain only | same as Gate 1 | all required anchors exist | `AEF-QW-002` |
| Gate-Async | Async boundary | FastStream only / Topic required / idempotency_key required | same as Gate 1 | all async constraints present | `AEF-QW-004` |
| Gate-Egress | Egress boundary | `offline-first`; modes only `offline|allowlist` | same as Gate 1 | exact match | `AEF-QW-006` |
| Gate-Runtime | Runtime boundary | runtime changes MUST go through `POST /v1/policy/publish` or `POST /v1/policy/rollback`; direct live-state mutation is forbidden | same as Gate 1 | no forbidden wording and no bypass path | `AEF-QW-003` |

## 4. C-7 / Error / Async
- C-7 required: `trace_id` / `run_id` / `audit_id`
- report-chain only: `report_id`
- error envelope requirement: `ErrorEnvelope.v1`
- formal async semantics for runtime APIs remain: `202 Accepted + Location`
- allowed runtime publish references:
  - `POST /v1/policy/publish`
  - `POST /v1/policy/rollback`
- this guard script is synchronous gate only; it does not publish runtime policy

## 5. Protected Domains
- `auth`
- `policy`
- `report`
- `audit`
- `sandbox`
- `deploy`

## 6. Non-Extrapolation
- NOT runtime governance chain replaced
- NOT runtime publish chain taken over by AEF
- NOT runtime live-state switch asserted
- NOT formal acceptance complete
