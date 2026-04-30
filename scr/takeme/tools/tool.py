from abc import ABC, abstractmethod

class Tool(ABC):
    """
    工具类
    """

    name: str
    description: str

    @abstractmethod
    def execute(self, arguments: dict[str, any]) -> str:
        """
        执行工具
        """
        pass
    
    @property
    @abstractmethod
    def schema(self) -> dict:
        """
        工具模式
        """
        pass
