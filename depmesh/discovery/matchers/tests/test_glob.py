from __future__ import annotations

from pathlib import Path

import pytest

from depmesh.discovery.matchers.glob import GlobMatcher, _compile_glob, _parse_capture
from depmesh.discovery.matchers.entities import CaptureName
from depmesh.domain.entities import ArtifactId


class TestParseCapture:
    def test_star_capture(self) -> None:
        assert _parse_capture("*module") == ("*", "module")

    def test_double_star_capture(self) -> None:
        assert _parse_capture("**package") == ("**", "package")

    def test_missing_wildcard(self) -> None:
        with pytest.raises(ValueError, match="invalid glob capture"):
            _parse_capture("module")

    def test_invalid_capture_name(self) -> None:
        with pytest.raises(ValueError, match="invalid glob capture name"):
            _parse_capture("*1module")


class TestCompileGlob:
    def test_question_mark__matches_one_character_inside_segment(self) -> None:
        regex = _compile_glob("./src/a?.py")

        assert regex.fullmatch("./src/ab.py") is not None
        assert regex.fullmatch("./src/a/b.py") is None

    def test_star__matches_zero_or_more_characters_inside_segment(self) -> None:
        regex = _compile_glob("./src/*.py")

        assert regex.fullmatch("./src/a.py") is not None
        assert regex.fullmatch("./src/.py") is not None
        assert regex.fullmatch("./src/a/b.py") is None

    def test_double_star__matches_nested_segments(self) -> None:
        regex = _compile_glob("./src/**/*.py")

        assert regex.fullmatch("./src/a/b.py") is not None
        assert regex.fullmatch("./src/b.py") is not None

    def test_double_star_without_trailing_slash__matches_any_characters(self) -> None:
        regex = _compile_glob("./src/**")

        assert regex.fullmatch("./src/a/b.py") is not None

    def test_star_capture__captures_inside_one_segment(self) -> None:
        regex = _compile_glob("./src/{*module}.py")

        match = regex.fullmatch("./src/a.py")

        assert match is not None
        assert match.groupdict() == {"module": "a"}
        assert regex.fullmatch("./src/a/b.py") is None

    def test_double_star_capture__captures_nested_segments(self) -> None:
        regex = _compile_glob("./src/{**package}/test_{*module}.py")

        match = regex.fullmatch("./src/a/b/test_core.py")

        assert match is not None
        assert match.groupdict() == {"package": "a/b", "module": "core"}

    def test_double_star_capture__captures_zero_segments(self) -> None:
        regex = _compile_glob("./src/{**package}/test_{*module}.py")

        match = regex.fullmatch("./src/test_core.py")

        assert match is not None
        assert match.groupdict() == {"package": None, "module": "core"}

    def test_double_star_capture_without_trailing_slash__captures_any_characters(self) -> None:
        regex = _compile_glob("./src/{**package}.py")

        match = regex.fullmatch("./src/a/b.py")

        assert match is not None
        assert match.groupdict() == {"package": "a/b"}

    def test_unclosed_capture__is_treated_as_literal(self) -> None:
        regex = _compile_glob("./src/{module.py")

        assert regex.fullmatch("./src/{module.py") is not None

    def test_literal_characters__are_escaped(self) -> None:
        regex = _compile_glob("./src/a.b.py")

        assert regex.fullmatch("./src/a.b.py") is not None
        assert regex.fullmatch("./src/axb.py") is None


class TestGlobMatcher:
    def test_captures__extracts_capture_names(self) -> None:
        matcher = GlobMatcher(type="glob", pattern="./src/{**package}/{*module}.py")

        assert matcher.captures() == {CaptureName("module"), CaptureName("package")}

    def test_captures__invalid_capture_name(self) -> None:
        matcher = GlobMatcher(type="glob", pattern="./src/{*1module}.py")

        with pytest.raises(ValueError, match="invalid glob capture name"):
            matcher.captures()

    def test_captures__capture_without_wildcard(self) -> None:
        matcher = GlobMatcher(type="glob", pattern="./src/{module}.py")

        with pytest.raises(ValueError, match="invalid glob capture"):
            matcher.captures()

    def test_match__success(self, tmp_path: Path) -> None:
        matcher = GlobMatcher(type="glob", pattern="./src/{*module}.py")

        assert matcher.match(ArtifactId("./src/a.py"), tmp_path) == {"module": "a"}

    def test_match__double_star_capture_matches_zero_segments(self, tmp_path: Path) -> None:
        matcher = GlobMatcher(type="glob", pattern="./src/{**package}/test_{*module}.py")

        assert matcher.match(ArtifactId("./src/test_core.py"), tmp_path) == {
            "package": "",
            "module": "core",
        }

    def test_match__no_match(self, tmp_path: Path) -> None:
        matcher = GlobMatcher(type="glob", pattern="./src/{*module}.py")

        assert matcher.match(ArtifactId("./docs/a.md"), tmp_path) is None
