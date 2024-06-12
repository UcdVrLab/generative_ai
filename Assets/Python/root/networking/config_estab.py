import re

from networking.peers import Peer,Self
from datastructs.datalist import DataList,Entry
from processing.services import Service

def share_services_with_peers(main: Self, peers: list[Peer]):
    services = [f"{p.name}.{s}" for p in main.packages for s in p.get_all_of_class(Service)]
    service_dl = DataList(content=[Entry('service', s) for s in services])
    main.set_services(services)
    for p in peers: p.send_datalist(service_dl)
    for p in peers: p.set_services([e.data for e in p.receive_datalist().content])

def find_used_services(main: Self, peers: list[Peer], virtual_network):
    required = [n['name'] for n in virtual_network['nodes']]
    possible = True
    try:
        match_list = match_services(main.services, [s for p in peers for s in p.services], required)
    except(AmbiguousServiceException, UnknownServiceException) as e:
        print(e)
        possible = False
    for p in peers: p.send_entry(Entry("possible", int(possible)))
    others_possible = all(map(lambda e: e.data if e else False, [p.receive_entry() for p in peers]))
    if (possible and others_possible):
        for (fn,_),n in zip(match_list, virtual_network['nodes']):
            n['name'] = fn
        return list(set([fn for fn,local in match_list if local]))
    else:
        print("Application virtual network is not possible... Terminating")
        exit()

class AmbiguousServiceException(Exception): pass
class UnknownServiceException(Exception): pass

def match_services(local: list[str], external: list[str], required: list[str]):
    local_matches = [[m for m in map(lambda p: re.match(rf"^(\w+\.)*{re.escape(s)}$", p), local) if m] for s in required]
    external_matches = [[m for m in map(lambda p: re.match(rf"^(\w+\.)*{re.escape(s)}$", p), external) if m] for s in required]
    match_list: list[tuple[str, bool]] = []
    for req,loc,ext in zip(required, local_matches, external_matches):
        if len(loc) + len(ext) == 0:
            raise UnknownServiceException(f"Couldn't find service '{req}' in either local or remote packages")
        elif len(loc) == 1:
            match_list.append((loc[0].group(0), True))
        elif len(ext) == 1:
            match_list.append((ext[0].group(0), False))
        else:
            raise AmbiguousServiceException(f"Couldn't disambiguate service '{req}' in either local or remote packages, please use a more specific identifier") 
    return match_list