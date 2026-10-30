"""Layer 1 of the SQL defences: tokenizer, statement shape, deny keywords and functions."""
from __future__ import annotations

import pytest

from s3logs import sqlguard
from s3logs.validate import Refused

DENY_KEYWORDS = ("COPY ATTACH DETACH INSTALL LOAD PRAGMA SET RESET EXPORT IMPORT CREATE INSERT UPDATE "
                 "DELETE DROP ALTER CALL CHECKPOINT VACUUM USE PREPARE EXECUTE").split()


def refused(sql, check=sqlguard.check):
    with pytest.raises(Refused) as e:
        check(sql)
    return str(e.value)


# ---- statement shape ------------------------------------------------------------------------

def test_refuses_second_statement():
    refused("SELECT 1; DROP TABLE x")
    refused("SELECT 1; SELECT 2")
    refused(";SELECT 1")
    refused("SELECT 1;;")
    refused("SELECT 1; -- c\nSELECT 2")


def test_one_trailing_semicolon_allowed_and_stripped():
    assert sqlguard.check("SELECT 1;") == "SELECT 1"
    assert sqlguard.check("  SELECT 1 ;  \n") == "SELECT 1"
    assert sqlguard.check("SELECT 1; -- done\n") == "SELECT 1"
    assert sqlguard.check("SELECT 1; /* done */") == "SELECT 1"


def test_semicolon_inside_string_ok():
    assert sqlguard.check("SELECT ';' AS x") == "SELECT ';' AS x"
    assert sqlguard.check("SELECT 'a'';b' AS x") == "SELECT 'a'';b' AS x"
    assert sqlguard.check('SELECT 1 AS "a;b"') == 'SELECT 1 AS "a;b"'


def test_comment_hiding_keyword_refused():
    refused("SELECT 1 /* x */; COPY (SELECT 1) TO '/tmp/x'")
    refused("SELECT 1 /* x */ COPY (SELECT 1) TO '/tmp/x'")
    refused("SELECT 1 -- x\n; COPY (SELECT 1) TO '/tmp/x'")
    refused("/* leading */ COPY (SELECT 1) TO '/tmp/x'")


def test_keywords_in_comments_and_strings_do_not_trigger():
    assert sqlguard.check("SELECT 'COPY', 'read_csv(x)' -- DROP TABLE x") == "SELECT 'COPY', 'read_csv(x)'"
    assert sqlguard.check("SELECT /* SET x */ 1") == "SELECT   1"
    assert sqlguard.check('SELECT "set", "copy" FROM logs') == 'SELECT "set", "copy" FROM logs'


def test_comment_is_replaced_by_whitespace_not_glued():
    assert sqlguard.check("SELECT 1/**/+/**/2") == "SELECT 1 + 2"
    # a trailing line comment cannot swallow whatever the caller appends
    assert "--" not in sqlguard.check("SELECT 1 -- x")


@pytest.mark.parametrize("first", ["SELECT 1", "select 1", "WITH a AS (SELECT 1) SELECT * FROM a",
                                   "DESCRIBE logs", "SUMMARIZE logs", "FROM logs", "describe logs"])
def test_allowed_first_keywords(first):
    assert sqlguard.check(first)


@pytest.mark.parametrize("sql", ["INSERT INTO x VALUES (1)", "VALUES (1)", "(SELECT 1)", "EXPLAIN SELECT 1",
                                 "SHOW TABLES", "TABLE logs", "TRUNCATE x", "MERGE INTO x USING y ON 1=1",
                                 "1", "'SELECT'", "", "   ", "-- only a comment", "/* c */"])
def test_other_first_tokens_refused(sql):
    refused(sql)


@pytest.mark.parametrize("kw", DENY_KEYWORDS)
def test_deny_keywords_refused_anywhere(kw):
    refused("SELECT 1 %s" % kw)
    refused("SELECT 1 %s" % kw.lower())
    refused("WITH a AS (SELECT 1) SELECT * FROM a WHERE x IN (%s)" % kw)


def test_refuses_set_and_attach_statements():
    refused("SET enable_external_access=true")
    refused("ATTACH '/tmp/x.db' AS x")
    refused("COPY logs TO '/tmp/x.csv'")
    refused("PRAGMA database_list")
    refused("INSTALL httpfs")
    refused("LOAD httpfs")
    refused("CALL pragma_version()")
    refused("CREATE TABLE x AS SELECT 1")
    refused("WITH x AS (SELECT 1) INSERT INTO t SELECT * FROM x")


# ---- functions (R6) -------------------------------------------------------------------------

@pytest.mark.parametrize("sql", [
    "SELECT * FROM read_parquet('/x')",
    "SELECT * FROM READ_CSV('/x')",
    "SELECT * FROM read_csv_auto ('/x')",
    "SELECT * FROM read_text('/x')",
    "SELECT * FROM read_blob('/x')",
    "SELECT * FROM read_json_objects('/x')",
    "FROM glob('*')",
    "FROM GLOB ('*')",
    "SELECT * FROM parquet_scan('/x')",
    "SELECT * FROM csv_scan('/x')",
    "SELECT * FROM anything_scan('/x')",
    "SELECT * FROM sniff_csv('/x')",
    "SELECT * FROM query('select 1')",
    "SELECT * FROM query_table('logs')",
    "SELECT getenv('HOME')",
    "SELECT * FROM main.read_csv('/x')",
    'SELECT * FROM "read_csv"(\'/x\')',
    'SELECT * FROM main."read_csv" (\'/x\')',
    "SELECT * FROM read_csv /* c */ ('/x')",
    "SELECT * FROM read_csv -- c\n('/x')",
    "SELECT * FROM parquet_metadata('/x')",
    "SELECT * FROM duckdb_settings()",
    "SELECT * FROM pragma_database_list()",
    "SELECT current_setting('home_directory')",
    "SELECT json_execute_serialized_sql('{}')",
])
def test_refuses_read_functions(sql):
    refused(sql)


def test_identifiers_named_like_functions_are_not_refused():
    assert sqlguard.check("SELECT read_csv, glob, query, getenv FROM logs")
    assert sqlguard.check("SELECT x AS read_things FROM logs WHERE y GLOB 'a*'")
    assert sqlguard.check("SELECT 'read_csv(' AS s")
    assert sqlguard.check("SELECT count(*), lower(x), getvariable('object') FROM logs")


# ---- lexer agreement with DuckDB ------------------------------------------------------------

@pytest.mark.parametrize("sql", [
    "SELECT E'\\''; COPY (SELECT 1) TO '/tmp/x' --'",
    "SELECT e'a'",
    "SELECT U&'\\0041'",
    'SELECT * FROM U&"read\\005fcsv"(\'/x\')',
    "SELECT $$a$$",
    "SELECT $tag$a$tag$",
    "SELECT $1",
    "SELECT 1 /* a /* b */ COPY x */",
    "SELECT 1 /* never closed",
    "SELECT 'never closed",
    'SELECT "never closed',
    "SELECT 1\x00",
    "SELECT 1\x1b[0m",
    "SELECT 1\x7f",
    "SELECT ('a'",
    "SELECT 1)",
    "SELECT 1) AS q UNION ALL SELECT 2 --",
])
def test_ambiguous_or_malformed_text_refused(sql):
    refused(sql)


def test_dollar_and_e_inside_strings_are_fine():
    assert sqlguard.check("SELECT regexp_matches(x, '^a$') FROM logs")
    assert sqlguard.check("SELECT 'E', 'e''x' AS e FROM logs")
    assert sqlguard.check("SELECT type, ee, x_e FROM logs")      # identifiers ending in e/E next to nothing quoted


def test_string_or_path_after_from_is_refused():
    refused("SELECT * FROM '/etc/passwd'")
    refused("SELECT * FROM logs JOIN 'x.csv' ON 1=1")
    refused('SELECT * FROM "/etc/passwd"')
    refused('SELECT * FROM "x.parquet"')
    assert sqlguard.check('SELECT * FROM "logs"')
    assert sqlguard.check("SELECT * FROM logs WHERE a = 'FROM' AND b = '/api'")
    assert sqlguard.check("SELECT extract(year FROM ts) FROM logs")


# ---- dot-commands (R11) ---------------------------------------------------------------------

@pytest.mark.parametrize("sql", [
    ".shell id",
    "  .shell id",
    "\t.shell id",
    "SELECT 1\n.shell id",
    "SELECT 1\n   .shell id",
    "SELECT 1\r.shell id",
    "SELECT 1\r\n.shell id",
    "SELECT 1\x0b.shell id",
    "SELECT 1\x0c.shell id",
    "SELECT 1\x85.shell id",
    "SELECT 1 .shell id",
    "SELECT 1 .shell id",
    "SELECT 1\x1c.shell id",
    "SELECT 1\n.shell id\n",
    "SELECT 1 /* x\n.shell id */",
    "SELECT 'x\n.shell id'",
    "SELECT 1 -- c\n.shell id",
    "SELECT 1;\n.shell id",
    "SELECT 1;\r.shell id",
    "SELECT 1\n.",
])
def test_dot_command_lines_refused(sql):
    refused(sql)


def test_dot_in_middle_of_line_is_fine():
    assert sqlguard.check("SELECT q.a FROM logs AS q")
    assert sqlguard.check("SELECT 1.5, 'a.b' FROM logs")


def test_dot_line_created_by_comment_removal_is_refused():
    # raw line 2 starts with '/', but once the comment is gone the line would start with '.'
    refused("SELECT q\n/* c */ .a FROM logs AS q")


# ---- limits ---------------------------------------------------------------------------------

def test_overlong_sql_refused():
    refused("SELECT '" + "a" * sqlguard.MAX_SQL_CHARS + "'")


def test_non_string_refused():
    refused(None)       # type: ignore[arg-type]
    refused(b"SELECT 1")  # type: ignore[arg-type]


# ---- named files (light check) --------------------------------------------------------------

def test_named_check_accepts_plain_select_with_comment_header():
    sql = "-- purpose\nSELECT a FROM logs WHERE b = getvariable('b')\n"
    assert sqlguard.check_named(sql) == "SELECT a FROM logs WHERE b = getvariable('b')"
    assert sqlguard.check_named("WITH a AS (SELECT 1) SELECT * FROM a;")
    assert sqlguard.check_named("FROM logs")


@pytest.mark.parametrize("sql", [
    "COPY logs TO '/tmp/x'",
    "DESCRIBE logs",
    "SUMMARIZE logs",
    "SELECT 1; SELECT 2",
    "SELECT 1\n.shell id",
    "SELECT 1\r.shell id",
    "SELECT (1",
    "",
    "-- only a comment\n",
    "SELECT 'x",
])
def test_named_check_fails_closed(sql):
    refused(sql, sqlguard.check_named)
