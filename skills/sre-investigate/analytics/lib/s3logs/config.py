"""Parse logs.env. The file is parsed line by line, never sourced by a shell.

Caps and every other setting come from the file or the defaults below, never
from environment variables.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Dict, Optional, Tuple

from s3logs import paths
from s3logs.validate import Refused, bucket, dataset_name, pos_int, safe_key

DATASET_TYPES = ("cloudfront", "alb", "waf")

DEFAULT_MAX_MB = 200
DEFAULT_RUN_MAX_MB = 1024
DEFAULT_DAY_MAX_MB = 2048
DEFAULT_MARKER_TTL_S = 1800
DEFAULT_IDENTITY_COOKIES = ("session", "sessionid", "sid", "jsessionid", "phpsessid", "connect.sid")
DEFAULT_IDENTITY_HEADERS = ("authorization", "x-api-key")
DEFAULT_SENSITIVE_PARAMS = (
    "token", "access_token", "id_token", "refresh_token", "code", "password", "passwd", "pwd",
    "secret", "key", "api_key", "apikey", "signature", "sig", "auth", "session", "sessionid",
    "email", "phone",
)

_MAX_FILE_BYTES = 64 * 1024
_LINE_RE = re.compile(r"([A-Za-z][A-Za-z0-9_-]*)=([A-Za-z0-9_.,:/{}@+=-]*)")
_COMMENT_RE = re.compile(r"(?:^|\s)#.*$")
_REGION_RE = re.compile(r"[a-z]{2}(?:-[a-z]+)+-[0-9]")
_PROFILE_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.@+-]{0,127}")
_LIST_ITEM_RE = re.compile(r"[a-z0-9][a-z0-9_.-]{0,63}")
_TOKEN_RE = re.compile(r"\{([^{}]*)\}")
_DATE_TOKENS = ("{yyyy}", "{MM}", "{dd}")
_ALL_TOKENS = ("yyyy", "MM", "dd", "HH")

_SCALAR_KEYS = (
    "AWS_PROFILE", "AWS_REGION", "PRICE_PER_GB", "PRICE_PER_1K_GET", "MAX_MB", "RUN_MAX_MB",
    "DAY_MAX_MB", "MARKER_TTL_S", "WAF_IDENTITY_COOKIES", "WAF_IDENTITY_HEADERS", "SENSITIVE_PARAMS",
)


class ConfigError(Exception):
    def __init__(self, line: int, msg: str):
        super().__init__(line, msg)
        self.line = line
        self.msg = msg

    def __str__(self) -> str:
        return "line %d: %s" % (self.line, self.msg) if self.line > 0 else self.msg


@dataclass(frozen=True)
class Dataset:
    name: str
    type: str
    bucket: str
    template: str


@dataclass(frozen=True)
class Config:
    aws_profile: Optional[str] = None
    aws_region: Optional[str] = None
    datasets: Dict[str, Dataset] = field(default_factory=dict)
    price_per_gb: Optional[Decimal] = None
    price_per_1k_get: Optional[Decimal] = None
    max_mb: int = DEFAULT_MAX_MB
    run_max_mb: int = DEFAULT_RUN_MAX_MB
    day_max_mb: int = DEFAULT_DAY_MAX_MB
    marker_ttl_s: int = DEFAULT_MARKER_TTL_S
    identity_cookies: Tuple[str, ...] = DEFAULT_IDENTITY_COOKIES
    identity_headers: Tuple[str, ...] = DEFAULT_IDENTITY_HEADERS
    sensitive_params: frozenset = frozenset(DEFAULT_SENSITIVE_PARAMS)


def default_path() -> Path:
    return paths.config_path()


def _decimal(value: str) -> Decimal:
    try:
        d = Decimal(value)
    except InvalidOperation:
        raise Refused("expected a decimal number, got %r" % (value,))
    if not d.is_finite() or d < 0:
        raise Refused("expected a non-negative decimal number, got %r" % (value,))
    return d


def _name_list(value: str) -> Tuple[str, ...]:
    items = [i.strip().lower() for i in value.split(",")]
    if not value or any(not _LIST_ITEM_RE.fullmatch(i) for i in items):
        raise Refused("expected a comma-separated list of names (a-z 0-9 _ . -), got %r" % (value,))
    return tuple(items)


def _dataset(name: str, value: str) -> Dataset:
    typ, sep, rest = value.partition(":")
    if not sep or typ not in DATASET_TYPES:
        raise Refused("dataset type must be one of %s (got %r)" % ("|".join(DATASET_TYPES), typ))
    if not rest.startswith("s3://"):
        raise Refused("dataset location must look like s3://<bucket>/<template>")
    bkt, sep, template = rest[len("s3://"):].partition("/")
    if not sep or not template:
        raise Refused("dataset location needs a template after the bucket")
    bucket(bkt)
    for tok in _TOKEN_RE.findall(template):
        if tok not in _ALL_TOKENS:
            raise Refused("unknown template token {%s} (allowed: {yyyy} {MM} {dd} {HH})" % tok)
    if "{" in _TOKEN_RE.sub("", template) or "}" in _TOKEN_RE.sub("", template):
        raise Refused("unbalanced braces in template")
    for tok in _DATE_TOKENS:
        if tok not in template:
            raise Refused("template must contain %s" % tok)
    safe_key(_TOKEN_RE.sub("0", template))
    return Dataset(name, typ, bkt, template)


def _apply(values: dict, key: str, value: str) -> None:
    if key == "AWS_PROFILE":
        if value and not _PROFILE_RE.fullmatch(value):
            raise Refused("invalid AWS_PROFILE %r" % (value,))
        values["aws_profile"] = value or None
    elif key == "AWS_REGION":
        if value and not _REGION_RE.fullmatch(value):
            raise Refused("invalid AWS_REGION %r" % (value,))
        values["aws_region"] = value or None
    elif key == "PRICE_PER_GB":
        values["price_per_gb"] = _decimal(value)
    elif key == "PRICE_PER_1K_GET":
        values["price_per_1k_get"] = _decimal(value)
    elif key == "MAX_MB":
        values["max_mb"] = pos_int(value, key)
    elif key == "RUN_MAX_MB":
        values["run_max_mb"] = pos_int(value, key)
    elif key == "DAY_MAX_MB":
        values["day_max_mb"] = pos_int(value, key)
    elif key == "MARKER_TTL_S":
        values["marker_ttl_s"] = pos_int(value, key)
    elif key == "WAF_IDENTITY_COOKIES":
        values["identity_cookies"] = _name_list(value)
    elif key == "WAF_IDENTITY_HEADERS":
        values["identity_headers"] = _name_list(value)
    elif key == "SENSITIVE_PARAMS":
        values["sensitive_params"] = frozenset(_name_list(value))


def load(path: Optional[Path] = None) -> Config:
    """Read and strictly parse the config file. Raises ConfigError(line, msg)."""
    p = Path(path) if path is not None else default_path()
    try:
        if not p.is_file():
            raise ConfigError(0, "%s is not a regular file" % (p,))
        raw = p.read_bytes()
        if len(raw) > _MAX_FILE_BYTES:
            raise ConfigError(0, "config file is larger than %d bytes" % _MAX_FILE_BYTES)
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise ConfigError(0, "config file is not valid UTF-8")
    except OSError as e:
        raise ConfigError(0, "cannot read config file: %s" % (e.strerror or e,))

    values: dict = {}
    datasets: Dict[str, Dataset] = {}
    seen = set()
    for lineno, line in enumerate(text.splitlines(), start=1):
        line = _COMMENT_RE.sub("", line).strip()
        if not line:
            continue
        m = _LINE_RE.fullmatch(line)
        if not m:
            raise ConfigError(lineno, "not a KEY=value line (values may use only A-Za-z0-9 _ . , : / { } @ + = -)")
        key, value = m.group(1), m.group(2)
        if key in seen:
            raise ConfigError(lineno, "duplicate key %s" % key)
        try:
            if key.startswith("DATASET_"):
                name = dataset_name(key[len("DATASET_"):])
                datasets[name] = _dataset(name, value)
            elif key in _SCALAR_KEYS:
                _apply(values, key, value)
            else:
                raise ConfigError(lineno, "unknown key %s" % key)
        except Refused as e:
            raise ConfigError(lineno, "%s: %s" % (key, e))
        seen.add(key)
    return Config(datasets=datasets, **values)
