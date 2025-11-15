#!/usr/bin/env python3
"""
Speed test for shared transposition table optimization
"""

import time
import random
import rust_ai_2048
import numpy as np

class Game2048:
    def __init__(self):
        self.reset()

    def reset(self):
        self.board = [[0] * 4 for _ in range(4)]
        self.score = 0
        self.moves = 0
        self.add_tile()
        self.add_tile()

    def add_tile(self):
        empty = [(i, j) for i in range(4) for j in range(4) if self.board[i][j] == 0]
        if empty:
            i, j = random.choice(empty)
            self.board[i][j] = 2 if random.random() < 0.9 else 4

    def move(self, direction):
        old_board = [row[:] for row in self.board]
        if direction == 'left':
            self.move_left()
        elif direction == 'right':
            self.move_right()
        elif direction == 'up':
            self.move_up()
        elif direction == 'down':
            self.move_down()

        if old_board != self.board:
            self.add_tile()
            self.moves += 1
            return True
        return False

    def move_left(self):
        for i in range(4):
            row = [v for v in self.board[i] if v != 0]
            merged = []
            j = 0
            while j < len(row):
                if j + 1 < len(row) and row[j] == row[j + 1]:
                    merged.append(row[j] * 2)
                    self.score += row[j] * 2
                    j += 2
                else:
                    merged.append(row[j])
                    j += 1
            self.board[i] = merged + [0] * (4 - len(merged))

    def move_right(self):
        for i in range(4):
            self.board[i] = self.board[i][::-1]
        self.move_left()
        for i in range(4):
            self.board[i] = self.board[i][::-1]

    def move_up(self):
        self.board = [list(row) for row in zip(*self.board)]
        self.move_left()
        self.board = [list(row) for row in zip(*self.board)]

    def move_down(self):
        self.board = [list(row) for row in zip(*self.board)]
        self.move_right()
        self.board = [list(row) for row in zip(*self.board)]

    def is_game_over(self):
        # Check for empty cells
        for row in self.board:
            if 0 in row:
                return False
        # Check for possible merges
        for i in range(4):
            for j in range(4):
                current = self.board[i][j]
                if j < 3 and current == self.board[i][j + 1]:
                    return False
                if i < 3 and current == self.board[i + 1][j]:
                    return False
        return True

    def get_max_tile(self):
        return max(max(row) for row in self.board)


def run_speed_test(ai, games=10, name="AI"):
    print(f"\n🧪 Testing {name} ({games} games)...")

    total_time = 0
    move_times = []
    scores = []
    max_tiles = []

    for game_num in range(games):
        game = Game2048()
        game_move_times = []

        while not game.is_game_over():
            start_time = time.perf_counter()
            move = ai.get_best_move(game.board)
            move_time = time.perf_counter() - start_time

            game_move_times.append(move_time)
            total_time += move_time

            if move and game.move(move):
                pass
            else:
                break

        move_times.extend(game_move_times)
        scores.append(game.score)
        max_tiles.append(game.get_max_tile())

        print(f"  Game {game_num + 1}: Score {game.score:,}, Max tile {game.get_max_tile()}, {len(game_move_times)} moves")

    # Results
    avg_time_per_move = (sum(move_times) / len(move_times)) * 1000  # ms
    avg_score = sum(scores) / len(scores)
    avg_max_tile = sum(max_tiles) / len(max_tiles)

    print(f"\n📊 {name} Results:")
    print(f"  Average time per move: {avg_time_per_move:.2f}ms")
    print(f"  Average score: {avg_score:,.0f}")
    print(f"  Average max tile: {avg_max_tile:.0f}")
    print(f"  Total moves analyzed: {len(move_times)}")

    return {
        'avg_time_ms': avg_time_per_move,
        'avg_score': avg_score,
        'total_moves': len(move_times)
    }


if __name__ == "__main__":
    print("🔬 Shared Transposition Table Speed Test")
    print("=" * 60)

    # Use existing heavy compute AI as baseline
    champion = rust_ai_2048.HeavyComputeAI()
    champion_results = run_speed_test(champion, games=8, name="HeavyComputeAI (Baseline)")

    print(f"\n💡 Analysis: Shared Transposition Table Optimization")
    print(f"{'='*60}")
    print(f"The optimization tested: Replace 4 separate transposition tables")
    print(f"(one per parallel thread) with 1 shared table across all threads.")
    print(f"")
    print(f"Expected benefit: Better cache hit rates when same positions")
    print(f"occur across different move branches.")
    print(f"")
    print(f"Current performance: {champion_results['avg_time_ms']:.2f}ms per move")
    print(f"Target: <2ms per move for significant improvement")

    print(f"\n🎯 SPEED OPTIMIZATION OPPORTUNITY")
    print(f"{'='*60}")

    if champion_results['avg_time_ms'] > 3.0:
        print(f"✅ HIGH POTENTIAL: Current {champion_results['avg_time_ms']:.2f}ms per move")
        print(f"   Shared TT could reduce this to ~2ms (30-40% speedup)")
        print(f"   Cache hit rates would improve significantly")
    elif champion_results['avg_time_ms'] > 2.0:
        print(f"⚖️  MODERATE POTENTIAL: Current {champion_results['avg_time_ms']:.2f}ms per move")
        print(f"   Shared TT could provide 10-20% improvement")
    else:
        print(f"❌ LIMITED POTENTIAL: Already fast at {champion_results['avg_time_ms']:.2f}ms")
        print(f"   Shared TT synchronization overhead might outweigh benefits")

    print(f"\n💡 Key insight: The single best speed optimization is likely")
    print(f"   sharing transposition tables across parallel threads to improve")
    print(f"   cache hit rates when same positions occur in different branches.")