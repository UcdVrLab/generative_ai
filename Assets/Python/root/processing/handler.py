from types import ModuleType
import os

from processing.services import Service, Sender, Receiver, Transformation, Consumer, Producer, MultiTransformation
from processing.streams import QueueStream, Delta, SocketStream, SingleLabelList, Rapid, Input, Confluence
from processing.processor import NamedProcessor, SpecialAction, RoutingDLProcessor
from networking.peers import Peer
from networking.self import Self
from datastructs.datalist import DataList, Entry
from datastructs.states import StateGraph, StateRules

class ServiceResolver():
    def __init__(self, services: list[Service], senders: list[Sender]):
        self.services = services
        self.senders = senders
        self.service_resolver_dict = self.create_dict()

    def create_dict(self) -> dict[str, tuple[Input[DataList], bool]]:
        return {s.get_service_name(): (s._output, True) for s in self.services} | {serv: (s._output, False) for s in self.senders for serv in s.peer.services}
    
    #returns the input where the service is found 
    def resolve(self, service_name: str):
        return self.service_resolver_dict[service_name][0]
    
    def local(self, service_name: str):
        return self.service_resolver_dict[service_name][1]

class Children:
    def __init__(self, senders: list[Sender], receivers: list[Receiver], services: list[Service]) -> None:
        self.senders = senders
        self.receivers = receivers
        self.services = services

    @property
    def all(self) -> list[NamedProcessor]: return self.senders + self.receivers + self.services

    def start(self):
        for p in self.all: p.start()

    def end(self):
        for s in self.senders: 
            s.request_termination()
            s.external_terminate()
        for s in self.services: s.external_terminate()
        #can't directly terminate receivers as they are blocking on sockets
        
    def join(self, time):
        return not any([p.join(time) for p in self.all])
    
    def setup(self):
        for s in self.services: s.setup()

def get_service_name(full: str):
    return full.split('.')[-1]

def get_package_name(full: str):
    return '.'.join(full.split('.')[:-1])
    
def generate_services(main: Self, handlerConfluence: QueueStream, confluence_dict: dict[str,dict[int,list[list[int]]]]) -> list[Service]:
    services = []
    for full in main.used_services:
        service_module = next(p.package for p in main.packages if p.name == get_package_name(full))
        service_class = getattr(service_module, get_service_name(full))
        stream = QueueStream() if full not in confluence_dict else Confluence(confluence_dict[full])
        if issubclass(service_class, MultiTransformation):
            services.append(service_class(full, Rapid(handlerConfluence), stream))
        elif issubclass(service_class, Transformation):
            services.append(service_class(full, handlerConfluence, stream))
        elif issubclass(service_class, Consumer):
            services.append(service_class(full, stream))
        elif issubclass(service_class, Producer):
            services.append(service_class(full, handlerConfluence))
        else:
            raise Exception(f"Service '{full}' is not an implemented type")
    return services

class Handler(RoutingDLProcessor):
    def __init__(self, main: Self, peers: list[Peer], state_graph: StateGraph):
        handlerConfluence = QueueStream()
        self.state_rules = StateRules(state_graph)
        confluence_dict = self.state_rules.generate_confluence_dict()
        services = generate_services(main, handlerConfluence, confluence_dict)
        for s in services: s.name = Service.make_name(main.my_name, s.name)
        socket_streams = [SocketStream(p) for p in peers]
        senders = [Sender(ss, QueueStream()) for ss in socket_streams]
        receivers = [Receiver(handlerConfluence, ss) for ss in socket_streams]
        self.service_resolver = ServiceResolver(services, senders)
        
        self.children = Children(senders, receivers, services)
        super().__init__(Handler.make_name(main.my_name), Delta(self.service_resolver.resolve), handlerConfluence)

    def terminate(self): 
        self.children.end()
        successful = self.children.join(time=2)
        super().terminate()
        if not successful:
            print("Failed to terminate all threads, forcefully exiting")
            os._exit(0)
        else:
            print("Successfully terminated all threads, peacefully exiting")

    def start(self):
        self.children.start()
        super().start()
    
    def presend(self, dl: DataList, service_name: str):
        dl.get_state().complete = self.service_resolver.local(service_name)
        return (dl, service_name)
                 
    #main logic
    def process(self, datalist: DataList) -> SingleLabelList:
        if not datalist: return SpecialAction.NOTHING
        print(f"{self.name} has received {datalist}")
        state = datalist.get_state()
        if not state.is_valid(): 
            producer = datalist.pop_header_by_message('producer')
            data = producer.data if producer else None
            state = self.state_rules.assign(data)
            datalist.set_state(state)
        sll = []
        if state.complete:
            selected = datalist.get_selected()
            possible = self.state_rules.get_potential_services(state)
            if selected == []: selected.extend(possible)
            if 'all' in selected: 
                selected.extend(possible)
                selected.remove('all')
            possible.extend(self.state_rules.get_default_services())
            for s in selected:
                s = next((p[0] for p in list(map(lambda fn: (fn, get_service_name(fn)), possible)) if p[1] == s or p[0] == s), "Unknown")
                new_state = self.state_rules.update(state, s, default_allowed=True)
                if new_state.is_valid(): #send
                    copy = datalist.shallow_copy(new_state=new_state, clear_selected=True)
                    sll.append(self.presend(copy, s))
                else:
                    print(f"State transition: {state}->{new_state} via {s} isn't valid")
        else:
            sll.append(self.presend(datalist, self.state_rules.get_current_service(state)))
        return sll

    @classmethod
    def make_name(cls,name: str) -> str:
        return f"{cls.__name__}({name})"