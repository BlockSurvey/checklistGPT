from abc import ABC, abstractmethod

# Define the interface


class DocumentLoaderInterface(ABC):

    @abstractmethod
    def get_text(self) -> str:
        pass
