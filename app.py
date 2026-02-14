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
    if 'current_street' not in st.session_state:
        st.session_state.current_street = 'preflop'  # preflop, flop, turn, river
    if 'flop_cards' not in st.session_state:
        st.session_state.flop_cards = []
    if 'turn_card' not in st.session_state:
        st.session_state.turn_card = None
    if 'river_card' not in st.session_state:
        st.session_state.river_card = None

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


def get_card_display_info(card_str: str) -> dict:
    """Get display information for a card.

    Args:
        card_str: Card string like 'Ah', 'Kd', 'Tc'

    Returns:
        Dict with rank_display, suit_symbol, and suit_color
    """
    rank = card_str[0].upper()
    suit = card_str[1].lower()

    # Rank display (10 instead of T for clarity)
    rank_display = '10' if rank == 'T' else rank

    # Suit symbols and colors
    SUIT_INFO = {
        'h': {'symbol': '♥', 'color': '#dc3545'},  # Red hearts
        'd': {'symbol': '♦', 'color': '#dc3545'},  # Red diamonds
        'c': {'symbol': '♣', 'color': '#212529'},  # Black clubs
        's': {'symbol': '♠', 'color': '#212529'},  # Black spades
    }

    suit_info = SUIT_INFO[suit]

    return {
        'rank_display': rank_display,
        'suit_symbol': suit_info['symbol'],
        'suit_color': suit_info['color']
    }


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

    # Only disable if selected in another context (hero/board)
    disabled = is_selected_elsewhere

    # Get card display info
    card_info = get_card_display_info(card_str)
    rank = card_info['rank_display']
    suit_symbol = card_info['suit_symbol']
    suit_color = card_info['suit_color']

    # Determine styling based on state
    if is_selected_here:
        border = '4px solid #28a745'
        bg_color = '#d4edda'
        shadow = '0 4px 8px rgba(40, 167, 69, 0.3)'
        opacity = '1.0'
        cursor = 'pointer'
    elif disabled:
        border = '2px solid #dee2e6'
        bg_color = '#f1f3f5'
        shadow = 'none'
        opacity = '0.4'
        cursor = 'not-allowed'
    else:
        border = '2px solid #ced4da'
        bg_color = '#ffffff'
        shadow = '0 2px 4px rgba(0,0,0,0.1)'
        opacity = '1.0'
        cursor = 'pointer'

    # Button key and label (no checkmark, color shows selection)
    button_key = f"card_{context}_{card_str}"
    button_label = f"{rank}\n{suit_symbol}"

    # Style button to look like card
    st.markdown(f"""
    <style>
        button[data-testid="baseButton"][key*="{button_key}"] {{
            background: {bg_color} !important;
            border: {border} !important;
            border-radius: 8px !important;
            box-shadow: {shadow} !important;
            opacity: {opacity} !important;
            transition: all 0.2s ease !important;
            padding: 8px !important;
            min-height: 80px !important;
            color: {suit_color} !important;
            font-size: 24px !important;
            font-weight: bold !important;
            white-space: pre-line !important;
            cursor: {cursor} !important;
        }}
    </style>
    """, unsafe_allow_html=True)

    if st.button(
        button_label,
        key=button_key,
        disabled=disabled,
        type='primary' if is_selected_here else 'secondary',
        use_container_width=True
    ):
        # Smart selection logic
        if is_selected_here:
            # Deselect if already selected
            current_selected.remove(card_str)
        elif at_max:
            # At max capacity - use smart replacement
            suit = card_str[1].lower()

            # Check if same suit already selected
            same_suit_card = None
            for c in current_selected:
                if c[1].lower() == suit:
                    same_suit_card = c
                    break

            if same_suit_card:
                # Replace same suit card
                current_selected.remove(same_suit_card)
                current_selected.append(card_str)
            else:
                # Replace oldest card (first in list)
                current_selected.pop(0)
                current_selected.append(card_str)
        else:
            # Normal selection
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
# Main content - Progressive Game Flow
# ──────────────────────────────────────────────

# Step 1: Select Hero Cards (Preflop)
st.header("🎴 Step 1: Your Hole Cards")
render_card_grid('hero', max_cards=2)

# Auto-analyze when hero cards are selected
hero_count = len(st.session_state.hero_cards_selected)
if hero_count == 2:
    st.success(f"✅ Selected: {' '.join(st.session_state.hero_cards_selected)}")

    # Preflop Analysis
    st.markdown("---")
    st.subheader("📊 Preflop Analysis")

    hero_cards = parse_cards(cards_selected_to_text('hero'))
    board_cards = []

    with st.spinner("Calculating preflop equity..."):
        equity_result = equity_vs_random(hero_cards, board_cards, mc_iters=5000, seed=42)
        equity = equity_result['win'] + equity_result['tie'] / 2

        advice = get_advice(hero_cards, board_cards, pot=None, call_amount=None, seed=42)

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Equity vs Random", f"{equity*100:.1f}%")
        win_pct = equity_result['win'] * 100
        st.caption(f"Win: {win_pct:.1f}% | Tie: {equity_result['tie']*100:.1f}% | Lose: {equity_result['lose']*100:.1f}%")

    with col2:
        action = advice['action'].upper()
        action_icon = {'RAISE': '🟢', 'CALL': '🟡', 'FOLD': '🔴'}.get(action, '')
        st.markdown(f"### {action_icon} {action}")
        st.caption(f"Confidence: {advice['confidence']}")

    st.markdown("**Rationale:**")
    for point in advice['rationale']:
        st.markdown(f"- {point}")

    # Next step button
    st.markdown("---")
    if st.button("🃏 Deal Flop (3 cards)", type="primary", use_container_width=True):
        st.session_state.current_street = 'flop'
        st.rerun()

elif hero_count < 2:
    st.info(f"👆 Select {2 - hero_count} more card(s) to continue")

# Step 2: Flop (only show if preflop complete)
if st.session_state.current_street in ['flop', 'turn', 'river'] and hero_count == 2:
    st.markdown("---")
    st.header("🃏 Step 2: Flop (3 cards)")

    # Track flop cards (use board_cards_selected length directly)
    flop_count = len(st.session_state.board_cards_selected)

    if flop_count < 3:
        st.info(f"Select {3 - flop_count} more card(s) for the flop")
        # Continue showing card grid for board cards
        if flop_count == 0:
            render_card_grid('board', max_cards=3)

    if len(st.session_state.board_cards_selected) >= 3:
        board_text = cards_selected_to_text('board')
        board_cards = parse_cards(board_text)[:3]  # Only first 3 cards

        st.success(f"✅ Flop: {' '.join([repr(c) for c in board_cards])}")

        # Flop Analysis
        st.subheader("📊 Flop Analysis")
        with st.spinner("Calculating flop equity..."):
            equity_result = equity_vs_random(hero_cards, board_cards, seed=42)
            equity = equity_result['win'] + equity_result['tie'] / 2
            draws = detect_draws(hero_cards, board_cards)
            advice = get_advice(hero_cards, board_cards, pot=None, call_amount=None, seed=42)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Equity", f"{equity*100:.1f}%")
        with col2:
            st.metric("Outs", draws['total_outs'])
        with col3:
            action = advice['action'].upper()
            action_icon = {'RAISE': '🟢', 'CALL': '🟡', 'FOLD': '🔴'}.get(action, '')
            st.markdown(f"### {action_icon} {action}")

        # Next step
        st.markdown("---")
        if st.session_state.current_street == 'flop':
            if st.button("🃏 Deal Turn (1 card)", type="primary", use_container_width=True):
                st.session_state.current_street = 'turn'
                st.rerun()

# Step 3: Turn
if st.session_state.current_street in ['turn', 'river'] and len(st.session_state.board_cards_selected) >= 3:
    st.markdown("---")
    st.header("🃏 Step 3: Turn (1 card)")

    if len(st.session_state.board_cards_selected) < 4:
        st.info("Select 1 more card for the turn")
        render_card_grid('board', max_cards=4)

    if len(st.session_state.board_cards_selected) >= 4:
        board_cards = parse_cards(cards_selected_to_text('board'))[:4]
        st.success(f"✅ Turn: {repr(board_cards[3])}")

        # Turn Analysis
        st.subheader("📊 Turn Analysis")
        with st.spinner("Calculating turn equity..."):
            equity_result = equity_vs_random(hero_cards, board_cards, seed=42)
            equity = equity_result['win'] + equity_result['tie'] / 2
            draws = detect_draws(hero_cards, board_cards)
            advice = get_advice(hero_cards, board_cards, pot=None, call_amount=None, seed=42)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Equity", f"{equity*100:.1f}%")
        with col2:
            st.metric("Outs", draws['total_outs'])
        with col3:
            action = advice['action'].upper()
            action_icon = {'RAISE': '🟢', 'CALL': '🟡', 'FOLD': '🔴'}.get(action, '')
            st.markdown(f"### {action_icon} {action}")

        # Next step
        st.markdown("---")
        if st.session_state.current_street == 'turn':
            if st.button("🃏 Deal River (1 card)", type="primary", use_container_width=True):
                st.session_state.current_street = 'river'
                st.rerun()

# Step 4: River
if st.session_state.current_street == 'river' and len(st.session_state.board_cards_selected) >= 4:
    st.markdown("---")
    st.header("🃏 Step 4: River (1 card)")

    if len(st.session_state.board_cards_selected) < 5:
        st.info("Select 1 more card for the river")
        render_card_grid('board', max_cards=5)

    if len(st.session_state.board_cards_selected) == 5:
        board_cards = parse_cards(cards_selected_to_text('board'))
        st.success(f"✅ River: {repr(board_cards[4])}")

        # River Analysis (Full)
        st.subheader("📊 Final Analysis")
        with st.spinner("Calculating final equity..."):
            equity_result = equity_vs_random(hero_cards, board_cards, seed=42)
            equity = equity_result['win'] + equity_result['tie'] / 2
            dist = hand_distribution(hero_cards, board_cards, seed=42)
            advice = get_advice(hero_cards, board_cards, pot=None, call_amount=None, seed=42)

        # Full results display
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total Equity", f"{equity*100:.1f}%")
            win_pct = equity_result['win'] * 100
            tie_pct = equity_result['tie'] * 100
            lose_pct = equity_result['lose'] * 100
            st.markdown(
                f"- Win: **{win_pct:.1f}%**\n"
                f"- Tie: **{tie_pct:.1f}%**\n"
                f"- Lose: **{lose_pct:.1f}%**"
            )

        with col2:
            st.markdown("**Hand Distribution**")
            dist_display = {
                'straight_flush': 'Straight Flush',
                'four_of_a_kind': 'Quads',
                'full_house': 'Full House',
                'flush': 'Flush',
                'straight': 'Straight',
                'three_of_a_kind': 'Trips',
                'two_pair': 'Two Pair',
                'one_pair': 'Pair',
                'high_card': 'High Card',
            }
            shown = 0
            for key, label in dist_display.items():
                if key in dist and dist[key] > 0.001:
                    pct = dist[key] * 100
                    st.markdown(f"- {label}: {pct:.1f}%")
                    shown += 1
                    if shown >= 3:
                        break

        with col3:
            action = advice['action'].upper()
            action_icon = {'RAISE': '🟢', 'CALL': '🟡', 'FOLD': '🔴'}.get(action, '')
            st.markdown(f"### {action_icon} {action}")
            st.caption(f"Confidence: {advice['confidence']}")

        st.markdown("**Rationale:**")
        for point in advice['rationale']:
            st.markdown(f"- {point}")

# Reset button (always visible at bottom)
st.markdown("---")
if st.button("🔄 New Hand", use_container_width=True):
    st.session_state.hero_cards_selected = []
    st.session_state.board_cards_selected = []
    st.session_state.current_street = 'preflop'
    st.session_state.flop_cards = []
    st.session_state.turn_card = None
    st.session_state.river_card = None
    st.rerun()

