from struct import pack
from typing import Optional
from game import GameState, GameUpdateFlag

GAME_UPDATE_ALL = GameUpdateFlag.Empty
for flag in GameUpdateFlag:
    GAME_UPDATE_ALL |= flag

def build_game_update(game: GameState, flags: Optional[GameUpdateFlag] = None) -> Optional[bytes]:
    # If no custom flags are provided, use the game state's update flags
    if flags == None:
        flags = game.update_flags
    # Do not build a packet when there is no update
    if flags == GameUpdateFlag.Empty:
        return None
    # Build a packet with the values required by the update flags
    packet = bytearray(pack('<B', flags.value))
    if flags & GameUpdateFlag.Phase:
        packet.extend(pack('<B', game.phase.value))
    if flags & GameUpdateFlag.BallPosition:
        packet.extend(pack('<f', game.ball.position_x))
        packet.extend(pack('<f', game.ball.position_y))
    if flags & GameUpdateFlag.PaddleScoreA:
        packet.extend(pack('<B', game.paddle_a.score))
    if flags & GameUpdateFlag.PaddleScoreB:
        packet.extend(pack('<B', game.paddle_b.score))
    if flags & GameUpdateFlag.PaddlePositionA:
        packet.extend(pack('<f', game.paddle_a.position))
    if flags & GameUpdateFlag.PaddlePositionB:
        packet.extend(pack('<f', game.paddle_b.position))
    return packet
