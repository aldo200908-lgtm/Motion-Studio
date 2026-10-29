#!/usr/bin/env python3
"""Motion Studio 2.0: offline deterministic animation renderer, not an AI agent."""
import json, math, os, random, struct, subprocess, sys, wave
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"output"
SIZES={"vertical":(540,960),"horizontal":(960,540),"square":(720,720)}
STYLES={"high-energy","engaging","clean"}
FONTS=Path("/usr/share/fonts/truetype/dejavu")
random.seed(41)

def limit(v,a,b): return max(a,min(b,v))
def mix(a,b,n): return tuple(round(x*(1-n)+y*n) for x,y in zip(a,b))
def ease(n): return 1-(1-limit(n,0,1))**3
def font(n,bold=False): return ImageFont.truetype(str(FONTS/("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf")),max(12,int(n)))
def wrap(draw,text,f,width):
    lines=[]
    for segment in text.split("\n"):
        line=""
        for word in segment.split():
            trial=(line+" "+word).strip()
            if line and draw.textbbox((0,0),trial,font=f)[2]>width:
                lines.append(line);line=word
            else: line=trial
        lines.append(line)
    return "\n".join(lines[:5])
def centered(draw,text,x,y,width,size,color,bold=False):
    if text:
        f=font(size,bold)
        draw.multiline_text((int(x),int(y)),wrap(draw,text,f,width),font=f,fill=color,anchor="mm",align="center",spacing=10)

def configuration():
    cfg={k:os.getenv(k.upper(),v) for k,v in {
        "title":"Haz crecer tu negocio","subtitle":"Diseño web, apps y sistemas",
        "cta":"Cotiza por WhatsApp","style":"high-energy","format":"vertical",
        "accent":"#FF7A00","duration":"12","sound":"true"}.items()}
    if os.getenv("GITHUB_EVENT_NAME")=="issues":
        event=json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text(encoding="utf-8"))
        if event.get("issue",{}).get("user",{}).get("login","").lower()!="aldo200908-lgtm":
            raise ValueError("Only the repository owner can request a render")
        body=event.get("issue",{}).get("body") or ""
        marker="<!-- MOTION_STUDIO_REQUEST_V2 -->"
        fence=chr(96)*3
        if marker not in body or fence+"json" not in body:
            raise ValueError("Invalid Motion Studio issue")
        raw=body.split(marker,1)[1].split(fence+"json",1)[1].split(fence,1)[0]
        values=json.loads(raw)
        if not isinstance(values,dict): raise ValueError("Expected a JSON object")
        for key in cfg:
            if key in values: cfg[key]=values[key]
    for k in ("title","subtitle","cta"):
        cfg[k]=str(cfg[k]).strip()[:150]
    if not cfg["title"]: raise ValueError("Title required")
    if cfg["style"] not in STYLES or cfg["format"] not in SIZES:
        raise ValueError("Unknown style or format")
    color=str(cfg["accent"]).upper()
    if len(color)!=7 or not color.startswith("#") or any(c not in "0123456789ABCDEF" for c in color[1:]):
        raise ValueError("Invalid accent color")
    cfg["accent"]=color
    cfg["duration"]=int(limit(float(cfg["duration"]),6,20))
    cfg["sound"]=str(cfg["sound"]).lower() not in ("false","no","off","0")
    return cfg

def bg(width,height,accent,style):
    im=Image.new("RGB",(width,height))
    pix=im.load()
    base=(246,246,242) if style=="clean" else (11,17,30)
    other=mix(base,accent,.09 if style=="clean" else .2)
    for y in range(height):
        row=mix(base,other,y/height)
        for x in range(width): pix[x,y]=row
    return im

def draw_frame(cfg,base,t):
    w,h=base.size;style=cfg["style"]
    accent=tuple(int(cfg["accent"][i:i+2],16) for i in (1,3,5))
    im=base.copy();d=ImageDraw.Draw(im)
    scene_len=cfg["duration"]/4
    index=min(3,int(t/scene_len));u=(t-index*scene_len)/scene_len
    entrance=ease(u/.28);departure=limit((1-u)/.16,0,1)
    opacity=min(entrance,departure)
    fg=(26,35,45) if style=="clean" else (248,248,246)
    gray=(99,110,125) if style=="clean" else (166,181,204)
    pad=int(w*.07)
    titles=[cfg["title"],cfg["subtitle"] or "Una idea extraordinaria",
            "Tu proyecto cobra vida",cfg["cta"] or "Descubre más"]
    tags=["PRESENTAMOS","01 / DESCUBRE","02 / TRANSFORMA","03 / COMIENZA"]
    title=titles[index]
    if style=="high-energy":
        for j in range(6):
            theta=t*(.45+j*.08)+j*1.1
            x=w/2+math.cos(theta)*w*.4
            y=h*.47+math.sin(theta)*h*.24
            r=w*(.045+.014*j)
            d.ellipse((x-r,y-r,x+r,y+r),outline=mix((22,38,61),accent,.17+j*.12),width=3)
        d.rounded_rectangle((pad,h*.09,pad+w*.24,h*.097),radius=4,fill=accent)
        d.text((pad,h*.14),"MOTION STUDIO",font=font(w*.031,True),fill=gray)
        d.text((w-pad,h*.14),f"0{index+1}/04",font=font(w*.031,True),fill=gray,anchor="ra")
        if index in (1,2):
            centered(d,f"0{index}",w/2,h*.30,w*.7,w*.18,mix((24,37,57),accent,.6),True)
        centered(d,title,w/2,h*.49+(1-entrance)*h*.12,w*.86,w*.077,
                 mix((27,38,54),fg,opacity),True)
        centered(d,tags[index],w/2,h*.72,w*.85,w*.032,accent,True)
        d.rounded_rectangle((pad,h*.87,w-pad,h*.88),radius=4,fill=(40,49,68))
        d.rounded_rectangle((pad,h*.87,pad+(w-2*pad)*t/cfg["duration"],h*.88),radius=4,fill=accent)
    elif style=="clean":
        d.rounded_rectangle((pad,h*.08,w-pad,h*.093),radius=3,fill=accent)
        d.text((pad,h*.14),"MOTION / STUDIO",font=font(w*.029,True),fill=fg)
        d.text((w-pad,h*.14),f"0{index+1}/04",font=font(w*.028),fill=gray,anchor="ra")
        y=h*.23+(1-entrance)*h*.09
        d.rounded_rectangle((pad,y,w-pad,h*.78),radius=int(w*.05),fill=(255,255,255),outline=(224,225,225),width=2)
        d.rounded_rectangle((pad+w*.06,y+h*.047,pad+w*.19,y+h*.059),radius=3,fill=accent)
        centered(d,title,w/2,h*.49+(1-entrance)*h*.06,w*.74,w*.065,
                 mix((255,255,255),fg,opacity),True)
        centered(d,tags[index],w/2,h*.67,w*.75,w*.03,gray)
        for j in range(4):
            d.ellipse((w*.32+j*w*.12,h*.86,w*.34+j*w*.12,h*.86+w*.02),
                      fill=accent if j==index else (204,208,210))
    else:
        points=[(w*.17,h*.28),(w*.8,h*.35),(w*.22,h*.67),(w*.8,h*.79)]
        for j in range(3):
            d.line((*points[j],*points[j+1]),fill=mix((43,57,77),accent,.35),width=max(3,int(w*.008)))
        for j,(x,y) in enumerate(points):
            r=w*(.05 if j==index else .034)
            d.ellipse((x-r,y-r,x+r,y+r),fill=accent if j<=index else (44,57,73))
            centered(d,str(j+1),x,y,w*.1,w*.026,(255,255,255),True)
        a,b=points[index],points[min(index+1,3)];p=ease(u)
        x=a[0]+(b[0]-a[0])*p;y=a[1]+(b[1]-a[1])*p;r=w*.025
        d.ellipse((x-r,y-r,x+r,y+r),fill=(255,255,255),outline=accent,width=4)
        d.rounded_rectangle((pad,h*.39,w-pad,h*.6),radius=int(w*.035),
                            fill=(17,26,42),outline=(57,69,88),width=2)
        centered(d,title,w/2,h*.49+(1-entrance)*h*.04,w*.78,w*.067,
                 mix((17,26,42),fg,opacity),True)
        d.text((pad,h*.11),"ONE STORY / FOUR STEPS",font=font(w*.028,True),fill=gray)
        d.text((pad,h*.9),tags[index],font=font(w*.03,True),fill=accent)
    return im

def sound_file(duration,path):
    rate=22050;hits=[i*duration/4 for i in range(4)]
    with wave.open(str(path),"wb") as wf:
        wf.setnchannels(1);wf.setsampwidth(2);wf.setframerate(rate)
        data=bytearray()
        for n in range(rate*duration):
            t=n/rate;v=0.
            for cue in hits:
                u=t-cue
                if 0<=u<.2: v+=.3*math.sin(2*math.pi*160*u)*math.exp(-23*u)
                if .03<=u<.27: v+=.047*(random.random()*2-1)*math.exp(-15*(u-.03))
            data.extend(struct.pack("<h",int(limit(v,-.9,.9)*32767)))
        wf.writeframes(data)

def main():
    cfg=configuration()
    OUT.mkdir(exist_ok=True)
    w,h=SIZES[cfg["format"]]
    accent=tuple(int(cfg["accent"][i:i+2],16) for i in (1,3,5))
    base=bg(w,h,accent,cfg["style"])
    if cfg["sound"]:sound_file(cfg["duration"],OUT/"sfx.wav")
    cmd=["ffmpeg","-hide_banner","-loglevel","error","-y","-f","rawvideo",
         "-pix_fmt","rgb24","-s",f"{w}x{h}","-r","24","-i","-"]
    if cfg["sound"]:cmd+=["-i",str(OUT/"sfx.wav"),"-map","0:v:0","-map","1:a:0"]
    cmd+=["-c:v","libx264","-preset","veryfast","-crf","24","-pix_fmt","yuv420p"]
    if cfg["sound"]:cmd+=["-c:a","aac","-b:a","128k","-af","loudnorm=I=-16:TP=-3:LRA=11","-shortest"]
    cmd+=["-movflags","+faststart",str(OUT/"video.mp4")]
    process=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    try:
        for frame in range(cfg["duration"]*24):
            im=draw_frame(cfg,base,frame/24)
            process.stdin.write(im.tobytes())
    finally:
        process.stdin.close()
    if process.wait():raise RuntimeError("FFmpeg render failed")
    (OUT/"metadata.json").write_text(json.dumps(cfg,indent=2,ensure_ascii=False),encoding="utf-8")
    (OUT/"CREDITS.txt").write_text(
        "Video and original synthesized SFX by Motion Studio 2.0.\n"
        "Style inspiration: Barty-Bart/motion-graphics (MIT).\n"
        "No agent skills were executed and no external media were used.\n",encoding="utf-8")
    print(f"OK output/video.mp4 — {w}x{h}, {cfg['duration']}s, {cfg['style']}")

if __name__=="__main__":
    try:main()
    except Exception as exc:
        print(f"Render failed: {exc}",file=sys.stderr)
        sys.exit(1)
