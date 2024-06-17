from .client import Client
from .game import GameState, GamePhase, PaddleState
from .protocol import build_game_update, GAME_UPDATE_ALL

from asyncio import sleep
from functools import partial
from typing import Set, List, Tuple
from websockets import WebSocketException, broadcast, serve

class Server:
    def __init__(self, host: str, port: int, jwt_secret: str, tick_rate: float, player_ids: List[int]) -> None:
        self.host = host
        self.port = port
        self.jwt_secret = jwt_secret
        self.tick_interval = 1.0 / tick_rate
        self.player_ids = set(player_ids)
        self.waiting_ids = set(player_ids)
        self.player_order = player_ids
        self.game_state = GameState()
        self.clients: Set[Client] = set()

    async def main_loop(self) -> None:
        async with serve(self.handle_client, self.host, self.port, create_protocol=partial(Client, self)):
            # Simulate a game tick, broadcast a partial update and wait for the next tick
            while True:
                self.game_state.tick(self.tick_interval)
                broadcast(self.clients, build_game_update(self.game_state))
                await sleep(self.tick_interval)

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
                pass
        except WebSocketException:
            # Ignore WebSocket-related exceptions and drop the client
            pass
        finally:
            self.clients.discard(client)

    def get_client_paddles(self, client: 'Client') -> List['PaddleState']:
        paddles = []
        for user_id in client.user_ids:
            if user_id in self.player_ids:
                match self.player_order.index(user_id):
                    case 0: paddles.append(self.game_state.paddle_a)
                    case 1: paddles.append(self.game_state.paddle_b)
        return paddles
