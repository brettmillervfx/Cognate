import logging
from os import path
import copy
import yaml
import predicate
import knowledge


class Action:
    def __init__(self, action_name, variables, descriptive_statement):
        self.name = action_name
        self.variables = variables
        self.description = descriptive_statement
        self.preconditions = []
        self.add_effects = []
        self.delete_effects = []

    def add_precondition(self, precondition):
        self.preconditions.append(precondition)

    def add_add_effect(self, add_effect):
        self.add_effects.append(add_effect)

    def add_delete_effect(self, delete_effect):
        self.delete_effects.append(delete_effect)

    def get_instances(self, knowledge):
        solutions = knowledge.search(self.preconditions)
        #what about true? Can I provide an env?
        actions = []
        for solution in solutions:
            actions.append(ActionInstance(self, solution[0], solution[1]))
        return actions

    def __repr__(self):
        return self.description
        


class ActionInstance():
    def __init__(self, template, env, preconditions):
        self._env = env
        self.name = template.name
        self.description = self._desc_sub(template.description)
        self.preconditions = preconditions
        #self.add_effects = [self._collapse(add) for add in template.add_effects]
        self.add_effects = [copy.deepcopy(add).collapse(env) for add in template.add_effects]
        #self.delete_effects = [self._collapse(delete) for delete in template.delete_effects]
        self.delete_effects = [copy.deepcopy(delete).collapse(env) for delete in template.delete_effects]

    # def _collapse(self, rule):
    #     ret_rule = copy.deepcopy(rule)
    #     for var, val in self._env.items():
    #         for arg in ret_rule.args:
    #             arg.pred = arg.pred.replace(var,val)
    #     return ret_rule

    def _collapse_term(self, term):
        ret_term = copy.deepcopy(term)
        for var, val in self._env.items():
            for arg in ret_term.args:
                arg.pred = arg.pred.replace(var,val)
        return ret_term

    def _desc_sub(self, desc):
        ret_desc = copy.deepcopy(desc)
        for var, val in self._env.items():
            ret_desc = ret_desc.replace(var,val)
        return ret_desc

    def __repr__(self):
        return self.description

    def __hash__(self):
        return hash(self.description)
    
    def __eq__(self, other):
        return hash(self) == hash(other)



class ActionDB:
    def __init__(self):
        self._actions = []

    def add_action(self, action):
        self._actions.append(action)

    def get_possible_actions(self, knowledge):
        action_instances = []
        for action in self._actions:
            action_instances = action_instances + action.get_instances(knowledge)

        de_duped_actions = []
        [de_duped_actions.append(action) for action in action_instances if action not in de_duped_actions]

        return de_duped_actions


def read_action_file(filename):
    # check to make sure file exists
    if not path.isfile(filename):
        logging.error(f"{filename} doesn't exist.")
        return None

    # does it have a yaml extension?
    if not path.splitext(filename)[-1] == '.yml':
        logging.error(f"{filename} doesn't appear to be a yaml file.")
        return None

    parser = predicate.Parser()
    action_db = ActionDB()
    with open(filename, 'r') as fp:
        actions = yaml.load(fp, Loader=yaml.FullLoader)
        for a, body in actions.items():
            new_action = Action(a, body['variables'], body['desc'])
            if body['preconditions']:
                for prec in body['preconditions']:
                    neg, pred, args = parser.compile_term(prec)
                    new_action.add_precondition(predicate.Term(neg, pred, args))
            if body['adds']:
                for add in body['adds']:
                    add_term = parser.parse_line(add)
                    new_action.add_add_effect(add_term)
            if body['deletes']:
                for delete in body['deletes']:
                    delete_term = parser.parse_line(delete)
                    new_action.add_delete_effect(delete_term)
            action_db.add_action(new_action)

    return action_db




def test():
    logging.basicConfig(level=logging.DEBUG)

    adb = read_action_file("D:\\cognate\\EscapeRoom.yml")
    parser = predicate.Parser()
    parser.read_knowledge_file("D:\\cognate\\EscapeRoom.pl")
    k = parser.knowledge

    # t = parser.parse_line('at(closet_door,by_the_closet)')
    # print('T ->' + str(k.axiom_db.test_axiom(t)))
    _,t = parser.compile_goals('at(closet_door,by_the_closet)')
    print(k.search(t))
    
    viables = adb.get_possible_actions(k)
    for v in viables:
        print(v.description)

if __name__ == "__main__" : test()   
