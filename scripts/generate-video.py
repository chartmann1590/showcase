#!/usr/bin/env python3
"""
Generate a promotional video for the portfolio showcase.
  - Pillow  : slide image generation
  - edge-tts: neural TTS voiceover (Microsoft, free)
  - ffmpeg  : assemble slides + audio into MP4

Output: assets/video/promo.mp4  +  assets/video/poster.png
"""

import asyncio
import json
import os
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
    import edge_tts
except ImportError:
    print("Missing deps. Run: pip install Pillow edge-tts")
    sys.exit(1)

# ── Layout ─────────────────────────────────────────────────────────────────
W, H = 1280, 720
FPS  = 30

SHOWCASE_URL  = "https://chartmann1590.github.io/showcase"
BMC_URL       = "https://buymeacoffee.com/charleshartmann"
GITHUB_URL    = "https://github.com/chartmann1590"
VOICE         = "en-US-AriaNeural"  # Microsoft Neural — natural female

# ── Palette ────────────────────────────────────────────────────────────────
BG      = (6,   6,  14)
CARD    = (17,  17, 34)
BORDER  = (40,  40, 70)
BLUE    = (79,  111, 255)
PURPLE  = (168, 85,  247)
CYAN    = (34,  211, 238)
GREEN   = (52,  211, 153)
YELLOW  = (251, 191, 36)
RED     = (248, 113, 113)
WHITE   = (240, 240, 255)
DIM     = (140, 140, 195)
MUTED   = (70,  70,  110)
COFFEE  = (255, 221, 0)

CAT_COLORS = {
    "android": GREEN,
    "web":     CYAN,
    "ai":      PURPLE,
    "python":  YELLOW,
    "game":    RED,
    "iot":     (100, 116, 139),
    "other":   (100, 100, 140),
}

ICON_COLORS = [
    BLUE, PURPLE, CYAN, GREEN, (244, 114, 182), (251, 146, 60),
    (167, 139, 250), (52, 211, 153), (34, 211, 238), (248, 113, 113),
]

def icon_color(name):
    h = 0
    for c in name: h = (h * 31 + ord(c)) & 0xFFFFFFFF
    return ICON_COLORS[h % len(ICON_COLORS)]

# ── Fonts ──────────────────────────────────────────────────────────────────
BOLD_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]
REG_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
    "C:/Windows/Fonts/arial.ttf",
]

def _first(paths):
    return next((p for p in paths if Path(p).exists()), None)

def load_fonts():
    b = _first(BOLD_PATHS)
    r = _first(REG_PATHS) or b
    def f(path, size):
        try:
            return ImageFont.truetype(path, size) if path else ImageFont.load_default()
        except Exception:
            return ImageFont.load_default()
    return {
        "b72": f(b, 72), "b56": f(b, 56), "b42": f(b, 42),
        "b30": f(b, 30), "b22": f(b, 22),
        "r36": f(r, 36), "r26": f(r, 26), "r20": f(r, 20), "r16": f(r, 16),
    }

# ── Drawing helpers ─────────────────────────────────────────────────────────
def center_x(draw, text, font, y, color):
    bb = font.getbbox(text)
    x = (W - (bb[2] - bb[0])) // 2
    draw.text((x, y), text, font=font, fill=color)
    return bb[2] - bb[0]

def pill(draw, x, y, label, color, font, pad_x=14, pad_y=7):
    bb = font.getbbox(label)
    tw, th = bb[2]-bb[0], bb[3]-bb[1]
    x2, y2 = x + tw + pad_x*2, y + th + pad_y*2
    r = (y2-y)//2
    draw.rounded_rectangle([x, y, x2, y2], radius=r, fill=(*color, 35))
    draw.rounded_rectangle([x, y, x2, y2], radius=r, outline=(*color, 120), width=1)
    draw.text((x+pad_x, y+pad_y), label, font=font, fill=color)
    return x2

def icon_box(draw, x, y, size, letter, color, font):
    r = size // 4
    draw.rounded_rectangle([x, y, x+size, y+size], radius=r, fill=color)
    shade = tuple(min(255, int(c*1.6)) for c in color)
    bb = font.getbbox(letter)
    lx = x + (size - (bb[2]-bb[0])) // 2
    ly = y + (size - (bb[3]-bb[1])) // 2 - 2
    draw.text((lx, ly), letter, font=font, fill=shade)

def bg_base(draw):
    """Draw ambient gradient orbs onto a transparent RGBA overlay."""
    for r in range(480, 0, -12):
        a = int(22 * r/480)
        draw.ellipse([-200, -180, r*2-200, r*2-180], fill=(*BLUE, a))
    for r in range(380, 0, -12):
        a = int(18 * r/380)
        cx, cy = W-80, H//2
        draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=(*PURPLE, a))
    for r in range(280, 0, -12):
        a = int(14 * r/280)
        bx = W//2
        draw.ellipse([bx-r, H-60, bx+r, H-60+r*2], fill=(*CYAN, a))

def make_bg():
    base = Image.new("RGB", (W, H), BG)
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bg_base(ImageDraw.Draw(overlay))
    return Image.alpha_composite(base.convert("RGBA"), overlay).convert("RGB")

def code_lines(draw, x, y, w=260, n=7):
    """Decorative abstract code stripe pattern."""
    widths = [220, 170, 240, 130, 200, 160, 210]
    for i in range(n):
        a = 25 + i * 5
        draw.rectangle([x, y + i*20, x+widths[i%len(widths)]*w//240, y+i*20+3], fill=(*BLUE, a))
        if i % 3 == 1:
            draw.rectangle([x, y+i*20+8, x+widths[(i+2)%len(widths)]*w//300, y+i*20+11], fill=(*PURPLE, a-10))

def sep(draw, margin=80):
    y = H - 100
    draw.rectangle([margin, y, W-margin, y+1], fill=(*BORDER, 200))

# ── Slides ──────────────────────────────────────────────────────────────────
def slide_title(F):
    img = make_bg()
    d = ImageDraw.Draw(img)

    # Decorative lines left
    for i, (length, col) in enumerate([(200, BLUE), (120, PURPLE), (160, CYAN)]):
        d.rectangle([60, 200+i*18, 60+length, 202+i*18], fill=(*col, 80+i*20))

    # Big initial
    d.text((60, 80), "CH", font=F["b72"], fill=(*BLUE, 200))

    # Name
    d.text((60, 200), "Charles Hartmann", font=F["b56"], fill=WHITE)
    # Subtitle
    d.text((63, 270), "Open Source Developer", font=F["r36"], fill=DIM)

    # Accent line
    d.rectangle([60, 318, 340, 321], fill=BLUE)

    # Tagline chips
    chips = [("Android", GREEN), ("AI Tools", PURPLE), ("Web", CYAN), ("Python", YELLOW)]
    cx = 60
    for label, col in chips:
        cx = pill(d, cx, 340, label, col, F["b22"], pad_x=12, pad_y=6) + 10

    # URL
    d.text((60, 410), SHOWCASE_URL, font=F["r20"], fill=(*BLUE, 160))

    # Right side - decorative
    code_lines(d, W-300, 150, w=260)
    d.rounded_rectangle([W-310, 140, W-40, H-80], radius=16,
                        fill=(*CARD, 160), outline=(*BORDER, 100))
    icon_box(d, W-200, H//2-50, 100, "C", BLUE, F["b56"])

    sep(d)
    d.text((60, H-75), "Browse 61+ open source apps at " + SHOWCASE_URL, font=F["r16"], fill=(*MUTED, 200))
    return img

def slide_stats(catalog, F):
    stats = catalog["stats"]
    total = stats["total"]
    stars = stats.get("total_stars", 0)
    by_cat = stats.get("by_category", {})

    img = make_bg()
    d = ImageDraw.Draw(img)

    center_x(d, "Open Source Portfolio", F["b42"], 55, WHITE)
    # Underline
    bb = F["b42"].getbbox("Open Source Portfolio")
    uw = bb[2]-bb[0]
    d.rectangle([(W-uw)//2, 110, (W+uw)//2, 113], fill=BLUE)

    # Big number
    center_x(d, str(total), F["b72"], 130, BLUE)
    center_x(d, "Apps & Tools", F["r26"], 215, DIM)

    # Stars
    center_x(d, f"* {stars} GitHub Stars  |  {GITHUB_URL}", F["b22"], 265, YELLOW)

    # Category pills in 2 rows
    rows = [
        [("android", "Android"), ("web", "Web"), ("python", "Python")],
        [("ai", "AI Tools"), ("game", "Games"), ("iot", "IoT & Hardware")],
    ]
    for ri, row in enumerate(rows):
        labels = [f"{by_cat.get(cat,0)} {lbl}" for cat, lbl in row]
        cols   = [CAT_COLORS.get(cat, DIM) for cat, _ in row]
        total_w = sum(F["b22"].getbbox(lbl)[2]-F["b22"].getbbox(lbl)[0]+32 for lbl in labels) + 20*2
        px = (W-total_w)//2
        py = 320 + ri * 60
        for lbl, col in zip(labels, cols):
            px = pill(d, px, py, lbl, col, F["b22"], pad_x=16, pad_y=8) + 14

    sep(d)
    d.text((W//2-180, H-75), "Daily auto-updated  |  " + SHOWCASE_URL, font=F["r16"], fill=(*MUTED, 200))
    return img

def slide_repo(repo, F):
    name  = repo["name"]
    desc  = repo.get("description") or "No description."
    lang  = repo.get("language") or ""
    stars = repo.get("stars") or 0
    cat   = repo.get("category", "other")
    url   = repo["url"]

    img = make_bg()
    d = ImageDraw.Draw(img)

    # Icon
    icon_box(d, 60, 55, 80, name[0].upper(), icon_color(name), F["b42"])

    # Badges
    bx = 160
    if lang:
        bx = pill(d, bx, 68, lang, DIM, F["b22"]) + 10
    cat_col = CAT_COLORS.get(cat, DIM)
    pill(d, bx, 68, cat.upper(), cat_col, F["b22"])

    # Stars
    if stars:
        d.text((160, 110), f"* {stars} stars", font=F["b22"], fill=YELLOW)

    # Name
    d.text((60, 155), name, font=F["b56"], fill=WHITE)

    # Description wrapped
    wrapped = textwrap.fill(desc, width=58)
    ty = 230
    for line in wrapped.split("\n")[:3]:
        d.text((60, ty), line, font=F["r26"], fill=DIM)
        ty += 42

    # Separator
    sy = ty + 20
    d.rectangle([60, sy, W-60, sy+1], fill=(*BORDER, 200))

    # URL
    d.text((60, sy+12), url, font=F["r20"], fill=(*BLUE, 180))

    # Right decorative panel
    code_lines(d, W-300, 140)
    return img

def slide_cta(F):
    img = make_bg()
    d = ImageDraw.Draw(img)

    center_x(d, "Explore the Full Catalog", F["b56"], 70, WHITE)
    bb = F["b56"].getbbox("Explore the Full Catalog")
    uw = bb[2]-bb[0]
    d.rectangle([(W-uw)//2, 138, (W+uw)//2, 141], fill=BLUE)

    # URL box
    bb2 = F["b30"].getbbox(SHOWCASE_URL)
    uw2 = bb2[2]-bb2[0]
    mx = (W-uw2)//2 - 22
    d.rounded_rectangle([mx, 158, mx+uw2+44, 206], radius=14,
                        fill=(*BLUE, 28), outline=(*BLUE, 110))
    d.text((mx+22, 168), SHOWCASE_URL, font=F["b30"], fill=BLUE)

    # Feature pills
    feats = ["Full-text search", "7 categories", "Auto-updated daily"]
    feat_cols = [CYAN, PURPLE, GREEN]
    total_w = sum(F["r20"].getbbox(f)[2]-F["r20"].getbbox(f)[0]+32 for f in feats) + 20*2
    fx = (W-total_w)//2
    for feat, col in zip(feats, feat_cols):
        fx = pill(d, fx, 228, feat, col, F["r20"], pad_x=16, pad_y=8) + 14

    # Divider
    d.rectangle([W//2-150, 295, W//2+150, 296], fill=(*BORDER, 180))

    # Buy Me a Coffee
    center_x(d, "Support this work:", F["r26"], 316, DIM)
    bb3 = F["b30"].getbbox(BMC_URL)
    uw3 = bb3[2]-bb3[0]
    mx2 = (W-uw3)//2-22
    d.rounded_rectangle([mx2, 354, mx2+uw3+44, 402], radius=14,
                        fill=(*COFFEE, 22), outline=(*COFFEE, 110))
    d.text((mx2+22, 364), BMC_URL, font=F["b30"], fill=COFFEE)

    # Icon accents
    for i, col in enumerate([BLUE, PURPLE, CYAN, GREEN, YELLOW]):
        icon_box(d, 60+i*55, H-200, 42, ["A","I","W","P","G"][i], col, F["b22"])

    sep(d)
    footer = f"github.com/chartmann1590  |  61+ open source projects  |  Free on GitHub"
    center_x(d, footer, F["r16"], H-70, (*MUTED, 200))
    return img

# ── Voiceover ───────────────────────────────────────────────────────────────
SCRIPT = (
    "Welcome to Charles Hartmann's open source portfolio. "
    "Over sixty apps and tools — built with passion and shared completely for free. "

    "VowVault is a beautiful wedding photo gallery and guestbook with twenty-nine GitHub stars. "
    "Rokid Maps is a standalone navigation app for Rokid augmented reality glasses, with twenty-three stars. "
    "Bee A I Web provides a sleek interface for the Bee A I wearable device. "
    "AirGF is an on-device A I companion powered by Gemma four, complete with three D avatars. "
    "TrailSage A I is an offline G P S audio tour guide that runs entirely on your Android phone. "
    "Pixel Fish Tank is a cozy virtual pet game with charming pixel-art fish. "

    "Charles builds across every platform — Android, web, Python, A I tools, games, and hardware. "
    "The entire catalog is searchable and filtered by category. "
    "And it updates itself automatically every single day. "

    "Browse everything at chartmann1590 dot github dot io slash showcase. "
    "If any of these projects helped you, support Charles at buy me a coffee dot com slash charleshartmann."
)

async def gen_voice(out_path):
    print(f"  Generating voiceover with {VOICE} ...")
    comm = edge_tts.Communicate(SCRIPT, VOICE, rate="-8%", pitch="+0Hz")
    await comm.save(str(out_path))

def audio_duration(path):
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True,
    )
    try:
        return float(r.stdout.strip())
    except Exception:
        return 42.0

# ── Featured repos ──────────────────────────────────────────────────────────
PRIORITY = ["VowVault", "Rokid-Maps", "bee-ai-web", "airgf",
            "trailsage-ai-android", "Pixel-Fish-Tank"]

def pick_repos(catalog, n=6):
    by_name = {r["name"]: r for r in catalog["repos"]}
    featured, seen = [], set()
    for name in PRIORITY:
        if name in by_name and name not in seen:
            featured.append(by_name[name]); seen.add(name)
        if len(featured) >= n: break
    for r in catalog["repos"]:
        if r["name"] not in seen and len(featured) < n:
            featured.append(r); seen.add(r["name"])
    return featured[:n]

# ── FFmpeg assembly ─────────────────────────────────────────────────────────
def assemble(slide_paths, durations, audio_path, output_path):
    tmp = Path("_tmp_video")
    tmp.mkdir(exist_ok=True)
    concat = tmp / "list.txt"
    with open(concat, "w") as fh:
        for sp, dur in zip(slide_paths, durations):
            fh.write(f"file '{Path(sp).resolve()}'\nduration {dur:.2f}\n")
        fh.write(f"file '{Path(slide_paths[-1]).resolve()}'\n")

    silent = tmp / "silent.mp4"
    print("  Encoding slideshow ...")
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat),
        "-vf", f"fps={FPS},scale={W}:{H}:force_original_aspect_ratio=decrease,"
               f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:{BG[0]:02x}{BG[1]:02x}{BG[2]:02x}",
        "-c:v", "libx264", "-preset", "medium", "-crf", "22", "-pix_fmt", "yuv420p",
        str(silent),
    ], check=True, capture_output=True)

    print("  Mixing audio ...")
    subprocess.run([
        "ffmpeg", "-y", "-i", str(silent), "-i", str(audio_path),
        "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", "-shortest",
        str(output_path),
    ], check=True, capture_output=True)

    shutil.rmtree(tmp, ignore_errors=True)

# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    out_dir = Path("assets/video")
    out_dir.mkdir(parents=True, exist_ok=True)
    tmp_slides = Path("_tmp_slides")
    tmp_slides.mkdir(exist_ok=True)

    with open("catalog.json", encoding="utf-8") as fh:
        catalog = json.load(fh)

    print("Loading fonts ...")
    F = load_fonts()

    audio_path = tmp_slides / "voice.mp3"
    asyncio.run(gen_voice(audio_path))
    dur = audio_duration(audio_path)
    print(f"  Audio duration: {dur:.1f}s")

    repos = pick_repos(catalog)
    print(f"  Featured: {[r['name'] for r in repos]}")

    # Base durations
    d_title = 4.0
    d_stats = 3.5
    d_repo  = [4.0] * len(repos)
    d_cta   = 5.5
    fixed   = d_title + d_stats + sum(d_repo) + d_cta

    # Stretch repo slides to fill audio
    if dur > fixed:
        extra = (dur - fixed) / len(repos)
        d_repo = [x + extra for x in d_repo]

    print("Generating slides ...")
    paths, durs = [], []

    def add(img, d, name):
        p = tmp_slides / name
        img.save(p)
        paths.append(p); durs.append(d)

    add(slide_title(F),        d_title, "s000_title.png")
    add(slide_stats(catalog, F), d_stats, "s001_stats.png")
    for i, repo in enumerate(repos):
        add(slide_repo(repo, F), d_repo[i], f"s{i+2:03d}_{repo['name']}.png")
    add(slide_cta(F), d_cta, f"s{len(repos)+2:03d}_cta.png")

    # Save poster (title frame)
    shutil.copy(paths[0], out_dir / "poster.png")

    print(f"Assembling {len(paths)} slides ({sum(durs):.1f}s) ...")
    output = out_dir / "promo.mp4"
    assemble(paths, durs, audio_path, output)

    shutil.rmtree(tmp_slides, ignore_errors=True)

    size_mb = output.stat().st_size / 1024 / 1024
    print(f"\nDone: {output}  ({size_mb:.1f} MB)")

if __name__ == "__main__":
    main()
