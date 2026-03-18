# ChatGPT Runbook

## Purpose
本文件定义 ChatGPT 作为 QuantWin DevLoop 中 specialist execution node 的输入、输出、错误与回滚规则。

## Role Definition
ChatGPT MUST 承担以下高复杂度任务：
- architecture
- deep_implementation
- spec_rewrite
- complex_reasoning

ChatGPT MUST NOT 直接承担：
- merge_decision
- independent_review
- bootstrap/classify/quick_plan 的默认首跳

## Input Contract
输入 MUST 符合 `contracts/devloop/chatgpt_task.schema.json`。

### Required fields
- task_id
- trace_id
- audit_id
- task_type
- title
- objective
- repository
- base_branch
- target_branch
- origin_provider
- escalation_reason
- inputs
- constraints
- requested_outputs
- execution_policy

## Output Contract
输出 MUST 符合 `contracts/devloop/chatgpt_result.schema.json`。

### Required fields
- task_id
- trace_id
- audit_id
- status
- summary
- files_touched
- changes
- commands_to_run
- self_check
- rollback
- generated_at

## Status semantics
### SUCCESS
仅当输出可执行、可审阅、可回滚时使用。

### BLOCKED
缺少输入、约束冲突、或升级条件不成立时 MUST 使用。
不得伪造 SUCCESS。

### ERROR
结构性失败时 MUST 使用。
例如：输出无法满足 schema、回滚缺失、关键字段不一致。

## Idempotency
- `task_id + target_branch` MUST 视为同一逻辑任务。
- 同一逻辑任务重复提交时，结果 MUST 保持可比较，不得无故漂移。

## Timeout
- specialist task MUST 显式携带 `execution_policy.timeout_sec`。
- 默认 900 秒。
- 超时后的重试 SHOULD 由上层编排器控制，不由本契约自动隐式重试。

## MUST rules
- task_id / trace_id / audit_id MUST 在 task/result 中保持一致。
- ChatGPT MUST 输出 self_check。
- ChatGPT MUST 输出 rollback。
- ChatGPT MUST NOT 声称修改了 changes 中不存在的文件。
- ChatGPT MUST NOT 在 BLOCKED/ERROR 场景输出误导性的 SUCCESS。

## SHOULD rules
- summary SHOULD 简洁、面向执行。
- commands_to_run SHOULD 可直接复制执行。
- files_touched SHOULD 与 changes 对齐。

## Rollback
最小安全回滚 MUST 至少覆盖：
- 新增 schema
- 新增 sample
- 新增 runbook
- 新增 escalation policy

## Validation Procedure
- 校验 task sample against task schema
- 校验 result sample against result schema
- 两项必须同时通过，方可进入 PR
