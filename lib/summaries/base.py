"""
Base class for all Phorager summary types.

Each summary subclass must implement:
  - name (str)              : unique identifier used with --type
  - description (str)       : shown in phorager summarize --list
  - required_files(**dirs)  : returns {label: Path} for all mandatory inputs
  - generate(**dirs)        : reads those files and returns a pd.DataFrame

Optional overrides:
  - optional_files(**dirs)  : returns {label: Path} for inputs that trigger
                              a warning (not a failure) when absent
  - validate(**dirs)        : custom validation logic (default checks required_files)
"""

from abc import ABC, abstractmethod
from pathlib import Path


class BaseSummary(ABC):

    # -- Subclasses must set these as class attributes --
    name: str
    description: str

    @abstractmethod
    def required_files(self, **dirs) -> dict:
        """
        Return {label: Path} for every file that must exist before generate()
        is called. Validation fails hard if any of these are missing.
        """

    def optional_files(self, **dirs) -> dict:
        """
        Return {label: Path} for every file that is used when present but
        whose absence should only print a warning. Default: empty dict.
        """
        return {}

    @abstractmethod
    def generate(self, **dirs):
        """
        Read input files and return a tidy pd.DataFrame.
        Never writes files — the command layer handles output format/path.
        """

    def validate(self, **dirs) -> tuple:
        """
        Check required_files all exist and warn about missing optional_files.
        Returns (ok: bool, messages: list[str]).
        ok is False only if a required file is missing.
        """
        messages = []

        for label, path in self.required_files(**dirs).items():
            if not Path(path).exists():
                messages.append(f"  [REQUIRED] {label}: {path}")

        for label, path in self.optional_files(**dirs).items():
            if not Path(path).exists():
                messages.append(f"  [OPTIONAL] {label}: {path}  (column will be NA)")

        required_ok = not any("[REQUIRED]" in m for m in messages)
        return (required_ok, messages)
