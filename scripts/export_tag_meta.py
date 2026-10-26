"""
Exports tag metadata from generator/tags.py to server/app/tag_meta.json
Ensures Part 1 (generator) and Part 2 (server) remain decoupled while sharing metadata.
"""

import json
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root / "generator"))

from tags import TAGS

out_path = root / "server" / "app" / "tag_meta.json"
out_path.parent.mkdir(parents=True, exist_ok=True)

with open(out_path, "w", encoding="utf-8") as f:
    json.dump(TAGS, f, indent=2)

print(f"Successfully generated {out_path} with {len(TAGS)} tag definitions.")
