from typing import Type, TypeVar, Generic, Any

from datastructs.command import Command, DirectCommand, CommandType
from datastructs.states import State
from networking.serializer import Serializer

T = TypeVar('T')
class Entry(Generic[T]):
    def __init__(self, message: str, data: T):
        self.message = message
        self.data = data

    @property
    def typename(self) -> str:
        return Serializer.type_to_name(type(self.data))

    def get_terminal_entry(target: str=None):
        command = Command(CommandType.EXIT) if target is None else DirectCommand(CommandType.EXIT, target)
        return Entry('terminate', command)

    def isTerminal(self, target: str=None):
        is_terminal_command = isinstance(self.data, Command) and self.data.type is CommandType.EXIT
        is_for_target = not isinstance(self.data, DirectCommand) or self.data.target == target
        return is_terminal_command and is_for_target
    
    def __str__(self) -> str:
        return f"({self.typename},{self.message},{self.data})"

class DataList:
    def __init__(self, headers:list[Entry]=None, content: list[Entry]=None):
        self.headers = headers or []
        self.content = content or []
    
    def add_headers(self, headers: list[Entry]):
        self.headers.extend(headers)

    def add_contents(self, content: list[Entry]):
        self.content.extend(content)

    def add_header(self, header: Entry):
        self.headers.append(header)

    def add_content(self, content: Entry):
        self.content.append(content)

    def get_state(self) -> State:
        entry = self.get_header_of_type(State)
        return entry.data if entry else State.unknown()
    
    def get_previous_state(self) -> State:
        entry: Entry[int] = self.get_header_by_message('previous state')
        return State(entry.data, True) if entry else State.unknown()
    
    def set_state(self, new_state: State):
        old = self.pop_header_of_type(State)
        self.pop_header_by_message('previous state')
        if old: self.add_header(Entry('previous state', old.data.id))
        self.add_header(Entry('current state', new_state))

    def set_previous_state(self, id: int):
        self.pop_header_by_message('previous state')
        self.add_header(Entry('previous state', id))
    
    def get_selected(self) -> list[str]:
        entry: Entry[str] = self.get_header_by_message('selected')
        if not entry: return []
        else: return entry.data.split(',')

    def set_selected(self, selected: list[str]):
        self.clear_selected()
        self.add_header(Entry('selected', ','.join(selected)))

    def clear_selected(self):
        self.pop_header_by_message('selected')
        
    def get_content_of_type(self, type: Type[T]) -> Entry[T]:
        return next((e for e in self.content if e.typename == Serializer.type_to_name(type)), None)
    
    def get_content_by_message(self, message: str):
        return next((e for e in self.content if e.message == message), None)
    
    def pop_content_of_type(self, type: Type[T]) -> Entry[T]:
        for e in self.content:
            if e.typename == Serializer.type_to_name(type):
                self.content.remove(e)
                return e
        return None
    
    def pop_content_by_message(self, *messages: str) -> Entry:
        for e in self.content:
            for m in messages:
                if e.message == m:
                    self.content.remove(e)
                    return e
        return None
    
    def pop_content_get_data_by_message(self, message: str) -> Any:
        entry = self.pop_content_by_message(message)
        return entry.data if entry else None
    
    def pop_content_to_tuple_by_messages(self, *messages: str) -> tuple:
        return tuple([self.pop_content_get_data_by_message(m) for m in messages])
    
    def get_header_of_type(self, type: Type[T]) -> Entry[T]:
        return next((e for e in self.headers if e.typename == Serializer.type_to_name(type)), None)
    
    def get_header_by_message(self, message: str):
        return next((e for e in self.headers if e.message == message), None)
    
    def pop_header_of_type(self, type: Type[T]) -> Entry[T]:
        for e in self.headers:
            if e.typename == Serializer.type_to_name(type):
                self.headers.remove(e)
                return e
        return None
    
    def pop_header_by_message(self, message: str) -> Entry:
        for e in self.headers:
            if e.message == message:
                self.headers.remove(e)
                return e
        return None
    
    
    def get_terminal(targets: list[str] = None):
        return DataList(headers=[Entry.get_terminal_entry(t) for t in (targets or [None])])
    
    def has_terminal_command_for(self, target: str = None):
        return any(e.isTerminal(target) for e in self.headers)
    
    def shallow_copy(self, new_state=None, clear_selected=False, new_contents=[]):
        copy = DataList(headers=self.headers[:], content=self.content[:])
        if new_state: copy.set_state(new_state)
        if clear_selected: copy.clear_selected()
        if new_contents: copy.add_contents(new_contents)
        return copy

    def __str__(self) -> str:
        return f"{list(map(str, self.headers))}{list(map(str, self.content))}"