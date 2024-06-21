from subprocess import Popen
from os import fdopen, close, pipe

class GameServer:
    def __init__(self, port: int, jwt_secret: str, game_id: int, player_a_id: int, player_b_id: int) -> None:
        self.port = port
        self.game_id = game_id
        read_end, write_end = pipe()
        try:
            # Wrap the pipe's read end in a GC'd file object, setting the raw
            # descriptor to -1 when successful
            self.notifier = fdopen(read_end, 'rb')
            read_end = -1
            self.process = Popen(
                ['python3', '-m', 'server',
                 '-p', str(port),
                 '-j', jwt_secret,
                 '-I', str(player_a_id), str(player_b_id),
                 '-n', str(write_end)],
                pass_fds=(write_end, )
            )
        finally:
            # Prevent leaking file descriptors on exception
            if read_end != -1:
                close(read_end)
            close(write_end)

    def kill(self) -> None:
        try:
            if self.process != None:
                self.process.kill()
                self.process = None
        except Exception:
            pass

    def __del__(self) -> None:
        # hasattr() is required here since __del__() is also called when
        # __init__() raises an exception as early as a failed argument
        # count check
        if hasattr(self, 'process'):
            self.kill()
