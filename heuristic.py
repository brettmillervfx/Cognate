from typing import Tuple, List
from functools import reduce

# The heuristic value that says "don't go here"
DEAD_END = 99999

class RelaxedPlanningGraph:
    def __init__(self, knowledge, agent):
        self.knowledge = knowledge
        self.agent = agent
        self.goal = agent.goal

        # list of lists: each element is a layer of actions that can be taken
        self.plan = []
        self.depth = 0

    def is_satisfied(self):
        # TODO We currently think of the goal as a fixed fact.
        # Is that too limiting? If we need to open it up as a proposal, we can do that..
        return self.knowledge.check_fact(self.goal)
    
    def generate_heuristic(self, max_depth=999) -> Tuple[int, List]:
        """ Explain RPG so future self doesn't forget... """
        # Add positive facts from valid actions until goal state is found
        while self.depth < max_depth:
            if self.is_satisfied():
                break

            valid_actions = self.agent.produce_valid_actions(self.knowledge)

            # if there are no actions and we haven't satisfied goals, this is a dead end
            if len(valid_actions) == 0:
                return (DEAD_END, [])
            
            # append a new layer of actions
            self.plan.append(valid_actions)
            
            # add a new fact layer populated by add effects from viable actions 
            # that aren't already in the knowledge stack
            self.knowledge.push_layer() 
            for action in valid_actions:
                adds = action.generate_add_list(self.knowledge) 
                for add in adds:
                    self.knowledge.append(add)

            # if no new facts were added, we have reached a terminal state
            if self.knowledge.facts_in_current_add() == 0:
                return (DEAD_END, [])
            
            # increase depth and continue searching
            self.depth += 1

        # if we searched and search and found nothing, we have failed.
        if self.depth == max_depth:
            return (DEAD_END, [])

        # But if we found our goal state, analyze the plan for heuristoc and helpful actions
        return self.analyze_plan()   

    def analyze_plan(self) -> Tuple[int, List]:
        """ Explain how this leads to a heuristic, so future self doesn't forget. """
        helpful_actions = [set() for _ in range(self.depth)]
        preconditions = [set() for _ in range(self.depth+1)]
        
        # At the surface level, the only fact we care about is the satisfied goal
        preconditions[self.depth].add(self.goal)

        for layer in reversed(range(self.depth)):
            # for precondition in the layer above, find the first action
            # that satisfies the precondition. That action is set at a helpful 
            # action in the layer it was found and the preconditions ar added to 
            # it's layer
             
            for pc in preconditions[layer+1]:
                found = False
                for l in range(layer+1):
                    for action in self.plan[l]:
                        if pc in action.add_list:
                            found = True
                            helpful_actions[l].add(action)
                            preconditions[l].update(action.dependencies)
                            break
                    if found:
                        break 

            self.knowledge.pop_layer()

        if self.depth == 0:
            return 0, []
        
        # The heuristic is the count of all helpful actions.
        # Fewer is better
        heuristic = reduce(lambda count, l: count + len(l), helpful_actions, 0)

        # the last helpful actions in the stack indicate the agent's best moves
        return heuristic, helpful_actions[0]

                 
            
                      

                    



