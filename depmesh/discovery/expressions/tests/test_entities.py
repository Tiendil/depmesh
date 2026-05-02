from __future__ import annotations

from depmesh.discovery.expressions.entities import TemplateText
from depmesh.discovery.matchers import CaptureName


class TestTemplateText:
    def test_variables__extracts_unique_template_variables(self) -> None:
        template = TemplateText("./src/{module}/{module}_{kind}.py")

        assert template.variables == frozenset(
            {
                CaptureName("kind"),
                CaptureName("module"),
            }
        )

    def test_substitute__replaces_captures(self) -> None:
        template = TemplateText("./tests/test_{module}.py")

        assert template.substitute({"module": "a"}) == "./tests/test_a.py"

    def test_model_validate__accepts_raw_string(self) -> None:
        template = TemplateText.model_validate(" ./tests/test_{module}.py ")

        assert template.value == "./tests/test_{module}.py"
