"""Exhaustive tests for app/group_filtered_planner.py — LogicalPlanner."""
import pytest

from plugins.emu.app.group_filtered_planner import LogicalPlanner
from tests.conftest import _StubLink


BUCKET_NAME = 'fetch_and_run_links'


# ---------------------------------------------------------------------------
# Helpers / dummies
# ---------------------------------------------------------------------------

class DummyOperation:
    def __init__(self, dummy_adversary, dummy_agents):
        self.adversary = dummy_adversary
        self.agents = dummy_agents

    async def wait_for_links_completion(self, _):
        return

    async def apply(self, link):
        return link


class DummyAdversary:
    def __init__(self, atomic_ordering):
        self.atomic_ordering = atomic_ordering


class DummyAgent:
    def __init__(self, paw, group):
        self.paw = paw
        self.group = group


class DummyAbility:
    def __init__(self, ability_id):
        self.ability_id = ability_id


def _make_link(paw, ability_id, command='test command'):
    return _StubLink(command=command, paw=paw, ability=DummyAbility(ability_id))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def dummy_agents():
    return [
        DummyAgent('paw1', 'group1'),
        DummyAgent('paw2', 'group2'),
        DummyAgent('paw3', 'group3'),
        DummyAgent('paw4', 'group1'),
        DummyAgent('paw5', 'group4'),
    ]


@pytest.fixture
def pending_links():
    return [
        _make_link('paw1', '123'),
        _make_link('paw1', '123', command='test command variant'),
        _make_link('paw2', '123'),
        _make_link('paw3', '123'),
    ]


@pytest.fixture
def potential_links_dict():
    return {
        'paw1': [
            _make_link('paw1', '123'),
            _make_link('paw1', '123', command='test command variant'),
            _make_link('paw1', '456'),
            _make_link('paw1', '1011'),
        ],
        'paw2': [
            _make_link('paw2', '123'),
        ],
        'paw3': [
            _make_link('paw3', '1011'),
        ],
        'paw4': [
            _make_link('paw4', '456'),
        ],
    }


@pytest.fixture
def sample_abilities():
    return ['123', '456', '789', '1011']


@pytest.fixture
def sample_filter():
    return {
        '123': ['group1'],
        '789': ['group2'],
        '1011': ['group1', 'group3'],
    }


@pytest.fixture
def generate_planner(potential_links_dict):
    async def _get_links_mock(agent):
        return potential_links_dict.get(agent.paw, [])

    def _generate_planner(atomic_ordering, agents, filtered_groups_by_ability=None):
        operation = DummyOperation(DummyAdversary(atomic_ordering), agents)
        planner = LogicalPlanner(operation, None, filtered_groups_by_ability=filtered_groups_by_ability)
        planner._get_links = _get_links_mock
        return planner
    return _generate_planner


@pytest.fixture
def planner_without_filter(generate_planner, dummy_agents, sample_abilities):
    return generate_planner(sample_abilities, dummy_agents)


@pytest.fixture
def filtered_planner(generate_planner, dummy_agents, sample_abilities, sample_filter):
    return generate_planner(sample_abilities, dummy_agents, filtered_groups_by_ability=sample_filter)


# ---------------------------------------------------------------------------
# Tests — construction
# ---------------------------------------------------------------------------

class TestLogicalPlannerInit:
    def test_default_attributes(self):
        op = DummyOperation(DummyAdversary([]), [])
        planner = LogicalPlanner(op, planning_svc=None)
        assert planner.state_machine == ['fetch_and_run_links']
        assert planner.next_bucket == 'fetch_and_run_links'
        assert planner.filtered_groups_by_ability == {}
        assert planner.pending_links == []
        assert planner.current_ability_index == 0
        assert planner.stopping_conditions == ()
        assert planner.stopping_condition_met is False

    def test_with_stopping_conditions(self):
        op = DummyOperation(DummyAdversary([]), [])
        planner = LogicalPlanner(op, None, stopping_conditions=('cond1',))
        assert planner.stopping_conditions == ('cond1',)

    def test_with_filtered_groups(self):
        filt = {'abc': ['g1']}
        op = DummyOperation(DummyAdversary([]), [])
        planner = LogicalPlanner(op, None, filtered_groups_by_ability=filt)
        assert planner.filtered_groups_by_ability == filt

    def test_none_filtered_groups_defaults_to_empty(self):
        op = DummyOperation(DummyAdversary([]), [])
        planner = LogicalPlanner(op, None, filtered_groups_by_ability=None)
        assert planner.filtered_groups_by_ability == {}


# ---------------------------------------------------------------------------
# Tests — _fetch_from_pending_links
# ---------------------------------------------------------------------------

class TestFetchFromPendingLinks:
    async def test_basic(self, planner_without_filter, pending_links):
        planner_without_filter.pending_links = pending_links
        links_to_use = planner_without_filter._fetch_from_pending_links()
        assert len(links_to_use) == 3
        assert len(planner_without_filter.pending_links) == 1
        paws_used = {l.paw for l in links_to_use}
        assert paws_used == {'paw1', 'paw2', 'paw3'}

    async def test_empty(self, planner_without_filter):
        links_to_use = planner_without_filter._fetch_from_pending_links()
        assert not links_to_use
        assert not planner_without_filter.pending_links

    async def test_single_agent_multiple_links(self, planner_without_filter):
        planner_without_filter.pending_links = [
            _make_link('paw1', '123', command='cmd1'),
            _make_link('paw1', '123', command='cmd2'),
            _make_link('paw1', '456', command='cmd3'),
        ]
        links = planner_without_filter._fetch_from_pending_links()
        assert len(links) == 1
        assert links[0].command == 'cmd1'
        assert len(planner_without_filter.pending_links) == 2

    async def test_all_different_agents(self, planner_without_filter):
        planner_without_filter.pending_links = [
            _make_link('p1', '123'),
            _make_link('p2', '123'),
            _make_link('p3', '456'),
        ]
        links = planner_without_filter._fetch_from_pending_links()
        assert len(links) == 3
        assert len(planner_without_filter.pending_links) == 0


# ---------------------------------------------------------------------------
# Tests — _get_valid_agents_for_ability
# ---------------------------------------------------------------------------

class TestGetValidAgents:
    async def test_no_filter(self, planner_without_filter):
        valid = planner_without_filter._get_valid_agents_for_ability('123')
        assert len(valid) == 5

    async def test_with_filter_single_group(self, filtered_planner):
        valid = filtered_planner._get_valid_agents_for_ability('123')
        paws = [a.paw for a in valid]
        assert set(paws) == {'paw1', 'paw4'}

    async def test_with_filter_multiple_groups(self, filtered_planner):
        valid = filtered_planner._get_valid_agents_for_ability('1011')
        paws = [a.paw for a in valid]
        assert set(paws) == {'paw1', 'paw3', 'paw4'}

    async def test_ability_not_in_filter(self, filtered_planner):
        """Ability 456 is not in filter — all agents should be valid."""
        valid = filtered_planner._get_valid_agents_for_ability('456')
        assert len(valid) == 5

    async def test_filter_with_no_matching_agents(self, generate_planner):
        agents = [DummyAgent('p1', 'groupX')]
        filt = {'abc': ['groupY']}
        planner = generate_planner(['abc'], agents, filtered_groups_by_ability=filt)
        valid = planner._get_valid_agents_for_ability('abc')
        assert len(valid) == 0


# ---------------------------------------------------------------------------
# Tests — _get_pending_links
# ---------------------------------------------------------------------------

class TestGetPendingLinks:
    async def test_without_filter(self, planner_without_filter):
        links = await planner_without_filter._get_pending_links('123')
        assert len(links) == 3
        assert all(l.ability.ability_id == '123' for l in links)

    async def test_with_filter(self, filtered_planner):
        links = await filtered_planner._get_pending_links('123')
        assert len(links) == 2
        assert all(l.ability.ability_id == '123' for l in links)

    async def test_no_matching_ability(self, planner_without_filter):
        links = await planner_without_filter._get_pending_links('nonexistent')
        assert len(links) == 0


# ---------------------------------------------------------------------------
# Tests — _fetch_links full sequence
# ---------------------------------------------------------------------------

class TestFetchLinksSequence:
    async def test_without_filter_full(self, planner_without_filter):
        # First pass: ability 123
        links = await planner_without_filter._fetch_links()
        assert len(links) == 2
        assert planner_without_filter.current_ability_index == 1

        # Second pass: remaining from 123
        links = await planner_without_filter._fetch_links()
        assert len(links) == 1

        # Third pass: ability 456
        links = await planner_without_filter._fetch_links()
        assert len(links) == 2
        assert planner_without_filter.current_ability_index == 2

        # Fourth pass: skip 789 (no links), go to 1011
        links = await planner_without_filter._fetch_links()
        assert len(links) == 2
        assert planner_without_filter.current_ability_index == 4

        # Fifth pass: end
        links = await planner_without_filter._fetch_links()
        assert len(links) == 0

    async def test_with_filter_full(self, filtered_planner):
        # Ability 123 filtered to group1 only
        links = await filtered_planner._fetch_links()
        assert len(links) == 1
        assert filtered_planner.current_ability_index == 1

        # Remaining from 123
        links = await filtered_planner._fetch_links()
        assert len(links) == 1

        # Ability 456 — no filter
        links = await filtered_planner._fetch_links()
        assert len(links) == 2

        # Skip 789, go to 1011
        links = await filtered_planner._fetch_links()
        assert len(links) == 2

        # End
        links = await filtered_planner._fetch_links()
        assert len(links) == 0

    async def test_empty_ordering(self, generate_planner, dummy_agents):
        planner = generate_planner([], dummy_agents)
        links = await planner._fetch_links()
        assert links == []

    async def test_single_ability(self, generate_planner, dummy_agents):
        planner = generate_planner(['123'], dummy_agents)
        links = await planner._fetch_links()
        assert len(links) > 0
        # Drain remaining
        while True:
            more = await planner._fetch_links()
            if not more:
                break


# ---------------------------------------------------------------------------
# Tests — fetch_and_run_links
# ---------------------------------------------------------------------------

class TestFetchAndRunLinks:
    async def test_runs_and_waits(self, planner_without_filter):
        await planner_without_filter.fetch_and_run_links()
        assert planner_without_filter.next_bucket == BUCKET_NAME

    async def test_sets_none_when_empty(self, generate_planner, dummy_agents):
        planner = generate_planner([], dummy_agents)
        await planner.fetch_and_run_links()
        assert planner.next_bucket is None

    async def test_exhausts_all_links(self, planner_without_filter):
        """Run fetch_and_run_links until planner stops."""
        iterations = 0
        while planner_without_filter.next_bucket is not None:
            await planner_without_filter.fetch_and_run_links()
            iterations += 1
            if iterations > 20:
                pytest.fail('Planner did not terminate')
        assert planner_without_filter.next_bucket is None


# ---------------------------------------------------------------------------
# Tests — execute
# ---------------------------------------------------------------------------

class TestExecute:
    async def test_execute_delegates(self):
        from unittest.mock import AsyncMock
        mock_planning_svc = AsyncMock()
        op = DummyOperation(DummyAdversary([]), [])
        planner = LogicalPlanner(op, mock_planning_svc)
        await planner.execute()
        mock_planning_svc.execute_planner.assert_awaited_once_with(planner)
