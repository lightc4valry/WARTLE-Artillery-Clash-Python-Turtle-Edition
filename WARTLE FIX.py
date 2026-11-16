import math
import random
import time
import turtle

# ==========================================
# 1. KONFIGURASI & SETUP LAYAR
# ==========================================
screen = turtle.Screen()
screen.title("WARTLE - War Turtle Artillery Game")
screen.bgcolor("#070b1f")
screen.setup(width=900, height=550)
screen.tracer(0)

GROUND_Y = -150
BARREL_LEN = 30
G = 0.8
SPEED_SCALE = 0.3
DT = 0.5
HIT_W = 28
DMG = 25
EDGE = 400
SKILL_USES = 3

LEVELS = ["NORMAL", "HARD", "BRUTAL"]
LEVEL_COL = ["#a6e3a1", "#f9e2af", "#f38ba8"]

SK = {
    "BIASA": ("#fab387", "Tembakan biasa"),
    "PERISAI": ("#89dceb", "Kebal terhadap 1 serangan berikutnya"),
    "OBAT": ("#a6e3a1", "Pulihkan 30 HP"),
    "LEDAK": ("#f38ba8", "Tembakan meledak besar & melubangi tanah"),
    "TIGA": ("#f9e2af", "Peluru pecah jadi 3 di puncak lintasan"),
    "TELEPORT": ("#cba6f7", "Tembak lalu pindah ke titik jatuhnya peluru"),
    "GRAVITASI": ("#fab387", "Ubah gravitasi selama 2 giliran"),
    "MEDAN": ("#8fd48a", "Acak ulang bentuk tanah"),
    "DORONG": ("#74c7ec", "Dorong lawan mundur (tanpa damage)"),
}
SKILLS = [k for k in SK if k != "BIASA"]
UTIL = ("PERISAI", "OBAT", "GRAVITASI", "MEDAN", "DORONG")
COLORS = [("#f38ba8", "#a8506a", "#fbc2d1"), ("#89b4fa", "#4b6fb3", "#c3dbff")]

P = [
    {"x": -350, "hp": 100, "angle": 45, "power": 60, "score": 0, "skill": "", "uses": 0, "shield": False},
    {"x": 350, "hp": 100, "angle": 45, "power": 60, "score": 0, "skill": "", "uses": 0, "shield": False},
]
mode, level, cur, state = "bot", 0, 0, "menu"
bot_error = 0.15
wind, gmul, gturns = 0.0, 1.0, 0
H = [GROUND_Y] * 91

def name(i):
    return ("KAMU" if i == 0 else "BOT") if mode == "bot" else f"PEMAIN {i + 1}"

def heading(i, a=None):
    a = P[i]["angle"] if a is None else a
    return a if i == 0 else 180 - a

def ground(x):
    f = max(0, min(90, (x + 450) / 10))
    k = int(f)
    k2 = min(90, k + 1)
    return H[k] + (H[k2] - H[k]) * (f - k)

def py(i):
    return ground(P[i]["x"]) + 23

# ==========================================
# 2. FUNGSI BANTUAN GAMBAR
# ==========================================
def lerp_color(c1, c2, t):
    a, b = [[int(c[k:k + 2], 16) for k in (1, 3, 5)] for c in (c1, c2)]
    t = max(0.0, min(1.0, t))
    return "#%02x%02x%02x" % tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

def poly(t, pts, fill, outline=None):
    t.penup()
    t.goto(pts[0])
    t.color(outline or fill, fill)
    t.pendown()
    t.begin_fill()
    for p in pts[1:]: t.goto(p)
    t.goto(pts[0])
    t.end_fill()
    t.penup()

def rect(t, x, y, w, h, fill, outline=None):
    poly(t, [(x, y), (x + w, y), (x + w, y + h), (x, y + h)], fill, outline)

def new_turtle():
    t = turtle.Turtle()
    t.hideturtle()
    t.penup()
    t.speed(0)
    return t

def write(t, x, y, text, color, size=12, style="bold", align="center"):
    t.color(color)
    t.goto(x, y)
    t.write(text, align=align, font=("Arial", size, style))

# ==========================================
# 3. LATAR BELAKANG & TANAH
# ==========================================
def draw_scenery():
    s = new_turtle()
    top, bottom, bands = 275, GROUND_Y, 28
    bh = (top - bottom) / bands
    for i in range(bands):
        rect(s, -450, top - (i + 1) * bh - 1, 900, bh + 2, lerp_color("#070b1f", "#5a3a7a", i / (bands - 1)))
    rect(s, -450, -275, 900, 126, "#5a3a7a")
    rnd = random.Random(7)
    for _ in range(70):
        s.goto(rnd.randint(-440, 440), rnd.randint(-20, 265))
        s.dot(rnd.choice([2, 2, 3]), "#f5f0ff")
    s.goto(340, 195); s.dot(54, "#f5e6c8")
    s.goto(355, 203); s.dot(48, lerp_color("#070b1f", "#5a3a7a", (275 - 203) / (275 - GROUND_Y)))
    poly(s, [(-450, -275), (-450, -40), (-370, 10), (-290, -60), (-200, 40), (-100, -50), (0, 20), (110, -70), (210, 30), (320, -40), (450, 0), (450, -275)], "#241f4a")
    poly(s, [(-450, -275), (-450, -90), (-330, -40), (-240, -100), (-120, -60), (-20, -110), (100, -50), (220, -105), (330, -55), (450, -95), (450, -275)], "#2f2a5e")

draw_scenery()

land = new_turtle()
tank_t = [new_turtle(), new_turtle()]
trail = [new_turtle(), new_turtle()]
pointer, hud, fx, msg, ui = (new_turtle() for _ in range(5))

bullets = [new_turtle() for _ in range(3)]
for b in bullets:
    b.shape("circle")
    b.shapesize(0.6, 0.6)
    b.hideturtle()

def make_terrain():
    global H
    if level == 0:
        H = [GROUND_Y] * 91
        return
    amp = 1.0 if level == 1 else 1.5
    ph = [random.uniform(0, 6.28) for _ in range(3)]
    ln = [random.uniform(55, 90), random.uniform(25, 40), random.uniform(12, 18)]
    am = [28, 14, 6 if level == 1 else 10]
    H = [max(-188, min(-80, -140 + amp * sum(a * math.sin((-450 + 10 * k) / l + p) for a, l, p in zip(am, ln, ph)))) for k in range(91)]

def draw_land():
    land.clear()
    top = [(-450 + 10 * k, H[k]) for k in range(91)]
    poly(land, [(-450, -275)] + top + [(450, -275)], "#5b3f2e")
    poly(land, [(-450, -275)] + [(x, y - 45) for x, y in top] + [(450, -275)], "#4a3226")
    poly(land, top + [(x, y - 9) for x, y in reversed(top)], "#5fa35a")
    land.color("#8fd48a")
    land.pensize(2)
    land.goto(top[0])
    land.pendown()
    for p in top: land.goto(p)
    land.penup()

def crater(x, r):
    for k in range(91):
        dx = abs(-450 + 10 * k - x)
        if dx < r:
            H[k] = max(-188, H[k] - int(math.sqrt(r * r - dx * dx) * 0.7))

# ==========================================
# 4. GAMBAR TANK, HUD, EFEK
# ==========================================
def muzzle(i, a=None):
    r = math.radians(heading(i, a))
    return (P[i]["x"] + BARREL_LEN * math.cos(r), py(i) + BARREL_LEN * math.sin(r))

def draw_tank(i):
    t = tank_t[i]
    main, dark, light = COLORS[i]
    x, g = P[i]["x"], ground(P[i]["x"])
    t.clear()
    t.goto(x, g + 23); t.color(dark); t.pensize(7); t.pendown(); t.goto(muzzle(i)); t.penup(); t.pensize(1)
    poly(t, [(x - 26, g), (x + 26, g), (x + 31, g + 6), (x + 26, g + 11), (x - 26, g + 11), (x - 31, g + 6)], dark)
    for dx in (-19, -6.5, 6.5, 19):
        t.goto(x + dx, g + 5.5); t.dot(8, light)
    poly(t, [(x - 20, g + 11), (x + 20, g + 11), (x + 15, g + 24), (x - 15, g + 24)], main, dark)
    t.goto(x, g + 13); t.setheading(0); t.color(dark, light); t.begin_fill(); t.circle(10); t.end_fill()
    t.goto(x, g + 23); t.dot(6, dark)
    if P[i]["shield"]:
        t.color(SK["PERISAI"][0]); t.pensize(3); t.goto(x + 40, g); t.setheading(90); t.pendown(); t.circle(40, 180); t.penup(); t.pensize(1)

def draw_pointer():
    pointer.clear()
    if state != "aim": return
    pointer.color("#f9e2af"); pointer.pensize(3)
    r = math.radians(heading(cur))
    x0, y0 = P[cur]["x"], py(cur)
    for k in range(3 + P[cur]["power"] // 12):
        a = BARREL_LEN + 8 + k * 14
        pointer.goto(x0 + a * math.cos(r), y0 + a * math.sin(r)); pointer.pendown()
        pointer.goto(x0 + (a + 8) * math.cos(r), y0 + (a + 8) * math.sin(r)); pointer.penup()

def hp_bar(x, y, hp, label, col, right=False):
    w = 210
    rect(hud, x, y, w, 16, "#1b1e36", "#3a3f6b")
    if hp > 0: rect(hud, x, y, w * hp / 100, 16, lerp_color("#f38ba8", "#a6e3a1", hp / 100))
    write(hud, x + (w if right else 0), y + 20, label, col, 11, align="right" if right else "left")

def draw_hud():
    hud.clear()
    if state == "menu": return
    hp_bar(-430, 235, P[0]["hp"], name(0), COLORS[0][0])
    hp_bar(220, 235, P[1]["hp"], name(1), COLORS[1][0], True)
    write(hud, 0, 232, f"{P[0]['score']}  :  {P[1]['score']}", "#f9e2af", 18)
    p = P[cur]
    if level == 2:
        for i, (x, al) in enumerate([(-430, "left"), (430, "right")]):
            s = P[i]["skill"]
            write(hud, x, 213, f"{s}  " + "●" * P[i]["uses"] + "○" * (SKILL_USES - P[i]["uses"]), SK[s][0], 11, align=al)
        write(hud, 0, 188, f"Angin {'►' if wind > 0 else '◄'} {abs(wind) * 1000:.0f}   Gravitasi {gmul}x", "#a6adc8", 10, "normal")
    if state != "gameover":
        write(hud, 0, 208, f"Giliran: {name(cur)}   [{LEVELS[level]}]", COLORS[cur][0])

    rect(hud, -430, -270, 860, 74, "#12142b", COLORS[cur][0])
    write(hud, -400, -222, "SUDUT", "#a6adc8", 10, align="left")
    write(hud, -400, -258, f"{p['angle']}°", COLORS[cur][2], 22, align="left")
    bx, by, bw = -170, -250, 340
    write(hud, bx, by + 38, "POWER", "#a6adc8", 10, align="left")
    write(hud, bx + bw, by + 38, f"{p['power']}", "white", 12, align="right")
    rect(hud, bx, by + 8, bw, 16, "#1b1e36", "#3a3f6b")
    for k in range(max(1, int(bw * p["power"] / 100 // 4))):
        rect(hud, bx + k * 4, by + 9, 3, 14, lerp_color("#a6e3a1", "#f38ba8", k * 4 / bw))
    hints = ["▲▼ Sudut   ◄► Power", "SPASI  Tembak"] + (["S  Skill"] if level == 2 else [])
    for k, txt in enumerate(hints):
        write(hud, 420, -226 - k * 17, txt, "#a6adc8", 10, "normal", "right")

def render():
    draw_tank(0); draw_tank(1); draw_hud(); draw_pointer(); screen.update()

def explosion(x, y, big=True):
    for r in range(6, 44 if big else 18, 6):
        fx.clear(); fx.goto(x, y); fx.dot(r * 2, "#fab387"); fx.dot(r * 1.3, "#f9e2af"); fx.dot(r * 0.6, "#ffffff")
        screen.update(); time.sleep(0.02)
    fx.clear(); screen.update()

def message(text, color, secs=1.0):
    msg.clear()
    write(msg, 2, 118, text, "#000000", 18)
    write(msg, 0, 120, text, color, 18)
    screen.update(); time.sleep(secs); msg.clear(); screen.update()

# ==========================================
# 5. FISIKA PELURU
# ==========================================
def launch(i, ang, pw):
    x, y = muzzle(i, ang)
    r = math.radians(ang)
    sp = pw * SPEED_SCALE
    return [x, y, sp * math.cos(r) * (1 if i == 0 else -1), sp * math.sin(r)]

def step(b):
    b[0] += b[2] * DT; b[1] += b[3] * DT
    b[2] += wind * DT; b[3] -= G * gmul * DT

def simulate(i, ang, pw):
    b = launch(i, ang, pw)
    for n in range(500):
        step(b)
        if (n > 2 and b[1] <= ground(b[0]) + 2) or abs(b[0]) > 470: break
    return b[0]

def flight(i, pw, ammo, trace):
    tx, gy = P[1 - i]["x"], ground(P[1 - i]["x"])
    dmg = {"TIGA": 15, "TELEPORT": 15}.get(ammo, DMG)
    bs = [launch(i, P[i]["angle"], pw) + [dmg, bullets[0]]]
    for t in bullets: t.color(SK[ammo][0])
    bullets[0].goto(bs[0][0], bs[0][1]); bullets[0].showturtle()
    imp, n, split = [], 0, ammo == "TIGA"
    while bs:
        n += 1
        for b in bs[:]:
            step(b); b[5].goto(b[0], b[1])
            if trace and n % 4 == 0:
                trail[i].goto(b[0], b[1]); trail[i].dot(4, COLORS[i][2])
            direct = abs(b[0] - tx) < HIT_W and gy - 2 < b[1] < gy + 38
            if direct or (n > 2 and b[1] <= ground(b[0]) + 2) or abs(b[0]) > 470:
                imp.append((b[0], b[1], direct, b[4]))
                b[5].hideturtle(); bs.remove(b)
        if split and bs and bs[0][3] <= 0:
            split = False
            b0 = bs[0]
            for k, (mv, dv) in enumerate([(1.25, 3), (1.0, 0)]):
                bs.append([b0[0], b0[1], b0[2] * mv, b0[3] + dv, b0[4], bullets[k + 1]])
                bullets[k + 1].showturtle()
            b0[2] *= 0.75
        if n % 2 == 0:
            screen.update(); time.sleep(0.012)
    return imp

# ==========================================
# 6. ALUR GILIRAN & KONTROL
# ==========================================
def retreat(j):
    away = 1 if j == 1 else -1
    x, target = P[j]["x"], P[j]["x"] + away * random.randint(70, 140)
    txt = "terdorong mundur!"
    if away * target > EDGE:
        target = away * EDGE if EDGE - away * x >= 30 else away * random.randint(60, 200)
        txt = "berpindah posisi!"
    message(f"{name(j)} {txt}", "#cba6f7", 0.5)
    d = 4 if target > x else -4
    while abs(target - P[j]["x"]) > 4:
        P[j]["x"] += d; draw_tank(j); screen.update(); time.sleep(0.01)
    P[j]["x"] = target; draw_tank(j); screen.update()

def shoot(i, pw, trace, ammo="BIASA"):
    global state, bot_error, gmul, gturns
    state = "flying"; pointer.clear()
    j = 1 - i
    if ammo != "BIASA": P[i]["uses"] -= 1

    if ammo in UTIL:
        if ammo == "PERISAI": P[i]["shield"] = True
        elif ammo == "OBAT": P[i]["hp"] = min(100, P[i]["hp"] + 30)
        elif ammo == "GRAVITASI": gmul, gturns = random.choice([0.5, 1.8]), 3
        elif ammo == "MEDAN": make_terrain(); draw_land()
        render(); message(f"{name(i)} memakai {ammo}!", SK[ammo][0], 0.9)
        if ammo == "DORONG": retreat(j)
        next_turn(); return

    if trace: trail[i].clear()
    imps = flight(i, pw, ammo, trace)
    ex, ey = P[j]["x"], ground(P[j]["x"]) + 12
    total = sum(dmg if (direct or (ammo == "LEDAK" and math.hypot(x - ex, y - ey) < 70)) else 0 for x, y, direct, dmg in imps)
    
    if level:
        for x, y, _, _ in imps: crater(x, 45 if ammo == "LEDAK" else 18)
        draw_land(); render()

    if ammo == "TELEPORT":
        nx = imps[0][0]
        P[i]["x"] = max(-420, min(-30, nx)) if i == 0 else max(30, min(420, nx))
        render(); message("TELEPORT!", SK[ammo][0], 0.6)

    if mode == "bot" and i == 1:
        bot_error = 0.15 if total else max(0.05, bot_error - 0.025)

    if total and P[j]["shield"]:
        P[j]["shield"] = False; render(); message("PERISAI menahan serangan!", SK["PERISAI"][0], 0.9)
    elif total:
        P[j]["hp"] -= total; P[i]["score"] += total * 4; draw_hud()
        if P[j]["hp"] <= 0: end_game(i); return
        message(f"{name(j)} TERKENA!  -{total} HP", COLORS[i][0], 0.6); retreat(j)
    else:
        message(f"{name(i)} meleset!", "#f9e2af", 0.7)
    next_turn()

def bot_turn():
    p = P[1]
    sk = "BIASA"
    if level == 2 and p["uses"] > 0 and random.random() < 0.4:
        if not (p["skill"] == "PERISAI" and p["shield"]) and not (p["skill"] == "OBAT" and p["hp"] > 70):
            sk = p["skill"]
    if sk in UTIL:
        render(); time.sleep(0.5); shoot(1, 0, False, sk); return
    tx = P[0]["x"]
    cand = sorted((abs(simulate(1, a, w) - tx), a, w) for a in range(30, 76, 5) for w in range(20, 101, 3))
    _, ang, pw = random.choice([c for c in cand if c[0] < 20] or cand[:1])
    pw = max(10, min(100, pw * random.uniform(1 - bot_error, 1 + bot_error)))
    p["angle"], p["power"] = ang, round(pw)
    render(); time.sleep(0.6); shoot(1, pw, False, sk)

def begin_turn():
    global state, wind, gmul, gturns
    if level == 2:
        wind = random.uniform(-0.05, 0.05)
        if gturns > 0:
            gturns -= 1
            if gturns == 0: gmul = 1.0
    else:
        wind, gmul, gturns = 0.0, 1.0, 0
    state = "bot_turn" if (mode == "bot" and cur == 1) else "aim"
    render()
    if state == "bot_turn": bot_turn()
    elif mode == "pvp": message(f"Giliran {name(cur)}", COLORS[cur][0], 0.5)

def next_turn():
    global cur
    cur = 1 - cur
    begin_turn()

def show_menu():
    global state
    state = "menu"; ui.clear()
    for t in trail: t.clear()
    make_terrain(); draw_land()
    P[0]["x"], P[1]["x"] = -350, 350
    P[0]["shield"] = P[1]["shield"] = False
    render()
    rect(ui, -300, -140, 600, 300, "#11132a", "#f38ba8")
    write(ui, 0, 85, "WARTLE", "#f38ba8", 42)
    write(ui, 0, 58, "Perang Artileri Kura-Kura Berbasis Giliran", "#cdd6f4", 13, "italic")
    write(ui, 0, 18, "[1]   Lawan BOT", COLORS[0][0], 18)
    write(ui, 0, -20, "[2]   Lawan TEMAN (gantian)", COLORS[1][0], 18)
    write(ui, 0, -62, f"[D]   Tingkat:  < {LEVELS[level]} >", LEVEL_COL[level], 16)
    write(ui, 0, -125, "▲ / ▼  Sudut      ◄ / ►  Power      SPASI  Tembak", "#a6adc8", 10, "normal")
    screen.update()

def reset_game(m):
    global mode, cur, bot_error, state, gmul, gturns
    mode, cur, bot_error, gmul, gturns = m, 0, 0.15, 1.0, 0
    state = "flying"; ui.clear()
    for t in trail: t.clear()
    make_terrain(); draw_land()
    P[0].update(x=random.randint(-340, -230), hp=100, angle=45, power=60, score=0, shield=False, skill="", uses=0)
    P[1].update(x=random.randint(230, 340), hp=100, angle=45, power=60, score=0, shield=False, skill="", uses=0)
    if level == 2:
        for p, s in zip(P, random.sample(SKILLS, 2)): p["skill"], p["uses"] = s, SKILL_USES
    render()
    if level == 2:
        rect(ui, -300, -30, 600, 165, "#11132a", "#f9e2af")
        write(ui, 0, 95, f"SKILL ACAK  (maks {SKILL_USES}x)", "#f9e2af", 16)
        for i in (0, 1): write(ui, 0, 58 - i * 40, f"{name(i)}:  {P[i]['skill']}", SK[P[i]['skill']][0], 14)
        screen.update(); time.sleep(3.0); ui.clear(); screen.update()
    begin_turn()

def end_game(winner):
    global state
    state = "gameover"; P[winner]["score"] += 200; pointer.clear(); draw_hud()
    title = ("KAMU MENANG!" if winner == 0 else "KAMU KALAH!") if mode == "bot" else f"{name(winner)} MENANG!"
    rect(ui, -230, -70, 460, 180, "#11132a", COLORS[winner][0])
    write(ui, 0, 35, title, COLORS[winner][0], 30)
    write(ui, 0, -5, f"Skor  {P[0]['score']} : {P[1]['score']}", "#cdd6f4", 16, "normal")
    write(ui, 0, -45, "[SPASI] Main lagi      [M] Menu", "#a6adc8", 12, "normal")
    screen.update()

def adjust(key, delta, lo, hi):
    if state == "aim":
        P[cur][key] = max(lo, min(hi, P[cur][key] + delta))
        render()

screen.listen()
screen.onkeypress(lambda: adjust("angle", 1, 5, 85), "Up")
screen.onkeypress(lambda: adjust("angle", -1, 5, 85), "Down")
screen.onkeypress(lambda: adjust("power", 1, 1, 100), "Right")
screen.onkeypress(lambda: adjust("power", -1, 1, 100), "Left")
screen.onkeypress(lambda: (reset_game(mode) if state == "gameover" else shoot(cur, P[cur]["power"], True)), "space")
screen.onkeypress(lambda: (shoot(cur, P[cur]["power"], True, P[cur]["skill"]) if state == "aim" and level == 2 and P[cur]["uses"] > 0 else None), "s")
screen.onkeypress(lambda: reset_game("bot") if state == "menu" else None, "1")
screen.onkeypress(lambda: reset_game("pvp") if state == "menu" else None, "2")
screen.onkeypress(lambda: (globals().update(level=(level + 1) % 3), show_menu()) if state == "menu" else None, "d")
screen.onkeypress(lambda: show_menu() if state == "gameover" else None, "m")

show_menu()
screen.mainloop()