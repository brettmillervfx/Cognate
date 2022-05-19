from functools import reduce
import logging

import predicate
import knowledge
import action

DEAD_END = 99999

class RelaxedPlanningGraph:
    def __init__(self, delta, adb, goals):
        self._state = delta
        self._adb = adb
        self._goals = goals
        self._relaxed_plan = []
        self._depth = 0

    def satisfied(self):
        solutions = self._state.search(self._goals)
        if len(solutions) == 0:
            return False
        return True

    def evaluate_relaxed_plan(self):
        helpful_actions = []
        
        # start with satisfied goals
        search_axioms = [predicate.Axiom.from_term_instance(goal.instance({})) for goal in self._goals]
        for l in reversed(range(self._depth)):
            # find current goals in this fact layer
            found_rules = [rule for rule in search_axioms if rule in self._state.current_add()]
            
            # get actions in previous action layer that added facts that satisfied those goals
            found_actions = []
            for rule in found_rules:
                #found_actions.extend([action for action in self._relaxed_plan[l] if rule in action.add_effects])
                for action in self._relaxed_plan[l]:
                    if rule in action.add_effects:
                        if action not in found_actions:
                            found_actions.append(action)
                        if rule in search_axioms:
                            search_axioms.remove(rule)
                        break

            # helpful actions are the ones leading to the goal
            helpful_actions.append(found_actions)
            
            #preconditions of the helpful actions become goals to search for in next fact layer
            for action in helpful_actions[-1]:
                for rule in action.preconditions:
                    if rule not in search_axioms:
                        search_axioms.append(rule)
            
            # cleanup
            self._state.remove_layer()

        # heuristic is count of helpful goals
        h = reduce(lambda count, l: count + len(l), helpful_actions, 0)
        if len(helpful_actions):
            return helpful_actions[-1], h
        return None, h

    def heuristic(self, max_depth=999):
        while self._depth < max_depth:
            if self.satisfied():
                break

            viables = self._adb.get_possible_actions(self._state)

            # if there are no actions and we haven't satisfied goals, this is a dead end
            if len(viables) == 0:
                return [],DEAD_END

            # add a new fact layer resulting from the action layer
            self._state.add_layer()
            self._relaxed_plan.append(viables)
            for action in viables:
                for effect in action.add_effects:
                    # expensive -- is there a cheaper way?
                    if not self._state.test_axiom(effect):
                        self._state.add_axiom(effect)
            
            # if no new facts were added and the goal isn't found,
            # this is a dead end
            if self._state.current_add_count() == 0:
                return [],DEAD_END

            self._depth += 1

        # extract actions, heuristic
        helpful_actions, h = self.evaluate_relaxed_plan()

        return helpful_actions, h




def test():
    logging.basicConfig(level=logging.DEBUG)

    adb = action.read_action_file("D:\\cognate\\EscapeRoom.yml")
    parser = predicate.Parser()
    parser.read_knowledge_file("D:\\cognate\\EscapeRoom.pl")
    k = parser.knowledge
    delta = knowledge.KnowledgeDelta(k)

    _, terms = parser.compile_goals('at(agent,outside)')
    rpg = RelaxedPlanningGraph(delta, adb, terms)
    #print(delta.search([knowledge.Term('at(agent,X)')]))
    #print(delta.search( [ knowledge.Term('at(A,L)'), knowledge.Term('person(A)'), knowledge.Term('can_traverse(L,T)') ] ))
    #delta.add_rule(knowledge.Rule('foo(bar)'))
    #delta.add_rule(knowledge.Rule('foo(bar)'))
    #print(delta._base.search( [ knowledge.Term('at(A,L)') ], delta ))
    ha, h = rpg.heuristic(max_depth=10)
    for act in ha:
        print(act)
    print(h)
    
    # can_open(A,D) :- door(D), unlocked(D), closed(D), next_to(A,D)
    # print(initial_state.search([ knowledge.Term('can_open(agent,closet_door)')]))
    # print(initial_state.search([ knowledge.Term('next_to(agent,X)')]))
    # print(initial_state.search([ knowledge.Term('can_traverse(in_the_closet,X)')]))
    
    viables = adb.get_possible_actions(k)
    for v in viables:
        print(v.description)

if __name__ == "__main__" : test() 