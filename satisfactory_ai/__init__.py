"""Satisfactory AI - AI-powered factory analyzer for Satisfactory."""

__version__ = "0.1.0"
__author__ = "Brian Hopkins"
__license__ = "MIT"

from .cli import cli
from .parse_save import parse_save_file
from .analyze_factory import FactoryAnalyzer

__all__ = ["cli", "parse_save_file", "FactoryAnalyzer"]
