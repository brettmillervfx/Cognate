from enum import Enum
from typing import List, Tuple, Set
import copy

import sys
sys.path.append('D:\\projects')
import cognate.knowledge as cog
import cognate.world as world


"""
Miniboss is somewhat simpler than bandits inthat it cannot use triggers to open gates. Movement and is the only action it may take.

On the other hand, it introduces some new complications. It must assume that all gates before it are open.
When it encounters a gate, it queues a goal with a requested timestamp. 
These goals feed a set of bandits who try to fulfill them.

The bandits will all review the goals, select them then estimate when they expect to be able to satisfy them.
Miniboss revises it's plan, until there is convergence.
This second part is somewhat more complicated so first we'll implmement just the goal queue.
"""


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

        # Miniboss is specific about when this action will occur
        self.timestamp = None

        # Miniboss may need a gate to be opened, expressed as a goal
        self.required_goal = None

    def meets_preconditions(self, knowledge: cog.KnowledgeStack):
        can_move = self.can_move_rule.test(knowledge)
        if not can_move:
            return False
        self.prev_location = self.can_move_rule.current_location
        self.dependencies = self.can_move_rule.dependencies

        self.required_goal = self.can_move_rule.required_goal
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
        try:
            prev_loc = self.prev_location[0]
        except IndexError:
            prev_loc = self.prev_location
        ret = f"t={self.timestamp}: Move {self.agent} from {prev_loc} to {self.location}"
        if self.required_goal:
            ret += f"\n\trequired: {self.required_goal}"
        return ret
    
    def hash(self):
        return hash((self.dependencies, self.add_list, self.add_list, 'move'))
    

class Miniboss():
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
        
        # with relaxed planning, miniboss may be in multiple locations at once
        for current_location in current_location.possible_values:
            destinations = cog.Variable()
            knowledge.find_possible_solutions( cog.Proposal( world.Functor.PATH, (current_location, destinations) ) )
            for destination in destinations.possible_values:
                potential_action = MoveAction(self.name, destination)
                if potential_action.meets_preconditions(knowledge):
                    valid_actions.append(potential_action)

        return valid_actions