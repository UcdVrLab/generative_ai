import traceback
from threading import Thread
from typing import Generic, TypeVar, Any
from enum import IntEnum
import os

from processing.streams import Input, Output, Stream, SingleLabelList, MultiLabelList
from datastructs.datalist import DataList

class SpecialAction(IntEnum):
    NOTHING = 0
    TERMINATE = 1

T = TypeVar('T')
U = TypeVar('U')
class Processor(Generic[T, U]):
    def __init__(self, input: Input[U], output: Output[T]):
        self._thread = Thread(target=self.loop)
        self._terminated = False
        self._input = input 
        self._output = output
        self._threaded = True

    def process(self, t: T) -> U: 
        raise NotImplementedError("Process method was not implemented")

    def take(self) -> T: return self._output.output()
    def give(self, u: U): self._input.input(u)

    def on_exception(self, e: Exception):
        traceback.print_exc()
        os._exit(0)

    def should_terminate(self, a: Any) -> bool:
        return a is SpecialAction.TERMINATE
    
    def should_skip(self, a: Any) -> bool:
        return a is SpecialAction.NOTHING

    def loop(self):
        while True:
            try:   
                self.setup()
                break
            except Exception:
                print("Had an strange exception while setting up, trying again")
        while not self._terminated:
            try:
                item = self.take()
                if self.should_terminate(item):      
                    finish = self.terminate()              
                    if not finish: break
                p_item = self.process(item)             
                if self.should_skip(p_item): continue   
                self.give(p_item)
            except Exception as e:
                self.on_exception(e)
    
    def start(self):
        if self._threaded: self._thread.start()
        else: self.setup()

    def setup(self):
        pass

    def join(self, time) -> bool:
        if not self._threaded: return False
        self._thread.join(time)
        return self._thread.is_alive()

    def manual(self, t: T):
        if self._threaded: return
        self.give(self.process(t))

    def send_special(self, u: U):
        self.give(u)

    def terminate(self) -> bool: 
        self._terminated = True

    def external_terminate(self):
        if isinstance(self._output, Stream):
            self._output.input(SpecialAction.TERMINATE)

class NamedProcessor(Processor[T,U]):
    def __init__(self, name: str, input: Input[U], output: Output[T]):
        super().__init__(input, output)
        self.name = name

class DLInputter(NamedProcessor[DataList, U]):
    def should_terminate(self, dl: DataList) -> bool:
        if dl is None: return True
        return super().should_terminate(dl) or dl.has_terminal_command_for(self.name)
    
class DLOutputter(NamedProcessor[T, DataList]): pass
    
class DLProcessor(DLInputter[DataList]): 
    def process(self, dl: DataList) -> DataList:
        return dl
    
class RoutingDLProcessor(DLInputter[SingleLabelList]): pass
class LabellingDLProcessor(DLInputter[MultiLabelList]): pass