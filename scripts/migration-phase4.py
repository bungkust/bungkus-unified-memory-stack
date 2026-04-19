#!/usr/bin/env python3
"""Phase 4: Index Brain + Obsidian pages ke MemPalace."""
import os, sys, re
from pathlib import Path

sys.path.insert(0, os.path.expanduser("~/.hermes/mempalace-venv/lib/python3.12/site-packages"))
os.environ["MEMPALACE_PALACE"] = "/root/.mempalace/palace"

from mempalace.mcp_server import tool_add_drawer, tool_search

def get_tldr(filepath, max_lines=8):
    """Extract TLDR from markdown file — first meaningful lines."""
    try:
        with open(filepath, 'r', errors='ignore') as f:
            lines = f.readlines()
    except:
        return None
    
    # Skip frontmatter
    content_lines = []
    in_frontmatter = False
    for line in lines:
        stripped = line.strip()
        if stripped == '---':
            in_frontmatter = not in_frontmatter
            continue
        if not in_frontmatter and stripped and not stripped.startswith('#'):
            content_lines.append(stripped)
        elif stripped.startswith('##') and not in_frontmatter:
            content_lines.append(stripped)
    
    if not content_lines:
        # Fallback: first non-empty lines
        content_lines = [l.strip() for l in lines if l.strip() and not l.strip().startswith('---')][:max_lines]
    
    return ' | '.join(content_lines[:max_lines])[:500]

def add_index(wing, room, title, content, source):
    """Add wiki page index to MemPalace."""
    # Duplicate check
    existing = tool_search(title[:50], limit=2)
    if "results" in existing:
        for r in existing["results"]:
            if r.get("similarity", 0) > 0.90:
                return False
    
    tool_add_drawer(wing=wing, room=room, 
                    content=f"[{title}] {content}", 
                    source_file=source)
    return True

added = 0
skipped = 0

# ─── INDEX BRAIN ───
print("=" * 50)
print("INDEXING BRAIN (/root/brain/)")
print("=" * 50)

brain_dir = Path("/root/brain")
for md_file in brain_dir.rglob("*.md"):
    rel = md_file.relative_to(brain_dir)
    parts = rel.parts
    
    # Skip index files and scripts
    if md_file.name in ("index.md", "README.md"):
        continue
    if "scripts" in parts:
        continue
    
    category = parts[0] if len(parts) > 1 else "general"
    title = md_file.stem.replace("-", " ").title()
    tldr = get_tldr(md_file)
    
    if tldr:
        room = f"brain-{category}"
        if add_index("research", room, title, tldr, f"brain/{rel}"):
            print(f"  ✅ {category}/{title}")
            added += 1
        else:
            skipped += 1

print(f"\nBrain: {added} indexed, {skipped} skipped (duplicates)")

# ─── INDEX OBSIDIAN (key pages only — not all 105) ───
print("\n" + "=" * 50)
print("INDEXING OBSIDIAN (/root/obsidian-vault/)")
print("=" * 50)

vault_dir = Path("/root/obsidian-vault")
obsidian_added = 0
obsidian_skipped = 0

# Index categories: 10-Projects, 20-Areas, 30-Resources, 00-Inbox
# Skip: Daily Notes, Tasks, .git, attachments
skip_dirs = {".git", "attachments", "Daily Notes", "Tasks", "scripts"}

for md_file in vault_dir.rglob("*.md"):
    rel = md_file.relative_to(vault_dir)
    parts = rel.parts
    
    # Skip certain directories
    if any(s in parts for s in skip_dirs):
        continue
    if md_file.name in ("index.md", "Home.md", "log.md"):
        continue
    
    # Determine category from PARA structure
    category = parts[0] if parts else "uncategorized"
    title = md_file.stem
    tldr = get_tldr(md_file)
    
    if tldr:
        room = f"obsidian-{category[:20]}"
        if add_index("research", room, title, tldr, f"obsidian/{rel}"):
            print(f"  ✅ {category}/{title[:40]}")
            obsidian_added += 1
        else:
            obsidian_skipped += 1

print(f"\nObsidian: {obsidian_added} indexed, {obsidian_skipped} skipped (duplicates)")
print(f"\n{'='*50}")
print(f"Phase 4 TOTAL: {added + obsidian_added} pages indexed")
print(f"{'='*50}")
