from typing import Generic, TypeVar, Any, Callable
from queue import Queue

from networking.peers import Peer
from datastructs.datalist import DataList

T = TypeVar('T')
class Input(Generic[T]):
    def input(self, t:T): pass
class Output(Generic[T]):
    def output(self) -> T: pass

class Stream(Input[T], Output[T]):
    pass

SingleLabelList = list[tuple[DataList,str]]
MultiLabelList = list[tuple[DataList,list[str]]]

#routes datalists to different inputs
class Delta(Input[SingleLabelList]):
    def __init__(self, name_to_input: Callable[[str], Input[DataList]]):
        self.name_to_input = name_to_input

    def input(self, sll: SingleLabelList):
        for dl, sn in sll: 
            input = self.name_to_input(sn)
            if input: input.input(dl)

#Simple stream using a queue for datalists
class QueueStream(Stream[DataList]):
    def __init__(self, queue: Queue=None) -> None:
        self.queue = queue or Queue()

    def input(self, d: DataList): 
        self.queue.put(d)

    def output(self) -> DataList:
        return self.queue.get()
    
#Stream implementing a socket endpoint
class SocketStream(Stream[DataList]):
    def __init__(self, peer: Peer) -> None:
        self.peer = peer

    def input(self, d: DataList):
        if not self.peer.can_send(): return
        self.peer.send_datalist(d)

    def output(self) -> DataList:
        if self.peer.can_receive():
            return self.peer.receive_datalist()
        else: return None

#Stream for returning nothing important
class NullStream(Stream[Any]):
    def input(self, t: Any):
        pass

    def output(self) -> Any:
        return None
    
#takes a list of Datalists and labels them
class Rapid(Input[MultiLabelList], Output[DataList]):
    def __init__(self, queue: QueueStream=None) -> None:
        self.queue = queue or QueueStream()

    def input(self, mll: MultiLabelList):
        for dl, selected in mll:
            dl.set_selected(selected)
            self.queue.input(dl)

    def output(self) -> DataList:
        return self.queue.output()
    
Group = list[list[int]]
    
#Stream that takes in multiple values and only passes them on if they finish a group, groups can be different depending on when the service is encountered
class Confluence(QueueStream):
    def __init__(self, groups: dict[int, Group], queue: Queue = None) -> None:
        super().__init__(queue)
        self.main_group_list_dict = groups
        self.input_state_group_dict = self.create_input_state_group_dict(groups)
        self.example_dict = {m: {s: None for g in G for s in g} for m,G in groups.items()}

    def create_input_state_group_dict(self, groups: dict[int, Group]):
        return {m: {s: i for i, g in enumerate(G) for s in g} for m,G in groups.items()}
    
    def dl_to_id(self, dl: DataList):
        return dl.get_previous_state().id
    def dl_to_group(self, dl: DataList):
        return self.input_state_group_dict[self.dl_to_main(dl)][self.dl_to_id(dl)]
    def dl_to_main(self, dl: DataList):
        return dl.get_state().id
    def dl_ids(self, dl: DataList):
        return (self.dl_to_id(dl), self.dl_to_main(dl), self.dl_to_group(dl))
    
    def get_group_examples(self) -> list[DataList]:
        return [self.example_dict[self.mid][s] for s in self.main_group_list_dict[self.mid][self.gid]]
    
    def group_satisfied(self):
        return all(self.get_group_examples())
    #merges several datalists into one
    def merge(self):
        examples = self.get_group_examples()
        merged_dl = DataList()
        merged_dl.set_state(examples[0].get_state())
        merged_dl.set_previous_state(self.gid) #only a gimmick
        for e in examples:
            merged_dl.add_contents(e.content)
            self.example_dict[self.mid][self.dl_to_id(e)] = None
        return merged_dl
    
    #inserts a datalist into its storage
    def insert_datalist(self, dl: DataList):
        was_empty = self.example_dict[self.mid][self.sid] is None
        self.example_dict[self.mid][self.sid] = dl
        return was_empty
    
    def input(self, dl: DataList):
        if not isinstance(dl, DataList): 
            super().input(dl)
            return
        self.sid, self.mid, self.gid = self.dl_ids(dl)
        was_empty = self.insert_datalist(dl)
        if not was_empty: return
        if self.group_satisfied():
            super().input(self.merge())