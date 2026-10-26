"""
Pointillism Bouquet - Generative Floral Art in Pygame & NumPy
An organic, multi-flower bouquet blooming in real-time with 3D pointillism simulation,
flowing satin ribbon & bow, hand-tied stems, lush foliage, starry filler blossoms,
staggered floral bloom, and atmospheric particle glow.
"""

import sys
import os
import math
import numpy as np
import pygame

# --- Canvas & Timing Configuration ---
W, H = 720, 1280
FPS = 60
T_GROW = 4.4       # Time for stems and foliage to grow into position
LOOP_AT = 0        # 0 = play continuously, or set seconds to loop (e.g. 22.0)
BG = (4, 2, 10)    # Deep mystical twilight background
S = W / 720.0      # Coordinate scaling factor

rng = np.random.default_rng(42)

# Global bouquet gathering anchors
gx, gy = W / 2.0, H * 0.88      # Bottom base of the gathered stem handle
tx, ty = W / 2.0, H * 0.70      # Waist / ribbon tie cinch point

def smooth(x):
    """Hermite smoothstep interpolation [0, 1]."""
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3.0 - 2.0 * x)

def lerp(a, b, t):
    return a + (b - a) * t

def midrib(L, a0, curl, K=40):
    """Computes the 2D spinal curve (r, h) of a petal or leaf."""
    us = np.linspace(0.0, 1.0, K + 1)
    al = a0 + curl * (us ** 1.6)
    ds = L / K
    r = np.concatenate([[0.0], np.cumsum(np.sin(al[1:])) * ds])
    h = np.concatenate([[0.0], np.cumsum(np.cos(al[1:])) * ds])
    return us, r, h

def get_rotation_matrix(pitch, yaw, roll):
    """Returns 3x3 rotation matrix from pitch (X), yaw (Y), roll (Z)."""
    cp, sp = math.cos(pitch), math.sin(pitch)
    cy, sy = math.cos(yaw), math.sin(yaw)
    cr, sr = math.cos(roll), math.sin(roll)

    # Rz * Ry * Rx
    return np.array([
        [cr * cy, cr * sy * sp - sr * cp, cr * sy * cp + sr * sp],
        [sr * cy, sr * sy * sp + cr * cp, sr * sy * cp - cr * sp],
        [-sy,     cy * sp,                cy * cp]
    ], dtype=float)

# --- Flower Specifications for the Bouquet ---
FLOWERS = [
    {
        "id": "center",
        "name": "Royal Stargazer Lily",
        "head_target": (gx + 0.0, H * 0.31),
        "scale": 1.06 * S,
        "t_start": 4.8,
        "duration": 7.8,
        "base_pitch": 0.38,
        "base_yaw": 0.0,
        "base_roll": 0.0,
        "stops": [0.0, 0.28, 0.65, 1.0],
        # Deep magenta core to pure pearl edges
        "grad_r": [245, 255, 255, 255],
        "grad_g": [35,  85,  160, 240],
        "grad_b": [115, 150, 205, 250],
        "throat_col": (230, 240, 140),
        "spot_col": (145, 15, 75),
        "handle_offset": 0.0,
    },
    {
        "id": "mid_left",
        "name": "Coral Sunset Lily",
        "head_target": (gx - 150.0 * S, H * 0.39),
        "scale": 0.95 * S,
        "t_start": 5.4,
        "duration": 7.6,
        "base_pitch": 0.42,
        "base_yaw": -0.26,
        "base_roll": -0.32,
        "stops": [0.0, 0.30, 0.68, 1.0],
        # Sunset coral & warm peach
        "grad_r": [255, 255, 255, 255],
        "grad_g": [60,  125, 195, 245],
        "grad_b": [30,  70,  140, 220],
        "throat_col": (255, 235, 120),
        "spot_col": (180, 45, 25),
        "handle_offset": -8.0 * S,
    },
    {
        "id": "mid_right",
        "name": "Lilac Orchid Lily",
        "head_target": (gx + 145.0 * S, H * 0.38),
        "scale": 0.96 * S,
        "t_start": 5.9,
        "duration": 7.6,
        "base_pitch": 0.44,
        "base_yaw": 0.24,
        "base_roll": 0.30,
        "stops": [0.0, 0.28, 0.66, 1.0],
        # Ethereal violet-amethyst to frosted lilac
        "grad_r": [220, 238, 250, 255],
        "grad_g": [40,  95,  175, 235],
        "grad_b": [225, 248, 255, 255],
        "throat_col": (240, 225, 150),
        "spot_col": (120, 20, 140),
        "handle_offset": 8.0 * S,
    },
    {
        "id": "lower_left",
        "name": "Champagne Lily",
        "head_target": (gx - 205.0 * S, H * 0.49),
        "scale": 0.88 * S,
        "t_start": 6.5,
        "duration": 7.3,
        "base_pitch": 0.48,
        "base_yaw": -0.38,
        "base_roll": -0.54,
        "stops": [0.0, 0.33, 0.70, 1.0],
        # Golden champagne & honey buttercup
        "grad_r": [255, 255, 255, 255],
        "grad_g": [140, 185, 230, 255],
        "grad_b": [40,  90,  170, 240],
        "throat_col": (255, 220, 90),
        "spot_col": (170, 90, 20),
        "handle_offset": -13.0 * S,
    },
    {
        "id": "lower_right",
        "name": "Blush Rose Lily",
        "head_target": (gx + 200.0 * S, H * 0.48),
        "scale": 0.90 * S,
        "t_start": 7.0,
        "duration": 7.3,
        "base_pitch": 0.46,
        "base_yaw": 0.35,
        "base_roll": 0.52,
        "stops": [0.0, 0.30, 0.66, 1.0],
        # Soft blush rose to deep raspberry
        "grad_r": [255, 255, 255, 255],
        "grad_g": [55,  115, 180, 240],
        "grad_b": [135, 175, 215, 245],
        "throat_col": (245, 230, 160),
        "spot_col": (160, 25, 85),
        "handle_offset": 13.0 * S,
    }
]

# --- Precompute Petal Point Clouds for Each Flower ---
NP_PETAL = 1400  # Detailed points per petal
flower_data = []

for fl_idx, fl in enumerate(FLOWERS):
    fl_petals = []
    sc = fl["scale"]
    for k in range(6):
        outer = (k % 2 == 0)
        pu = rng.random(NP_PETAL) ** 0.85
        pv = rng.uniform(-1.0, 1.0, NP_PETAL)
        prof = np.sin(np.pi * (pu ** 0.7)) ** 0.9
        keep = np.abs(pv) <= 1.0

        stops = np.array(fl["stops"])
        base = np.stack([
            np.interp(pu, stops, fl["grad_r"]),
            np.interp(pu, stops, fl["grad_g"]),
            np.interp(pu, stops, fl["grad_b"]),
        ], axis=1)

        # Flower throat stripe
        mid = (np.abs(pv) < 0.07) & (pu < 0.55)
        base[mid] = fl["throat_col"]

        # Freckle spots
        spot = (rng.random(NP_PETAL) < 0.12) & (pu < 0.58) & (np.abs(pv) < 0.72) & ~mid
        base[spot] = fl["spot_col"]

        # Petal edge illumination
        edge = np.abs(pv) > 0.88
        base[edge] *= 1.08
        base *= (0.84 + 0.32 * rng.random((NP_PETAL, 1)))

        fl_petals.append({
            "phi": math.radians(k * 60.0 + 8.0 + fl_idx * 6.0),
            "L": (300.0 if outer else 280.0) * sc,
            "Wm": (66.0 if outer else 74.0) * sc,
            "ac": 0.10 if outer else 0.05,
            "ao": 1.06 if outer else 0.83,
            "curl": 0.96 if outer else 0.76,
            "pu": pu, "pv": pv, "prof": prof,
            "base": base, "keep": keep
        })

    # Stamens per flower
    fl_stam = []
    for k in range(6):
        fl_stam.append({
            "phi": math.radians(k * 60.0 + 38.0 + fl_idx * 6.0),
            "jit": rng.normal(0.0, 1.0, (40, 1)),
            "an": rng.normal(0.0, 1.0, (30, 2))
        })

    flower_data.append({
        "info": fl,
        "petals": fl_petals,
        "stam": fl_stam,
    })

# --- Stems: Hand-Tied Florist Bouquet Architecture ---
# Stems are gathered in a tight handle from gy up to ty, then gracefully arch outward to flower heads
NS_PER_STEM = 1800
stems_data = []

for fl_idx, fl in enumerate(FLOWERS):
    s_vals = rng.random(NS_PER_STEM)
    # Tapering from stem base to receptacle
    th = (4.0 * S) * (1.0 - 0.40 * s_vals)
    radial_jit = rng.normal(0.0, 1.0, NS_PER_STEM) * th

    # Woody emerald to fresh spring jade
    col = np.stack([
        lerp(35, 115, s_vals),
        lerp(140, 210, s_vals),
        lerp(80, 125, s_vals)
    ], axis=1)
    col *= (0.82 + 0.36 * rng.random((NS_PER_STEM, 1)))

    stems_data.append({
        "fl_idx": fl_idx,
        "s": s_vals,
        "jit": radial_jit,
        "col": col,
        "handle_off": fl["handle_offset"]
    })

def eval_stem_spline(fl_idx, s, t):
    """
    Evaluates 2D stem position along hand-tied bouquet curve:
    Gathered handle: (gx + handle_off, gy) -> (tx + handle_off*0.7, ty)
    Upper arch: expands smoothly into a fan curve to (hx, hy)
    """
    fl = FLOWERS[fl_idx]
    hx, hy = fl["head_target"]

    # Natural breeze sway
    sway = (6.0 * S) * math.sin(0.85 * t + fl_idx * 0.9) * (s ** 2)

    # 4-point cubic spline
    # P0: Base of handle
    p0x = gx + fl["handle_offset"]
    p0y = gy
    # P1: Inside the ribbon cinch
    p1x = tx + fl["handle_offset"] * 0.45
    p1y = ty + 10.0 * S
    # P2: Upper fan curve inflection
    arch_out = (hx - tx) * 0.65
    p2x = tx + arch_out + sway * 0.5
    p2y = ty - (ty - hy) * 0.45
    # P3: Receptacle head
    p3x = hx + sway
    p3y = hy

    u = 1.0 - s
    bx = (u**3) * p0x + 3 * (u**2) * s * p1x + 3 * u * (s**2) * p2x + (s**3) * p3x
    by = (u**3) * p0y + 3 * (u**2) * s * p1y + 3 * u * (s**2) * p2y + (s**3) * p3y
    return bx, by

# --- Foliage & Leaves ---
LEAF_COUNT = 22
leaves_data = []
for i in range(LEAF_COUNT):
    fl_idx = i % len(FLOWERS)
    s0 = float(rng.uniform(0.24, 0.72))
    side = -1 if (i % 2 == 0) else 1
    L = float(rng.uniform(130.0, 210.0)) * S
    n_pts = 600
    u = rng.random(n_pts) ** 0.88
    v = rng.uniform(-1.0, 1.0, n_pts)
    prof = np.sin(np.pi * (u ** 0.78)) ** 0.85

    col = np.stack([
        lerp(30, 130, u),
        lerp(145, 230, u),
        lerp(85, 135, u)
    ], axis=1)
    col[np.abs(v) < 0.08] = (185, 240, 165)
    col *= (0.8 + 0.4 * rng.random((n_pts, 1)))

    leaves_data.append({
        "fl_idx": fl_idx,
        "s0": s0,
        "side": side,
        "L": L,
        "u": u, "v": v,
        "prof": prof,
        "col": col,
        "phase": rng.uniform(0.0, 6.28)
    })

# --- Starry Filler Blossoms (Baby's Breath / Gypsophila) ---
# Delicate clusters of tiny sparkling florets nestled around the bouquet
N_FILLER_SPRIGS = 10
filler_sprigs = []
for i in range(N_FILLER_SPRIGS):
    # Anchor between flowers
    angle = -0.75 + (i / (N_FILLER_SPRIGS - 1)) * 1.5
    dist = float(rng.uniform(160.0, 280.0)) * S
    fx = gx + math.sin(angle) * dist
    fy = ty - math.cos(angle) * dist * 0.95

    n_florets = 26
    fl_pts = []
    for _ in range(n_florets):
        ox = rng.normal(0.0, 14.0 * S)
        oy = rng.normal(0.0, 14.0 * S)
        # Petals of tiny blossom
        for p_ang in np.linspace(0, 2*np.pi, 5, endpoint=False):
            fl_pts.append((ox + math.cos(p_ang) * 4.0 * S, oy + math.sin(p_ang) * 4.0 * S))

    filler_sprigs.append({
        "x": fx, "y": fy,
        "pts": np.array(fl_pts),
        "t_start": float(rng.uniform(4.5, 6.5)),
        "phase": rng.uniform(0, 6.28)
    })

# --- Realistic Satin Ribbon Bow & Draping Tails ---
N_RIBBON = 5200
rib_u = rng.random(N_RIBBON)
rib_part = rng.choice(
    ["knot", "loop_l", "loop_r", "tail_l", "tail_r", "band"],
    size=N_RIBBON,
    p=[0.14, 0.22, 0.22, 0.18, 0.18, 0.06]
)
rib_pts = []

for idx in range(N_RIBBON):
    part = rib_part[idx]
    u = rib_u[idx]
    v = rng.uniform(-1.0, 1.0) # Width coordinate across the satin ribbon
    w = 16.0 * S               # Luxurious wide satin ribbon

    if part == "band":
        # Tied band wrapped around the stem handle
        theta = (u - 0.5) * math.pi * 0.92
        rx = tx + math.sin(theta) * (26.0 * S) + v * (2.5 * S)
        ry = ty + (u - 0.5) * (22.0 * S) + v * (2.0 * S)
        rz = 120.0 + math.cos(theta) * 22.0
    elif part == "knot":
        # Rounded central tie knot
        phi = u * 2.0 * math.pi
        rad = (rng.random() ** 0.5) * (14.0 * S)
        rx = tx + math.cos(phi) * rad
        ry = ty + math.sin(phi) * (rad * 0.85)
        rz = 220.0 + math.cos(phi) * 10.0
    elif part == "loop_l":
        # Full filled left satin bow loop
        theta = u * 2.0 * math.pi
        # Main spine of loop
        cx = tx - 14.0 * S - (1.0 - math.cos(theta)) * (42.0 * S)
        cy = ty - 4.0 * S + math.sin(theta) * (24.0 * S)
        # Normal across ribbon width
        dx = (1.0 - math.cos(theta)) * 0.4
        dy = math.cos(theta)
        mag = math.hypot(dx, dy) + 1e-5
        nx, ny = -dy / mag, dx / mag
        loop_w = w * (0.45 + 0.55 * math.sin(theta * 0.5))
        rx = cx + nx * v * loop_w
        ry = cy + ny * v * loop_w
        rz = 180.0 + math.sin(theta) * 22.0
    elif part == "loop_r":
        # Full filled right satin bow loop
        theta = u * 2.0 * math.pi
        cx = tx + 14.0 * S + (1.0 - math.cos(theta)) * (42.0 * S)
        cy = ty - 4.0 * S + math.sin(theta) * (24.0 * S)
        dx = -(1.0 - math.cos(theta)) * 0.4
        dy = math.cos(theta)
        mag = math.hypot(dx, dy) + 1e-5
        nx, ny = -dy / mag, dx / mag
        loop_w = w * (0.45 + 0.55 * math.sin(theta * 0.5))
        rx = cx + nx * v * loop_w
        ry = cy + ny * v * loop_w
        rz = 180.0 + math.sin(theta) * 22.0
    elif part == "tail_l":
        # Cascading flowing left satin ribbon tail
        cx = tx - 8.0 * S - u * (42.0 * S) + math.sin(u * 4.2) * (14.0 * S)
        cy = ty + 12.0 * S + u * (165.0 * S)
        rx = cx + v * (w * 0.75) * (1.0 - 0.25 * u)
        ry = cy
        rz = 160.0 - u * 35.0
    else:
        # Cascading flowing right satin ribbon tail
        cx = tx + 8.0 * S + u * (46.0 * S) - math.sin(u * 4.0) * (15.0 * S)
        cy = ty + 12.0 * S + u * (175.0 * S)
        rx = cx + v * (w * 0.75) * (1.0 - 0.25 * u)
        ry = cy
        rz = 160.0 - u * 35.0

    # Satin champagne-pearl sheen with subtle blush tint
    base_col = np.array([255, 235, 205], dtype=float)
    shimmer = 0.84 + 0.30 * rng.random()
    col = base_col * shimmer
    rib_pts.append((rx, ry, rz, col))

rib_x = np.array([p[0] for p in rib_pts])
rib_y = np.array([p[1] for p in rib_pts])
rib_z = np.array([p[2] for p in rib_pts])
rib_col = np.array([p[3] for p in rib_pts])

# --- Background Aura & Celestial Rings ---
ang_ring = rng.random(1500) * 6.28
ang_c = [rng.random(320) * 6.28 for _ in range(7)]

ND = 550 # Ambient floating dust motes
d_x = rng.random(ND) * W
d_y = rng.random(ND) * H
d_sp = rng.uniform(8.0, 24.0, ND) * S
d_ph = rng.random(ND) * 6.28
d_f = rng.uniform(1.2, 4.0, ND)

# Drifting golden pollen particles
NF = 240
f_off = rng.random(NF)
f_ph = rng.random(NF) * 6.28
f_dr = rng.uniform(-170.0, 170.0, NF) * S
f_sp = rng.uniform(0.04, 0.12, NF)
f_fl_source = rng.integers(0, len(FLOWERS), NF)

# --- Stem Base Soil Mound ---
NG = 3400
so_dx = rng.uniform(-240.0, 240.0, NG) * S
mound = (1.0 - (so_dx / (240.0 * S)) ** 2) * 40.0 * S
so_y = gy - mound * (rng.random(NG) ** 0.5) + rng.normal(0.0, 1.6, NG)
so_col = np.stack([
    lerp(55, 110, rng.random(NG)),
    lerp(45, 85, rng.random(NG)),
    lerp(65, 100, rng.random(NG))
], axis=1)

def render(t, buf):
    """Renders the bouquet scene at simulation time t into numpy buffer buf."""
    P_list, Z_list, C_list = [], [], []

    def add(x, y, z, col):
        P_list.append(np.stack([x, y], 1))
        Z_list.append(np.broadcast_to(z, x.shape).astype(float))
        C_list.append(col)

    # 1. Floating Ambient Dust Motes
    tw = 0.35 + 0.65 * (np.sin(t * d_f + d_ph) > 0.2)
    yy = (d_y - t * d_sp) % H
    add(d_x, yy, -1200, np.stack([255 * tw, 215 * tw, 240 * tw], 1) * 0.52)

    # 2. Celestial Halo / Aura Behind the Bouquet
    ha = float(smooth((t - 3.2) / 4.0)) * 0.95
    if ha > 0.01:
        cx0, cy0 = W / 2.0, H * 0.40
        R = 340.0 * S
        rot = t * 0.09
        a = ang_ring + rot
        add(cx0 + R * np.cos(a), cy0 + R * np.sin(a), -1000,
            np.broadcast_to(np.array([255, 205, 230]) * ha * 0.60, (len(a), 3)))
        for k, ac in enumerate(ang_c):
            ca = rot * 1.25 + k * (math.pi * 2.0 / 7.0)
            ox, oy = cx0 + R * math.cos(ca), cy0 + R * math.sin(ca)
            a_sub = ac + rot
            add(ox + R * 0.45 * np.cos(a_sub), oy + R * 0.45 * np.sin(a_sub), -1000,
                np.broadcast_to(np.array([255, 185, 220]) * ha * 0.35, (len(a_sub), 3)))

    # 3. Base Soil Mound
    add(so_dx + gx, so_y, -600, so_col * 0.85)

    # 4. Bouquet Stems Growth
    stem_progress = smooth(t / T_GROW)
    for st in stems_data:
        m = st["s"] <= stem_progress
        if m.any():
            s_act = st["s"][m]
            bx, by = eval_stem_spline(st["fl_idx"], s_act, t)
            base_z = -120 + FLOWERS[st["fl_idx"]]["scale"] * 30.0
            add(bx + st["jit"][m], by, base_z, st["col"][m])

    # 5. Foliage Leaves
    for lf in leaves_data:
        lg = float(np.clip((stem_progress - lf["s0"]) * 2.6, 0.0, 1.0))
        if lg <= 0.01:
            continue
        L = lf["L"] * lg
        us, r, h = midrib(L, 0.88, 1.15)
        u, v = lf["u"], lf["v"]
        rr, hh = np.interp(u, us, r), np.interp(u, us, h)
        wid = 16.0 * S * lf["prof"] * lg

        fl_idx = lf["fl_idx"]
        bx, by = eval_stem_spline(fl_idx, np.array([lf["s0"]]), t)
        bx, by = float(bx[0]), float(by[0])
        sway = math.sin(t * 1.3 + lf["phase"]) * 0.04

        x = bx + lf["side"] * (rr + v * wid * 0.35) + sway * hh * lf["side"]
        y = by - hh + v * wid
        add(x, y, -95, lf["col"])

    # 6. Starry Filler Blossoms (Baby's Breath)
    for sprig in filler_sprigs:
        sp_t = smooth((t - sprig["t_start"]) / 2.5)
        if sp_t > 0.01:
            sway_fx = math.sin(t * 1.5 + sprig["phase"]) * 3.0 * S
            pts = sprig["pts"] * sp_t
            px = sprig["x"] + pts[:, 0] + sway_fx
            py = sprig["y"] + pts[:, 1]
            twinkle = 0.75 + 0.25 * math.sin(t * 3.5 + sprig["phase"])
            col = np.array([255, 250, 235], dtype=float) * (sp_t * twinkle)
            add(px, py, 60.0, np.broadcast_to(col, (len(px), 3)))

    # 7. Satin Ribbon & Bow (forms as stems reach tie point)
    rib_progress = float(smooth((t - 2.0) / 2.2))
    if rib_progress > 0.01:
        rib_mask = rib_u <= rib_progress
        if rib_mask.any():
            shimmer = 0.95 + 0.08 * math.sin(t * 2.0)
            add(rib_x[rib_mask], rib_y[rib_mask], rib_z[rib_mask], rib_col[rib_mask] * shimmer)

    # 8. Flowers Blooming (Staggered Opening & 3D Pointillism)
    for f_idx, fl_obj in enumerate(flower_data):
        fl_info = fl_obj["info"]
        t_s = fl_info["t_start"]
        dur = fl_info["duration"]

        # Current receptacle head location
        hx, hy = eval_stem_spline(f_idx, np.array([min(1.0, stem_progress)]), t)
        hx, hy = float(hx[0]), float(hy[0])

        e = smooth((t - t_s) / dur)
        rev = float(smooth((t - t_s + 0.4) / 1.7))

        if rev > 0.01:
            # Dynamic flower orientation with gentle breathing sway
            breeze = math.sin(t * 1.1 + f_idx * 1.2) * 0.04
            pitch = fl_info["base_pitch"] + breeze
            yaw = fl_info["base_yaw"] + breeze * 0.6
            roll = fl_info["base_roll"] + breeze * 0.4
            R_mat = get_rotation_matrix(pitch, yaw, roll)

            # Render Petals
            for p in fl_obj["petals"]:
                Ls = p["L"] * (0.45 + 0.55 * e) * (0.35 + 0.65 * rev)
                a0 = lerp(p["ac"], p["ao"], e)
                curl = (0.12 + 0.88 * e) * p["curl"]
                us, r, h = midrib(Ls, a0, curl)

                pu, pv = p["pu"], p["pv"]
                mk = (pu <= rev) & p["keep"]
                u_pts = pu[mk]
                v_pts = pv[mk]
                pr_pts = p["prof"][mk]

                rr = np.interp(u_pts, us, r)
                hh = np.interp(u_pts, us, h)
                wid = p["Wm"] * (0.55 + 0.45 * e) * pr_pts * (0.35 + 0.65 * rev)
                ph = p["phi"]

                # Local petal coordinates
                X = rr * math.cos(ph) - v_pts * wid * math.sin(ph)
                Z = rr * math.sin(ph) + v_pts * wid * math.cos(ph)
                Y = hh + (v_pts ** 2) * wid * (0.30 * (1.0 - e) - 0.25 * e)

                # Rotate via flower orientation matrix
                P_local = np.stack([X, Y, Z], axis=0)
                P_rot = R_mat @ P_local

                Xp = P_rot[0]
                Yp = P_rot[1]
                Zp = P_rot[2]

                # Depth shading
                shade = 0.55 + 0.45 * np.clip(Zp / p["L"] * 0.85 + 0.5, 0.0, 1.0)
                col = p["base"][mk].copy()
                tint = ((1.0 - e) * np.clip(u_pts * 1.3, 0.0, 1.0) * 0.6)[:, None]
                col = col * (1.0 - tint) + np.array([135, 205, 125]) * tint

                # Add to buffer
                add(hx + Xp, hy - Yp, Zp + (f_idx * 15.0), col * shade[:, None])

            # Render Stamens & Pollen Anthers
            if e > 0.28:
                sr = float(smooth((e - 0.28) / 0.42))
                for sdat in fl_obj["stam"]:
                    Ls = 185.0 * fl_info["scale"] * (0.4 + 0.6 * e) * sr
                    us, r, h = midrib(Ls, lerp(0.15, 0.60, e), 0.55 * e)
                    u_s = rng.random(40)
                    rr = np.interp(u_s, us, r)
                    hh = np.interp(u_s, us, h)
                    ph = sdat["phi"]

                    st_px = rr * math.cos(ph)
                    st_pz = rr * math.sin(ph)
                    st_py = hh

                    P_st = R_mat @ np.stack([st_px, st_py, st_pz], axis=0)
                    add(hx + P_st[0], hy - P_st[1], P_st[2] + 20.0,
                        np.broadcast_to(np.array([245, 235, 195]), (40, 3)).astype(float))

                    # Golden pollen anther tips
                    tx_pt = r[-1] * math.cos(ph)
                    tz_pt = r[-1] * math.sin(ph)
                    ty_pt = h[-1]
                    P_tip = R_mat @ np.array([tx_pt, ty_pt, tz_pt])

                    an = sdat["an"] * 4.5 * S
                    ac = np.broadcast_to(np.array([255, 160, 45]), (30, 3)).astype(float) * (0.8 + 0.4 * rng.random((30, 1)))
                    add(hx + P_tip[0] + an[:, 0], hy - P_tip[1] + an[:, 1], P_tip[2] + 25.0, ac)

    # 9. Floating Glowing Pollen & Drifting Firefly Particles
    for i in range(NF):
        src_fl = f_fl_source[i]
        fl_info = FLOWERS[src_fl]
        t_s = fl_info["t_start"]
        e_src = smooth((t - t_s) / fl_info["duration"])

        if e_src > 0.5:
            fa = float(smooth((e_src - 0.5) / 0.4))
            q = (t * f_sp[i] + f_off[i]) % 1.0
            shx, shy = eval_stem_spline(src_fl, np.array([1.0]), t)
            shx, shy = float(shx[0]), float(shy[0])

            fx = shx + f_dr[i] * q + math.sin(q * 7.5 + f_ph[i]) * 35.0 * S
            fy = (shy - 80.0 * S) + q * (gy - shy + 120.0 * S)
            fade = (1.0 - q) * fa
            pcol = np.array([255, 205, 95]) if (f_ph[i] > 3.1) else np.array([255, 165, 215])
            add(np.array([fx]), np.array([fy]), 350.0, (pcol * fade).reshape(1, 3))

    # --- Depth Sort & Splat Rendering ---
    x = np.concatenate([p[:, 0] for p in P_list])
    y = np.concatenate([p[:, 1] for p in P_list])
    z = np.concatenate(Z_list)
    c = np.concatenate(C_list)

    # Sort back-to-front
    order = np.argsort(z, kind='stable')
    x = x[order]
    y = y[order]
    c = np.clip(c[order], 0, 255).astype(np.uint8)

    ix = x.astype(int)
    iy = y.astype(int)
    valid = (ix >= 0) & (ix < W - 2) & (iy >= 0) & (iy < H - 2)

    ix, iy, c = ix[valid], iy[valid], c[valid]

    # Clear buffer to background
    buf[:] = BG

    # 2x2 Pointillism Particle Splat
    buf[ix, iy] = c
    buf[ix + 1, iy] = c
    buf[ix, iy + 1] = c
    buf[ix + 1, iy + 1] = c

def glow(screen):
    """Smooth additive glow/bloom post-processing effect."""
    small = pygame.transform.smoothscale(screen, (W // 10, H // 10))
    big = pygame.transform.smoothscale(small, (W, H))
    screen.blit(big, (0, 0), special_flags=pygame.BLEND_RGB_ADD)

def main():
    pygame.init()

    # Headless rendering mode: python bouquet.py --frame <time> <output.png>
    if len(sys.argv) >= 4 and sys.argv[1] == '--frame':
        os.environ['SDL_VIDEODRIVER'] = 'dummy'
        pygame.display.init()
        screen = pygame.display.set_mode((W, H))
        buf = np.zeros((W, H, 3), np.uint8)
        render(float(sys.argv[2]), buf)
        pygame.surfarray.blit_array(screen, buf)
        glow(screen)
        pygame.image.save(screen, sys.argv[3])
        print(f"Frame at t={sys.argv[2]} saved to {sys.argv[3]}")
        return

    # Interactive windowed display
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("Pointillism Blooming Bouquet")
    clock = pygame.time.Clock()
    buf = np.zeros((W, H, 3), np.uint8)
    t = 0.0
    paused = False

    while True:
        dt = clock.tick(FPS) / 1000.0
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT or (ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE):
                pygame.quit()
                return
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_r:
                    t = 0.0
                elif ev.key == pygame.K_SPACE:
                    paused = not paused
                elif ev.key == pygame.K_s:
                    pygame.image.save(screen, "bouquet_screenshot.png")
                    print("Saved bouquet_screenshot.png")

        if not paused:
            t += dt
            if LOOP_AT and t > LOOP_AT:
                t = 0.0

        render(t, buf)
        pygame.surfarray.blit_array(screen, buf)
        glow(screen)
        pygame.display.flip()

if __name__ == "__main__":
    main()
