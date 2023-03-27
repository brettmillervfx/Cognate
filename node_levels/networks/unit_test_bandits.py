import copy
import sys
sys.path.append("D:\\projects\\")

import cognate.knowledge as cog
import cognate.bandits as band
import cognate.heuristic as heu
import cognate.search as search



def test_trigger():
    band.k.append( band.At('bandit_A', 'junction') )
    gate1 = cog.Variable()   
    gate2 = cog.Variable() 
    band.k.find_possible_solutions( cog.Proposal( band.Functor.TRIGGER, (gate1, gate2, 'junction') ) )
    print(gate1)   


def test_move_action():
    band.k.append( band.At('bandit_A', 'junction') )
    b = band.Bandit('bandit_A')
    actions = b.produce_valid_actions(band.k)
    print(actions)

    for action in actions:
        print(action.meets_preconditions(band.k))
        print(action.generate_add_list(band.k))
        print(action.generate_delete_list(band.k))
        print('---')



def test_relaxed_planning_graph():
    
    b = band.Bandit('bandit_A')
    b.set_goal(band.At('bandit_A', 'path_b1'))

    test_k = copy.deepcopy(band.k)
    test_k.append( band.At('bandit_A', 'junction') )
    rpg = heu.RelaxedPlanningGraph(test_k, b)
    heuristic, actions = rpg.generate_heuristic()
    print('from junction')
    print(heuristic)
    print(actions)

    test_k = copy.deepcopy(band.k)
    test_k.append( band.At('bandit_A', 'path_b1') )
    rpg = heu.RelaxedPlanningGraph(test_k, b)
    heuristic, actions = rpg.generate_heuristic()
    print('from path_b1')
    print(heuristic)
    print(actions)

    test_k = copy.deepcopy(band.k)
    test_k.append( band.At('bandit_A', 'trigger_c') )
    rpg = heu.RelaxedPlanningGraph(test_k, b)
    heuristic, actions = rpg.generate_heuristic()
    print('from trigger_c')
    print(heuristic)
    print(actions)


def test_search_easy():
    b = band.Bandit('bandit_A')
    b.set_goal(band.At('bandit_A', 'path_b1'))

    test_k = copy.deepcopy(band.k)
    test_k.append( band.At('bandit_A', 'start') ) 

    s = search.SearchPlan(test_k, b)
    plan = s.plan()

    for p in plan:
        print(p) 

    print(s.dc_count) 

def test_search_hard():
    b = band.Bandit('bandit_A')
    b.set_goal(band.At('bandit_A', 'end'))

    test_k = copy.deepcopy(band.k)
    test_k.append( band.At('bandit_A', 'start') ) 

    s = search.SearchPlan(test_k, b)
    plan = s.plan()

    for p in plan:
        print(p)  

    # this isn't determinsitic
    print(f"generated {s.dc_count} states") 




#if __name__ == "__main__" : test_trigger() 
#if __name__ == "__main__" : test_move_action() 
#if __name__ == "__main__" : test_relaxed_planning_graph() 
#if __name__ == "__main__" : test_search_easy() 
if __name__ == "__main__" : test_search_hard() 




