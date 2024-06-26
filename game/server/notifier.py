from struct import pack
from typing import BinaryIO
from os import fdopen, close
from abc import ABC, abstractmethod

class AbstractNotifier(ABC):
    def notify_ready(self) -> None:
        self.send_message('ready')

    def notify_finished(self, winner: int, score_a: int, score_b: int) -> None:
        self.send_message(f'finished:{winner}:{score_a}:{score_b}')

    @abstractmethod
    def send_message(self, message: str) -> None: ...

class NullNotifier(AbstractNotifier):
    def send_message(self, _: str) -> None:
        pass

class FileNotifier(AbstractNotifier):
    def __init__(self, file: BinaryIO) -> None:
        self.file = file

    def send_message(self, string: str) -> None:
        # Write the message as a length-prefixed UTF-8 string
        string = string.encode('utf-8')
        self.file.write(pack('<H', len(string)))
        self.file.write(string)
        self.file.flush()

    @staticmethod
    def from_raw_fd(raw_fd: int) -> 'FileNotifier':
        try:
            file = fdopen(raw_fd, 'wb')
            raw_fd = -1
        finally:
            # Make sure the file descriptor is not leaked when fdopen() raises an exception
            if raw_fd != -1:
                close(raw_fd)
        return FileNotifier(file)
