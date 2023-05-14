from abc import ABC, abstractmethod
from typing import List


class AbstractCommandExecutor(ABC):

    @abstractmethod
    def execute_commands(self, commands: List[str]):
        """

        :param commands:
        :return:
        """
