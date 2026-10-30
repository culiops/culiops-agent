"""logs-status: print the one-line on/off state of the S3 log module. Always exits 0."""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional, Tuple

if __name__ == "__main__":
    # python3 -I drops the script dir from sys.path; add the lib dir that holds this package.
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from s3logs import config, paths  # noqa: E402

MIN_S5CMD = (2, 2, 0)
MIN_DUCKDB = (1, 4, 0)
_VERSION_RE = re.compile(r"v?(\d+)\.(\d+)\.(\d+)")


def _fmt(v: Tuple[int, ...]) -> str:
    return ".".join(str(x) for x in v)


def _tool_version(name: str, args: list) -> Tuple[Optional[str], Optional[Tuple[int, int, int]]]:
    """Return (path, version). path None = not on PATH; version None = unreadable."""
    exe = shutil.which(name)
    if not exe:
        return None, None
    env = {"PATH": os.environ.get("PATH", ""), "HOME": os.environ.get("HOME", "")}
    try:
        r = subprocess.run([exe] + args, stdin=subprocess.DEVNULL, capture_output=True,
                           text=True, timeout=15, env=env)
    except (OSError, subprocess.SubprocessError, UnicodeDecodeError):
        return exe, None
    m = _VERSION_RE.search(r.stdout + "\n" + r.stderr)
    if not m:
        return exe, None
    return exe, (int(m.group(1)), int(m.group(2)), int(m.group(3)))


def status() -> str:
    """Return the single status line (without newline)."""
    cfg_path = paths.config_path()
    if not (cfg_path.exists() or cfg_path.is_symlink()):
        return "S3 log module: off (not configured)"
    try:
        cfg = config.load(cfg_path)
    except config.ConfigError as e:
        return "S3 log module: off (config error: %s)" % e
    if not cfg.datasets:
        return "S3 log module: off (no datasets configured)"

    tools = []
    for name, args, minimum in (("s5cmd", ["version"], MIN_S5CMD), ("duckdb", ["--version"], MIN_DUCKDB)):
        exe, ver = _tool_version(name, args)
        if exe is None:
            return "S3 log module: off (%s missing)" % name
        if ver is None:
            return "S3 log module: off (%s version unreadable)" % name
        if ver < minimum:
            return "S3 log module: off (%s %s < %s)" % (name, _fmt(ver), _fmt(minimum))
        tools.append("%s %s" % (name, _fmt(ver)))

    ds = ", ".join("%s[%s]" % (d.name, d.type) for d in cfg.datasets.values())
    return "S3 log module: on (datasets: %s; %s)" % (ds, ", ".join(tools))


def main(argv: Optional[list] = None) -> int:
    print(status())
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
