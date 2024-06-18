import networkx as nx
from networkx import DiGraph
import matplotlib.pyplot as plt
from collections import defaultdict

from util.json_helper import read_json_file

class State:
    def __init__(self, id: int, complete: bool=False):
        self.id = id
        self.complete = complete

    #Selected an invalid direction when path split
    def lost():
        return State(-1, True)
    #Didn't select a direction when path split
    def confused():
        return State(-2, True)
    #Selected a service that doesn't exist
    def error():
        return State(-3, True)
    #State doesn't exist
    def unknown():
        return State(-4, True)
    #state was made without unknown parents
    def orphan():
        return State(-5, True)
    
    def is_valid(self):
        return self.is_real() or self.id == -5
    
    def is_real(self):
        return self.id >= 0
    
    def __str__(self) -> str:
        return f"({self.id},{self.complete})"

class StateGraph(DiGraph):
    def from_virtual(virtual_network):
        G = StateGraph()
        for s in virtual_network["nodes"]:
            G.add_node(s['id'], label=s['name'], default=s['default'] if 'default' in s else False)
        for c in virtual_network["edges"]:
            G.add_edge(c['a'], c['b'], label=c['type'], group=c['group'] if 'group' in c else None)
        return G
    
    def to_json(G, file_name: str):
        raise NotImplementedError("Function not implemented")
    
    def save_plot(G, file_name: str):
        pos = nx.spring_layout(G)  # You can choose a different layout if needed
        labels = {node: data['label'] for node, data in G.nodes(data=True)}
        edge_labels = {(u, v): data['label'] for u,v, data in G.edges(data=True)}
        plt.figure()
        nx.draw(G, pos, with_labels=True, labels=labels, node_size=1000, node_color='skyblue', font_size=8, font_color='black', font_weight='bold', arrowsize=20)
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color='red')

        plt.savefig(file_name)

    def get_sources(G):
        return [n for n in G.nodes() if G.in_degree(n) == 0]
    
    def get_consumers(G):
        return [n for n in G.nodes() if G.in_degree(n) > 0]

class Cycle:
    def __init__(self, values: list[int]) -> None:
        self.length = len(values)
        self.values = values
        self.cur = 0

    def incr(self):
        self.cur += 1
        if self.cur >= self.length:
            self.cur = 0

    def get(self, incr=True) -> int:
        v = self.values[self.cur]
        if incr: self.incr()
        return v

class StateRules:
    def __init__(self, graph: StateGraph) -> None:
        self.graph = graph
        self.producer_cycles = self.generate_prod_cycles()

    def generate_prod_cycles(self) -> dict[str, Cycle]:
        producers = [(n, self.graph.nodes[n]['label']) for n in self.graph.get_sources()]
        id_dict = defaultdict(list)
        for id, name in producers: id_dict[name].append(id)
        return {n: Cycle(ids) for n,ids in id_dict.items()}

    def assign(self, producer: str) -> State:
        if not producer: return State.orphan()
        return State(self.producer_cycles[producer].get(), True)

    def update(self, state: State, selected: str = None, default_allowed: bool = False) -> State:
        if not state.complete: return state
        G = self.graph
        if not state.is_valid(): return State.error()
        if not state.is_real():
            if not default_allowed: return State.error()
            for n in G:
                if G.nodes[n]['label'] == selected and G.nodes[n]['default']:
                    return State(n)
        neighbours = G.neighbors(state.id)
        if G.degree(state.id) == 1: 
            return State(next(neighbours, None))
        if selected is None:
            return State.confused()
        for n in neighbours:
            if G.nodes[n]['label'] == selected: 
                return State(n)
        if default_allowed:
            for n in G:
                if G.nodes[n]['label'] == selected and G.nodes[n]['default']:
                    return State(n)
        return State.lost()
    
    def get_current_service(self, state: State) -> str:
        if not state.is_real(): return None
        return self.graph.nodes[state.id]['label']

    def get_potential_services(self, state: State) -> list[str]:
        if not state.is_real(): return []
        G = self.graph
        return [G.nodes[n]['label'] for n in G.neighbors(state.id)]
    
    def get_default_services(self) -> list[str]:
        G = self.graph
        return [G.nodes[n]['label'] for n in G if G.nodes[n]['default']]
    
    def generate_confluence_dict(self) -> dict[str,dict[int,list[list[int]]]]:
        G = self.graph
        node_to_groups = defaultdict(list)
        
        for u, v, data in G.edges(data=True):
            for l in node_to_groups[v]:
                for n in l:
                    other_group = G.edges[n, v]['group']
                    if other_group and other_group == data.get('group'):
                        l.append(u)
                        break
                else: continue
                break
            else: node_to_groups[v].append([u])
        print([(G.nodes[n]['label'], n) for n in G.get_consumers()])
        cd = defaultdict(dict)
        for n in G.get_consumers(): cd[G.nodes[n]['label']][n] = node_to_groups[n]
        return cd






