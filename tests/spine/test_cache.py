"""A-2 pipeline integration — content-addressed cache + reroll boundary (D-RR).
The invariant: creative nodes (S3/S5/LLM_META) fold creative_epoch into the key
(so a reroll invalidates them) while deterministic nodes (S1/S2) do not (always
reused). Previously uncovered directly.

Reference: PRD §7 ALWAYS · workflow.md §4 [DESIGN] D-RR.
"""
from __future__ import annotations

import sqlite3

from shorts_forge.spine import cache as C


def test_file_hash_deterministic(tmp_path):
    f = tmp_path / "x.bin"
    f.write_bytes(b"hello world")
    assert C.file_hash(f) == C.file_hash(f)


def test_creative_node_key_depends_on_epoch():
    k1 = C.cache_key("S3", "ch", "p", creative_epoch=1)
    k2 = C.cache_key("S3", "ch", "p", creative_epoch=2)
    assert k1 != k2, "creative node must invalidate across reroll epochs"


def test_deterministic_node_key_ignores_epoch():
    k1 = C.cache_key("S1", "ch", "p", creative_epoch=1)
    k2 = C.cache_key("S1", "ch", "p", creative_epoch=2)
    assert k1 == k2, "deterministic node must be reused across epochs"


def test_creative_node_set_is_exactly_s3_s5_llm():
    assert C.CREATIVE_NODES == frozenset({"S3", "S5", "LLM_META"})


def test_get_put_roundtrip():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("CREATE TABLE cache (content_hash TEXT PRIMARY KEY, stage TEXT, "
                 "artifact_path TEXT, created_at REAL)")
    assert C.get(conn, "abc") is None
    C.put(conn, "abc", "S1", "/art/x.png")
    assert C.get(conn, "abc") == "/art/x.png"
    # INSERT OR REPLACE — second put updates rather than duplicates
    C.put(conn, "abc", "S1", "/art/y.png")
    assert C.get(conn, "abc") == "/art/y.png"
