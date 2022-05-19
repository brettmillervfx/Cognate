
'''
Agent has a part that lives on the ai thread and part that lives in the game thread.
We prefix with AI_ or GT_ for anything that must stay in one of the other.
Agent can think about what to do next (AI) or can actually do things or sense things (GT).
'''
class Behavior:
    def __init__(self):
        pass

class AgentNotify:
    def __init__(self):
        pass

class Agent:
    def __init__(self):
        pass

    def load(self, knowledge_base):
        # load agent specific knowledge
        # load agent specific actions and behaviors
        # load agent specific sensors and goals
        
    
    def gt_tick(self):
        pass
        # iterate notifications
        # execute current behavior

    def gt_register(self):
        # register agent with ai manager

        # generate a goal

        # queue up first request: give me a plan
        pass

