from enum import Enum
from typing import List, Tuple, Set
import copy


class Variable:
    """
    Holds a list of sets of values.

    """
    def __init__(self):
        self.possible_values = set()
        self.cached_results = None

    def add_possibility(self, value: any) -> None:
        self.possible_values.add(value)

    def cache_results(self):
        self.cached_results = copy.copy(self.possible_values)
        self.possible_values.clear()
    
    def apply_and(self) -> None:
        if self.cached_results is not None:
            self.possible_values = self.possible_values.intersection(self.cached_results)

    def apply_or(self) -> None:
        if self.cached_results is not None:
            self.possible_values = self.possible_values.union(self.cached_results)
    
    def __str__(self):
        if len(self.possible_values):
            return f"possible values: {self.possible_values}"
        else:
            return 'There are no solutions.'


class Fact:
    def __init__(self, functor=None, arguments=()):
        self.functor = functor
        self.arguments = arguments

    def __eq__(self, other) -> bool:
        """ Compare the two fixed axioms """
        if self.functor != other.functor:
            return False
        if len(self.arguments) != len(other.arguments):
            return False
        if hash(self.arguments) != hash(other.arguments):
            return False
        
        return True
    
    def __hash__(self):
        return hash((self.functor, self.arguments))
    
    def __repr__(self):
        return f"{self.functor.name} -> {self.arguments}"
    
    
class Proposal():
    def __init__(self, functor, arguments: Tuple):
        self.functor = functor
        self.arguments = arguments
        
        self.variables = []
        self.fixed_arguments = []
        for i in range(len(self.arguments)):
            if isinstance(self.arguments[i], Variable):
                self.arguments[i].cache_results()
                self.variables.append(i)
            else:
                self.fixed_arguments.append(i)

    def consider(self, arguments) -> bool:
        # We assume that the functor has already matched
        if len(arguments) == len(self.arguments):
            # fixed arguments must match
            for index in self.fixed_arguments:
                if arguments[index] != self.arguments[index]:
                    return False
            # unfixed arguments are unioned to existing variables
            for index in self.variables:
                self.arguments[index].add_possibility(arguments[index])



class BaseKnowledge():
    """ Flat Knowledge contains all of the facts that are known.
    """
    def __init__(self):
        """ Facts are arranged by functor. Each functor has a set of known argument tuples. """
        self.facts = {}

    def append(self, fact: Fact) -> None:
        try:
            self.facts[fact.functor].add(fact.arguments)
        except KeyError:
            self.facts[fact.functor] = {fact.arguments}

    def test(self, fact: Fact) -> bool:
        """ Test if the proposed fact is known. """
        return fact.arguments in self.facts[fact.functor]
    
    def find_possible_solutions(self, proposal):
        if isinstance(proposal, Proposal):
            for fact_arguments in self.facts[proposal.functor]:
                proposal.consider(fact_arguments)
        else: # this is a Rule
            proposal.solve(self)


class PredictedKnowledge():
    """ Tranches of knowledge that are predicted to be true at a future date.
    """
    def __init__(self):
        """ 
        Facts are arranged by functor, as with BaseKnowledge.
        Each functor has a dictionary mapping known argument tuples to timestamps when the fact will be
        added or removed.
        """
        self.added_facts = {}
        self.removed_facts = {}

    def append_add(self, fact: Fact, time: int) -> None:
        try:
            tranch = self.added_facts[fact.functor]
            try:
                tranch[fact.arguments] = min(time, tranch[fact.arguments])
            except KeyError:
                tranch[fact.arguments] = time
        except KeyError:
            self.added_facts[fact.functor] = {fact.arguments: time}

    def append_remove(self, fact: Fact, time: int) -> None:
        try:
            tranch = self.removed_facts[fact.functor]
            try:
                tranch[fact.arguments] = min(time, tranch[fact.arguments])
            except KeyError:
                tranch[fact.arguments] = time
        except KeyError:
            self.removed_facts[fact.functor] = {fact.arguments: time}

    def test_addition(self, fact: Fact) -> int:
        """ 
        Test if the proposed fact is predicted to be added.
        Returns a -1 if it is not, otherwise the relative timestamp at which it is predicted to be true.
        """
        try:
            return self.added_facts[fact.functor][fact.arguments]
        except KeyError:
            return -1
        
    def test_removal(self, fact: Fact) -> int:
        """ 
        Test if the proposed fact is predicted to be removed.
        Returns a -1 if it is not, otherwise the relative timestamp at which it is predicted to be true.
        """
        try:
            return self.removed_facts[fact.functor][fact.arguments]
        except KeyError:
            return -1
        
    def get_predicted_adds(self, time: int) -> List[Fact]:
        adds = []
        for functor,tranch in self.added_facts.items():
            for arguments,prediction_time in tranch.items():
                if time == prediction_time:
                    adds.append(Fact(functor, arguments))
        return adds
    
    def get_predicted_removes(self, time: int) -> List[Fact]:
        removes = []
        for functor,tranch in self.removed_facts.items():
            for arguments,prediction_time in tranch.items():
                if time == prediction_time:
                    removes.append(Fact(functor, arguments))
        return removes
        

class KnowledgeDelta:
    def __init__(self):
        self.adds = {}
        self.deletes = {}

    def append(self, fact: Fact) -> None:
        try:
            functor_set = self.adds[fact.functor]
        except KeyError:           
            functor_set = set()
            self.adds[fact.functor] = functor_set

        functor_set.add(fact.arguments)

    def remove(self, fact: Fact) -> None:
        try:
            functor_set = self.deletes[fact.functor]
        except KeyError:           
            functor_set = set()
            self.deletes[fact.functor] = functor_set

        functor_set.add(fact.arguments)


class KnowledgeStack:
    def __init__(self, base_knowledge=None):
        if base_knowledge is None:
            self.base = BaseKnowledge()
        else:
            self.base = base_knowledge
        
        self.current_layer = 0
        self.layers = []
        self.predictions = PredictedKnowledge()

    def push_layer(self) -> int:
        self.current_layer += 1
        self.layers.append(KnowledgeDelta())

        # realize predictions
        for fact in self.predictions.get_predicted_adds(self.current_layer):
            self.append(fact)

        for fact in self.predictions.get_predicted_removes(self.current_layer):
            self.remove(fact)

        return self.current_layer 

    def pop_layer(self) -> int:
        if self.current_layer == 0:
            # Base layer cannot be popped
            return -1
        
        self.layers.pop()
        self.current_layer -= 1
        return self.current_layer
    
    def append(self, fact: Fact) -> None:
        if self.current_layer == 0:
            self.base.append(fact)
        else:        
            # don't append a fact that is already true
            if not self.check_fact(fact):
                self.layers[self.current_layer-1].append(fact)

    def remove(self, fact: Fact) -> None:
        if self.current_layer == 0:
            # Base layer is only positive
            return
        
        # don't remove a fact that isn't already true
        if self.check_fact(fact):
            self.layers[self.current_layer-1].remove(fact)

    def flatten(self, functor) -> Set[Tuple]:
        try:
            flattened = copy.copy(self.base.facts[functor])
        except KeyError:
            flattened = set()

        layer = 1
        while layer <= self.current_layer:
            # add and remove according to current layer
            if functor in self.layers[layer-1].adds:
                for args in self.layers[layer-1].adds[functor]:
                    flattened.add(args)
            if functor in self.layers[layer-1].deletes:
                for args in self.layers[layer-1].deletes[functor]:
                    flattened.discard(args)
                
            layer += 1

        return flattened
    
    def check_fact(self, fact: Fact) -> bool:
        flattened_knowledge = self.flatten(fact.functor)  

        for fact_arguments in flattened_knowledge:
            if fact_arguments == fact.arguments:
                return True
        return False  
    
    def find_possible_solutions(self, proposal: Proposal):
        # One wonders if this will become a performance issue
        # We may want to cache this.
        # Note that this is a shallow copy so the facts themselves persist
        flattened_knowledge = self.flatten(proposal.functor)
        
        for fact_arguments in flattened_knowledge:
            proposal.consider(fact_arguments)

    def facts_in_current_add(self):
        """ This is used in heuristic search to determine if we've reached a terminal state. """
        if self.current_layer == 0:
            return 0
        
        return len(self.layers[self.current_layer-1].adds)
    
    def predict_add(self, fact: Fact, time: int) -> None:
        self.predictions.append_add(fact, time)

    def predict_remove(self, fact: Fact, time: int) -> None:
        self.predictions.append_remove(fact, time)

    def check_prediction(self, fact: Fact, removal=False) -> int:
        if removal:
            return self.predictions.test_removal(fact)
        else:
            return self.predictions.test_removal(fact)

