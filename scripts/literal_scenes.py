"""Literal visual storyboard for HyperFrames: keywords, logos, comparisons.

Each short spoken clause becomes its own clip. This is deterministic text matching,
not speech-to-text or AI generation. All brand artwork is bundled from simple-icons.
"""
import html
import re
import shutil
from pathlib import Path

BRANDS = [
 ("Claude", "claude", ("claude", "anthropic")),
 ("ChatGPT", "openai", ("chatgpt", "chat gpt")),
 ("Codex", "openai", ("codex",)),
 ("ElevenLabs", "elevenlabs", ("elevenlabs", "eleven labs")),
 ("GitHub", "github", ("github", "git hub")),
 ("DeepSeek", "deepseek", ("deepseek", "deep seek")),
 ("Gemini", "googlegemini", ("gemini",)),
 ("HyperFrames", "hyperframes", ("hyperframes", "hyperframe")),
 ("Remotion", "remotion", ("remotion",)),
 ("FFmpeg", "ffmpeg", ("ffmpeg",)),
 ("OpenCode", "opencode", ("opencode", "open code")),
]
CONCEPTS = [
 ("buscar", "INVESTIGACIÓN", "🔎", ("investig", "buscar", "analiz", "información")),
 ("programar", "PROGRAMACIÓN", "⌘", ("código", "program", "desarroll", "software")),
 ("web", "PÁGINA WEB", "▣", ("página", "sitio web", "web", "landing")),
 ("video", "VIDEO", "▶", ("video", "vídeo", "render", "animaci")),
 ("voz", "VOZ", "◉", ("voz", "audio", "narr", "locuci", "sonido")),
 ("ventas", "RESULTADOS", "↗", ("venta", "cliente", "crecim", "negocio")),
 ("automatizar", "AUTOMATIZACIÓN", "⚙", ("automatiz", "workflow", "actions")),
]


def names_in(text):
    lowered = text.casefold()
    found = []
    for name, slug, keys in BRANDS:
        if any(re.search(r"(?<!\w)" + re.escape(k) + r"(?!\w)", lowered) for k in keys):
            found.append((name, slug))
    return found


def split_script(cfg):
    spoken = (cfg.get("script") or "").strip()
    if not spoken:
        spoken = ". ".join(filter(None, [cfg["title"], cfg["subtitle"], cfg["cta"]]))
    clauses = [s.strip(" \t\n-–") for s in re.split(r"(?:[.!?;]\s+|\n+|,\s+)", spoken) if s.strip()]
    # "Claude ... y Codex ..." is two events; "Claude es parecido a ChatGPT" stays together.
    expanded = []
    for clause in clauses:
        candidate = re.split(r"\s+y\s+(?=(?:Claude|ChatGPT|Codex|GitHub|ElevenLabs|DeepSeek|Gemini|OpenCode|Remotion|HyperFrames|FFmpeg)\b)", clause, flags=re.I)
        if len(candidate) > 1 and not re.search(r"\b(vs|versus|similar|parecido|mejor que|contra)\b", clause, flags=re.I):
            expanded.extend(candidate)
        else:
            expanded.append(clause)
    # Avoid scenes too short to read. Maximum 5 for a 6-20 sec video.
    parts = [s[:125] for s in expanded if s.strip()]
    max_scenes = max(2, min(5, int(cfg.get("duration", 12)) // 2))
    if len(parts) > max_scenes:
        parts = parts[:max_scenes-1] + ["; ".join(parts[max_scenes-1:])[:125]]
    return parts or [cfg["title"]]


def relation(clause, entities):
    text = clause.casefold()
    if len(entities) < 2:
        return None
    if re.search(r"\b(vs|versus|contra|comparar|comparación)\b", text):
        return "VS"
    if re.search(r"\b(similar(?:es)?|parecid[oa]s?|como)\b", text):
        return "SIMILAR"
    if re.search(r"\b(mejor que|supera|vence)\b", text):
        return "VS"
    return "→"


def bundle_icons(root, project):
    src = root/"node_modules"/"simple-icons"/"icons"
    dst = project/"assets"/"icons"
    dst.mkdir(parents=True, exist_ok=True)
    copied = []
    for _, slug, _ in BRANDS:
        file = src/(slug+".svg")
        if file.is_file():
            shutil.copyfile(file, dst/(slug+".svg"))
            copied.append(slug)
    return set(copied)


def card(entity, available):
    name, slug = entity
    caption = html.escape(name)
    initials = "".join(part[0] for part in name.split()).upper()
    if slug in available:
        visual = '<img src="./assets/icons/'+slug+'.svg" alt="Logo '+caption+'">'
    else:
        visual = '<span class="fallback-logo">'+html.escape(initials[:3])+'</span>'
    return '<div class="brand-card"><div class="logo-box">'+visual+'</div><strong>'+caption+'</strong></div>'


def concept(clause):
    lower = clause.casefold()
    for _, title, symbol, needles in CONCEPTS:
        if any(needle in lower for needle in needles):
            return '<div class="concept"><div class="concept-symbol">'+symbol+'</div><strong>'+title+'</strong></div>'
    return '<div class="concept"><div class="concept-symbol">▣</div><strong>IDEA PRINCIPAL</strong></div>'


def visual_for(clause, available):
    entities = names_in(clause)
    rel = relation(clause, entities)
    if rel:
        markup = (card(entities[0], available) +
                  '<div class="relation">'+html.escape(rel)+'</div>' +
                  card(entities[1], available))
        return '<div class="literal-visual pair">'+markup+'</div>', [x[0] for x in entities[:2]], rel
    if entities:
        markup = "".join(card(item, available) for item in entities[:3])
        return '<div class="literal-visual logos">'+markup+'</div>', [x[0] for x in entities[:3]], None
    return '<div class="literal-visual">'+concept(clause)+'</div>', [], None


def make_scenes(cfg, clip, root, project):
    available = bundle_icons(root, project)
    parts = split_script(cfg)
    result = []
    metadata = []
    for idx, clause in enumerate(parts):
        visual, brands, rel = visual_for(clause, available)
        headline = html.escape(clause, quote=True)
        # Larger titles may wrap poorly on very small layouts, cap to 125 chars.
        markup = ('<div class="spoken-title">'+headline+'</div>' +
                  visual + '<div class="scene-counter">ESCENA '+str(idx+1)+' / '+str(len(parts))+'</div>')
        result.append(clip(idx, "VISUAL BASADO EN EL GUION", markup))
        metadata.append({"sentence":clause,"brands":brands,"relation":rel})
    return result, metadata
