import copy
import cognate.heuristic as heu


class State:
    def __init__(self, knowledge, agent, timestamp, action=None):
        self.agent = agent
        
        # This will lead to performance issues I think.
        # We'll need to architect knowledge in such a way as to minimize the impact of this sort of copy.
        # perhaps all facts can be maintained as singletons in a big hashtable?
        # Previously I think I had a 'clone' function to do this.
        # regardless, we'll want to measure how much allocation we're doing....
        self.knowledge = copy.deepcopy(knowledge)
       
        # action is what effected this state. None signifies that it is initial conditions
        self.action = action

        # Each state is timestamped from the original state
        self.timestamp = timestamp

        # we immediately generate heuristic for this state and helpful actions
        rpg = heu.RelaxedPlanningGraph(self.knowledge, self.agent)
        self.heuristic, self.actions = rpg.generate_heuristic()
        
        # timestamp all actions
        for action in self.actions:
            action.timestamp = self.timestamp+1 

    def get_successors(self):
        """ generate successor states from each helpful action """
        successors = []
        for action in self.actions:
            if action.meets_preconditions(self.knowledge):
                adds = action.generate_adds(self.knowledge)
                deletes = action.generate_removes(self.knowledge)
                
                if self.is_taboo(action):
                    continue
                
                self.knowledge.push_layer()
                for add in adds:
                    self.knowledge.append(add)
                for delete in deletes:
                    self.knowledge.remove(delete)
                successors.append(State(self.knowledge, self.agent, self.timestamp+1, action))
                self.knowledge.pop_layer()

        return sorted(successors, key=lambda s: s.heuristic)
    
    def is_taboo(self, successor):
        """ A successor is taboo if it precisely reverses the action that got us to
        this state in the first place, ie it backtracks.
        """
        if self.action is None:
            return False
        return self.action.adds == successor.removes and self.action.removes == successor.adds    

class SearchPlan:
    def __init__(self, knowledge, agent):
        self.curr_state = State(knowledge, agent, knowledge.current_layer)
        self.dc_count = 0

    def plan(self):
        ''' Enforced Hill Climbing Search of states leading to goal satisfaction.
        '''
        open_list = [[self.curr_state]]
        best_heuristic = self.curr_state.heuristic
        while len(open_list):
            path = open_list.pop(0)
            curr_state = path[-1]
            
            # evaluate all state that can be attained from this one.
            # the states are sort from best to worst
            successors = curr_state.get_successors()
            self.dc_count += len(successors)
            while len(successors):
                next_state = successors.pop(0)
                h = next_state.heuristic
                if h == 0: # this is a goal state
                    path.append(next_state)
                    return [state.action for state in path[1:]]
                
                if h < best_heuristic:
                    # either the first possible state is better than the current
                    # or we're at a local minimum or a plateau. If that's the case,
                    # we'll explore all possibilities.                  
                    for successor in successors:
                        new_path = copy.copy(path)
                        new_path.append(successor)
                        open_list.append(new_path)    
                    successors.clear()
                    best_heuristic = h
                new_path = copy.copy(path)
                new_path.append(next_state)
                open_list.insert(0, new_path)
        return None