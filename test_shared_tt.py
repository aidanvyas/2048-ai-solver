#!/usr/bin/env python3
"""
A/B Test: ChampionAI vs SharedTTChallenger
Tests if persistent transposition table improves performance
"""

import numpy as np
from scipy import stats
import json
import time
import random
from datetime import datetime

# Import the A/B testing framework
from ab_test_framework import Game2048, ABTester

# Import Rust AI implementations
import rust_ai_2048

def main():
    print("=" * 70)
    print("A/B TEST: ChampionAI vs SharedTTChallenger")
    print("=" * 70)
    print("\nObjective: Test if persistent transposition table improves performance")
    print("\nChanges in SharedTTChallenger:")
    print("  - Transposition table persists across moves within a game")
    print("  - TT is reset between games to avoid pollution")
    print("  - Same depth strategy as ChampionAI")
    print("\nExpected Impact:")
    print("  - Better cache hit rate → faster move times")
    print("  - Potentially better move quality from more complete search")
    print()

    # Create AI instances
    champion = rust_ai_2048.ChampionAI()
    challenger = rust_ai_2048.SharedTTChallenger()

    # Run A/B test with 30 games each
    tester = ABTester(
        champion,
        challenger,
        name_a="ChampionAI (fresh TT per move)",
        name_b="SharedTTChallenger (persistent TT)"
    )

    print("Starting 30 games per AI...")
    print("This will take approximately 10-15 minutes...")
    print()

    results = tester.run_test(games_per_ai=30)

    # Print detailed results
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)

    print(f"\nChampionAI (baseline):")
    print(f"  Average Score: {results['ChampionAI (fresh TT per move)']['summary']['avg_score']:.1f}")
    print(f"  Win Rate: {results['ChampionAI (fresh TT per move)']['summary']['win_rate']*100:.1f}%")
    print(f"  Avg Time/Move: {results['ChampionAI (fresh TT per move)']['summary']['avg_time_ms']:.2f}ms")

    print(f"\nSharedTTChallenger:")
    print(f"  Average Score: {results['SharedTTChallenger (persistent TT)']['summary']['avg_score']:.1f}")
    print(f"  Win Rate: {results['SharedTTChallenger (persistent TT)']['summary']['win_rate']*100:.1f}%")
    print(f"  Avg Time/Move: {results['SharedTTChallenger (persistent TT)']['summary']['avg_time_ms']:.2f}ms")

    # Calculate improvements
    score_improvement = (results['SharedTTChallenger (persistent TT)']['summary']['avg_score'] /
                        results['ChampionAI (fresh TT per move)']['summary']['avg_score'] - 1) * 100
    time_improvement = (results['ChampionAI (fresh TT per move)']['summary']['avg_time_ms'] /
                       results['SharedTTChallenger (persistent TT)']['summary']['avg_time_ms'] - 1) * 100

    print(f"\nImprovements:")
    print(f"  Score: {score_improvement:+.1f}%")
    print(f"  Speed: {time_improvement:+.1f}%")

    # Statistical analysis
    champion_scores = [g['score'] for g in results['ChampionAI (fresh TT per move)']['results']]
    challenger_scores = [g['score'] for g in results['SharedTTChallenger (persistent TT)']['results']]

    t_stat, p_value = stats.ttest_ind(champion_scores, challenger_scores)

    print(f"\nStatistical Significance:")
    print(f"  p-value: {p_value:.4f}")
    if p_value < 0.05:
        print(f"  ✅ STATISTICALLY SIGNIFICANT (p < 0.05)")
        if score_improvement > 0:
            print(f"  🏆 SharedTTChallenger is the NEW CHAMPION!")
        else:
            print(f"  ❌ SharedTTChallenger performed worse")
    else:
        print(f"  ⚠️  NOT statistically significant (p >= 0.05)")
        print(f"  Performance difference could be due to chance")

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"ab_test_shared_tt_{timestamp}.json"
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to: {filename}")

if __name__ == "__main__":
    main()
