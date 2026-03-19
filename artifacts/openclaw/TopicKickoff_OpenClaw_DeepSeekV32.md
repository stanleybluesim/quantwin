# TopicKickoff

## Topic
openclaw-deepseek-v32-provider

## Goal
在不影响 qwen-portal 现有 worker 基线的前提下，为 OpenClaw 增加 DeepSeek V3.2 custom OpenAI-compatible provider 接入路径，后续用于 AEF Auditor / complex reasoning / architecture review 链路。

## SoT
- AEF 协议 V10.4
- ADR-AEF-015
- OpenClaw 主机配置.txt
- vnpy项目分析.txt
- 本轮终端发现记录
- 用户提供的 DeepSeek baseUrl / model_id 输入

## Boundary
- 只改 OpenClaw 工程配置与发现/验证工件
- 不改 QuantWin 运行时当前生效策略状态
- 不删除 qwen-portal 现有配置
- 不切换 primary model
- 本轮只接 DeepSeek V3.2，不接 V4

## Acceptance
- 已建立专题分支
- 已新增 DeepSeek V3.2 custom provider
- 已新增 DeepSeek 模型别名
- openclaw config validate PASS
- openclaw models list 可见 deepseek-v32/deepseek-chat
- openclaw models status --probe-provider deepseek-v32 返回可审阅结果

## Traceability
- REQ-OCLAW-REBUILD-003
- ADR-OCLAW-REBUILD-002
- TC-OCLAW-REBUILD-027
- TC-OCLAW-REBUILD-028
