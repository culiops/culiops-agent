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


# ---- query strings and path parameters ---------------------------------------------------

def sensitive_names(cfg) -> "frozenset":
    """Names to mask in query strings and path parameters: SENSITIVE_PARAMS plus the identity
    cookie names (so ``jsessionid`` is masked by default). Everything lowercased."""
    return frozenset(str(n).lower() for n in tuple(cfg.sensitive_params) + tuple(cfg.identity_cookies))


def _name_candidates(raw_name: str) -> "List[str]":
    """Normalised forms of a decoded parameter name to compare against the sensitive set.

    Raises UnicodeError/ValueError when the name does not strictly decode. Control characters
    are removed, ``.`` and space map to ``_`` (PHP style), and ``name[...]`` also yields
    ``name``; both the mapped and unmapped spellings are returned.
    """
    name = unquote_plus(raw_name, errors="strict")
    name = "".join(c for c in name if not (ord(c) < 32 or 127 <= ord(c) < 160))
    name = name.strip().lower()
    forms = [name, name.replace(".", "_").replace(" ", "_")]
    forms += [f.split("[", 1)[0].strip() for f in list(forms)]
    return forms


def _is_sensitive(raw_name: str, names: "frozenset") -> bool:
    return any(f in names for f in _name_candidates(raw_name))


def mask_query(qs: str, sensitive: "frozenset") -> str:
    """Mask the values of sensitive parameters, keeping order and raw spelling of the rest.

    Names are compared after one percent-decode (strict UTF-8) and normalisation (see
    ``_name_candidates``). ``&`` and ``;`` both separate pairs. A piece with no ``=`` that
    decodes to something containing ``=`` is masked whole. If decoding fails, or the decoded
    text still holds a ``%XX`` escape (double encoding), the whole string becomes ``***``.

    Nested queries, one level: the value of a non-sensitive pair is decoded once; if it holds
    any of ``? & ; =``, its query part (after the first ``?``, else the whole value) is run
    through the same masking and its path part through ``mask_path``. If either changes
    anything the whole value becomes ``***`` (name kept). So ``redirect=%2Fx%3Ftoken%3Dabc``
    is masked while ``q=a%3Db`` is kept. Inside that nested check a value that itself holds
    a ``?`` (a third level) is masked too; nothing recurses further.
    """
    if qs is None or qs == "" or qs == "-":
        return qs
    if not isinstance(qs, str):
        return MASK
    return _mask_query(qs, frozenset(str(x).lower() for x in sensitive), False)


_SCHEME_RE = re.compile(r"[A-Za-z][A-Za-z0-9+.-]*:")
_AUTH_END_RE = re.compile(r"[/?#]")
_URL_JUNK_RE = re.compile(r"[\t\r\n]")
_LEADING_JUNK = "".join(chr(i) for i in range(33))  # C0 controls and space, stripped like browsers do


def _find_userinfo(text: str, conservative: bool) -> "Tuple[str, int, int]":
    """Fail-closed userinfo finder. Returns ``(t, start, at)``: ``t`` is ``text`` normalised the
    way a browser would (``\\`` read as ``/``, tab/CR/LF removed, leading controls and spaces
    stripped); ``t[start:]`` is what follows the scheme and any run of ``/``; ``at`` is the index
    of the last ``@`` that sits before the first ``/``, ``?`` or ``#`` of that remainder, or -1.

    The rule applies to a value with a scheme (``name:``, whatever the slashes: ``https:/x@h``,
    ``https:x@h``, ``https:///x@h``) and to a scheme-less value starting with ``//`` (or, when
    ``conservative``, with a single ``/``, because a nested value is only ever masked, never
    rewritten). So ``mailto:user@example.com`` counts as userinfo too: an address is personal data.
    """
    t = _URL_JUNK_RE.sub("", text.replace("\\", "/")).lstrip(_LEADING_JUNK)
    m = _SCHEME_RE.match(t)
    if m:
        start = m.end()
    elif t.startswith("//") or (conservative and t.startswith("/")):
        start = 0
    else:
        return t, 0, -1
    while start < len(t) and t[start] == "/":
        start += 1
    m = _AUTH_END_RE.search(t, start)
    end = m.start() if m else len(t)
    return t, start, t.rfind("@", start, end)


def _has_userinfo(text: str) -> bool:
    return _find_userinfo(text, True)[2] >= 0


def _nested_leaks(text: str, names: "frozenset") -> bool:
    """Would the query part (after the first ``?``, else the whole text) or the path part of
    ``text`` change under masking? One level: the inner run is ``nested``."""
    path, sep, q = text.partition("?")
    qpart = q if sep else text
    return _mask_query(qpart, names, True) != qpart or mask_path(path, names) != path


def _value_leaks(raw_value: str, names: "frozenset", nested: bool) -> bool:
    """Does the (non-sensitive) parameter value hide a sensitive nested query or path param,
    a sensitive fragment, or URL userinfo? May raise UnicodeError/ValueError, which callers
    turn into a whole-string mask."""
    dec = unquote_plus(raw_value, errors="strict")
    if not any(c in dec for c in "?&;=#@"):
        return False
    # Every '#'-separated piece is checked on its own: the first is the value itself, the rest
    # are fragments (a second '#' does not start a new URL, but a browser-side script may read it).
    pieces = dec.split("#")
    if any(_has_userinfo(p) for p in pieces):
        return True
    if nested:
        # Third level: do not look deeper, just refuse anything that still looks like a URL.
        return "?" in dec or "#" in dec
    before = pieces[0]
    if any(_nested_leaks(p, names) for p in pieces[1:]):
        return True
    return any(c in before for c in "?&;=") and _nested_leaks(before, names)


def _mask_query(qs: str, names: "frozenset", nested: bool) -> str:
    n = len(qs) - len(qs.lstrip("?"))
    prefix, qs = qs[:n], qs[n:]
    if qs == "":
        return prefix
    try:
        decoded = unquote_plus(qs, errors="strict")
    except (UnicodeError, ValueError):
        return MASK
    if _ENCODED_RE.search(decoded):
        return MASK
    parts = _SEP_RE.split(qs)
    out = []  # type: List[str]
    for i, piece in enumerate(parts):
        if i % 2 == 1:
            out.append(piece)
            continue
        try:
            if "=" not in piece:
                out.append(MASK if "=" in unquote_plus(piece, errors="strict") else piece)
                continue
            raw_name, _, raw_value = piece.partition("=")
            if _is_sensitive(raw_name, names) or _value_leaks(raw_value, names, nested):
                out.append(raw_name + "=" + MASK)
            else:
                out.append(piece)
        except (UnicodeError, ValueError):
            return MASK
    return prefix + "".join(out)


_ENC_SEMI_RE = re.compile(r"%3b", re.IGNORECASE)


def _mask_param(piece: str, names: "frozenset") -> str:
    """One ``;``-separated path piece: unchanged, ``name=***`` (sensitive name), or ``***``
    (does not decode strictly, residual ``%XX`` after decoding, or no ``=`` but decodes to a
    pair)."""
    try:
        decoded = unquote_plus(piece, errors="strict")
        if _ENCODED_RE.search(decoded):
            return MASK
        if "=" not in piece:
            return MASK if "=" in decoded else piece
        raw_name = piece.partition("=")[0]
        return raw_name + "=" + MASK if _is_sensitive(raw_name, names) else piece
    except (UnicodeError, ValueError):
        return MASK


def _mask_segment(seg: str, names: "frozenset") -> str:
    """Mask raw ``;`` matrix parameters in one path segment."""
    if ";" not in seg:
        return seg
    pieces = seg.split(";")
    for i in range(1, len(pieces)):
        if pieces[i] != "":
            pieces[i] = _mask_param(pieces[i], names)
    return ";".join(pieces)


def mask_path(path: str, sensitive: "frozenset") -> str:
    """Mask sensitive ``;name=value`` matrix parameters in a URL path (e.g. ``;jsessionid=``).

    Names compare like query names. A parameter that does not strictly decode, still holds a
    ``%XX`` escape after decoding, or has no ``=`` but decodes to something with one, is
    replaced by ``***``. Raw spelling of everything else is kept.

    Encoded delimiter: a segment holding ``%3B``/``%3b`` is decoded once. If any ``;`` param of
    the decoded segment would be masked (or the segment does not decode), everything from the
    first encoded ``%3B`` on is replaced by the literal ``%3B***`` (so ``/a%3Bjsessionid=ZZ``
    becomes ``/a%3B***``); the text before it still gets the normal raw ``;`` masking.
    """
    if path is None or path == "":
        return path
    if not isinstance(path, str):
        return MASK
    if ";" not in path and not _ENC_SEMI_RE.search(path):
        return path
    names = frozenset(str(x).lower() for x in sensitive)
    segments = path.split("/")
    for si, seg in enumerate(segments):
        m = _ENC_SEMI_RE.search(seg)
        if m:
            try:
                decoded = unquote_plus(seg, errors="strict")
                flagged = bool(_ENCODED_RE.search(decoded)) or any(
                    _mask_param(p, names) != p for p in decoded.split(";")[1:] if p)
            except (UnicodeError, ValueError):
                flagged = True
            if flagged:
                segments[si] = _mask_segment(seg[:m.start()], names) + "%3B" + MASK
                continue
        segments[si] = _mask_segment(seg, names)
    return "/".join(segments)


def _mask_uri(uri: str, sensitive: "frozenset") -> str:
    path, sep, q = uri.partition("?")
    path = mask_path(path, sensitive)
    return path + sep + mask_query(q, sensitive) if sep else path


def mask_url(url: str, sensitive: "frozenset") -> str:
    """Mask a full URL (referer, ALB redirect URL): query via mask_query, path parameters via
    mask_path. Also drops userinfo (see ``_find_userinfo``: any scheme/slash spelling, and a
    ``mailto:`` address; a scheme-less value with one leading slash is a path and is kept) and
    the fragment (both can carry secrets). Unparseable -> ``***``. ``None``, ``""`` and ``"-"`` (the logs' "absent") are returned as they are;
    a non-string becomes ``***``."""
    if url is None or url == "" or url == "-":
        return url
    if not isinstance(url, str):
        return MASK
    value, start, at = _find_userinfo(url, False)
    if at >= 0:  # drop everything up to and including the userinfo '@' (rebuilt below, else '***')
        value = value[:start] + value[at + 1:]
    try:
        sp = urlsplit(value)
        netloc = sp.netloc.rsplit("@", 1)[-1]
        base = urlunsplit((sp.scheme, netloc, mask_path(sp.path, sensitive), "", ""))
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
            os.fchmod(fd, 0o600)
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
        return str(v) if abs(v) < 10 ** 18 else None
    return None


def _int(v: Any) -> Optional[int]:
    if isinstance(v, bool):
        return None
    if isinstance(v, int):
        return v if abs(v) < 10 ** 18 else None
    if isinstance(v, str) and v.isascii() and v.isdigit() and len(v) <= 18:
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


_WAF_KEYS = (
    "ts", "action", "terminating_rule_id", "terminating_rule_type", "rule_group_matches",
    "non_terminating_rules", "labels", "client_ip", "country", "asn", "host", "uri",
    "query_masked", "http_method", "http_version", "request_id", "ja3", "ja4", "header_names",
    "user_agent", "referer_masked", "client_key", "identity_hashes", "response_code_sent",
    "matched_field", "match_type", "matched_hash",
)


def waf_record(rec: dict, cfg, salt: bytes) -> dict:
    """Reduce one WAF log record to the fixed, redacted key set. No header or cookie value
    survives except through a salted hash of a configured identity.

    Never raises on the shape of ``rec``. If building the record fails for any reason the
    result is the full key set, every value null except ``query_masked`` and
    ``referer_masked`` which are ``***`` (never a partial record).
    """
    try:
        return _waf_record(rec, cfg, salt)
    except Exception:
        out = {k: None for k in _WAF_KEYS}
        out["query_masked"] = MASK
        out["referer_masked"] = MASK
        return out


def _waf_record(rec: dict, cfg, salt: bytes) -> dict:
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

    sensitive = sensitive_names(cfg)
    args = http.get("args")
    query_masked = mask_query(args, sensitive) if isinstance(args, str) else None
    uri = http.get("uri")
    uri = _mask_uri(uri, sensitive) if isinstance(uri, str) else None

    referer = _first_header(headers, "referer")
    referer_masked = mask_url(referer, sensitive) if referer is not None else None

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
