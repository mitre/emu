from app.objects.secondclass.c_fact import Fact
from app.objects.secondclass.c_relationship import Relationship
from app.utility.base_parser import BaseParser


class Parser(BaseParser):

    def parse(self, blob):
        """Parses out group names from net group /domain"""
        relationships = []

        for line in self.line(blob):
            if line.startswith('*'):
                for mp in self.mappers:
                    source = self.set_value(mp.source, line, self.used_facts)
                    target = self.set_value(mp.target, line, self.used_facts)
                    relationships.append(
                    Relationship(source=Fact(mp.source, source),
                                    edge=mp.edge,
                                    target=Fact(mp.target, target))
                    )
        return relationships
