import copy

import rpg
import action
import knowledge
import predicate



class StateNode:
    def __init__(self, action_db, goals, delta, max_depth=10, action=None):
        self._action_db = action_db
        self._goals = goals
        self._max_depth = max_depth
        self.action = action
        self._delta = delta.clone()
        self.counter = 0

        relaxed_plan = rpg.RelaxedPlanningGraph(self._delta, action_db, goals)
        self.helpful_actions, self.heuristic = relaxed_plan.heuristic(max_depth)

    def __lt__(self, other):
        return self.heuristic < other.heuristic

    def apply_action(self, action):
        # produce a new node using an action
        # heuristic is already calculated
        
        # can this action be applied?
        terms = [predicate.Term.from_axiom(prec) for prec in action.preconditions]
        #success, _ = self._delta.search(terms)
        search_results = self._delta.search(terms) 
        
        if len(search_results) == 0:
            return None  
        
        self._delta.add_layer()
        for effect in action.add_effects:
            self._delta.add_axiom(effect)
        for effect in action.delete_effects:
            self._delta.delete_axiom(effect)

        successor = StateNode(self._action_db, self._goals, self._delta, self._max_depth, action)
        self._delta.remove_layer()
        return successor

    def get_successors(self):
        successors = []
        for h_a in self.helpful_actions:
            successor = self.apply_action(h_a)
            if successor:
                successors.append(successor)
        successors.sort()
        return successors

    def get_next_successor(self):
        if self.counter >= len(self.helpful_actions):
            return None
        next_action = self.apply_action(self.helpful_actions[self.counter])
        self.counter += 1
        return next_action

    def is_exhausted(self):
        return self.counter >= len(self.helpful_actions)

    def __repr__(self):
        return f"action: {self.action}, h: {self.heuristic}"

    def __lt__(self, other):
        return self.heuristic < other.heuristic


class EnforcedHillClimbingSearch:
    def __init__(self, action_db, known, goals):
        self._delta = knowledge.KnowledgeDelta(known)
        self._curr_state = StateNode(action_db, goals, self._delta)
        self._initial_state = self._curr_state
        pass

    def bf_search(self, candidates, heuristic_to_beat):
        queue = [ [candidate] for candidate in candidates ]
        while len(queue):
            path = queue.pop(0)
            node = path[-1]
            if node.heuristic < heuristic_to_beat:
                return path[-1], [state.action for state in path]
            
            #successors = [node.apply_action(h_a) for h_a in node.helpful_actions]
            successors = []
            for h_a in node.helpful_actions:
                successor = node.apply_action(h_a)
                if successor:
                    successors.append(successor)

            successors.sort()
            for successor in successors:
                new_path = path
                new_path.append(successor)
                queue.append(new_path)
        return None, []

    def DEPsearch(self):
        ''' Enforced Hill Climbing Search
        '''
        action_stack = []
        while self._curr_state.heuristic > 0:
            #successors = [self._curr_state.apply_action(h_a) for h_a in self._curr_state.helpful_actions]
            successors = []
            for h_a in self._curr_state.helpful_actions:
                successor = self._curr_state.apply_action(h_a)
                if successor:
                    successors.append(successor)
            
            if len(successors):
                successors.sort()

                # greedily explore best successor state if heuristic improves
                if successors[0] < self._curr_state:
                    action_stack.append(successors[0].action)
                    self._curr_state = successors[0]
                else:
                    # if there isn't a better state, we resort to breadth-first search
                    self._curr_state, substack = self.bf_search(successors, self._curr_state.heuristic)
                    # self._curr_state, substack = self.bf_search(successors, 1)
                    action_stack.extend(substack)
            
            else:
                # ECH has failed
                print('ECH has failed. Restarting search with BFS.')
                successors = [self._initial_state.apply_action(h_a) for h_a in self._initial_state.helpful_actions]
                if len(successors):
                    _, action_stack = self.bf_search(successors, self._curr_state.heuristic)
                else:
                    # dead end -- we can't achieve the goal from here.
                    return None

        return action_stack

    
    def greedy_bfs(self):
        search_queue = [self._initial_state]
        while len(search_queue):
            search_queue.sort()
            current = search_queue.pop(0)
            while not current.is_exhausted():
                successor = current.get_next_successor()
                if successor.heuristic == 0: # arrived at goal state
                    return successor # replace this with plan
                if successor.heuristic < current.heuristic:
                    search_queue.insert(0,current)
                    search_queue.insert(0,successor)
                    break
                else:
                    search_queue.append(successor)
        return None

    def ehc_search(self):
        open_list = [[self._curr_state]]
        best_heuristic = self._curr_state.heuristic
        while len(open_list):
            path = open_list.pop(0)
            curr_state = path[-1]
            successors = curr_state.get_successors()
            while len(successors):
                next_state = successors.pop(0)
                h = next_state.heuristic
                if h == 0: # this is a goal state
                    path.append(next_state)
                    return path
                if h < best_heuristic:
                    successors.clear()
                    open_list.clear()
                    best_heuristic = h
                new_path = copy.copy(path)
                new_path.append(next_state)
                open_list.append(new_path)
        return None

    def search(self):
        results = None 
        self.ehc_search()
        if results == None:
            print('failed. trying best first search.')
            results = self.greedy_bfs()
            if results == None:
                print('failed. there is no solution.')




# https://www.cs.cmu.edu/afs/cs/project/jair/pub/volume28/coles07a-html/node5.html
# I'm doing this wrong.

def test():
    adb = action.read_action_file("D:\\cognate\\EscapeRoom.yml")
    parser = predicate.Parser()
    parser.read_knowledge_file("D:\\cognate\\EscapeRoom.pl")
    k = parser.knowledge
    
    _, goals = parser.compile_goals('at(agent,outside)')
    #goals = [knowledge.Term('at(agent,outside)')]
    #goals = [knowledge.Term('at(agent,under_the_window)')]
    #goals = [knowledge.Term('has(agent,key)')]


    ehcs = EnforcedHillClimbingSearch( adb, k, goals )
    actions = ehcs.ehc_search()
    #actions = ehcs.greedy_bfs()
    if actions:
        for a in actions:
            print(a)
    else:
        print("You can't get there from here.")

def weird():
    adb = action.read_action_file("D:\\cognate\\EscapeRoom.yml")
    parser = predicate.Parser()
    _, goals = parser.compile_goals('at(agent,outside)')
    parser.read_knowledge_file("D:\\cognate\\EscapeRoom.pl")
    k = parser.knowledge
    d = knowledge.KnowledgeDelta(k)
    d.add_layer()
    d.add_axiom(parser.parse_line('open(closet_door)'))
    d.delete_axiom(parser.parse_line('closed(closet_door)'))
    d.add_layer()
    d.add_axiom(parser.parse_line('at(agent,under_the_window)'))
    d.delete_axiom(parser.parse_line('at(agent,by_the_closet)'))
    d.add_layer()
    d.delete_axiom(parser.parse_line('at(agent,under_the_window)'))
    d.add_axiom(parser.parse_line('at(agent,by_the_closet)'))
    
    relaxed_plan = rpg.RelaxedPlanningGraph(d, adb, goals)
    helpful_actions, heuristic = relaxed_plan.heuristic(10)
    print(heuristic)
    


if __name__ == "__main__" : test()     







