"""
Tests for summaries/registry.py

Covers: register(), get(), list_all(), error cases.
"""

import pytest
from summaries.registry import SummaryRegistry
from summaries.base import BaseSummary


# ---------------------------------------------------------------------------
# Helpers — minimal concrete summary classes used only in these tests
# ---------------------------------------------------------------------------

def _make_summary_class(name, description="Test summary"):
    """Factory to create a minimal concrete BaseSummary subclass."""
    class _Summary(BaseSummary):
        def required_files(self, **kw):
            return {}
        def generate(self, **kw):
            return None
    _Summary.name        = name
    _Summary.description = description
    return _Summary


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def fresh_registry():
    """Return an empty registry (isolated from the global singleton)."""
    return SummaryRegistry()


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

class TestRegister:

    def test_register_and_retrieve_by_name(self, fresh_registry):
        cls = _make_summary_class("my_summary")
        fresh_registry.register(cls)
        instance = fresh_registry.get("my_summary")
        assert isinstance(instance, cls)

    def test_register_returns_class_unchanged(self, fresh_registry):
        """register() must return the class so it works as a decorator."""
        cls = _make_summary_class("decorator_test")
        result = fresh_registry.register(cls)
        assert result is cls

    def test_register_multiple_summaries(self, fresh_registry):
        for name in ("alpha", "beta", "gamma"):
            fresh_registry.register(_make_summary_class(name))
        assert set(fresh_registry.list_all().keys()) == {"alpha", "beta", "gamma"}

    def test_register_duplicate_name_raises_value_error(self, fresh_registry):
        cls_a = _make_summary_class("duplicate")
        cls_b = _make_summary_class("duplicate")
        fresh_registry.register(cls_a)
        with pytest.raises(ValueError, match="already registered"):
            fresh_registry.register(cls_b)

    def test_register_class_without_name_raises_value_error(self, fresh_registry):
        cls = _make_summary_class("")   # empty name
        with pytest.raises(ValueError, match="non-empty 'name'"):
            fresh_registry.register(cls)

    def test_register_class_without_name_attribute_raises_value_error(self, fresh_registry):
        class NoName(BaseSummary):
            description  = "no name"
            required_files = lambda self, **kw: {}
            generate       = lambda self, **kw: None
        with pytest.raises((ValueError, AttributeError)):
            fresh_registry.register(NoName)


# ---------------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------------

class TestGet:

    def test_get_unknown_name_raises_key_error(self, fresh_registry):
        with pytest.raises(KeyError, match="Unknown summary type"):
            fresh_registry.get("does_not_exist")

    def test_get_error_message_lists_available_types(self, fresh_registry):
        fresh_registry.register(_make_summary_class("known_one"))
        with pytest.raises(KeyError, match="known_one"):
            fresh_registry.get("typo_name")

    def test_get_returns_new_instance_each_time(self, fresh_registry):
        cls = _make_summary_class("singleton_check")
        fresh_registry.register(cls)
        inst_a = fresh_registry.get("singleton_check")
        inst_b = fresh_registry.get("singleton_check")
        assert inst_a is not inst_b


# ---------------------------------------------------------------------------
# list_all()
# ---------------------------------------------------------------------------

class TestListAll:

    def test_list_all_empty_registry(self, fresh_registry):
        assert fresh_registry.list_all() == {}

    def test_list_all_returns_name_description_pairs(self, fresh_registry):
        fresh_registry.register(_make_summary_class("s1", "First summary"))
        fresh_registry.register(_make_summary_class("s2", "Second summary"))
        result = fresh_registry.list_all()
        assert result == {"s1": "First summary", "s2": "Second summary"}

    def test_list_all_is_sorted_by_name(self, fresh_registry):
        for name in ("zebra", "apple", "mango"):
            fresh_registry.register(_make_summary_class(name))
        keys = list(fresh_registry.list_all().keys())
        assert keys == sorted(keys)
