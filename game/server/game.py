from enum import Enum, Flag
from typing import Optional
from math import cos, sin, pi
from dataclasses import dataclass
from random import random, randint

# Constants for establishing world bounds
WORLD_SIZE = 40.0
WORLD_ASPECT = 4.0 / 3.0
WORLD_X_SIZE = WORLD_SIZE * WORLD_ASPECT
WORLD_Y_SIZE = WORLD_SIZE
WORLD_X_EDGE = WORLD_X_SIZE / 2.0
WORLD_Y_EDGE = WORLD_Y_SIZE / 2.0

class GamePhase(Enum):
    Waiting = 0
    Playing = 1
    Intermission = 2
    Finished = 3

class GameUpdateFlag(Flag):
    Empty = 0
    Phase = 1 << 0
    BallPosition = 1 << 1
    PaddleScoreA = 1 << 2
    PaddleScoreB = 1 << 3
    PaddlePositionA = 1 << 4
    PaddlePositionB = 1 << 5
    ForceBallPosition = 1 << 6

@dataclass
class GameState:
    WINNING_SCORE = 11
    WAITING_TIMEOUT = 30.0
    INTERMISSION_TIMEOUT = 1.5

    phase: 'GamePhase'
    ball: 'BallState'
    paddle_a: 'PaddleState'
    paddle_b: 'PaddleState'
    update_flags: 'GameUpdateFlag'
    next_update_flags: 'GameUpdateFlag'
    timeout: float
    winning_side: int

    def __init__(self) -> None:
        self.phase = GamePhase.Waiting
        self.ball = BallState()
        self.paddle_a = PaddleState(-WORLD_X_EDGE + 1.0)
        self.paddle_b = PaddleState( WORLD_X_EDGE - 1.0)
        self.update_flags = GameUpdateFlag.Empty
        self.next_update_flags = GameUpdateFlag.Empty
        self.timeout = GameState.WAITING_TIMEOUT
        self.winning_side = -1

    def tick(self, delta_time: float) -> None:
        self.update_flags = self.next_update_flags
        self.next_update_flags = GameUpdateFlag.Empty
        # Always keep the paddles moving
        if self.paddle_a.tick(delta_time):
            self.update_flags |= GameUpdateFlag.PaddlePositionA
        if self.paddle_b.tick(delta_time):
            self.update_flags |= GameUpdateFlag.PaddlePositionB
        match self.phase:
            case GamePhase.Waiting:
                # Wait for the game to start for the configured timeout or finish
                # it prematurely
                self.timeout -= delta_time
                if self.timeout <= 0.0:
                    self.phase = GamePhase.Finished
                    self.update_flags |= GameUpdateFlag.Phase
            case GamePhase.Playing:
                # Simulate the ball and check if a goal was scored
                self.ball.tick(delta_time, self.paddle_a, self.paddle_b)
                self.update_flags |= GameUpdateFlag.BallPosition
                if (side := self.ball.check_goal()) != None:
                    match side:
                        case 0:
                            self.paddle_a.score += 1
                            self.update_flags |= GameUpdateFlag.PaddleScoreA
                        case 1:
                            self.paddle_b.score += 1
                            self.update_flags |= GameUpdateFlag.PaddleScoreB
                    # Reset the ball position and switch into intermission phase
                    self.ball.reset(side)
                    self.phase = GamePhase.Intermission
                    self.timeout = GameState.INTERMISSION_TIMEOUT
                    self.update_flags |= GameUpdateFlag.ForceBallPosition | GameUpdateFlag.Phase
            case GamePhase.Intermission:
                # Wait for the intermission timeout to expire, then switch phase
                self.timeout -= delta_time
                if self.timeout <= 0.0:
                    if self.paddle_a.score >= GameState.WINNING_SCORE or self.paddle_b.score >= GameState.WINNING_SCORE:
                        self.phase = GamePhase.Finished
                        self.winning_side = 0 if self.paddle_a.score > self.paddle_b.score else 1
                    else:
                        self.phase = GamePhase.Playing
                    self.update_flags |= GameUpdateFlag.Phase
            case GamePhase.Finished:
                pass

    def start(self) -> None:
        if self.phase == GamePhase.Waiting:
            # Start the game in intermission phase with the regular timeout
            self.phase = GamePhase.Intermission
            self.timeout = GameState.INTERMISSION_TIMEOUT
            self.next_update_flags |= GameUpdateFlag.Phase

@dataclass
class BallState:
    SPEED = 32.0
    SPIN_INCREASE = 1.5
    SPIN_DECREASE = 0.5
    SPIN_CLAMP_MIN = 0.2
    SPIN_CLAMP_MAX = 1.1
    RANDOM_OFFSET_MIN = 0.35

    position_x: float
    position_y: float
    velocity_x: float
    velocity_y: float
    last_position_x: float
    last_position_y: float

    def __init__(self) -> None:
        self.reset()
        self.last_position_x = 0.0
        self.last_position_y = 0.0

    def tick(self, delta_time: float, paddle_a: 'PaddleState', paddle_b: 'PaddleState') -> None:
        # Keep track of the last position
        self.last_position_x = self.position_x
        self.last_position_y = self.position_y
        # Apply horizontal motion and collide with the paddles
        self.position_x += self.velocity_x * BallState.SPEED * delta_time
        if self.velocity_x < 0.0 and paddle_a.collide_with_ball(self):
            self.position_x = self.last_position_x
            self.velocity_x = -self.velocity_x
            self.handle_spin(paddle_a)
        if self.velocity_x > 0.0 and paddle_b.collide_with_ball(self):
            self.position_x = self.last_position_x
            self.velocity_x = -self.velocity_x
            self.handle_spin(paddle_b)
        # Apply vertical motion and collide with the ceiling and floor
        self.position_y += self.velocity_y * BallState.SPEED * delta_time
        if self.position_y < -WORLD_Y_EDGE:
            self.position_y = -WORLD_Y_EDGE
            self.velocity_y = -self.velocity_y
        if self.position_y > WORLD_Y_EDGE:
            self.position_y = WORLD_Y_EDGE
            self.velocity_y = -self.velocity_y

    def reset(self, side: Optional[int] = None) -> None:
        self.position_x = 0.0
        self.position_y = 0.0
        # Choose a side and its corresponding angle
        if side != 0 and side != 1:
            side = randint(0, 1)
        match side:
            case 0: angle = 0
            case 1: angle = pi
        # Slightly randomize the angle and calculate the velocity
        offset = random() * 1.5 - 0.75
        if offset < 0.0 and offset > -BallState.RANDOM_OFFSET_MIN:
            offset = -BallState.RANDOM_OFFSET_MIN
        if offset >= 0.0 and offset < BallState.RANDOM_OFFSET_MIN:
            offset = BallState.RANDOM_OFFSET_MIN
        angle += offset
        # Set the velocity vector, also resetting the accumulated spin
        # which is the vector's magnitude
        self.velocity_x = cos(angle)
        self.velocity_y = sin(angle)

    def check_goal(self) -> Optional[int]:
        # If a goal line was passed, return the scoring side's index
        if self.position_x < -WORLD_X_EDGE - 8.0:
            return 1
        if self.position_x > WORLD_X_EDGE + 8.0:
            return 0
        return None

    def handle_spin(self, paddle: 'PaddleState') -> None:
        # Increase or decrease spin depending on paddle direction
        if paddle.direction < 0:
            if self.velocity_y < 0:
                self.velocity_y *= BallState.SPIN_DECREASE
            else:
                self.velocity_y *= BallState.SPIN_INCREASE
        if paddle.direction > 0:
            if self.velocity_y > 0:
                self.velocity_y *= BallState.SPIN_DECREASE
            else:
                self.velocity_y *= BallState.SPIN_INCREASE
        # Clamp the vertical velocity affected by spin
        sign = -1 if (self.velocity_y < 0) else 1
        value = abs(self.velocity_y)
        if value <= BallState.SPIN_CLAMP_MIN:
            self.velocity_y = sign * BallState.SPIN_CLAMP_MIN
        if value >= BallState.SPIN_CLAMP_MAX:
            self.velocity_y = sign * BallState.SPIN_CLAMP_MAX

@dataclass
class PaddleState:
    SPEED = 28.0
    LENGTH = 8.0
    HALF_LENGTH = LENGTH / 2.0
    GRACE_WINDOW = 0.5

    edge: float
    score: int
    position: float
    direction: int

    def __init__(self, edge: float) -> None:
        self.edge = edge
        self.score = 0
        self.position = 0
        self.direction = 0

    def tick(self, delta_time: float) -> bool:
        # Move according to the direction, clamping at the world edges
        self.position += self.direction * PaddleState.SPEED * delta_time
        if self.position < -WORLD_Y_EDGE + PaddleState.HALF_LENGTH:
            self.position = -WORLD_Y_EDGE + PaddleState.HALF_LENGTH
        if self.position > WORLD_Y_EDGE - PaddleState.HALF_LENGTH:
            self.position = WORLD_Y_EDGE - PaddleState.HALF_LENGTH
        return self.direction != 0

    def collide_with_ball(self, ball: 'BallState') -> bool:
        # The ball must have passed the paddle's edge position in this tick
        if (ball.last_position_x >= self.edge or ball.position_x < self.edge) and \
           (ball.last_position_x <= self.edge or ball.position_x > self.edge):
            return False
        # The ball must be on the same vertical level as the paddle or within the grace window
        if (ball.position_y < self.position - PaddleState.HALF_LENGTH - PaddleState.GRACE_WINDOW) or \
           (ball.position_y >= self.position + PaddleState.HALF_LENGTH + PaddleState.GRACE_WINDOW):
            return False
        return True
