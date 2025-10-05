from mosaico import widget, colors, config
import datetime

# =========================
# FIXED COLORS (not from config)
# =========================
ACCENT_HEX = "#FFD36E"   # soft amber (tickers / accents)
WORK_HEX   = "#FF5A3C"   # warning orange for WORK
SHORT_HEX  = "#52E0B3"   # zen teal for short break
LONG_HEX   = "#6FA8FF"   # calm blue for long break
PROGBG_HEX = "#1E1E1E"   # progress bg
TEXT_HEX   = "#FFFFFF"   # text
BG_HEX     = "#000000"   # bg

# =========================
# CONFIG (only timings / structure)
# =========================
def _get_int(key, default):
    try:
        return int(str(config.get(key, default)))
    except:
        return int(default)

def _get_str(key, default):
    v = config.get(key, default)
    return str(v) if v is not None else str(default)

TITLE            = _get_str("name", "Pomodoro")
WORK_MIN         = _get_int("work_minutes", 25)
SHORT_MIN        = _get_int("short_break_minutes", 5)
LONG_MIN         = _get_int("long_break_minutes", 15)
SLICES_PER_ROUND = _get_int("slices_per_round", 4)
ROUNDS           = _get_int("rounds", 1)

# =========================
# UI ELEMENTS (created once)
# =========================
# Title
titleText = widget.createText()
titleText.setFont("4x6")
titleText.setText(TITLE)
titleText.setHexColor(ACCENT_HEX)
titleText.moveTo(4, 2)

# Phase label on same line as title (will be right-aligned)
phaseText = widget.createText()
phaseText.setFont("4x6")
phaseText.setHexColor(TEXT_HEX)
phaseText.moveTo(4, 2)  # initial; re-positioned in init/_start_phase

# Timer (MM:SS)
timerMinText = widget.createText()
timerMinText.setFont("10x20")
timerMinText.setHexColor(TEXT_HEX)
timerMinText.moveTo(8, 20)

timerColonText = widget.createText()
timerColonText.setFont("10x20")
timerColonText.setHexColor(TEXT_HEX)
timerColonText.moveTo(27, 20)

timerSecText = widget.createText()
timerSecText.setFont("10x20")
timerSecText.setHexColor(TEXT_HEX)
timerSecText.moveTo(36, 20)

# Clock ring (phase-colored frame around time) — bottom lifted by 1px
RING_X, RING_Y, RING_W, RING_H = 4, 18, 56, 24
ringTop = widget.createRectangle();    ringTop.setSize(RING_W, 2);      ringTop.moveTo(RING_X, RING_Y)
ringBottom = widget.createRectangle(); ringBottom.setSize(RING_W, 2);   ringBottom.moveTo(RING_X, RING_Y + RING_H - 3)  # lifted 1px
ringLeft = widget.createRectangle();   ringLeft.setSize(2, RING_H - 1); ringLeft.moveTo(RING_X, RING_Y)
ringRight = widget.createRectangle();  ringRight.setSize(2, RING_H - 1);ringRight.moveTo(RING_X + RING_W - 2, RING_Y)

def _set_ring_color(hexcolor):
    ringTop.setHexColor(hexcolor)
    ringBottom.setHexColor(hexcolor)
    ringLeft.setHexColor(hexcolor)
    ringRight.setHexColor(hexcolor)

# ---- Slow "spinning" border: two black blocks moving along the ring path ----
# Create two tiny blocks (2x2) that travel the ring perimeter slowly.
ringSpin1 = widget.createRectangle(); ringSpin1.setSize(2, 2); ringSpin1.setHexColor(BG_HEX)
ringSpin2 = widget.createRectangle(); ringSpin2.setSize(2, 2); ringSpin2.setHexColor(BG_HEX)

# Build a list of coordinates (top-left) along the ring border, clockwise.
ring_path = []
# Top edge (left -> right)
for x in range(RING_X, RING_X + RING_W - 1):  # stop before rightmost outer edge
    ring_path.append((x, RING_Y))
# Right edge (top -> bottom)
right_x = RING_X + RING_W - 2
for y in range(RING_Y, RING_Y + RING_H - 2):  # bottom lifted by 1px; keep inside border
    ring_path.append((right_x, y))
# Bottom edge (right -> left)
bottom_y = RING_Y + RING_H - 3
for x in range(RING_X + RING_W - 2, RING_X, -1):
    ring_path.append((x, bottom_y))
# Left edge (bottom -> top)
left_x = RING_X
for y in range(RING_Y + RING_H - 3, RING_Y, -1):
    ring_path.append((left_x, y))

# Spinner state
ring_index1 = 0
ring_index2 = len(ring_path) // 2 if len(ring_path) > 0 else 0  # opposite side
ring_last_step_at = datetime.datetime.now()
RING_STEP_MS = 250  # slow step (one position every 250ms)

def _position_ring_spinners():
    if not ring_path:
        return
    x1, y1 = ring_path[ring_index1]
    x2, y2 = ring_path[ring_index2]
    ringSpin1.moveTo(x1, y1)
    ringSpin2.moveTo(x2, y2)

def _tick_ring_spinners():
    # advance along path slowly, independent of the 1Hz timer
    global ring_index1, ring_index2, ring_last_step_at
    now = datetime.datetime.now()
    if (now - ring_last_step_at).total_seconds() * 1000.0 < RING_STEP_MS:
        return
    ring_last_step_at = now
    if not ring_path:
        return
    ring_index1 = (ring_index1 + 1) % len(ring_path)
    ring_index2 = (ring_index2 + 1) % len(ring_path)
    _position_ring_spinners()

# Slices (centered squares above clock)
sliceDots = []
SLICE_Y = 14
_sq = 3
_gap = 3
total_w_s = SLICES_PER_ROUND * _sq + (SLICES_PER_ROUND - 1) * _gap
start_s_x = max(0, (64 - total_w_s) // 2)
for i in range(SLICES_PER_ROUND):
    d = widget.createRectangle()
    d.setSize(_sq, _sq)
    d.moveTo(start_s_x + i * (_sq + _gap), SLICE_Y)
    d.setHexColor(PROGBG_HEX)
    sliceDots.append(d)

def _mark_slice(i, filled=True):
    if 0 <= i < len(sliceDots):
        sliceDots[i].setHexColor(ACCENT_HEX if filled else PROGBG_HEX)

def _reset_slice_row():
    for i in range(SLICES_PER_ROUND):
        _mark_slice(i, filled=False)

# Rounds (centered squares below clock)
roundDots = []
ROUNDS_Y = 43
_sq_r = 3
_gap_r = 3
total_w_r = ROUNDS * _sq_r + (ROUNDS - 1) * _gap_r
start_r_x = max(0, (64 - total_w_r) // 2)
for i in range(ROUNDS):
    r = widget.createRectangle()
    r.setSize(_sq_r, _sq_r)
    r.moveTo(start_r_x + i * (_sq_r + _gap_r), ROUNDS_Y)
    r.setHexColor(PROGBG_HEX)
    roundDots.append(r)

def _update_round_dots():
    # mark completed rounds (current_round - 1)
    done = max(0, current_round - 1)
    for i in range(ROUNDS):
        roundDots[i].setHexColor(ACCENT_HEX if i < done else PROGBG_HEX)

# Progress bar (bottom) — moved up by 1px
BAR_X = 4
BAR_Y = 55
BAR_W = 56
BAR_H = 6

progressBg = widget.createRectangle()
progressBg.setSize(BAR_W, BAR_H)
progressBg.moveTo(BAR_X, BAR_Y)
progressBg.setHexColor(PROGBG_HEX)

progressFill = widget.createRectangle()
progressFill.setSize(0, BAR_H)
progressFill.moveTo(BAR_X, BAR_Y)
progressFill.setHexColor(WORK_HEX)

# Per-second sweep ticker
progressTick = widget.createRectangle()
progressTick.setSize(1, BAR_H)
progressTick.moveTo(BAR_X, BAR_Y)
progressTick.setHexColor(ACCENT_HEX)

# Flash border for timeout animation
bd_top = widget.createRectangle();   bd_top.setSize(64, 2); bd_top.moveTo(0, 0);  bd_top.setHexColor(BG_HEX)
bd_bottom = widget.createRectangle();bd_bottom.setSize(64, 2); bd_bottom.moveTo(0, 62); bd_bottom.setHexColor(BG_HEX)
bd_left = widget.createRectangle();  bd_left.setSize(2, 60);  bd_left.moveTo(0, 2);  bd_left.setHexColor(BG_HEX)
bd_right = widget.createRectangle(); bd_right.setSize(2, 60); bd_right.moveTo(62, 2); bd_right.setHexColor(BG_HEX)

def _set_border_color(hexcolor):
    bd_top.setHexColor(hexcolor)
    bd_bottom.setHexColor(hexcolor)
    bd_left.setHexColor(hexcolor)
    bd_right.setHexColor(hexcolor)

def _hide_border():
    _set_border_color(BG_HEX)

# =========================
# STATE
# =========================
PHASE_WORK   = "work"
PHASE_SBREAK = "short_break"
PHASE_LBREAK = "long_break"

current_phase = PHASE_WORK
remaining_seconds = WORK_MIN * 60
phase_total_seconds = max(1, remaining_seconds)

colon_visible = True
last_tick_at = datetime.datetime.now()

current_round = 1
completed_slices_in_round = 0

# Animation
animating = False
anim_end_at = None
blink_on = False
last_blink_at = datetime.datetime.now()

# Ticker drift control
_last_tick_sec_mod = -1

# =========================
# HELPERS
# =========================
def _color_for_phase(ph):
    if ph == PHASE_WORK: return WORK_HEX
    if ph == PHASE_SBREAK: return SHORT_HEX
    return LONG_HEX

def _phase_label(ph):
    if ph == PHASE_WORK: return "WORK"
    if ph == PHASE_SBREAK: return "BREAK"
    return "BREAK XL"

def _right_align_phase_label(lbl_text):
    # Font "4x6" ≈ 4 px per character
    phaseText.moveTo(64 - (len(lbl_text) * 4) - 2, 2)

def _start_phase(ph):
    global current_phase, remaining_seconds, phase_total_seconds, _last_tick_sec_mod
    current_phase = ph
    if ph == PHASE_WORK:
        remaining_seconds = WORK_MIN * 60
    elif ph == PHASE_SBREAK:
        remaining_seconds = SHORT_MIN * 60
    else:
        remaining_seconds = LONG_MIN * 60
    phase_total_seconds = max(1, remaining_seconds)

    # Phase UI updates
    lbl = _phase_label(ph)
    phaseText.setText(lbl)
    hexcol = _color_for_phase(ph)
    phaseText.setHexColor(hexcol)
    _right_align_phase_label(lbl)
    progressFill.setHexColor(hexcol)
    _set_ring_color(hexcol)

    # Reset bars
    progressFill.setSize(0, BAR_H)
    progressTick.moveTo(BAR_X, BAR_Y)
    _last_tick_sec_mod = -1  # force first animate

def _format_mm_ss(sec):
    mm = max(0, sec) // 60
    ss = max(0, sec) % 60
    return f"{mm:02d}", f"{ss:02d}"

def _update_timer_text():
    global colon_visible
    mm, ss = _format_mm_ss(remaining_seconds)
    timerMinText.setText(mm)
    timerSecText.setText(ss)
    timerColonText.setText(":" if colon_visible else "")

def _update_progress(elapsed):
    """Update main bar + second ticker (animateTo)"""
    # Main bar (phase color)
    if phase_total_seconds <= 0:
        width = BAR_W
    else:
        frac = min(1.0, max(0.0, elapsed / float(phase_total_seconds)))
        width = int(round(BAR_W * frac))
    progressFill.setSize(width, BAR_H)

    # Ticker: sweep each minute for visible movement
    sec_mod = int(elapsed % 60)
    targetX = BAR_X + int(round((sec_mod / 60.0) * BAR_W))

    global _last_tick_sec_mod
    if sec_mod != _last_tick_sec_mod:
        _last_tick_sec_mod = sec_mod
        progressTick.moveTo(targetX, BAR_Y)
        next_sec_mod = (sec_mod + 1) % 60
        nextX = BAR_X + int(round((next_sec_mod / 60.0) * BAR_W))
        progressTick.animateTo(nextX, BAR_Y, 980)  # ~1s sweep

def _advance_after_work():
    """Call when a WORK phase completes."""
    global completed_slices_in_round, current_round
    _mark_slice(completed_slices_in_round, filled=True)
    completed_slices_in_round += 1
    if completed_slices_in_round < SLICES_PER_ROUND:
        return PHASE_SBREAK
    # Round completed
    completed_slices_in_round = 0
    current_round += 1
    if current_round > ROUNDS:
        current_round = 1
    _reset_slice_row()
    _update_round_dots()
    return PHASE_LBREAK

def _next_phase():
    if current_phase == PHASE_WORK:
        return _advance_after_work()
    return PHASE_WORK

def _start_timeout_animation():
    global animating, anim_end_at, blink_on, last_blink_at
    animating = True
    anim_end_at = datetime.datetime.now() + datetime.timedelta(seconds=1.6)
    blink_on = False
    last_blink_at = datetime.datetime.now()

def _tick_animation():
    global animating, blink_on, last_blink_at
    if not animating:
        return
    now = datetime.datetime.now()
    if (now - last_blink_at).total_seconds() >= (1.0/6.0):
        blink_on = not blink_on
        last_blink_at = now
        _set_border_color(ACCENT_HEX if blink_on else BG_HEX)
    if now >= anim_end_at:
        animating = False
        _hide_border()

# =========================
# INIT
# =========================
# Phase label init (text, color, right-aligned on title line)
init_lbl = _phase_label(current_phase)
phaseText.setText(init_lbl)
phaseText.setHexColor(_color_for_phase(current_phase))
_right_align_phase_label(init_lbl)

# Set ring color
_set_ring_color(_color_for_phase(current_phase))

# Position ring spinners initially
_position_ring_spinners()

# Timer text init
_update_timer_text()

# Slices/rounds init
_reset_slice_row()
_update_round_dots()

# Bars init
progressFill.setSize(0, BAR_H)
progressTick.moveTo(BAR_X, BAR_Y)
_hide_border()

# =========================
# LOOP
# =========================
def loop():
    global remaining_seconds, last_tick_at, colon_visible

    now = datetime.datetime.now()

    # Slow spinner along the ring (runs independently of 1Hz timer)
    _tick_ring_spinners()

    # Border flash animation
    _tick_animation()

    # 1Hz updates
    if (now - last_tick_at).total_seconds() >= 1.0:
        last_tick_at = now
        colon_visible = not colon_visible

        remaining_seconds -= 1
        if remaining_seconds < 0:
            _start_timeout_animation()
            nextp = _next_phase()
            _start_phase(nextp)
            _update_round_dots()
            _update_timer_text()
            _update_progress(0)  # reset bars for new phase
        else:
            elapsed = phase_total_seconds - remaining_seconds
            _update_progress(elapsed)
            _update_timer_text()
