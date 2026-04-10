"""
Central registry for Phorager summary types.

Usage pattern:
  from summaries.registry import registry

  @registry.register
  class MySummary(BaseSummary):
      name = "my_summary"
      ...

The registry is populated automatically when the summaries package is
imported (via __init__.py auto-discovery). You never need to touch this
file to add a new summary.
"""


class SummaryRegistry:

    def __init__(self):
        self._summaries = {}

    def register(self, cls):
        """
        Register a BaseSummary subclass. Can be used as a decorator or
        called directly: registry.register(MySummary).
        Returns the class unchanged so decorator usage works cleanly.
        """
        if not hasattr(cls, 'name') or not cls.name:
            raise ValueError(
                f"Summary class {cls.__name__} must define a non-empty 'name' attribute."
            )
        if cls.name in self._summaries:
            raise ValueError(
                f"A summary named '{cls.name}' is already registered "
                f"(by {self._summaries[cls.name].__name__}). "
                f"Each summary must have a unique name."
            )
        self._summaries[cls.name] = cls
        return cls

    def get(self, name) -> object:
        """
        Return a fresh instance of the named summary.
        Raises KeyError with a helpful message if the name is unknown.
        """
        if name not in self._summaries:
            available = ", ".join(sorted(self._summaries.keys())) or "(none registered)"
            raise KeyError(
                f"Unknown summary type '{name}'. "
                f"Available types: {available}. "
                f"Use --list to see descriptions."
            )
        return self._summaries[name]()

    def list_all(self) -> dict:
        """Return {name: description} for all registered summaries, sorted by name."""
        return {
            name: cls.description
            for name, cls in sorted(self._summaries.items())
        }


# Module-level singleton — import this everywhere
registry = SummaryRegistry()
