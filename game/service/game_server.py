from typing import Callable
from subprocess import Popen
from dataclasses import dataclass
from asyncio import get_event_loop
from os import close, pipe2, O_NONBLOCK

@dataclass
class GameServerSettings:
    port: int
    jwt_secret: str
    player_a_id: int
    player_b_id: int

class GameServerProcess:
    def __init__(self, settings: GameServerSettings, on_readable: Callable[[], None]) -> None:
        read_end, write_end = pipe2(O_NONBLOCK)
        try:
            self.fileno = read_end
            read_end = -1
            self.process = Popen(
                ['python3', '-m', 'server',
                 '-p', str(settings.port),
                 '-j', settings.jwt_secret,
                 '-I', str(settings.player_a_id), str(settings.player_b_id),
                 '-n', str(write_end)],
                pass_fds=(write_end, )
            )
        finally:
            # Prevents the file descriptors from being leaked in case of an exception
            try:
                close(write_end)
            finally:
                if read_end != -1:
                    close(read_end)
        # Register the given callback to be invoked when the pipe becomes readable
        self.loop = get_event_loop()
        self.loop.add_reader(self.fileno, on_readable)

    def __del__(self) -> None:
        # This method has to handle a partially initialized object when
        # __init__() raises an exception, hence the use of getattr()
        process = getattr(self, 'process', None)
        loop = getattr(self, 'loop', None)
        fileno = getattr(self, 'fileno')
        # The cascade of try-finally ensures that the cleanup process
        # is exception-safe and nothing is leaked
        try:
            if process != None:
                process.kill()
                process.wait()
        finally:
            if fileno == None:
                return
            try:
                if loop != None:
                    loop.remove_reader(self.fileno)
            finally:
                close(fileno)

class GameServer:
    def __init__(self, game_id: int, settings: GameServerSettings, on_state_update: Callable[['GameServer'], None]) -> None:
        self.game_id = game_id
        self.settings = settings
        self.on_state_update = on_state_update
