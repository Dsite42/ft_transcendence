from .client import Client
from .notifier import AbstractNotifier
from .protocol import build_game_update, GAME_UPDATE_ALL
from .game import GameUpdateFlag, GameState, GamePhase, PaddleState

from asyncio import sleep
from ssl import SSLContext
from functools import partial
from typing import Optional, Set, List, Union
from websockets import WebSocketException, broadcast, serve

class Server:
    def __init__(self, host: str, port: int, jwt_secret: str, tick_rate: float, player_ids: List[int], notifier: AbstractNotifier, ssl_context: Optional[SSLContext]) -> None:
        self.host = host
        self.port = port
        self.jwt_secret = jwt_secret
        self.tick_interval = 1.0 / tick_rate
        self.player_ids = set(player_ids)
        self.waiting_ids = set(player_ids)
        self.player_order = player_ids
        self.notifier = notifier
        self.game_state = GameState()
        self.clients: Set[Client] = set()
        self.ssl_context = ssl_context

    async def main_loop(self) -> None:
        async with serve(self.handle_client, self.host, self.port, create_protocol=partial(Client, self), ssl=self.ssl_context):
            self.notifier.notify_ready()
            # Simulate a game tick, broadcast a partial update and wait for the next tick
            while self.game_state.phase != GamePhase.Finished:
                self.game_state.tick(self.tick_interval)
                broadcast(self.clients, build_game_update(self.game_state))
                await sleep(self.tick_interval)
            # Report the game's final state
            match self.game_state.winning_side:
                case 0 | 1:
                    winner = self.player_order[self.game_state.winning_side]
                case _:
                    winner = -1
            self.notifier.notify_finished(
                winner,
                self.game_state.paddle_a.score,
                self.game_state.paddle_b.score
            )

    async def handle_client(self, client: 'Client') -> None:
        # Prevents a race-condition where multiple clients with the same user ID pass
        # the pre-connection authorization
        if client.is_already_connected():
            return
        self.clients.add(client)
        try:
            paddles = self.get_client_paddles(client)
            # Start the game when all players have connected once
            if self.game_state.phase == GamePhase.Waiting and len(paddles) > 0:
                for user_id in client.user_ids:
                    self.waiting_ids.discard(user_id)
                if len(self.waiting_ids) == 0:
                    self.game_state.start()
            # Send a full game update to synchronize the client and start processing its messages
            await client.send(build_game_update(self.game_state, GAME_UPDATE_ALL))
            async for message in client:
                self.handle_client_message(message, paddles)
        except WebSocketException:
            # Ignore WebSocket-related exceptions and drop the client
            pass
        finally:
            self.clients.discard(client)
            # Finish the game prematurely when all players have disconnected
            if len(self.clients) == 0 and len(self.waiting_ids) == 0:
                self.game_state.phase = GamePhase.Finished
                self.game_state.next_update_flags |= GameUpdateFlag.Phase

    def handle_client_message(self, message: Union[bytes, str], paddles: list['PaddleState']) -> None:
        if not isinstance(message, bytes) or len(message) != 1:
            raise ValueError('Invalid message')
        input_state = message[0]
        # Extract the bit-packed directions for all client-owned paddles
        for index, paddle in enumerate(paddles):
            paddle.direction = 0
            direction_bits = (input_state >> (index << 1)) & 3
            if direction_bits & 1: paddle.direction -= 1
            if direction_bits & 2: paddle.direction += 1

    def get_client_paddles(self, client: 'Client') -> List['PaddleState']:
        paddles = []
        for user_id in client.user_ids:
            if user_id in self.player_ids:
                match self.player_order.index(user_id):
                    case 0: paddles.append(self.game_state.paddle_a)
                    case 1: paddles.append(self.game_state.paddle_b)
        return paddles
