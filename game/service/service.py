from .aiorpc import AioRPC
from .game_server import GameServer

from asyncio import Future
from typing import Optional
from tinyrpc.dispatch import public

class GameService:
    def __init__(self, rpc_host: str, game_host: str, ports: range, jwt_secret: str) -> None:
        self.rpc_host = rpc_host
        self.game_host = game_host
        self.ports = set(ports)
        self.jwt_secret = jwt_secret
        self.servers = set()

    @public
    async def create_game(self, game_id: int, player_a_id: int, player_b_id: int) -> Optional[dict]:
        # Attempt to allocate a port
        if len(self.ports) == 0:
            return None
        port = self.ports.pop()
        try:
            server = GameServer(port, self.jwt_secret, game_id, player_a_id, player_b_id)
            self.servers.add(server)
            # TODO: Wait for server to be ready and handle its events
            return {
                'game_id': game_id,
                'game_address': f'{self.game_host}:{port}'
            }
        except Exception:
            # Prevent leaking the port on exception
            self.ports.add(port)
            return None

    async def main_loop(self) -> None:
        async with AioRPC(self.rpc_host, 'game_service', self):
            await Future()
