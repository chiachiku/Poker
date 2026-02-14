#!/usr/bin/env python3
"""CLI verification script for poker equity calculator.

Usage:
    python3 cli.py --hero "Ah Ks" --board "2d 7d Jc"
    python3 cli.py --hero "Ad Kd" --board "Qh Jc Tc 9h"
    python3 cli.py --hero "Ah Kh"  # Preflop (no board)
"""

import argparse
from src.models.card import Card
from src.engine.equity import equity_vs_random


def parse_cards(card_string: str) -> list:
    """Parse space-separated card strings like 'Ah Ks' into Card list."""
    if not card_string:
        return []
    return [Card.from_string(s) for s in card_string.split()]


def format_equity(result: dict) -> str:
    """Format equity results as percentages."""
    win_pct = result['win'] * 100
    tie_pct = result['tie'] * 100
    lose_pct = result['lose'] * 100

    output = []
    output.append(f"Win:  {win_pct:6.2f}%")
    output.append(f"Tie:  {tie_pct:6.2f}%")
    output.append(f"Lose: {lose_pct:6.2f}%")
    output.append(f"Total equity: {win_pct + tie_pct/2:6.2f}%")

    return "\n".join(output)


def main():
    parser = argparse.ArgumentParser(
        description="Calculate poker equity vs random opponent hand.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # River equity
  python3 cli.py --hero "Ah Ks" --board "Qh Jc Tc 2d 3h"

  # Flop equity
  python3 cli.py --hero "Ad Kd" --board "Qh Jc Tc"

  # Preflop equity (Monte Carlo with 10k iterations)
  python3 cli.py --hero "Ah Kh"

  # Preflop with custom iterations
  python3 cli.py --hero "Ah Kh" --iterations 50000
        """
    )

    parser.add_argument(
        "--hero",
        required=True,
        help="Hero's 2 hole cards (e.g., 'Ah Ks')"
    )

    parser.add_argument(
        "--board",
        default="",
        help="Community cards: 0 (preflop), 3 (flop), 4 (turn), or 5 (river) cards (e.g., 'Qh Jc Tc')"
    )

    parser.add_argument(
        "--iterations",
        type=int,
        default=10000,
        help="Monte Carlo iterations for preflop (default: 10000)"
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducible preflop results (optional)"
    )

    args = parser.parse_args()

    # Parse cards
    try:
        hero_cards = parse_cards(args.hero)
        board_cards = parse_cards(args.board)
    except Exception as e:
        print(f"Error parsing cards: {e}")
        return 1

    # Validate input
    if len(hero_cards) != 2:
        print(f"Error: Hero must have exactly 2 cards, got {len(hero_cards)}")
        return 1

    if len(board_cards) > 5:
        print(f"Error: Board cannot have more than 5 cards, got {len(board_cards)}")
        return 1

    # Display input
    print("=" * 50)
    print("POKER EQUITY CALCULATOR")
    print("=" * 50)
    print(f"Hero:  {' '.join(str(c) for c in hero_cards)}")

    if board_cards:
        print(f"Board: {' '.join(str(c) for c in board_cards)}")
        street_names = {0: "preflop", 3: "flop", 4: "turn", 5: "river"}
        street = street_names.get(len(board_cards), f"{len(board_cards)} cards")
        print(f"Street: {street}")
    else:
        print("Board: (preflop)")
        print(f"Monte Carlo iterations: {args.iterations:,}")
        if args.seed is not None:
            print(f"Random seed: {args.seed}")

    print("-" * 50)

    # Calculate equity
    try:
        result = equity_vs_random(
            hero_cards,
            board_cards,
            mc_iters=args.iterations if not board_cards else None,
            seed=args.seed if not board_cards else None
        )

        # Display results
        print("\nEQUITY VS RANDOM OPPONENT:")
        print(format_equity(result))
        print("=" * 50)

        return 0

    except Exception as e:
        print(f"Error calculating equity: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
