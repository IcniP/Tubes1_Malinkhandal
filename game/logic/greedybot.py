import random
from typing import Optional
from game.logic.base import BaseLogic
from game.models import GameObject, Board, Position
from game.util import get_direction


# Muhammad Farisi Suyitno 123140152
# Ali Akbar
# Bima aryaseta


#Kelompok 5 (malink handal)


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


        def predict_enemy_target(bot: GameObject) -> Optional[Position]:
            d = bot.properties.diamonds
            if d >= 5:
                return bot.properties.base  # balik ke base
            elif 3 <= d < 5:
                red_diamonds = [d for d in board.diamonds if d.type == "RedDiamondGameObject"]
                blue_diamonds = [d for d in board.diamonds if d.type != "RedDiamondGameObject"]
                all_diamonds = red_diamonds + blue_diamonds
                if all_diamonds:
                    return min(all_diamonds, key=lambda x: distance(bot.position, x.position)).position
            return None


        # menghindar dari musuh jika diamond penuh
        enemy_positions = {
            (bot.position.x, bot.position.y)
            for bot in board.bots
            if bot.properties.name != board_bot.properties.name
        }


        diamonds = board_bot.properties.diamonds
        time_left = board_bot.properties.milliseconds_left


        # kalau waktu game mau abis balik ke base
        if time_left is not None and time_left < 1500:
            move = try_move(board_bot.properties.base.x, board_bot.properties.base.y)
            if move:
                return move


        # balik ke base kalo diamond 4
        if diamonds == 4:
            move = try_move(board_bot.properties.base.x, board_bot.properties.base.y, avoid_positions=enemy_positions)
            if move:
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


        # prediksi gerakan musuh
        for enemy in board.bots:
            if enemy.properties.name == board_bot.properties.name:
                continue
            if enemy.properties.diamonds >= 5 or (3 <= enemy.properties.diamonds < 5):
                target = predict_enemy_target(enemy)
                if target and distance(board_bot.position, target) <= 6:
                    move = try_move(target.x, target.y)
                    if move:
                        return move


        # cari dimaond terdekat utamain merah
        if board.diamonds:
            red_diamonds = [d for d in board.diamonds if d.type == "RedDiamondGameObject"]
            blue_diamonds = [d for d in board.diamonds if d.type != "RedDiamondGameObject"]


            nearest_red = min(red_diamonds, key=lambda d: distance(board_bot.position, d.position), default=None)
            nearest_blue = min(blue_diamonds, key=lambda d: distance(board_bot.position, d.position), default=None)


            if nearest_red and (not nearest_blue or distance(board_bot.position, nearest_red.position) <= distance(board_bot.position, nearest_blue.position)):
                move = try_move(nearest_red.position.x, nearest_red.position.y)
                if move:
                    return move
            elif nearest_blue:
                move = try_move(nearest_blue.position.x, nearest_blue.position.y)
                if move:
                    return move


        # jalan jalan kalo gaada target
        for i in range(len(self.directions)):
            dx, dy = self.directions[self.current_direction]
            if board.is_valid_move(board_bot.position, dx, dy):
                if random.random() > 0.7:
                    self.current_direction = (self.current_direction + 1) % len(self.directions)
                return dx, dy
            else:
                self.current_direction = (self.current_direction + 1) % len(self.directions)


        # backup
        for radius in range(2, 4):
            offsets = [(dx, dy) for dx in range(-radius, radius+1)
                                 for dy in range(-radius, radius+1)
                                 if (dx != 0 or dy != 0) and abs(dx) != abs(dy)]
            random.shuffle(offsets)
            for dx, dy in offsets:
                if board.is_valid_move(board_bot.position, dx, dy):
                    return dx, dy


        # gerak random kalau bener bener gaada apa apa
        return random.choice(self.directions)