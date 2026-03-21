"""Satisfactory AI - AI-powered factory analyzer for Satisfactory."""

__version__ = "0.1.0"
__author__ = "Brian Hopkins"
__license__ = "MIT"

from .analyze_factory import FactoryAnalyzer
from .cli import cli
from .parse_save import parse_save_file

__all__ = ["cli", "parse_save_file", "FactoryAnalyzer"]
