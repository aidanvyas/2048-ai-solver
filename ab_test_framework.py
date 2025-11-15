#!/usr/bin/env python3
"""
A/B Testing Framework for 2048 AI Improvements
Ensures statistical significance when comparing implementations
"""

import numpy as np
from scipy import stats
import json
import time
import random
from typing import Dict, List, Tuple
import rust_ai_2048

class Game2048:
    """Standard 2048 game implementation for testing"""

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


class ABTester:
    """Statistical A/B testing for AI implementations"""

    def __init__(self, ai_a, ai_b, name_a="AI_A", name_b="AI_B"):
        self.ai_a = ai_a
        self.ai_b = ai_b
        self.name_a = name_a
        self.name_b = name_b
        self.results_a = []
        self.results_b = []

    def run_game(self, ai) -> Dict:
        """Run one game and return statistics"""
        game = Game2048()
        move_times = []

        while not game.is_game_over():
            start = time.perf_counter()
            move = ai.get_best_move(game.board)
            move_time = time.perf_counter() - start
            move_times.append(move_time)

            if move and game.move(move):
                pass
            else:
                break

        return {
            'score': game.score,
            'moves': game.moves,
            'max_tile': game.get_max_tile(),
            'avg_move_time': np.mean(move_times) * 1000,  # ms
            'median_move_time': np.median(move_times) * 1000,
            'win': game.get_max_tile() >= 2048
        }

    def run_test(self, games_per_ai: int = 100, parallel: bool = False):
        """Run full A/B test with statistical analysis"""
        print(f"{'='*70}")
        print(f"A/B TEST: {self.name_a} vs {self.name_b}")
        print(f"Running {games_per_ai} games per implementation...")
        print(f"{'='*70}\n")

        # Run games for AI A
        print(f"Testing {self.name_a}...")
        for i in range(games_per_ai):
            if (i + 1) % 10 == 0:
                print(f"  Progress: {i + 1}/{games_per_ai}")
            result = self.run_game(self.ai_a)
            self.results_a.append(result)

        # Run games for AI B
        print(f"\nTesting {self.name_b}...")
        for i in range(games_per_ai):
            if (i + 1) % 10 == 0:
                print(f"  Progress: {i + 1}/{games_per_ai}")
            result = self.run_game(self.ai_b)
            self.results_b.append(result)

        # Analyze results
        self.analyze_results()

    def analyze_results(self):
        """Statistical analysis of A/B test results"""
        print(f"\n{'='*70}")
        print("RESULTS ANALYSIS")
        print(f"{'='*70}\n")

        # Extract metrics
        scores_a = [r['score'] for r in self.results_a]
        scores_b = [r['score'] for r in self.results_b]

        times_a = [r['avg_move_time'] for r in self.results_a]
        times_b = [r['avg_move_time'] for r in self.results_b]

        wins_a = sum(r['win'] for r in self.results_a)
        wins_b = sum(r['win'] for r in self.results_b)

        max_tiles_a = [r['max_tile'] for r in self.results_a]
        max_tiles_b = [r['max_tile'] for r in self.results_b]

        # Performance Metrics
        print("📊 PERFORMANCE METRICS")
        print(f"{'Metric':<20} {self.name_a:<25} {self.name_b:<25}")
        print("-" * 70)

        # Score Statistics
        print("SCORE STATISTICS:")
        print(f"{'Avg Score':<20} {np.mean(scores_a):>25.0f} {np.mean(scores_b):>25.0f}")
        print(f"{'Min Score':<20} {min(scores_a):>25,} {min(scores_b):>25,}")
        print(f"{'Max Score':<20} {max(scores_a):>25,} {max(scores_b):>25,}")
        print(f"{'Median Score':<20} {np.median(scores_a):>25.0f} {np.median(scores_b):>25.0f}")
        print(f"{'Std Dev Score':<20} {np.std(scores_a):>25.0f} {np.std(scores_b):>25.0f}")

        # Time per Move Statistics
        print(f"\nTIME PER MOVE STATISTICS:")
        print(f"{'Avg Time (ms)':<20} {np.mean(times_a):>25.3f} {np.mean(times_b):>25.3f}")
        print(f"{'Min Time (ms)':<20} {min(times_a):>25.3f} {min(times_b):>25.3f}")
        print(f"{'Max Time (ms)':<20} {max(times_a):>25.3f} {max(times_b):>25.3f}")
        print(f"{'Median Time (ms)':<20} {np.median(times_a):>25.3f} {np.median(times_b):>25.3f}")
        print(f"{'Std Dev Time (ms)':<20} {np.std(times_a):>25.3f} {np.std(times_b):>25.3f}")

        # Tile Achievement Rates
        print(f"\nTILE ACHIEVEMENT RATES:")
        for tile_val in [512, 1024, 2048, 4096, 8192]:
            count_a = sum(1 for t in max_tiles_a if t >= tile_val)
            count_b = sum(1 for t in max_tiles_b if t >= tile_val)
            print(f"{'≥' + str(tile_val) + ' tiles':<20} {100*count_a/len(max_tiles_a):>24.1f}% "
                  f"{100*count_b/len(max_tiles_b):>24.1f}%")

        # Statistical Tests
        print(f"\n{'='*70}")
        print("📈 STATISTICAL SIGNIFICANCE TESTS")
        print(f"{'='*70}\n")

        # T-test for scores
        t_stat, p_value = stats.ttest_ind(scores_a, scores_b)
        print(f"Score Comparison (t-test):")
        print(f"  t-statistic: {t_stat:.4f}")
        print(f"  p-value: {p_value:.6f}")

        if p_value < 0.05:
            if np.mean(scores_a) > np.mean(scores_b):
                print(f"  ✅ {self.name_a} scores significantly higher (p < 0.05)")
            else:
                print(f"  ✅ {self.name_b} scores significantly higher (p < 0.05)")
        else:
            print(f"  ⚖️  No significant difference in scores (p = {p_value:.3f})")

        # Chi-square test for win rates
        wins = [[wins_a, len(self.results_a) - wins_a],
                [wins_b, len(self.results_b) - wins_b]]
        chi2, p_chi = stats.chi2_contingency(wins)[:2]

        print(f"\nWin Rate Comparison (chi-square):")
        print(f"  chi-square: {chi2:.4f}")
        print(f"  p-value: {p_chi:.6f}")

        if p_chi < 0.05:
            if wins_a > wins_b:
                print(f"  ✅ {self.name_a} wins significantly more (p < 0.05)")
            else:
                print(f"  ✅ {self.name_b} wins significantly more (p < 0.05)")
        else:
            print(f"  ⚖️  No significant difference in win rates (p = {p_chi:.3f})")

        # Time per Move comparison
        t_speed, p_speed = stats.ttest_ind(times_a, times_b)
        print(f"\nTime per Move Comparison (t-test):")
        print(f"  t-statistic: {t_speed:.4f}")
        print(f"  p-value: {p_speed:.6f}")

        if p_speed < 0.05:
            if np.mean(times_a) < np.mean(times_b):
                speedup = np.mean(times_b) / np.mean(times_a)
                print(f"  ⚡ {self.name_a} is {speedup:.1f}x faster (p < 0.05)")
            else:
                speedup = np.mean(times_a) / np.mean(times_b)
                print(f"  ⚡ {self.name_b} is {speedup:.1f}x faster (p < 0.05)")
        else:
            print(f"  ⚖️  No significant difference in time per move (p = {p_speed:.3f})")

        # Effect size (Cohen's d)
        pooled_std = np.sqrt((np.var(scores_a) + np.var(scores_b)) / 2)
        cohens_d = (np.mean(scores_a) - np.mean(scores_b)) / pooled_std

        print(f"\nEffect Size (Cohen's d): {cohens_d:.3f}")
        if abs(cohens_d) < 0.2:
            print("  → Negligible effect")
        elif abs(cohens_d) < 0.5:
            print("  → Small effect")
        elif abs(cohens_d) < 0.8:
            print("  → Medium effect")
        else:
            print("  → Large effect")

        # Overall recommendation
        print(f"\n{'='*70}")
        print("🎯 RECOMMENDATION")
        print(f"{'='*70}")

        score_winner = self.name_a if np.mean(scores_a) > np.mean(scores_b) else self.name_b
        speed_winner = self.name_a if np.mean(times_a) < np.mean(times_b) else self.name_b

        if score_winner == speed_winner:
            print(f"\n✅ {score_winner} is clearly superior (better scores AND faster)")
        else:
            print(f"\n⚖️  Trade-off detected:")
            print(f"  - {score_winner} has better game performance")
            print(f"  - {speed_winner} is faster")
            print(f"  Choose based on your priority (quality vs speed)")

        # Save results
        self.save_results()

    def save_results(self):
        """Save test results to JSON"""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"ab_test_{timestamp}.json"

        results = {
            'test_name': f"{self.name_a}_vs_{self.name_b}",
            'timestamp': timestamp,
            'games_per_ai': len(self.results_a),
            self.name_a: {
                'results': self.results_a,
                'summary': {
                    'avg_score': np.mean([r['score'] for r in self.results_a]),
                    'win_rate': sum(r['win'] for r in self.results_a) / len(self.results_a),
                    'avg_time_ms': np.mean([r['avg_move_time'] for r in self.results_a])
                }
            },
            self.name_b: {
                'results': self.results_b,
                'summary': {
                    'avg_score': np.mean([r['score'] for r in self.results_b]),
                    'win_rate': sum(r['win'] for r in self.results_b) / len(self.results_b),
                    'avg_time_ms': np.mean([r['avg_move_time'] for r in self.results_b])
                }
            }
        }

        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"\n💾 Results saved to {filename}")


def run_improvement_test():
    """Test challenger improvements against the champion"""

    # Current champion (established performer)
    champion_ai = rust_ai_2048.ChampionAI()

    # Challenger (for testing new improvements)
    challenger_ai = rust_ai_2048.ChallengerAI()

    # Run A/B test
    tester = ABTester(
        champion_ai,
        challenger_ai,
        name_a="Champion",
        name_b="Challenger"
    )

    # Run with sufficient games for statistical significance
    # Rule of thumb: need ~30 games minimum, 100+ better
    tester.run_test(games_per_ai=30)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        games = int(sys.argv[1])
    else:
        games = 30

    print(f"Running A/B test with {games} games per AI...")
    run_improvement_test()