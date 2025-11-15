#!/usr/bin/env python3
"""
Rust-Level Profiler for 2048 AI
Measures time spent in different operations within the AI
"""

import time
import rust_ai_2048
import numpy as np

class RustProfiler:
    """Profile specific operations within the AI"""

    def __init__(self):
        self.ai = rust_ai_2048.ChampionAI()

    def profile_operation_breakdown(self, board, iterations=50):
        """
        Profile different aspects by isolating operations
        This helps identify which specific parts are slow
        """
        print("🔬 RUST-LEVEL OPERATION PROFILING")
        print("=" * 50)
        print(f"Board complexity: {self.get_board_complexity(board)}")
        print(f"Iterations: {iterations}")
        print()

        # We can't directly profile inside Rust, but we can:
        # 1. Test different board states to isolate bottlenecks
        # 2. Compare with simplified versions
        # 3. Measure specific scenarios

        # 1. Profile by search depth (simulate depth impact)
        print("📊 DEPTH IMPACT ANALYSIS:")
        self.profile_depth_impact(board)

        # 2. Profile by board complexity
        print("\n📊 COMPLEXITY IMPACT ANALYSIS:")
        self.profile_complexity_impact()

        # 3. Profile move ordering impact
        print("\n📊 MOVE ORDERING ANALYSIS:")
        self.profile_move_patterns(board)

    def profile_depth_impact(self, board):
        """
        Understand how search depth affects performance
        This tells us if expectimax recursion is the bottleneck
        """
        empty_count = sum(row.count(0) for row in board)

        print(f"  Empty tiles: {empty_count}")

        # Based on ChampionAI logic, predict depth:
        if empty_count <= 2:
            predicted_depth = 9
        elif empty_count <= 4:
            predicted_depth = 8
        elif empty_count <= 6:
            predicted_depth = 7
        elif empty_count <= 9:
            predicted_depth = 6
        else:
            predicted_depth = 5

        print(f"  Predicted depth: {predicted_depth}")

        # Time the actual call
        times = []
        for _ in range(10):
            start = time.perf_counter()
            move = self.ai.get_best_move(board)
            elapsed = time.perf_counter() - start
            times.append(elapsed * 1000)

        avg_time = np.mean(times)
        print(f"  Average time: {avg_time:.2f}ms")
        print(f"  Time per depth level: {avg_time/predicted_depth:.2f}ms")

        # Complexity factor (rough estimate)
        branching_factor = min(4, empty_count)  # Max 4 moves
        search_nodes = branching_factor ** predicted_depth
        print(f"  Est. search nodes: {search_nodes:,}")
        print(f"  Time per 1000 nodes: {(avg_time/search_nodes)*1000:.3f}ms")

    def profile_complexity_impact(self):
        """
        Test boards of increasing complexity to isolate evaluation cost
        """
        test_cases = [
            ("Very Simple", [[2, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]),
            ("Simple", [[4, 2, 0, 0], [2, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]),
            ("Moderate", [[32, 16, 8, 4], [16, 8, 4, 2], [8, 4, 2, 0], [4, 2, 0, 0]]),
            ("Complex", [[128, 64, 32, 16], [64, 32, 16, 8], [32, 16, 8, 4], [16, 8, 4, 0]]),
            ("Very Complex", [[512, 256, 128, 64], [256, 128, 64, 32], [128, 64, 32, 16], [64, 32, 16, 0]]),
        ]

        for name, board in test_cases:
            empty_count = sum(row.count(0) for row in board)
            max_tile = max(max(row) for row in board)

            # Time this complexity level
            times = []
            for _ in range(5):
                start = time.perf_counter()
                move = self.ai.get_best_move(board)
                elapsed = time.perf_counter() - start
                times.append(elapsed * 1000)

            avg_time = np.mean(times)
            complexity_score = max_tile * (16 - empty_count)

            print(f"  {name:<12}: {avg_time:6.2f}ms (max:{max_tile:4d}, empty:{empty_count:2d}, complex:{complexity_score:5d})")

    def profile_move_patterns(self, board):
        """
        Understanding which types of moves are slower to evaluate
        """
        print("  Testing move evaluation consistency...")

        # Test the same board multiple times to see variance
        times = []
        moves = []
        for _ in range(20):
            start = time.perf_counter()
            move = self.ai.get_best_move(board)
            elapsed = time.perf_counter() - start
            times.append(elapsed * 1000)
            moves.append(move)

        avg_time = np.mean(times)
        std_time = np.std(times)
        unique_moves = set(moves)

        print(f"  Average time: {avg_time:.2f}ms")
        print(f"  Std deviation: {std_time:.2f}ms ({std_time/avg_time*100:.1f}%)")
        print(f"  Move consistency: {len(unique_moves)} unique moves out of 20 calls")
        print(f"  Primary move: {max(set(moves), key=moves.count)}")

        if std_time / avg_time > 0.1:  # >10% variance
            print("  ⚠️  High variance suggests non-deterministic bottlenecks")
        else:
            print("  ✅ Consistent performance")

    def get_board_complexity(self, board):
        """Calculate a complexity score for the board"""
        empty_count = sum(row.count(0) for row in board)
        max_tile = max(max(row) for row in board)
        unique_tiles = len(set(val for row in board for val in row if val > 0))

        # Higher complexity = more tiles, higher values, fewer empties
        complexity = max_tile * unique_tiles * (16 - empty_count)
        return complexity

    def suggest_optimizations(self, board):
        """Based on profiling, suggest specific optimizations"""
        print("\n🎯 OPTIMIZATION SUGGESTIONS:")
        print("-" * 30)

        empty_count = sum(row.count(0) for row in board)
        max_tile = max(max(row) for row in board)

        if empty_count <= 3 and max_tile >= 512:
            print("1. 🔴 ENDGAME SCENARIO - Consider depth reduction")
            print("   - Current depth likely 8-9, could reduce to 6-7")
            print("   - Focus on alpha-beta pruning improvements")

        if max_tile >= 256:
            print("2. 🟡 HIGH-VALUE TILES - Consider evaluation caching")
            print("   - Snake pattern weights could be precomputed")
            print("   - Position evaluation could use lookup tables")

        print("3. 🔧 GENERAL OPTIMIZATIONS:")
        print("   - Better move ordering (score-based)")
        print("   - Transposition table optimization")
        print("   - Early termination on obvious moves")

def main():
    """Profile the ChampionAI to find bottlenecks"""
    profiler = RustProfiler()

    # Test on the worst-case scenario that showed 33ms
    worst_case_board = [
        [2048, 1024, 512, 256],
        [1024, 512, 256, 128],
        [512, 256, 128, 64],
        [256, 128, 64, 0]
    ]

    profiler.profile_operation_breakdown(worst_case_board)
    profiler.suggest_optimizations(worst_case_board)

if __name__ == "__main__":
    main()