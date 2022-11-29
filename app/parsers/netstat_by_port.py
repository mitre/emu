import re

from app.objects.secondclass.c_fact import Fact
from app.objects.secondclass.c_relationship import Relationship
from app.utility.base_parser import BaseParser


class Parser(BaseParser):

    def parse(self, blob):
        """Parses out the IPv4 address(es) of an established connection to the given port
        from the output of `netstat -an`"""
        relationships = []

        lines = self.line(blob)
        connections = [l.split() for l in lines[lines.index('Active Connections')+2]]
        established = [c for c in connections if c[-1] == 'ESTABLISHED']
        matches = [x for x in established if bool(re.match(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b:' + mp.custom_parser_vals['port'], x[2]))]

        for m in matches:
            for mp in self.mappers:
                source = self.set_value(mp.source, m, self.used_facts)
                target = self.set_value(mp.target, m, self.used_facts)
                relationships.append(
                Relationship(source=Fact(mp.source, source),
                                edge=mp.edge,
                                target=Fact(mp.target, target))
                )
        return relationships
