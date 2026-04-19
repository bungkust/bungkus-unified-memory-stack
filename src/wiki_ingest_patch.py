"""
wiki_ingest_patch.py — Patch for wiki-ingest.py to auto-index to MemPalace.

Add this function to wiki-ingest.py and call it after page creation:

    index_to_mempalace(pages)

See README.md for full integration instructions.
"""
import os, sys

def index_to_mempalace(pages):
    """Index created pages to MemPalace for semantic search."""
    try:
        venv_path = os.path.expanduser("~/.hermes/mempalace-venv/lib/python3.12/site-packages")
        if venv_path not in sys.path:
            sys.path.insert(0, venv_path)
        os.environ.setdefault("MEMPALACE_PALACE", "/root/.mempalace/palace")

        from mempalace.mcp_server import tool_add_drawer, tool_search

        indexed = 0
        for page in pages:
            title = page.get("title", "")
            content = page.get("content", "")
            category = page.get("category", "notes")
            if not title:
                continue

            tldr = content[:300].replace("\n", " ").strip()
            room = f"brain-{category}"

            existing = tool_search(title[:50], limit=1)
            if "results" in existing:
                for r in existing["results"]:
                    if r.get("similarity", 0) > 0.90:
                        continue

            tool_add_drawer(
                wing="research", room=room,
                content=f"[{title}] {tldr}",
                source_file="wiki-ingest-auto"
            )
            indexed += 1

        if indexed:
            print(f"🧠 MemPalace: {indexed} page(s) indexed")
    except Exception as e:
        print(f"⚠️  MemPalace index skipped: {e}", file=sys.stderr)
