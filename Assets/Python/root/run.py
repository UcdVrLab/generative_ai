import argparse

import custom.serializers.default as default
from networking.config_estab import share_services_with_peers, find_used_services
from networking.peers import generate_P2P_connections
from networking.serializer import Serializer
from util.file_resolver import file_from_ancestor
from util.json_helper import read_json_file
from util.physical_graph import PhysicalNetwork
from processing.handler import Handler
from datastructs.states import StateGraph

parser = argparse.ArgumentParser("Python peer for the network")
parser.add_argument("name", help="What the python handler should assume the role of in the physical network", type=str)
parser.add_argument('-p', '--physical', type=str, help="Where the peer should look for the physical config file")
parser.add_argument('-v', '--virtual', type=str, help="Where the peer should look for the virtual config file")
args = parser.parse_args()

physical_network = read_json_file(file_from_ancestor(f"Config/physical/{args.physical}.json"))
virtual_network = read_json_file(file_from_ancestor(f"Config/virtual/{args.virtual}.json"))

StateGraph.from_virtual(virtual_network).save_plot(file_from_ancestor('outputs/virtual_graph.png', ancestor_name="root"))
PhysicalNetwork.from_physical(physical_network).save_plot(file_from_ancestor('outputs/physical_graph.png', ancestor_name="root"))

Serializer.load_serializers_from_module(default)
main, peers = generate_P2P_connections(args.name, physical_network)
print("importing")
for p in main.packages: p.import_package()
print("finished imported")
share_services_with_peers(main, peers)
print("Local Services that are available")
print(main.services)
print("Remote Services that are available")
for p in peers: print(p.services)
main.set_used_services(find_used_services(main, peers, virtual_network))
handler = Handler(main, peers, StateGraph.from_virtual(virtual_network))
print("Setup finished")
handler.start()