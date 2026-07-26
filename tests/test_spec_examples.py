"""Every example manifest in spec/examples must pass the schema."""

from __future__ import annotations

import json

import jsonschema
import pytest
import yaml

from tests.conftest import REPO_ROOT

SCHEMA_PATH = REPO_ROOT / "spec" / "shelf.schema.json"
EXAMPLES = sorted((REPO_ROOT / "spec" / "examples").glob("*/shelf.yml"))


def test_examples_exist() -> None:
    assert len(EXAMPLES) >= 3


@pytest.mark.parametrize("example", EXAMPLES, ids=lambda p: p.parent.name)
def test_example_validates(example) -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    data = yaml.safe_load(example.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema).validate(data)


def test_packaged_schema_matches_canonical() -> None:
    """The engine must load the same schema the spec publishes."""
    from shelf_spec.engine.manifest import load_schema

    canonical = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert load_schema() == canonical
