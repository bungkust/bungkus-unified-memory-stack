#!/usr/bin/env python3
"""Phase 1: Backup everything before migration."""
import os, sys, json, shutil
from datetime import datetime

# Use venv Python
sys.path.insert(0, os.path.expanduser("~/.hermes/mempalace-venv/lib/python3.12/site-packages"))
os.environ["MEMPALACE_PALACE"] = "/root/.mempalace/palace"

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_dir = os.path.expanduser(f"~/.hermes/backups/migration-{timestamp}")
os.makedirs(backup_dir, exist_ok=True)

print(f"📁 Backup dir: {backup_dir}")

# Import MemPalace tools
from mempalace.mcp_server import (
    tool_status, tool_search, tool_kg_query, tool_diary_read
)

# 1. Get all data via search
status = tool_status()
print(f"📊 MemPalace: {status['total_drawers']} drawers, {len(status['wings'])} wings")

broad_queries = [
    "user", "profile", "preferences", "kulino", "hermes", "agent",
    "system", "provider", "tools", "entities", "para", "decisions",
    "test", "diary", "inbox", "telegram", "discord", "skills",
    "patterns", "booth", "threads", "browserstack", "future",
    "resources", "testing", "self-test", "setup"
]

all_results = []
seen_texts = set()
for q in broad_queries:
    results = tool_search(q, limit=10)
    if "results" in results:
        for r in results["results"]:
            if r["text"] not in seen_texts:
                seen_texts.add(r["text"])
                all_results.append(r)

print(f"📦 Exported {len(all_results)} unique drawer contents")

# 2. Export KG
kg_export = {}
for entity_name in ["kulinobot", "mempalace", "persib", "testproject", "bungkustools", "onyx"]:
    facts = tool_kg_query(entity_name)
    if facts:
        kg_export[entity_name] = facts
print(f"🧠 Exported KG: {len(kg_export)} entities")

# 3. Export diary
diary = tool_diary_read("kulino-bot", last_n=50)

# 4. Save full MemPalace export
mempalace_export = {
    "status": status,
    "drawers": all_results,
    "kg": kg_export,
    "diary": diary,
    "exported_at": timestamp
}
with open(f"{backup_dir}/mempalace-full-export.json", "w") as f:
    json.dump(mempalace_export, f, indent=2, ensure_ascii=False)
print(f"✅ MemPalace full export saved")

# 5. Copy Light Memory
light_mem_src = os.path.expanduser("~/.hermes/memory")
light_mem_dst = f"{backup_dir}/light-memory-original"
if os.path.exists(light_mem_src):
    shutil.copytree(light_mem_src, light_mem_dst, dirs_exist_ok=True)
    file_count = sum(len(files) for _, _, files in os.walk(light_mem_dst))
    print(f"✅ Light Memory backup: {file_count} files")

# 6. Git status check
brain_status = os.popen("cd /root/brain && git status --short 2>&1").read().strip()
obsidian_status = os.popen("cd /root/obsidian-vault && git status --short 2>&1").read().strip()
with open(f"{backup_dir}/git-status.txt", "w") as f:
    f.write(f"=== Brain ===\n{brain_status or 'clean'}\n\n=== Obsidian ===\n{obsidian_status or 'clean'}\n")
print(f"📝 Brain: {'clean' if not brain_status else f'{len(brain_status.splitlines())} changes'}")
print(f"📝 Obsidian: {'clean' if not obsidian_status else f'{len(obsidian_status.splitlines())} changes'}")

# 7. Create fallback JSON (live location)
kg_triples = []
for entity, data in kg_export.items():
    if isinstance(data, dict) and "triples" in data:
        kg_triples.extend(data["triples"])

fallback_data = {
    "drawers": all_results,
    "kg_triples": kg_triples,
    "diary": diary.get("entries", []) if isinstance(diary, dict) else [],
    "metadata": {
        "created": timestamp,
        "source": "migration-backup",
        "total_drawers": len(all_results)
    }
}

# Save to backup
with open(f"{backup_dir}/mempalace-fallback.json", "w") as f:
    json.dump(fallback_data, f, indent=2, ensure_ascii=False)

# Save to live location
fallback_live = os.path.expanduser("~/.hermes/memory/mempalace-fallback.json")
os.makedirs(os.path.dirname(fallback_live), exist_ok=True)
with open(fallback_live, "w") as f:
    json.dump(fallback_data, f, indent=2, ensure_ascii=False)

print(f"✅ Fallback JSON: {len(all_results)} drawers, {len(kg_triples)} triples")

print(f"\n{'='*50}")
print(f"📋 BACKUP SUMMARY")
print(f"{'='*50}")
for item in os.listdir(backup_dir):
    path = f"{backup_dir}/{item}"
    if os.path.isfile(path):
        size = os.path.getsize(path)
        print(f"  📄 {item} ({size:,} bytes)")
    else:
        count = sum(len(files) for _, _, files in os.walk(path))
        print(f"  📁 {item}/ ({count} files)")
print(f"\n✅ Phase 1 COMPLETE — backup at {backup_dir}")
