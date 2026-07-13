"""Tests for hook.py — plugin enable function and module-level attributes."""
import os
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from app.utility.base_world import BaseWorld


class TestHookModuleAttributes:
    """Test the module-level constants in hook.py."""

    def test_name(self):
        from plugins.emu import hook
        assert hook.name == 'Emu'

    def test_description(self):
        from plugins.emu import hook
        assert isinstance(hook.description, str)
        assert len(hook.description) > 0

    def test_address(self):
        from plugins.emu import hook
        assert hook.address == '/plugin/emu/gui'

    def test_access(self):
        from plugins.emu import hook
        assert hook.access == BaseWorld.Access.RED

    def test_data_dir(self):
        from plugins.emu import hook
        expected = os.path.join('plugins', 'emu', 'data')
        assert hook.data_dir == expected


class TestHookEnable:
    """Test the enable() coroutine."""

    async def test_enable_clones_when_repo_missing(self):
        from plugins.emu import hook
        from plugins.emu.app.emu_svc import EmuService

        mock_app_svc = MagicMock()
        mock_app_svc.application = MagicMock()
        mock_app_svc.application.router = MagicMock()

        services = {
            'app_svc': mock_app_svc,
            'auth_svc': MagicMock(),
            'data_svc': MagicMock(),
        }

        with patch.object(BaseWorld, 'apply_config'):
            with patch.object(BaseWorld, 'strip_yml', return_value=[{'evals_c2_host': '127.0.0.1', 'evals_c2_port': 8888}]):
                with patch.object(BaseWorld, 'get_config', return_value=None):
                    with patch.object(os.path, 'isdir', return_value=False):
                        with patch.object(EmuService, 'clone_repo', new_callable=AsyncMock) as mock_clone:
                            with patch.object(EmuService, 'decrypt_payloads', new_callable=AsyncMock) as mock_decrypt:
                                with patch.object(EmuService, 'populate_data_directory', new_callable=AsyncMock) as mock_pop:
                                    await hook.enable(services)

        mock_clone.assert_awaited_once()
        mock_decrypt.assert_awaited_once()
        mock_pop.assert_awaited_once()

    async def test_enable_skips_clone_when_repo_exists(self):
        from plugins.emu import hook
        from plugins.emu.app.emu_svc import EmuService

        mock_app_svc = MagicMock()
        mock_app_svc.application = MagicMock()
        mock_app_svc.application.router = MagicMock()

        services = {
            'app_svc': mock_app_svc,
            'auth_svc': MagicMock(),
            'data_svc': MagicMock(),
        }

        with patch.object(BaseWorld, 'apply_config'):
            with patch.object(BaseWorld, 'strip_yml', return_value=[{'evals_c2_host': '127.0.0.1', 'evals_c2_port': 8888}]):
                with patch.object(BaseWorld, 'get_config', return_value=None):
                    with patch.object(os.path, 'isdir', return_value=True):
                        with patch.object(EmuService, 'clone_repo', new_callable=AsyncMock) as mock_clone:
                            with patch.object(EmuService, 'decrypt_payloads', new_callable=AsyncMock):
                                with patch.object(EmuService, 'populate_data_directory', new_callable=AsyncMock):
                                    await hook.enable(services)

        mock_clone.assert_not_awaited()

    async def test_enable_adds_gui_route(self):
        from plugins.emu import hook

        mock_app_svc = MagicMock()
        mock_app_svc.application = MagicMock()
        mock_router = MagicMock()
        mock_app_svc.application.router = mock_router

        services = {
            'app_svc': mock_app_svc,
            'auth_svc': MagicMock(),
            'data_svc': MagicMock(),
        }

        with patch.object(BaseWorld, 'apply_config'):
            with patch.object(BaseWorld, 'strip_yml', return_value=[{'evals_c2_host': '127.0.0.1', 'evals_c2_port': 8888}]):
                with patch.object(BaseWorld, 'get_config', return_value=None):
                    with patch.object(os.path, 'isdir', return_value=True):
                        from plugins.emu.app.emu_svc import EmuService
                        with patch.object(EmuService, 'decrypt_payloads', new_callable=AsyncMock):
                            with patch.object(EmuService, 'populate_data_directory', new_callable=AsyncMock):
                                await hook.enable(services)

        # Should have registered GET /plugin/emu/gui route
        route_calls = mock_router.add_route.call_args_list
        get_routes = [c for c in route_calls if c[0][0] == 'GET' and c[0][1] == '/plugin/emu/gui']
        assert len(get_routes) >= 1
