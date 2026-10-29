#!/usr/bin/env python3
"""Motion Studio 4: kinetic typography, transitions, motion, sound, storyboard."""
import html
import json
import math
import random
import shutil
import struct
import wave
from pathlib import Path

from hyperframes_build import ROOT, PROJECT, OUTPUT, read_config
from literal_scenes import names_in, bundle_icons, card

FPS = 24
W, H = 540, 960
random.seed(17)

def synth_music(path, seconds, beats):
    rate = 22050
    count = seconds * rate
    samples = [0.0] * count
    # Original synthesized ambient harmony + kick/snare/hi-hat and cue sweeps.
    notes = [110.0, 130.81, 164.81, 196.0]
    for i in range(count):
        t = i / rate
        chord = notes[int(t // 4) % 4]
        ambient = (.038*math.sin(2*math.pi*chord*t)
                   + .026*math.sin(2*math.pi*chord*1.5*t)
                   + .018*math.sin(2*math.pi*chord*2*t))
        samples[i] = ambient * min(1, t*3) * min(1, (seconds-t)*2)
    for beat in range(0, seconds*2):
        start = int(beat*.5*rate)
        for j in range(min(int(.22*rate), count-start)):
            x = j/rate
            kick = .22*math.sin(2*math.pi*(105-180*x)*x)*math.exp(-22*x)
            hat = .042*(random.random()*2-1)*math.exp(-90*x)
            samples[start+j] += kick+hat
    for time in beats:
        start = int(time*rate)
        for j in range(min(int(.32*rate), count-start)):
            x = j/rate
            sweep = .17*math.sin(2*math.pi*(320+500*x)*x)*math.exp(-11*x)
            samples[start+j] += sweep
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path),"wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        frames=bytearray()
        for sample in samples:
            v=max(-.94,min(.94,math.tanh(sample*1.5)))
            frames.extend(struct.pack("<h",int(v*32767)))
        wav.writeframes(frames)

def phrase_html(text, key):
    words = text.split()
    return '<div class="kinetic">' + ''.join(
        '<span class="word '+('key' if i==key else '')+'"><span>'+html.escape(w)+'</span></span>'
        for i,w in enumerate(words)) + '</div>'

def select_key(text):
    words=text.split()
    for i,w in enumerate(words):
        if any(k in w.lower() for k in ("claude","chatgpt","codex","github","viral","gratis","motion","video")):
            return i
    return min(len(words)-1,max(0,len(words)//2))

def scene_visual(text, icons):
    brands=names_in(text)
    if len(brands)>1:
        return '<div class="logo-strip">'+card(brands[0],icons)+'<div class="vs">VS</div>'+card(brands[1],icons)+'</div>',[b[0] for b in brands[:2]]
    if brands:
        return '<div class="logo-strip">'+card(brands[0],icons)+'</div>',[brands[0][0]]
    if any(k in text.lower() for k in ("resultado","crece","venta","cliente","impacto")):
        return '<div class="metrics"><div class="metric-title">IMPACTO VISUAL</div><div class="bar-track"><div class="bar-fill"></div></div><div class="counter">0%</div></div>',[]
    return '<div class="flow-graphic"><div class="node">IDEA</div><svg viewBox="0 0 180 90"><path class="draw" d="M4 45 H170 M146 22 L170 45 L146 68"/></svg><div class="node accent">ACCIÓN</div></div>',[]

def build():
    cfg=read_config()
    duration=15  # reliable HyperFrames render window; 15 seconds meets requested 15–20s
    cfg.update(engine="hyperframes",format="vertical",duration=duration)
    PROJECT.mkdir(parents=True,exist_ok=True)
    (PROJECT/"assets").mkdir(exist_ok=True)
    OUTPUT.mkdir(parents=True,exist_ok=True)
    gsap=ROOT/"node_modules"/"gsap"/"dist"/"gsap.min.js"
    if not gsap.is_file():
        raise RuntimeError("Install GSAP before building")
    shutil.copyfile(gsap,PROJECT/"assets"/"gsap.min.js")
    icons=bundle_icons(ROOT,PROJECT)
    phrases=[
        cfg["title"] or "Motion Studio",
        "Claude y ChatGPT explicados con gráficos que se mueven",
        "Codex crea. GitHub Actions renderiza el video",
        cfg["cta"] or "Crea tu próximo video",
    ]
    if cfg.get("script"):
        parts=[p.strip() for p in __import__("re").split(r"[.!?;]\s+|\n+",cfg["script"]) if p.strip()]
        if parts:
            phrases=[cfg["title"]]+parts[:2]+[cfg["cta"]]
    scenes=[]
    plan=[]
    beat=duration/len(phrases)
    for i,text in enumerate(phrases):
        graphic,brands=scene_visual(text,icons)
        key=select_key(text)
        plan.append({"text":text,"brands":brands,"start":round(i*beat,3),"duration":round(beat,3)})
        scenes.append(f'<section id="scene-{i}" class="clip scene scene-{i}" data-start="{i*beat:.3f}" data-duration="{beat:.3f}" data-track-index="0"><div class="scene-inner"><div class="scene-kicker">MOTION STUDIO / {i+1:02d}</div>{phrase_html(text,key)}{graphic}<div class="scene-bottom">EXPLICA · ANIMA · IMPACTA</div></div></section>')
    css=r"""
*{box-sizing:border-box}html,body{margin:0;width:540px;height:960px;overflow:hidden;background:#070b15}
body{font-family:Arial,Helvetica,sans-serif;color:#f9fbff}
#root{position:relative;width:540px;height:960px;overflow:hidden;isolation:isolate;background:#070b15}
.ambient{position:absolute;inset:-30%;background:radial-gradient(ellipse at 30% 20%,#263957 0,transparent 42%),radial-gradient(ellipse at 80% 75%,#21314a 0,transparent 43%);opacity:.6}
.grid-bg{position:absolute;inset:-15%;background-image:linear-gradient(#ffffff0b 1px,transparent 1px),linear-gradient(90deg,#ffffff0b 1px,transparent 1px);background-size:64px 64px;transform:perspective(700px) rotateX(16deg)}
.orb{position:absolute;width:330px;height:330px;border-radius:50%;filter:blur(30px);opacity:.18;background:ACCENT;left:-130px;top:130px}
.orb.two{width:270px;height:270px;left:380px;top:650px;background:#45baff}
.brand-top{position:absolute;top:48px;left:35px;right:35px;z-index:50;display:flex;justify-content:space-between;letter-spacing:3px;font-weight:900;font-size:15px}
.brand-top span{color:ACCENT}
.progress{position:absolute;bottom:48px;left:35px;right:35px;height:5px;background:#ffffff22;z-index:60;border-radius:8px}
.progress-fill{height:100%;width:100%;background:ACCENT;transform-origin:left;border-radius:8px}
.scene{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;padding:100px 34px 105px;overflow:hidden}
.scene-inner{width:100%;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:34px;text-align:center}
.scene-kicker{font-weight:900;color:ACCENT;font-size:16px;letter-spacing:3px}
.kinetic{display:flex;flex-wrap:wrap;justify-content:center;gap:9px 12px;max-width:100%;font-size:56px;line-height:1.02;font-weight:900;letter-spacing:-2px;text-transform:uppercase}
.word{display:inline-block;overflow:hidden;padding-bottom:7px}.word>span{display:block;transform-origin:bottom center}
.word.key{color:ACCENT;font-size:1.08em;text-shadow:0 0 30px #ff7a0040}
.logo-strip{display:flex;align-items:center;justify-content:center;gap:14px;width:100%;min-height:205px}
.brand-card{display:flex;align-items:center;flex-direction:column;justify-content:center;gap:14px;min-width:0;flex:1;max-width:190px;min-height:205px;background:#151d30;border:2px solid #34415c;border-radius:26px;padding:16px}
.logo-box{background:#fff;border-radius:20px;padding:17px;width:100px;height:100px;display:grid;place-items:center}
.logo-box img{width:100%;height:100%;object-fit:contain}
.fallback-logo{font-size:28px;font-weight:900;color:#111}
.brand-card strong{font-size:23px;letter-spacing:-1px;overflow-wrap:anywhere}
.vs{background:ACCENT;color:#090b12;font-weight:900;padding:10px 12px;border-radius:100px;font-size:23px}
.flow-graphic{display:flex;align-items:center;justify-content:center;width:100%;gap:8px}
.node{padding:18px 14px;border:2px solid #5b7194;border-radius:20px;font-size:22px;font-weight:900;background:#151d30}
.node.accent{background:ACCENT;color:#10151f;border-color:ACCENT}
.flow-graphic svg{width:130px;overflow:visible}
.draw{fill:none;stroke:ACCENT;stroke-width:7;stroke-linecap:round;stroke-linejoin:round;stroke-dasharray:270;stroke-dashoffset:270}
.metrics{width:92%;border:2px solid #394a65;border-radius:24px;background:#141d30;padding:30px 22px}
.metric-title{letter-spacing:3px;font-size:17px;font-weight:900}
.bar-track{margin-top:25px;height:18px;border-radius:20px;background:#34415c;overflow:hidden}
.bar-fill{height:100%;width:100%;background:ACCENT;transform:scaleX(0);transform-origin:left}
.counter{font-size:65px;color:ACCENT;font-weight:900;margin-top:16px}
.scene-bottom{font-size:14px;letter-spacing:3px;color:#c5cee0;font-weight:800}
.wipe{position:absolute;z-index:45;inset:-10%;background:ACCENT;pointer-events:none}
.wipe.alt{background:#fff;z-index:44}
.transition-circle{position:absolute;z-index:46;left:50%;top:50%;width:1200px;height:1200px;margin-left:-600px;margin-top:-600px;background:#0d1526;border-radius:50%;pointer-events:none}
"""
    css=css.replace("ACCENT",cfg["accent"])
    js=[
        'window.__timelines=window.__timelines||{};',
        'const tl=gsap.timeline({paused:true});',
        f'tl.fromTo(".progress-fill",{{scaleX:0}},{{scaleX:1,duration:{duration},ease:"none"}},0);',
        f'tl.to(".grid-bg",{{x:-90,y:75,rotation:4,duration:{duration},ease:"none"}},0);',
        f'tl.to(".ambient",{{scale:1.25,x:60,y:-35,duration:{duration},ease:"sine.inOut"}},0);',
        f'tl.to(".orb",{{x:180,y:-110,scale:1.25,duration:{duration},ease:"sine.inOut"}},0);',
        f'tl.to(".orb.two",{{x:-150,y:90,duration:{duration},ease:"sine.inOut"}},0);',
    ]
    for i,text in enumerate(phrases):
        start=i*beat
        selector=f".scene-{i}"
        js += [
            f'tl.fromTo("{selector} .scene-inner",{{scale:1.16,y:35}},{{scale:1,y:0,duration:{beat:.3f},ease:"sine.out"}},{start:.3f});',
            f'tl.fromTo("{selector} .scene-kicker",{{autoAlpha:0,y:-30}},{{autoAlpha:1,y:0,duration:.55,ease:"expo.out"}},{start+.08:.3f});',
            f'tl.fromTo("{selector} .word>span",{{yPercent:130,rotation:9,scale:.7,autoAlpha:0}},{{yPercent:0,rotation:0,scale:1,autoAlpha:1,duration:.72,stagger:.11,ease:"back.out(1.8)"}},{start+.22:.3f});',
            f'tl.fromTo("{selector} .literal-visual, {selector} .logo-strip, {selector} .flow-graphic, {selector} .metrics",{{autoAlpha:0,y:90,scale:.72,rotation:-6}},{{autoAlpha:1,y:0,scale:1,rotation:0,duration:.9,ease:"elastic.out(1,.62)"}},{start+.68:.3f});',
            f'tl.to("{selector} .scene-inner",{{y:-13,duration:{max(1,beat-1):.3f},ease:"sine.inOut"}},{start+.95:.3f});',
            f'tl.fromTo("{selector} .scene-bottom",{{autoAlpha:0,y:25}},{{autoAlpha:1,y:0,duration:.55,ease:"expo.out"}},{start+1.0:.3f});',
            f'tl.fromTo("{selector} .draw",{{strokeDashoffset:270}},{{strokeDashoffset:0,duration:1.2,ease:"expo.out"}},{start+.9:.3f});',
            f'tl.fromTo("{selector} .bar-fill",{{scaleX:0}},{{scaleX:.92,duration:1.5,ease:"expo.out"}},{start+1:.3f});',
            f'tl.fromTo("{selector} .counter",{{textContent:0}},{{textContent:92,snap:{{textContent:1}},duration:1.5,ease:"expo.out",onUpdate:function(){{}}}},{start+1:.3f});',
        ]
        if i<len(phrases)-1:
            t=(i+1)*beat
            js += [
                f'tl.fromTo(".wipe-{i}",{{xPercent:-110,rotation:-5}},{{xPercent:110,rotation:-5,duration:.86,ease:"expo.inOut"}},{t-.43:.3f});',
                f'tl.fromTo(".wipe-alt-{i}",{{xPercent:-125,rotation:-5}},{{xPercent:125,rotation:-5,duration:.82,ease:"expo.inOut"}},{t-.31:.3f});',
                f'tl.fromTo(".circle-{i}",{{scale:0}},{{scale:1.5,duration:.52,ease:"expo.in"}},{t-.3:.3f});',
                f'tl.to(".circle-{i}",{{scale:0,duration:.5,ease:"expo.out"}},{t+.22:.3f});',
            ]
    js.append('window.__timelines["motion-studio"]=tl;')
    html_doc=('<!doctype html><html lang="es"><head><meta charset="utf-8"><style>'+css+
       '</style></head><body><div id="root" data-composition-id="motion-studio" data-start="0" data-duration="'+str(duration)+
       '" data-width="540" data-height="960"><div class="ambient"></div><div class="grid-bg"></div>'+
       '<div class="orb"></div><div class="orb two"></div><div class="brand-top">MOTION <span>STUDIO</span></div>'+
       ''.join(scenes)+''.join(f'<div class="wipe wipe-{i}"></div><div class="wipe alt wipe-alt-{i}"></div><div class="transition-circle circle-{i}"></div>' for i in range(len(phrases)-1))+
       '<div class="progress"><div class="progress-fill"></div></div></div>'+
       '<script src="./assets/gsap.min.js"></script><script>'+'\n'.join(js)+'</script></body></html>')
    (PROJECT/"index.html").write_text(html_doc,encoding="utf-8")
    cfg["scene_plan"]=plan
    (OUTPUT/"metadata.json").write_text(json.dumps(cfg,ensure_ascii=False,indent=2),encoding="utf-8")
    (OUTPUT/"CREDITS.txt").write_text("Motion Studio 4.0: original synthesized soundtrack, GSAP, HyperFrames, Simple Icons.\n",encoding="utf-8")
    synth_music(OUTPUT/"music.wav",duration,[i*beat for i in range(len(phrases))])
    print("Motion Studio 4 built:",duration,"seconds",len(plan),"scenes",W,H,FPS)

if __name__=="__main__":
    build()
