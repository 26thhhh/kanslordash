# KANSLORDASH

A lightweight, read-only fleet and network health dashboard for monitoring remote Linux and Windows hosts over SSH.

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## Overview

KANSLORDASH is a keyboard-driven TUI (Textual/Rich) application designed for monitoring server fleets from a trusted management workstation. It focuses on visibility without remote system modification — all monitoring is read-only, and SSH sessions are launched interactively through your existing SSH client.

## Key Features

- **Read-only monitoring** — Probes run non-destructive commands; no remote changes are made
- **Persistent server registry** — Local JSON registry with atomic writes and restricted permissions
- **Dual interface** — Interactive TUI dashboard or CLI subcommands for scripting
- **Multi-OS support** — Node abstractions for Linux, Windows, and unknown hosts
- **Health insights** — CPU/memory/disk/load/uptime, failed units, pending updates (where available)
- **Status logic** — Clear states: HEALTHY, DEGRADED, OFFLINE, UNKNOWN, DISABLED
- **Quick SSH access** — Press `s` to open an interactive SSH session in your terminal using your existing SSH config/agent
- **Keyboard-first navigation** — Efficient workflow with shortcuts

## Architecture & Tech Stack

- **Language:** Python 3.11+
- **TUI:** [Textual](https://textual.textualize.io/) >= 8.0, < 9.0
- **Rich output:** [Rich](https://rich.readthedocs.io/)
- **Config paths:** [platformdirs](https://github.com/platformdirs/platformdirs)
- **Transport:** OpenSSH client (`ssh`) — uses your local SSH agent and configuration
- **Packaging:** [hatchling](https://hatch.pypa.io/)

The codebase is organized into `models`, `registry`, `config`, `nodes/` (OS abstractions), `probes/` (SSH/network), `status`, `monitor`, and `ui/` (Textual screens).

## Installation

### Requirements
- Python 3.11 or newer
- OpenSSH client installed and available on `PATH` (`ssh` command)
- Network access to monitored hosts (SSH reachable)

### From source (recommended)

```bash
# Clone the repository
git clone https://github.com/26thhhh/kanslordash.git
cd kanslordash

# Create and activate virtual environment
python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows (PowerShell)
# .\.venv\Scripts\Activate.ps1

# Install in development mode
pip install -e ".[dev]"
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv sync
```

## Usage

### Launch the TUI
```bash
kanslordash
```

### CLI commands
```bash
# List registered servers
kanslordash list

# Add a server
kanslordash add "Web-01" 203.0.113.10 --os linux --username ops --port 22

# Remove a server (requires confirmation)
kanslordash remove "Web-01" --yes

# Run a one-time read-only check
kanslordash check
kanslordash check "Web-01" --json
```

Use `--registry /path/to/servers.json` or set `KANSLORDASH_CONFIG_DIR` to override the config location.

## SSH Authentication

KANSLORDASH **does not** store passwords or private keys. Authentication relies on your existing SSH setup:
- SSH keys loaded in your SSH agent (`ssh-agent`)
- `~/.ssh/config` Host entries and settings
- Standard SSH authentication prompts in your terminal when needed

When you press `s` (or "Open SSH") in the TUI, the app suspends and launches your system `ssh` client interactively — you'll be prompted in the same terminal as normal.

## Keyboard Shortcuts (TUI)

| Key | Action |
|---|---|
| `A` | Add server |
| `E` | Edit server |
| `R` | Remove server |
| `S` | Open SSH session |
| `D` | View server details |
| `N` | Network view |
| `T` | Troubleshoot (read-only info) |
| `F5` | Refresh |
| `Q` | Quit |

## Health Monitoring & States

| State | Meaning |
|---|---|
| `HEALTHY` | Reachable, SSH open, probes succeeded within thresholds |
| `DEGRADED` | SSH reachable but health data incomplete/auth issues/threshold concerns |
| `OFFLINE` | Host not reachable on network/SSH port |
| `UNKNOWN` | Not yet checked or cannot determine state |
| `DISABLED` | Server marked disabled (not actively monitored) |

Monitoring is strictly read-only. The "Troubleshoot" action provides information only — it does not execute remediation commands.

## Configuration

By default, the server registry is stored at:
- **Linux:** `~/.config/kanslordash/servers.json`
- **macOS:** `~/Library/Application Support/kanslordash/servers.json`
- **Windows:** `%LOCALAPPDATA%\kanslordash\servers.json`

See `config.example.json` for a sanitized example structure. User configurations are never included in this repository.

## Security Model & Limitations

- **Read-only by design** — No remote configuration changes or command execution that modifies systems
- **No credential storage** — Uses system SSH client and agent
- **Local-only registry** — Host list stays on your machine
- **BatchMode probing** — Health checks use `ssh -o BatchMode=yes` to avoid interactive prompts
- **Input validation** — Hostnames/ports/usernames/tags are validated to prevent injection
- **Permissions** — Registry files are created with restrictive permissions where possible

**Limitations:**
- Requires SSH access to monitored hosts
- Some health metrics depend on OS and available commands (Linux is most comprehensive; Windows support varies)
- ICMP/ping availability depends on platform and permissions
- No built-in secret management — relies on SSH agent/config

## Troubleshooting

- **SSH permission denied during checks** — Ensure your SSH key is loaded in the agent or use `~/.ssh/config`. Interactive SSH (`s`) will prompt normally.
- **Host shows OFFLINE** — Check network connectivity, firewall, and SSH port.
- **Host shows DEGRADED** — SSH is reachable but probes failed or returned partial data. Check auth and host permissions for read-only commands.
- **No data after first launch** — Press `F5` or wait for auto-refresh to collect health data.

## Roadmap

- [ ] Improved Windows probe coverage
- [ ] Export reports (JSON/CSV)
- [ ] Custom probe scripts (read-only)
- [ ] Additional themes
- [ ] Plugin system (carefully sandboxed)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines. All contributions must maintain the read-only security model.

## License

MIT License — see [LICENSE](LICENSE) for details.
