import os

from app.utility.base_world import BaseWorld
from plugins.emu.app.emu_svc import EmuService

name = 'Emu'
description = 'The collection of abilities from the CTID Adversary Emulation Plans'
address = None
access = BaseWorld.Access.RED
data_dir = os.path.join('plugins', name.lower(), 'data')


async def enable(services):
    if "abilities" not in os.listdir(data_dir):
        plugin_svc = EmuService()
        await plugin_svc.clone_repo()
        await plugin_svc.populate_data_directory()
        await plugin_svc.populate_sources_directory()
