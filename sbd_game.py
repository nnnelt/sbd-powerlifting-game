import math
import random
import sys

import pygame


pygame.init()
pygame.display.set_caption("SBD Game")
SCREEN = pygame.display.set_mode((1000, 700), pygame.RESIZABLE)
CLOCK = pygame.time.Clock()

BG = (17, 18, 28)
PANEL = (29, 31, 45)
PANEL_LIGHT = (39, 42, 59)
WHITE = (245, 246, 250)
MUTED = (158, 163, 182)
PINK = (255, 91, 165)
PURPLE = (155, 112, 255)
CYAN = (93, 218, 224)
GREEN = (116, 230, 163)
BAR_COLOR = (220, 225, 237)
FLOOR = (56, 61, 79)
SKIN = (238, 190, 159)
SKIN_SHADE = (191, 137, 113)

FONT = pygame.font.SysFont("Arial", 22, bold=True)
SMALL = pygame.font.SysFont("Arial", 16)
MEDIUM = pygame.font.SysFont("Arial", 28, bold=True)
LARGE = pygame.font.SysFont("Arial", 47, bold=True)

LIFTS = {
    "squat": {"title": "SQUAT", "accent": PINK, "hint": "Bar across your upper back"},
    "bench": {"title": "BENCH PRESS", "accent": PURPLE, "hint": "Paused on the chest, then press"},
    "deadlift": {"title": "DEADLIFT", "accent": CYAN, "hint": "Conventional stance, pull to lockout"},
}

state = "menu"
selected_lift = "squat"
weight_text = "60"
input_active = False
phase = "idle"
phase_started = 0
confetti = []
message = ""
message_until = 0
buttons = {}


def text(surface, value, font, color, pos, center=True):
    image = font.render(str(value), True, color)
    rect = image.get_rect(center=pos) if center else image.get_rect(topleft=pos)
    surface.blit(image, rect)
    return rect


def rounded(surface, rect, color, radius=16, border=None, width=1):
    pygame.draw.rect(surface, color, rect, border_radius=radius)
    if border:
        pygame.draw.rect(surface, border, rect, width, border_radius=radius)


def button(surface, label, rect, fill):
    rounded(surface, rect, fill, 13)
    text(surface, label, FONT, WHITE, rect.center)
    return rect


def line(surface, color, start, end, width=7):
    pygame.draw.line(surface, color, start, end, width)
    pygame.draw.circle(surface, color, (int(start[0]), int(start[1])), width // 2)
    pygame.draw.circle(surface, color, (int(end[0]), int(end[1])), width // 2)


def draw_stick_person(surface, points, color, width=8, head_radius=17):
    """Draw an athlete with a filled torso and rounded limbs."""
    shoulder = points["shoulder"]
    hip = points["hip"]
    dx = hip[0] - shoulder[0]
    dy = hip[1] - shoulder[1]
    length = max(1, math.hypot(dx, dy))
    px = -dy / length
    py = dx / length
    torso = [
        (shoulder[0] + px * 15, shoulder[1] + py * 15),
        (shoulder[0] - px * 15, shoulder[1] - py * 15),
        (hip[0] - px * 13, hip[1] - py * 13),
        (hip[0] + px * 13, hip[1] + py * 13),
    ]
    pygame.draw.polygon(surface, color, torso)
    pygame.draw.lines(surface, (255, 255, 255), False, torso[:2], 2)

    limb_width = max(12, width + 4)
    for a, b in (("shoulder", "elbow"), ("elbow", "wrist"),
                 ("hip", "knee"), ("knee", "ankle"),
                 ("hip", "knee2"), ("knee2", "ankle2")):
        if a in points and b in points:
            line(surface, SKIN, points[a], points[b], limb_width)

    for joint in ("elbow", "knee", "knee2", "wrist"):
        if joint in points:
            pygame.draw.circle(surface, SKIN,
                               (int(points[joint][0]), int(points[joint][1])),
                               limb_width // 2)

    head = points["head"]
    pygame.draw.circle(surface, color, (int(head[0]), int(head[1])), head_radius)
    pygame.draw.circle(surface, SKIN, (int(head[0]), int(head[1])), head_radius - 3)
    pygame.draw.circle(surface, BG, (int(head[0] + 5), int(head[1] - 2)), 2)


def draw_weight_plates(surface, x, y, accent, scale=1.0):
    # Plates are intentionally drawn as shapes so the project needs no image assets.
    for offset, radius, color in ((0, 30, accent), (13, 24, (235, 238, 247)), (24, 18, accent)):
        r = int(radius * scale)
        plate = pygame.Rect(int(x + offset * scale - r), int(y - r), r * 2, r * 2)
        pygame.draw.rect(surface, color, plate, border_radius=max(3, int(5 * scale)))
        pygame.draw.rect(surface, BG, plate, max(1, int(2 * scale)), border_radius=max(3, int(5 * scale)))
        pygame.draw.circle(surface, BG, (int(x + offset * scale), int(y)), max(2, int(4 * scale)))


def make_confetti():
    colors = [PINK, PURPLE, CYAN, GREEN, (255, 205, 92), WHITE]
    w, h = SCREEN.get_size()
    for _ in range(140):
        confetti.append([random.uniform(0, w), random.uniform(-h, 0), random.uniform(-1.5, 1.5),
                         random.uniform(2.0, 6.0), random.choice(colors), random.randint(4, 9)])


def draw_background(surface):
    surface.fill(BG)
    w, h = surface.get_size()
    # Quiet grid adds depth without distracting from the movement.
    for x in range(0, w, 50):
        pygame.draw.line(surface, (24, 26, 38), (x, 0), (x, h), 1)
    for y in range(0, h, 50):
        pygame.draw.line(surface, (24, 26, 38), (0, y), (w, y), 1)
    pygame.draw.circle(surface, (25, 23, 42), (w - 30, 25), min(250, h // 2), 0)


def draw_menu(surface):
    draw_background(surface)
    w, h = surface.get_size()
    text(surface, "SBD GAME", LARGE, WHITE, (w // 2, 78))
    text(surface, "nada eltahhan, with a touch of 'tism", SMALL, MUTED, (w // 2, 121))
    # Athlete mascot in a soft halo.
    pygame.draw.circle(surface, (37, 32, 57), (w // 2, 285), 106)
    points = {"head": (w // 2, 205), "shoulder": (w // 2, 244), "hip": (w // 2, 310),
              "elbow": (w // 2 - 42, 280), "wrist": (w // 2 - 57, 245),
              "knee": (w // 2 - 28, 365), "ankle": (w // 2 - 38, 420),
              "knee2": (w // 2 + 30, 365), "ankle2": (w // 2 + 43, 420)}
    draw_stick_person(surface, points, PINK, 10, 20)
    line(surface, BAR_COLOR, (w // 2 - 117, 239), (w // 2 + 117, 239), 7)
    draw_weight_plates(surface, w // 2 - 113, 239, PURPLE, .65)
    draw_weight_plates(surface, w // 2 + 91, 239, PURPLE, .65)
    labels = [("SQUAT", "squat"), ("BENCH PRESS", "bench"), ("DEADLIFT", "deadlift")]
    total = 3 * 230 + 2 * 18
    left = (w - total) // 2
    buttons.clear()
    for i, (label, key) in enumerate(labels):
        rect = pygame.Rect(left + i * 248, min(h - 155, 480), 230, 76)
        rounded(surface, rect, PANEL, 16, LIFTS[key]["accent"], 2)
        text(surface, label, FONT, WHITE, rect.center)
        buttons[key] = rect
    text(surface, "Choose a lift to get started", SMALL, MUTED, (w // 2, h - 38))


def draw_squat(surface, t, accent, weight):
    w, h = surface.get_size()
    floor_y = h - 125
    center_x = int(w * .49)
    # Squat: bar sits on the upper back; athlete descends and grinds back up.
    y_shift = 0
    torso_tilt = 0
    if phase in ("lower", "grind", "stand"):
        if phase == "lower":
            p = min(1, t / .65)
            y_shift = int(72 * p)
        elif phase == "grind":
            y_shift = 72 - int(10 * math.sin(t * 6))
            torso_tilt = 8
        elif phase == "stand":
            y_shift = int(72 * max(0, 1 - t / .55))
    shoulder = (center_x, floor_y - 240 + y_shift)
    hip = (center_x + torso_tilt, floor_y - 155 + y_shift)
    knee = (center_x - 62, floor_y - 72 + y_shift // 2)
    knee2 = (center_x + 66, floor_y - 72 + y_shift // 2)
    head = (center_x, shoulder[1] - 38)
    points = {"head": head, "shoulder": shoulder, "hip": hip,
              "elbow": (center_x - 60, shoulder[1] + 22), "wrist": (center_x - 91, shoulder[1] + 3),
              "knee": knee, "ankle": (center_x - 81, floor_y),
              "knee2": knee2, "ankle2": (center_x + 88, floor_y)}
    draw_stick_person(surface, points, accent, 9)
    bar_y = shoulder[1] + 3
    line(surface, BAR_COLOR, (center_x - 178, bar_y), (center_x + 178, bar_y), 7)
    draw_weight_plates(surface, center_x - 167, bar_y, accent, .72)
    draw_weight_plates(surface, center_x + 141, bar_y, accent, .72)
    text(surface, f"{weight} kg", SMALL, WHITE, (center_x, bar_y - 40))


def draw_bench(surface, t, accent, weight):
    w, h = surface.get_size()
    floor_y = h - 126
    cx = int(w * .50)
    bench_y = floor_y - 82
    pygame.draw.rect(surface, (82, 87, 108), (cx - 220, bench_y, 420, 19), border_radius=8)
    pygame.draw.line(surface, (82, 87, 108), (cx - 165, bench_y + 18), (cx - 175, floor_y), 10)
    pygame.draw.line(surface, (82, 87, 108), (cx + 165, bench_y + 18), (cx + 175, floor_y), 10)
    # Side view: head is on the left, body supported by the bench, feet planted.
    head = (cx - 185, bench_y - 30)
    shoulder = (cx - 145, bench_y - 12)
    hip = (cx + 47, bench_y - 8)
    bar_y = bench_y - 72
    if phase in ("lower", "grind", "stand"):
        if phase == "lower":
            bar_y = int(bench_y - 72 + 45 * min(1, t / .7))
        elif phase == "grind":
            bar_y = int(bench_y - 27 + 5 * math.sin(t * 8))
        elif phase == "stand":
            bar_y = int(bench_y - 27 - 45 * min(1, t / .55))
    points = {"head": head, "shoulder": shoulder, "hip": hip,
              "knee": (cx + 113, bench_y + 11), "ankle": (cx + 147, floor_y),
              "knee2": (cx + 171, bench_y + 10), "ankle2": (cx + 203, floor_y)}
    draw_stick_person(surface, points, accent, 9)

    # Draw both arms reaching to the bar; the shaded far arm adds depth.
    far_shoulder = (cx - 145, bench_y - 20)
    far_elbow = (cx - 88, bar_y + 24)
    far_wrist = (cx - 60, bar_y + 3)
    line(surface, SKIN_SHADE, far_shoulder, far_elbow, 14)
    line(surface, SKIN_SHADE, far_elbow, far_wrist, 14)

    near_shoulder = (cx - 145, bench_y - 7)
    near_elbow = (cx - 10, bar_y + 23)
    near_wrist = (cx + 28, bar_y + 3)
    line(surface, SKIN, near_shoulder, near_elbow, 16)
    line(surface, SKIN, near_elbow, near_wrist, 16)
    pygame.draw.circle(surface, SKIN, (int(far_wrist[0]), int(far_wrist[1])), 9)
    pygame.draw.circle(surface, SKIN, (int(near_wrist[0]), int(near_wrist[1])), 9)

    pygame.draw.arc(surface, WHITE, (head[0] - 17, head[1] - 17, 34, 34), 1.7, 4.8, 3)
    line(surface, BAR_COLOR, (cx - 90, bar_y), (cx + 130, bar_y), 7)
    draw_weight_plates(surface, cx - 80, bar_y, accent, .68)
    draw_weight_plates(surface, cx + 120, bar_y, accent, .68)
    text(surface, f"{weight} kg", SMALL, WHITE, (cx + 16, bar_y - 31))


def draw_deadlift(surface, t, accent, weight):
    w, h = surface.get_size()
    floor_y = h - 125
    cx = int(w * .50)
    if phase == "lower":
        progress = 0.025 * abs(math.sin(t * 8))
    elif phase == "grind":
        progress = min(1, t / 1.8)
    elif phase in ("stand", "celebrate"):
        progress = 1
    else:
        progress = 0

    def blend(start, end):
        return round(start + (end - start) * progress)

    # Blend from the hinged starting position to a fully upright lockout.
    bar_y = blend(floor_y - 11, floor_y - 130)
    shoulder = (blend(cx - 42, cx), blend(floor_y - 218, floor_y - 300))
    hip = (blend(cx + 45, cx), blend(floor_y - 128, floor_y - 207))
    knee = (blend(cx - 58, cx - 15), blend(floor_y - 58, floor_y - 112))
    knee2 = (blend(cx + 83, cx + 15), blend(floor_y - 61, floor_y - 112))
    ankle = (cx - 40, floor_y)
    ankle2 = (cx + 42, floor_y)
    elbow = (blend(cx - 10, cx - 28), blend(floor_y - 81, bar_y - 40))
    wrist = (blend(cx + 8, cx - 28), bar_y)

    points = {"head": (shoulder[0] - 19, shoulder[1] - 29), "shoulder": shoulder, "hip": hip,
              "elbow": elbow, "wrist": wrist,
              "knee": knee, "ankle": ankle,
              "knee2": knee2, "ankle2": ankle2}
    draw_stick_person(surface, points, accent, 9)
    line(surface, BAR_COLOR, (cx - 195, int(bar_y)), (cx + 195, int(bar_y)), 7)
    draw_weight_plates(surface, cx - 182, int(bar_y), accent, .75)
    draw_weight_plates(surface, cx + 155, int(bar_y), accent, .75)
    text(surface, f"{weight} kg", SMALL, WHITE, (cx, bar_y - 45))


def draw_scene(surface, t, weight):
    draw_background(surface)
    w, h = surface.get_size()
    data = LIFTS[selected_lift]
    text(surface, data["title"], MEDIUM, WHITE, (w // 2, 49))
    text(surface, data["hint"], SMALL, MUTED, (w // 2, 81))
    floor_y = h - 125
    pygame.draw.line(surface, FLOOR, (70, floor_y), (w - 70, floor_y), 3)
    if selected_lift == "squat":
        draw_squat(surface, t, data["accent"], weight)
    elif selected_lift == "bench":
        draw_bench(surface, t, data["accent"], weight)
    else:
        draw_deadlift(surface, t, data["accent"], weight)
    if phase == "celebrate":
        text(surface, "LIFT COMPLETE!", LARGE, GREEN, (w // 2, 145))
        text(surface, "LET'S GO!", FONT, WHITE, (w // 2, 190))
        for bit in confetti:
            bit[0] += bit[2]
            bit[1] += bit[3]
            pygame.draw.rect(surface, bit[4], (int(bit[0]), int(bit[1]), bit[5], bit[5] * 1.5), border_radius=2)
            if bit[1] > h:
                bit[0] = random.randrange(max(1, w))
                bit[1] = random.randrange(-80, -5)
    # Footer controls
    button(surface, "BACK", pygame.Rect(34, h - 72, 110, 44), PANEL_LIGHT)
    if phase in ("idle", "celebrate"):
        button(surface, "LIFT AGAIN", pygame.Rect(w - 184, h - 72, 150, 44), data["accent"])
    else:
        text(surface, "Stay tight…", SMALL, MUTED, (w // 2, h - 47))


def draw_setup(surface):
    draw_background(surface)
    w, h = surface.get_size()
    data = LIFTS[selected_lift]
    text(surface, data["title"], LARGE, WHITE, (w // 2, 78))
    text(surface, data["hint"], SMALL, MUTED, (w // 2, 120))
    pygame.draw.circle(surface, (35, 31, 53), (w // 2, 280), 122)
    # Static preview of the chosen setup.
    previous = phase
    globals()["phase"] = "idle"
    if selected_lift == "squat":
        draw_squat(surface, 0, data["accent"], weight_text or "60")
    elif selected_lift == "bench":
        draw_bench(surface, 0, data["accent"], weight_text or "60")
    else:
        draw_deadlift(surface, 0, data["accent"], weight_text or "60")
    globals()["phase"] = previous
    # Input panel
    panel = pygame.Rect(w // 2 - 205, h - 216, 410, 118)
    rounded(surface, panel, PANEL, 18)
    text(surface, "WEIGHT (KG)", SMALL, MUTED, (w // 2, panel.y + 28))
    field = pygame.Rect(w // 2 - 85, panel.y + 48, 170, 48)
    rounded(surface, field, (19, 21, 32), 10, data["accent"] if input_active else PANEL_LIGHT, 2)
    shown = weight_text + ("|" if input_active and pygame.time.get_ticks() % 1000 < 500 else "")
    text(surface, shown or "Type kg", FONT, WHITE if weight_text else MUTED, field.center)
    buttons["weight_field"] = field
    buttons["start"] = button(surface, "START LIFT", pygame.Rect(w // 2 - 100, h - 82, 200, 54), data["accent"])
    buttons["back"] = button(surface, "BACK", pygame.Rect(34, h - 72, 110, 44), PANEL_LIGHT)
    text(surface, "Type a number, then press Enter", SMALL, MUTED, (w // 2, h - 24))


def start_lift():
    global phase, phase_started, confetti, message, message_until
    if not weight_text.strip():
        message = "Enter a weight first"
        message_until = pygame.time.get_ticks() + 1800
        return False
    try:
        kg = float(weight_text)
        if not math.isfinite(kg) or kg <= 0 or kg > 999:
            raise ValueError
    except ValueError:
        message = "Enter a weight from 0.1 to 999 kg"
        message_until = pygame.time.get_ticks() + 2200
        return False
    phase = "lower"
    phase_started = pygame.time.get_ticks()
    confetti = []
    return True


def update_animation(now):
    global phase, phase_started, confetti
    if phase == "lower" and now - phase_started > 700:
        phase, phase_started = "grind", now
    elif phase == "grind":
        duration = 1800 if selected_lift == "deadlift" else 1400
        if now - phase_started > duration:
            phase, phase_started = "stand", now
    elif phase == "stand" and now - phase_started > 600:
        phase, phase_started = "celebrate", now
        make_confetti()
    elif phase == "celebrate" and now - phase_started > 8500:
        phase = "idle"
        confetti = []


def handle_click(pos):
    global state, selected_lift, input_active, phase, confetti
    if state == "menu":
        for key in ("squat", "bench", "deadlift"):
            if buttons.get(key) and buttons[key].collidepoint(pos):
                selected_lift = key
                state = "setup"
                return
    elif state == "setup":
        if buttons.get("weight_field") and buttons["weight_field"].collidepoint(pos):
            input_active = True
        elif buttons.get("start") and buttons["start"].collidepoint(pos):
            input_active = False
            if start_lift():
                state = "scene"
        elif buttons.get("back") and buttons["back"].collidepoint(pos):
            state = "menu"
            input_active = False
    elif state == "scene":
        w, h = SCREEN.get_size()
        if pos[1] > h - 84 and pos[0] < 160:
            state, phase, confetti = "setup", "idle", []
        elif phase in ("idle", "celebrate"):
            start_lift()


def main():
    global state, input_active, weight_text, selected_lift, phase, confetti, SCREEN
    running = True
    while running:
        now = pygame.time.get_ticks()
        dt = CLOCK.tick(60) / 1000
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEORESIZE:
                SCREEN = pygame.display.set_mode(event.size, pygame.RESIZABLE)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                handle_click(event.pos)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if state == "scene":
                        state, phase, confetti = "setup", "idle", []
                    elif state == "setup":
                        state, input_active = "menu", False
                elif state == "setup" and input_active:
                    if event.key == pygame.K_RETURN:
                        input_active = False
                        if start_lift():
                            state = "scene"
                    elif event.key == pygame.K_BACKSPACE:
                        weight_text = weight_text[:-1]
                    elif event.unicode and (event.unicode.isdigit() or event.unicode == "."):
                        if event.unicode != "." or "." not in weight_text:
                            if len(weight_text) < 6:
                                weight_text += event.unicode
                elif state == "setup" and event.key == pygame.K_RETURN:
                    if start_lift():
                        state = "scene"
                elif state == "scene" and event.key == pygame.K_RETURN and phase in ("idle", "celebrate"):
                    start_lift()

        if state == "menu":
            draw_menu(SCREEN)
        elif state == "setup":
            draw_setup(SCREEN)
        else:
            update_animation(now)
            value = float(weight_text) if weight_text else 60
            elapsed = (now - phase_started) / 1000
            draw_scene(SCREEN, elapsed, f"{value:g}")
        if now < message_until:
            w, h = SCREEN.get_size()
            rounded(SCREEN, pygame.Rect(w // 2 - 190, h - 122, 380, 42), (67, 38, 55), 12)
            text(SCREEN, message, SMALL, WHITE, (w // 2, h - 101))
        pygame.display.flip()
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
