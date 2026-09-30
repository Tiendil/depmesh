from depmesh.core import warnings


class TestAdd:
    def test_adds_warning(self) -> None:
        warnings.add("message")

        assert warnings.read() == ["message"]


class TestRead:
    def test_preserves_insertion_order(self) -> None:
        warnings.add("first")
        warnings.add("second")

        assert warnings.read() == ["first", "second"]

    def test_returns_copy(self) -> None:
        warnings.add("message")

        stored_warnings = warnings.read()
        stored_warnings.append("changed")

        assert warnings.read() == ["message"]


class TestClear:
    def test_removes_all_warnings(self) -> None:
        warnings.add("message")

        warnings.clear()

        assert warnings.read() == []
