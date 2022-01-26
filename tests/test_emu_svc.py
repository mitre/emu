import glob
import yaml
import shutil

import pytest

from unittest.mock import patch

from app.utility.base_world import BaseWorld
from plugins.emu.app.emu_svc import EmuService


@pytest.fixture
def emu_svc():
    return EmuService()


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


class TestEmuSvc:
    LIBRARY_GLOB_PATH = 'plugins/emu/data/adversary-emulation-plans/*'
    PLANNER_GLOB_PATH = 'plugins/emu/data/adversary-emulation-plans/*/Emulation_Plan/yaml/planners/*.yml'
    PLANNER_PATH = 'plugins/emu/data/adversary-emulation-plans/library1/Emulation_Plan/yaml/planners/test_planner.yml'
    DEST_PLANNER_PATH = 'plugins/emu/data/planners/testid.yml'

    def test_general_svc_creation(self, emu_svc):
        assert emu_svc.emu_dir == 'plugins/emu'
        assert emu_svc.repo_dir == 'plugins/emu/data/adversary-emulation-plans'
        assert emu_svc.data_dir == 'plugins/emu/data'
        assert emu_svc.payloads_dir == 'plugins/emu/payloads'

    async def test_ingest_planner(self, emu_svc, planner_yaml):

        with patch.object(BaseWorld, 'strip_yml', return_value=planner_yaml) as new_strip_yml:
            await emu_svc._ingest_planner(TestEmuSvc.PLANNER_PATH)
        new_strip_yml.assert_called_once_with(TestEmuSvc.PLANNER_PATH)

    async def test_ingest_bad_planner(self, emu_svc, not_planner_yaml):
        with patch.object(BaseWorld, 'strip_yml', return_value=not_planner_yaml) as new_strip_yml:
            with patch.object(shutil, 'copyfile', return_value=None) as new_copyfile:
                await emu_svc._ingest_planner(TestEmuSvc.PLANNER_PATH)
        new_strip_yml.assert_called_once_with(TestEmuSvc.PLANNER_PATH)
        new_copyfile.assert_not_called()

    async def test_load_planners(self, emu_svc, planner_yaml):
        with patch.object(BaseWorld, 'strip_yml', return_value=planner_yaml) as new_strip_yml:
            with patch.object(glob, 'iglob', return_value=[TestEmuSvc.PLANNER_PATH]) as new_iglob:
                await emu_svc._load_planners(TestEmuSvc.LIBRARY_GLOB_PATH)
        new_iglob.assert_called_once_with(TestEmuSvc.PLANNER_GLOB_PATH)
        new_strip_yml.assert_called_once_with(TestEmuSvc.PLANNER_PATH)

    async def test_load_bad_planners(self, emu_svc, not_planner_yaml):
        with patch.object(BaseWorld, 'strip_yml', return_value=not_planner_yaml) as new_strip_yml:
            with patch.object(glob, 'iglob', return_value=[TestEmuSvc.PLANNER_PATH]) as new_iglob:
                await emu_svc._load_planners(TestEmuSvc.LIBRARY_GLOB_PATH)
        new_iglob.assert_called_once_with(TestEmuSvc.PLANNER_GLOB_PATH)
        new_strip_yml.assert_called_once_with(TestEmuSvc.PLANNER_PATH)
