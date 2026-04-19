#!/usr/bin/env python3
"""Phase 2: Migrate Light Memory → MemPalace."""
import os, sys, json
from datetime import datetime

sys.path.insert(0, os.path.expanduser("~/.hermes/mempalace-venv/lib/python3.12/site-packages"))
os.environ["MEMPALACE_PALACE"] = "/root/.mempalace/palace"

from mempalace.mcp_server import (
    tool_add_drawer, tool_kg_add, tool_kg_query, tool_search
)

def add(wing, room, content, source="light-memory-migration"):
    """Add drawer with duplicate check."""
    # Quick duplicate check
    existing = tool_search(content[:80], limit=3)
    if "results" in existing:
        for r in existing["results"]:
            if r.get("similarity", 0) > 0.95:
                print(f"  ⏭️  SKIP (duplicate): {wing}/{room} — {content[:50]}...")
                return False
    tool_add_drawer(wing=wing, room=room, content=content, source_file=source)
    print(f"  ✅ Added: {wing}/{room} — {content[:60]}...")
    return True

added = 0
print("=" * 60)
print("PHASE 2: Migrate Light Memory → MemPalace")
print("=" * 60)

# ─── USER PROFILE ───
print("\n📂 user/profile")
add("user", "profile", "Bot utama: Kulino Bot (kusbot), persona helpful. User orang Jogja. WAJIB 'aku/kamu', JANGAN 'gw/lo'. Ramah khas Jawa, sopan tapi santai.")
add("user", "profile", "User product-minded, pakai framework JTBD/BMC/PMF. VPS bukan milik user sendiri — bantuin orang lain. Badminton GOR DS.")
add("user", "profile", "User punya anak: Kiano, lahir 27 Agustus 2019. Cash Flow dan Tumbuh Kembang di Kulino Family workspace Notion.")
add("user", "profile", "User prefer SHORT output, hemat token. Caveman 'lite' mode. Prefer Obsidian.")

# ─── USER PREFERENCES ───
print("\n📂 user/preferences")
add("user", "preferences", "WAJIB 'aku/kamu', JANGAN 'gw/lo'. WAJIB clarify ambigu sebelum eksekusi. Jangan asumsi.")
add("user", "preferences", "Struk belanja format: breakdown per item — Nama+Qty(title), Harga Satuan(Catatan), Total(Jumlah), Kategori, Metode Bayar, Tanggal. Jangan cuma total doang.")
add("user", "preferences", "QA reports: structured format — Section name, Steps to Reproduce, Expected Result, Actual Result. Notion table columns. Pages categorized by user type (Parent/Child/Settings).")
add("user", "preferences", "User prefer text reports sederhana, bukan dashboard. Testing pakai real data (backup files), bukan empty-state.")

# ─── USER ENTITIES ───
print("\n📂 user/entities")
add("user", "entities", "Notion workspace: PARA format. Inbox page ID di Notion. Auto-capture dari Discord channel #task-and-note.")
add("user", "entities", "Cash Flow DB ID di Notion. Title='Deskripsi' (item name only, NO qty/price). WAJIB query schema dulu sebelum create.")
add("user", "entities", "Cash Flow DB format: Deskripsi, Qty(number), Harga Satuan(number), Jumlah(=Qty×Satuan), Tempat Beli(text), Kategori, Metode Bayar, Tanggal, Tipe. Catatan for extra notes only.")

# KG entries for entities
tool_kg_add("user", "has_child", "kiano")
tool_kg_add("kiano", "born", "2019-08-27")
tool_kg_add("user", "uses_platform", "notion")
tool_kg_add("user", "has_vps", "sumopod")
tool_kg_add("user", "plays_badminton_at", "gor-ds")
print("  ✅ KG: 5 triples added")

# ─── AGENT TOOLS ───
print("\n📂 hermes/tools")
add("hermes", "tools", "Provider fallback: Nous Free (mimo) → OpenRouter (gemma-3 free). Manual switch: /model --provider <provider>.")
add("hermes", "tools", "Gateway issue: sering stop setelah 1-3 menit. Monitor script + cron every 5 min. Backups di /root/.hermes/backups/. WAJIB izin user sebelum restart!")
add("hermes", "tools", "Alert destination: Discord ID 1492370557927166053 (#alert). SEMUA cron jobs → channel ini kecuali diminta lain.")
add("hermes", "tools", "Gold reports: include harga Antam, buyback, simulasi dengan 0.45% tax. Mention @bungkust dan @lira.")
add("hermes", "tools", "Kulino Booth: Android app (React+Capacitor) v1.7.7. Payment: Mayar Dynamic QRCode. Fee: 2.2% (1.5% + 0.7% QRIS). Sandbox: web.mayar.club.")
add("hermes", "tools", "Social media: @kustiarnow (personal, Threads) & @bungkust_ (Kulino Booth B2B). JANGAN ketuker konsep! Repliz API untuk posting.")

# ─── AGENT PATTERNS ───
print("\n📂 agent/patterns")
add("agent", "patterns", "Core principles: (1) Kerjakan dulu kalau info cukup, (2) Jangan basa-basi, (3) Ingat konteks, (4) Proaktif. WAJIB clarify ambigu.")
add("agent", "patterns", "Research style: deep dive → vault → user review → decide. Jangan langsung eksekusi. Konten dari real experience only.")

# ─── AGENT SKILLS/CONFIG ───
print("\n📂 hermes/system")
add("hermes", "system", "Cron: 7 jobs. Default alert ch: Discord 1492370557927166053 (#alert). COST TRACKING: cost-logger.py /root/.hermes/scripts/cost-logger.py.")
add("hermes", "system", "Play Store: mobile viewport 390×844 @3x, JANGAN desktop. LOCALE: id-ID INVALID → use 'id'. App Name 30char, Short Desc 80char.")
add("hermes", "system", "GMaps scraper: /root/google-maps-scraper/gmaps_scraper.py. Airtable: QA=appX0L86LjtAIcLns, GScrapy=apprHyWxJzDo6D8w9.")
add("hermes", "system", "StarHabit: localhost:5173, PIN=5555 (Kiano). Play Store listing v2.0 finalized 18 Apr en-US+id. Feature graphic typo 'rack'→'Track'.")
add("hermes", "system", "Threads @kustiarnow: food list = Name ⭐reviews 📍address ONLY. Viral post → 500 email (blast after PS approve).")
add("hermes", "system", "RULES: (1) konten dari real experience only. (2) Multi-part: WAJIB threaded vs non-threaded + pro/con. (3) git pull DULU sebelum kerja.")

# KG entries for tools
tool_kg_add("kulinobot", "uses", "mempalace")
tool_kg_add("kulinobot", "monitors", "gateway")
tool_kg_add("user", "owns_project", "kulino-booth")
tool_kg_add("user", "owns_project", "starhabit")
print("  ✅ KG: 4 more triples added")

print(f"\n{'='*60}")
print(f"✅ Phase 2 COMPLETE")
print(f"{'='*60}")
