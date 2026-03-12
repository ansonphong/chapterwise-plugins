#!/usr/bin/env python3
"""Tests for insert_engine module."""
import pytest
from insert_engine import InsertEngine


class TestInsertEngineSmoke:
    """Smoke test to verify imports work."""

    def test_import(self):
        engine = InsertEngine()
        assert engine is not None
