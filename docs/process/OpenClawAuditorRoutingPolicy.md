# OpenClaw Auditor Routing Policy

## Objective
定义 OpenClaw 在 Auditor / complex_reasoning 场景下引入 DeepSeek V3.2 的正式路由策略、边界、失败语义、追溯要求与回滚方式。

## Current Baseline
当前默认路由基线保持不变：
- bootstrap/classify/quick_plan/shell_guidance -> qwen-portal
- architecture/deep_implementation/spec_rewrite/complex_reasoning -> chatgpt-openai
- independent_review -> qwen-review-3.5
- merge_decision -> github-control-plane

## Target Formalization
本专题目标态仅限：
- 将 DeepSeek V3.2 (`deepseek-v32/deepseek-chat`) 明确挂到 Auditor / complex_reasoning 链路
- 保持 qwen-portal 为当前 bootstrap 主基线
- 不切 primary model
- 不直接把 DeepSeek 投入 QuantWin 真实开发任务

## Scope Boundary
### MUST
- 本专题只修改工程治理层工件：文档、样例、验收记录
- 不直接修改线上当前生效的运行时策略状态
- 不改变 merge_decision -> github-control-plane
- 不改变 independent_review -> qwen-review-3.5
- 不改变 bootstrap/classify/quick_plan/shell_guidance -> qwen-portal

### MUST NOT
- MUST NOT 切换 primary model
- MUST NOT 将 DeepSeek 直接接入 QuantWin 真实开发任务
- MUST NOT 绕过正式治理链路去生效运行时策略
- MUST NOT 将 reviewer 结果自动视为 merge PASS

## Routing Policy
### Current-State Effective Route
- complex_reasoning -> chatgpt-openai

### Formalized Target Route
- Auditor / complex_reasoning -> deepseek-v32/deepseek-chat

### Role Separation
- qwen-portal: bootstrap provider
- qwen-review-3.5: reviewer provider
- github-control-plane: merge decision control plane
- deepseek-v32/deepseek-chat: auditor / complex reasoning target provider

## Timeout / Retry
- request_timeout_sec = 45
- max_attempts = 2
- backoff_sec = 3

## Error Semantics
### TIMEOUT
- MUST retry until max_attempts exhausted
- MUST block route after retries exhausted

### RATE_LIMIT
- MUST block
- MAY retry only within the defined retry policy

### AUTH_FAILED
- MUST output ERROR
- MUST stop current provider

### PROVIDER_UNAVAILABLE
- bootstrap route MAY escalate to ChatGPT when policy allows
- reviewer route MUST block auto-merge and require human intervention
- auditor route MUST fail-closed until route health is restored

### INVALID_RESPONSE
- MUST be treated as failure
- MUST NOT mark provider as HEALTHY
- reviewer route MAY downgrade to local rule checks
- downgraded local rule checks MUST NOT be treated as automatic PASS

## Traceability
所有本专题相关工件与后续验收记录 MUST 挂接以下字段：
- trace_id
- run_id
- audit_id
- report_id

### Minimum Rules
- trace_id MUST be present and non-empty
- run_id MUST be present and non-empty when execution is involved
- audit_id MUST be present and non-empty for auditable artifacts
- report_id MUST be present for report-chain artifacts only

## Rollback
- 删除本专题新增的 Auditor routing formalization 文档与样例
- 回退当前提交
- 保留 main 分支不变
- 不触发任何运行时策略发布动作
