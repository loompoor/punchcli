from __future__ import annotations

import pytest

from punchcli.core.validate import (
    MAX_MESSAGE_LEN,
    MAX_TAGS,
    ValidationError,
    parse_tags,
    validate_message,
)


class TestParseTags:
    @pytest.mark.parametrize("raw", [None, "", "   ", ",,"])
    def test_none_or_empty(self, raw: str | None) -> None:
        assert parse_tags(raw) == []

    def test_single(self) -> None:
        assert parse_tags("backend") == ["backend"]

    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("Backend", ["backend"]),
            ("BACKEND,Bug", ["backend", "bug"]),
            (" a , b ,c", ["a", "b", "c"]),
            ("a-b,c_d,123", ["a-b", "c_d", "123"]),
        ],
    )
    def test_lowercased_and_stripped(self, raw: str, expected: list[str]) -> None:
        assert parse_tags(raw) == expected

    def test_dedupe_preserves_order(self) -> None:
        assert parse_tags("a,b,a,c,b") == ["a", "b", "c"]

    @pytest.mark.parametrize("raw", ["bad!!", "with space", "emoji😀"])
    def test_invalid_chars_rejected(self, raw: str) -> None:
        with pytest.raises(ValidationError):
            parse_tags(raw)

    def test_tag_length_limit(self) -> None:
        assert parse_tags("a" * 32) == ["a" * 32]
        with pytest.raises(ValidationError):
            parse_tags("a" * 33)

    def test_max_tags_cap(self) -> None:
        ok = ",".join(f"t{i}" for i in range(MAX_TAGS))
        assert len(parse_tags(ok)) == MAX_TAGS

    def test_too_many_rejected(self) -> None:
        too_many = ",".join(f"t{i}" for i in range(MAX_TAGS + 1))
        with pytest.raises(ValidationError, match="Too many tags"):
            parse_tags(too_many)

    def test_dedupe_then_count(self) -> None:
        assert len(parse_tags("a,a,b,b,c,c,d,d,e,e")) == 5


class TestValidateMessage:
    def test_none_passes(self) -> None:
        assert validate_message(None) is None

    def test_normal(self) -> None:
        assert validate_message("hello") == "hello"

    def test_max_len_ok(self) -> None:
        s = "x" * MAX_MESSAGE_LEN
        assert validate_message(s) == s

    def test_too_long_rejected(self) -> None:
        with pytest.raises(ValidationError, match="exceeds"):
            validate_message("x" * (MAX_MESSAGE_LEN + 1))

    def test_newline_rejected(self) -> None:
        with pytest.raises(ValidationError, match="newline"):
            validate_message("line1\nline2")
