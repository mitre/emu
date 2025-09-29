import os

from app.utility.base_world import BaseWorld
from plugins.emu.app.emu_svc import EmuService
from plugins.emu.app.emu_gui import EmuGUI

name = 'Emu'
description = 'The collection of abilities from the CTID Adversary Emulation Plans'
address = '/plugin/emu/gui'
access = BaseWorld.Access.RED
data_dir = os.path.join('plugins', name.lower(), 'data')


async def enable(services):
    BaseWorld.apply_config('emu', BaseWorld.strip_yml('plugins/emu/conf/default.yml')[0])
    plugin_svc = EmuService()
    emu_gui = EmuGUI(services, name, description)
    app = services.get('app_svc').application
    app.router.add_route('GET', '/plugin/emu/gui', emu_gui.splash)

    if not os.path.isdir(plugin_svc.repo_dir):
        await plugin_svc.clone_repo()

    await plugin_svc.decrypt_payloads()
    await plugin_svc.populate_data_directory()
