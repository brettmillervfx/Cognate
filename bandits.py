from enum import Enum
from typing import List, Tuple, Set
import copy

import sys
sys.path.append('D:\\projects')
import cognate.knowledge as cog


class Functor(Enum):
    PATH = 0
    DROP = 1
    TELEPORTABLE = 2
    DOWNSTAIRS = 3
    UPSTAIRS = 4
    OPEN_GATE = 5
    CLOSED_GATE = 6
    AT = 7
    TRIGGER = 8

class Path(cog.Fact):
    def __init__(self, node1, node2):
        self.functor = Functor.PATH
        self.arguments = (node1, node2) 

    def __repr__(self):
        return f"Path {self.arguments}" 

class Drop(cog.Fact):
    def __init__(self, node1, node2):
        self.functor = Functor.DROP
        self.arguments = (node1, node2)  

    def __repr__(self):
        return f"Drop {self.arguments}" 

class Teleportable(cog.Fact):
    def __init__(self, node1, node2):
        self.functor = Functor.TELEPORTABLE
        self.arguments = (node1, node2)

    def __repr__(self):
        return f"Teleportable {self.arguments}" 

class Downstairs(cog.Fact):
    def __init__(self, node1, node2):
        self.functor = Functor.DOWNSTAIRS
        self.arguments = (node1, node2)  

    def __repr__(self):
        return f"Downstairs {self.arguments}" 

class Upstairs(cog.Fact):
    def __init__(self, node1, node2):
        self.functor = Functor.UPSTAIRS
        self.arguments = (node1, node2) 

    def __repr__(self):
        return f"Upstairs {self.arguments}" 

class OpenGate(cog.Fact):
    def __init__(self, node1, node2):
        self.functor = Functor.OPEN_GATE
        self.arguments = (node1, node2) 

    def __repr__(self):
        return f"OpenGate {self.arguments}" 

class ClosedGate(cog.Fact):
    def __init__(self, node1, node2):
        self.functor = Functor.CLOSED_GATE
        self.arguments = (node1, node2) 

    def __repr__(self):
        return f"ClosedGate {self.arguments}" 

class At(cog.Fact):
    def __init__(self, agent, node):
        self.functor = Functor.AT
        self.arguments = (agent, node) 

    def __repr__(self):
        return f"At {self.arguments}" 

class Trigger(cog.Fact):
    def __init__(self, gate1, gate2, trigger_location):
        self.functor = Functor.TRIGGER
        self.arguments = (gate1, gate2, trigger_location) 

    def __repr__(self):
        return f"Trigger {self.arguments}" 


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
        knowledge.find_possible_solutions( cog.Proposal( Functor.AT, (self.agent, current_location) ) )

        # it's unlikely that there is no location, but...
        if len(current_location.possible_values) == 0:
            return False
        
        # On the other hand, with relaxed planning it's possible to be in many locations at once..
        # see if there's a path from any of my locations
        found = False
        for current_location in current_location.possible_values:
            if knowledge.check_fact(Path(current_location, self.location)):
                
                # With relaxed planning we may have simultaneous open/closed gates.
                # If a gate is both open and closed, we allow passage.
                if knowledge.check_fact(OpenGate(current_location, self.location)):
                    self.dependencies.add(OpenGate(current_location, self.location))
                elif knowledge.check_fact(ClosedGate(current_location, self.location)):
                    continue
                               
                self.dependencies.add(At(self.agent, current_location))
                self.dependencies.add(Path(current_location, self.location))

                self.current_location.append(current_location)

                found = True
        
        return found
    

class CanTriggerRule:
    def __init__(self, agent):
        self.agent = agent
        self.dependencies = set()

    def test(self, knowledge: cog.KnowledgeStack) -> bool:
        current_location = cog.Variable()
        knowledge.find_possible_solutions( cog.Proposal( Functor.AT, (self.agent, current_location) ) )

        # it's unlikely that there is no location, but...
        if len(current_location.possible_values) == 0:
            return False
        
        # On the other hand, with relaxed planning it's possible to be in many locations at once..
        found = False
        for current_location in current_location.possible_values:
            gate1 = cog.Variable()   
            gate2 = cog.Variable() 
            knowledge.find_possible_solutions( cog.Proposal( Functor.TRIGGER, (gate1, gate2, current_location) ) )
            if len(gate1.possible_values) > 0:
                found = True
                self.dependencies.add(At(self.agent, current_location)) 
       
                # Not all combinations are actually real.
                for g1 in gate1.possible_values:
                    for g2 in gate2.possible_values:
                        if knowledge.check_fact(Trigger(g1, g2, current_location)): 
                            self.dependencies.add(Trigger(g1, g2, current_location)) 
       
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
        self.add_list = {At(self.agent, self.location)}
        return self.add_list
    
    def generate_delete_list(self, knowledge: cog.KnowledgeStack):
        # we sometimes have multiple prev_locations
        prevs = set(self.prev_location)
        for prev in prevs:
            self.delete_list.add(At(self.agent, prev))
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
            if dep.functor == Functor.TRIGGER:
                gate1, gate2, self.location = dep.arguments
                if knowledge.check_fact(OpenGate(gate1, gate2)):
                    self.add_list.add(ClosedGate(gate1, gate2))
                if knowledge.check_fact(ClosedGate(gate1, gate2)):
                    self.add_list.add(OpenGate(gate1, gate2))
        return self.add_list
    
    def generate_delete_list(self, knowledge: cog.KnowledgeStack):
        # flop gate pairs
        for dep in self.can_trigger_rule.dependencies:
            if dep.functor == Functor.TRIGGER:
                gate1, gate2, _ = dep.arguments
                if knowledge.check_fact(ClosedGate(gate1, gate2)):
                    self.delete_list.add(ClosedGate(gate1, gate2))
                if knowledge.check_fact(OpenGate(gate1, gate2)):
                    self.delete_list.add(OpenGate(gate1, gate2))
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
        knowledge.find_possible_solutions( cog.Proposal( Functor.AT, (self.name, current_location) ) )
        if len(current_location.possible_values) == 0:
            return [] # maybe bandit is dead?
        
        # with relaxed planning, bandit may be in multiple locations at once
        for current_location in current_location.possible_values:
            destinations = cog.Variable()
            knowledge.find_possible_solutions( cog.Proposal( Functor.PATH, (current_location, destinations) ) )
            for destination in destinations.possible_values:
                potential_action = MoveAction(self.name, destination)
                if potential_action.meets_preconditions(knowledge):
                    valid_actions.append(potential_action)

        potential_action = TriggerAction(self.name)
        if potential_action.meets_preconditions(knowledge):
            valid_actions.append(potential_action)

        return valid_actions



k = cog.KnowledgeStack()

# maze initial conditions
k.append( Path('start', 'junction') )
k.append( Path('junction', 'start') )
k.append( Path('junction', 'path_a') )
k.append( Path('path_a', 'junction') )
k.append( Path('junction', 'path_b') )
k.append( Path('path_b', 'junction') )
k.append( Path('junction', 'path_c') )
k.append( Path('path_c', 'junction') )
k.append( Path('trigger_a', 'trigger_b') )
k.append( Path('trigger_b', 'trigger_a') )
k.append( Path('path_a', 'trigger_a') )
k.append( Path('trigger_a', 'path_a') )
k.append( ClosedGate('path_a', 'trigger_a') )
k.append( ClosedGate('trigger_a', 'path_a') )
k.append( Trigger('path_a', 'trigger_a', 'junction') )
k.append( Trigger('trigger_a', 'path_a', 'junction') )
k.append( Path('path_b', 'path_b1') )
k.append( Path('path_b1', 'path_b') )
k.append( Path('path_b1', 'path_b2') )
k.append( Path('path_b2', 'path_b1') )
k.append( ClosedGate('path_b1', 'path_b2') )
k.append( ClosedGate('path_b2', 'path_b1') )
k.append( Trigger('path_b1', 'path_b2', 'trigger_b') )
k.append( Trigger('path_b2', 'path_b1', 'trigger_b') )
k.append( Path('path_b2', 'path_b3') )
k.append( Path('path_b3', 'path_b2') )
k.append( Path('path_b3', 'end') )
k.append( Path('end', 'path_b3') )
k.append( ClosedGate('path_b3', 'end') )
k.append( ClosedGate('end', 'path_b3') )
k.append( Trigger('path_b3', 'end', 'trigger_c') )
k.append( Trigger('end', 'path_b3', 'trigger_c') )
k.append( Path('path_c', 'trigger_c') )
k.append( Path('trigger_c', 'path_c') )


# bandit initial condition
# k.append( cog.At('bandit_A', 'start') )
# b = Bandit('bandit_A')
# b.set_goal(At('bandit_a', 'end'))