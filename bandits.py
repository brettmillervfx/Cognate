from enum import Enum
from typing import List, Tuple, Set
import copy

import sys
sys.path.append('D:\\projects')
import cognate.knowledge as cog
import cognate.world as world



class CanMoveRule:
    def __init__(self, agent, location):
        self.agent = agent
        self.location = location
        self.current_location = []
        self.dependencies = set()

    def test(self, knowledge: cog.KnowledgeStack) -> bool:
        """
        Must be a path, no closed gate
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
                
                # With relaxed planning we may have simultaneous open/closed gates.
                # If a gate is both open and closed, we allow passage.
                if knowledge.check_fact(world.OpenGate(current_location, self.location)):
                    self.dependencies.add(world.OpenGate(current_location, self.location))
                elif knowledge.check_fact(world.ClosedGate(current_location, self.location)):
                    continue
                               
                self.dependencies.add(world.At(self.agent, current_location))
                self.dependencies.add(world.Path(current_location, self.location))

                self.current_location.append(current_location)

                found = True
        
        return found
    

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
        

class MoveAction:
    def __init__(self, agent, location):
        # these values are fixed, necessarily
        self.agent = agent
        self.location = location
        self.prev_location = None

        self.can_move_rule = CanMoveRule(self.agent, self.location)

        self.dependencies = set()

        self.add_list = set()
        self.delete_list = set()

    def meets_preconditions(self, knowledge: cog.KnowledgeStack):
        can_move = self.can_move_rule.test(knowledge)
        if not can_move:
            return False
        self.prev_location = self.can_move_rule.current_location
        self.dependencies = self.can_move_rule.dependencies
        return True

    def generate_add_list(self, knowledge: cog.KnowledgeStack):
        self.add_list = {world.At(self.agent, self.location)}
        return self.add_list
    
    def generate_delete_list(self, knowledge: cog.KnowledgeStack):
        # we sometimes have multiple prev_locations
        prevs = set(self.prev_location)
        for prev in prevs:
            self.delete_list.add(world.At(self.agent, prev))
        return self.delete_list
    
    def __repr__(self):
        return f"Move {self.agent} from {self.prev_location} to {self.location}"
    
    def hash(self):
        return hash((self.dependencies, self.add_list, self.add_list, 'move'))


class TriggerAction:
    def __init__(self, agent):
        # these values are fixed, necessarily
        self.agent = agent

        self.can_trigger_rule = CanTriggerRule(self.agent)

        self.dependencies = set()

        self.add_list = set()
        self.delete_list = set()

        self.location = None

    def meets_preconditions(self, knowledge: cog.KnowledgeStack):
        can_trigger = self.can_trigger_rule.test(knowledge)
        if not can_trigger:
            return False
        self.dependencies = self.can_trigger_rule.dependencies
        return True

    def generate_add_list(self, knowledge: cog.KnowledgeStack):
        # flop gate pairs
        for dep in self.can_trigger_rule.dependencies:
            if dep.functor == world.Functor.TRIGGER:
                gate1, gate2, self.location = dep.arguments
                if knowledge.check_fact(world.OpenGate(gate1, gate2)):
                    self.add_list.add(world.ClosedGate(gate1, gate2))
                if knowledge.check_fact(world.ClosedGate(gate1, gate2)):
                    self.add_list.add(world.OpenGate(gate1, gate2))
        return self.add_list
    
    def generate_delete_list(self, knowledge: cog.KnowledgeStack):
        # flop gate pairs
        for dep in self.can_trigger_rule.dependencies:
            if dep.functor == world.Functor.TRIGGER:
                gate1, gate2, _ = dep.arguments
                if knowledge.check_fact(world.ClosedGate(gate1, gate2)):
                    self.delete_list.add(world.ClosedGate(gate1, gate2))
                if knowledge.check_fact(world.OpenGate(gate1, gate2)):
                    self.delete_list.add(world.OpenGate(gate1, gate2))
        return self.delete_list
    
    def __repr__(self):
        return f"Trigger at {self.location}"
    
    def hash(self):
        return hash((self.dependencies, self.add_list, self.add_list, 'trigger'))


class Bandit():
    def __init__(self, name):
        self.name = name
        self.goal = None

    def set_goal(self, goal):
        self.goal = goal

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


