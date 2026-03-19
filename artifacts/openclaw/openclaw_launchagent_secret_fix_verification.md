# OpenClaw LaunchAgent Secret Fix Verification (Sanitized)

## shell env
- QWEN_API_KEY=SET
- DEEPSEEK_API_KEY=SET

## launchctl env
- QWEN_API_KEY=SET
- DEEPSEEK_API_KEY=SET

## gateway status
Service: LaunchAgent (loaded)
File logs: /tmp/openclaw/openclaw-2026-03-19.log
Command: /opt/homebrew/opt/node@22/bin/node /opt/homebrew/lib/node_modules/openclaw/dist/index.js gateway --port 18789
Service file: ~/Library/LaunchAgents/ai.openclaw.gateway.plist
Service env: OPENCLAW_GATEWAY_PORT=18789

Config (cli): ~/.openclaw/openclaw.json
Config (service): ~/.openclaw/openclaw.json

Gateway: bind=loopback (127.0.0.1), port=18789 (service args)
Probe target: ws://127.0.0.1:18789
Dashboard: http://127.0.0.1:18789/
Probe note: Loopback-only gateway; only local clients can connect.

Runtime: running (pid 6904, state active)
RPC probe: ok

Listening: 127.0.0.1:18789
Troubles: run openclaw status
Troubleshooting: https://docs.openclaw.ai/troubleshooting


## probe qwen-portal
Config        : ~/.openclaw/openclaw.json
Agent dir     : ~/.openclaw/agents/main/agent
Default       : qwen-portal/coder-model
Fallbacks (0) : -
Image model   : -
Image fallbacks (0): -
Aliases (2)   : qwen -> qwen-portal/coder-model, deepseek -> "deepseek-v32/deepseek-chat"
Configured models (3): qwen-portal/coder-model, qwen-portal/vision-model, "deepseek-v32/deepseek-chat"

Auth overview
Auth store    : ~/.openclaw/agents/main/agent/auth-profiles.json
Shell env     : off
Providers w/ OAuth/tokens (1): qwen-portal (1)
- deepseek-v32 effective=models.json:[REDACTED_KEY] | models.json=[REDACTED_KEY] | source=models.json: ~/.openclaw/agents/main/agent/models.json
- qwen-portal effective=profiles:~/.openclaw/agents/main/agent/auth-profiles.json | profiles=1 (oauth=1, token=0, api_key=0) | qwen-portal:default=OAuth | models.json=marker(qwen-oauth) | source=models.json: ~/.openclaw/agents/main/agent/models.json

OAuth/token status
- qwen-portal
  - qwen-portal:default ok expires in 5h

Auth probes
┌─────────────────────────┬─────────────────────────────┬────────────┐
│ Model                   │ Profile                     │ Status     │
├─────────────────────────┼─────────────────────────────┼────────────┤
│ qwen-portal/coder-model │ qwen-portal:default (oauth) │ ok · 2.8s  │
└─────────────────────────┴─────────────────────────────┴────────────┘
Probed 1 target in 2.8s


## probe deepseek-v32
Config        : ~/.openclaw/openclaw.json
Agent dir     : ~/.openclaw/agents/main/agent
Default       : qwen-portal/coder-model
Fallbacks (0) : -
Image model   : -
Image fallbacks (0): -
Aliases (2)   : qwen -> qwen-portal/coder-model, deepseek -> "deepseek-v32/deepseek-chat"
Configured models (3): qwen-portal/coder-model, qwen-portal/vision-model, "deepseek-v32/deepseek-chat"

Auth overview
Auth store    : ~/.openclaw/agents/main/agent/auth-profiles.json
Shell env     : off
Providers w/ OAuth/tokens (1): qwen-portal (1)
- deepseek-v32 effective=models.json:[REDACTED_KEY] | models.json=[REDACTED_KEY] | source=models.json: ~/.openclaw/agents/main/agent/models.json
- qwen-portal effective=profiles:~/.openclaw/agents/main/agent/auth-profiles.json | profiles=1 (oauth=1, token=0, api_key=0) | qwen-portal:default=OAuth | models.json=marker(qwen-oauth) | source=models.json: ~/.openclaw/agents/main/agent/models.json

OAuth/token status
- qwen-portal
  - qwen-portal:default ok expires in 5h

Auth probes
┌────────────────────────────┬────────────────────────┬────────────┐
│ Model                      │ Profile                │ Status     │
├────────────────────────────┼────────────────────────┼────────────┤
│ deepseek-v32/deepseek-chat │ models.json (api_key)  │ ok · 4.4s  │
└────────────────────────────┴────────────────────────┴────────────┘
Probed 1 target in 4.4s

