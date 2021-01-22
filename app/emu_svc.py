import glob
import os
import uuid
import yaml
from subprocess import DEVNULL, STDOUT, check_call

from app.utility.base_service import BaseService


class EmuService(BaseService):
    def __init__(self):
        self.log = self.add_service('emu_svc', self)
        self.emu_dir = os.path.join('plugins', 'emu')
        self.repo_dir = os.path.join(self.emu_dir, 'adversary-emulation-plans')
        self.data_dir = os.path.join(self.emu_dir, 'data')
        self.payloads_dir = os.path.join(self.emu_dir, 'payloads')
        self.sources_dir = os.path.join(self.data_dir, 'sources')

    async def clone_repo(self, repo_url=None):
        """
        Clone the Adversary Emulation Library repository. You can use a specific url via
        the `repo_url` parameter (eg. if you want to use a fork).
        """
        if not repo_url:
            repo_url = 'https://github.com/center-for-threat-informed-defense/adversary_emulation_library'

        if not os.path.exists(self.repo_dir) or not os.listdir(self.repo_dir):
            self.log.debug('cloning repo %s' % repo_url)
            check_call(['git', 'clone', '--depth', '1', repo_url, self.repo_dir], stdout=DEVNULL, stderr=STDOUT)
            self.log.debug('clone complete')

    async def populate_data_directory(self, path_yaml=None):
        """
        Populate the 'data' directory with the Adversary Emulation Library abilities.
        """

        if not path_yaml:
            path_yaml = os.path.join(self.repo_dir, '**', '**', '*.yaml')

        at_total = 0
        at_ingested = 0
        errors = 0
        for filename in glob.iglob(path_yaml):
            emulation_plan = self.strip_yml(filename)[0]

            abilities = []
            details = dict()
            for entry in emulation_plan:
                if 'emulation_plan_details' in entry:
                    details = entry['emulation_plan_details']
                if await self._is_ability(entry):
                    at_total += 1
                    try:
                        ability_id = await self._save_ability(entry)
                        abilities.append(ability_id)
                        at_ingested += 1
                    except:
                        errors += 1

            await self._save_adversary(name=details.get('adversary_name', filename),
                                       description=details.get('adversary_description', filename),
                                       abilities=abilities)

        errors_output = f' and ran into {errors} errors' if errors else ''
        self.log.debug(f'Ingested {at_ingested} abilities (out of {at_total}) from emu plugin{errors_output}')

    """ PRIVATE """

    @staticmethod
    def get_adversary_from_filename(filename):
        base = os.path.basename(filename)
        return os.path.splitext(base)[0]

    async def _write_adversary(self, data):
        d = os.path.join(self.data_dir, 'adversaries')

        if not os.path.exists(d):
            os.makedirs(d)

        file_path = os.path.join(d, '%s.yml' % data['id'])
        with open(file_path, 'w') as f:
            f.write(yaml.dump(data))

    async def _save_adversary(self, name, description, abilities):
        adversary = dict(
            id=str(uuid.uuid4()),
            name=name,
            description='%s (Emu)' % description,
            atomic_ordering=abilities
        )
        await self._write_adversary(adversary)

    @staticmethod
    async def _is_ability(data):
        if {'id', 'platforms'}.issubset(set(data.keys())):
            return True
        return False

    async def _write_ability(self, data):
        d = os.path.join(self.data_dir, 'abilities', data['tactic'])
        if not os.path.exists(d):
            os.makedirs(d)
        file_path = os.path.join(d, '%s.yml' % data['id'])
        with open(file_path, 'w') as f:
            f.write(yaml.dump([data]))

    @staticmethod
    def get_privilege(executors):
        try:
            for ex in executors:
                if 'elevation_required' in ex:
                    return 'Elevated'
                return False
        except:
            return False

    async def _save_ability(self, ab):
        """
        Return True iif an ability was saved.
        """

        ability = dict(
            id=str(uuid.uuid4()),
            name=ab.pop('name', ''),
            description=ab.pop('description', ''),
            tactic=ab.pop('tactic', None),
            technique=dict(name=ab.get('technique', dict()).get('name'),
                           attack_id=ab.pop('technique', dict()).get('attack_id')),
            repeatable=ab.pop('repeatable', False),
            requirements=ab.pop('requirements', []),
            platforms=dict()
        )

        privilege = self.get_privilege(ab.get('executors'))
        if privilege:
            ability['privilege'] = privilege

        for platforms, executors in ab.pop('platforms', dict()).items():
            for name, info in executors.items():
                for e in name.split(','):
                    for pl in platforms.split(','):
                        ability.get('platforms', dict()).update({
                            pl: {
                                e:
                                    {
                                        'command': info['command'].strip(),
                                        'payloads': info.get('payloads', []),
                                        'cleanup': info['command'].strip()
                                    }
                            }
                        })

        await self._write_ability(ability)
        return ability['id']

    async def populate_sources_directory(self, path_yaml=None):
        """
        Populate the 'sources' directory with the Adversary Emulation Library abilities.
        """

        if not path_yaml:
            path_yaml = os.path.join(self.repo_dir, '**', '**', '*.yaml')

        for filename in glob.iglob(path_yaml):
            emulation_plan = self.strip_yml(filename)[0]

            variables = {}
            details = {}
            for entry in emulation_plan:
                if 'emulation_plan_details' in entry:
                    details = entry['emulation_plan_details']
                if not await self._is_ability(entry):
                    continue
                arguments = entry.get('input_arguments')
                if not arguments:
                    continue
                platforms = entry.get('platforms', {})
                for platform, executors in platforms.items():
                    for executor, properties in executors.items():
                        if 'command' not in properties:
                            continue
                        command = properties['command']
                        for name, values in arguments.items():
                            value = values.get('default')
                            if value:
                                variables[name.strip()] = value.strip()

            await self._save_facts(details.get('adversary_name', filename),
                                   variables)

    async def _save_facts(self, name, variables):
        id = str(uuid.uuid4())
        sources = {
            'id': id,
            'name': name,
            'facts': self._facts(variables),
        }
        if not os.path.exists(self.sources_dir):
            os.makedirs(self.sources_dir)
        path = os.path.join(self.sources_dir, '%s.yml' % id)
        with open(path, 'w', encoding='utf-8') as f:
            yaml.dump(sources, stream=f, sort_keys=False)

    def _facts(self, variables):
        return [{'trait': name, 'value': value}
                for name, value in sorted(variables.items())]
