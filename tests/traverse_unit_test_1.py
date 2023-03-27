import logging

import sys
sys.path.append("D:\\projects\\")

# from cognate import action
# from cognate import predicate
# from cognate import rpg
# from cognate import knowledge
# from cognate import ehc

# def test_old_system():
#     logging.basicConfig(level=logging.DEBUG)

#     adb = action.read_action_file("D:\\cognate\\tests\\EscapeRoom.yml")
#     parser = predicate.Parser()
#     parser.read_knowledge_file("D:\\cognate\\tests\\EscapeRoom.pl")
#     k = parser.knowledge

#     _, goals = parser.compile_goals('at(agent,outside)')
#     ehcs = ehc.EnforcedHillClimbingSearch( adb, k, goals )
#     actions = ehcs.ehc_search()
#     if actions:
#         for a in actions:
#             print(a)
#     else:
#         print("You can't get there from here.")


#from cognate import knowledge2
import cognate.knowledge as cog


def test_flat_knowledge_and_facts():
    k = cog.BaseKnowledge() 
    k.append( cog.At('bill', 'canyon') )
    k.append( cog.At('sam', 'esb') )
    k.append( cog.At('robert', 'esb') )
    k.append( cog.IsHouse('esb') )  

    print(f"k.test( At('bill', 'canyon') ) -> {k.test( cog.At('bill', 'canyon') )}") 
    print(f"k.test( At('sam', 'canyon') ) -> {k.test( cog.At('sam', 'canyon') )}") 
    print(f"k.test( At('sam', 'esb') ) -> {k.test( cog.At('sam', 'esb') )}") 
    print(f"k.test( At('lucy', 'canyon') -> {k.test( cog.At('lucy', 'canyon') )}") 
    print(f"k.test( IsHouse('esb') ) -> {k.test( cog.IsHouse('esb') )}") 

def test_variables():
    x = cog.Variable()
    p = cog.Proposal( cog.Functor.AT, ('bill', x) )
    p.consider( ('bill', 'canyon') ) 
    p.consider( ('sam', 'canyon') )   
    p.consider( ('bill', 'esb') )
    print(x)

    p = cog.Proposal( cog.Functor.IS_HOUSE, (x,) )
    p.consider( ('esb',) )  
    print(x)

    x.apply_and()
    print(x)

def test_multi_term_proposal():
    """ This is how we'd do multiple term proposals. """
    k = cog.BaseKnowledge() 
    k.append( cog.At('bill', 'canyon') )
    k.append( cog.At('sam', 'esb') )
    k.append( cog.At('robert', 'esb') )
    k.append( cog.IsHouse('esb') ) 

    location = cog.Variable()
    p1 = cog.Proposal( cog.Functor.AT, ('bill', location) )  
    k.find_possible_solutions(p1)

    p2 = cog.Proposal( cog.Functor.IS_HOUSE, (location,) )  
    k.find_possible_solutions(p2)

    location.apply_and()

    print(location)

    # this doesn't work because we're not supporting ambiguous proposals.
    # is that a mistake? Is that important for this system?
    
    who = cog.Variable()
    where = cog.Variable()
    p1 = cog.Proposal( cog.Functor.AT, (who, where) )  
    k.find_possible_solutions(p1)

    p2 = cog.Proposal( cog.Functor.IS_HOUSE, (where,) )  
    k.find_possible_solutions(p2)

    print(who)
    print(where)

    # find all house occupants
    # could do it like this:
    where = cog.Variable()
    p1 = cog.Proposal( cog.Functor.IS_HOUSE, (where,) )  
    k.find_possible_solutions(p1)

    who = cog.Variable()
    for l in where.possible_values:
        p = cog.Proposal( cog.Functor.AT, (who, l ) )
        k.find_possible_solutions(p)
        who.apply_or()

    print(who)

def test_rule():
    # We consider a thief is somebody who has a weapon and is at a house.
    # we want to find out who the thief is.
    
    k = cog.KnowledgeStack()
    k.append(cog.At('bill', 'wall street'))
    k.append(cog.At('bob', 'white house'))
    k.append(cog.At('sam', 'your house'))
    k.append(cog.IsHouse('your house'))
    k.append(cog.IsHouse('white house'))
    k.append(cog.Has('bill', 'sandwich'))
    k.append(cog.Has('bob', 'dagger'))
    k.append(cog.Has('sam', 'phone'))
    k.append(cog.IsWeapon('dagger'))

    r = cog.IsThiefRule('bill')
    if r.test(k):
        print(f"Bill is the thief: {r.dependencies}")
    else:
        print('Bill is not a thief.')

    r = cog.IsThiefRule('bob')
    if r.test(k):
        print(f"Bob is the thief: {r.dependencies}")
    else:
        print('Bob is not a thief.')


def test_knowledge_stack():
    ks = cog.KnowledgeStack()
    ks.append(cog.At('bill', 'wall street'))
    ks.append(cog.At('bob', 'white house'))
    ks.append(cog.At('sam', 'your house'))
    ks.append(cog.IsHouse('your house'))
    ks.append(cog.IsHouse('white house'))  

    who = cog.Variable()
    p = cog.Proposal( cog.Functor.AT, (who, 'white house') )
    ks.find_possible_solutions(p)
    print(who) # {'bob'}

    print(ks.push_layer()) # 1
    ks.append(cog.At('sam', 'white house'))
    ks.remove(cog.At('sam', 'your house'))
    p = cog.Proposal( cog.Functor.AT, (who, 'white house') )
    ks.find_possible_solutions(p)
    print(who) # {'bob', 'sam'}

    print(ks.push_layer()) # 2
    ks.remove(cog.At('bob', 'white house'))
    p = cog.Proposal( cog.Functor.AT, (who, 'white house') )
    ks.find_possible_solutions(p)
    print(who) # {'sam'}

    print(ks.pop_layer()) # 1
    p = cog.Proposal( cog.Functor.AT, (who, 'white house') )
    ks.find_possible_solutions(p)
    print(who) # {'bob', 'sam'}

    print(ks.pop_layer()) # 0
    p = cog.Proposal( cog.Functor.AT, (who, 'white house') )
    ks.find_possible_solutions(p)
    print(who) # {'bob'}

    print(ks.pop_layer()) # -1
    p = cog.Proposal( cog.Functor.AT, (who, 'white house') )
    ks.find_possible_solutions(p)
    print(who) # {'bob'}


# if __name__ == "__main__" : test_flat_knowledge_and_facts() 
# if __name__ == "__main__" : test_variables() 
#if __name__ == "__main__" : test_knowledge_stack() 
if __name__ == "__main__" : test_rule() 