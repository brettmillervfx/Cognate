import sys
sys.path.append('D:\\projects')
import cognate.knowledge as cog

from enum import Enum


class Functor(Enum):
    PATH = 0
    DROP = 1
    TELEPORTABLE = 2
    DOWNSTAIRS = 3
    UPSTAIRS = 4
    OPEN_GATE = 5
    CLOSED_GATE = 6
    AT = 7
    TRIGGER = 8

class Path(cog.Fact):
    def __init__(self, node1, node2):
        self.functor = Functor.PATH
        self.arguments = (node1, node2) 

    def __repr__(self):
        return f"Path {self.arguments}" 

class Drop(cog.Fact):
    def __init__(self, node1, node2):
        self.functor = Functor.DROP
        self.arguments = (node1, node2)  

    def __repr__(self):
        return f"Drop {self.arguments}" 

class Teleportable(cog.Fact):
    def __init__(self, node1, node2):
        self.functor = Functor.TELEPORTABLE
        self.arguments = (node1, node2)

    def __repr__(self):
        return f"Teleportable {self.arguments}" 

class Downstairs(cog.Fact):
    def __init__(self, node1, node2):
        self.functor = Functor.DOWNSTAIRS
        self.arguments = (node1, node2)  

    def __repr__(self):
        return f"Downstairs {self.arguments}" 

class Upstairs(cog.Fact):
    def __init__(self, node1, node2):
        self.functor = Functor.UPSTAIRS
        self.arguments = (node1, node2) 

    def __repr__(self):
        return f"Upstairs {self.arguments}" 

class OpenGate(cog.Fact):
    def __init__(self, node1, node2):
        self.functor = Functor.OPEN_GATE
        self.arguments = (node1, node2) 

    def __repr__(self):
        return f"OpenGate {self.arguments}" 

class ClosedGate(cog.Fact):
    def __init__(self, node1, node2):
        self.functor = Functor.CLOSED_GATE
        self.arguments = (node1, node2) 

    def __repr__(self):
        return f"ClosedGate {self.arguments}" 

class At(cog.Fact):
    def __init__(self, agent, node):
        self.functor = Functor.AT
        self.arguments = (agent, node) 

    def __repr__(self):
        return f"At {self.arguments}" 

class Trigger(cog.Fact):
    def __init__(self, gate1, gate2, trigger_location):
        self.functor = Functor.TRIGGER
        self.arguments = (gate1, gate2, trigger_location) 

    def __repr__(self):
        return f"Trigger {self.arguments}" 
