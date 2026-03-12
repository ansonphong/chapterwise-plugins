#!/usr/bin/env python3
"""Tests for location_finder module."""
import pytest
from location_finder import LocationFinder


class TestLocationFinderSmoke:
    """Smoke test to verify imports work."""

    def test_import(self):
        finder = LocationFinder()
        assert finder is not None
