#!/usr/bin/env python3

# test_pygame.py: Runs the game using PyGame for game logic testing
#                 This is not part of actual project code, it will not be used at runtime

import os; os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
from time import time
from math import floor, ceil
from argparse import ArgumentParser
from game import (
    GameState,
    GamePhase,
    PaddleState,
    WORLD_SIZE,
    WORLD_ASPECT,
    WORLD_X_EDGE
)
import pygame

# Bit-packed font data for digits (0-9)
DIGIT_FONT = (
    0x0e9d72e, 0x0842988, 0x1f1322e, 0x0f83a0f,
    0x0847d4c, 0x0f83c3f, 0x0e8bc2e, 0x011111f,
    0x0e8ba2e, 0x0e87a2e
)

class PygameRunner:
    def __init__(self, width: int, height: int, tick_rate: int) -> None:
        self.surface = pygame.display.set_mode((width, height))
        pygame.display.set_caption('PygameRunner')
        self.font = pygame.font.Font(pygame.font.get_default_font(), 24)
        # Initialize input
        self.keys_held = set()
        # Initialize timing
        self.tick_interval = (1.0 / tick_rate)
        self.last_tick_time = time()
        # Initialize world-space to screen-space constants
        self.scale = height / WORLD_SIZE
        self.height = height
        self.clip_width = height * WORLD_ASPECT
        self.half_width = width / 2.0
        self.half_height = height / 2.0
        # Create a game state
        self.game_state = GameState()

    def game_loop(self) -> None:
        self.running = True
        while self.running:
            self.tick()
            self.draw()
            self.poll()

    def poll(self) -> None:
        for event in pygame.event.get():
            match event.type:
                case pygame.QUIT:
                    self.running = False
                case pygame.KEYUP:
                    self.keys_held.discard(event.key)
                case pygame.KEYDOWN:
                    if event.key == pygame.K_x:
                        self.game_state.start()
                    self.keys_held.add(event.key)

    def tick(self) -> None:
        # Limit the number of ticks to the configured tick rate
        current_time = time()
        delta_time = current_time - self.last_tick_time
        if delta_time >= self.tick_interval:
            self.last_tick_time = current_time
            # Set paddle directions based on input
            self.game_state.paddle_a.direction = 0
            self.game_state.paddle_b.direction = 0
            if pygame.K_w in self.keys_held: self.game_state.paddle_a.direction -= 1
            if pygame.K_s in self.keys_held: self.game_state.paddle_a.direction += 1
            if pygame.K_o in self.keys_held: self.game_state.paddle_b.direction -= 1
            if pygame.K_l in self.keys_held: self.game_state.paddle_b.direction += 1
            # Simulate a game tick
            self.game_state.tick(delta_time)

    def draw(self) -> None:
        # Fill the whole frame's background
        self.surface.set_clip()
        self.surface.fill((30, 30, 30))
        # Set world clipping and fill the world's background
        self.surface.set_clip((
            self.half_width - self.clip_width / 2.0,
            0,
            self.clip_width,
            self.height
        ))
        self.surface.fill((0, 0, 0))
        # Draw the dividing line
        for y in range(floor(WORLD_SIZE)):
            if (y % 6) == 0:
                self.fill_rect(-0.1, -3.0 - y - 1.0, 0.2, 1.0)
                self.fill_rect(-0.1,  3.0 + y,       0.2, 1.0)
        # Draw the ball and both paddles
        self.fill_rect(
            self.game_state.ball.position_x - 0.5,
            self.game_state.ball.position_y - 0.5,
            1.0, 1.0
        )
        self.fill_rect(
            -WORLD_X_EDGE,
            self.game_state.paddle_a.position - PaddleState.HALF_LENGTH,
            1.0,
            PaddleState.LENGTH
        )
        self.fill_rect(
            WORLD_X_EDGE - 1.0,
            self.game_state.paddle_b.position - PaddleState.HALF_LENGTH,
            1.0,
            PaddleState.LENGTH
        )
        # Draw scores if in intermission or finished phase
        if self.game_state.phase == GamePhase.Intermission or self.game_state.phase == GamePhase.Finished:
            self.draw_number(self.game_state.paddle_a.score, -WORLD_X_EDGE + 8.0, -3.75, 1.5, False)
            self.draw_number(self.game_state.paddle_b.score, WORLD_X_EDGE - 8.0, -3.75, 1.5, True)
        # Draw debug text
        self.surface.set_clip()
        if self.game_state.phase == GamePhase.Waiting or self.game_state.phase == GamePhase.Intermission:
            debug_phase = f'phase={self.game_state.phase} (timeout={self.game_state.timeout:0.2f})'
        else:
            debug_phase = f'phase={self.game_state.phase}'
        self.draw_text(debug_phase, 0, self.height - 24, (255, 255, 255))
        self.draw_text(f'update_flags={self.game_state.update_flags}', 0, self.height - 48, (255, 255, 0))
        if self.game_state.phase == GamePhase.Waiting:
            self.draw_text('>>> Press [X] to start game', 0, self.height - 72, (0, 255, 255))
        # Present the frame
        pygame.display.flip()

    def fill_rect(self, x: float, y: float, w: float, h: float) -> None:
        # Transform the rectangle from world-space to screen-space
        x = x * self.scale + self.half_width
        y = y * self.scale + self.half_height
        w *= self.scale
        h *= self.scale
        # If X or Y is negative, reduce W or H
        if x < 0:
            w += x
            x = 0
        if y < 0:
            h += y
            y = 0
        if w < 0: return
        if h < 0: return
        # Fill the transformed rectangle
        self.surface.fill((255, 255, 255), (floor(x), floor(y), ceil(w), ceil(h)))

    def draw_text(self, text: str, x: int, y: int, color: pygame.Color) -> None:
        self.surface.blit(self.font.render(text, True, color), (x, y))

    def draw_5x5_bitmap(self, bitmap: int, x: float, y: float, scale: float) -> None:
        # Draws a packed 1bpp 5x5 bitmap
        for offset_y in range(5):
            for offset_x in range(5):
                if bitmap & 1:
                    self.fill_rect(x + offset_x * scale, y + offset_y * scale, scale, scale)
                bitmap >>= 1

    def draw_number(self, number: int, x: float, y: float, scale: float, align_right: bool) -> None:
        # Make sure the number is a positive integer
        number = int(floor(number))
        if number < 0: number = 0
        # Collect all font bitmaps for the required digits
        bitmaps = []
        while True:
            bitmaps.append(DIGIT_FONT[number % 10])
            number //= 10
            # Break here to have at least one digit
            if number == 0:
                break
        # Calculate the initial offset and horizontal step
        x_step = 6.0 * scale
        if align_right:
            x_step = -x_step
            x -= 5.0 * scale
        else:
            bitmaps = reversed(bitmaps)
        # Draw the bitmaps in the required order
        for bitmap in bitmaps:
            self.draw_5x5_bitmap(bitmap, x, y, scale)
            x += x_step

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-W', '--width', type=int, default=1280)
    parser.add_argument('-H', '--height', type=int, default=720)
    parser.add_argument('-r', '--rate', type=float, default=60.0)
    arguments = parser.parse_args()
    pygame.init()
    PygameRunner(arguments.width, arguments.height, arguments.rate).game_loop()
