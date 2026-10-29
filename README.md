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

## Windows — Download and Run

**Recommended for most Windows users (no Python required):**

1. Go to the [GitHub Releases](https://github.com/26thhhh/kanslordash/releases) page.
2. Download `KANSLORDASH-v1.0.0-windows-x64.zip`.
3. Extract all files to a folder (e.g., `C:\Tools\KANSLORDASH\` or Desktop).
4. Double-click `KANSLORDASH.exe` to launch the dashboard.
5. Press `A` to add your first server and start monitoring.

### Requirements
- Windows 10 or Windows 11 (x64)
- [OpenSSH Client](https://learn.microsoft.com/en-us/windows-server/administration/openssh/openssh_install_firstuse) installed (available in modern Windows; can be enabled via Settings/Optional Features)
- SSH access to the hosts you want to monitor
- Network connectivity to those hosts

### SSH Authentication
KANSLORDASH uses your system OpenSSH client. No passwords or keys are stored in the app:
- Use SSH keys with your SSH agent (`ssh-add`) or `~/.ssh/config`
- When launching SSH from the app (`S` key), you'll be prompted in the terminal as normal
- The app uses `ssh -o BatchMode=yes` for read-only monitoring probes

### Where is configuration stored?
User settings and the server registry are stored in your Windows user config directory (e.g., `%LOCALAPPDATA%\kanslordash\`), not in the extracted ZIP folder. Your configuration persists across updates/extractions.

### Windows SmartScreen warning
When first launching an unsigned executable downloaded from the internet, Windows may show a SmartScreen warning. This is normal for unsigned apps. You can click "More info" → "Run anyway" if you trust the source. **Do not disable Windows security features.**

### Troubleshooting (Windows)
- **App closes immediately**: Run from Command Prompt/Terminal to see any error messages
- **SSH not found**: Install OpenSSH Client via Windows Optional Features
- **Permission denied**: Ensure your SSH key is loaded or use key-based auth
- **Terminal display issues**: Use Windows Terminal for best Unicode/colors support (falls back to cmd/conhost)

### Developer installation
If you want to run from source on Windows, see the Installation section above. The source version works on Windows, Linux, and macOS.

## Antivirus & Windows SmartScreen Notes

KANSLORDASH is open-source and auditable. Some antivirus engines may flag PyInstaller-packaged Python applications as false positives due to heuristic detection.

- **Microsoft Defender:** Generally does not flag KANSLORDASH
- **SmartScreen:** May show "Unknown Publisher" since the executable is not code-signed (code signing requires a paid certificate)
- **VirusTotal:** Heuristic detections are possible on packed executables

**Recommendations:**
- Download only from the official [GitHub repository](https://github.com/26thhhh/kanslordash)
- Verify the SHA-256 checksum of downloaded files
- Review the source code yourself — it's fully open source
- Code signing is planned if resources become available, but is not required for the software to function safely

The application has no telemetry, no network calls to external services, and only connects to SSH hosts you explicitly configure.

### Verify download integrity (PowerShell)
After downloading the ZIP, verify its SHA-256 checksum:

```powershell
$zip = "KANSLORDASH-v1.0.0-windows-x64.zip"
$expected = (Get-Content "$zip.sha256").Split(" ")[0]
$actual = (Get-FileHash -Algorithm SHA256 $zip).Hash
if ($actual -eq $expected) { Write-Host "Checksum OK" } else { Write-Host "Checksum MISMATCH" }
```

## Download (Windows)

**Recommended:** Download the installer from the [latest release](https://github.com/26thhhh/kanslordash/releases/latest).

- **[KANSLORDASH-Setup-x64.exe](https://github.com/26thhhh/kanslordash/releases/latest/download/KANSLORDASH-Setup-x64.exe)** — Windows 10/11 x64 installer (per-user, no admin required). Creates Start Menu shortcut and optional Desktop shortcut.
- **[KANSLORDASH-v1.0.0-windows-x64.zip](https://github.com/26thhhh/kanslordash/releases/latest/download/KANSLORDASH-v1.0.0-windows-x64.zip)** — Portable alternative (extract and run `KANSLORDASH.exe` directly).

### Installation
1. Download `KANSLORDASH-Setup-x64.exe` from the latest release
2. Run the installer (unsigned — Windows SmartScreen may show a warning; click "More info" → "Run anyway" if trusted)
3. Choose install location (defaults to user app directory)
4. Launch from Start Menu or optionally from installer checkbox
5. Add servers with `A` key and start monitoring

### Portable
1. Download and extract the ZIP
2. Double-click `KANSLORDASH.exe` in the extracted folder
3. Configuration is stored in `%LOCALAPPDATA%\kanslordash\`

### Uninstall
Use Windows Settings → Apps or Control Panel. Your configuration in `%LOCALAPPDATA%\kanslordash\` is preserved during uninstall.

### Checksum verification
Download both the file and its `.sha256` sidecar, then verify in PowerShell:
```powershell
$zip = "KANSLORDASH-Setup-x64.exe"
$expected = (Get-Content "$zip.sha256").Split(" ")[0]
$actual = (Get-FileHash -Algorithm SHA256 $zip).Hash
if ($actual -eq $expected) { "OK" } else { "MISMATCH" }
```

*Note:* The download links above become functional after the first release is published. The installer is unsigned and may trigger SmartScreen warnings — this is expected and does not mean the software is malicious. Do not disable antivirus or Windows security protections.
