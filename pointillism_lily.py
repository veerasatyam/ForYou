import sys, os, math
import numpy as np
import pygame

W, H = 720, 1280
FPS = 60
T_STEM = 4.0
T_B0, T_B1 = 5.0, 15.0
LOOP_AT = 0
BG = (4, 2, 10)
S = W / 720.0

rng = np.random.default_rng(11)
gx, gy = W / 2, H * 0.82
HS = 380 * S

def smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)

def lerp(a, b, t):
    return a + (b - a) * t

def midrib(L, a0, curl, K=40):
    us = np.linspace(0, 1, K + 1)
    al = a0 + curl * us ** 1.6
    ds = L / K
    r = np.concatenate([[0], np.cumsum(np.sin(al[1:])) * ds])
    h = np.concatenate([[0], np.cumsum(np.cos(al[1:])) * ds])
    return us, r, h

NP = 2300
petals = []
for k in range(6):
    outer = (k % 2 == 0)
    pu = rng.random(NP) ** 0.85
    pv = rng.uniform(-1, 1, NP)
    prof = np.sin(np.pi * pu ** 0.7) ** 0.9
    keep = np.abs(pv) <= 1
    stops = np.array([0, .35, .7, 1])
    base = np.stack([
        np.interp(pu, stops, [205, 255, 255, 255]),
        np.interp(pu, stops, [40, 95, 150, 195]),
        np.interp(pu, stops, [125, 165, 205, 228]),
    ], axis=1)

    mid = (np.abs(pv) < 0.07) & (pu < 0.55)
    base[mid] = (235, 225, 150)
    spot = (rng.random(NP) < 0.10) & (pu < 0.6) & (np.abs(pv) < 0.75) & ~mid
    base[spot] = (140, 15, 80)
    edge = np.abs(pv) > 0.88
    base[edge] *= 1.08
    base *= (0.82 + 0.35 * rng.random((NP, 1)))
    petals.append(dict(
        phi=math.radians(k * 60 + 8), L=(300 if outer else 280) * S,
        Wm=(64 if outer else 72) * S, ac=0.10 if outer else 0.05,
        ao=1.05 if outer else 0.82, curl=0.95 if outer else 0.75,
        pu=pu, pv=pv, prof=prof, base=base, keep=keep))

NS = 3200
st_s = rng.random(NS)
st_dx = rng.normal(0, 1, NS) * (3.2 * S) * (1 - 0.5 * st_s)
st_col = np.stack([lerp(40, 120, st_s), lerp(150, 215, st_s), lerp(95, 120, st_s)], axis=1)
st_col *= (0.8 + 0.4 * rng.random((NS, 1)))

leaves = []
for i, (s0, Lf, side) in enumerate([(0.10, 190, 1), (0.24, 175, -1), (0.40, 150, 1), (0.56, 120, -1)]):
    n = 900
    u = rng.random(n) ** 0.9
    v = rng.uniform(-1, 1, n)
    prof = np.sin(np.pi * u ** 0.8) ** 0.8
    col = np.stack([lerp(40, 140, u), lerp(160, 235, u), lerp(100, 140, u)], axis=1)
    col[np.abs(v) < 0.08] = (190, 240, 170)
    col *= (0.8 + 0.4 * rng.random((n, 1)))
    leaves.append(dict(s0=s0, L=Lf * S, side=side, u=u, v=v, prof=prof, col=col))

NG = 5000
so_dx = rng.uniform(-340, 340, NG) * S
mound = (1 - (so_dx / (340 * S)) ** 2) * 55 * S
so_y = gy - mound * rng.random(NG) ** 0.5 + rng.normal(0, 1.5, NG)
so_col = np.stack([lerp(70, 140, rng.random(NG)), lerp(55, 100, rng.random(NG)), lerp(80, 120, rng.random(NG))], axis=1)

ND = 450
d_x = rng.random(ND) * W; d_y = rng.random(ND) * H
d_sp = rng.uniform(6, 22, ND) * S; d_ph = rng.random(ND) * 6.28; d_f = rng.uniform(1, 4, ND)

ang_ring = rng.random(1100) * 6.28
ang_c = [rng.random(260) * 6.28 for _ in range(6)]

NF = 140
f_off = rng.random(NF); f_ph = rng.random(NF) * 6.28
f_dr = rng.uniform(-80, 80, NF) * S; f_sp = rng.uniform(0.05, 0.12, NF)

stam = [dict(phi=math.radians(k * 60 + 38), jit=rng.normal(0, 1, (45, 1)),
             an=rng.normal(0, 1, (35, 2))) for k in range(6)]

def stem_x(s, t):
    sway = 10 * S * math.sin(0.9 * t)
    return gx + 30 * S * np.sin(2.2 * s) + sway * s ** 2

def stem_y(s):
    return gy - s * HS

def render(t, buf):
    P, Zs, C = [], [], []

    def add(x, y, z, col):
        P.append(np.stack([x, y], 1)); Zs.append(np.broadcast_to(z, x.shape).astype(float)); C.append(col)

    g = smooth(t / T_STEM)
    e = smooth((t - T_B0) / (T_B1 - T_B0))
    rev = float(smooth((t - T_STEM + 0.3) / 1.6))

    hx, hy = float(stem_x(1.0, t)), float(stem_y(1.0))

    tw = 0.35 + 0.65 * (np.sin(t * d_f + d_ph) > 0.2)
    yy = (d_y - t * d_sp) % H
    add(d_x, yy, -1000, np.stack([255 * tw, 200 * tw, 235 * tw], 1) * 0.55)

    ha = float(smooth((t - T_B0 + 1.5) / 4.0)) * 0.9
    if ha > 0.01:
        cx0, cy0 = hx, hy - 90 * S
        R = 300 * S
        rot = t * 0.12
        a = ang_ring + rot
        add(cx0 + R * np.cos(a), cy0 + R * np.sin(a), -900,
            np.broadcast_to(np.array([255, 190, 225]) * ha * 0.7, (len(a), 3)))
        for k, ac in enumerate(ang_c):
            ca = rot * 1.3 + k * math.pi / 3
            ox, oy = cx0 + R * math.cos(ca), cy0 + R * math.sin(ca)
            a = ac + rot
            add(ox + R * 0.5 * np.cos(a), oy + R * 0.5 * np.sin(a), -900,
                np.broadcast_to(np.array([255, 170, 215]) * ha * 0.45, (len(a), 3)))

    add(so_dx + gx, so_y, -500, so_col * 0.8)

    m = st_s <= g
    if m.any():
        s = st_s[m]
        add(stem_x(s, t) + st_dx[m], stem_y(s), -100, st_col[m])

    for lf in leaves:
        lg = float(np.clip((g - lf['s0']) * 2.5, 0, 1))
        if lg <= 0.01:
            continue
        L = lf['L'] * lg
        us, r, h = midrib(L, 0.85, 1.1)
        u, v = lf['u'], lf['v']
        rr, hh = np.interp(u, us, r), np.interp(u, us, h)
        wid = 15 * S * lf['prof'] * lg
        bx, by = float(stem_x(lf['s0'], t)), float(stem_y(lf['s0']))
        sway = math.sin(t * 1.2 + lf['s0'] * 5) * 0.03
        x = bx + lf['side'] * (rr + v * wid * 0.35) + sway * hh * lf['side']
        y = by - hh + v * wid
        add(x, y, -90, lf['col'])

    if rev > 0.01:
        psi = 0.25 + t * 0.22
        tau = 0.5
        cp, sp = math.cos(psi), math.sin(psi)
        ct, st = math.cos(tau), math.sin(tau)
        sway_t = math.sin(t * 0.8) * 0.02
        for p in petals:
            Ls = p['L'] * (0.45 + 0.55 * e) * (0.35 + 0.65 * rev)
            a0 = lerp(p['ac'], p['ao'], e)
            curl = (0.12 + 0.88 * e) * p['curl']
            us, r, h = midrib(Ls, a0, curl)
            pu, pv = p['pu'], p['pv']
            mk = (pu <= rev) & p['keep']
            u, v, pr = pu[mk], pv[mk], p['prof'][mk]
            rr, hh = np.interp(u, us, r), np.interp(u, us, h)
            wid = p['Wm'] * (0.55 + 0.45 * e) * pr * (0.35 + 0.65 * rev)
            ph = p['phi']
            X = rr * math.cos(ph) - v * wid * math.sin(ph)
            Z = rr * math.sin(ph) + v * wid * math.cos(ph)
            Y = hh + (v ** 2) * wid * (0.30 * (1 - e) - 0.25 * e)
            Xp = X * cp + Z * sp
            Zp = -X * sp + Z * cp
            sy = Y * ct - Zp * st
            shade = 0.55 + 0.45 * np.clip(Zp / p['L'] * 0.8 + 0.5, 0, 1)
            col = p['base'][mk].copy()
            tint = ((1 - e) * np.clip(u * 1.3, 0, 1) * 0.6)[:, None]
            col = col * (1 - tint) + np.array([135, 205, 125]) * tint
            add(hx + Xp + sway_t * sy, hy - sy, Zp, col * shade[:, None])

        if e > 0.28:
            sr = float(smooth((e - 0.28) / 0.4))
            for sdat in stam:
                Ls = 215 * S * (0.4 + 0.6 * e) * sr
                us, r, h = midrib(Ls, lerp(0.15, 0.62, e), 0.55 * e)
                u = rng.random(45)
                rr, hh = np.interp(u, us, r), np.interp(u, us, h)
                ph = sdat['phi']
                X, Z, Y = rr * math.cos(ph), rr * math.sin(ph), hh
                Xp = X * cp + Z * sp; Zp = -X * sp + Z * cp
                sy = Y * ct - Zp * st
                add(hx + Xp, hy - sy, Zp + 5, np.broadcast_to(np.array([245, 235, 200]), (45, 3)).astype(float))

                tx, tz, ty = r[-1] * math.cos(ph), r[-1] * math.sin(ph), h[-1]
                txp = tx * cp + tz * sp; tzp = -tx * sp + tz * cp
                tsy = ty * ct - tzp * st
                an = sdat['an'] * 5 * S
                ac = np.broadcast_to(np.array([255, 150, 40]), (35, 3)).astype(float) * (0.8 + 0.4 * rng.random((35, 1)))
                add(hx + txp + an[:, 0] * 1.6, hy - tsy + an[:, 1] * 0.7, tzp + 6, ac)

    if e > 0.6:
        fa = float(smooth((e - 0.6) / 0.4))
        q = (t * f_sp + f_off) % 1.0
        fx = hx + f_dr * q + np.sin(q * 7 + f_ph) * 25 * S
        fy = (hy - 110 * S) + q * (gy - hy + 90 * S)
        fade = (1 - q) * fa
        pc = np.where((f_ph > 3.1)[:, None], np.array([255, 190, 80]), np.array([255, 150, 205])) * fade[:, None]
        add(fx, fy, 300, pc)

    x = np.concatenate([p[:, 0] for p in P]); y = np.concatenate([p[:, 1] for p in P])
    z = np.concatenate(Zs); c = np.concatenate(C)
    o = np.argsort(z, kind='stable')
    x, y, c = x[o], y[o], np.clip(c[o], 0, 255).astype(np.uint8)
    ix, iy = x.astype(int), y.astype(int)
    ok = (ix >= 0) & (ix < W - 2) & (iy >= 0) & (iy < H - 2)
    ix, iy, c = ix[ok], iy[ok], c[ok]
    buf[:] = BG
    buf[ix, iy] = c
    buf[ix + 1, iy] = c
    buf[ix, iy + 1] = c

def glow(screen):
    small = pygame.transform.smoothscale(screen, (W // 10, H // 10))
    big = pygame.transform.smoothscale(small, (W, H))
    screen.blit(big, (0, 0), special_flags=pygame.BLEND_RGB_ADD)

def main():
    pygame.init()

    if len(sys.argv) >= 4 and sys.argv[1] == '--frame':
        os.environ['SDL_VIDEODRIVER'] = 'dummy'
        pygame.display.init()
        screen = pygame.display.set_mode((W, H))
        buf = np.zeros((W, H, 3), np.uint8)
        render(float(sys.argv[2]), buf)
        pygame.surfarray.blit_array(screen, buf)
        glow(screen)
        pygame.image.save(screen, sys.argv[3])
        return
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("Pointillism Lily")
    clock = pygame.time.Clock()
    buf = np.zeros((W, H, 3), np.uint8)
    t, paused = 0.0, False
    while True:
        dt = clock.tick(FPS) / 1000.0
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT or (ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE):
                pygame.quit(); return
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_r: t = 0.0
                if ev.key == pygame.K_SPACE: paused = not paused
        if not paused:
            t += dt
            if LOOP_AT and t > LOOP_AT: t = 0.0
        render(t, buf)
        pygame.surfarray.blit_array(screen, buf)
        glow(screen)
        pygame.display.flip()

if __name__ == "__main__":
    main()
