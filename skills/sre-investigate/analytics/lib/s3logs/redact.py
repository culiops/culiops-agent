"""Redaction of request-level log data. Fail closed: when unsure, mask.

Nothing here logs, prints or puts a sensitive value into an exception message. The
fail-closed paths return the constant ``***`` instead of echoing their input.

WAF record shape (field names, nesting, examples):
  https://docs.aws.amazon.com/waf/latest/developerguide/logging-fields.html
  https://docs.aws.amazon.com/waf/latest/developerguide/logging-examples.html
``clientAsn`` is a documented field ("logged only when an ASN match statement is used"). The
docs do not show where it nests, so both ``httpRequest.clientAsn`` and top-level ``clientAsn``
are read; it is null when absent. Match details are documented as ``conditionType``,
``location`` and ``matchedData`` (a list of strings); the docs show no field-name member, so
``matched_field`` holds the ``location`` only.
"""
from __future__ import annotations

import hashlib
import os
import re
import secrets
import stat
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import unquote_plus, urlsplit, urlunsplit

from s3logs import paths
from s3logs.validate import Refused

MASK = "***"

_ENCODED_RE = re.compile(r"%[0-9A-Fa-f]{2}")
_SEP_RE = re.compile(r"([&;])")
_SALT_RE = re.compile(r"[0-9a-f]{64}")
_EPOCH = datetime(1970, 1, 1)


# ---- query strings ----------------------------------------------------------------------

def mask_query(qs: str, sensitive: "frozenset") -> str:
    """Mask the values of sensitive parameters, keeping order and raw spelling of the rest.

    Names are compared after one percent-decode (strict UTF-8), lowercased and trimmed; a
    PHP-style ``name[...]`` also matches on ``name``. ``&`` and ``;`` both separate pairs. If
    decoding fails, or the decoded text still holds a ``%XX`` escape (double encoding), the
    whole string becomes ``***``.
    """
    if qs is None or qs == "" or qs == "-":
        return qs
    if not isinstance(qs, str):
        return MASK
    if qs.startswith("?"):
        return "?" + mask_query(qs[1:], sensitive)
    try:
        decoded = unquote_plus(qs, errors="strict")
    except (UnicodeError, ValueError):
        return MASK
    if _ENCODED_RE.search(decoded):
        return MASK
    names = frozenset(str(n).lower() for n in sensitive)
    parts = _SEP_RE.split(qs)
    out = []  # type: List[str]
    for i, piece in enumerate(parts):
        if i % 2 == 1 or "=" not in piece:
            out.append(piece)
            continue
        raw_name, _, _value = piece.partition("=")
        try:
            name = unquote_plus(raw_name, errors="strict").strip().lower()
        except (UnicodeError, ValueError):
            return MASK
        if name in names or name.split("[", 1)[0].strip() in names:
            out.append(raw_name + "=" + MASK)
        else:
            out.append(piece)
    return "".join(out)


def _mask_referer(value: str, sensitive: "frozenset") -> str:
    """Mask the query of a referer URL. Also drops userinfo and the fragment (both can carry
    secrets). An unparseable referer becomes ``***``."""
    try:
        sp = urlsplit(value)
        netloc = sp.netloc.rsplit("@", 1)[-1]
        base = urlunsplit((sp.scheme, netloc, sp.path, "", ""))
        query = sp.query
    except ValueError:
        return MASK
    if query:
        return base + "?" + mask_query(query, sensitive)
    return base


# ---- hashing and the per-install salt ---------------------------------------------------

def hash_value(v: str, salt: bytes) -> str:
    """sha256(salt || value), first 12 hex characters."""
    return hashlib.sha256(salt + v.encode("utf-8", "surrogatepass")).hexdigest()[:12]


def _salt_path():
    return paths.state_root() / "salt"


def _read_salt(p) -> bytes:
    try:
        st = os.lstat(str(p))
    except OSError as e:
        raise Refused("cannot stat salt file %s: %s" % (p, e.strerror or "error"))
    if stat.S_ISLNK(st.st_mode):
        raise Refused("salt file %s is a symlink; refusing to use it" % (p,))
    if not stat.S_ISREG(st.st_mode):
        raise Refused("salt file %s is not a regular file" % (p,))
    if st.st_uid != os.getuid():
        raise Refused("salt file %s is owned by another user" % (p,))
    if stat.S_IMODE(st.st_mode) & ~0o600:
        raise Refused("salt file %s has mode %s, looser than 0600; fix with chmod 600" % (p, oct(stat.S_IMODE(st.st_mode))))
    try:
        fd = os.open(str(p), os.O_RDONLY | os.O_NOFOLLOW)
    except OSError as e:
        raise Refused("cannot open salt file %s: %s" % (p, e.strerror or "error"))
    try:
        st2 = os.fstat(fd)
        if (st2.st_ino, st2.st_dev) != (st.st_ino, st.st_dev):
            raise Refused("salt file %s changed while being read" % (p,))
        data = os.read(fd, 128)
    finally:
        os.close(fd)
    try:
        text = data.decode("ascii")
    except UnicodeDecodeError:
        text = ""
    if not _SALT_RE.fullmatch(text):
        raise Refused("salt file %s is malformed (expected 64 lowercase hex characters); delete it to start a new salt" % (p,))
    return bytes.fromhex(text)


def load_or_create_salt() -> bytes:
    """The per-install salt at <state root>/salt: 64 hex chars, mode 0600.

    Created from 32 random bytes written to a private temp file (O_CREAT|O_EXCL|O_NOFOLLOW,
    0600) and then hard-linked into place, so the salt file never exists half-written and a
    lost race simply reads the winner's file. A symlink, a mode looser than 0600, a foreign
    owner or malformed content is refused.
    """
    paths.ensure_private_dirs()
    p = _salt_path()
    if os.path.lexists(str(p)):
        return _read_salt(p)
    raw = secrets.token_bytes(32)
    tmp = p.with_name("salt.tmp.%s" % secrets.token_hex(8))
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
    try:
        fd = os.open(str(tmp), flags, 0o600)
    except OSError as e:
        raise Refused("cannot create salt file %s: %s" % (p, e.strerror or "error"))
    try:
        try:
            os.write(fd, raw.hex().encode("ascii"))
            os.fsync(fd)
        finally:
            os.close(fd)
        try:
            os.link(str(tmp), str(p))
        except FileExistsError:
            return _read_salt(p)
        except OSError as e:
            raise Refused("cannot create salt file %s: %s" % (p, e.strerror or "error"))
    finally:
        try:
            os.unlink(str(tmp))
        except OSError:
            pass
    return _read_salt(p)


# ---- WAF records ------------------------------------------------------------------------

def _str(v: Any) -> Optional[str]:
    if isinstance(v, str):
        return v
    if isinstance(v, int) and not isinstance(v, bool):
        return str(v)
    return None


def _int(v: Any) -> Optional[int]:
    if isinstance(v, bool):
        return None
    if isinstance(v, int):
        return v
    if isinstance(v, str) and v.isdigit():
        return int(v)
    return None


def _list(v: Any) -> list:
    return v if isinstance(v, list) else []


def _dict(v: Any) -> dict:
    return v if isinstance(v, dict) else {}


def _iso_ms(ms: Any) -> Optional[str]:
    n = _int(ms)
    if n is None:
        return None
    try:
        d = _EPOCH + timedelta(milliseconds=n)
    except OverflowError:
        return None
    return d.strftime("%Y-%m-%dT%H:%M:%S.") + "%03dZ" % (d.microsecond // 1000)


def _headers(http: dict) -> List[Tuple[str, str]]:
    """(lowercased name, value) for each well-formed header, in order."""
    out = []
    for h in _list(http.get("headers")):
        h = _dict(h)
        name = h.get("name")
        value = h.get("value")
        if isinstance(name, str) and isinstance(value, str):
            out.append((name.lower(), value))
        elif isinstance(name, str):
            out.append((name.lower(), ""))
    return out


def _header_names(http: dict) -> List[str]:
    out = []
    for h in _list(http.get("headers")):
        name = _dict(h).get("name")
        if isinstance(name, str):
            out.append(name.lower())
    return out


def _first_header(headers: List[Tuple[str, str]], name: str) -> Optional[str]:
    for n, v in headers:
        if n == name:
            return v
    return None


def _cookies(headers: List[Tuple[str, str]]) -> Dict[str, str]:
    """name -> first non-empty value across every ``cookie`` header (names case-sensitive)."""
    jar = {}  # type: Dict[str, str]
    for n, v in headers:
        if n != "cookie":
            continue
        for pair in v.split(";"):
            k, eq, val = pair.partition("=")
            k = k.strip()
            val = val.strip()
            if eq and k and val and k not in jar:
                jar[k] = val
    return jar


def _match_details(rec: dict) -> List[dict]:
    """Match details of the terminating rule: top-level first, then the terminating rule of
    a rule group."""
    top = [d for d in _list(rec.get("terminatingRuleMatchDetails")) if isinstance(d, dict)]
    if top:
        return top
    for g in _list(rec.get("ruleGroupList")):
        t = _dict(_dict(g).get("terminatingRule"))
        det = [d for d in _list(t.get("ruleMatchDetails")) if isinstance(d, dict)]
        if det:
            return det
    return []


def waf_record(rec: dict, cfg, salt: bytes) -> dict:
    """Reduce one WAF log record to the fixed, redacted key set. No header or cookie value
    survives except through a salted hash of a configured identity."""
    rec = _dict(rec)
    http = _dict(rec.get("httpRequest"))
    headers = _headers(http)

    group_rules = []  # type: List[str]
    for g in _list(rec.get("ruleGroupList")):
        g = _dict(g)
        ids = [_dict(g.get("terminatingRule")).get("ruleId")]
        ids += [_dict(r).get("ruleId") for r in _list(g.get("nonTerminatingMatchingRules"))]
        for i in ids:
            if isinstance(i, str) and i not in group_rules:
                group_rules.append(i)

    non_term = []
    for r in _list(rec.get("nonTerminatingMatchingRules")):
        r = _dict(r)
        rid = r.get("ruleId")
        if isinstance(rid, str):
            non_term.append("%s:%s" % (rid, _str(r.get("action")) or ""))

    labels = [n for n in (_dict(x).get("name") for x in _list(rec.get("labels"))) if isinstance(n, str)]

    sensitive = cfg.sensitive_params
    args = http.get("args")
    query_masked = mask_query(args, sensitive) if isinstance(args, str) else None
    uri = http.get("uri")
    if isinstance(uri, str) and "?" in uri:
        path, _, q = uri.partition("?")
        uri = path + "?" + mask_query(q, sensitive)
    uri = uri if isinstance(uri, str) else None

    referer = _first_header(headers, "referer")
    referer_masked = _mask_referer(referer, sensitive) if referer is not None else None

    identity = []  # type: List[str]
    keys = []  # type: List[str]
    for hname in cfg.identity_headers:
        val = next((v for n, v in headers if n == hname.lower() and v), None)
        if val is not None:
            h = hash_value(val, salt)
            keys.append(h)
            identity.append("%s:%s" % (hname.lower(), h))
    jar = _cookies(headers)
    for cname in cfg.identity_cookies:
        if cname in jar:
            h = hash_value(jar[cname], salt)
            keys.append(h)
            identity.append("%s:%s" % (cname, h))

    details = _match_details(rec)
    matched_field = match_type = matched_hash = None
    if details:
        matched_field = _str(details[0].get("location"))
        match_type = _str(details[0].get("conditionType"))
        data = []
        for d in details:
            data += [str(x) for x in _list(d.get("matchedData")) if isinstance(x, (str, int, float))]
        if data:
            matched_hash = hash_value("\x1f".join(data), salt)

    asn = _str(http.get("clientAsn"))
    if asn is None:
        asn = _str(rec.get("clientAsn"))

    return {
        "ts": _iso_ms(rec.get("timestamp")),
        "action": _str(rec.get("action")),
        "terminating_rule_id": _str(rec.get("terminatingRuleId")),
        "terminating_rule_type": _str(rec.get("terminatingRuleType")),
        "rule_group_matches": group_rules,
        "non_terminating_rules": non_term,
        "labels": labels,
        "client_ip": _str(http.get("clientIp")),
        "country": _str(http.get("country")),
        "asn": asn,
        "host": _first_header(headers, "host"),
        "uri": uri,
        "query_masked": query_masked,
        "http_method": _str(http.get("httpMethod")),
        "http_version": _str(http.get("httpVersion")),
        "request_id": _str(http.get("requestId")),
        "ja3": _str(rec.get("ja3Fingerprint")),
        "ja4": _str(rec.get("ja4Fingerprint")),
        "header_names": _header_names(http),
        "user_agent": _first_header(headers, "user-agent"),
        "referer_masked": referer_masked,
        "client_key": keys[0] if keys else None,
        "identity_hashes": identity,
        "response_code_sent": _int(rec.get("responseCodeSent")),
        "matched_field": matched_field,
        "match_type": match_type,
        "matched_hash": matched_hash,
    }
