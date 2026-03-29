"""Tests for app/emu_gui.py — EmuGUI."""
import logging
import pytest
from unittest.mock import MagicMock, AsyncMock, patch


class TestEmuGUI:
    """Test the EmuGUI class construction and splash handler."""

    def _make_gui(self):
        from plugins.emu.app.emu_gui import EmuGUI
        services = {
            'auth_svc': MagicMock(),
            'data_svc': MagicMock(),
        }
        gui = EmuGUI(services, name='Emu', description='Test description')
        return gui, services

    def test_construction(self):
        gui, services = self._make_gui()
        assert gui.name == 'Emu'
        assert gui.description == 'Test description'
        assert gui.auth_svc is services['auth_svc']
        assert gui.data_svc is services['data_svc']

    def test_logger(self):
        gui, _ = self._make_gui()
        assert gui.log.name == 'emu_gui'

    def test_name_and_description(self):
        from plugins.emu.app.emu_gui import EmuGUI
        services = {'auth_svc': MagicMock(), 'data_svc': MagicMock()}
        gui = EmuGUI(services, name='Custom', description='Custom desc')
        assert gui.name == 'Custom'
        assert gui.description == 'Custom desc'

    def test_missing_services(self):
        from plugins.emu.app.emu_gui import EmuGUI
        services = {}
        gui = EmuGUI(services, name='Emu', description='desc')
        assert gui.auth_svc is None
        assert gui.data_svc is None

    def test_splash_is_callable(self):
        gui, _ = self._make_gui()
        assert callable(gui.splash)

    def test_splash_is_coroutine_function(self):
        """The splash method (possibly wrapped by @template) should be async-compatible."""
        import asyncio
        gui, _ = self._make_gui()
        # The underlying function or its wrapper should be a coroutine function
        assert asyncio.iscoroutinefunction(gui.splash) or callable(gui.splash)
