"""Poker Companion — Streamlit UI.

Minimal web interface for Texas Hold'em analysis:
- Input: hole cards, community cards, pot/bet amounts
- Output: equity, outs, hand distribution, rule-based advice
"""
import streamlit as st
from src.models.card import Card
from src.engine.equity import equity_vs_random
from src.engine.outs import detect_draws
from src.engine.distribution import hand_distribution
from src.engine.odds import pot_odds, ev_call
from src.advisor.advisor import get_advice


# ──────────────────────────────────────────────
# Page config
# ──────────────────────────────────────────────

st.set_page_config(
    page_title="Poker Companion",
    page_icon="🃏",
    layout="wide",
)

st.title("🃏 Poker Companion")
st.caption("Texas Hold'em analysis: equity, outs, distribution & advice")


# ──────────────────────────────────────────────
# Helper functions
# ──────────────────────────────────────────────

def parse_cards(text: str) -> list:
    """Parse a space/comma separated card string into Card objects."""
    text = text.strip()
    if not text:
        return []
    tokens = text.replace(",", " ").split()
    cards = []
    for t in tokens:
        t = t.strip()
        if t:
            cards.append(Card.from_string(t))
    return cards


def validate_cards(hero_text: str, board_text: str):
    """Validate card inputs. Returns (hero_cards, board_cards, error_msg)."""
    try:
        hero = parse_cards(hero_text)
    except (ValueError, KeyError) as e:
        return None, None, f"Hero cards error: {e}"

    try:
        board = parse_cards(board_text)
    except (ValueError, KeyError) as e:
        return None, None, f"Board cards error: {e}"

    if len(hero) != 2:
        return None, None, "Hero must have exactly 2 cards."

    if len(board) not in (0, 3, 4, 5):
        return None, None, "Board must have 0, 3, 4, or 5 cards."

    # Check for duplicates
    all_cards = hero + board
    all_strs = [repr(c) for c in all_cards]
    if len(set(all_strs)) != len(all_strs):
        return None, None, "Duplicate cards detected."

    return hero, board, None


# ──────────────────────────────────────────────
# Sidebar: inputs
# ──────────────────────────────────────────────

with st.sidebar:
    st.header("Card Input")
    st.markdown(
        "**Format:** Rank + Suit  \n"
        "Ranks: `2 3 4 5 6 7 8 9 T J Q K A`  \n"
        "Suits: `h` ♥ `d` ♦ `c` ♣ `s` ♠  \n"
        "Example: `Ah Kd` = A♥ K♦"
    )

    hero_text = st.text_input(
        "Your hole cards (2 cards)",
        value="",
        placeholder="e.g. Ah Kd",
    )

    board_text = st.text_input(
        "Community cards (0, 3, 4, or 5)",
        value="",
        placeholder="e.g. Qh Jc Tc",
    )

    st.divider()
    st.header("Pot & Bet (optional)")

    pot_size = st.number_input(
        "Pot size",
        min_value=0.0,
        value=0.0,
        step=10.0,
        format="%.1f",
    )

    call_amt = st.number_input(
        "Call amount",
        min_value=0.0,
        value=0.0,
        step=5.0,
        format="%.1f",
    )

    st.divider()
    analyze_btn = st.button("Analyze", type="primary", use_container_width=True)


# ──────────────────────────────────────────────
# Main content
# ──────────────────────────────────────────────

if not analyze_btn:
    st.info("Enter your hole cards and community cards in the sidebar, then click **Analyze**.")
    st.stop()

# Validate
hero_cards, board_cards, error = validate_cards(hero_text, board_text)
if error:
    st.error(error)
    st.stop()

# Determine optional pot info
pot_val = pot_size if pot_size > 0 else None
call_val = call_amt if call_amt > 0 else None

street_labels = {0: "Preflop", 3: "Flop", 4: "Turn", 5: "River"}
street = street_labels.get(len(board_cards), "Unknown")

# Display parsed cards
hero_display = " ".join(repr(c) for c in hero_cards)
board_display = " ".join(repr(c) for c in board_cards) if board_cards else "—"
st.markdown(f"**Hero:** `{hero_display}` | **Board:** `{board_display}` | **Street:** {street}")
st.divider()

# ──── Compute everything ────

with st.spinner("Calculating..."):
    # Equity
    equity_result = equity_vs_random(hero_cards, board_cards, seed=42)
    equity = equity_result['win'] + equity_result['tie'] / 2

    # Outs (only meaningful on flop/turn)
    draws = detect_draws(hero_cards, board_cards)

    # Distribution
    dist = hand_distribution(hero_cards, board_cards, seed=42)

    # Advice
    advice = get_advice(
        hero_cards, board_cards,
        pot=pot_val, call_amount=call_val,
        seed=42,
    )

    # Pot odds (if applicable)
    po_info = None
    if pot_val and call_val and call_val > 0:
        po = pot_odds(pot_val, call_val)
        ev = ev_call(pot_val, call_val, equity)
        po_info = {'pot_odds': po, 'ev': ev}


# ──────────────────────────────────────────────
# Layout: 3 columns
# ──────────────────────────────────────────────

col1, col2, col3 = st.columns(3)

# ──── Column 1: Equity ────
with col1:
    st.subheader("Equity")

    eq_pct = equity * 100
    win_pct = equity_result['win'] * 100
    tie_pct = equity_result['tie'] * 100
    lose_pct = equity_result['lose'] * 100

    st.metric("Total Equity", f"{eq_pct:.1f}%")

    st.markdown(
        f"- Win: **{win_pct:.1f}%**\n"
        f"- Tie: **{tie_pct:.1f}%**\n"
        f"- Lose: **{lose_pct:.1f}%**"
    )

    # Pot odds section
    if po_info:
        st.divider()
        st.markdown("**Pot Odds**")
        po_pct = po_info['pot_odds'] * 100
        ev_val = po_info['ev']
        ev_color = "green" if ev_val > 0 else "red"
        st.markdown(f"Need: **{po_pct:.1f}%** equity to call")
        st.markdown(f"EV(call): **:{ev_color}[{ev_val:+.1f}]**")


# ──── Column 2: Outs & Distribution ────
with col2:
    st.subheader("Draws & Outs")

    if len(board_cards) in (3, 4):
        total_outs = draws['total_outs']
        st.metric("Total Outs", total_outs)

        if draws['flush_draw']:
            fd = draws['flush_draw']
            st.markdown(f"- Flush draw: **{fd['outs']} outs**")

        for sd in draws['straight_draws']:
            label = "OESD" if sd['type'] == 'oesd' else "Gutshot"
            st.markdown(f"- {label}: **{sd['outs']} outs**")

        if total_outs == 0:
            st.markdown("_No draws detected._")
    else:
        st.markdown("_Draws are shown on flop/turn only._")

    st.divider()
    st.subheader("Hand Distribution")

    if dist:
        # Show as a nice table
        dist_display = {
            'straight_flush': 'Straight Flush',
            'four_of_a_kind': 'Four of a Kind',
            'full_house': 'Full House',
            'flush': 'Flush',
            'straight': 'Straight',
            'three_of_a_kind': 'Three of a Kind',
            'two_pair': 'Two Pair',
            'one_pair': 'One Pair',
            'high_card': 'High Card',
        }

        for key, label in dist_display.items():
            if key in dist:
                pct = dist[key] * 100
                st.markdown(f"- {label}: **{pct:.1f}%**")


# ──── Column 3: Advice ────
with col3:
    st.subheader("Advice")

    action = advice['action'].upper()
    confidence = advice['confidence']

    # Color-code the action
    action_colors = {
        'RAISE': '🟢',
        'CALL': '🟡',
        'FOLD': '🔴',
    }
    icon = action_colors.get(action, '')

    st.markdown(f"### {icon} {action}")
    st.markdown(f"Confidence: **{confidence}**")

    if advice['bet_sizing'] is not None:
        sizing_pct = advice['bet_sizing'] * 100
        st.markdown(f"Suggested bet: **{sizing_pct:.0f}% of pot**")

    st.divider()
    st.markdown("**Rationale:**")
    for point in advice['rationale']:
        st.markdown(f"- {point}")
