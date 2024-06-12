import importlib
import inspect
from types import ModuleType

class Package():
    def __init__(self, name: str) -> None:
        self.name = name
        
    def import_package(self):
        self.package = importlib.import_module(f"custom.services.{self.name}")
        
    def get_all_of_class(self, cls: ModuleType):
        members = inspect.getmembers(self.package)
        return [obj.__name__ for _,obj in members if inspect.isclass(obj) and issubclass(obj.__base__, cls)] 

class Self():
    def __init__(self, my_name: str, packages: list[Package]):
        self.my_name = my_name
        self.packages = packages

    def set_services(self, services: list[str]):
        self.services = services

    def set_used_services(self, used: list[str]):
        self.used_services = used