from plugins.stockpile.app.requirements.base_requirement import BaseRequirement


class Requirement(BaseRequirement):

    async def enforce(self, link, operation):
        """
        Given a link and the current operation, ensure will only run if the agent with the given ID/PAW is alive.
        
        :param link
        :param operation
        :return: True if it complies, False if it doesn't
        """
        print("\n\n*********************\nin check_registered.py")
        agent_paws = [agent.paw for agent in await operation.active_agents()]
        for uf in link.used:
            print("id: ", uf.value ,"   agent_paws:", agent_paws)
            if uf.value in agent_paws:
                print("returning true - run this ability")
                return True
        print("returning false - don't run this ability")
        return False
    