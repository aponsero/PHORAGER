"""
Phorager Commands Module

Contains all command implementations for the phorager wrapper.
Each command is implemented as a separate class with consistent interface.
"""

from .config import ConfigCommand
from .install import InstallCommand
from .bacterial import BacterialCommand
from .prophage import ProphageCommand
from .annotation import AnnotationCommand

__all__ = ['ConfigCommand', 'InstallCommand', 'BacterialCommand', 'ProphageCommand','AnnotationCommand']