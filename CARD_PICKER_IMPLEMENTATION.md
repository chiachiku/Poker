# 可視化卡牌選擇器 - 完整實現指南

> **目標**: 將 Poker Companion 的卡牌輸入方式從文字輸入改為 52 張牌的點擊式網格選擇器

## 一、背景資訊

### 當前狀態
- **文件**: `app.py`
- **當前輸入方式**: 文字輸入（第 88-98 行）
- **需求**: 完全移除文字輸入，改用可視化網格
- **佈局**: 花色分行（4 行 × 13 列）

### 技術棧
- Streamlit 1.50.0
- Python 3.9+
- 僅使用 Streamlit 原生組件，無外部依賴

---

## 二、完整代碼實現

### 步驟 1: 添加核心函數到 app.py

在 `app.py` 的第 46 行（`parse_cards()` 函數之後）添加以下代碼：

```python
# ──────────────────────────────────────────────
# Card Grid Picker Functions
# ──────────────────────────────────────────────

def init_card_picker_state():
    """Initialize session state for card picker."""
    if 'hero_cards_selected' not in st.session_state:
        st.session_state.hero_cards_selected = []
    if 'board_cards_selected' not in st.session_state:
        st.session_state.board_cards_selected = []


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
```

### 步驟 2: 在 app 啟動時初始化狀態

在 `st.title()` 之後（約第 28 行）添加：

```python
st.title("🃏 Poker Companion")
st.caption("Texas Hold'em analysis: equity, outs, distribution & advice")

# Initialize card picker state (ADD THIS LINE)
init_card_picker_state()
```

### 步驟 3: 替換 Sidebar 的輸入區塊

**原始代碼（第 79-121 行）需要完全替換為：**

```python
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

    # ── Pot & Bet (unchanged) ────
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
```

### 步驟 4: 修改驗證邏輯整合

找到 `validate_cards()` 的呼叫處（約第 132 行），修改為：

**原始代碼：**
```python
# Validate
hero_cards, board_cards, error = validate_cards(hero_text, board_text)
```

**修改為：**
```python
# Convert grid selections to text format for validation
hero_text = cards_selected_to_text('hero')
board_text = cards_selected_to_text('board')

# Validate
hero_cards, board_cards, error = validate_cards(hero_text, board_text)
```

---

## 三、詳細修改步驟

### 修改清單

1. **第 46 行後**: 添加 5 個新函數（約 100 行代碼）
   - `init_card_picker_state()`
   - `get_all_selected_cards()`
   - `render_card_button()`
   - `render_card_grid()`
   - `cards_selected_to_text()`

2. **第 28 行後**: 添加初始化呼叫
   ```python
   init_card_picker_state()
   ```

3. **第 79-121 行**: 完全替換 sidebar 輸入區塊
   - 移除文字輸入相關代碼
   - 添加卡牌網格渲染
   - 保留 Pot & Bet 輸入（不變）

4. **第 132 行**: 修改驗證邏輯整合
   - 添加 `hero_text = cards_selected_to_text('hero')`
   - 添加 `board_text = cards_selected_to_text('board')`

### 不需要修改的部分

- `parse_cards()` 函數 - 保留（用於解析卡牌字串）
- `validate_cards()` 函數 - 完全不變
- 主內容區（equity, outs, advice 顯示）- 完全不變
- Pot & Bet 輸入 - 完全不變
- Analyze 按鈕 - 完全不變

---

## 四、測試驗證

### 手動測試清單

執行以下測試案例，確保功能正常：

| Test | 操作 | 預期結果 |
|------|------|----------|
| TC-01 | 點擊 Ah | Hero selected: [Ah] (1/2) |
| TC-02 | 再點擊 Ah | 反選，Hero: [] (0/2) |
| TC-03 | Hero 選 Ah, Kd | Hero (2/2)，其他 hero 按鈕禁用 |
| TC-04 | Hero 選 Ah，Board 點擊 Ah | Board 的 Ah 按鈕禁用（灰色） |
| TC-05 | Board 選 5 張 | (5/5)，未選按鈕禁用 |
| TC-06 | 點 Clear All | 所有選擇清空，所有按鈕恢復可選 |
| TC-07 | 選 Hero 2 張 + Board 3 張，點 Analyze | 正常計算並顯示結果 |
| TC-08 | 選 Hero 1 張，點 Analyze | 錯誤："Hero must have exactly 2 cards." |
| TC-09 | 選 Board 2 張，點 Analyze | 錯誤："Board must have 0, 3, 4, or 5 cards." |
| TC-10 | 快速連點同一按鈕 3 次 | 狀態正確切換（1→0→1） |

### 回歸測試

確保現有測試套件仍然通過：

```bash
pytest tests/ -v
# 預期：121 tests passed
```

### 驗證 Streamlit 運行

```bash
# 停止舊的 Streamlit 進程（如果有）
pkill -f "streamlit run"

# 重新啟動
python3 -m streamlit run app.py --server.headless true

# 在瀏覽器打開 http://localhost:8501
```

---

## 五、預期效果

### UI 佈局

```
[Sidebar]
┌─────────────────────────────────────┐
│ 🃏 Select Cards                     │
│                                     │
│ ### Hero Cards                     │
│ (0/2 selected)                     │
│ ♥ [A][K][Q][J][T][9][8][7][6][5][4][3][2] │
│ ♦ [A][K][Q][J][T][9][8][7][6][5][4][3][2] │
│ ♣ [A][K][Q][J][T][9][8][7][6][5][4][3][2] │
│ ♠ [A][K][Q][J][T][9][8][7][6][5][4][3][2] │
│                                     │
│ ────────────────────────────────   │
│                                     │
│ ### Board Cards                    │
│ (0/5 selected)                     │
│ ♥ [A][K][Q][J][T][9][8][7][6][5][4][3][2] │
│ ♦ [A][K][Q][J][T][9][8][7][6][5][4][3][2] │
│ ♣ [A][K][Q][J][T][9][8][7][6][5][4][3][2] │
│ ♠ [A][K][Q][J][T][9][8][7][6][5][4][3][2] │
│                                     │
│ [🗑️ Clear All Cards]               │
│                                     │
│ ────────────────────────────────   │
│ Pot & Bet (optional)               │
│ ...                                │
└─────────────────────────────────────┘
```

### 按鈕狀態

- **未選**: 白底黑字，顯示 rank 字符（如 "A"）
- **已選**: 藍底白字（primary），顯示 "✓A"
- **禁用**: 灰底淡字，不可點擊
  - 已在其他區域選擇（hero 選了 Ah，board 的 Ah 禁用）
  - 已達上限（hero 2/2 時，未選的按鈕禁用）

---

## 六、潛在問題與解決方案

### 問題 1: Sidebar 空間不足

**症狀**: 兩個網格太長，需要滾動很多

**解決方案 A**: 使用 `st.expander` 折疊區塊

```python
with st.expander("Hero Cards (0/2)", expanded=True):
    render_card_grid('hero', 2)

with st.expander("Board Cards (0/5)", expanded=False):
    render_card_grid('board', 5)
```

**解決方案 B**: 使用 tabs 切換

```python
tab_hero, tab_board = st.tabs(["Hero Cards", "Board Cards"])

with tab_hero:
    render_card_grid('hero', 2)

with tab_board:
    render_card_grid('board', 5)
```

### 問題 2: 按鈕渲染速度慢

**症狀**: 點擊後重新渲染需要 > 500ms

**解決方案**: 這是 Streamlit 的預期行為，52 個按鈕在純 Python 環境下無法更快。如果影響用戶體驗，可以：
- 使用 tabs 分頁（每次只渲染 13 個按鈕）
- 添加 loading spinner 提示用戶

### 問題 3: 按鈕太小難以點擊

**症狀**: 在小螢幕上按鈕太擠

**解決方案**: 調整列數或使用更大的字體

```python
# 方案 1: 減少每行顯示的按鈕數（例如只顯示 7 張，分成兩行）
# 方案 2: 使用自訂 CSS 增大按鈕
st.markdown("""
<style>
button[kind="secondary"], button[kind="primary"] {
    font-size: 14px !important;
    padding: 8px !important;
}
</style>
""", unsafe_allow_html=True)
```

---

## 七、Git Commit 建議

完成實現並測試通過後，執行以下 commit：

```bash
git add app.py
git commit -m "Add visual card grid picker to Streamlit UI

- Replace text input with 52-card clickable grid (4 suits × 13 ranks)
- Implement session state management for hero/board cards
- Prevent duplicate selection across hero and board
- Enforce max limits (2 hero, 5 board)
- Add Clear All button
- Maintain backward compatibility with validation logic

All 10 manual test cases passed.
Existing test suite: 121 tests passing.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## 八、執行指令摘要

```bash
# 1. 停止現有 Streamlit（如果運行中）
pkill -f "streamlit run"

# 2. 修改 app.py（按照本指南的步驟 1-4）

# 3. 重新啟動 Streamlit
python3 -m streamlit run app.py --server.headless true

# 4. 在瀏覽器打開測試
open http://localhost:8501

# 5. 執行測試清單（TC-01 ~ TC-10）

# 6. 執行回歸測試
pytest tests/ -v

# 7. Commit
git add app.py
git commit -m "Add visual card grid picker to Streamlit UI"
```

---

## 九、快速檢查清單

實現完成後，確認以下項目：

- [ ] 5 個新函數已添加到 `app.py`
- [ ] `init_card_picker_state()` 在 app 啟動時被呼叫
- [ ] Sidebar 中的文字輸入已完全移除
- [ ] Hero 和 Board 網格正常顯示
- [ ] 點擊按鈕可以選擇/反選卡牌
- [ ] 達到上限時按鈕正確禁用
- [ ] Hero 和 Board 之間的重複防護生效
- [ ] Clear All 按鈕正常運作
- [ ] Analyze 按鈕和計算邏輯正常
- [ ] TC-01 ~ TC-10 測試案例全部通過
- [ ] `pytest tests/` 仍然 121 tests passing

---

## 十、聯絡與支援

如果在實現過程中遇到問題：

1. **檢查 Streamlit 版本**: `pip show streamlit` → 應該是 1.50.0
2. **檢查語法錯誤**: `python3 -m py_compile app.py`
3. **檢查瀏覽器控制台**: 查看是否有 JavaScript 錯誤
4. **重新啟動 Streamlit**: `pkill -f streamlit && python3 -m streamlit run app.py`

---

**實現完成後，你將擁有一個直觀的 52 張牌點擊式選擇器，完全取代文字輸入！** 🎴
