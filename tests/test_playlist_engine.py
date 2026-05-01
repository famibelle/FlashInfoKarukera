#!/usr/bin/env python3
"""
Unit tests for Spotify Playlist Engine

Run with: python -m pytest tests/test_playlist_engine.py -v
"""

import pytest
from datetime import datetime
from playlist_engine import (
    RadioMode,
    RADIO_CONFIG,
    get_radio_mode,
    build_playlist
)


class TestRadioModeDetection:
    """Test radio mode detection based on hour"""

    def test_morning_mode(self):
        """Test morning mode detection (6:00 - 11:59)"""
        assert get_radio_mode(6) == RadioMode.MORNING
        assert get_radio_mode(9) == RadioMode.MORNING
        assert get_radio_mode(11) == RadioMode.MORNING

    def test_midday_mode(self):
        """Test midday mode detection (12:00 - 17:59)"""
        assert get_radio_mode(12) == RadioMode.MIDDAY
        assert get_radio_mode(15) == RadioMode.MIDDAY
        assert get_radio_mode(17) == RadioMode.MIDDAY

    def test_evening_mode(self):
        """Test evening mode detection (18:00 - 5:59)"""
        assert get_radio_mode(18) == RadioMode.EVENING
        assert get_radio_mode(23) == RadioMode.EVENING
        assert get_radio_mode(0) == RadioMode.EVENING
        assert get_radio_mode(5) == RadioMode.EVENING

    def test_boundary_conditions(self):
        """Test boundary hours"""
        # Transition from EVENING to MORNING
        assert get_radio_mode(5) == RadioMode.EVENING
        assert get_radio_mode(6) == RadioMode.MORNING

        # Transition from MORNING to MIDDAY
        assert get_radio_mode(11) == RadioMode.MORNING
        assert get_radio_mode(12) == RadioMode.MIDDAY

        # Transition from MIDDAY to EVENING
        assert get_radio_mode(17) == RadioMode.MIDDAY
        assert get_radio_mode(18) == RadioMode.EVENING

        # Transition from EVENING to EVENING (midnight)
        assert get_radio_mode(23) == RadioMode.EVENING
        assert get_radio_mode(0) == RadioMode.EVENING


class TestRadioConfig:
    """Test radio configuration"""

    def test_config_keys(self):
        """Test that all radio modes have required config keys"""
        required_keys = {"time_range", "genres", "queries", "energy_max", "description"}

        for mode in [RadioMode.MORNING, RadioMode.MIDDAY, RadioMode.EVENING]:
            assert mode in RADIO_CONFIG
            config = RADIO_CONFIG[mode]
            assert set(config.keys()) == required_keys

    def test_queries_not_empty(self):
        """Test that each mode has search queries"""
        for mode in [RadioMode.MORNING, RadioMode.MIDDAY, RadioMode.EVENING]:
            queries = RADIO_CONFIG[mode]["queries"]
            assert len(queries) > 0
            assert all(isinstance(q, str) for q in queries)
            assert all(len(q) > 0 for q in queries)

    def test_energy_max_valid(self):
        """Test that energy_max is between 0 and 1"""
        for mode in [RadioMode.MORNING, RadioMode.MIDDAY, RadioMode.EVENING]:
            energy_max = RADIO_CONFIG[mode]["energy_max"]
            assert 0 <= energy_max <= 1

    def test_modes_distinct(self):
        """Test that each mode has different characteristics"""
        morning = RADIO_CONFIG[RadioMode.MORNING]
        midday = RADIO_CONFIG[RadioMode.MIDDAY]
        evening = RADIO_CONFIG[RadioMode.EVENING]

        # Each should have unique queries
        assert set(morning["queries"]) != set(midday["queries"])
        assert set(midday["queries"]) != set(evening["queries"])
        assert set(morning["queries"]) != set(evening["queries"])


class TestPlaylistBuilding:
    """Test playlist building logic"""

    def test_radio_mode_values(self):
        """Test that RadioMode values are strings"""
        assert isinstance(RadioMode.MORNING, str)
        assert isinstance(RadioMode.MIDDAY, str)
        assert isinstance(RadioMode.EVENING, str)

    def test_radio_mode_uniqueness(self):
        """Test that radio modes are unique"""
        modes = [RadioMode.MORNING, RadioMode.MIDDAY, RadioMode.EVENING]
        assert len(modes) == len(set(modes))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
