import networkx as nx
from networkx import DiGraph
import matplotlib.pyplot as plt
import numpy as np
from itertools import permutations

class PhysicalNetwork(DiGraph):
    def from_physical(physical_network):
        G = PhysicalNetwork()
        G.peers = physical_network['nodes']
        for hobj in G.peers:
            h = hobj["name"]
            G.add_node(h, label=h)
            for pobj in G.peers:
                p = pobj["name"]
                if p == h: continue
                G.add_node(f"Sender({h}->{p})", label="Sender")
                G.add_node(f"Receiver({h}<-{p})", label="Receiver")
                G.add_edge(h, f"Sender({h}->{p})", label="Queue", weight=0.5)
                G.add_edge(f"Receiver({h}<-{p})",h, label="Queue", weight=0.5)

                G.add_edge(f"Sender({h}->{p})", f"Receiver({p}<-{h})", label="Socket", weight=5)
            for s in hobj['packages']:
                G.add_node(s, label=s)
                G.add_edge(h, s, label="Queue", weight=0.5)
                G.add_edge(s, h, label="Queue", weight=0.5)
        return G
    
    def to_json(G, file_name: str):
        raise NotImplementedError("Function not implemented")
    
    def save_plot(G, file_name: str):
        shells = [list(sum([(f"Sender({a['name']}->{b['name']})", f"Receiver({a['name']}<-{b['name']})") for a,b in permutations(G.peers, 2)], ())), [p['name'] for p in G.peers], [s for p in G.peers for s in p['packages']]]
        pos = nx.shell_layout(G, shells, rotate=0, scale=2)
        labels = {node: data['label'] for node, data in G.nodes(data=True)}
        edge_labels = {(u, v): data['label'] for u,v, data in G.edges(data=True)}
        plt.figure()
        nx.draw(G, pos, with_labels=True, labels=labels, node_size=600, node_color='skyblue', font_size=8, font_color='black', font_weight='bold', arrowsize=20)
        #nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color='red')
        
        plt.savefig(file_name)
