#!/usr/bin/env python3
"""
Performance Profiler for 2048 AI
Identifies actual bottlenecks with detailed timing breakdown
"""

import time
import rust_ai_2048
import cProfile
import pstats
from functools import wraps
import numpy as np

class AIProfiler:
    """Profile AI performance with detailed breakdown"""

    def __init__(self, ai, ai_name):
        self.ai = ai
        self.ai_name = ai_name
        self.call_times = []

    def profile_single_moves(self, boards_and_names, iterations=10):
        """Profile individual move decisions across different board complexities"""
        print(f"🔍 PROFILING {self.ai_name}")
        print("=" * 50)

        for board_name, board in boards_and_names:
            print(f"\n📋 {board_name}:")

            # Time multiple iterations
            times = []
            for _ in range(iterations):
                start = time.perf_counter()
                move = self.ai.get_best_move(board)
                elapsed = time.perf_counter() - start
                times.append(elapsed * 1000)  # Convert to ms

            avg_time = np.mean(times)
            min_time = min(times)
            max_time = max(times)
            std_time = np.std(times)

            print(f"  Average: {avg_time:7.2f}ms")
            print(f"  Range:   {min_time:7.2f}ms - {max_time:7.2f}ms")
            print(f"  Std Dev: {std_time:7.2f}ms")
            print(f"  Move:    {move}")

            # Categorize performance
            if avg_time < 1:
                status = "✅ FAST"
            elif avg_time < 5:
                status = "🟡 OKAY"
            elif avg_time < 15:
                status = "🟠 SLOW"
            else:
                status = "🔴 VERY SLOW"

            print(f"  Status:  {status}")

        return True

    def profile_with_cprofile(self, board, output_file=None):
        """Deep profile using cProfile to find function-level bottlenecks"""
        print(f"\n🔬 DEEP PROFILING {self.ai_name} with cProfile")
        print("-" * 50)

        if output_file is None:
            output_file = f"{self.ai_name.lower()}_profile.prof"

        # Profile the AI move decision
        profiler = cProfile.Profile()
        profiler.enable()

        # Run multiple iterations for better statistics
        for _ in range(5):
            move = self.ai.get_best_move(board)

        profiler.disable()

        # Save and analyze results
        profiler.dump_stats(output_file)

        # Print top time-consuming functions
        stats = pstats.Stats(profiler)
        stats.sort_stats('cumulative')

        print(f"\n📊 TOP TIME-CONSUMING FUNCTIONS:")
        stats.print_stats(10)  # Top 10 functions

        return output_file

def create_test_boards():
    """Create test boards of varying complexity"""
    return [
        ("Early Game (Simple)", [[2, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]),

        ("Mid Game (Moderate)", [[32, 16, 8, 4], [16, 8, 4, 2], [0, 0, 0, 0], [0, 0, 0, 0]]),

        ("Late Game (Complex)", [[512, 256, 128, 64], [256, 128, 64, 32], [128, 64, 32, 16], [64, 32, 16, 0]]),

        ("Endgame (Very Complex)", [[1024, 512, 256, 128], [512, 256, 128, 64], [256, 128, 64, 32], [128, 64, 32, 16]]),

        ("Worst Case (Nearly Full)", [[2048, 1024, 512, 256], [1024, 512, 256, 128], [512, 256, 128, 64], [256, 128, 64, 0]]),
    ]

def compare_ai_performance(ai_classes, ai_names):
    """Compare performance across multiple AI implementations"""
    test_boards = create_test_boards()

    print("🏁 AI PERFORMANCE COMPARISON")
    print("=" * 60)

    # Test each board scenario
    for board_name, board in test_boards:
        print(f"\n🎮 {board_name}:")
        print("-" * 30)

        for ai_class, ai_name in zip(ai_classes, ai_names):
            ai = ai_class()

            # Time 10 iterations
            times = []
            for _ in range(10):
                start = time.perf_counter()
                move = ai.get_best_move(board)
                elapsed = time.perf_counter() - start
                times.append(elapsed * 1000)

            avg_time = np.mean(times)
            print(f"  {ai_name:<15}: {avg_time:6.2f}ms ({move})")

        print()

def main():
    """Main profiling routine"""
    print("🔬 2048 AI PERFORMANCE PROFILER")
    print("Identifying bottlenecks for optimization")
    print("=" * 60)

    # Create test scenarios
    test_boards = create_test_boards()

    # Profile ChampionAI in detail
    champion = rust_ai_2048.ChampionAI()
    profiler = AIProfiler(champion, "ChampionAI")

    # 1. Profile across different complexities
    profiler.profile_single_moves(test_boards)

    # 2. Deep profile the worst case (most complex board)
    worst_case_board = test_boards[-1][1]  # Nearly full board
    print(f"\n" + "="*60)
    print("🎯 DEEP PROFILING WORST CASE SCENARIO")
    print("="*60)

    profile_file = profiler.profile_with_cprofile(worst_case_board)

    print(f"\n💾 Detailed profile saved to: {profile_file}")
    print("\n🎯 OPTIMIZATION RECOMMENDATIONS:")
    print("Based on profiling results:")
    print("1. Focus on the slowest scenarios first")
    print("2. Look for functions taking >10% of total time")
    print("3. Optimize hot code paths identified by cProfile")
    print("4. Test each optimization incrementally")

    # Compare available AIs if multiple exist
    try:
        print(f"\n" + "="*60)
        print("⚖️  COMPARING AVAILABLE AI IMPLEMENTATIONS")
        print("="*60)

        ai_classes = [rust_ai_2048.ChampionAI]
        ai_names = ["ChampionAI"]

        # Add other AIs if available
        try:
            rust_ai_2048.ChallengerAI()
            ai_classes.append(rust_ai_2048.ChallengerAI)
            ai_names.append("ChallengerAI")
        except: pass

        try:
            rust_ai_2048.FastAI()
            ai_classes.append(rust_ai_2048.FastAI)
            ai_names.append("FastAI")
        except: pass

        if len(ai_classes) > 1:
            compare_ai_performance(ai_classes, ai_names)
        else:
            print("Only ChampionAI available for comparison")

    except Exception as e:
        print(f"Comparison error: {e}")

if __name__ == "__main__":
    main()