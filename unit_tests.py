import sys
sys.path.append('D:\\projects')
import cognate.knowledge as cog
import cognate.heuristic as heu
import cognate.search as search

import cognate.world as world
import cognate.bandits as band
import cognate.miniboss as miniboss

import copy


def define_trigger_maze():
    k = cog.KnowledgeStack()

    # maze initial conditions
    k.append( world.Path('start', 'junction') )
    k.append( world.Path('junction', 'start') )
    k.append( world.Path('junction', 'path_a') )
    k.append( world.Path('path_a', 'junction') )
    k.append( world.Path('junction', 'path_b') )
    k.append( world.Path('path_b', 'junction') )
    k.append( world.Path('junction', 'path_c') )
    k.append( world.Path('path_c', 'junction') )
    k.append( world.Path('trigger_a', 'trigger_b') )
    k.append( world.Path('trigger_b', 'trigger_a') )
    k.append( world.Path('path_a', 'trigger_a') )
    k.append( world.Path('trigger_a', 'path_a') )
    k.append( world.ClosedGate('path_a', 'trigger_a') )
    k.append( world.ClosedGate('trigger_a', 'path_a') )
    k.append( world.Trigger('path_a', 'trigger_a', 'junction') )
    k.append( world.Trigger('trigger_a', 'path_a', 'junction') )
    k.append( world.Path('path_b', 'path_b1') )
    k.append( world.Path('path_b1', 'path_b') )
    k.append( world.Path('path_b1', 'path_b2') )
    k.append( world.Path('path_b2', 'path_b1') )
    k.append( world.ClosedGate('path_b1', 'path_b2') )
    k.append( world.ClosedGate('path_b2', 'path_b1') )
    k.append( world.Trigger('path_b1', 'path_b2', 'trigger_b') )
    k.append( world.Trigger('path_b2', 'path_b1', 'trigger_b') )
    k.append( world.Path('path_b2', 'path_b3') )
    k.append( world.Path('path_b3', 'path_b2') )
    k.append( world.Path('path_b3', 'end') )
    k.append( world.Path('end', 'path_b3') )
    k.append( world.ClosedGate('path_b3', 'end') )
    k.append( world.ClosedGate('end', 'path_b3') )
    k.append( world.Trigger('path_b3', 'end', 'trigger_c') )
    k.append( world.Trigger('end', 'path_b3', 'trigger_c') )
    k.append( world.Path('path_c', 'trigger_c') )
    k.append( world.Path('trigger_c', 'path_c') )

    return k


def test_trigger():
    k = define_trigger_maze()
    k.append( world.At('bandit_A', 'junction') )
    gate1 = cog.Variable()   
    gate2 = cog.Variable() 
    k.find_possible_solutions( cog.Proposal( world.Functor.TRIGGER, (gate1, gate2, 'junction') ) )
    print(gate1)   


def test_move_action():
    k = define_trigger_maze()
    k.append( world.At('bandit_A', 'junction') )
    b = band.Bandit('bandit_A')
    actions = b.produce_valid_actions(k)
    print(actions)

    for action in actions:
        print(action.meets_preconditions(k))
        print(action.generate_add_list(k))
        print(action.generate_delete_list(k))
        print('---')


def test_relaxed_planning_graph():
    k = define_trigger_maze()
    b = band.Bandit('bandit_A')
    b.set_goal(world.At('bandit_A', 'path_b1'))

    test_k = copy.deepcopy(k)
    test_k.append( world.At('bandit_A', 'junction') )
    rpg = heu.RelaxedPlanningGraph(test_k, b)
    heuristic, actions = rpg.generate_heuristic()
    print('from junction')
    print(heuristic)
    print(actions)

    test_k = copy.deepcopy(k)
    test_k.append( world.At('bandit_A', 'path_b1') )
    rpg = heu.RelaxedPlanningGraph(test_k, b)
    heuristic, actions = rpg.generate_heuristic()
    print('from path_b1')
    print(heuristic)
    print(actions)

    test_k = copy.deepcopy(k)
    test_k.append( world.At('bandit_A', 'trigger_c') )
    rpg = heu.RelaxedPlanningGraph(test_k, b)
    heuristic, actions = rpg.generate_heuristic()
    print('from trigger_c')
    print(heuristic)
    print(actions)


def test_search_easy():
    k = define_trigger_maze()
    b = band.Bandit('bandit_A')
    b.set_goal(world.At('bandit_A', 'path_b1'))

    k.append( world.At('bandit_A', 'start') ) 

    s = search.SearchPlan(k, b)
    plan = s.plan()

    for p in plan:
        print(p) 

    print(s.dc_count) 

def test_search_hard():
    k = define_trigger_maze()
    b = band.Bandit('bandit_A')
    b.set_goal(world.At('bandit_A', 'end'))

    k.append( world.At('bandit_A', 'start') ) 

    s = search.SearchPlan(k, b)
    plan = s.plan()

    for p in plan:
        print(p)  

    # this isn't determinsitic
    print(f"generated {s.dc_count} states") 

def test_miniboss_goal_queue():
    k = define_trigger_maze()

    mb = miniboss.Miniboss('Miniboss')
    mb.set_goal(world.At('Miniboss', 'end'))
    k.append( world.At('Miniboss', 'start') ) 

    s = search.SearchPlan(k, mb)
    plan = s.plan()

    for p in plan:
        print(p)

def test_knowledge_base_predictions():
    k = define_trigger_maze()
    print(f"true: {k.check_fact(world.ClosedGate('path_a', 'trigger_a'))}")   
    
    k.predict_add(world.OpenGate('path_a', 'trigger_a'), time=4)
    k.predict_remove(world.ClosedGate('path_a', 'trigger_a'), time=4)

    print(f"true: {k.check_fact(world.ClosedGate('path_a', 'trigger_a'))}") 

    # The gate is closed now, but will it ever be opened?
    print(f"true: {k.check_prediction(world.ClosedGate('path_a', 'trigger_a'), removal=True)}") 

    print(f"adds at 4: {k.predictions.get_predicted_adds(4)}")
    print(f"removes at 4: {k.predictions.get_predicted_removes(4)}")

    # add 4 layers to k and test the facts
    print(f"push {k.push_layer()}")
    print(f"push {k.push_layer()}")
    print(f"push {k.push_layer()}")
    print(f"is the gate open? {k.check_fact(world.OpenGate('path_a', 'trigger_a'))}")
    print(f"push {k.push_layer()}")
    print(f"is the gate open? {k.check_fact(world.OpenGate('path_a', 'trigger_a'))}")



if __name__ == "__main__" : 
    # print('----- test_trigger -----')
    # test_trigger() 

    # print('----- test_move_action -----')
    # test_move_action() 

    # print('----- test_relaxed_planning_graph -----')
    # test_relaxed_planning_graph() 

    # print('----- test_search_easy -----')
    # test_search_easy() 

    # print('----- test_search_hard -----')
    # test_search_hard() 

    # print('----- test_miniboss_goal_queue -----')
    # test_miniboss_goal_queue() 

    print('----- test_knowledge_base_predictions -----')
    test_knowledge_base_predictions() 
