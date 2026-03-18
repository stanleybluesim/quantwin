# Qwen to ChatGPT Escalation Policy

## Objective
定义 OpenClaw 中 Qwen bootstrap provider 升级到 ChatGPT specialist node 的边界与触发条件。

## MUST escalate to ChatGPT
以下任务类型 MUST 由 Qwen 升级到 ChatGPT：
- architecture
- deep_implementation
- spec_rewrite
- complex_reasoning

## MAY escalate to ChatGPT
以下情况 MAY 触发升级：
- Qwen 返回信息不足，但任务仍可继续
- Qwen 识别到需要更高质量的结构化设计输出
- Provider route policy 允许的临时专家升级

## MUST NOT escalate to ChatGPT
以下情况 MUST NOT 自动升级：
- merge_decision
- independent_review
- 权限不足
- 输入缺失到无法形成 specialist task

## Failure semantics
### Qwen timeout
- SHOULD 按 bootstrap route policy 先重试
- 重试后仍失败时，只有当任务类型允许时才 MAY 升级到 ChatGPT

### Qwen rate limit
- MUST BLOCK
- 不得自动绕过为 ChatGPT 成功执行

### Qwen provider unavailable
- 若 task_type 在 specialist 范围内，可按路由策略升级到 ChatGPT
- 否则 MUST BLOCK

## Required handoff fields
升级到 ChatGPT 时，MUST 保留：
- task_id
- trace_id
- run_id
- audit_id
- origin_provider=qwen-portal
- escalation_reason

## Transport and egress boundary
- 若升级通过异步 handoff 传递，MUST 经 FastStream 已登记 Topic 完成。
- 若升级通过异步 handoff 传递，每条消息 MUST 包含 `idempotency_key`。
- `execution_policy.egress_mode` MUST 为 `offline` 或 `allowlist`，默认 MUST 为 `offline`。
- 升级到 ChatGPT specialist 不得等同于运行时策略生效动作，不得直接修改线上当前生效策略状态。

## Audit requirement
所有升级动作 MUST 形成可审计记录，并可由上层 OpenClaw 编排器回溯。
