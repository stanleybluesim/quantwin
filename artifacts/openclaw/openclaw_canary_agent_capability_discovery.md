# OpenClaw Canary Agent Capability Discovery

## generated_at
2026-03-19T05:30:05Z

## openclaw agents --help

🦞 OpenClaw 2026.3.8 (3caab92) — Like having a senior engineer on call, except I don't bill hourly or sigh audibly.

Usage: openclaw agents [options] [command]

Manage isolated agents (workspaces + auth + routing)

Options:
  -h, --help    Display help for command

Commands:
  add           Add a new isolated agent
  bind          Add routing bindings for an agent
  bindings      List routing bindings
  delete        Delete an agent and prune workspace/state
  list          List configured agents
  set-identity  Update an agent identity (name/theme/emoji/avatar)
  unbind        Remove routing bindings for an agent

Docs: https://docs.openclaw.ai/cli/agents


## openclaw models set --help

🦞 OpenClaw 2026.3.8 (3caab92) — You had me at 'openclaw gateway start.'

Usage: openclaw models set [options] <model>

Set the default model

Arguments:
  model       Model id or alias

Options:
  -h, --help  Display help for command

## openclaw agent --help

🦞 OpenClaw 2026.3.8 (3caab92) — I've read more man pages than any human should—so you don't have to.

Usage: openclaw agent [options]

Run an agent turn via the Gateway (use --local for embedded)

Options:
  --agent <id>               Agent id (overrides routing bindings)
  --channel <channel>        Delivery channel:
                             last|telegram|whatsapp|discord|irc|googlechat|slack|signal|imessage|line|feishu|nostr|msteams|mattermost|nextcloud-talk|matrix|bluebubbles|zalo|zalouser|synology-chat|tlon
                             (omit to use the main session channel)
  --deliver                  Send the agent's reply back to the selected channel
                             (default: false)
  -h, --help                 Display help for command
  --json                     Output result as JSON (default: false)
  --local                    Run the embedded agent locally (requires model
                             provider API keys in your shell) (default: false)
  -m, --message <text>       Message body for the agent
  --reply-account <id>       Delivery account id override
  --reply-channel <channel>  Delivery channel override (separate from routing)
  --reply-to <target>        Delivery target override (separate from session
                             routing)
  --session-id <id>          Use an explicit session id
  -t, --to <number>          Recipient number in E.164 used to derive the
                             session key
  --thinking <level>         Thinking level: off | minimal | low | medium | high
  --timeout <seconds>        Override agent command timeout (seconds, default
                             600 or config value)
  --verbose <on|off>         Persist agent verbose level for the session

Examples:
  openclaw agent --to +15555550123 --message "status update"
    Start a new session.
  openclaw agent --agent ops --message "Summarize logs"
    Use a specific agent.
  openclaw agent --session-id 1234 --message "Summarize inbox" --thinking medium
    Target a session with explicit thinking level.
  openclaw agent --to +15555550123 --message "Trace logs" --verbose on --json
    Enable verbose logging and JSON output.
  openclaw agent --to +15555550123 --message "Summon reply" --deliver
    Deliver reply.
  openclaw agent --agent ops --message "Generate report" --deliver --reply-channel slack --reply-to "#reports"
    Send reply to a different channel/target.

Docs: https://docs.openclaw.ai/cli/agent
