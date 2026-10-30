"""Layer 1 of the SQL defences: decide whether an agent-supplied statement may run at all.

``check(sql)`` returns the normalized single statement or raises ``validate.Refused``. It is
a screen, not a security boundary: ``duck.run`` (layer 2) must hold on its own, so nothing
here is ever allowed to replace it.

How it works. The text is tokenized first, so a keyword hidden in a comment or a string
literal neither triggers nor evades a rule: comments are dropped, string literals and quoted
identifiers become single tokens. Then:

* exactly one statement (one trailing ``;`` is tolerated, nothing may follow it);
* the first token is one of SELECT, WITH, DESCRIBE, SUMMARIZE, FROM;
* no deny keyword appears as a word anywhere (a quoted identifier is not a keyword);
* no deny function is called: an identifier (quoted or not, last part of a qualified name)
  directly followed by ``(`` and named ``read_*``, ``*_scan``, ``glob``, ``sniff_csv``,
  ``query``, ``query_table``, ``getenv`` or one of the extras below (R6: a plain identifier
  that is not called is never refused);
* no line starts with ``.`` (DuckDB CLI dot-commands such as ``.shell`` are not SQL and bypass
  every setting; R11). This is checked on the raw text, before comments are removed, and
  again on the normalized text, with every line terminator the CLI accepts counted as a break.

Where this is deliberately stricter than the plain rules, because the lexer must agree with
DuckDB's about where a string or comment ends (any disagreement could hide a keyword):
``$`` outside a string, ``E'...'`` and ``U&'...'`` strings, nested ``/* /* */ */`` comments,
control characters, unbalanced parentheses (the CLI wraps the statement in ``( ... )``) and a
string literal or a path-like quoted name in table position (after FROM, JOIN, DESCRIBE, SUMMARIZE,
PIVOT, UNPIVOT, or after a comma inside a FROM clause; DuckDB would read it as a file) are refused.

Extra denied function names beyond the brief: ``parquet_*``, ``duckdb_*``, ``pragma_*``,
``current_setting``, ``which_secret``, ``json_execute_serialized_sql`` (runs serialized SQL).
"""
from __future__ import annotations

import re
from typing import List, NamedTuple

from s3logs.validate import Refused

ALLOWED_FIRST = frozenset({"SELECT", "WITH", "DESCRIBE", "SUMMARIZE", "FROM"})
NAMED_FIRST = frozenset({"SELECT", "WITH", "FROM"})
DENY_KEYWORDS = frozenset(
    "COPY ATTACH DETACH INSTALL LOAD PRAGMA SET RESET EXPORT IMPORT CREATE INSERT UPDATE DELETE "
    "DROP ALTER CALL CHECKPOINT VACUUM USE PREPARE EXECUTE".split())
DENY_FUNCTIONS = frozenset({
    "glob", "sniff_csv", "query", "query_table", "getenv",
    "current_setting", "which_secret", "json_execute_serialized_sql",
})
DENY_FUNCTION_PREFIXES = ("read_", "parquet_", "duckdb_", "pragma_")
DENY_FUNCTION_SUFFIXES = ("_scan",)

MAX_SQL_CHARS = 64 * 1024

# Same set duck.py uses: anything the CLI could treat as a line break.
_LINE_BREAKS = "\n\r\x0b\x0c\x1c\x1d\x1e\x85\u2028\u2029"
_LINE_BREAKS_RE = re.compile("[%s]" % _LINE_BREAKS)
_WS = " \t\n\r\f\v"
_WORD_START_RE = re.compile(r"[A-Za-z_\u0080-\U0010ffff]")
_WORD_RE = re.compile(r"[A-Za-z0-9_\u0080-\U0010ffff]*")
# Numbers the way DuckDB lexes them. Letters after a number start a new word token, so
# "1.FROM" is the number "1." then the word FROM, never one blob that hides a keyword.
_NUM_RE = re.compile(r"0[xX][0-9A-Fa-f_]+|0[bB][01_]+"
                     r"|[0-9][0-9_]*(?:\.[0-9_]*)?(?:[eE][+-]?[0-9]+)?"
                     r"|\.[0-9][0-9_]*(?:[eE][+-]?[0-9]+)?")
_PUNCT = set("(),.+-*/%=<>!~^&|:?@#[]{}\\`")
_PLAIN_NAME_RE = re.compile(r"[A-Za-z0-9_]*")
# Words after which a table (or a file DuckDB would read as one) may follow directly.
_TABLE_INTRODUCERS = frozenset({"FROM", "JOIN", "DESCRIBE", "SUMMARIZE", "PIVOT", "UNPIVOT"})
# Words that end the table list of a FROM clause at the same parenthesis depth.
_FROM_ENDERS = frozenset({"SELECT", "WHERE", "GROUP", "ORDER", "HAVING", "LIMIT", "OFFSET", "UNION",
                          "EXCEPT", "INTERSECT", "QUALIFY", "WINDOW", "SAMPLE", "FETCH", "RETURNING"})


class _Tok(NamedTuple):
    kind: str    # word | qident | string | num | punct | semi
    text: str    # raw text; for qident the unescaped name
    start: int


def _is_ident_char(ch: str) -> bool:
    return ch.isalnum() or ch == "_" or ord(ch) >= 0x80


def _check_dot_lines(text: str) -> None:
    for line in _LINE_BREAKS_RE.split(text):
        if line.lstrip().startswith("."):
            raise Refused("a line starts with '.': DuckDB CLI dot-commands are not allowed")


def _scan_quoted(sql: str, i: int, q: str) -> int:
    """Index just past the closing quote of the literal that opens at ``i`` (doubled quotes
    escape). Refuses an unterminated literal."""
    j = i + 1
    n = len(sql)
    while True:
        k = sql.find(q, j)
        if k < 0:
            raise Refused("unterminated %s" % ("string literal" if q == "'" else "quoted identifier"))
        if k + 1 < n and sql[k + 1] == q:
            j = k + 2
            continue
        return k + 1


def _tokenize(sql: str):
    """Return (tokens, pieces, semi_piece): the tokens, the pieces of the normalized text
    (comments replaced by one space) and the index in ``pieces`` of the ``;`` token."""
    if not isinstance(sql, str):
        raise Refused("SQL must be text")
    if len(sql) > MAX_SQL_CHARS:
        raise Refused("SQL is too long (maximum %d characters)" % MAX_SQL_CHARS)
    _check_dot_lines(sql)
    toks = []   # type: List[_Tok]
    pieces = []  # type: List[str]
    semi_piece = -1
    i, n = 0, len(sql)
    while i < n:
        c = sql[i]
        if c in _WS:
            pieces.append(c)
            i += 1
        elif ord(c) < 0x20 or ord(c) == 0x7F:
            raise Refused("control character in SQL")
        elif c == "-" and sql.startswith("--", i):
            j = i + 2
            while j < n and sql[j] not in _LINE_BREAKS:
                j += 1
            pieces.append(" ")
            i = j
        elif c == "/" and sql.startswith("/*", i):
            j = sql.find("*/", i + 2)
            if j < 0:
                raise Refused("unterminated block comment")
            if "/*" in sql[i + 2:j]:
                raise Refused("nested block comments are not supported")
            pieces.append(" ")
            i = j + 2
        elif c == "'":
            if i >= 1 and sql[i - 1] in "eE" and (i < 2 or not _is_ident_char(sql[i - 2])):
                raise Refused("escape strings (E'...') are not supported; use a plain 'string'")
            if i >= 2 and sql[i - 1] == "&" and sql[i - 2] in "uU" and (i < 3 or not _is_ident_char(sql[i - 3])):
                raise Refused("unicode-escape strings (U&'...') are not supported")
            j = _scan_quoted(sql, i, "'")
            toks.append(_Tok("string", sql[i:j], i))
            pieces.append(sql[i:j])
            i = j
        elif c == '"':
            if i >= 2 and sql[i - 1] == "&" and sql[i - 2] in "uU" and (i < 3 or not _is_ident_char(sql[i - 3])):
                raise Refused("unicode-escape identifiers (U&\"...\") are not supported")
            j = _scan_quoted(sql, i, '"')
            toks.append(_Tok("qident", sql[i + 1:j - 1].replace('""', '"'), i))
            pieces.append(sql[i:j])
            i = j
        elif c == "$":
            raise Refused("'$' outside a string is not supported (dollar quoting and parameters are refused)")
        elif c == ";":
            toks.append(_Tok("semi", ";", i))
            pieces.append(";")
            semi_piece = len(pieces) - 1
            i += 1
        elif (c.isdigit() and c.isascii()) or (c == "." and sql[i + 1:i + 2].isdigit() and sql[i + 1].isascii()):
            m = _NUM_RE.match(sql, i)
            toks.append(_Tok("num", m.group(0), i))
            pieces.append(m.group(0))
            i = m.end()
        elif _WORD_START_RE.match(c):
            m = _WORD_RE.match(sql, i)
            toks.append(_Tok("word", m.group(0), i))
            pieces.append(m.group(0))
            i = m.end()
        elif c in _PUNCT:
            toks.append(_Tok("punct", c, i))
            pieces.append(c)
            i += 1
        else:
            raise Refused("unsupported character %r in SQL" % c)
    return toks, pieces, semi_piece


def _structure(sql: str):
    """Tokenize and check the shape shared by check() and check_named(). Returns the real
    tokens (without the trailing ``;``) and the normalized text."""
    toks, pieces, semi_piece = _tokenize(sql)
    semis = [k for k, t in enumerate(toks) if t.kind == "semi"]
    if semis:
        if len(semis) > 1 or semis[0] != len(toks) - 1:
            raise Refused("exactly one statement is allowed (found text around or after a ';')")
        toks = toks[:-1]
        pieces[semi_piece] = ""
    if not toks:
        raise Refused("empty statement")
    depth = 0
    for t in toks:
        if t.kind == "punct" and t.text == "(":
            depth += 1
        elif t.kind == "punct" and t.text == ")":
            depth -= 1
            if depth < 0:
                raise Refused("unbalanced parentheses")
    if depth != 0:
        raise Refused("unbalanced parentheses")
    normalized = "".join(pieces).strip()
    _check_dot_lines(normalized)
    return toks, normalized


def _first_keyword(toks: List[_Tok], allowed, label: str) -> None:
    first = toks[0]
    if first.kind != "word" or first.text.upper() not in allowed:
        raise Refused("only %s statements are allowed" % label)


def _denied_function(name: str) -> bool:
    low = name.lower()
    return (low in DENY_FUNCTIONS or low.startswith(DENY_FUNCTION_PREFIXES)
            or low.endswith(DENY_FUNCTION_SUFFIXES))


def check(sql: str) -> str:
    """Return the normalized single statement (comments removed, no trailing ``;``) or raise
    Refused."""
    toks, normalized = _structure(sql)
    _first_keyword(toks, ALLOWED_FIRST, "SELECT, WITH, DESCRIBE, SUMMARIZE or FROM")
    in_from = [False]    # per parenthesis depth: inside the table list of a FROM clause
    for k, t in enumerate(toks):
        if t.kind == "word" and t.text.upper() in DENY_KEYWORDS:
            raise Refused("keyword %s is not allowed" % t.text.upper())
        nxt = toks[k + 1] if k + 1 < len(toks) else None
        if t.kind in ("word", "qident") and nxt is not None and nxt.kind == "punct" and nxt.text == "(":
            if _denied_function(t.text):
                raise Refused("function %s() is not allowed" % t.text.lower())
        prev = toks[k - 1] if k > 0 else None
        table_position = prev is not None and (
            (prev.kind == "word" and prev.text.upper() in _TABLE_INTRODUCERS)
            or (prev.kind == "punct" and prev.text == "," and in_from[-1]))
        if table_position:
            if t.kind == "string":
                raise Refused("a string literal in table position reads a file; "
                              "query the view 'logs' (or one of the listed views) instead")
            if t.kind == "qident" and not _PLAIN_NAME_RE.fullmatch(t.text):
                raise Refused("a path-like quoted name in table position reads a file; "
                              "query the view 'logs' (or one of the listed views) instead")
        if t.kind == "punct" and t.text == "(":
            in_from.append(False)
        elif t.kind == "punct" and t.text == ")":
            in_from.pop()
        elif t.kind == "word":
            up = t.text.upper()
            if up in ("FROM", "JOIN"):
                in_from[-1] = True
            elif up in _FROM_ENDERS:
                in_from[-1] = False
    return normalized


def check_named(sql: str) -> str:
    """Light check for named query files (trusted repo content, so a corrupted one fails
    closed rather than being re-audited line by line): a single statement starting with
    SELECT, WITH or FROM, balanced, with no dot-command line. Returns the normalized text."""
    toks, normalized = _structure(sql)
    _first_keyword(toks, NAMED_FIRST, "SELECT, WITH or FROM")
    return normalized
