> DEPRECATED
> archived under SoT file naming convention v2.7 on 2026-03-27

# 正式任务入口注册 SoT (Source of Truth)
## 编号：SoT-WP-P1-4-20260327-01
## 版本：V3
## 状态：EFFECTIVE

## 0. 文档定位
## 本文件用于**注册并解锁**项目层正式任务 `WP-P1-4`。  
## 本文件在签署生效前，不改变当前冻结结论；签署生效后，仅解锁 `WP-P1-4`，不自动上推任何正式验收或运行时状态。

---

## 1. 正式任务名 (Formal Task Name)
`WP-P1-4: FastStream 异步通信层集成与幂等性验证`

---

## 2. 责任人 (Owner / Accountable Owner)
- **Accountable Owner (问责 Owner)**: `Stanleybluesim`
- **Responsible Owner (执行 Owner)**: `QuantWin AI Agent (OpenClaw)`
- **Governance Reviewer**: `AEF Governance Bot`
- **Review Mode (默认)**: `human_required`

---

## 3. 任务目标 (Goal)
在不改变运行时当前生效状态的前提下，为 QuantWin 建立受 AEF 边界约束的 `FastStream` 异步通信层集成与幂等性验证能力，完成以下最小闭环：

1. 已登记 `Topic` 的注册与校验
2. `idempotency_key` 生成、传播与判重
3. `trace_id / run_id / audit_id / report_id` 的 C-7 追溯挂接
4. 集成测试与门禁记录落库
5. 与 `Traceability Matrix / Metric Specifications / Test Specifications & Gates` 的映射

---

## 4. 产出路径 (Output Path)
- **代码工件**: `src/infrastructure/messaging/faststream_impl/`
- **契约工件**: `contracts/faststream/topic_registry.yaml`
- **契约工件**: `contracts/faststream/idempotency_contract.yaml`
- **测试工件**: `tests/wp_p1_4/idempotency_test_suite.py`
- **文档工件**: `artifacts/wp-p1-4/Integration_Report.md`
- **门禁工件**: `artifacts/wp-p1-4/FastStream_Idempotency_Gate_Record.md`

> 上述路径以本 SoT 注册范围为准；任何超出 `Output Path` 的修改均视为范围蔓延，必须重新注册 SoT。

---

## 5. 进入条件 / 退出条件 (Entry / Exit Conditions)

### 5.1 进入条件 (Entry) — MUST 全部满足
1. 本 SoT 已由 `Accountable Owner` 正式签字确认。
2. 当前冻结状态已继承，且保持：
   - `FORMAL_ACCEPTANCE_REVIEW_READY`
   - `Formal acceptance = NOT ASSERTED`
3. 当前项目层正式下一任务在签署前仍为 `NONE`；本 SoT 的签署行为仅用于解锁 `WP-P1-4`。
4. 开发环境 `QuantWin-Dev-Env` 可访问，且允许在非生产路径执行本任务。
5. 当前运行时 `current-live` 状态未发生切换，且本任务不以切换运行时状态为目标。

### 5.2 退出条件 (Exit) — MUST 全部满足
1. `Topic` 注册表文件已落库并通过校验。
2. `idempotency_contract.yaml` 已落库，并定义判重规则、默认值、错误码、重试、超时、异步语义。
3. `tests/wp_p1_4/` 测试通过率 `100%`。
4. `Integration_Report.md` 已生成，且包含：
   - `Traceability Matrix`
   - `Metric Specifications`
   - `Test Specifications & Gates`
   - `trace_id / run_id / audit_id / report_id`
5. `FastStream_Idempotency_Gate_Record.md` 已生成并记录本轮门禁结果。
6. 无 `Critical` 级别静态代码分析告警。
7. 未调用运行时发布 / 回滚入口；未改写生产 `current-live` 状态。

---

## 6. Contract Execution Semantics

### 6.1 MUST 字段
以下字段 MUST 出现在本任务涉及的契约工件、报告工件或门禁工件中：
- `topic`
- `idempotency_key`
- `trace_id`
- `run_id`
- `audit_id`
- `report_id_policy`
- `egress_mode`
- `formal_acceptance`
- `runtime_publish_state`

### 6.2 默认值
- `review_mode = human_required`
- `formal_acceptance = NOT_ASSERTED`
- `runtime_publish_state = NOT_ASSERTED`
- `report_id = N/A unless report-chain evidence is included`
- `egress_mode = offline`
- `retry_policy = no_automatic_retry`
- `timeout_policy = fail_closed_on_command_timeout`
- `async_semantics = no_acceptance_async_job`

### 6.3 边界条件
1. `FastStream` MUST 作为唯一异步通信层。
2. 所有异步消息 MUST 通过已登记 `Topic` 传递。
3. 所有异步消息 MUST 携带 `idempotency_key`。
4. 工件变更与运行时发布动作 MUST 分离。
5. 本任务 MUST NOT 直接改写生产 `current-live` 状态。
6. 本任务 MUST NOT 声称运行时策略已切换、已生效、已上线。

### 6.4 错误码
- `FS-TOPIC-001`: `TOPIC_NOT_REGISTERED`
- `FS-IDEMP-001`: `IDEMPOTENCY_KEY_MISSING`
- `FS-IDEMP-002`: `IDEMPOTENCY_DUPLICATE_DETECTED`
- `FS-TRACE-001`: `TRACEABILITY_FIELDS_MISSING`
- `FS-RUNTIME-001`: `RUNTIME_PUBLISH_FORBIDDEN_IN_CURRENT_STAGE`
- `FS-VAL-001`: `CONTRACT_VALIDATION_FAILED`
- `FS-GATE-001`: `STATIC_GATE_FAILED`

### 6.5 重试 / 超时 / 幂等 / 异步语义
- **重试**：默认 `no_automatic_retry`。出现契约错误或门禁错误时 MUST `fail_closed`，只允许人工修复后手动重跑。
- **超时**：默认 `fail_closed_on_command_timeout`。任一验收命令超时即视为未通过。
- **幂等**：
  1. 相同 `topic + idempotency_key` 的重复消息 MUST 被判为同一逻辑请求。
  2. 重复请求 MUST NOT 造成重复副作用。
  3. 幂等冲突 MUST 返回 `FS-IDEMP-002`。
- **异步语义**：
  1. 本任务的验收流程不使用 `202 + Location`。
  2. 本任务的验收流程不使用 `job_id` 状态机。
  3. 验收语义为同步校验；异步消息能力仅作为被测对象，不作为验收编排语义。

---

## 7. 验收命令 (Acceptance Commands)

### 7.1 自动化验收 — MUST 全部通过
```
pytest tests/wp_p1_4/ --cov=src/infrastructure/messaging --cov-report=xml

python - <<'PY'
from pathlib import Path
required = [
    Path("contracts/faststream/topic_registry.yaml"),
    Path("contracts/faststream/idempotency_contract.yaml"),
    Path("artifacts/wp-p1-4/Integration_Report.md"),
    Path("artifacts/wp-p1-4/FastStream_Idempotency_Gate_Record.md"),
]
for p in required:
    assert p.exists(), f"missing required artifact: {p}"
print("PASS: required WP-P1-4 artifacts exist")
PY

grep -nE 'topic|FastStream|registered|Scope|Output Path' contracts/faststream/topic_registry.yaml
grep -nE 'idempotency_key|trace_id|run_id|audit_id|report_id_policy|error_codes|retry_policy|timeout_policy|async_semantics' contracts/faststream/idempotency_contract.yaml
grep -nE 'trace_id|run_id|audit_id|report_id|Traceability Matrix|Metric Specifications|Test Specifications & Gates' artifacts/wp-p1-4/Integration_Report.md

semgrep --error --severity ERROR src/infrastructure/messaging tests/wp_p1_4
```

## 8. 不可外推声明 (Non-extrapolation Declaration)

### 8.1 不得外推为
- `FORMALLY_ACCEPTED`
- 正式验收完成
- `runtime current-live state changed`
- QuantWin 全仓 acceptance 完成
- QuantWin 全仓 traceability completion
- 建议新增 ID / `PROPOSED-*` / 临时标签已正式注册

### 8.2 不得混写为
- AEF 全域正式验收结论
- 其他专题的正式结论
- 运行时发布结论
- 上线 / 生效 / 切换完成结论

### 8.3 范围限制
本 SoT 仅代表：
- `WP-P1-4` 的项目层任务注册与治理授权
- 非生产路径下的集成与幂等性验证范围
- 本文件 `Output Path` 内的工件范围

## 9. 签字确认区 (Signature Section)
- `signature_status = EFFECTIVE`
- `confirmed_by = Stanleybluesim`
- `confirmed_at = 2026-03-27`
- [x] 我已阅读并确认本 SoT 的任务范围、进入条件、退出条件、验收命令与不可外推声明完整且准确。
- [x] 我授权依据本 SoT 解锁 `WP-P1-4`。