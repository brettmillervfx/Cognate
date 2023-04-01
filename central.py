from typing import List, Dict

import sys
sys.path.append('D:\\projects')

import cognate.knowledge as cog

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from cognate.agent import Agent
    from cognate.agent import Action


class CentralPlanner:
    def __init__(self, base: cog.BaseKnowledge, agents: Dict[str, "Agent"]):
        self.knowledge_stack = cog.KnowledgeStack(base)
        self.agents = agents

    def plan(self, instigator_name: str, goal: cog.Fact) -> bool:
        """ Returns True if a plan was successfully developed. """
        try:
            instigator = self.agents[instigator_name]
        except KeyError:
            return False
        
        instigator.set_knowledge(self.knowledge_stack)
        return instigator.plan(goal, self)
    
    def contract(self, goal: cog.Fact) -> int:
        """ contracts goal to available agents, returns time of goal satisfaction. """
        # Collect initial bids
        bids = []
        for a in self.agents.values():
            a.set_knowledge(self.knowledge_stack)
            bids.append((a.supply_bid(goal), a))

        # sort bids
        bids.sort(key=lambda x:x[0])
   
        # assumption here is that the goal is attainable. 
        # We need to revisit this to test multiple agents and pick the best one.
        # and we also need to signal when a plan won't work
        bid_winner = bids[0][1]
        completion_time = bid_winner.plan(goal, self)
        return completion_time
    
    def add_predictions(self, action: "Action"):
        time_of_action = action.timestamp
        for add in action.adds:
            self.knowledge_stack.predict_add(add, time_of_action)
        for remove in action.removes:
            self.knowledge_stack.predict_remove(remove, time_of_action)
    
    def get_agents(self, agent_class: type) -> List["Agent"]:
        return [a for a in self.agents.values if isinstance(a, agent_class)]
    
    def admit_plans(self):
        for agent_name,agent in self.agents.items():
            print("-----------------")
            print(agent_name)
            agent.admit_plans()


