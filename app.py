"""Poker Companion — Streamlit UI (Mobile-Friendly).

Texas Hold'em analysis: input hole cards + community cards,
get equity, outs, hand distribution, and rule-based advice.
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

st.set_page_config(page_title="Poker Companion", page_icon="🃏", layout="centered")

st.markdown("""<style>
/* Prevent column wrapping on mobile — keep card grid intact */
[data-testid="stHorizontalBlock"] {
    flex-wrap: nowrap !important;
    gap: 0.2rem !important;
}
/* Bigger touch targets for card buttons */
[data-testid="stHorizontalBlock"] button {
    min-height: 2.4rem;
    padding: 0.25rem 0;
    font-size: 0.95rem;
    border-radius: 6px;
}
@media (max-width: 640px) {
    [data-testid="stHorizontalBlock"] button {
        min-height: 2.8rem;
        font-size: 1rem;
    }
}
</style>""", unsafe_allow_html=True)

st.title("🃏 Poker Companion")
st.caption("Texas Hold'em equity · outs · advice")


# ──────────────────────────────────────────────
# Session state
# ──────────────────────────────────────────────

for _key, _default in [
    ('hero_cards_selected', []),
    ('board_cards_selected', []),
    ('picking_for', 'hero'),
]:
    if _key not in st.session_state:
        st.session_state[_key] = _default


# ──────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────

SUITS = ['h', 'd', 'c', 's']
SUIT_SYMBOLS = {'h': '♥', 'd': '♦', 'c': '♣', 's': '♠'}
# 4-color deck for clarity: red / blue / green / gray
SUIT_COLORS = {'h': '#e74c3c', 'd': '#3498db', 'c': '#2ecc71', 's': '#7f8c8d'}
RANKS = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def parse_cards(text: str) -> list:
    """Parse space/comma separated card string into Card objects."""
    text = text.strip()
    if not text:
        return []
    return [Card.from_string(t.strip()) for t in text.replace(",", " ").split() if t.strip()]


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
    all_strs = [repr(c) for c in hero + board]
    if len(set(all_strs)) != len(all_strs):
        return None, None, "Duplicate cards detected."
    return hero, board, None


def _card_btn(card_str: str, rank: str, ctx_key: str, max_cards: int,
              all_selected: set, current: list):
    """Render a single card toggle button."""
    sel_here = card_str in current
    sel_elsewhere = card_str in all_selected and not sel_here
    at_max = len(current) >= max_cards and not sel_here
    if st.button(
        f"✓{rank}" if sel_here else rank,
        key=f"c_{card_str}",
        disabled=sel_elsewhere or at_max,
        type='primary' if sel_here else 'secondary',
        use_container_width=True,
    ):
        if sel_here:
            current.remove(card_str)
        else:
            current.append(card_str)
            # Auto-switch to board after hero is full
            if ctx_key == 'hero_cards_selected' and len(current) >= 2:
                st.session_state.picking_for = 'board'
        st.rerun()


# ──────────────────────────────────────────────
# Selected cards display
# ──────────────────────────────────────────────

hero_sel = st.session_state.hero_cards_selected
board_sel = st.session_state.board_cards_selected

col_h, col_b = st.columns(2)
with col_h:
    st.markdown("**Hero**")
    st.markdown(" ".join(f"`{c}`" for c in hero_sel) if hero_sel else "_tap 2 cards_")
with col_b:
    st.markdown("**Board**")
    st.markdown(" ".join(f"`{c}`" for c in board_sel) if board_sel else "_0–5 cards_")

if hero_sel or board_sel:
    if st.button("🗑️ Clear All", use_container_width=True):
        st.session_state.hero_cards_selected = []
        st.session_state.board_cards_selected = []
        st.session_state.pop('last_analysis', None)
        st.rerun()

st.divider()


# ──────────────────────────────────────────────
# Picking mode toggle
# ──────────────────────────────────────────────

st.radio(
    "Selecting for:",
    ['hero', 'board'],
    format_func=lambda x: (
        f"Hero ({len(st.session_state.hero_cards_selected)}/2)" if x == 'hero'
        else f"Board ({len(st.session_state.board_cards_selected)}/5)"
    ),
    horizontal=True,
    key='picking_for',
)


# ──────────────────────────────────────────────
# Card grid — 7 columns, 2 rows per suit
# ──────────────────────────────────────────────

ctx = st.session_state.picking_for
ctx_key = f'{ctx}_cards_selected'
max_cards = 2 if ctx == 'hero' else 5
all_selected = set(hero_sel + board_sel)
current = st.session_state[ctx_key]

for suit in SUITS:
    sym = SUIT_SYMBOLS[suit]
    color = SUIT_COLORS[suit]
    st.markdown(
        f"<span style='color:{color};font-size:1.1rem;font-weight:bold'>{sym}</span>",
        unsafe_allow_html=True,
    )

    # Row 1: A K Q J T 9 8
    cols = st.columns(7)
    for i, rank in enumerate(RANKS[:7]):
        with cols[i]:
            _card_btn(f"{rank}{suit}", rank, ctx_key, max_cards, all_selected, current)

    # Row 2: 7 6 5 4 3 2 (+ 1 empty column for consistent sizing)
    cols = st.columns(7)
    for i, rank in enumerate(RANKS[7:]):
        with cols[i]:
            _card_btn(f"{rank}{suit}", rank, ctx_key, max_cards, all_selected, current)

st.divider()


# ──────────────────────────────────────────────
# Pot & Bet
# ──────────────────────────────────────────────

st.markdown("**Pot & Bet** (optional)")
pcol, ccol = st.columns(2)
with pcol:
    pot_size = st.number_input("Pot", min_value=0.0, value=0.0, step=10.0, format="%.0f")
with ccol:
    call_amt = st.number_input("Call", min_value=0.0, value=0.0, step=5.0, format="%.0f")


# ──────────────────────────────────────────────
# Analyze
# ──────────────────────────────────────────────

analyze_btn = st.button("🔍 Analyze", type="primary", use_container_width=True)

if analyze_btn:
    hero_text = " ".join(st.session_state.hero_cards_selected)
    board_text = " ".join(st.session_state.board_cards_selected)

    hero_cards, board_cards, error = validate_cards(hero_text, board_text)
    if error:
        st.error(error)
        st.stop()

    pot_val = pot_size if pot_size > 0 else None
    call_val = call_amt if call_amt > 0 else None

    with st.spinner("Calculating..."):
        equity_result = equity_vs_random(hero_cards, board_cards, seed=42)
        equity = equity_result['win'] + equity_result['tie'] / 2
        draws = detect_draws(hero_cards, board_cards)
        dist = hand_distribution(hero_cards, board_cards, seed=42)
        advice = get_advice(
            hero_cards, board_cards,
            pot=pot_val, call_amount=call_val, seed=42,
        )
        po_info = None
        if pot_val and call_val and call_val > 0:
            po_info = {
                'pot_odds': pot_odds(pot_val, call_val),
                'ev': ev_call(pot_val, call_val, equity),
            }

    st.session_state.last_analysis = {
        'hero_text': hero_text,
        'board_text': board_text,
        'equity_result': equity_result,
        'equity': equity,
        'draws': draws,
        'dist': dist,
        'advice': advice,
        'po_info': po_info,
        'board_len': len(board_cards),
        'hero_display': " ".join(repr(c) for c in hero_cards),
        'board_display': " ".join(repr(c) for c in board_cards) if board_cards else "—",
        'street': {0: "Preflop", 3: "Flop", 4: "Turn", 5: "River"}.get(len(board_cards), ""),
    }


# ──────────────────────────────────────────────
# Results (persisted in session state)
# ──────────────────────────────────────────────

if 'last_analysis' not in st.session_state:
    st.info("Select hero + board cards, then tap **Analyze**.")
    st.stop()

st.divider()
r = st.session_state.last_analysis

# Warn if cards changed since last analysis
cur_hero = " ".join(st.session_state.hero_cards_selected)
cur_board = " ".join(st.session_state.board_cards_selected)
if cur_hero != r['hero_text'] or cur_board != r['board_text']:
    st.warning("Cards changed — tap **Analyze** to update.")

st.markdown(f"**Hero:** `{r['hero_display']}` · **Board:** `{r['board_display']}` · {r['street']}")

# ── Advice (most actionable — show first) ──
advice = r['advice']
action = advice['action'].upper()
icon = {'RAISE': '🟢', 'CALL': '🟡', 'FOLD': '🔴'}.get(action, '')

st.markdown(f"### {icon} {action}")
st.markdown(f"Confidence: **{advice['confidence']}**")
if advice['bet_sizing'] is not None:
    st.markdown(f"Bet sizing: **{advice['bet_sizing'] * 100:.0f}% pot**")
for pt in advice['rationale']:
    st.markdown(f"- {pt}")

st.divider()

# ── Equity ──
st.markdown("**Equity**")
eq_pct = r['equity'] * 100
er = r['equity_result']
st.metric("Total Equity", f"{eq_pct:.1f}%")
st.markdown(
    f"Win **{er['win']*100:.1f}%** · "
    f"Tie **{er['tie']*100:.1f}%** · "
    f"Lose **{er['lose']*100:.1f}%**"
)

if r['po_info']:
    po = r['po_info']
    ev_val = po['ev']
    ev_color = "green" if ev_val > 0 else "red"
    st.markdown(f"Pot odds: need **{po['pot_odds']*100:.1f}%** equity to call")
    st.markdown(f"EV(call): **:{ev_color}[{ev_val:+.1f}]**")

st.divider()

# ── Draws & Outs ──
st.markdown("**Draws & Outs**")
if r['board_len'] in (3, 4):
    draws = r['draws']
    st.metric("Outs", draws['total_outs'])
    if draws['flush_draw']:
        st.markdown(f"- Flush draw: **{draws['flush_draw']['outs']} outs**")
    for sd in draws['straight_draws']:
        label = "OESD" if sd['type'] == 'oesd' else "Gutshot"
        st.markdown(f"- {label}: **{sd['outs']} outs**")
    if draws['total_outs'] == 0:
        st.markdown("_No draws detected._")
else:
    st.markdown("_Draws shown on flop/turn._")

st.divider()

# ── Hand Distribution ──
st.markdown("**Hand Distribution**")
dist = r['dist']
if dist:
    for key, label in [
        ('straight_flush', 'Str. Flush'), ('four_of_a_kind', 'Quads'),
        ('full_house', 'Full House'), ('flush', 'Flush'),
        ('straight', 'Straight'), ('three_of_a_kind', 'Trips'),
        ('two_pair', 'Two Pair'), ('one_pair', 'Pair'),
        ('high_card', 'High Card'),
    ]:
        if key in dist and dist[key] > 0:
            st.markdown(f"- {label}: **{dist[key]*100:.1f}%**")
