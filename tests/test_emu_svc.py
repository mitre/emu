"""Exhaustive tests for app/emu_svc.py — EmuService."""
import glob
import json
import os
import shutil
import uuid
import yaml

import asyncio
import pytest

from pathlib import Path, PosixPath
from unittest.mock import patch, call, MagicMock, AsyncMock, mock_open

from app.utility.base_world import BaseWorld
from app.utility.base_service import BaseService


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def async_mock_return(to_return):
    fut = asyncio.Future()
    fut.set_result(to_return)
    return fut


def _make_emu_svc(mock_app_svc=None, mock_contact_svc=None):
    """Create an EmuService with stubbed caldera services."""
    if mock_app_svc is None:
        mock_app_svc = MagicMock()
        mock_app_svc.application = MagicMock()
        mock_app_svc.application.router = MagicMock()
    if mock_contact_svc is None:
        mock_contact_svc = MagicMock()
        mock_contact_svc.handle_heartbeat = AsyncMock()

    BaseService._services['app_svc'] = mock_app_svc
    BaseService._services['contact_svc'] = mock_contact_svc

    # Provide minimal config
    conf_dir = os.path.join('plugins', 'emu', 'conf')
    os.makedirs(conf_dir, exist_ok=True)
    conf_path = os.path.join(conf_dir, 'default.yml')
    if not os.path.exists(conf_path):
        with open(conf_path, 'w') as f:
            yaml.dump({'evals_c2_host': '127.0.0.1', 'evals_c2_port': 8888}, f)

    from plugins.emu.app.emu_svc import EmuService
    svc = EmuService()
    return svc


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def emu_svc():
    return _make_emu_svc()


@pytest.fixture
def planner_yaml():
    return [yaml.safe_load('''
---
id: testid
name: Test Planner
description: |
  Test planner
module: plugins.emu.app.test_planner_module
params:
  param_name:
    key1:
      - value1
    key2:
      - value2
ignore_enforcement_modules: []
allow_repeatable_abilities: False
''')]


@pytest.fixture
def not_planner_yaml():
    return [yaml.safe_load('''
---
name: I am a yaml file
value: But I am not a planner
description: something
''')]


@pytest.fixture
def sample_emu_plan():
    return yaml.safe_load('''
- emulation_plan_details:
    id: planid123
    adversary_name: Adversary APTXY
    adversary_description: Adversary description
    attack_version: 8
    format_version: 1.0

# two payloads, 1 input arg
- id: 1-2-3
  name: Ability 1
  description: Desc 1
  tactic: tactic1
  technique:
    attack_id: technique1
    name: technique 1
  cti_source: source1
  procedure_group: procedure1
  procedure_step: step1
  platforms:
    linux:
      sh:
        command: test command
        payloads:
          - payload1A
          - payload1B

  input_arguments:
    arg1:
      description: argdesc1
      type: string
      default: default1

# 1 payload, 2 input arguments, 2 executors
- id: 2-3-4
  name: Ability 2
  description: Desc 2
  tactic: tactic2
  technique:
    attack_id: technique2
    name: technique 2
  cti_source: source2
  procedure_group: procedure2
  procedure_step: step2
  platforms:
    linux:
      sh:
        command: test command
        payloads:
          - payload2A
    windows:
      cmd:
        command: test command

  input_arguments:
    arg1:
      description: argdesc1
      type: string
      default: default1
    arg2:
      description: argdesc2
      type: string
      default: default2

# 0 payloads, 0 input arguments, 2 uploads, cleanup
- id: 3-4-5
  name: Ability 3
  description: Desc 3
  tactic: tactic3
  technique:
    attack_id: technique3
    name: technique 3
  cti_source: source3
  procedure_group: procedure3
  procedure_step: step3
  platforms:
    linux:
      sh:
        command: test command
        uploads:
          - upload1A
          - upload1B
        cleanup: cleanup command
''')


@pytest.fixture
def sample_emu_plan_bad_version():
    return yaml.safe_load('''
- emulation_plan_details:
    id: planid999
    adversary_name: Bad Adversary
    adversary_description: Bad desc
    attack_version: 8
    format_version: 0.5
''')


@pytest.fixture
def sample_emu_plan_no_adversary():
    return yaml.safe_load('''
- emulation_plan_details:
    id: planid888
    attack_version: 8
    format_version: 1.0
''')


@pytest.fixture
def ability_with_elevation():
    return {
        'id': 'elev-1',
        'name': 'Elevated Ability',
        'description': 'Needs elevation',
        'tactic': 'Privilege Escalation',
        'technique': {'attack_id': 'T1234', 'name': 'Elevate'},
        'platforms': {'windows': {'psh': {'command': 'whoami /priv'}}},
        'executors': [{'elevation_required': True, 'name': 'psh'}],
    }


@pytest.fixture
def ability_without_elevation():
    return {
        'id': 'noelev-1',
        'name': 'Normal Ability',
        'description': 'No elevation',
        'tactic': 'Discovery',
        'technique': {'attack_id': 'T5678', 'name': 'Discover'},
        'platforms': {'linux': {'sh': {'command': 'id'}}},
        'executors': [{'name': 'sh'}],
    }


# ---------------------------------------------------------------------------
# TestEmuSvc — original tests preserved + many new ones
# ---------------------------------------------------------------------------

class TestEmuSvc:
    LIBRARY_GLOB_PATH = 'plugins/emu/data/adversary-emulation-plans/*'
    PLANNER_GLOB_PATH = 'plugins/emu/data/adversary-emulation-plans/*/Emulation_Plan/yaml/planners/*.yml'
    PLANNER_PATH = 'plugins/emu/data/adversary-emulation-plans/library1/Emulation_Plan/yaml/planners/test_planner.yml'
    DEST_PLANNER_PATH = 'plugins/emu/data/planners/testid.yml'

    # -- creation --

    def test_general_svc_creation(self, emu_svc):
        assert emu_svc.emu_dir == 'plugins/emu'
        assert emu_svc.repo_dir == 'plugins/emu/data/adversary-emulation-plans'
        assert emu_svc.data_dir == 'plugins/emu/data'
        assert emu_svc.payloads_dir == 'plugins/emu/payloads'

    def test_required_payloads_initially_empty(self, emu_svc):
        assert emu_svc.required_payloads == set()

    def test_dynamically_compiled_payloads_class_attr(self):
        from plugins.emu.app.emu_svc import EmuService
        assert 'sandcat.go-linux' in EmuService._dynamicically_compiled_payloads
        assert 'sandcat.go-darwin' in EmuService._dynamicically_compiled_payloads
        assert 'sandcat.go-windows' in EmuService._dynamicically_compiled_payloads
        assert len(EmuService._dynamicically_compiled_payloads) == 3

    # -- planner ingestion --

    async def test_ingest_planner(self, emu_svc, planner_yaml):
        with patch.object(BaseWorld, 'strip_yml', return_value=planner_yaml):
            with patch.object(shutil, 'copyfile', return_value=None) as new_copyfile:
                num_planners, num_ingested, num_errors = await emu_svc._ingest_planner(TestEmuSvc.PLANNER_PATH)
        new_copyfile.assert_called_once_with(TestEmuSvc.PLANNER_PATH, TestEmuSvc.DEST_PLANNER_PATH)
        assert num_planners == 1
        assert num_ingested == 1
        assert num_errors == 0

    async def test_ingest_bad_planner(self, emu_svc, not_planner_yaml):
        with patch.object(BaseWorld, 'strip_yml', return_value=not_planner_yaml):
            with patch.object(shutil, 'copyfile', return_value=None) as new_copyfile:
                num_planners, num_ingested, num_errors = await emu_svc._ingest_planner(TestEmuSvc.PLANNER_PATH)
        new_copyfile.assert_not_called()
        assert num_planners == 0
        assert num_ingested == 0
        assert num_errors == 1

    async def test_ingest_planner_yaml_parse_error(self, emu_svc):
        with patch.object(BaseWorld, 'strip_yml', side_effect=Exception('parse error')):
            num_planners, num_ingested, num_errors = await emu_svc._ingest_planner(TestEmuSvc.PLANNER_PATH)
        assert num_planners == 0
        assert num_ingested == 0
        assert num_errors == 1

    async def test_ingest_planner_copy_io_error(self, emu_svc, planner_yaml):
        with patch.object(BaseWorld, 'strip_yml', return_value=planner_yaml):
            with patch.object(shutil, 'copyfile', side_effect=IOError('disk full')):
                num_planners, num_ingested, num_errors = await emu_svc._ingest_planner(TestEmuSvc.PLANNER_PATH)
        assert num_planners == 1
        assert num_ingested == 0
        assert num_errors == 1

    async def test_load_planners(self, emu_svc, planner_yaml):
        with patch.object(BaseWorld, 'strip_yml', return_value=planner_yaml):
            with patch.object(shutil, 'copyfile', return_value=None) as new_copyfile:
                with patch.object(glob, 'iglob', return_value=[TestEmuSvc.PLANNER_PATH]):
                    await emu_svc._load_planners(TestEmuSvc.LIBRARY_GLOB_PATH)
        new_copyfile.assert_called_once_with(TestEmuSvc.PLANNER_PATH, TestEmuSvc.DEST_PLANNER_PATH)

    async def test_load_bad_planners(self, emu_svc, not_planner_yaml):
        with patch.object(BaseWorld, 'strip_yml', return_value=not_planner_yaml):
            with patch.object(shutil, 'copyfile', return_value=None) as new_copyfile:
                with patch.object(glob, 'iglob', return_value=[TestEmuSvc.PLANNER_PATH]):
                    await emu_svc._load_planners(TestEmuSvc.LIBRARY_GLOB_PATH)
        new_copyfile.assert_not_called()

    async def test_load_planners_empty_glob(self, emu_svc):
        with patch.object(glob, 'iglob', return_value=[]):
            await emu_svc._load_planners(TestEmuSvc.LIBRARY_GLOB_PATH)
        # Should succeed with no errors

    # -- _is_planner --

    def test_is_planner_true(self):
        from plugins.emu.app.emu_svc import EmuService
        assert EmuService._is_planner({'id': '1', 'module': 'mod', 'name': 'test'}) is True

    def test_is_planner_false_missing_id(self):
        from plugins.emu.app.emu_svc import EmuService
        assert EmuService._is_planner({'module': 'mod', 'name': 'test'}) is False

    def test_is_planner_false_missing_module(self):
        from plugins.emu.app.emu_svc import EmuService
        assert EmuService._is_planner({'id': '1', 'name': 'test'}) is False

    def test_is_planner_false_empty(self):
        from plugins.emu.app.emu_svc import EmuService
        assert EmuService._is_planner({}) is False

    # -- _is_valid_format_version --

    def test_is_valid_format_version_1_0(self):
        from plugins.emu.app.emu_svc import EmuService
        assert EmuService._is_valid_format_version({'format_version': 1.0}) is True

    def test_is_valid_format_version_2_0(self):
        from plugins.emu.app.emu_svc import EmuService
        assert EmuService._is_valid_format_version({'format_version': 2.0}) is True

    def test_is_valid_format_version_below_1(self):
        from plugins.emu.app.emu_svc import EmuService
        assert EmuService._is_valid_format_version({'format_version': 0.5}) is False

    def test_is_valid_format_version_missing(self):
        from plugins.emu.app.emu_svc import EmuService
        assert EmuService._is_valid_format_version({}) is False

    def test_is_valid_format_version_non_numeric(self):
        from plugins.emu.app.emu_svc import EmuService
        assert EmuService._is_valid_format_version({'format_version': 'abc'}) is False

    # -- _is_ability --

    async def test_is_ability_true(self):
        from plugins.emu.app.emu_svc import EmuService
        result = await EmuService._is_ability({'id': '1', 'platforms': {}, 'name': 'test'})
        assert result is True

    async def test_is_ability_false_missing_id(self):
        from plugins.emu.app.emu_svc import EmuService
        result = await EmuService._is_ability({'platforms': {}, 'name': 'test'})
        assert result is False

    async def test_is_ability_false_missing_platforms(self):
        from plugins.emu.app.emu_svc import EmuService
        result = await EmuService._is_ability({'id': '1', 'name': 'test'})
        assert result is False

    async def test_is_ability_false_empty(self):
        from plugins.emu.app.emu_svc import EmuService
        result = await EmuService._is_ability({})
        assert result is False

    # -- get_adversary_from_filename --

    def test_get_adversary_from_filename_normal(self):
        from plugins.emu.app.emu_svc import EmuService
        assert EmuService.get_adversary_from_filename('/path/to/apt29.yaml') == 'apt29'

    def test_get_adversary_from_filename_nested(self):
        from plugins.emu.app.emu_svc import EmuService
        assert EmuService.get_adversary_from_filename('/a/b/c/fin7.yml') == 'fin7'

    def test_get_adversary_from_filename_no_extension(self):
        from plugins.emu.app.emu_svc import EmuService
        assert EmuService.get_adversary_from_filename('/path/adversary') == 'adversary'

    def test_get_adversary_from_filename_just_filename(self):
        from plugins.emu.app.emu_svc import EmuService
        assert EmuService.get_adversary_from_filename('test.yaml') == 'test'

    # -- get_privilege --

    def test_get_privilege_elevated(self):
        from plugins.emu.app.emu_svc import EmuService
        result = EmuService.get_privilege([{'elevation_required': True, 'name': 'psh'}])
        assert result == 'Elevated'

    def test_get_privilege_not_elevated(self):
        from plugins.emu.app.emu_svc import EmuService
        result = EmuService.get_privilege([{'name': 'sh'}])
        assert result is False

    def test_get_privilege_empty_list(self):
        from plugins.emu.app.emu_svc import EmuService
        result = EmuService.get_privilege([])
        assert not result

    def test_get_privilege_none(self):
        from plugins.emu.app.emu_svc import EmuService
        result = EmuService.get_privilege(None)
        assert result is False

    # -- abilities ingestion --

    async def test_ingest_abilities(self, emu_svc, sample_emu_plan):
        from plugins.emu.app.emu_svc import EmuService
        with patch.object(EmuService, '_write_ability', return_value=async_mock_return(None)) as write_ability:
            abilities, facts, at_total, at_ingested, errors = await emu_svc._ingest_abilities(sample_emu_plan)
        assert write_ability.call_count == 3
        assert abilities == ['1-2-3', '2-3-4', '3-4-5']
        assert facts == [
            dict(trait='arg1', value='default1'),
            dict(trait='arg1', value='default1'),
            dict(trait='arg2', value='default2'),
        ]
        assert at_total == 3
        assert at_ingested == 3
        assert errors == 0
        assert {'payload1A', 'payload1B', 'payload2A'} == emu_svc.required_payloads

    async def test_ingest_abilities_empty_plan(self, emu_svc):
        from plugins.emu.app.emu_svc import EmuService
        with patch.object(EmuService, '_write_ability', return_value=async_mock_return(None)) as write_ability:
            abilities, facts, at_total, at_ingested, errors = await emu_svc._ingest_abilities([])
        assert abilities == []
        assert facts == []
        assert at_total == 0
        assert at_ingested == 0
        assert errors == 0
        write_ability.assert_not_called()

    async def test_ingest_abilities_write_error(self, emu_svc, sample_emu_plan):
        from plugins.emu.app.emu_svc import EmuService
        with patch.object(EmuService, '_write_ability', side_effect=Exception('write error')):
            abilities, facts, at_total, at_ingested, errors = await emu_svc._ingest_abilities(sample_emu_plan)
        assert at_total == 3
        assert at_ingested == 0
        assert errors == 3

    # -- emulation plan ingestion --

    async def test_ingest_emulation_plan(self, emu_svc, sample_emu_plan):
        from plugins.emu.app.emu_svc import EmuService
        with patch.object(BaseWorld, 'strip_yml', return_value=[sample_emu_plan]):
            with patch.object(EmuService, '_write_ability', return_value=async_mock_return(None)):
                with patch.object(EmuService, '_write_adversary', return_value=async_mock_return(None)) as w_adv:
                    with patch.object(EmuService, '_write_source', return_value=async_mock_return(None)) as w_src:
                        at_total, at_ingested, errors = await emu_svc._ingest_emulation_plan('test.yaml')
        assert at_total == 3
        assert at_ingested == 3
        assert errors == 0
        w_adv.assert_called_once()
        w_src.assert_called_once()

    async def test_ingest_emulation_plan_bad_version(self, emu_svc, sample_emu_plan_bad_version):
        with patch.object(BaseWorld, 'strip_yml', return_value=[sample_emu_plan_bad_version]):
            at_total, at_ingested, errors = await emu_svc._ingest_emulation_plan('test.yaml')
        assert at_total == 0
        assert at_ingested == 0
        assert errors == 1

    async def test_ingest_emulation_plan_no_adversary(self, emu_svc, sample_emu_plan_no_adversary):
        with patch.object(BaseWorld, 'strip_yml', return_value=[sample_emu_plan_no_adversary]):
            at_total, at_ingested, errors = await emu_svc._ingest_emulation_plan('test.yaml')
        assert at_total == 0
        assert at_ingested == 0
        assert errors == 1

    # -- _save_ability with elevation --

    async def test_save_ability_with_elevation(self, emu_svc, ability_with_elevation):
        from plugins.emu.app.emu_svc import EmuService
        with patch.object(EmuService, '_write_ability', return_value=async_mock_return(None)):
            ability_id, facts = await emu_svc._save_ability(ability_with_elevation)
        assert ability_id == 'elev-1'

    async def test_save_ability_without_elevation(self, emu_svc, ability_without_elevation):
        from plugins.emu.app.emu_svc import EmuService
        with patch.object(EmuService, '_write_ability', return_value=async_mock_return(None)):
            ability_id, facts = await emu_svc._save_ability(ability_without_elevation)
        assert ability_id == 'noelev-1'

    # -- _unique_facts --

    async def test_unique_facts_no_duplicates(self):
        from plugins.emu.app.emu_svc import EmuService
        facts = [{'trait': 'a', 'value': '1'}, {'trait': 'b', 'value': '2'}]
        result = await EmuService._unique_facts(facts)
        assert result == facts

    async def test_unique_facts_with_duplicates(self):
        from plugins.emu.app.emu_svc import EmuService
        facts = [
            {'trait': 'a', 'value': '1'},
            {'trait': 'b', 'value': '2'},
            {'trait': 'a', 'value': '1'},
        ]
        result = await EmuService._unique_facts(facts)
        assert len(result) == 2
        assert result == [{'trait': 'a', 'value': '1'}, {'trait': 'b', 'value': '2'}]

    async def test_unique_facts_empty(self):
        from plugins.emu.app.emu_svc import EmuService
        result = await EmuService._unique_facts([])
        assert result == []

    # -- _register_required_payloads --

    def test_register_required_payloads(self, emu_svc):
        payloads = ['payload1', 'payload2', 'payload3', 'sandcat.go-darwin', 'sandcat.go-linux', 'sandcat.go-windows']
        want = {'payload1', 'payload2', 'payload3'}
        emu_svc._register_required_payloads(payloads)
        assert emu_svc.required_payloads == want

    def test_register_required_payloads_empty(self, emu_svc):
        emu_svc._register_required_payloads([])
        assert emu_svc.required_payloads == set()

    def test_register_required_payloads_only_dynamic(self, emu_svc):
        emu_svc._register_required_payloads(['sandcat.go-linux', 'sandcat.go-darwin'])
        assert emu_svc.required_payloads == set()

    def test_register_required_payloads_accumulates(self, emu_svc):
        emu_svc._register_required_payloads(['a', 'b'])
        emu_svc._register_required_payloads(['b', 'c'])
        assert emu_svc.required_payloads == {'a', 'b', 'c'}

    # -- _store_required_payloads --

    def test_store_required_payloads(self, emu_svc):
        def _rglob(_, target):
            return [PosixPath('/path/to/' + target), PosixPath('/path2/to/' + target)]

        emu_svc.required_payloads = {'payload1', 'payload2', 'payload3'}
        with patch.object(Path, 'rglob', new=_rglob):
            with patch.object(shutil, 'copyfile', return_value=None) as new_copyfile:
                emu_svc._store_required_payloads()
        assert new_copyfile.call_count == 3
        new_copyfile.assert_has_calls([
            call(PosixPath('/path/to/payload1'), 'plugins/emu/payloads/payload1'),
            call(PosixPath('/path/to/payload2'), 'plugins/emu/payloads/payload2'),
            call(PosixPath('/path/to/payload3'), 'plugins/emu/payloads/payload3'),
        ], any_order=True)

    def test_store_required_payloads_empty(self, emu_svc):
        emu_svc.required_payloads = set()
        emu_svc._store_required_payloads()
        # No error, nothing to copy

    def test_store_required_payloads_not_found(self, emu_svc):
        emu_svc.required_payloads = {'missing_payload'}
        with patch.object(Path, 'rglob', return_value=[]):
            emu_svc._store_required_payloads()
        # Should log a warning but not raise

    def test_store_required_payloads_copy_failure(self, emu_svc):
        def _rglob(_, target):
            return [PosixPath('/path/to/' + target)]

        emu_svc.required_payloads = {'bad_payload'}
        with patch.object(Path, 'rglob', new=_rglob):
            with patch.object(shutil, 'copyfile', side_effect=Exception('copy failed')):
                emu_svc._store_required_payloads()
        # Should log but not raise

    def test_store_required_payloads_already_exists(self, emu_svc):
        emu_svc.required_payloads = {'existing_payload'}
        with patch.object(os.path, 'exists', return_value=True):
            emu_svc._store_required_payloads()
        # Payload already in payloads dir — skip

    # -- _copy_planner --

    def test_copy_planner_new(self, emu_svc, tmp_path):
        src = tmp_path / 'source.yml'
        src.write_text('test')
        target = 'target.yml'
        with patch.object(os.path, 'exists', side_effect=lambda p: p == str(src)):
            with patch.object(os, 'makedirs'):
                with patch.object(shutil, 'copyfile') as cp:
                    emu_svc._copy_planner(str(src), target)
        cp.assert_called_once()

    def test_copy_planner_already_exists(self, emu_svc, tmp_path):
        with patch.object(os.path, 'exists', return_value=True):
            with patch.object(shutil, 'copyfile') as cp:
                emu_svc._copy_planner('src.yml', 'target.yml')
        cp.assert_not_called()

    # -- clone_repo --

    async def test_clone_repo_default_url(self, emu_svc):
        with patch.object(os.path, 'exists', return_value=False):
            with patch('plugins.emu.app.emu_svc.check_call') as mock_check:
                await emu_svc.clone_repo()
        mock_check.assert_called_once()
        args = mock_check.call_args[0][0]
        assert 'git' in args[0]
        assert 'clone' in args
        assert 'adversary_emulation_library' in args[4]

    async def test_clone_repo_custom_url(self, emu_svc):
        with patch.object(os.path, 'exists', return_value=False):
            with patch('plugins.emu.app.emu_svc.check_call') as mock_check:
                await emu_svc.clone_repo(repo_url='https://example.com/fork.git')
        args = mock_check.call_args[0][0]
        assert args[4] == 'https://example.com/fork.git'

    async def test_clone_repo_already_exists(self, emu_svc):
        with patch.object(os.path, 'exists', return_value=True):
            with patch.object(os, 'listdir', return_value=['file1']):
                with patch('plugins.emu.app.emu_svc.check_call') as mock_check:
                    await emu_svc.clone_repo()
        mock_check.assert_not_called()

    # -- populate_data_directory --

    async def test_populate_data_directory_default(self, emu_svc):
        from plugins.emu.app.emu_svc import EmuService
        with patch.object(EmuService, '_load_adversaries_and_abilities', return_value=async_mock_return(None)) as load_adv:
            with patch.object(EmuService, '_load_planners', return_value=async_mock_return(None)) as load_plan:
                await emu_svc.populate_data_directory()
        expected = os.path.join(emu_svc.repo_dir, '*')
        load_adv.assert_called_once_with(expected)
        load_plan.assert_called_once_with(expected)

    async def test_populate_data_directory_custom_path(self, emu_svc):
        from plugins.emu.app.emu_svc import EmuService
        with patch.object(EmuService, '_load_adversaries_and_abilities', return_value=async_mock_return(None)) as load_adv:
            with patch.object(EmuService, '_load_planners', return_value=async_mock_return(None)) as load_plan:
                await emu_svc.populate_data_directory(library_path='/custom/path')
        load_adv.assert_called_once_with('/custom/path')
        load_plan.assert_called_once_with('/custom/path')

    # -- handle_forwarded_beacon --

    async def test_handle_forwarded_beacon_full_profile(self, emu_svc, mock_contact_svc):
        from plugins.emu.app.emu_svc import EmuService
        emu_svc.contact_svc = mock_contact_svc
        profile_data = {
            'guid': 'test-paw-123',
            'platform': 'windows',
            'hostName': 'WORKSTATION1',
            'user': 'admin',
            'pid': 1234,
            'ppid': 5678,
        }
        request = MagicMock()
        request.read = AsyncMock(return_value=json.dumps(profile_data).encode())

        response = await emu_svc.handle_forwarded_beacon(request)
        assert 'test-paw-123' in response.text
        mock_contact_svc.handle_heartbeat.assert_called_once()
        call_kwargs = mock_contact_svc.handle_heartbeat.call_args[1]
        assert call_kwargs['paw'] == 'test-paw-123'
        assert call_kwargs['platform'] == 'windows'
        assert call_kwargs['host'] == 'WORKSTATION1'
        assert call_kwargs['username'] == 'admin'
        assert call_kwargs['pid'] == 1234
        assert call_kwargs['ppid'] == 5678

    async def test_handle_forwarded_beacon_minimal_profile(self, emu_svc, mock_contact_svc):
        emu_svc.contact_svc = mock_contact_svc
        profile_data = {'guid': 'min-paw'}
        request = MagicMock()
        request.read = AsyncMock(return_value=json.dumps(profile_data).encode())

        response = await emu_svc.handle_forwarded_beacon(request)
        assert 'min-paw' in response.text
        call_kwargs = mock_contact_svc.handle_heartbeat.call_args[1]
        assert call_kwargs['platform'] == 'evals'

    async def test_handle_forwarded_beacon_error(self, emu_svc):
        request = MagicMock()
        request.read = AsyncMock(side_effect=Exception('bad request'))
        with pytest.raises((TypeError, Exception)):
            await emu_svc.handle_forwarded_beacon(request)

    # -- _write_ability / _write_adversary / _write_source with tmp dirs --

    async def test_write_ability(self, emu_svc, tmp_data_dir):
        emu_svc.data_dir = str(tmp_data_dir / 'data')
        ability_data = {
            'id': 'test-ab-1',
            'tactic': 'discovery',
            'name': 'test',
            'platforms': {},
        }
        await emu_svc._write_ability(ability_data)
        path = os.path.join(emu_svc.data_dir, 'abilities', 'discovery', 'test-ab-1.yml')
        assert os.path.exists(path)

    async def test_write_ability_skip_existing(self, emu_svc, tmp_data_dir):
        emu_svc.data_dir = str(tmp_data_dir / 'data')
        ability_data = {'id': 'test-ab-2', 'tactic': 'discovery', 'name': 'test', 'platforms': {}}
        await emu_svc._write_ability(ability_data)
        # Write again — should skip
        await emu_svc._write_ability(ability_data)
        # No error

    async def test_write_adversary(self, emu_svc, tmp_data_dir):
        emu_svc.data_dir = str(tmp_data_dir / 'data')
        adv_data = {'id': 'test-adv-1', 'name': 'Test Adv', 'description': 'desc', 'atomic_ordering': []}
        await emu_svc._write_adversary(adv_data)
        path = os.path.join(emu_svc.data_dir, 'adversaries', 'test-adv-1.yml')
        assert os.path.exists(path)

    async def test_write_adversary_skip_existing(self, emu_svc, tmp_data_dir):
        emu_svc.data_dir = str(tmp_data_dir / 'data')
        adv_data = {'id': 'test-adv-dup', 'name': 'Dup', 'description': 'desc', 'atomic_ordering': []}
        await emu_svc._write_adversary(adv_data)
        await emu_svc._write_adversary(adv_data)
        # No error on duplicate

    async def test_write_source(self, emu_svc, tmp_data_dir):
        emu_svc.data_dir = str(tmp_data_dir / 'data')
        source_data = {'id': 'test-src-1', 'name': 'Test Source', 'facts': []}
        await emu_svc._write_source(source_data)
        path = os.path.join(emu_svc.data_dir, 'sources', 'test-src-1.yml')
        assert os.path.exists(path)

    # -- _save_adversary --

    async def test_save_adversary(self, emu_svc, tmp_data_dir):
        from plugins.emu.app.emu_svc import EmuService
        emu_svc.data_dir = str(tmp_data_dir / 'data')
        await emu_svc._save_adversary(id='adv-1', name='APT1', description='Test', abilities=['a', 'b'])
        path = os.path.join(emu_svc.data_dir, 'adversaries', 'adv-1.yml')
        assert os.path.exists(path)
        with open(path) as f:
            data = yaml.safe_load(f)
        assert data['name'] == 'APT1'
        assert data['description'] == 'Test (Emu)'
        assert data['atomic_ordering'] == ['a', 'b']

    # -- _save_source --

    async def test_save_source(self, emu_svc, tmp_data_dir):
        emu_svc.data_dir = str(tmp_data_dir / 'data')
        facts = [{'trait': 'a', 'value': '1'}, {'trait': 'b', 'value': '2'}]
        await emu_svc._save_source('TestAdv', facts)
        src_dir = os.path.join(emu_svc.data_dir, 'sources')
        files = os.listdir(src_dir)
        assert len(files) == 1
        with open(os.path.join(src_dir, files[0])) as f:
            data = yaml.safe_load(f)
        assert data['name'] == 'TestAdv (Emu)'
        assert len(data['facts']) == 2

    # -- _load_object --

    async def test_load_object_multiple_files(self, emu_svc):
        call_count = 0

        async def mock_ingest(filename):
            nonlocal call_count
            call_count += 1
            return 1, 1, 0

        with patch.object(glob, 'iglob', return_value=['f1.yaml', 'f2.yaml', 'f3.yaml']):
            await emu_svc._load_object('*.yaml', 'test_objects', mock_ingest)
        assert call_count == 3

    async def test_load_object_with_errors(self, emu_svc):
        async def mock_ingest(filename):
            return 1, 0, 1

        with patch.object(glob, 'iglob', return_value=['f1.yaml']):
            await emu_svc._load_object('*.yaml', 'test_objects', mock_ingest)
        # Should not raise; errors are counted

    # -- decrypt_payloads --

    async def test_decrypt_payloads_no_scripts(self, emu_svc):
        with patch.object(glob, 'iglob', return_value=[]):
            await emu_svc.decrypt_payloads()
        # No scripts found — nothing to do
