#!/usr/bin/env python3
"""
Speed Benchmark Framework for 2048 AI Performance Analysis
Measures move time, game duration, and identifies bottlenecks
"""

import numpy as np
import time
import random
import rust_ai_2048
from typing import Dict, List, Tuple
import statistics

class Game2048:
    """Lightweight 2048 game for speed benchmarking"""

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
        """Execute move and return if board changed"""
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
            row = [x for x in self.board[i] if x != 0]
            for j in range(len(row) - 1):
                if row[j] == row[j + 1]:
                    row[j] *= 2
                    self.score += row[j]
                    row[j + 1] = 0
            row = [x for x in row if x != 0]
            row += [0] * (4 - len(row))
            self.board[i] = row

    def move_right(self):
        for i in range(4):
            row = [x for x in self.board[i] if x != 0]
            row.reverse()
            for j in range(len(row) - 1):
                if row[j] == row[j + 1]:
                    row[j] *= 2
                    self.score += row[j]
                    row[j + 1] = 0
            row = [x for x in row if x != 0]
            row += [0] * (4 - len(row))
            row.reverse()
            self.board[i] = row

    def move_up(self):
        for j in range(4):
            col = [self.board[i][j] for i in range(4) if self.board[i][j] != 0]
            for i in range(len(col) - 1):
                if col[i] == col[i + 1]:
                    col[i] *= 2
                    self.score += col[i]
                    col[i + 1] = 0
            col = [x for x in col if x != 0]
            col += [0] * (4 - len(col))
            for i in range(4):
                self.board[i][j] = col[i]

    def move_down(self):
        for j in range(4):
            col = [self.board[i][j] for i in range(4) if self.board[i][j] != 0]
            col.reverse()
            for i in range(len(col) - 1):
                if col[i] == col[i + 1]:
                    col[i] *= 2
                    self.score += col[i]
                    col[i + 1] = 0
            col = [x for x in col if x != 0]
            col += [0] * (4 - len(col))
            col.reverse()
            for i in range(4):
                self.board[i][j] = col[i]

    def is_game_over(self):
        # Check for empty cells
        for row in self.board:
            if 0 in row:
                return False

        # Check for possible merges
        for i in range(4):
            for j in range(4):
                current = self.board[i][j]
                if (i < 3 and current == self.board[i + 1][j]) or \
                   (j < 3 and current == self.board[i][j + 1]):
                    return False

        return True

    def get_max_tile(self):
        return max(max(row) for row in self.board)

    def get_empty_count(self):
        return sum(row.count(0) for row in self.board)

class SpeedBenchmark:
    """Comprehensive speed testing framework"""

    def __init__(self, ai, ai_name: str):
        self.ai = ai
        self.ai_name = ai_name
        self.results = []

    def run_single_game(self) -> Dict:
        """Run one game and collect detailed timing data"""
        game = Game2048()
        move_times = []
        game_start = time.perf_counter()

        move_details = []

        while not game.is_game_over():
            empty_tiles = game.get_empty_count()
            max_tile = game.get_max_tile()

            # Time the AI decision
            start = time.perf_counter()
            move = self.ai.get_best_move(game.board)
            move_time = time.perf_counter() - start

            move_times.append(move_time)
            move_details.append({
                'move_num': game.moves + 1,
                'move_time_ms': move_time * 1000,
                'empty_tiles': empty_tiles,
                'max_tile': max_tile,
                'board_complexity': self.calculate_complexity(game.board)
            })

            if move and game.move(move):
                pass
            else:
                break

        total_game_time = time.perf_counter() - game_start

        return {
            'score': game.score,
            'moves': game.moves,
            'max_tile': game.get_max_tile(),
            'total_game_time': total_game_time,
            'avg_move_time_ms': np.mean(move_times) * 1000,
            'median_move_time_ms': np.median(move_times) * 1000,
            'min_move_time_ms': min(move_times) * 1000,
            'max_move_time_ms': max(move_times) * 1000,
            'std_move_time_ms': np.std(move_times) * 1000,
            'moves_per_second': game.moves / total_game_time,
            'move_details': move_details
        }

    def calculate_complexity(self, board) -> float:
        """Calculate board complexity score"""
        # Count unique values
        unique_values = len(set(val for row in board for val in row if val > 0))

        # Count empty spaces
        empty_count = sum(row.count(0) for row in board)

        # Max tile value
        max_tile = max(max(row) for row in board)

        # Complexity is higher with more unique values and higher max tile
        complexity = unique_values * np.log2(max_tile + 1) * (16 - empty_count)
        return complexity

    def run_benchmark(self, games: int = 5) -> Dict:
        """Run comprehensive speed benchmark"""
        print(f"🚀 SPEED BENCHMARK: {self.ai_name}")
        print(f"Running {games} games for performance analysis...")
        print("=" * 60)

        all_results = []

        for game_num in range(games):
            print(f"  Game {game_num + 1}/{games}...", end=" ")
            start_time = time.time()

            result = self.run_single_game()
            game_duration = time.time() - start_time

            all_results.append(result)

            print(f"Score: {result['score']:,}, "
                  f"Moves: {result['moves']}, "
                  f"Avg: {result['avg_move_time_ms']:.2f}ms/move, "
                  f"Total: {game_duration:.1f}s")

        # Aggregate statistics
        scores = [r['score'] for r in all_results]
        move_times = [r['avg_move_time_ms'] for r in all_results]
        total_times = [r['total_game_time'] for r in all_results]
        moves_counts = [r['moves'] for r in all_results]
        moves_per_sec = [r['moves_per_second'] for r in all_results]

        # Performance by game phase analysis
        early_game_times = []  # First 50 moves
        mid_game_times = []    # Moves 51-100
        late_game_times = []   # Moves 100+

        for result in all_results:
            for detail in result['move_details']:
                if detail['move_num'] <= 50:
                    early_game_times.append(detail['move_time_ms'])
                elif detail['move_num'] <= 100:
                    mid_game_times.append(detail['move_time_ms'])
                else:
                    late_game_times.append(detail['move_time_ms'])

        benchmark_results = {
            'ai_name': self.ai_name,
            'games_tested': games,
            'avg_score': np.mean(scores),
            'min_score': min(scores),
            'max_score': max(scores),
            'std_score': np.std(scores),
            'avg_moves': np.mean(moves_counts),
            'avg_game_duration': np.mean(total_times),
            'avg_move_time_ms': np.mean(move_times),
            'median_move_time_ms': np.median(move_times),
            'min_move_time_ms': min([r['min_move_time_ms'] for r in all_results]),
            'max_move_time_ms': max([r['max_move_time_ms'] for r in all_results]),
            'std_move_time_ms': np.mean([r['std_move_time_ms'] for r in all_results]),
            'avg_moves_per_second': np.mean(moves_per_sec),
            'early_game_avg_ms': np.mean(early_game_times) if early_game_times else 0,
            'mid_game_avg_ms': np.mean(mid_game_times) if mid_game_times else 0,
            'late_game_avg_ms': np.mean(late_game_times) if late_game_times else 0,
            'detailed_results': all_results
        }

        self.print_benchmark_results(benchmark_results)
        return benchmark_results

    def print_benchmark_results(self, results: Dict):
        """Print comprehensive benchmark results"""
        print("\n" + "=" * 60)
        print(f"📊 PERFORMANCE SUMMARY: {results['ai_name']}")
        print("=" * 60)

        print(f"\n🎯 GAME PERFORMANCE:")
        print(f"  Average Score:    {results['avg_score']:>10,.0f}")
        print(f"  Score Range:      {results['min_score']:>10,.0f} - {results['max_score']:>10,.0f}")
        print(f"  Average Moves:    {results['avg_moves']:>10.1f}")
        print(f"  Game Duration:    {results['avg_game_duration']:>10.2f}s")

        print(f"\n⚡ SPEED METRICS:")
        print(f"  Avg Move Time:    {results['avg_move_time_ms']:>10.2f}ms")
        print(f"  Median Move Time: {results['median_move_time_ms']:>10.2f}ms")
        print(f"  Speed Range:      {results['min_move_time_ms']:>10.2f}ms - {results['max_move_time_ms']:>10.2f}ms")
        print(f"  Moves/Second:     {results['avg_moves_per_second']:>10.1f}")

        print(f"\n🎮 PERFORMANCE BY GAME PHASE:")
        if results['early_game_avg_ms'] > 0:
            print(f"  Early Game (1-50):   {results['early_game_avg_ms']:>8.2f}ms/move")
        if results['mid_game_avg_ms'] > 0:
            print(f"  Mid Game (51-100):   {results['mid_game_avg_ms']:>8.2f}ms/move")
        if results['late_game_avg_ms'] > 0:
            print(f"  Late Game (100+):    {results['late_game_avg_ms']:>8.2f}ms/move")

        # Speed assessment
        avg_time = results['avg_move_time_ms']
        print(f"\n🔍 SPEED ASSESSMENT:")
        if avg_time < 1.0:
            print(f"  ✅ EXCELLENT: <1ms per move")
        elif avg_time < 3.0:
            print(f"  🟢 GOOD: <3ms per move")
        elif avg_time < 10.0:
            print(f"  🟡 ACCEPTABLE: <10ms per move")
        else:
            print(f"  🔴 SLOW: >{avg_time:.1f}ms per move - needs optimization")

        # Improvement potential
        potential_speedup = max(1, avg_time / 1.0)  # Target 1ms
        print(f"  🎯 Target: <1ms per move ({potential_speedup:.1f}x speedup needed)")

        print("=" * 60)

def main():
    """Run speed benchmark on ChampionAI"""
    print("🏁 2048 AI SPEED BENCHMARK")
    print("Analyzing ChampionAI performance...")

    # Test ChampionAI
    champion = rust_ai_2048.ChampionAI()
    benchmark = SpeedBenchmark(champion, "ChampionAI")

    # Run 5-game speed test
    results = benchmark.run_benchmark(games=5)

    print(f"\n💡 OPTIMIZATION OPPORTUNITIES:")
    print(f"- Current: {results['avg_move_time_ms']:.1f}ms per move")
    print(f"- Target:  <1.0ms per move")
    print(f"- Potential: {results['avg_move_time_ms']:.1f}x speedup available")

if __name__ == "__main__":
    main()