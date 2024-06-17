from .client import Client
from .game import GameState
from .protocol import build_game_update, GAME_UPDATE_ALL

from asyncio import sleep
from typing import Set, List
from functools import partial
from websockets import broadcast, serve

class Server:
    def __init__(self, host: str, port: int, jwt_secret: str, tick_rate: float, player_ids: List[int]) -> None:
        self.host = host
        self.port = port
        self.jwt_secret = jwt_secret
        self.tick_interval = 1.0 / tick_rate
        self.player_ids = set(player_ids)
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
        # TODO: Keep the client connected and handle its messages
