"""Tests for app/requirements/ — check_registered and check_lightneuron_registered."""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from app.utility.base_service import BaseService
from tests.conftest import _StubFact, _StubLink


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class DummyAgent:
    def __init__(self, paw):
        self.paw = paw


def _make_link(used_values):
    """Create a stub link with used facts."""
    facts = [_StubFact(trait='agent_paw', value=v) for v in used_values]
    return _StubLink(command='cmd', paw='test', used=facts)


class DummyOperation:
    def __init__(self, active_paws):
        self._active_paws = active_paws

    async def active_agents(self):
        return [DummyAgent(paw) for paw in self._active_paws]


# ---------------------------------------------------------------------------
# Tests — check_registered (Requirement)
# ---------------------------------------------------------------------------

class TestCheckRegistered:
    def _get_requirement(self):
        from plugins.emu.app.requirements.check_registered import Requirement
        return Requirement()

    async def test_enforce_true_when_agent_active(self):
        req = self._get_requirement()
        op = DummyOperation(active_paws=['paw1', 'paw2'])
        link = _make_link(['paw1'])
        result = await req.enforce(link, op)
        assert result is True

    async def test_enforce_false_when_agent_inactive(self):
        req = self._get_requirement()
        op = DummyOperation(active_paws=['paw2', 'paw3'])
        link = _make_link(['paw1'])
        result = await req.enforce(link, op)
        assert result is False

    async def test_enforce_false_empty_used(self):
        req = self._get_requirement()
        op = DummyOperation(active_paws=['paw1'])
        link = _make_link([])
        result = await req.enforce(link, op)
        assert result is False

    async def test_enforce_false_no_active_agents(self):
        req = self._get_requirement()
        op = DummyOperation(active_paws=[])
        link = _make_link(['paw1'])
        result = await req.enforce(link, op)
        assert result is False

    async def test_enforce_multiple_used_first_matches(self):
        req = self._get_requirement()
        op = DummyOperation(active_paws=['paw1'])
        link = _make_link(['paw1', 'paw2'])
        result = await req.enforce(link, op)
        assert result is True

    async def test_enforce_multiple_used_second_matches(self):
        req = self._get_requirement()
        op = DummyOperation(active_paws=['paw2'])
        link = _make_link(['paw1', 'paw2'])
        result = await req.enforce(link, op)
        assert result is True


# ---------------------------------------------------------------------------
# Tests — check_lightneuron_registered (Requirement)
# ---------------------------------------------------------------------------

class TestCheckLightneuronRegistered:
    def _get_requirement(self):
        from plugins.emu.app.requirements.check_lightneuron_registered import Requirement
        return Requirement()

    def _setup_data_svc(self, agent_paws):
        """Set up a mock data_svc with agents in its ram dict."""
        agents = [DummyAgent(paw) for paw in agent_paws]
        data_svc = MagicMock()
        data_svc.ram = {'agents': agents}
        BaseService._services['data_svc'] = data_svc
        return data_svc

    async def test_enforce_true_exact_match(self):
        req = self._get_requirement()
        self._setup_data_svc(['paw1', 'paw2'])
        link = _make_link(['paw1'])
        result = await req.enforce(link, MagicMock())
        assert result is True

    async def test_enforce_true_with_at_symbol(self):
        """The lightneuron requirement strips @ from values."""
        req = self._get_requirement()
        self._setup_data_svc(['paw1', 'paw2'])
        link = _make_link(['p@aw1'])
        result = await req.enforce(link, MagicMock())
        assert result is True

    async def test_enforce_false_no_match(self):
        req = self._get_requirement()
        self._setup_data_svc(['paw1', 'paw2'])
        link = _make_link(['paw99'])
        result = await req.enforce(link, MagicMock())
        assert result is False

    async def test_enforce_false_empty_used(self):
        req = self._get_requirement()
        self._setup_data_svc(['paw1'])
        link = _make_link([])
        result = await req.enforce(link, MagicMock())
        assert result is False

    async def test_enforce_false_no_agents(self):
        req = self._get_requirement()
        self._setup_data_svc([])
        link = _make_link(['paw1'])
        result = await req.enforce(link, MagicMock())
        assert result is False

    async def test_enforce_at_symbol_stripped_multiple(self):
        """Multiple @ symbols should all be removed."""
        req = self._get_requirement()
        self._setup_data_svc(['abc'])
        link = _make_link(['a@b@c'])
        result = await req.enforce(link, MagicMock())
        assert result is True

    async def test_enforce_multiple_used_facts(self):
        req = self._get_requirement()
        self._setup_data_svc(['paw2'])
        link = _make_link(['paw1', 'paw2'])
        result = await req.enforce(link, MagicMock())
        assert result is True
