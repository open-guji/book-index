"""book-text 的 `index/texts/{0-f}.json` 讀取：`{id: [{key, kind, label, chapters_total, quality?}]}`。

`kind` ∈ transcription／collated／self_collated。`quality`（若有）∈ none／placeholder 的版本不算「有」。
"""
import json
import os

BAD_QUALITY = ('none', 'placeholder')
COLLATED_KINDS = ('collated', 'self_collated')


def load(path):
    """→ {id: [version, …]}。path 為 `<book-text>/index/texts` 目錄。"""
    out = {}
    for fn in sorted(os.listdir(path)):
        if fn.endswith('.json'):
            with open(os.path.join(path, fn), encoding='utf-8') as f:
                for i, vs in json.load(f).items():
                    out.setdefault(i, []).extend(v for v in vs if isinstance(v, dict))
    return out


def usable(v):
    return v.get('quality') not in BAD_QUALITY


def flags(versions):
    """→ (has_text, has_collated)：只計 quality 可用的版本；任一可用版本即「有文本」。"""
    ok = [v for v in versions if usable(v)]
    return bool(ok), any(v.get('kind') in COLLATED_KINDS for v in ok)
