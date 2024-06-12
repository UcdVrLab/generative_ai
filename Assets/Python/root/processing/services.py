from datastructs.datalist import DataList, Entry
from processing.processor import NamedProcessor, DLProcessor, DLInputter, DLOutputter, LabellingDLProcessor, SpecialAction
from processing.streams import Input, Output, QueueStream, NullStream, SocketStream, T, MultiLabelList, Rapid
import re

class Service(NamedProcessor):
    @classmethod
    def make_name(cls,handler:str, name:str) -> str:
        return f"{cls.__name__}({handler}:{name})"
    
    def get_service_name(self) -> str:
        match = re.match(r"(.+?)\((.+?):(.+?)\)", self.name)
        return match.group(3) if match else None

    def create_special_dl(self, base_dl: DataList, entry: Entry, to: str=None):
        clone_dl = base_dl.shallow_copy()
        clone_dl.add_content(entry)
        if to: clone_dl.set_selected(clone_dl.get_selected() + [to])
        return clone_dl
    
class Transformation(DLProcessor, Service):
    def __init__(self, name: str, input: QueueStream, output: QueueStream):
        super().__init__(name, input, output)

class MultiTransformation(LabellingDLProcessor, Service):
    def __init__(self, name: str, input: Rapid, output: QueueStream):
        super().__init__(name, input, output)

class Consumer(DLInputter[None], Service):
    def __init__(self, name: str, output: QueueStream):
        super().__init__(name, NullStream(), output)

class Producer(DLOutputter[T], Service):
    def __init__(self, name: str, input: QueueStream):
        super().__init__(name, input, NullStream())
    
    def give(self, dl: DataList):
        if dl: dl.add_header(Entry('producer', self.get_service_name()))
        return super().give(dl)
    
    def external_terminate(self):
        self.terminate()
    
class Sender(DLProcessor):
    def __init__(self, input: SocketStream, output: QueueStream):
        super().__init__(Sender.make_name(*input.peer.names), input, output)
        self.peer = input.peer

    def request_termination(self):
        targets = [f"Handler({self.peer.peer_name})", Receiver.make_name(*self.peer.reversed_names)]
        self._output.input(DataList.get_terminal(targets))

    @classmethod
    def make_name(cls,A:str, B:str) -> str:
        return f"{cls.__name__}({A}->{B})"

class Receiver(DLProcessor):
    def __init__(self, input: QueueStream, output: SocketStream):
        super().__init__(Receiver.make_name(*output.peer.names), input, output)
        self.peer = output.peer

    @classmethod
    def make_name(cls, A:str, B:str) -> str:
        return f"{cls.__name__}({A}<-{B})"
    
    def terminate(self):
        super().terminate()
        return True
    
    def process(self, dl: DataList) -> DataList:
        if not dl: #Socket broke
            self.terminate()
            return SpecialAction.NOTHING
        return super().process(dl)