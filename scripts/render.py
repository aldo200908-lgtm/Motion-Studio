import os, math, subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

Path("output").mkdir(exist_ok=True)
vertical = os.getenv("FORMAT", "vertical") == "vertical"
w, h = (720, 1280) if vertical else (1280, 720)
duration = max(5, min(20, int(os.getenv("DURATION", "12"))))
title = os.getenv("TITLE", "Motion Studio")[:100]
subtitle = os.getenv("SUBTITLE", "Animaciones desde Android")[:120]
font_path = "/usr/share/fonts/truetype/dejavu/"
title_font = ImageFont.truetype(font_path + "DejaVuSans-Bold.ttf", 54 if vertical else 64)
sub_font = ImageFont.truetype(font_path + "DejaVuSans.ttf", 30 if vertical else 34)
def wrap(draw, text, font, maxwidth):
    lines, current = [], ""
    for word in text.split():
        candidate = (current + " " + word).strip()
        if draw.textbbox((0,0), candidate, font=font)[2] > maxwidth and current:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current: lines.append(current)
    return "\n".join(lines[:5])
cmd = ["ffmpeg","-hide_banner","-loglevel","error","-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{w}x{h}","-r","24","-i","-","-c:v","libx264","-preset","veryfast","-crf","24","-pix_fmt","yuv420p","-movflags","+faststart","output/video.mp4"]
p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
try:
    for frame in range(duration * 24):
        t = frame / 24
        im = Image.new("RGB", (w,h), (11,16,31))
        d = ImageDraw.Draw(im)
        for i in range(5):
            cx = int(w*(.1+i*.23)+math.sin(t*.8+i)*35)
            cy = int(h*(.18+i*.17)+math.cos(t*.6+i)*55)
            r = 35+i*11
            d.ellipse((cx-r,cy-r,cx+r,cy+r),outline=(32,124+i*15,190),width=4)
        progress = int((w-100)*t/duration)
        d.rounded_rectangle((50,h-80,50+progress,h-69),radius=5,fill=(255,122,0))
        alpha = max(0,min(1,t/.7,(duration-t)/.7))
        color = tuple(int(v*alpha) for v in (255,255,255))
        d.multiline_text((w/2,h*.44),wrap(d,title,title_font,w-110),font=title_font,fill=color,anchor="mm",align="center",spacing=12)
        d.multiline_text((w/2,h*.63),wrap(d,subtitle,sub_font,w-110),font=sub_font,fill=(145,190,220),anchor="mm",align="center",spacing=10)
        p.stdin.write(im.tobytes())
finally:
    p.stdin.close()
    rc = p.wait()
if rc: raise SystemExit(rc)
print("Generated output/video.mp4")
