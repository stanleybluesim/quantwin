# Model Routing Policy

## Objective
统一 OpenClaw 的模型路由与失败处理语义。

## Default Routing
- bootstrap/classify/quick_plan/shell_guidance -> qwen-portal
- architecture/deep_implementation/spec_rewrite/complex_reasoning -> chatgpt-openai
- independent_review -> qwen-review-3.5
- merge_decision -> github-control-plane

## Timeouts / Retries
- request_timeout_sec = 45
- max_attempts = 2
- backoff_sec = 3

## Fallback
- on_timeout = retry_then_block
- on_rate_limit = block
- on_provider_unavailable = escalate_to_chatgpt
- on_invalid_response = block

## Circuit Breaker
- open_after_failures = 3
- cooldown_sec = 300
