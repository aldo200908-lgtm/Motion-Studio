#!/usr/bin/env python3
"""Release gate: ffprobe, scene layout/beat validation, soundtrack and storyboard."""
import json
import hashlib
import os
import shutil
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

commit=subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip()
branch=subprocess.check_output(["git","rev-parse","--abbrev-ref","HEAD"],text=True).strip()
if branch=="HEAD":
    branch=os.environ.get("GITHUB_REF_NAME","detached")
assert os.environ.get("GITHUB_SHA",commit)==commit,("Workflow checkout is not the triggering commit",commit,os.environ.get("GITHUB_SHA"))
assert (root/"scripts/kinetic_v5.py").is_file(),"v5 engine missing from checkout"
assert (root/"scripts/verify_v5.py").is_file(),"release validator missing from checkout"
digest=hashlib.sha256(mp4.read_bytes()).hexdigest()
previous=root/"previous-render"/"video.mp4"
assert previous.is_file(),"Previous successful render unavailable: refusing unverified release"
previous_digest=hashlib.sha256(previous.read_bytes()).hexdigest()
assert digest!=previous_digest,("Duplicate MP4 from prior successful render",digest)
assert not digest.startswith("35b4fc5bfb8e7c7f77eeca27ae87383d"),("Matches user-reported stale render",digest)
filename=f"motion_v5_{commit[:7]}.mp4"
shutil.copyfile(mp4,root/"output"/filename)
report={
  "version":"5.0","verified":True,"branch":branch,"commit":commit,
  "commit_short":commit[:7],"mp4_filename":filename,"mp4_sha256":digest,
  "previous_mp4_sha256":previous_digest,
  "duration_seconds":duration,"fps":num/den,"width":video["width"],"height":video["height"],
  "video_codec":video["codec_name"],"audio_codec":audio["codec_name"],
  "music_bpm":metadata.get("music_bpm"),"scenes":scenes,
  "transitions":metadata.get("transitions",[]),
  "engine_script":"scripts/kinetic_v5.py"
}
(root/"output"/"render-report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
print("CHECKOUT_BRANCH="+branch)
print("CHECKOUT_COMMIT_SHA256="+commit)
print("MP4_SHA256="+digest)
print("PREVIOUS_MP4_SHA256="+previous_digest)
print("VERIFIED_MP4="+filename)
print(json.dumps(report,ensure_ascii=False))
