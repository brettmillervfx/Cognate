from typing import List, Set

import sys
sys.path.append('D:\\projects')

import cognate.knowledge as cog
import cognate.heuristic as heu
import cognate.central as central
import cognate.search as search


class Action:
    def __init__(self):
        self.dependencies = set()
        self.adds = set()
        self.removes = set()
        self.timestamp = None
        self.required_goal = None

    def meets_preconditions(self, knowledge: cog.KnowledgeStack) -> bool:
        return False
    
    def generate_adds(self, knowledge: cog.KnowledgeStack) -> Set[cog.Fact]:
        return {}
    
    def generate_removes(self, knowledge: cog.KnowledgeStack) -> Set[cog.Fact]:
        return {}
    
    def hash(self):
        return hash(1234)


class Agent:
    def __init__(self, name):
        self.name = name
        self.goal = None
        self.knowledge = None
        self.next_available_time = 0
        self.action_plan = []

    def set_knowledge(self, knowledge: cog.KnowledgeStack):
        self.knowledge = knowledge.clone()
        self.knowledge.advance_to(self.next_available_time)

    def supply_bid(self, goal: cog.Fact):
        self.goal = goal
        rpg = heu.RelaxedPlanningGraph(self.knowledge, self)
        bid,_ = rpg.generate_heuristic()
        return bid

    def plan(self, goal: cog.Fact, central_planner: central.CentralPlanner) -> int:
        """ Commit plan to satisfy goal. Return time when goal is satisfied. """
        self.goal = goal
        self.knowledge.rebuild_layers()
        s = search.SearchPlan(self.knowledge, self)
        
        # plan will be None if planning fails. We need to handle it.
        # for now we assume that plans always work.
        plan = s.plan()
        if plan is None:
            return heu.DEAD_END

        # Commit as much as possible. 
        blocking_goal = None
        for action in plan:
            if action.required_goal is None:
                self.action_plan.append(action)
                central_planner.add_predictions(action)
                self.knowledge.push_layer()       
                self.next_available_time += 1
            else:
                blocking_goal = action.required_goal
                break

        if blocking_goal is None:
            # Plan is complete
            return self.next_available_time
        
        # Contract blocking goal
        resume_time = central_planner.contract(blocking_goal)
        while self.next_available_time < resume_time:
            #self.plan.append(Wait(self))
            self.knowledge.push_layer() 
            self.next_available_time += 1    

        # Complete planning
        return self.plan(goal, central_planner)

    def produce_valid_actions(self, knowledge: cog.KnowledgeStack) -> List[Action]:
        return []

    def admit_plans(self):
        for p in self.action_plan:
            print(p)
