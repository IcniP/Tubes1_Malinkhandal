import random
from typing import Optional
from datetime import datetime
import os

from game.logic.base import BaseLogic
from game.models import GameObject, Board, Position
from game.util import get_direction

class GreedyBot(BaseLogic):
    def __init__(self):
        super().__init__()
        self.directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]
        self.current_direction = 0
        self.score_logged = False

    def next_move(self, board_bot: GameObject, board: Board):
        def distance(a, b):
            return abs(a.x - b.x) + abs(a.y - b.y)

        def try_move(target_x, target_y, avoid_positions=None):
            dx, dy = get_direction(board_bot.position.x, board_bot.position.y, target_x, target_y)
            next_x = board_bot.position.x + dx
            next_y = board_bot.position.y + dy
            if board.is_valid_move(board_bot.position, dx, dy):
                if avoid_positions and (next_x, next_y) in avoid_positions:
                    return 0, 0  # stay to avoid danger
                return dx, dy
            return 0, 0  # invalid move fallback

        def predict_enemy_target(bot: GameObject) -> Optional[Position]:
            d = bot.properties.diamonds
            if d >= 5:
                return bot.properties.base
            elif 3 <= d < 5:
                red_diamonds = [d for d in board.diamonds if d.type == "RedDiamondGameObject"]
                blue_diamonds = [d for d in board.diamonds if d.type != "RedDiamondGameObject"]
                all_diamonds = red_diamonds + blue_diamonds
                if all_diamonds:
                    return min(all_diamonds, key=lambda x: distance(bot.position, x.position)).position
            return None

        enemy_positions = {
            (bot.position.x, bot.position.y)
            for bot in board.bots
            if bot.properties.name != board_bot.properties.name
        }

        diamonds = board_bot.properties.diamonds
        time_left = board_bot.properties.milliseconds_left

        # Log final score once
        if time_left is not None and time_left < 1200 and not self.score_logged:
            self.score_logged = True
            name = board_bot.properties.name
            score = board_bot.properties.score
            d = board_bot.properties.diamonds
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[INFO][{name}] Final Score (early): {score} | Diamonds: {d}")
            try:
                with open("greedybot_score.txt", "a") as f:
                    f.write(f"[{timestamp}] {name} - Score: {score}, Diamonds: {d}\n")
            except:
                pass

        # Defensive mode
        if time_left is not None and time_left < 1200:
            return 0, 0

        # Return to base if carrying max diamonds
        if diamonds == 5:
            move = try_move(board_bot.properties.base.x, board_bot.properties.base.y, avoid_positions=enemy_positions)
            if move != (0, 0):
                return move
            target = board_bot.properties.base
            safe_moves = []
            for dx, dy in self.directions:
                next_x = board_bot.position.x + dx
                next_y = board_bot.position.y + dy
                if (next_x, next_y) in enemy_positions:
                    continue
                if board.is_valid_move(board_bot.position, dx, dy):
                    new_dist = distance(target, type('P', (), {'x': next_x, 'y': next_y}))
                    curr_dist = distance(target, board_bot.position)
                    if new_dist < curr_dist:
                        safe_moves.append((dx, dy))
            if safe_moves:
                return random.choice(safe_moves)

        # Intercept enemy
        for enemy in board.bots:
            if enemy.properties.name == board_bot.properties.name:
                continue
            if enemy.properties.diamonds >= 5 or (3 <= enemy.properties.diamonds < 5):
                target = predict_enemy_target(enemy)
                if target and distance(board_bot.position, target) <= 6:
                    move = try_move(target.x, target.y)
                    if move != (0, 0):
                        return move

        # Collect nearest diamond (prefer red)
        if board.diamonds:
            red_diamonds = [d for d in board.diamonds if d.type == "RedDiamondGameObject"]
            blue_diamonds = [d for d in board.diamonds if d.type != "RedDiamondGameObject"]

            nearest_red = min(red_diamonds, key=lambda d: distance(board_bot.position, d.position), default=None)
            nearest_blue = min(blue_diamonds, key=lambda d: distance(board_bot.position, d.position), default=None)

            if nearest_red and (not nearest_blue or distance(board_bot.position, nearest_red.position) <= distance(board_bot.position, nearest_blue.position)):
                move = try_move(nearest_red.position.x, nearest_red.position.y)
                if move != (0, 0):
                    return move
            elif nearest_blue:
                move = try_move(nearest_blue.position.x, nearest_blue.position.y)
                if move != (0, 0):
                    return move

        # Roam safely
        for i in range(len(self.directions)):
            dx, dy = self.directions[self.current_direction]
            if board.is_valid_move(board_bot.position, dx, dy):
                if random.random() > 0.7:
                    self.current_direction = (self.current_direction + 1) % len(self.directions)
                return dx, dy
            else:
                self.current_direction = (self.current_direction + 1) % len(self.directions)

        # Fallback movement
        for radius in range(2, 4):
            offsets = [(dx, dy) for dx in range(-radius, radius + 1)
                       for dy in range(-radius, radius + 1)
                       if (dx != 0 or dy != 0) and abs(dx) != abs(dy)]
            random.shuffle(offsets)
            for dx, dy in offsets:
                if board.is_valid_move(board_bot.position, dx, dy):
                    return dx, dy

        # Final fallback
        return 0, 0
