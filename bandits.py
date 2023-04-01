from enum import Enum
from typing import List, Tuple, Set
import copy

import sys
sys.path.append('D:\\projects')
import cognate.knowledge as cog
import cognate.world as world
import cognate.agent as agent


   

class CanTriggerRule:
    def __init__(self, agent):
        self.agent = agent
        self.dependencies = set()

    def test(self, knowledge: cog.KnowledgeStack) -> bool:
        current_location = cog.Variable()
        knowledge.find_possible_solutions( cog.Proposal( world.Functor.AT, (self.agent, current_location) ) )

        # it's unlikely that there is no location, but...
        if len(current_location.possible_values) == 0:
            return False
        
        # On the other hand, with relaxed planning it's possible to be in many locations at once..
        found = False
        for current_location in current_location.possible_values:
            gate1 = cog.Variable()   
            gate2 = cog.Variable() 
            knowledge.find_possible_solutions( cog.Proposal( world.Functor.TRIGGER, (gate1, gate2, current_location) ) )
            if len(gate1.possible_values) > 0:
                found = True
                self.dependencies.add(world.At(self.agent, current_location)) 
       
                # Not all combinations are actually real.
                for g1 in gate1.possible_values:
                    for g2 in gate2.possible_values:
                        if knowledge.check_fact(world.Trigger(g1, g2, current_location)): 
                            self.dependencies.add(world.Trigger(g1, g2, current_location)) 
       
        # trigger is at agent location
        return found
        

class CanMoveRule:
    def __init__(self, agent, location):
        self.agent = agent
        self.location = location
        self.current_location = []
        self.dependencies = set()

        # If Miniboss needs a gate opened, we record it here
        self.required_goal = None

    def test(self, knowledge: cog.KnowledgeStack) -> bool:
        """
        Must be a path, if gate is closed report as goal
        """
        current_location = cog.Variable()
        knowledge.find_possible_solutions( cog.Proposal( world.Functor.AT, (self.agent, current_location) ) )

        # it's unlikely that there is no location, but...
        if len(current_location.possible_values) == 0:
            return False
        
        # On the other hand, with relaxed planning it's possible to be in many locations at once..
        # see if there's a path from any of my locations
        found = False
        for current_location in current_location.possible_values:
            if knowledge.check_fact(world.Path(current_location, self.location)):
                
                # If we potentially have a closed gate here, record is as requirement for passage
                if knowledge.check_fact(world.ClosedGate(current_location, self.location)):
                    self.required_goal = world.OpenGate(current_location, self.location)
                               
                self.dependencies.add(world.At(self.agent, current_location))
                self.dependencies.add(world.Path(current_location, self.location))

                self.current_location.append(current_location)

                found = True
        
        return found

class MoveAction(agent.Action):
    def __init__(self, agent, location):
        super().__init__()

        # these values are fixed, necessarily
        self.agent = agent
        self.location = location
        self.prev_location = None

        self.can_move_rule = CanMoveRule(self.agent, self.location)

    def meets_preconditions(self, knowledge: cog.KnowledgeStack):
        can_move = self.can_move_rule.test(knowledge)
        if not can_move:
            return False
        self.prev_location = self.can_move_rule.current_location
        self.dependencies = self.can_move_rule.dependencies

        self.required_goal = self.can_move_rule.required_goal
        return True

    def generate_adds(self, knowledge: cog.KnowledgeStack):
        self.adds = {world.At(self.agent, self.location)}
        return self.adds
    
    def generate_removes(self, knowledge: cog.KnowledgeStack):
        # we sometimes have multiple prev_locations
        prevs = set(self.prev_location)
        for prev in prevs:
            self.removes.add(world.At(self.agent, prev))
        return self.removes
    
    def __repr__(self):
        try:
            prev_loc = self.prev_location[0]
        except IndexError:
            prev_loc = self.prev_location
        ret = f"t={self.timestamp}: Move {self.agent} from {prev_loc} to {self.location}"
        if self.required_goal:
            ret += f"\n\trequired: {self.required_goal}"
        return ret
    
    def hash(self):
        return hash((self.dependencies, self.adds, self.removes, 'move'))

class TriggerAction(agent.Action):
    def __init__(self, agent):
        super().__init__()

        # these values are fixed, necessarily
        self.agent = agent
        self.location = None

        self.can_trigger_rule = CanTriggerRule(self.agent)

    def meets_preconditions(self, knowledge: cog.KnowledgeStack):
        can_trigger = self.can_trigger_rule.test(knowledge)
        if not can_trigger:
            return False
        self.dependencies = self.can_trigger_rule.dependencies
        return True

    def generate_adds(self, knowledge: cog.KnowledgeStack):
        # flop gate pairs
        for dep in self.can_trigger_rule.dependencies:
            if dep.functor == world.Functor.TRIGGER:
                gate1, gate2, self.location = dep.arguments
                if knowledge.check_fact(world.OpenGate(gate1, gate2)):
                    self.adds.add(world.ClosedGate(gate1, gate2))
                if knowledge.check_fact(world.ClosedGate(gate1, gate2)):
                    self.adds.add(world.OpenGate(gate1, gate2))
        return self.adds
    
    def generate_removes(self, knowledge: cog.KnowledgeStack):
        # flop gate pairs
        for dep in self.can_trigger_rule.dependencies:
            if dep.functor == world.Functor.TRIGGER:
                gate1, gate2, _ = dep.arguments
                if knowledge.check_fact(world.ClosedGate(gate1, gate2)):
                    self.removes.add(world.ClosedGate(gate1, gate2))
                if knowledge.check_fact(world.OpenGate(gate1, gate2)):
                    self.removes.add(world.OpenGate(gate1, gate2))
        return self.removes
    
    def __repr__(self):
        return f"t={self.timestamp}: Trigger at {self.location}"
    
    def hash(self):
        return hash((self.dependencies, self.adds, self.adds, 'trigger'))


class Bandit(agent.Agent):
    def __init__(self, name):
        super().__init__(name)

    def produce_valid_actions(self, knowledge: cog.KnowledgeStack):
        valid_actions = []
        current_location = cog.Variable()
        knowledge.find_possible_solutions( cog.Proposal( world.Functor.AT, (self.name, current_location) ) )
        if len(current_location.possible_values) == 0:
            return [] # maybe bandit is dead?
        
        # with relaxed planning, bandit may be in multiple locations at once
        for current_location in current_location.possible_values:
            destinations = cog.Variable()
            knowledge.find_possible_solutions( cog.Proposal( world.Functor.PATH, (current_location, destinations) ) )
            for destination in destinations.possible_values:
                potential_action = MoveAction(self.name, destination)
                if potential_action.meets_preconditions(knowledge):
                    valid_actions.append(potential_action)

        potential_action = TriggerAction(self.name)
        if potential_action.meets_preconditions(knowledge):
            valid_actions.append(potential_action)

        return valid_actions


