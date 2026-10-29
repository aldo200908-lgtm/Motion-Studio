#!/usr/bin/env python3
"""Build a valid HyperFrames/GSAP composition from an owner-controlled render request.

HyperFrames is the real video engine (not an imitation); the HTML scenes are
authored by Motion Studio. No external user HTML/JS, tokens or API keys accepted.
"""
import argparse
import html
import json
import math
import os
import re
import shutil
import struct
import sys
import wave
from pathlib import Path
from literal_scenes import make_scenes, split_script, names_in, relation

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "hyperframes-project"
OUTPUT = ROOT / "output"
COLORS = re.compile(r"^#[0-9a-fA-F]{6}$")
FORMATS = {"vertical": (540, 960), "horizontal": (960, 540), "square": (720, 720)}
STYLES = {"high-energy", "engaging", "clean"}
MARKER = "<!-- MOTION_STUDIO_REQUEST_V2 -->"
OWNER = "aldo200908-lgtm"


def read_config():
    cfg = {
        "engine": os.getenv("ENGINE") or "hyperframes",
        "title": os.getenv("TITLE") or "Tu negocio merece una web",
        "subtitle": os.getenv("SUBTITLE") or "Diseño web, apps y sistemas",
        "script": os.getenv("SCRIPT") or "",
        "cta": os.getenv("CTA") or "Cotiza por WhatsApp",
        "style": os.getenv("STYLE") or "high-energy",
        "format": os.getenv("FORMAT") or "vertical",
        "accent": os.getenv("ACCENT") or "#FF7A00",
        "duration": os.getenv("DURATION") or "12",
        "sound": os.getenv("SOUND") if os.getenv("SOUND") is not None else "true",
    }
    event_name = os.getenv("GITHUB_EVENT_NAME", "")
    if event_name == "issues":
        payload = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text("utf-8"))
        issue = payload.get("issue") or {}
        author = (issue.get("user") or {}).get("login", "")
        if author.lower() != OWNER:
            raise ValueError("Only the repository owner may request a render")
        body = issue.get("body") or ""
        fence = chr(96) * 3
        if MARKER not in body or fence + "json" not in body:
            raise ValueError("Motion Studio issue missing a configuration block")
        raw = body.split(MARKER, 1)[1].split(fence + "json", 1)[1].split(fence, 1)[0]
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("The configuration must be a JSON object")
        for key in cfg:
            if key in data:
                cfg[key] = data[key]
        # Compatibility: issues from the older editor use the original renderer.
        if "engine" not in data:
            cfg["engine"] = "classic"
    if event_name == "push":
        cfg.update(engine="hyperframes", title="Claude vs ChatGPT",
                   subtitle="Comparación de herramientas de IA",
                   script="Claude es similar a ChatGPT. Codex ayuda a programar. GitHub Actions renderiza el video.",
                   cta="Crea videos con Motion Studio", style="high-energy", format="vertical",
                   accent="#FF7A00", duration=15, sound=True)
    for key in ("engine", "style", "format"):
        cfg[key] = str(cfg[key]).strip()
    if cfg["engine"] not in {"classic", "hyperframes"}:
        raise ValueError("Unknown rendering engine")
    if cfg["style"] not in STYLES or cfg["format"] not in FORMATS:
        raise ValueError("Unknown style or format")
    for key in ("title", "subtitle", "cta", "script"):
        cfg[key] = str(cfg[key]).strip()[:480 if key == "script" else 130]
    if not cfg["title"]:
        raise ValueError("Title must not be empty")
    cfg["accent"] = str(cfg["accent"]).upper()
    if not COLORS.fullmatch(cfg["accent"]):
        raise ValueError("Accent must be a hex RGB color")
    cfg["duration"] = max(6, min(20, int(float(cfg["duration"]))))
    cfg["sound"] = str(cfg["sound"]).lower() not in ("false", "0", "off", "no")
    return cfg


def synth_sound(duration, file):
    # Original four soft impacts / swishes, no copyrighted samples.
    rate = 22050
    cues = [duration * i / 4 for i in range(4)]
    with wave.open(str(file), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        frames = bytearray()
        for i in range(rate * duration):
            t = i / rate
            value = 0.0
            for cue in cues:
                x = t - cue
                if 0 <= x < 0.28:
                    value += .24 * math.sin(2 * math.pi * (210 - 80*x) * x) * math.exp(-18*x)
                    value += .07 * math.sin(2 * math.pi * 500*x) * math.exp(-30*x)
            frames.extend(struct.pack("<h", int(max(-1, min(1, value))*32767)))
        wav.writeframes(frames)


def composition(cfg):
    w, h = FORMATS[cfg["format"]]
    accent = cfg["accent"]
    duration = cfg["duration"]
    beat = duration / len(split_script(cfg))
    style = cfg["style"]
    esc = lambda text: html.escape(text, quote=True)
    def clip(index, tag, markup):
        start = round(index * beat, 4)
        end = round(beat, 4)
        return ('<section id="scene' + str(index) + '" class="clip scene s' + str(index) +
                '" data-start="' + str(start) + '" data-duration="' + str(end) +
                '" data-track-index="0"><div class="scene-content">' +
                '<div class="eyebrow">' + esc(tag) + '</div>' + markup +
                '</div></section>')
    scenes, visual_plan = make_scenes(cfg, clip, ROOT, PROJECT)
    text_size = 64 if cfg["format"] == "vertical" else (68 if cfg["format"] == "square" else 70)
    if len(cfg["title"]) > 45:
        text_size = int(text_size * .76)
    if len(cfg["title"]) > 85:
        text_size = int(text_size * .8)
    if style == "clean":
        bg, fg, muted, surface, border = "#f5f4f0", "#171f2d", "#5b6678", "#ffffff", "#d8dce2"
    elif style == "engaging":
        bg, fg, muted, surface, border = "#0f1427", "#ffffff", "#9eadd0", "#1d2744", "#364665"
    else:
        bg, fg, muted, surface, border = "#080e1c", "#fafbff", "#a1adc5", "#18243a", "#2c3a56"
    stylesheet = """
*{box-sizing:border-box} html,body{margin:0;overflow:hidden;width:100%;height:100%;background:VAR_BG;}
body{font-family:Arial,Helvetica,sans-serif}
#root{position:relative;isolation:isolate;width:VAR_Wpx;height:VAR_Hpx;overflow:hidden;background:VAR_BG;color:VAR_FG}
#root:before{position:absolute;inset:-30%;content:"";pointer-events:none;opacity:.45;
 background:radial-gradient(ellipse at 74% 25%,VAR_ACC22 0,transparent 47%),
 radial-gradient(ellipse at 22% 78%,VAR_ACC11 0,transparent 48%)}
.topline,.bottomline{position:absolute;z-index:20;left:6%;right:6%;display:flex;justify-content:space-between;
 align-items:center;font-weight:700;letter-spacing:3px;color:VAR_MUTED;font-size:12px}
.topline{top:5%}.bottomline{bottom:5%;letter-spacing:1.8px}
.progress{position:absolute;z-index:30;left:6%;right:6%;bottom:3%;height:5px;background:VAR_BORDER;border-radius:9px}
.progress span{display:block;background:VAR_ACC;height:100%;transform:scaleX(0);transform-origin:left center;border-radius:9px}
.scene{position:absolute;inset:0;display:flex;justify-content:center;align-items:center;overflow:hidden;
 padding:12% 7%;background:transparent}
.scene-content{width:100%;max-width:920px;position:relative;z-index:4;display:flex;flex-direction:column;
 align-items:center;text-align:center;justify-content:center;gap:25px}
.eyebrow{font-size:13px;font-weight:800;letter-spacing:3px;color:VAR_ACC;text-transform:uppercase}
.headline{color:VAR_FG;font-size:VAR_TEXTpx;font-weight:900;line-height:1.04;letter-spacing:-2.5px;margin:0;
 overflow-wrap:anywhere;max-width:100%}
.s2 .headline{font-size:VAR_TEXTpx}.highlight{color:VAR_ACC}
.micro,.mini-label{font-size:14px;letter-spacing:2px;color:VAR_MUTED;font-weight:700;margin:0}
.pill{display:inline-block;border:1px solid VAR_BORDER;background:VAR_SURFACE;border-radius:99px;
 padding:12px 24px;font-size:12px;font-weight:800;letter-spacing:2px;color:VAR_FG}
.hero-underline{height:9px;width:150px;border-radius:100px;background:VAR_ACC}
.device{margin-top:12px;width:min(90%,460px);height:255px;background:VAR_SURFACE;border:2px solid VAR_BORDER;
 border-radius:20px;padding:19px 24px;box-shadow:0 25px 70px #0002;text-align:left}
.device-top{display:flex;gap:7px;margin-bottom:30px}
.device-top span{width:10px;height:10px;border-radius:100px;background:VAR_ACC}
.device-top span:nth-child(2){opacity:.6}.device-top span:nth-child(3){opacity:.3}
.device-title{font-size:18px;font-weight:900;letter-spacing:1.5px;color:VAR_FG}
.device-bar{width:65%;height:10px;background:VAR_ACC;border-radius:6px;margin:20px 0}
.device-blocks{display:flex;gap:12px}.device-blocks i{height:54px;flex:1;background:VAR_BORDER;border-radius:8px}
.device-blocks i:nth-child(2){background:VAR_ACC;opacity:.55}
.stats{display:flex;gap:12px;width:min(95%,650px);justify-content:center;margin-top:22px}
.stat{display:flex;flex-direction:column;align-items:center;gap:14px;padding:24px 15px;
 border:1px solid VAR_BORDER;border-radius:18px;background:VAR_SURFACE;flex:1}
.stat strong{font-weight:900;color:VAR_ACC;font-size:38px}.stat span{font-size:12px;letter-spacing:1px;color:VAR_MUTED}
.last-symbol{font-size:75px;color:VAR_ACC}
.cta{margin-top:10px;background:VAR_ACC;color:#111;padding:22px 34px;border-radius:100px;
 max-width:100%;overflow-wrap:anywhere;font-size:24px;font-weight:800;display:flex;gap:22px;align-items:center}
.cta span{font-size:29px}
.shape{position:absolute;border:2px solid VAR_ACC;border-radius:50%;opacity:.22;pointer-events:none}
.shape.a{width:420px;height:420px;left:-150px;top:12%}.shape.b{width:350px;height:350px;right:-155px;bottom:10%}
#root.clean .shape{border-radius:15px;opacity:.08}
#root.engaging .shape{border-radius:30%;transform:rotate(35deg)}

/* Literal foreground for each narrated clause: logo, comparison, or semantic illustration. */
.spoken-title{max-width:96%;font-size:VAR_TITLEpx;font-weight:900;line-height:1.11;letter-spacing:-1.5px;overflow-wrap:anywhere}
.literal-visual{width:94%;min-height:185px;display:flex;align-items:center;justify-content:center;gap:14px}
.brand-card{flex:1;min-width:0;max-width:245px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:13px;border-radius:22px;padding:22px 14px;min-height:172px;background:VAR_SURFACE;border:2px solid VAR_BORDER;box-shadow:0 14px 35px #0002}
.brand-card strong{font-size:23px;color:VAR_FG;overflow-wrap:anywhere}
.logo-box{width:85px;height:85px;border-radius:20px;background:#fff;display:grid;place-items:center;padding:17px}
.logo-box img{width:100%;height:100%;object-fit:contain}
.fallback-logo{color:#181818;font-size:24px;font-weight:900}
.relation{flex-shrink:0;font-size:22px;font-weight:900;color:VAR_ACC;padding:12px;border-radius:100px;background:VAR_SURFACE;border:1px solid VAR_BORDER}
.concept{width:min(90%,430px);background:VAR_SURFACE;border:2px solid VAR_BORDER;border-radius:24px;padding:25px;display:flex;align-items:center;justify-content:center;gap:18px}
.concept-symbol{width:110px;height:110px;border-radius:18px;background:VAR_ACC;color:#111;font-size:64px;display:grid;place-items:center}
.concept strong{font-size:21px;color:VAR_FG}
.scene-counter{font-size:13px;font-weight:700;letter-spacing:2px;color:VAR_MUTED}
#root[data-format="vertical"] .literal-visual.pair{flex-direction:column;gap:9px}
#root[data-format="vertical"] .brand-card{min-height:130px;width:min(86%,350px);flex:none}
#root[data-format="vertical"] .logo-box{width:65px;height:65px;padding:13px}
#root[data-format="vertical"] .spoken-title{font-size:34px}
#root[data-format="vertical"] .concept-symbol{width:82px;height:82px;font-size:46px}
""".replace("VAR_W", str(w)).replace("VAR_H", str(h)).replace("VAR_TEXT", str(text_size)).replace("VAR_TITLE", str(round(text_size*.7)))
    for key, value in (("VAR_BG", bg), ("VAR_FG", fg), ("VAR_MUTED", muted),
                       ("VAR_SURFACE", surface), ("VAR_BORDER", border),
                       ("VAR_ACC22", accent + "22"), ("VAR_ACC11", accent + "11"),
                       ("VAR_ACC", accent)):
        stylesheet = stylesheet.replace(key, value)
    # The GSAP timeline is registered by composition id, paused for frame seeking.
    animations = []
    for idx in range(len(scenes)):
        begin = round(idx * beat, 4)
        slide = ".scene.s" + str(idx)
        animations.extend([
            "tl.fromTo(" + json.dumps(slide + " .eyebrow") +
            ',{autoAlpha:0,y:25},{autoAlpha:1,y:0,duration:.40,ease:"power3.out"},' + str(begin + .08) + ");",
            "tl.fromTo(" + json.dumps(slide + " .spoken-title") +
            ',{autoAlpha:0,y:100,scale:.88},{autoAlpha:1,y:0,scale:1,duration:.72,ease:"back.out(1.35)"},' +
            str(begin + .16) + ");",
            "tl.fromTo(" + json.dumps(slide + " .scene-content") +
            ',{autoAlpha:0},{autoAlpha:1,duration:.2},' + str(begin) + ");",
            "tl.to(" + json.dumps(slide + " .scene-content") +
            ',{autoAlpha:0,y:-38,duration:.3,ease:"power2.in"},' + str(begin + beat - .34) + ");",
        ])
        decorative = [".literal-visual", ".scene-counter"]
        for key in decorative:
            animations.append(
                "tl.fromTo(" + json.dumps(slide + " " + key) +
                ',{autoAlpha:0,y:35,scale:.92},{autoAlpha:1,y:0,scale:1,duration:.55,ease:"power2.out"},' +
                str(begin + .36) + ");")
    timeline = "\n".join(animations)
    # Use local, bundled GSAP file; avoids network requests during browser capture.
    return ('''<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Motion Studio · HyperFrames</title>
<style>''' + stylesheet + '''</style>
</head><body><div id="root" class="''' + esc(style.replace("high-energy", "energy")) +
            '''" data-composition-id="motion-studio" data-start="0" data-duration="''' + str(duration) +
            '''" data-format="''' + cfg["format"] + '''" data-width="''' + str(w) + '''" data-height="''' + str(h) + '''">
<div class="shape a"></div><div class="shape b"></div>
<div class="topline"><span>MOTION STUDIO</span><span>HYPERFRAMES / 03</span></div>
''' + "\n".join(scenes) + '''
<div class="bottomline"><span>CREADO CON HTML + GSAP</span><span>24 FPS</span></div>
<div class="progress"><span id="fill"></span></div>
</div><script src="./assets/gsap.min.js"></script>
<script>
window.__timelines=window.__timelines||{};
const tl=gsap.timeline({paused:true});
tl.to("#fill",{scaleX:1,duration:''' + str(duration) + ''',ease:"none"},0);
''' + timeline + '''
window.__timelines["motion-studio"]=tl;
</script></body></html>
''')


def build():
    cfg = read_config()
    if cfg["engine"] != "hyperframes":
        raise ValueError("This builder only accepts the HyperFrames engine")
    (PROJECT / "assets").mkdir(parents=True, exist_ok=True)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    gsap = ROOT / "node_modules" / "gsap" / "dist" / "gsap.min.js"
    if not gsap.exists():
        raise FileNotFoundError("GSAP is not installed: run npm install first")
    shutil.copyfile(gsap, PROJECT / "assets" / "gsap.min.js")
    (PROJECT / "index.html").write_text(composition(cfg), "utf-8")
    metadata = dict(cfg)
    metadata["scene_plan"] = [{"text": phrase,
                               "brands": [name for name, _ in names_in(phrase)],
                               "relation": relation(phrase, names_in(phrase))}
                              for phrase in split_script(cfg)]
    (OUTPUT / "metadata.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False), "utf-8")
    (OUTPUT / "CREDITS.txt").write_text(
        "Motor de video: HyperFrames (Apache-2.0, heygen-com/hyperframes)\n"
        "Animaciones: GSAP (licencia estándar GSAP), escenas originales Motion Studio.\n"
        "El renderizado de este proyecto no utiliza modelos de IA.\n"
        "Efectos de sonido: sintetizados por Motion Studio, sin muestras de terceros.\n", "utf-8")
    if cfg["sound"]:
        synth_sound(cfg["duration"], OUTPUT / "sfx.wav")
    print("Generated HyperFrames composition", PROJECT / "index.html",
          "format", cfg["format"], "duration", cfg["duration"])


def select():
    cfg = read_config()
    path = os.getenv("GITHUB_OUTPUT")
    if path:
        with open(path, "a", encoding="utf-8") as out:
            out.write("engine=" + cfg["engine"] + "\n")
            out.write("sound=" + ("true" if cfg["sound"] else "false") + "\n")
    print("Selected renderer:", cfg["engine"])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", required=True, choices=["select", "compose"])
    args = parser.parse_args()
    if args.mode == "select":
        select()
    else:
        build()


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print("Motion Studio builder error:", exc, file=sys.stderr)
        sys.exit(1)
