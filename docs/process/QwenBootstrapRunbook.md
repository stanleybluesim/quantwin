# Qwen Bootstrap Runbook

## Purpose
本文件定义 OpenClaw 在闭环中如何使用 Qwen 作为首跳引导模型。

## Role Definition
Qwen MUST 作为 bootstrap provider，用于：
- bootstrap
- classify
- quick_plan
- shell_guidance

Qwen MUST NOT 直接承担：
- merge_decision
- independent_review
- 最终审计裁决

## Escalation Rules
以下任务 SHOULD 升级到 ChatGPT：
- architecture
- deep_implementation
- spec_rewrite
- complex_reasoning

以下任务 MUST 走 Grok：
- independent_review

以下任务 MUST 走 GitHub control plane：
- merge_decision

## Error Semantics
### TIMEOUT
- SHOULD 重试至 retry_policy.max_attempts
- 超出后按 fallback_policy.on_timeout 执行

### RATE_LIMIT
- MUST 输出 BLOCKED
- MUST NOT 伪造成功

### AUTH_FAILED
- MUST 输出 ERROR
- MUST 停止当前 provider

### PROVIDER_UNAVAILABLE
- 若路由允许，MAY 升级到 ChatGPT
- 否则 MUST BLOCK

### INVALID_RESPONSE
- MUST 视为失败
- MUST NOT 标记 provider 为 HEALTHY

## Probe Procedure
本地探测命令：
`tools/qw_provider_probe.py --provider qwen-portal --host github.com --port 443 --timeout-sec 5 --auth-env QWEN_API_KEY --output artifacts/devloop/ProviderHealthReport.local.json`

## Output Contract
健康报告 MUST 符合 `contracts/devloop/provider_health.schema.json`。

## Rollback
- 删除本阶段新增契约与 runbook 文件
- 回退当前提交
- 保留 main 分支不变
