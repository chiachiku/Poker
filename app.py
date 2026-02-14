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

def init_card_picker_state():
    """Initialize session state for card picker."""
    if 'hero_cards_selected' not in st.session_state:
        st.session_state.hero_cards_selected = []
    if 'board_cards_selected' not in st.session_state:
        st.session_state.board_cards_selected = []

# Initialize card picker state
init_card_picker_state()

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


# ──────────────────────────────────────────────
# Card Grid Picker Functions
# ──────────────────────────────────────────────

def get_all_selected_cards() -> set:
    """Return set of all selected cards (hero + board)."""
    return set(
        st.session_state.hero_cards_selected +
        st.session_state.board_cards_selected
    )


def render_card_button(card_str: str, context: str, max_cards: int):
    """Render a single card button with selection logic.

    Args:
        card_str: Card string like 'Ah', 'Kd'
        context: 'hero' or 'board'
        max_cards: Maximum cards allowed (2 for hero, 5 for board)
    """
    all_selected = get_all_selected_cards()
    context_key = f'{context}_cards_selected'
    current_selected = st.session_state[context_key]

    # Determine button state
    is_selected_here = card_str in current_selected
    is_selected_elsewhere = card_str in all_selected and not is_selected_here
    at_max = len(current_selected) >= max_cards

    disabled = is_selected_elsewhere or (at_max and not is_selected_here)
    button_type = 'primary' if is_selected_here else 'secondary'
    label = f"✓{card_str[0]}" if is_selected_here else card_str[0]

    # Render button
    if st.button(
        label,
        key=f"card_{context}_{card_str}",
        disabled=disabled,
        type=button_type,
        use_container_width=True
    ):
        # Toggle selection
        if is_selected_here:
            current_selected.remove(card_str)
        else:
            current_selected.append(card_str)
        st.rerun()


def render_card_grid(context: str, max_cards: int):
    """Render 52-card grid for selection.

    Args:
        context: 'hero' or 'board'
        max_cards: Maximum cards allowed (2 or 5)
    """
    SUITS = ['h', 'd', 'c', 's']
    SUIT_SYMBOLS = {'h': '♥', 'd': '♦', 'c': '♣', 's': '♠'}
    SUIT_COLORS = {'h': 'red', 'd': 'red', 'c': 'black', 's': 'black'}
    RANKS = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']

    current_count = len(st.session_state[f'{context}_cards_selected'])
    st.caption(f"({current_count}/{max_cards} selected)")

    for suit in SUITS:
        suit_symbol = SUIT_SYMBOLS[suit]
        suit_color = SUIT_COLORS[suit]

        # Row header with colored suit symbol
        col_label, *cols = st.columns([1, *([1]*13)])
        with col_label:
            st.markdown(
                f"<div style='text-align:center;font-size:18px;color:{suit_color};'>{suit_symbol}</div>",
                unsafe_allow_html=True
            )

        # Render 13 card buttons for this suit
        for idx, rank_char in enumerate(RANKS):
            card_str = f"{rank_char}{suit}"
            with cols[idx]:
                render_card_button(card_str, context, max_cards)

    # Show selected cards preview
    selected = st.session_state[f'{context}_cards_selected']
    if selected:
        preview = " ".join(selected)
        st.markdown(f"**Selected:** `{preview}`")


def cards_selected_to_text(context: str) -> str:
    """Convert selected cards to text format for validation.

    Args:
        context: 'hero' or 'board'

    Returns:
        Space-separated card string, e.g., "Ah Kd"
    """
    return " ".join(st.session_state[f'{context}_cards_selected'])


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
    st.header("🃏 Select Cards")

    # ── Hero Cards Grid ────
    st.markdown("### Hero Cards")
    render_card_grid('hero', max_cards=2)

    st.divider()

    # ── Board Cards Grid ────
    st.markdown("### Board Cards")
    render_card_grid('board', max_cards=5)

    st.divider()

    # ── Clear All Button ────
    if st.button("🗑️ Clear All Cards", use_container_width=True):
        st.session_state.hero_cards_selected = []
        st.session_state.board_cards_selected = []
        st.rerun()

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
    st.info("Select your hole cards and community cards in the sidebar, then click **Analyze**.")
    st.stop()

# Convert grid selections to text format for validation
hero_text = cards_selected_to_text('hero')
board_text = cards_selected_to_text('board')

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
