from typing import Callable
from dataclasses import dataclass

@dataclass
class GameServerSettings:
    port: int
    jwt_secret: str
    player_a_id: int
    player_b_id: int

class GameServer:
    def __init__(self, game_id: int, settings: GameServerSettings, on_state_update: Callable[['GameServer'], None]) -> None:
        self.game_id = game_id
        self.settings = settings
        self.on_state_update = on_state_update
