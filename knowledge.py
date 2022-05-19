import logging
import copy

import predicate


def remove_duplicates(solutions):
    de_duped_env = []
    de_duped_axioms = []
    for solution in solutions:
        if solution[0] not in de_duped_env:
            de_duped_env.append(solution[0])
            de_duped_axioms.append(solution[1])

    ret = []
    for env, axiom in zip(de_duped_env, de_duped_axioms):
        ret.append((env,axiom))
    return ret


class AxiomDB:
    def __init__(self):
        self.axioms = {}

    def add_axiom(self, axiom):
        if axiom.phash not in self.axioms:
            self.axioms[axiom.phash] = {axiom.ahash: axiom}
        else:
            self.axioms[axiom.phash][axiom.ahash] = axiom

    def test_axiom(self, axiom, negate=False):
        axiom_set = self.axioms.get(axiom.phash)
        if axiom_set and axiom.ahash in axiom_set:
            return False if negate else True
        return False

    def find_matching_axioms(self, term):
        matches = self.axioms.get(term.phash)
        if matches:
            bound_envs = []
            axiom_deps = []
            for _,axiom in matches.items():
                bind = axiom.match(term)
                if bind:
                    # every binding is caused by an axiom
                    bound_envs.append(bind)
                    axiom_deps.append([axiom])
            return bound_envs, axiom_deps
        # no matching axioms
        return None, None

    
class Knowledge:
    def __init__(self):
        #self.axioms = {}
        self.axiom_db = AxiomDB()
        self.rules = {}

    def add_rule(self, rule):
        if isinstance(rule, predicate.Axiom):
            self.axiom_db.add_axiom(rule)
        else:
            if rule.head.phash not in self.rules:
                self.rules[rule.head.phash] = []
            self.rules[rule.head.phash].append(rule)

    def find_matching_rules(self, term):
        bound_rules = []
        matches = self.rules.get(term.phash)
        if matches:
            for rule in matches:
                bound_rules.append(rule.match(term))
        if term.negate:
            for bound_rule in bound_rules:
                bound_rule.head.negate = True
        return bound_rules    
    
    def bind(self, goal):
        # goal is a TermInstance but I'm making a Rule
        new_goals = []
        found = False

        # has this resolved to an axiom?
        axiom, negate = goal.proposal()
        if axiom:
            # is this axiom true?
            #resolution = self.active_axioms.test_axiom(axiom, negate)
            resolution = self.active_axioms.test_axiom(axiom, False)
            if resolution:
                #parent = goal.update_parent(resolution)
                parent = goal.update_parent(not negate)
                parent.axioms.append(axiom)
                new_goals.append(parent)
                found = True
        else:
            # find binding axioms
            axiom_envs, axiom_deps = self.active_axioms.find_matching_axioms(goal)
            if axiom_envs != None:
                if len(axiom_envs):
                    found = True
                    for env, dep in zip(axiom_envs, axiom_deps):
                        new_goals.append(goal.to_rule_instance(env, dep))
                
        # find binding rules
        rules = self.find_matching_rules(goal)
        if rules:
            found = True
            new_goals.extend(rules)

        if not found:
            if goal.negate:
                parent = goal.update_parent(True)
            else:
                parent = goal.update_parent(False)
            new_goals.append(parent)

        return new_goals
        
    def search(self, goal_terms, delta=None):
        #we may have a layered delta
        self.active_axioms = self.axiom_db
        if delta:
            self.active_axioms = delta
        
        goal_texts = [str(term) for term in goal_terms]
        parser = predicate.Parser()
        initial_rule = parser.parse_line("all(done):-" + ','.join(goal_texts))
        queue = [initial_rule.instance()]
        solutions = []

        while len(queue) :
            curr_rule = queue.pop(0)
            #print(curr_rule)
            if curr_rule.satisfied():
                if curr_rule.parent:
                    # put a parent back on the queue with the current bindings
                    #if this is a rule updating another rule, it's possible the env needs remapping
                    filter_env = len(curr_rule.goals) > 0
                    queue.append(curr_rule.update_parent(curr_rule.resolution(), filter_env))
                    continue
                else:
                    # no parent means this is our root
                    if curr_rule.resolution():
                        if curr_rule.env:
                            solutions.append((curr_rule.env, curr_rule.axioms))
                        else:
                            solutions.append((True, curr_rule.axioms))

                    continue

            # current rule is not complete so spawn the next goal
            curr_goal = curr_rule.get_next_goal()
            bound_goals = self.bind(curr_goal)
            for bound_goal in bound_goals:
                queue.append(bound_goal)
        
        remove_duplicates(solutions)
        return solutions


class KnowledgeDelta:
    def __init__(self, base):
        # layers are populated with Rules
        self._add_layers = []
        self._layer_counts = []
        self._delete_layers = []
        self._current_layer = -1
        self._base = base

    def add_layer(self):
        self._add_layers.append([])
        self._layer_counts.append(-1)
        self._delete_layers.append([])
        self._current_layer += 1

    def remove_layer(self):
        if self._current_layer > -1:
            self._add_layers.pop()
            self._layer_counts.pop()
            self._delete_layers.pop()
            self._current_layer -= 1 
            return True
        return False

    def add_axiom(self, axiom):
        # check to see if rule is already present
        if self.should_add(axiom):
            self._add_layers[self._current_layer].append(axiom)
            self._layer_counts[self._current_layer] += 1

    def delete_axiom(self, axiom):
        if axiom not in self._delete_layers[self._current_layer]:
            self._delete_layers[self._current_layer].append(axiom)

    def should_add(self, axiom):
        for layer in range(self._current_layer+1):
            if axiom in self._add_layers[layer]:
                return False
            if axiom in self._delete_layers[layer]:
                return True
        return True

    def is_axiom_deleted(self, axiom):
        for layer in reversed(range(self._current_layer+1)):
            if axiom in self._add_layers[layer]:
                return False
            if axiom in self._delete_layers[layer]:
                return True
        return False

    def current_add_count(self):
        return len(self._add_layers[self._current_layer])

    def current_add(self):
        return self._add_layers[self._current_layer]

    def search(self, terms):
        return self._base.search(terms, self)

    def clone(self):
        clone = KnowledgeDelta(self._base)
        clone._add_layers = copy.copy(self._add_layers)
        clone._layer_counts = copy.copy(self._layer_counts)
        clone._delete_layers = copy.copy(self._delete_layers)
        clone._current_layer = self._current_layer
        return clone

    def test_axiom(self, axiom, negate=False):
        for layer in reversed(range(self._current_layer+1)):
            for a in self._add_layers[layer]:
                if axiom == a:
                    return False if negate else True
            for a in self._delete_layers[layer]:
                if axiom == a:
                    return False

        return self._base.axiom_db.test_axiom(axiom, negate)

    def find_matching_axioms(self, term):
        bound_envs, axiom_deps = self._base.axiom_db.find_matching_axioms(term)
        if not bound_envs:
            bound_envs = []
            axiom_deps = []
        solutions = list(zip(bound_envs, axiom_deps))

        for layer in range(self._current_layer+1):
            solutions = [solution for solution in solutions if solution[1][0] not in self._delete_layers[layer]]
            for added in self._add_layers[layer]:
                if added.phash == term.phash:
                    bind = added.match(term)
                    if bind:
                        solutions.append((bind, [added]))

        if not solutions:
            return None, None

        solutions = remove_duplicates(solutions)
        return zip(*solutions)


def test():
    logging.basicConfig(level=logging.DEBUG)

    parser = predicate.Parser()
    parser.read_knowledge_file("D:\\cognate\\negtest.pl")

    k = parser.knowledge

    at1 = parser.parse_line('door(window)')
    print('T ->' + str(k.axiom_db.test_axiom(at1)))
    print('F ->' + str(k.axiom_db.test_axiom(at1, negate=True)))

    at2 = parser.parse_line('door(window, floor)')
    print('F ->' + str(k.axiom_db.test_axiom(at2)))
    
    at3 = parser.parse_line('door(floor)')
    print('F ->' + str(k.axiom_db.test_axiom(at3)))
    
    _, terms = parser.compile_goals('door(X)')
    print ('two solutions ->')
    print(k.search(terms))

    _, terms = parser.compile_goals('not(door(X))')
    print('empty ->')
    print(k.search(terms))

    _, terms = parser.compile_goals('not(open(window))')
    print('empty ->')
    print(k.search(terms))

    _, terms = parser.compile_goals('blocked(X, outside)')
    print('one solution ->')
    print(k.search(terms))

    _, terms = parser.compile_goals('can_traverse(X, outside)')
    print('one solution ->')
    print(k.search(terms))

    _, terms = parser.compile_goals('can_traverse(outside, X)')
    print('one solution ->')
    print(k.search(terms))

    d = KnowledgeDelta(k)
    at1 = parser.parse_line('door(window)')
    print('T ->' + str(d.test_axiom(at1)))
    print('F ->' + str(d.test_axiom(at1, negate=True)))

    d.add_layer()
    d.delete_axiom(at1)
    print('F ->' + str(d.test_axiom(at1)))
    print('F ->' + str(d.test_axiom(at1, negate=True)))

    d.add_layer()
    d.add_axiom(at1)
    print('T ->' + str(d.test_axiom(at1)))
    print('F ->' + str(d.test_axiom(at1, negate=True)))

    at = parser.parse_line('path(under_the_window,the_moon)')
    d.add_axiom(at)
    _, terms = parser.compile_goals('path(under_the_window,X)')
    print('two solutions ->')
    print(d.search(terms))

    _, terms = parser.compile_goals('can_traverse(under_the_window, the_moon)')
    print('truth ->')
    print(d.search(terms))

    _, terms = parser.compile_goals('at(window,outside)')
    print('truth ->')
    print(k.search(terms))

    _, terms = parser.compile_goals('foo(apple,durian)')
    print('truth ->')
    print(k.search(terms))

    _, terms = parser.compile_goals('at(window,outside)')
    print('truth ->')
    print(k.search(terms))

    parser = predicate.Parser()
    parser.read_knowledge_file("D:\\cognate\\EscapeRoom.pl")
    initstate = parser.knowledge
    _, terms = parser.compile_goals('person(agent),at(agent,by_the_closet),path(under_the_window,by_the_closet),open(under_the_window,by_the_closet)')
    print('truth ->')
    print(initstate.search(terms))
    delta = KnowledgeDelta(initstate)
    print('truth ->')
    print(delta.search(terms))

if __name__ == "__main__" : test()