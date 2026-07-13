"""Shared fixtures for emu plugin tests."""
import asyncio
import os
import yaml
import pytest

from unittest.mock import MagicMock, AsyncMock, patch


def async_mock_return(to_return):
    """Helper to create a resolved Future with a given value."""
    mock_future = asyncio.Future()
    mock_future.set_result(to_return)
    return mock_future


# ---------------------------------------------------------------------------
# Lightweight stubs for caldera framework objects that are not available
# when running the emu plugin tests in isolation.
# ---------------------------------------------------------------------------

class _StubBaseWorld:
    """Minimal stand-in for app.utility.base_world.BaseWorld."""

    class Access:
        RED = 'red'
        BLUE = 'blue'

    _configs = {}

    @classmethod
    def apply_config(cls, name, config):
        cls._configs[name] = config

    @classmethod
    def strip_yml(cls, path):
        if os.path.exists(path):
            with open(path, 'r') as fh:
                return list(yaml.safe_load_all(fh))
        return [{}]

    @classmethod
    def get_config(cls, name='main', prop=None):
        cfg = cls._configs.get(name, {})
        if prop:
            return cfg.get(prop)
        return cfg

    @staticmethod
    def create_logger(name):
        import logging
        return logging.getLogger(name)


class _StubBaseService(_StubBaseWorld):
    """Minimal stand-in for app.utility.base_service.BaseService."""
    _services = {}

    @classmethod
    def add_service(cls, name, svc):
        cls._services[name] = svc
        import logging
        return logging.getLogger(name)

    @classmethod
    def get_service(cls, name):
        return cls._services.get(name)


class _StubBaseParser:
    """Minimal stand-in for app.utility.base_parser.BaseParser."""

    def __init__(self):
        self.mappers = []
        self.used_facts = []

    def set_value(self, key, value, used_facts):
        return value


class _StubFact:
    """Minimal stand-in for app.objects.secondclass.c_fact.Fact."""

    def __init__(self, trait=None, value=None):
        self.trait = trait
        self.value = value

    def __eq__(self, other):
        return isinstance(other, _StubFact) and self.trait == other.trait and self.value == other.value

    def __repr__(self):
        return f'Fact(trait={self.trait!r}, value={self.value!r})'


class _StubRelationship:
    """Minimal stand-in for app.objects.secondclass.c_relationship.Relationship."""

    def __init__(self, source=None, edge=None, target=None):
        self.source = source
        self.edge = edge
        self.target = target


class _StubLink:
    """Minimal stand-in for app.objects.secondclass.c_link.Link."""

    def __init__(self, command='', paw='', ability=None, **kwargs):
        self.command = command
        self.paw = paw
        self.ability = ability
        self.used = kwargs.get('used', [])
        self.id = kwargs.get('id', '')


class _StubBaseRequirement:
    """Minimal stand-in for plugins.stockpile.app.requirements.base_requirement.BaseRequirement."""
    pass


# ---------------------------------------------------------------------------
# Patch caldera imports before any plugin code is imported
# ---------------------------------------------------------------------------

import sys

# Build module stubs
_base_world_mod = type(sys)('app.utility.base_world')
_base_world_mod.BaseWorld = _StubBaseWorld
_base_service_mod = type(sys)('app.utility.base_service')
_base_service_mod.BaseService = _StubBaseService
_base_parser_mod = type(sys)('app.utility.base_parser')
_base_parser_mod.BaseParser = _StubBaseParser
_fact_mod = type(sys)('app.objects.secondclass.c_fact')
_fact_mod.Fact = _StubFact
_rel_mod = type(sys)('app.objects.secondclass.c_relationship')
_rel_mod.Relationship = _StubRelationship
_link_mod = type(sys)('app.objects.secondclass.c_link')
_link_mod.Link = _StubLink
_auth_svc_mod = type(sys)('app.service.auth_svc')
_auth_svc_mod.for_all_public_methods = lambda func: lambda cls: cls
_auth_svc_mod.check_authorization = lambda func: func
_base_req_mod = type(sys)('plugins.stockpile.app.requirements.base_requirement')
_base_req_mod.BaseRequirement = _StubBaseRequirement

# Register in sys.modules (only if not already present — CI may have real caldera)
_stubs = {
    'app': type(sys)('app'),
    'app.utility': type(sys)('app.utility'),
    'app.utility.base_world': _base_world_mod,
    'app.utility.base_service': _base_service_mod,
    'app.utility.base_parser': _base_parser_mod,
    'app.objects': type(sys)('app.objects'),
    'app.objects.secondclass': type(sys)('app.objects.secondclass'),
    'app.objects.secondclass.c_fact': _fact_mod,
    'app.objects.secondclass.c_relationship': _rel_mod,
    'app.objects.secondclass.c_link': _link_mod,
    'app.service': type(sys)('app.service'),
    'app.service.auth_svc': _auth_svc_mod,
    'plugins': type(sys)('plugins'),
    'plugins.stockpile': type(sys)('plugins.stockpile'),
    'plugins.stockpile.app': type(sys)('plugins.stockpile.app'),
    'plugins.stockpile.app.requirements': type(sys)('plugins.stockpile.app.requirements'),
    'plugins.stockpile.app.requirements.base_requirement': _base_req_mod,
}

for mod_name, mod_obj in _stubs.items():
    sys.modules.setdefault(mod_name, mod_obj)

# Ensure the plugin package itself is importable from repo root
_repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

# Also make the plugin available as plugins.emu
_plugins_emu_mod = type(sys)('plugins.emu')
_plugins_emu_mod.__path__ = [_repo_root]
sys.modules.setdefault('plugins.emu', _plugins_emu_mod)

_plugins_emu_app_mod = type(sys)('plugins.emu.app')
_plugins_emu_app_mod.__path__ = [os.path.join(_repo_root, 'app')]
sys.modules.setdefault('plugins.emu.app', _plugins_emu_app_mod)


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def stub_fact_class():
    """Return the stub Fact class for use in tests."""
    return _StubFact


@pytest.fixture
def stub_link_class():
    """Return the stub Link class for use in tests."""
    return _StubLink


@pytest.fixture
def mock_app_svc():
    """Mock application service with a router."""
    svc = MagicMock()
    svc.application = MagicMock()
    svc.application.router = MagicMock()
    svc.application.router.add_route = MagicMock()
    return svc


@pytest.fixture
def mock_contact_svc():
    """Mock contact service."""
    svc = MagicMock()
    svc.handle_heartbeat = AsyncMock()
    return svc


@pytest.fixture
def tmp_data_dir(tmp_path):
    """Create a temporary data directory structure."""
    data = tmp_path / 'data'
    data.mkdir()
    (data / 'abilities').mkdir()
    (data / 'adversaries').mkdir()
    (data / 'sources').mkdir()
    (data / 'planners').mkdir()
    payloads = tmp_path / 'payloads'
    payloads.mkdir()
    return tmp_path
