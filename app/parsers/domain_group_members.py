from app.objects.secondclass.c_fact import Fact
from app.objects.secondclass.c_relationship import Relationship
from app.utility.base_parser import BaseParser


class Parser(BaseParser):
    SUCCESS_STR = 'The command completed successfully.'

    def parse(self, blob):
        """Parses out group members from net group <group name> /domain commands"""
        relationships = []
        for mp in self.mappers:
            for host in self._get_domain_computers(self.line(blob)):
                source = self.set_value(mp.source, host, self.used_facts)
                target = self.set_value(mp.target, host, self.used_facts)
                relationships.append(
                    Relationship(source=Fact(mp.source, source),
                                 edge=mp.edge,
                                 target=Fact(mp.target, target))
                )
        return relationships

    @staticmethod
    def _get_domain_computers(net_group_lines):
        end_index = -1
        dash_index = -1
        domain_computers = []
        for index, line in enumerate(net_group_lines):
            if line.startswith('---------------'):
                dash_index = index
            elif line.startswith(Parser.SUCCESS_STR):
                end_index = index
                break
        if end_index > 0 and dash_index > 0:
            for host_lines in net_group_lines[dash_index + 1:end_index]:
                for host_chunk in [host_lines[i:i + 25] for i in range(0, len(host_lines), 25)]:
                    host = host_chunk.strip().removesuffix('$')
                    domain_computers.append(host)
        return domain_computers
