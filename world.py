from enum import Enum


class Agent:
    def __init__(self, name:str) -> None:
        self.name = name

class Exposure(Enum):
    NO_COVER = 0
    TOP_COVER = 1
    SIDE_COVER = 2
    HIDDEN = 3

class Node:
    def __init__(self, name: str) -> None:
        self.exposure = Exposure.NO_COVER
        self.name = name
        self.index = -1

        self.egress = {} # dict[node_name] = edge

    def set_index(self, index: int) -> None:
        self.index = index

class LinkType(Enum):
    TWO_WAY = 0
    ONE_WAY = 1
    DROP = 2
    TELEPORT = 3
    STAIRS_UP = 4       

class Edge:
    def __init__(
        self, 
        from_node: str, 
        to_node: str
    ):
        self.from_node = from_node
        self.to_node = to_node
        self.tight = False
        self.gate_open = None
        self.trigger_location = None
        self.index = -1

    def set_index(self, index: int) -> None:
        self.index = index

    def make_gate(self, open: bool, trigger_location: str) -> None
        self.gate_open = open
        self.trigger_location = trigger_location


class World:
    def __init__(self):
        self.nodes = []
        self.node_name_to_index = {} # dict[str] = int

        self.edges = []

        # layered state like knowledge has

    def add_node(self, name: str) -> Node:
        """ add node and return handle to it for configuration"""
        new_node = Node(name)
        node_index = len(self.nodes)
        new_node.set_index(node_index)
        self.nodes.append(new_node)
        self.node_name_to_index[name] = new_node
        return new_node

    def add_edge(self, from_node: str, to_node: str) -> Edge:
        """ add edge and return handle for configuration """
        new_edge = Edge(from_node, to_node)
        edge_index = len(self.edges)
        new_edge.set_index(edge_index)
        self.edges.append(new_edge)
        return new_edge


""" 
I need a way to query the world state -- what do such queries look like? Do we maintain predicate logic?
I need a way to layer overrides.
A query is posed to an override layer.
Which is a stack.

Is a query a lambda?


new_layer = override_stack.push()
query = Query([bandit_1.location.count_inhabitants(bandits)>2]) # Is my bandit in a room with at least 2 other bandits?
override_stack.pop()

And this in turn leads to questions about 
"""