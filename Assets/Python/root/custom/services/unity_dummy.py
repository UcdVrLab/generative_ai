from typing import Any
from processing.streams import QueueStream

from datastructs.datalist import DataList, Entry
from processing.services import Transformation,Producer,Consumer
from processing.processor import SpecialAction

class SendPrompt(Producer):
    def __init__(self, name: str, input: QueueStream):
        super().__init__(name, input)
        self.count = 0

    def process(self, t: Any) -> DataList:
        if self.count > 0: 
            self.terminate()
            return SpecialAction.NOTHING
        self.count += 1 
        return DataList(content=[Entry("prompt", "Draw something")])
    
class SetTexture(Transformation):
    def process(self, dl: DataList) -> None:
        print(f"Set a texture to {dl.pop_content_by_message('image')}")
        return DataList.get_terminal()