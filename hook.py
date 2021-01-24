import os
import shutil

from app.utility.base_world import BaseWorld
from plugins.emu.app.emu_svc import EmuService

name = 'Emu'
description = 'The collection of abilities from the CTID Adversary Emulation Plans'
address = None
access = BaseWorld.Access.RED
data_dir = os.path.join('plugins', name.lower(), 'data')


async def enable(services):
    plugin_svc = EmuService()

    if not os.path.isdir(plugin_svc.repo_dir):
        await plugin_svc.clone_repo()

    for directory in ["abilities", "adversaries", "sources"]:
        full_path = os.path.join(data_dir, directory)
        if os.path.isdir(full_path):
            shutil.rmtree(full_path)

    await plugin_svc.populate_data_directory()
