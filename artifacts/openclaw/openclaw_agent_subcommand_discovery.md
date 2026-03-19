# OpenClaw Agent Subcommand Discovery

## generated_at
2026-03-19T05:39:43Z

## openclaw agents add --help

🦞 OpenClaw 2026.3.8 (3caab92) — I don't judge, but your missing API keys are absolutely judging you.

Usage: openclaw agents add [options] [name]

Add a new isolated agent

Options:
  --agent-dir <dir>             Agent state directory for this agent
  --bind <channel[:accountId]>  Route channel binding (repeatable) (default: [])
  -h, --help                    Display help for command
  --json                        Output JSON summary (default: false)
  --model <id>                  Model id for this agent
  --non-interactive             Disable prompts; requires --workspace (default:
                                false)
  --workspace <dir>             Workspace directory for the new agent

## openclaw agents bind --help

🦞 OpenClaw 2026.3.8 (3caab92) — Like having a senior engineer on call, except I don't bill hourly or sigh audibly.

Usage: openclaw agents bind [options]

Add routing bindings for an agent

Options:
  --agent <id>                  Agent id (defaults to current default agent)
  --bind <channel[:accountId]>  Binding to add (repeatable). If omitted,
                                accountId is resolved by channel defaults/hooks.
                                (default: [])
  -h, --help                    Display help for command
  --json                        Output JSON summary (default: false)

## openclaw agents list
Agents:
- main (default)
  Workspace: ~/.openclaw/workspace
  Agent dir: ~/.openclaw/agents/main/agent
  Model: qwen-portal/coder-model
  Routing rules: 0
  Routing: default (no explicit rules)
Routing rules map channel/account/peer to an agent. Use --bindings for full rules.
Channel status reflects local config/creds. For live health: openclaw channels status --probe.

## openclaw agents bindings
No routing bindings.
