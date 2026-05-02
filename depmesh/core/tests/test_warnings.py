from depmesh.core import warnings


class TestAdd:
    def test_adds_warning(self) -> None:
        warnings.clear()

        warnings.add("message")

        assert warnings.read() == ["message"]

        warnings.clear()


class TestRead:
    def test_preserves_insertion_order(self) -> None:
        warnings.clear()

        warnings.add("first")
        warnings.add("second")

        assert warnings.read() == ["first", "second"]

        warnings.clear()

    def test_returns_copy(self) -> None:
        warnings.clear()
        warnings.add("message")

        stored_warnings = warnings.read()
        stored_warnings.append("changed")

        assert warnings.read() == ["message"]

        warnings.clear()


class TestClear:
    def test_removes_all_warnings(self) -> None:
        warnings.clear()
        warnings.add("message")

        warnings.clear()

        assert warnings.read() == []
