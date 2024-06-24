from struct import unpack
from typing import Callable
from subprocess import Popen
from dataclasses import dataclass
from asyncio import Future, get_event_loop
from os import close, pipe2, read, O_NONBLOCK

# Invoked when a game server's result has become available
FinishHandler = Callable[['GameServer', int, int, int], None]

# Invoked when a game server's process has quit and its port has become usable again
QuitHandler = Callable[['GameServer'], None]

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
    def __init__(self, game_id: int, settings: GameServerSettings, on_finished: FinishHandler, on_quit: QuitHandler) -> None:
        self.game_id = game_id
        self.settings = settings
        self.on_finished = on_finished
        self.on_quit = on_quit
        self.process = GameServerProcess(settings, self.on_process_readable)
        self.ready_future = Future()
        self.message_length = None
        self.message_buffer = bytearray()
        self.finish_reported = False

    def on_game_ready(self) -> None:
        if not self.ready_future.done():
            # The server has become ready, finish the future for the waiting task
            self.ready_future.set_result(None)

    def on_game_finished(self, winning_side: int, score_a: int, score_b: int) -> None:
        if not self.finish_reported:
            # Prevent a finished game from being reported multiple times
            self.finish_reported = True
            self.on_finished(self, winning_side, score_a, score_b)

    def on_process_quit(self) -> None:
        if not self.ready_future.done():
            # The server has quit before becoming ready, raise an exception for the waiting task
            self.ready_future.set_exception(Exception('Server has quit unexpectedly'))
        else:
            if not self.finish_reported:
                # Prevent a finished game from being reported multiple times
                self.finish_reported = True
                # The server has quit before reporting its score, so report a draw
                self.on_finished(self, -1, 0, 0)
            self.on_quit(self)

    def on_process_message(self, message: str) -> None:
        # Split the message into command and arguments
        message = message.split(':')
        arguments = message[1:]
        match message[0]:
            case 'ready':
                # Check and dispatch message to on_game_ready()
                if len(arguments) != 0:
                    raise TypeError(f'`ready` message takes 0 parameters, {len(arguments)} given')
                self.on_game_ready()
            case 'finished':
                # Check, parse and dispatch message to on_game_finished(int, int, int)
                if len(arguments) != 3:
                    raise TypeError(f'`finished` message takes 3 parameters, {len(arguments)} given')
                try:
                    arguments = map(int, arguments)
                except ValueError:
                    raise TypeError(f'`finished` message is malformed (int, int, int)')
                self.on_game_finished(*arguments)

    def on_process_readable(self) -> None:
        try:
            # Read as many bytes as possible until a BlockingIOError is thrown
            while self.process != None:
                data = read(self.process.fileno, 4096)
                if len(data) == 0:
                    # Break out when the pipe was closed
                    raise EOFError()
                self.on_process_data(data)
        except BlockingIOError:
            pass
        except Exception:
            # Release the server on any exception and raise a quit event
            self.process = None
            self.on_process_quit()

    def on_process_data(self, data: bytes) -> None:
        offset = 0
        while offset < len(data):
            # Consume up to the required number of bytes to complete the
            # current message's header or payload
            bytes_left = len(data) - offset
            bytes_required = 2 if (self.message_length == None) else self.message_length
            bytes_to_consume = min(bytes_required - len(self.message_buffer), bytes_left)
            self.message_buffer.extend(data[offset : offset + bytes_to_consume])
            offset += bytes_to_consume
            # If any part has been consumed, handle it appropriately
            if bytes_to_consume == bytes_required:
                if self.message_length == None:
                    # The header has been completed, causing the payload to be consumed next
                    self.message_length, = unpack('<H', self.message_buffer)
                    self.message_buffer.clear()
                else:
                    # The payload has been completed, invoke the handler method and prepare
                    # for the next message
                    try:
                        self.on_process_message(self.message_buffer.decode('utf-8'))
                    finally:
                        self.message_length = None
                        self.message_buffer.clear()
