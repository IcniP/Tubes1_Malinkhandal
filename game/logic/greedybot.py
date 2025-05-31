import random
from typing import Optional
from game.logic.base import BaseLogic
from game.models import GameObject, Board, Position
from game.util import get_direction


class GreedyBot(BaseLogic):
    def __init__(self):
        super().__init__()
        self.directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]
        self.current_direction = 0

    def next_move(self, board_bot: GameObject, board: Board):
        def distance(a, b):
            return abs(a.x - b.x) + abs(a.y - b.y)

        def try_move(target_x, target_y, avoid_positions=None):
            dx, dy = get_direction(board_bot.position.x, board_bot.position.y, target_x, target_y)
            next_x = board_bot.position.x + dx
            next_y = board_bot.position.y + dy
            if board.is_valid_move(board_bot.position, dx, dy):
                if avoid_positions and (next_x, next_y) in avoid_positions:
                    return None
                return dx, dy
            return None

        # Hindari tabrakan dengan musuh saat pulang
        enemy_positions = {
            (bot.position.x, bot.position.y)
            for bot in board.bots
            if bot.properties.name != board_bot.properties.name
        }

        diamonds = board_bot.properties.diamonds
        time_left = board_bot.properties.milliseconds_left

        # 💡 FINAL PING: jika waktu hampir habis, tetap gerak ke base
        if time_left is not None and time_left < 1500:
            move = try_move(board_bot.properties.base.x, board_bot.properties.base.y)
            if move:
                return move

        # 1. Pulang ke base jika diamond sudah 5
        if diamonds == 5:
            move = try_move(board_bot.properties.base.x, board_bot.properties.base.y, avoid_positions=enemy_positions)
            if move:
                return move
            # Coba arah lain yang lebih dekat ke base tapi aman
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

        # 2. Kejar player (hanya jika diamond <= 3)
        if diamonds <= 3:
            enemy_bots = [
                other for other in board.bots
                if other.properties.name != board_bot.properties.name and other.properties.diamonds > 0
            ]
            if enemy_bots:
                enemy_bots.sort(key=lambda b: (-b.properties.diamonds, distance(board_bot.position, b.position)))
                for enemy in enemy_bots:
                    if distance(board_bot.position, enemy.position) <= 5:
                        move = try_move(enemy.position.x, enemy.position.y)
                        if move:
                            return move

        # 3. Cari diamond terdekat, red hanya jika memang paling dekat
        if board.diamonds:
            red_diamonds = [d for d in board.diamonds if d.type == "RedDiamondGameObject"]
            blue_diamonds = [d for d in board.diamonds if d.type != "RedDiamondGameObject"]

            nearest_red = min(red_diamonds, key=lambda d: distance(board_bot.position, d.position), default=None)
            nearest_blue = min(blue_diamonds, key=lambda d: distance(board_bot.position, d.position), default=None)

            # Ambil red hanya jika dia paling dekat
            if nearest_red and (not nearest_blue or distance(board_bot.position, nearest_red.position) <= distance(board_bot.position, nearest_blue.position)):
                move = try_move(nearest_red.position.x, nearest_red.position.y)
                if move:
                    return move
            elif nearest_blue:
                move = try_move(nearest_blue.position.x, nearest_blue.position.y)
                if move:
                    return move

        # 4. Roaming (kalem, tidak muter-muter bodoh)
        for i in range(len(self.directions)):
            dx, dy = self.directions[self.current_direction]
            if board.is_valid_move(board_bot.position, dx, dy):
                if random.random() > 0.7:
                    self.current_direction = (self.current_direction + 1) % len(self.directions)
                return dx, dy
            else:
                self.current_direction = (self.current_direction + 1) % len(self.directions)

        # 5. Gerak random valid radius 2–3 (bantu keluar dari situasi stuck)
        for radius in range(2, 4):
            offsets = [(dx, dy) for dx in range(-radius, radius+1)
                                 for dy in range(-radius, radius+1)
                                 if (dx != 0 or dy != 0) and abs(dx) != abs(dy)]
            random.shuffle(offsets)
            for dx, dy in offsets:
                if board.is_valid_move(board_bot.position, dx, dy):
                    return dx, dy

        # 6. Fail-safe arah acak
        return random.choice(self.directions)
