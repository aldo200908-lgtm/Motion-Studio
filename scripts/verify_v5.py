#!/usr/bin/env python3
"""Release gate: ffprobe, scene layout/beat validation, soundtrack and storyboard."""
import json
import subprocess
from pathlib import Path

root=Path(__file__).resolve().parents[1]
metadata=json.loads((root/"output/metadata.json").read_text())
mp4=root/"output/video.mp4"
assert mp4.exists() and mp4.stat().st_size>100000,"MP4 missing or too small"
probe=json.loads(subprocess.check_output(["ffprobe","-v","error","-show_streams","-show_format","-of","json",str(mp4)],text=True))
video=next(s for s in probe["streams"] if s["codec_type"]=="video")
audio=next((s for s in probe["streams"] if s["codec_type"]=="audio"),None)
duration=float(probe["format"]["duration"])
assert 15<=duration<=20.1,(duration,"duration")
assert abs(duration-metadata["duration"])<.15,(duration,metadata["duration"])
assert (video["width"],video["height"])==(540,960),video
num,den=map(int,video["avg_frame_rate"].split("/"))
assert abs(num/den-24)<.001,video["avg_frame_rate"]
assert audio is not None,"Audio track missing"
scenes=metadata["scene_plan"]
assert 4<=len(scenes)<=5
assert all(2.5<=s["nominal_duration"]<=5 for s in scenes)
assert all(a["layout"]!=b["layout"] for a,b in zip(scenes,scenes[1:]))
assert abs(sum(s["nominal_duration"] for s in scenes)-metadata["duration"])<.001
assert all(abs(s["start"]*2-round(s["start"]*2))<.001 for s in scenes),"Cuts off 120 BPM beat grid"
assert all((root/f"output/storyboard-{i+1:02d}.png").stat().st_size>1000 for i in range(len(scenes)))
# Detect blank/occluded scenes (e.g. a fullscreen transition accidentally covering the film).
for scene in scenes:
    t=scene["start"]+scene["nominal_duration"]/2
    frame=subprocess.check_output(["ffmpeg","-hide_banner","-loglevel","error","-ss",str(t),"-i",str(mp4),"-frames:v","1","-vf","scale=54:96","-pix_fmt","rgb24","-f","rawvideo","-"])
    assert len(frame)==54*96*3
    colors={frame[i:i+3] for i in range(0,len(frame),3)}
    assert len(colors)>100,("scene visually occluded or blank",scene["scene"],len(colors))

print(json.dumps({"verified":True,"duration":duration,"resolution":"540x960","fps":24,"audio":audio["codec_name"],"scenes":len(scenes),"layouts":[s["layout"] for s in scenes],"cuts":[s["start"] for s in scenes[1:]]},ensure_ascii=False))
