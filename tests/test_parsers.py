from kanslordash.probes.parsers import parse_linux_health, parse_windows_health


def test_parse_linux_health():
    output = """HOSTNAME=las1
OS=linux
UPTIME=147600
LOAD1=0.42
MEM=38
DISK=42
TEMP=48.3
FAILED=2
"""
    snapshot = parse_linux_health(output)
    assert snapshot.error is None
    assert snapshot.hostname == "las1"
    assert snapshot.os == "linux"
    assert snapshot.uptime_seconds == 147600
    assert snapshot.load1 == 0.42
    assert snapshot.mem_percent == 38
    assert snapshot.disk_percent == 42
    assert snapshot.temp_c == 48.3
    assert snapshot.failed_units == 2


def test_parse_linux_health_partial_data_is_not_an_error():
    snapshot = parse_linux_health("HOSTNAME=las1\nLOAD1=0.10\n")
    assert snapshot.error is None
    assert snapshot.hostname == "las1"
    assert snapshot.mem_percent is None


def test_parse_linux_health_empty():
    snapshot = parse_linux_health("")
    assert snapshot.error


def test_parse_windows_health_with_banner():
    output = (
        "Windows PowerShell\n"
        '{"hostname":"LAS2","os":"windows","uptime_seconds":7200,"cpu_percent":14,'
        '"mem_percent":38,"disk_percent":42,"temp_c":null,"failed_units":0,"updates":null}\n'
    )
    snapshot = parse_windows_health(output)
    assert snapshot.error is None
    assert snapshot.hostname == "LAS2"
    assert snapshot.os == "windows"
    assert snapshot.cpu_percent == 14
    assert snapshot.uptime_seconds == 7200
    assert snapshot.failed_units == 0


def test_parse_windows_health_invalid():
    snapshot = parse_windows_health("no json here")
    assert snapshot.error
