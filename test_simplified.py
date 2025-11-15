#!/usr/bin/env python3
"""
Test SimplifiedGeniusAI vs ChampionAI
Snake + Smoothness only vs Pure Snake Pattern
"""

import rust_ai_2048
import time
from ab_test_framework import ABTester

def quick_comparison():
    """Quick timing and decision comparison"""
    print("🔍 SIMPLIFIED GENIUS AI DEBUG TEST")
    print("=" * 60)
    print("ChampionAI (Snake only) vs SimplifiedGeniusAI (Snake + Smoothness)")
    print("=" * 60)

    champion = rust_ai_2048.ChampionAI()
    simplified = rust_ai_2048.SimplifiedGeniusAI()

    # Test boards
    test_boards = [
        ("Early Game", [[2, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]),
        ("Mid Game", [[32, 16, 8, 4], [16, 8, 4, 2], [0, 0, 0, 0], [0, 0, 0, 0]]),
        ("Late Game", [[512, 256, 128, 64], [256, 128, 64, 32], [128, 64, 32, 16], [64, 32, 16, 0]]),
        ("Endgame", [[2048, 1024, 512, 256], [1024, 512, 256, 128], [512, 256, 128, 64], [256, 128, 64, 0]])
    ]

    print("📊 MOVE TIMING & DECISION COMPARISON:")
    print("-" * 50)

    for board_name, board in test_boards:
        print(f"\n🎮 {board_name}:")

        # Time ChampionAI
        times = []
        for _ in range(5):
            start = time.perf_counter()
            champion_move = champion.get_best_move(board)
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)
        champion_avg = sum(times) / len(times)

        # Time SimplifiedGeniusAI
        times = []
        for _ in range(5):
            start = time.perf_counter()
            simplified_move = simplified.get_best_move(board)
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)
        simplified_avg = sum(times) / len(times)

        print(f"  ChampionAI:      {champion_move} ({champion_avg:.2f}ms)")
        print(f"  SimplifiedAI:    {simplified_move} ({simplified_avg:.2f}ms)")

        # Analysis
        if champion_move != simplified_move:
            print(f"  ❗ DIFFERENT MOVES")
        else:
            print(f"  ✅ Same move choice")

        speedup = simplified_avg / champion_avg
        if speedup > 2:
            print(f"  ⚠️  SimplifiedAI is {speedup:.1f}x slower")
        elif speedup > 1.5:
            print(f"  🟡 SimplifiedAI is {speedup:.1f}x slower")
        else:
            print(f"  ✅ SimplifiedAI speed: {speedup:.1f}x")

def full_ab_test():
    """Run complete A/B test"""
    print(f"\n" + "=" * 60)
    print("🔬 FULL A/B TEST: ChampionAI vs SimplifiedGeniusAI")
    print("=" * 60)

    champion = rust_ai_2048.ChampionAI()
    simplified = rust_ai_2048.SimplifiedGeniusAI()

    tester = ABTester(
        champion,
        simplified,
        name_a='ChampionAI (Snake Only)',
        name_b='SimplifiedGeniusAI (Snake + Smoothness)'
    )

    print("Running 15 games per AI for quick assessment...")
    tester.run_test(games_per_ai=15)

if __name__ == "__main__":
    quick_comparison()
    full_ab_test()