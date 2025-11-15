#!/usr/bin/env python3
"""
Debug Multi-Heuristic Evaluation
Identifies which heuristics are causing the 55% performance drop
"""

import rust_ai_2048
import time

def test_individual_heuristics():
    """Test each heuristic component individually to find the problem"""
    print("🔍 DEBUGGING MULTI-HEURISTIC EVALUATION FAILURE")
    print("=" * 60)
    print("GeniusAI: 19,523 avg (55% WORSE than ChampionAI's 43,399)")
    print("Analyzing individual heuristic components...\n")

    # Test board scenarios
    test_boards = [
        ("Early Game", [[2, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]),
        ("Mid Game", [[32, 16, 8, 4], [16, 8, 4, 2], [0, 0, 0, 0], [0, 0, 0, 0]]),
        ("Late Game", [[512, 256, 128, 64], [256, 128, 64, 32], [128, 64, 32, 16], [64, 32, 16, 0]]),
        ("Endgame", [[2048, 1024, 512, 256], [1024, 512, 256, 128], [512, 256, 128, 64], [256, 128, 64, 0]])
    ]

    # Initialize AIs
    champion = rust_ai_2048.ChampionAI()
    genius = rust_ai_2048.GeniusAI()

    print("📊 MOVE DECISION COMPARISON:")
    print("-" * 40)

    for board_name, board in test_boards:
        print(f"\n🎮 {board_name}:")

        # Time and get moves from each AI
        start = time.perf_counter()
        champion_move = champion.get_best_move(board)
        champion_time = (time.perf_counter() - start) * 1000

        start = time.perf_counter()
        genius_move = genius.get_best_move(board)
        genius_time = (time.perf_counter() - start) * 1000

        print(f"  ChampionAI: {champion_move} ({champion_time:.2f}ms)")
        print(f"  GeniusAI:   {genius_move} ({genius_time:.2f}ms)")

        if champion_move != genius_move:
            print(f"  ❗ DIFFERENT MOVES - This could explain performance gap!")
        else:
            print(f"  ✅ Same move choice")

        if genius_time > champion_time * 2:
            print(f"  ⚠️  GeniusAI is {genius_time/champion_time:.1f}x slower")

def analyze_evaluation_components():
    """Check if we can isolate evaluation component issues"""
    print(f"\n🔬 EVALUATION ANALYSIS:")
    print("-" * 30)

    # This would require exposing evaluation functions from Rust
    # For now, let's focus on move consistency and timing

    genius = rust_ai_2048.GeniusAI()
    champion = rust_ai_2048.ChampionAI()

    # Test the most complex board multiple times
    complex_board = [[2048, 1024, 512, 256], [1024, 512, 256, 128], [512, 256, 128, 64], [256, 128, 64, 0]]

    print("Testing move consistency on complex board:")

    genius_moves = []
    champion_moves = []

    for i in range(10):
        genius_moves.append(genius.get_best_move(complex_board))
        champion_moves.append(champion.get_best_move(complex_board))

    genius_consistency = len(set(genius_moves))
    champion_consistency = len(set(champion_moves))

    print(f"  GeniusAI consistency: {genius_consistency} unique moves out of 10")
    print(f"  ChampionAI consistency: {champion_consistency} unique moves out of 10")

    if genius_consistency > champion_consistency:
        print("  ❗ GeniusAI is less consistent - evaluation might be unstable")

    print(f"  GeniusAI primary move: {max(set(genius_moves), key=genius_moves.count)}")
    print(f"  ChampionAI primary move: {max(set(champion_moves), key=champion_moves.count)}")

def suggest_fixes():
    """Based on analysis, suggest what to fix"""
    print(f"\n🎯 LIKELY CAUSES & FIXES:")
    print("=" * 40)
    print("1. 🔴 HEURISTIC CONFLICTS")
    print("   - Multiple heuristics pulling in different directions")
    print("   - Solution: Test each heuristic individually")
    print()
    print("2. 🔴 BAD WEIGHTS")
    print("   - Weight ratios might favor wrong aspects")
    print("   - Solution: Revert to snake-only + gradually add others")
    print()
    print("3. 🔴 IMPLEMENTATION BUGS")
    print("   - Calculation errors in new heuristic functions")
    print("   - Solution: Add debug prints to trace evaluation scores")
    print()
    print("4. 🔴 OVER-OPTIMIZATION")
    print("   - Simple snake pattern might already be optimal")
    print("   - Solution: Try smaller, targeted improvements")
    print()
    print("📋 RECOMMENDED NEXT STEP:")
    print("Create SimplifiedGeniusAI with ONLY snake + smoothness (no other heuristics)")
    print("If that works, gradually add one heuristic at a time")

if __name__ == "__main__":
    test_individual_heuristics()
    analyze_evaluation_components()
    suggest_fixes()