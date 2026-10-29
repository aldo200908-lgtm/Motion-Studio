#!/usr/bin/env python3
"""Motion Studio 5: continuous motion, editorial scenes, beat-synced transitions."""
import html
import json
import math
import random
import re
import shutil
import struct
import wave

from hyperframes_build import ROOT, PROJECT, OUTPUT, read_config
from literal_scenes import bundle_icons, names_in

W,H,FPS=540,960,24

def safe(t):
    return html.escape(str(t),quote=True)

def brand(name,icons):
    slugs={"Claude":"claude","ChatGPT":"openai","Codex":"codex","GitHub":"github","HyperFrames":"hyperframes"}
    slug=slugs.get(name,"")
    if slug in icons:
        mark=f'<img src="./assets/icons/{slug}.svg" alt="Logo de {safe(name)}">'
    else:
        mark=f'<span class="logo-missing">LOGO NO DISPONIBLE</span>'
    return f'<div class="brand-card"><div class="brand-symbol">{mark}</div><strong>{safe(name)}</strong></div>'

def kinetic(s):
    words=s.split()
    key=next((i for i,w in enumerate(words) if any(k in w.casefold() for k in ("motion","claude","codex","video","gsap","crea","acción"))),max(0,len(words)//2))
    return '<div class="kinetic">'+''.join(f'<span class="word {"key" if i==key else ""}"><span>{safe(w)}</span></span>' for i,w in enumerate(words))+'</div>'

def audio(path,duration,cues):
    rate=24000
    n=round(duration*rate)
    random.seed(19)
    samples=[0.0]*n
    # Fully original four-chord bed, rhythmic 120 BPM pulse, transitions and entrance impacts.
    tones=(110,130.81,146.83,164.81)
    for j in range(n):
        t=j/rate
        root=tones[int(t//4)%4]
        env=min(1,t*2,max(0,(duration-t)*2))
        samples[j]=env*(.033*math.sin(2*math.pi*root*t)+.018*math.sin(2*math.pi*root*1.5*t)+.015*math.sin(2*math.pi*root*2*t))
    for k in range(int(duration*2)):
        st=int(k*.5*rate)
        for j in range(min(int(.17*rate),n-st)):
            x=j/rate
            kick=.19*math.sin(2*math.pi*(95-130*x)*x)*math.exp(-26*x)
            hat=.035*(random.random()*2-1)*math.exp(-72*x)
            samples[st+j]+=kick+hat
    for cue in cues:
        st=int(cue*rate)
        for j in range(min(int(.45*rate),n-st)):
            x=j/rate
            impact=.22*math.sin(2*math.pi*(260+720*x)*x)*math.exp(-15*x)
            sweep=.065*(random.random()*2-1)*math.exp(-8*x)
            samples[st+j]+=impact+sweep
    with wave.open(str(path),"wb") as f:
        f.setnchannels(1);f.setsampwidth(2);f.setframerate(rate)
        buf=bytearray()
        for v in samples:
            buf.extend(struct.pack("<h",round(max(-.92,min(.92,math.tanh(v*1.5)))*32767)))
        f.writeframes(buf)

def main():
    cfg=read_config()
    duration=max(15,min(20,int(cfg["duration"])))
    # 120 BPM, half-beat quantization (0.25 s). Scene lengths are nonuniform.
    # At 15s: 3.0 + 4.0 + 3.5 + 4.5. At 20s: 4 + 5 + 4.5 + 6.5 would exceed 5,
    # so use 5 scenes for longer renders.
    if duration<=17:
        lengths=[3.0,4.0,3.5,duration-10.5]
    else:
        lengths=[3.0,4.0,3.5,4.5,duration-15]
        if lengths[-1]<2.5:
            lengths=[3.5,4.0,4.0,duration-11.5]
    # Force last duration <=5 by redistributing for 18–20s.
    if len(lengths)==4 and lengths[-1]>5:
        lengths=[4.0,4.5,4.5,duration-13.0]
    if len(lengths)==5 and lengths[-1]<2.5:
        lengths=[3.5,4.0,4.0,4.5,duration-16]
    if not all(2.5<=x<=5 for x in lengths):
        lengths=[duration/4]*4
    assert abs(sum(lengths)-duration)<.0001
    cfg.update(engine="hyperframes",format="vertical",duration=duration,sound=True)
    PROJECT.mkdir(parents=True,exist_ok=True)
    (PROJECT/"assets").mkdir(exist_ok=True)
    OUTPUT.mkdir(parents=True,exist_ok=True)
    gsap=ROOT/"node_modules"/"gsap"/"dist"/"gsap.min.js"
    if not gsap.exists():
        raise RuntimeError("GSAP not installed")
    shutil.copyfile(gsap,PROJECT/"assets"/"gsap.min.js")
    icons=bundle_icons(ROOT,PROJECT)

    # Demo has a deliberate editorial arc, never an ambiguous VS comparison.
    # For custom requests, preserve title and user script without inventing claims.
    push_demo=cfg["title"].casefold().startswith("de una idea a un video")
    if push_demo:
        texts=[
            "DE UNA IDEA A UN VIDEO",
            "CLAUDE ORGANIZA EL GUION",
            "CODEX ANIMA CON GSAP",
            "MOTION STUDIO: CREA TU PRÓXIMO VIDEO",
        ]
    else:
        parts=[p.strip() for p in re.split(r"[.!?;]\s+|\n+",cfg.get("script","")) if p.strip()]
        texts=[cfg["title"]]
        texts.extend(parts[:max(0,len(lengths)-2)])
        while len(texts)<len(lengths)-1:
            texts.append(cfg.get("subtitle") or "Cada escena cuenta una idea")
        texts=texts[:len(lengths)-1]+[cfg["cta"] or "Crea tu próximo video"]
    if len(lengths)==5 and len(texts)==4:
        texts.insert(3,"GITHUB ACTIONS CONVIERTE EL DISEÑO EN MP4")
    layouts=["hero","duo","workflow","metric","cta"] if len(lengths)==5 else ["hero","duo","workflow","cta"]
    assert all(a!=b for a,b in zip(layouts,layouts[1:]))
    starts=[0.0]
    for d in lengths[:-1]:
        starts.append(round(starts[-1]+d,3))
    cuts=starts[1:]
    scenes=[]
    plan=[]
    for i,(name,text,start,nominal) in enumerate(zip(layouts,texts,starts,lengths)):
        clip_start=max(0,start-(.28 if i else 0))
        clip_end=min(duration,start+nominal+(.28 if i<len(lengths)-1 else 0))
        visual=""
        if name=="hero":
            visual='<div class="hero-graphic"><div class="halo halo-a"></div><div class="hero-ring"></div><div class="hero-arrow">↗</div><div class="hero-caption">IDEA → MOVIMIENTO</div></div>'
        elif name=="duo":
            names=[n for n,_ in names_in(text)]
            if not names: names=["Claude","ChatGPT"]
            visual='<div class="logo-duo">'+''.join(brand(n,icons) for n in names[:2])+'</div>'
        elif name=="workflow":
            visual='<div class="pipeline">'+brand("Codex",icons)+'<svg class="connector" viewBox="0 0 180 90"><path d="M8 45 H168 M145 20 L168 45 L145 70"/></svg><div class="code-window"><div class="code-line"></div><div class="code-line short"></div><div class="code-line accent"></div><span>GSAP</span></div></div>'
        elif name=="metric":
            visual='<div class="metric"><div class="meter-track"><div class="meter-fill"></div></div><div class="meter-label">MP4 · 24 FPS</div></div>'
        else:
            visual='<div class="cta-graphic"><div class="cta-play">▶</div><div class="cta-label">MOTION STUDIO</div><div class="cta-under">CREA · ANIMA · PUBLICA</div></div>'
        scenes.append(f'<section id="scene-{i}" class="clip scene scene-{i} layout-{name}" data-start="{clip_start:.3f}" data-duration="{clip_end-clip_start:.3f}" data-track-index="{i%3}"><div class="scene-inner"><div class="eyebrow">MOTION STUDIO / {i+1:02d}</div>{kinetic(text)}{visual}<div class="footer-line">DISEÑO EN MOVIMIENTO · {i+1:02d}</div></div></section>')
        plan.append(dict(scene=i+1,layout=name,text=text,start=start,nominal_duration=nominal,clip_start=round(clip_start,3),clip_end=round(clip_end,3),brands=[n for n,_ in names_in(text)]))
    css=r"""
*{box-sizing:border-box}html,body{margin:0;width:540px;height:960px;overflow:hidden;background:#080c17}
body{font-family:Arial,Helvetica,sans-serif;color:#fff}
#root{width:540px;height:960px;position:relative;overflow:hidden;isolation:isolate;background:#080c17}
.ambient{position:absolute;inset:-25%;background:radial-gradient(ellipse at 25% 30%,#1d3354 0,transparent 45%),radial-gradient(ellipse at 80% 75%,#2c1d3c 0,transparent 50%);opacity:.8}
.grid{position:absolute;inset:-15%;background-image:linear-gradient(#ffffff10 1px,transparent 1px),linear-gradient(90deg,#ffffff10 1px,transparent 1px);background-size:70px 70px;opacity:.6}
.glow{position:absolute;left:-140px;top:160px;width:370px;height:370px;border-radius:50%;filter:blur(55px);background:ACCENT;opacity:.18}
.glow.second{left:380px;top:570px;background:#65baff}
.topbrand{position:absolute;top:50px;left:35px;right:35px;z-index:70;display:flex;justify-content:space-between;align-items:center;font-weight:900;letter-spacing:2.5px;font-size:16px}
.topbrand em{font-style:normal;color:ACCENT}
.topbrand .badge-small{font-size:11px;color:#aab7cb;letter-spacing:2px}
.progress{position:absolute;bottom:45px;left:35px;right:35px;height:5px;background:#ffffff26;border-radius:8px;z-index:70}
.progress-fill{width:100%;height:100%;background:ACCENT;transform-origin:left;border-radius:8px}
.scene{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;padding:115px 29px 115px;overflow:hidden}
.scene-inner{display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;gap:28px;width:100%;min-height:560px}
.eyebrow{font-size:16px;font-weight:900;letter-spacing:3px;color:ACCENT}
.kinetic{display:flex;flex-wrap:wrap;justify-content:center;gap:8px 10px;font-weight:950;font-size:62px;line-height:.98;letter-spacing:-2.5px;text-transform:uppercase}
.word{display:inline-block;overflow:hidden;padding-bottom:10px}.word span{display:block}
.word.key{color:ACCENT;font-size:1.05em;text-shadow:0 0 28px #ff7a0045}
.layout-duo .kinetic,.layout-workflow .kinetic{font-size:58px}
.layout-cta .kinetic{font-size:60px}
.footer-line{font-size:13px;font-weight:900;letter-spacing:2.3px;color:#aab7cb}
.hero-graphic{width:320px;height:260px;position:relative;display:grid;place-items:center}
.halo{position:absolute;border:3px solid ACCENT;border-radius:50%;width:220px;height:220px;opacity:.35}
.hero-ring{position:absolute;width:170px;height:170px;border:8px solid ACCENT;border-radius:50%;box-shadow:0 0 80px #ff7a0030}
.hero-arrow{position:relative;color:ACCENT;font-size:105px;font-weight:900}
.hero-caption{position:absolute;bottom:-5px;font-size:16px;letter-spacing:3px;font-weight:900}
.logo-duo{display:flex;gap:20px;justify-content:center;align-items:center;width:100%;min-height:245px}
.brand-card{flex:1;max-width:200px;min-width:0;border:2px solid #43506a;background:#172139;border-radius:28px;padding:22px 10px;display:flex;flex-direction:column;align-items:center;gap:16px;box-shadow:0 25px 45px #0005}
.brand-symbol{width:112px;height:112px;border-radius:22px;background:#fff;display:grid;place-items:center;padding:20px}
.brand-symbol img{width:100%;height:100%;object-fit:contain}
.logo-missing{font-size:12px;font-weight:900;color:#111}
.brand-card strong{font-size:23px;overflow-wrap:anywhere}
.pipeline{display:flex;gap:5px;align-items:center;justify-content:center;width:100%}
.pipeline .brand-card{max-width:160px;padding:12px 6px}.pipeline .brand-symbol{width:85px;height:85px}.pipeline .brand-card strong{font-size:21px}
.connector{width:85px;flex-shrink:0;overflow:visible}.connector path{fill:none;stroke:ACCENT;stroke-width:8;stroke-linecap:round;stroke-linejoin:round;stroke-dasharray:270;stroke-dashoffset:270}
.code-window{width:170px;height:180px;border:2px solid #465775;border-radius:23px;background:#152139;padding:24px 16px;display:flex;flex-direction:column;justify-content:center;gap:15px}
.code-line{height:11px;width:100%;background:#7591bd;border-radius:10px}.code-line.short{width:65%}.code-line.accent{background:ACCENT;width:85%}
.code-window span{font-size:22px;font-weight:900;color:ACCENT}
.metric{width:90%;border:2px solid #43506a;background:#182138;padding:35px 20px;border-radius:28px}
.meter-track{width:100%;height:20px;border-radius:20px;background:#394862;overflow:hidden}.meter-fill{height:100%;width:100%;background:ACCENT;transform-origin:left}
.meter-label{font-size:24px;font-weight:900;margin-top:28px;letter-spacing:3px}
.cta-graphic{position:relative;display:flex;align-items:center;flex-direction:column;gap:14px;padding:20px}
.cta-play{width:148px;height:148px;border-radius:50%;background:ACCENT;color:#0a0e17;display:grid;place-items:center;font-size:68px;box-shadow:0 0 65px #ff7a0055}
.cta-label{font-size:36px;letter-spacing:-1px;font-weight:900}
.cta-under{font-size:17px;letter-spacing:3px;font-weight:900;color:ACCENT}
.trans-wipe{position:absolute;inset:-10%;z-index:42;background:ACCENT;opacity:0;pointer-events:none}
.trans-zoom{position:absolute;left:50%;top:50%;margin-left:-700px;margin-top:-700px;width:1400px;height:1400px;border-radius:50%;background:#f3f5fa;z-index:43;opacity:0;pointer-events:none}
.trans-shape{position:absolute;left:50%;top:50%;margin-left:-800px;margin-top:-800px;width:1600px;height:1600px;background:ACCENT;border-radius:23%;z-index:44;opacity:0;pointer-events:none}
"""
    css=css.replace("ACCENT",cfg["accent"])
    js=[
        'window.__timelines=window.__timelines||{};',
        'const tl=gsap.timeline({paused:true});',
        f'tl.fromTo(".progress-fill",{{scaleX:0}},{{scaleX:1,duration:{duration},ease:"none"}},0);',
        f'tl.fromTo(".ambient",{{scale:1,x:0,y:0}},{{scale:1.26,x:55,y:-55,duration:{duration},ease:"none"}},0);',
        f'tl.fromTo(".grid",{{x:0,y:0}},{{x:-90,y:90,duration:{duration},ease:"none"}},0);',
        f'tl.fromTo(".glow",{{x:0,y:0}},{{x:210,y:-100,duration:{duration},ease:"sine.inOut"}},0);',
        f'tl.fromTo(".glow.second",{{x:0,y:0}},{{x:-190,y:120,duration:{duration},ease:"sine.inOut"}},0);'
    ]
    for i,(start,dur) in enumerate(zip(starts,lengths)):
        sel=f".scene-{i}"
        clip_start=max(0,start-(.28 if i else 0))
        clip_end=min(duration,start+dur+(.28 if i<len(lengths)-1 else 0))
        active=clip_end-clip_start
        # Start inside the visible clip and animate until its end. At cuts, outgoing and incoming overlap.
        js.extend([
            f'tl.fromTo("{sel} .scene-inner",{{scale:1.045,y:16,opacity:0}},{{scale:1.0,y:-13,opacity:1,duration:.52,ease:"expo.out"}},{clip_start:.3f});',
            f'tl.to("{sel} .scene-inner",{{scale:1.09,x:10,y:-30,duration:{max(.5,active-.52):.3f},ease:"none",overwrite:"auto"}},{clip_start+.52:.3f});',
            f'tl.fromTo("{sel} .eyebrow",{{y:-30,autoAlpha:0}},{{y:0,autoAlpha:1,duration:.55,ease:"expo.out"}},{clip_start+.1:.3f});',
            f'tl.fromTo("{sel} .word>span",{{yPercent:125,rotation:7,scale:.7,autoAlpha:0}},{{yPercent:0,rotation:0,scale:1,autoAlpha:1,duration:.66,stagger:.085,ease:"back.out(1.7)"}},{clip_start+.19:.3f});',
            f'tl.fromTo("{sel} .hero-graphic, {sel} .logo-duo, {sel} .pipeline, {sel} .metric, {sel} .cta-graphic",{{autoAlpha:0,y:80,scale:.7}},{{autoAlpha:1,y:0,scale:1,duration:.95,ease:"elastic.out(1,.68)"}},{clip_start+.45:.3f});',
            f'tl.fromTo("{sel} .brand-card",{{y:14,rotation:-3}},{{y:-12,rotation:3,duration:1.25,ease:"sine.inOut",repeat:{max(1,math.ceil(active/2.5))},yoyo:true,immediateRender:false}},{clip_start+.65:.3f});',
            f'tl.fromTo("{sel} .hero-ring, {sel} .cta-play",{{scale:1}},{{scale:1.07,duration:.6,ease:"sine.inOut",repeat:{max(1,math.ceil(active/1.2))},yoyo:true,immediateRender:false}},{clip_start+.7:.3f});',
            f'tl.fromTo("{sel} .connector path",{{strokeDashoffset:270}},{{strokeDashoffset:0,duration:1.6,ease:"expo.out"}},{clip_start+.8:.3f});',
            f'tl.fromTo("{sel} .meter-fill",{{scaleX:0}},{{scaleX:.92,duration:1.4,ease:"expo.out"}},{clip_start+.8:.3f});',
            f'tl.fromTo("{sel} .footer-line",{{autoAlpha:0,y:20}},{{autoAlpha:1,y:0,duration:.65,ease:"expo.out"}},{clip_start+.95:.3f});'
        ])
        if i<len(lengths)-1:
            cut=starts[i+1]
            # Outgoing opacity fades as next scene enters; no blank frame at boundary.
            js.append(f'tl.to("{sel} .scene-inner",{{opacity:0,duration:.32,ease:"sine.in"}},{cut-.12:.3f});')
            kind=("wipe","zoom","shape")[i%3]
            if kind=="wipe":
                js.append(f'tl.fromTo(".trans-wipe-{i}",{{xPercent:-115,opacity:0}},{{xPercent:115,opacity:1,duration:.7,ease:"expo.inOut",immediateRender:false}},{cut-.35:.3f});')
            elif kind=="zoom":
                js.append(f'tl.fromTo(".trans-zoom-{i}",{{scale:0,opacity:0}},{{scale:1.6,opacity:1,duration:.38,ease:"expo.in",immediateRender:false}},{cut-.32:.3f});')
                js.append(f'tl.to(".trans-zoom-{i}",{{scale:0,duration:.4,ease:"expo.out"}},{cut+.06:.3f});')
            else:
                js.append(f'tl.fromTo(".trans-shape-{i}",{{scale:0,rotation:-35,opacity:0}},{{scale:1.6,rotation:25,opacity:1,duration:.42,ease:"expo.in",immediateRender:false}},{cut-.34:.3f});')
                js.append(f'tl.to(".trans-shape-{i}",{{scale:0,duration:.4,ease:"expo.out"}},{cut+.08:.3f});')
    js.append('window.__timelines["motion-studio"]=tl;')
    overlays=''.join(
        f'<div class="trans-wipe trans-wipe-{i}"></div>' if i%3==0 else
        (f'<div class="trans-zoom trans-zoom-{i}"></div>' if i%3==1 else f'<div class="trans-shape trans-shape-{i}"></div>')
        for i in range(len(cuts))
    )
    markup=('<!doctype html><html lang="es"><head><meta charset="utf-8"><style>'+css+
        '</style></head><body><div id="root" data-composition-id="motion-studio" data-start="0" data-duration="'+str(duration)+
        '" data-width="540" data-height="960"><div class="ambient"></div><div class="grid"></div>'+
        '<div class="glow"></div><div class="glow second"></div>'+
        '<div class="topbrand">MOTION <em>STUDIO</em><span class="badge-small">KINETIC FILMS</span></div>'+
        ''.join(scenes)+overlays+'<div class="progress"><div class="progress-fill"></div></div></div>'+
        '<script src="./assets/gsap.min.js"></script><script>'+'\n'.join(js)+'</script></body></html>')
    (PROJECT/"index.html").write_text(markup,encoding="utf-8")
    cfg["scene_plan"]=plan
    cfg["transitions"]=["wipe","zoom-through","growing-shape"][:len(cuts)]
    cfg["music_bpm"]=120
    cfg["beat_grid_seconds"]=.5
    (OUTPUT/"metadata.json").write_text(json.dumps(cfg,ensure_ascii=False,indent=2),encoding="utf-8")
    (OUTPUT/"CREDITS.txt").write_text("Motion Studio 5.0 | GSAP / HyperFrames | original synthesized music and SFX | official logos when available; otherwise explicit placeholder.\n",encoding="utf-8")
    audio(OUTPUT/"music.wav",duration,[0]+cuts)
    print("Motion Studio 5: duration",duration,"scene cuts",cuts,"layouts",layouts)

if __name__=="__main__":
    main()
