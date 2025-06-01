from game.logic.base import BaseLogic
from game.models import Board, GameObject, Position
from typing import Optional
from game.util import get_direction
import random
import math

class GreedyBot(BaseLogic):
    def __init__(self):
        # arah gerak (kanan, bawah, kiri, atas)
        self.directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]
        self.goal_position: Optional[Position] = None  # tujuan sekarang
        self.current_direction = 0  # arah terakhir
        self.chased_timer = 0  # ngitung berapa lama dikejar musuh
        self.last_position: Optional[Position] = None  # posisi sebelumnya
        self.run = 0  # buat ngitung berapa kali kabur
        self.diamound_counter_cd = 0  # cooldown ambil diamond
        self.stuck_counter = 0  # kalau nggak gerak

    def next_move(self, board_bot: GameObject, board: Board):
        # ambil semua data dari game
        props = board_bot.properties
        current_position = board_bot.position
        all_bots = board.bots
        diamonds = board.diamonds

        # ngitung jumlah diamond di sekitar target
        def count_near_diamond_target(center: Position, radius: int = 3) -> int:
            return sum(
                1 for d in diamonds
                if abs(d.position.x - center.x) + abs(d.position.y - center.y) <= radius
            )

        # jarak pake akar kuadrat
        def distance(pos1: Position, pos2: Position) -> int:
            return math.hypot(pos1.x - pos2.x, pos1.y - pos2.y)

        # cari musuh yang deket banget
        def steal(radius: int = 2):
            return [
                bot for bot in all_bots
                if bot.id != board_bot.id and
                abs(bot.position.x - current_position.x) + abs(bot.position.y - current_position.y) <= radius
            ]

        # update status dikejar
        nearby_bots = steal(radius=2)
        self.chased_timer = self.chased_timer + 1 if nearby_bots else 0
        if self.diamound_counter_cd > 0:
            self.diamound_counter_cd -= 1
        if self.last_position == current_position:
            self.stuck_counter += 1
        else:
            self.stuck_counter = 0
        self.last_position = current_position

        # kalau stuck 2 turn, ganti arah
        if self.stuck_counter >= 2:
            self.goal_position = None
            self.current_direction = (self.current_direction + 1) % len(self.directions)
            delta_x, delta_y = self.directions[self.current_direction]
            if board.is_valid_move(current_position, delta_x, delta_y):
                return delta_x, delta_y
            else:
                return 0, 0

        # kalau udah dikejar 5 turn, langsung balik ke base
        if self.chased_timer >= 5:
            base = props.base
            self.goal_position = base
            delta_x, delta_y = get_direction(current_position.x, current_position.y, base.x, base.y)
            if board.is_valid_move(current_position, delta_x, delta_y):
                return delta_x, delta_y
            else:
                return 0, 0

        # kalau udah megang 4+ diamond, pulang ke base 
        if props.diamonds >= 4:
            base = props.base
            if nearby_bots and self.run <= 2:
                closest = min(nearby_bots, key=lambda b: distance(current_position, b.position))
                dx = current_position.x - closest.position.x
                dy = current_position.y - closest.position.y
                dodge_x = 1 if dx >= 0 else -1
                dodge_y = 1 if dy >= 0 else -1
                self.goal_position = Position(
                    min(max(0, base.x + dodge_x), board.width - 1),
                    min(max(0, base.y + dodge_y), board.height - 1),
                )
                self.run += 1
            else:
                self.goal_position = base
                self.run += 1
                if self.run >= 5:
                    self.run = 0
            delta_x, delta_y = get_direction(current_position.x, current_position.y, self.goal_position.x, self.goal_position.y)
            if board.is_valid_move(current_position, delta_x, delta_y):
                return delta_x, delta_y
            else:
                return 0, 0

        # kejar musuh yang bawa banyak diamond
        enemy_carry_diamond = [
            bot for bot in all_bots
            if bot.id != board_bot.id
            and bot.properties.diamonds >= 2
            and distance(current_position, bot.position) <= 4
        ]

        if enemy_carry_diamond:
            target = max(enemy_carry_diamond, key=lambda b: b.properties.diamonds)
            if target.position != props.base:
                self.goal_position = target.position
                delta_x, delta_y = get_direction(current_position.x, current_position.y, self.goal_position.x, self.goal_position.y)
                if board.is_valid_move(current_position, delta_x, delta_y):
                    return delta_x, delta_y
                else:
                    return 0, 0

        # cari diamond terdekat yang rame
        if self.diamound_counter_cd == 0:
            candidate_diamonds = [d for d in diamonds if distance(current_position, d.position) <= 5]
            best_diamond = max(
                candidate_diamonds,
                key=lambda d: (
                    count_near_diamond_target(d.position, radius=2),
                    -distance(current_position, d.position)
                ),
                default=None
            )
            if best_diamond:
                self.goal_position = best_diamond.position
            elif diamonds:
                nearest = min(diamonds, key=lambda d: distance(current_position, d.position))
                self.goal_position = nearest.position
            else:
                self.goal_position = None

        # kalau ada diamond deket banget
        elif self.diamound_counter_cd > 0:
            close_diamonds = [d for d in diamonds if distance(current_position, d.position) <= 2]
            if close_diamonds:
                nearest = min(close_diamonds, key=lambda d: distance(current_position, d.position))
                self.goal_position = nearest.position

        # kalau ada tujuan jelas, kejar
        if self.goal_position and self.goal_position != current_position:
            delta_x, delta_y = get_direction(current_position.x, current_position.y, self.goal_position.x, self.goal_position.y)
            if board.is_valid_move(current_position, delta_x, delta_y):
                if self.goal_position == current_position:
                    self.diamound_counter_cd = 4
                return delta_x, delta_y
            else:
                return 0, 0
        else:
            # roaming nyari arah yang bisa dilalui
            for _ in range(4):
                delta_x, delta_y = self.directions[self.current_direction]
                if board.is_valid_move(current_position, delta_x, delta_y):
                    if random.random() > 0.6:
                        self.current_direction = (self.current_direction + 1) % len(self.directions)
                    return delta_x, delta_y
                else:
                    self.current_direction = (self.current_direction + 1) % len(self.directions)

        # fallback terakhir kalau nggak bisa kemana-mana
        return 0, 0
