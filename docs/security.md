# Security and Safety

This project controls local automation around a live game window. Treat it as a privileged local automation surface.

## Default Policy

- Expose semantic tasks, not raw input primitives.
- Require an allowlist for every mutating task or script.
- Refuse unknown task names.
- Allow only one mutating job at a time.
- Keep an emergency stop path available.
- Log task starts, stops, failures, and caller-provided arguments.
- Keep secrets and machine-local paths out of Git.

## Agent Boundary

Agents should call MCP tools. They should not:

- directly send keyboard or mouse events
- modify BetterGI internals
- run arbitrary scripts
- bypass task allowlists
- retry failed automation loops without reading logs

## SSH Boundary

When using `ssh-stdio`, the SSH user should be a dedicated Windows user or a user with the minimum practical privileges.

Recommended practices:

- use key-based auth
- restrict the remote command where practical
- keep the runner under a known install path
- avoid exposing a public network listener

## Logs

Logs can reveal local paths, account names, game state, or screenshots. Do not commit:

- BetterGI logs
- screenshots or captures
- `.env` files
- `*.local.json`
- SSH keys or tokens

## Future Hardening

- Signed runner releases.
- Config schema validation.
- Job audit log with redaction.
- Optional confirmation prompts for high-risk tasks.
- Read-only dry-run mode for inventory and detection.
