#import hashlib
import logging
from os import path
import re
import copy
from functools import reduce

import knowledge



class Axiom:
    def __init__(self, pred, args):
        # args is a tuple of strings
        self.pred = pred
        self.args = args
        self.phash = hash((pred, len(args)))
        self.ahash = hash(tuple(self.args))

    def __hash__(self):
        return self.phash

    def __eq__(self, other):
        return self.phash == other.phash and self.ahash == other.ahash

    def __repr__(self):
        repr = f"axiom: {self.pred}("
        repr += ",".join(self.args)
        repr += ")"
        return repr

    def match(self, term):
        env = copy.copy(term.env)
        for a in range(len(self.args)):
            if not term.vars[a]:
                # optimize: this should really be done with hashes
                if self.args[a]:
                    if term.args[a] in term.env:
                        if self.args[a] != term.env[term.args[a]]:
                            return None
                    else:
                        if self.args[a] != term.args[a]:
                            return None
            else:
                if term.args[a] != '_':
                    env[term.args[a]] = self.args[a]
        return env

    def collapse(self, env):
        for a in range(len(self.args)):
            if is_variable(self.args[a]) and self.args[a] in env and self.args[a] != '_':
                self.args[a] = env[self.args[a]]
        self.ahash = hash(tuple(self.args))
        return self

    def from_term_instance(term):
        pred = term.pred
        args = term.args
        env = term.env
        axiom = Axiom(pred, args)
        axiom.collapse(env)
        return axiom

Vars = '_ABCDEFGHIJKLMNOPQRSTUVWXYZ'
def is_variable(arg):
    return len(arg) == 1 and arg in Vars

class Term:
    def __init__(self, neg, pred, args):
        self.negate = neg
        self.pred = pred
        self.phash = hash((pred,len(args)))
        self.vars = [len(a)==1 and a in Vars for a in args]
        
        # optimize: convert this to hashes
        self.args = args

    def __hash__(self):
        return self.phash

    def __eq__(self, other):
        return self.phash == other.phash

    def __repr__(self):
        repr = f"{self.pred}("
        repr += ",".join(self.args)
        repr += ")"
        if self.negate:
            repr = "not(" + repr + ")"
        return repr

    def from_axiom(axiom):
        pred = axiom.pred
        args = axiom.args
        neg = False
        return Term(neg, pred, args)

    def instance(self, env, parent=None):
        return TermInstance(self, env, parent)

    def subbed_repr(self, env):
        # Term
        subs = copy.copy(self.args)
        for a in range(len(subs)):
            if is_variable(subs[a]) and subs[a] in env:
                subs[a] = env[subs[a]]

        repr = f"{self.pred}("
        repr += ",".join(subs)
        repr += ")"
        if self.negate:
            repr = "not(" + repr + ")"
                
        return "vterm: " + repr


class TermInstance:
    def __init__(self, template, env, parent=None):
        self.negate = template.negate
        self.pred = template.pred
        self.phash = template.phash
        self.env = copy.copy(env)
        if '_' in self.env:
            del self.env['_']
        self.parent = parent

        # bind env in place
        self.vars = copy.copy(template.vars)
        self.args = copy.copy(template.args)
        for a in range(len(template.args)):
            if self.vars[a]:
                if self.args[a] in env:
                    self.vars[a] = False
                    #self.args[a] = env[self.args[a]]

    def proposal(self):
        unbound = reduce(lambda a, b: a or b, self.vars)
        if unbound:
            return None, False
        # argument substitution
        for a in range(len(self.args)):
            if not self.vars[a] and is_variable(self.args[a]) and self.args[a] != '_':
                self.args[a] = self.env[self.args[a]]
        return Axiom(self.pred, self.args), self.negate

    def to_rule_instance(self, env, dep):
        instance = RuleInstance()
        instance.head = TermInstance(self, env)
        #instance.parent = copy.deepcopy(self.parent)
        instance.parent = copy.copy(self.parent)
        instance.env = env
        instance.axioms = dep

        # bind args to env
        for a in range(len(instance.head.args)):
            if len(instance.head.args[a]) == 1 and instance.head.args[a] in Vars:
                if instance.head.args[a] == '_':
                    instance.head.vars[a] = False
                elif instance.head.args[a] in instance.env:
                    instance.head.vars[a] = False
                    instance.head.args[a] = instance.env[instance.head.args[a]]
                else:
                    instance.head.vars[a] = True
            else:
                instance.head.vars[a] = False

        return instance

    def update_parent(self, success=True):
        #updated_parent = copy.deepcopy(self.parent)
        updated_parent = copy.copy(self.parent)
        updated_parent.curr_term += 1
        
        # remap env to parent?
        updated_parent.env.update(self.env)

        #updated_parent.axioms.append(self.axioms)
        updated_parent.resolutions.append(success)
        return updated_parent

    def __repr__(self):
        subs = []
        for a in range(len(self.args)):
            if not self.vars[a] and is_variable(self.args[a]):
                subs.append(self.env[self.args[a]])
            else:
                subs.append(self.args[a])

        repr = f"{self.pred}("
        repr += ",".join(subs)
        repr += ")"
        if self.negate:
            repr = "not(" + repr + ")"
        return "term instance: " + repr

    def subbed_repr(self, env):
        subs = []
        for a in range(len(self.args)):
            if not self.vars[a] and is_variable(self.args[a]):
                subs.append(env[self.args[a]])
            else:
                subs.append(self.args[a])

        repr = f"{self.pred}("
        repr += ",".join(subs)
        repr += ")"
        if self.negate:
            repr = "not(" + repr + ")"
        return "term instance: " + repr 


class Rule:
    def __init__(self, disj, head, goals):
        self.disjunctive = disj
        self.head = head
        self.goals = goals
        self.phash = hash(self.head.phash)

    def __hash__(self):
        return self.phash

    def __eq__(self, other):
        return self.phash == other.phash

    def __repr__(self):
        repr = str(self.head) + " :- "
        if self.disjuctive:
            repr += "; ".join(self.goals)
        else:
            repr += ", ".join(self.goals)
        return "rule: " + repr

    def instance(self, parent=None):
        return RuleInstance(self, parent)

    def match(self, term):
        instance = RuleInstance(self, term.parent)

        # apply env bindings
        for a in range(len(instance.head.args)):
            if len(instance.head.args[a]) == 1 and instance.head.args[a] in Vars:
                if not term.vars[a]:
                    if is_variable(term.args[a]):
                        instance.env[instance.head.args[a]] = term.env[term.args[a]]
                    else:
                        instance.env[instance.head.args[a]] = term.args[a]
                    instance.head.vars[a] = False
                else:
                    instance.head.vars[a] = True

        return instance


class RuleInstance:
    def __init__(self, template=None, parent=None):
        if template:
            self.disjunctive = template.disjunctive
            self.head = template.head
            self.goals = template.goals
            self.phash = hash(template.head.phash)
            self.parent = parent
        else:
            self.disjunctive = False
            self.head = None
            self.goals = []
            self.phash = None
            self.parent = None

        self.curr_term = 0
        self.resolutions = []
        self.env = {}
        self.axioms = []

    def invert(self):
        self.disjunctive = not self.disjunctive
        for goal in self.goals:
            goal = copy.copy(goal)
            goal.negate = not goal.negate

    def satisfied(self):
        if self.curr_term >= len(self.goals):
            return True
        return False

    def resolution(self):
        if self.disjunctive:
            # probably won't be this simple
            return False
        else:
            if len(self.goals):
                # conjunctive solution -- if all resolutions are true, the rule is true
                res = reduce(lambda a, b: a and b, self.resolutions)
            else:
                    # no args -- if anything is bound it succeeds
                res = not reduce(lambda a, b: a or b, self.head.vars)

            if self.head.negate:
                res = not res
            return res

    def get_next_goal(self):
        if self.curr_term < len(self.goals):
            next_goal = self.goals[self.curr_term].instance(self.env, self)
            #self._curr_terms += 1
            return next_goal
        else:
            return None

    def update_parent(self, success=True, filter_env=False):
        #updated_parent = copy.deepcopy(self.parent)
        updated_parent = self.parent.clone()
        
        if filter_env:
            # remap env to parent
            filtered_env = {}
            for a in range(len(self.head.args)):
                if updated_parent.goals[updated_parent.curr_term].vars[a]:
                    if self.head.vars[a]:
                        if self.head.args[a] in self.env:
                            filtered_env[updated_parent.goals[updated_parent.curr_term].args[a]] = self.env[self.head.args[a]]
            
            updated_parent.env.update(filtered_env)
        else:
            updated_parent.env.update(self.env)
            # update vars?

        updated_parent.curr_term += 1
        updated_parent.axioms.extend(self.axioms)
        updated_parent.resolutions.append(success)
        return updated_parent

    def clone(self):
        clone = copy.copy(self)
        clone.resolutions = copy.copy(self.resolutions)
        clone.env = copy.copy(self.env)
        clone.axioms = copy.copy(self.axioms)
        return clone

        
    def __hash__(self):
        return self.phash

    def __eq__(self, other):
        return self.phash == other.phash

    def __repr__(self):
        goal_text = [goal.subbed_repr(self.env) for goal in self.goals]
        repr = self.head.subbed_repr(self.env) + " :- "
        if self.disjunctive:
            repr += "; ".join(goal_text)
        else:
            repr += ", ".join(goal_text)
        return "rule instance: " + repr



class Parser:
    def __init__(self):
        self.knowledge = knowledge.Knowledge()

    def _preprocess_string(self, in_str):
        # trim comments
        s = in_str.split('%')[0]

        # remove whitespace
        s =  "".join(s.split())       
        
        # blank lines are okay but they don't do anything
        if s == "" :
            return None
        else:
            return s
    
    def compile_term(self, term):
        # strip negate first
        negate = False
        if term[:4] == "not(":
            term = term[4:-1]
            negate = True

        # Compile from "pred(a,b,c)" string
        fields = term.split('(')
        if len(fields) != 2: 
            logging.error(f"Syntax error in term: {term}")

        pred = fields[0]
        args = [arg for arg in fields[1][:-1].split(',')]

        return negate, pred, args

    def compile_goals(self, text):
        disjunctive = False
        if ';' in text:
            disjunctive = True
            phrases = text.split(');')
        else:
            phrases = text.split('),')

        # put the closing parenthesis back
        for i in range(len(phrases)-1):
            phrases[i] += ')'

        terms = []
        for phrase in phrases:
            neg, pred, args = self.compile_term(phrase)
            terms.append(Term(neg, pred, args))

        return disjunctive, terms
        
    def parse_line(self, line):
        processed_rule = self._preprocess_string(line)
        if not processed_rule:
            return None # blank line: valid but skipped
        
        fields = processed_rule.split(":-")
        if len(fields) == 1:
            # this is an Axiom
            _, pred, args = self.compile_term(fields[0])
            return Axiom(pred, args)
        else:
            # this is a rule
            _, pred, args = self.compile_term(fields[0])
            head = Term(False, pred, args)
            disj, goals = self.compile_goals(fields[1])
            return Rule(disj, head, goals)
            
    
    def read_knowledge_file(self, filename):
        # check to make sure file exists
        if not path.isfile(filename):
            logging.error(f"{filename} doesn't exist.")
            return None

        # does it have a prolog extension?
        if not path.splitext(filename)[-1] == '.pl':
            logging.error(f"{filename} doesn't appear to be a prolog file.")
            return None

        with open(filename, 'r') as fp:
            for index, line in enumerate(fp):
                rule = self.parse_line(line)
                if rule:
                    self.knowledge.add_rule(rule)
                
        


def test():
    logging.basicConfig(level=logging.DEBUG)

    parser = Parser()
    # parser.read_knowledge_file("D:\\cognate\\negtest.pl")

    at = parser.parse_line('path(X,the_moon)')
    at.env = {'X': 'the_stars'}
    ax = Axiom.from_term_instance(at)
    print(ax)

if __name__ == "__main__" : test()
