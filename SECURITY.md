# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.0.x   | Yes       |

## Security Model

KANSLORDASH is designed with security as a priority:

- **Read-only operations** — All monitoring probes execute read-only commands. The application has no features for remote system modification.
- **No credential storage** — Passwords, private keys, and tokens are never stored by the application. Authentication uses the system SSH client, SSH agent, and `~/.ssh/config`.
- **BatchMode probing** — Health checks use `ssh -o BatchMode=yes -o NumberOfPasswordPrompts=0` to avoid interactive password prompts during automated probes.
- **Local registry only** — Server configurations are stored locally in the user's config directory with restricted file permissions where possible.
- **Input validation** — All user inputs (hostnames, ports, usernames, tags) are validated to prevent injection attacks.
- **No shell interpolation** — SSH commands are executed using `asyncio.create_subprocess_exec` with argument lists, avoiding shell interpretation.

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly:

1. **Do not** open a public GitHub issue
2. Email the maintainers with details of the vulnerability
3. Include steps to reproduce if possible
4. Allow time for assessment and patching before public disclosure

## Best Practices for Users

- Keep your SSH keys secure and use an SSH agent
- Use SSH key authentication instead of passwords where possible
- Restrict SSH access to monitored hosts with appropriate user permissions (read-only where feasible)
- Keep the application and dependencies updated
- Review host configurations regularly
- Use firewall rules to limit SSH access to management networks

## Limitations

- The security model depends on the security of your SSH client, agent, and configuration
- Network connectivity is required for monitoring
- Some features depend on platform capabilities and permissions

## False Positive Reporting

If your antivirus flags KANSLORDASH, please:
1. Verify you downloaded from the official GitHub releases page
2. Check the SHA-256 checksum against published values
3. Report false positives to your AV vendor
4. Open an issue on GitHub with details if you believe it's a true positive
