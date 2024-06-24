from .aiorpc import AioRPC
from .game_server import GameServerSettings, GameServer

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
            settings = GameServerSettings(port, self.jwt_secret, player_a_id, player_b_id)
            server = GameServer(game_id, settings, self.on_server_finished, self.on_server_quit)
            await server.ready_future
            self.servers.add(server)
            return {
                'game_id': game_id,
                'game_address': f'{self.game_host}:{port}'
            }
        except Exception:
            # Prevent leaking the port on exception
            self.ports.add(port)
            return None

    def on_server_finished(self, server: GameServer, winning_side: int, score_a: int, score_b: int) -> None:
        print(f'on_server_finished({server=}, {winning_side=}, {score_a=}, {score_b=})')

    def on_server_quit(self, server: GameServer) -> None:
        print(f'on_server_quit({server=})')

    async def main_loop(self) -> None:
        async with AioRPC(self.rpc_host, 'game_service', self):
            await Future()
