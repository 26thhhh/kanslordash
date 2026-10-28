# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-10-28

### Added
- Initial release of KANSLORDASH
- Textual TUI dashboard with keyboard navigation
- CLI interface with list/add/remove/check commands
- Read-only fleet monitoring over SSH
- Support for Linux and Windows hosts
- Persistent server registry with atomic writes
- Health metrics collection (CPU, memory, disk, load, uptime)
- Status engine (HEALTHY, DEGRADED, OFFLINE, UNKNOWN, DISABLED)
- Interactive SSH launcher using system SSH client
- Server detail view
- Network view
- Input validation and security controls
- Comprehensive test suite

### Security
- No credential storage - uses system SSH agent/config
- BatchMode SSH probes to prevent interactive prompts
- Safe subprocess execution without shell interpolation
- Input validation to prevent injection
- Restricted registry file permissions
