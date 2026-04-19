# 🧠 Bungkus Unified Memory Stack

> Satu memory system buat AI agent. Gak perlu ribet cek 3 tempat berbeda.

**Problem:** AI agents punya banyak memory systems yang overlap — vector DB, file-based, wiki, KG. Pusing mau pake yang mana, data tersebar, token bengkak.

**Solution:** Satu source of truth (MemPalace) + hybrid search + fallback recovery + auto-indexing wiki.

---

## 📊 Before vs After

| Metric | Old (multi-store) | New (unified) | Delta |
|---|---|---|---|
| **Stores to check** | 2-3 per query | 1 | **-67%** |
| **Tokens per query** | ~600 | ~125 | **-79%** |
| **Tokens per session** | ~6,550 | ~2,533 | **-61%** |
| **Latency (easy)** | ~0.8s | **0.35s** | **-56%** |
| **Data loss risk** | High (3 stores drift) | Low (1 store + fallback) | ✅ |

---

## 🏗️ Architecture

```
                    ┌─────────────────────┐
                    │   USER INPUT        │
                    └─────────┬───────────┘
                              │
                    ┌─────────▼───────────┐
                    │   STORE?            │
                    └─────────┬───────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
        ┌──────────┐   ┌──────────┐   ┌────────────┐
        │ PROFILE  │   │ FACTS &  │   │ HUMAN-     │
        │ CONFIG   │   │ CONVO &  │   │ READABLE   │
        │ PREFS    │   │ RESEARCH │   │ DOCS       │
        └────┬─────┘   └────┬─────┘   └─────┬──────┘
             │              │               │
             ▼              ▼               ▼
        ┌─────────────────────────┐   ┌──────────────┐
        │      MEMPALACE          │   │ Brain +      │
        │   (satu2nya store)      │   │ Obsidian     │
        │                         │   │ (git repos)  │
        │  ┌───────────────────┐  │   └──────┬───────┘
        │  │ ChromaDB (vector) │  │          │
        │  │ KG (temporal)     │  │   ◄──────┘
        │  │ Diary (events)    │  │   auto-index
        │  └───────────────────┘  │   ke MemPalace
        │                         │
        │  ┌───────────────────┐  │
        │  │ JSON Fallback     │  │
        │  │ (kalau crash)     │  │
        │  └───────────────────┘  │
        └─────────────────────────┘
                      │
                      ▼
              ┌───────────────┐
              │ BungkusSearch │
              │ Hybrid:       │
              │ Basic → MQE   │
              └───────────────┘
```

---

## 🧩 Components

| Component | Role | File |
|---|---|---|
| **MemPalace** | Core memory store (vector + KG + diary) | [bungkus_mempalace.py](src/bungkus_mempalace.py) |
| **BungkusSearch** | Hybrid search: basic → MQE (auto-escalation) | [bungkus_search.py](src/bungkus_search.py) |
| **Wiki Ingest Patch** | Auto-index wiki pages to MemPalace | [wiki_ingest_patch.py](src/wiki_ingest_patch.py) |
| **Migration Script** | One-click migration from multi-store | [migrate.py](scripts/migrate.py) |
| **Flow Tests** | 22-test suite for verification | [test-flow.py](scripts/test-flow.py) |

---

## 🔧 Rules

```
RULE 1 — STORAGE
  Everything → MemPalace
  Except human docs → Brain/Obsidian (git)

RULE 2 — WIKI INGEST
  Create page di Brain/Obsidian
    → auto-add drawer ke MemPalace

RULE 3 — FALLBACK
  ChromaDB up   → normal path
  ChromaDB down  → write to JSON
  ChromaDB back  → auto-flush JSON → ChromaDB

RULE 4 — SEARCH
  Always BungkusSearch (hybrid)
  Basic first (0.35s), MQE if low confidence (1.44s)

RULE 5 — USER PROFILE
  MemPalace wing=user ONLY
  Old file-based memory → archived
```

---

## 📈 Token Consumption Analysis

### How tokens are consumed per query:

```
OLD APPROACH (multi-store):
├─ Load system memory:        550 tokens (always)
├─ Load Light Memory file:    200-400 tokens (grep)
├─ Search MemPalace:          200-300 tokens (semantic)
├─ Merge + dedup:             100-200 tokens (processing)
└─ Total per query:           ~950-1250 tokens

NEW APPROACH (unified):
├─ Load system memory:        543 tokens (always)
├─ One BungkusSearch:         125 tokens (semantic)
└─ Total per query:           ~668 tokens

SAVINGS: ~300-600 tokens/query (30-50%)
```

### Per session (10 queries):

```
OLD: 550 + (10 × 600)  = ~6,550 tokens/session
NEW: 543 + 740 + (10 × 125) = ~2,533 tokens/session

SAVINGS: ~4,000 tokens/session (61% reduction)
```

### Why:

| Old (multi-store) | New (unified) |
|---|---|
| Load 1-3 files per query | Zero files loaded |
| Grep untuk cari keyword | Semantic search (precise) |
| Search 2-3 stores | 1 store only |
| Merge results dari multiple sources | 1 result set |
| Filter duplicates | No duplicates |

---

## 🚀 Performance

| Operation | Latency |
|---|---|
| Wake-up (session start) | 0.01s |
| Basic search | 0.35s |
| MQE search (hard queries) | 1.44s |
| Hybrid (auto) | ~0.55s avg |
| Store fact | 0.37s |
| KG query | <0.01s |
| Diary write | 0.37s |

---

## 🔄 Hybrid Search (BungkusSearch)

```
Query masuk
    │
    ▼
Step 1: Basic search (1 ChromaDB call, 0.35s)
    │
    ├─ Top result sim >= 0.4 → Return (fast path, 80% queries)
    │
    └─ Top result sim < 0.4 → Step 2
                                  │
                                  ▼
                          Multi-Query Expansion + RRF
                          (8 parallel searches, 1.44s)
                                  │
                                  ├─ Original (weight 1.0)
                                  ├─ Keywords (weight 0.6×3)
                                  ├─ Variations (weight 0.7×2)
                                  ├─ Domain expansion (weight 0.5×2)
                                  │
                                  ▼
                          Weighted RRF merge → Return
```

**Key insight:** MQE uses dictionary-based expansion (NO LLM calls = 0 extra tokens). Pure latency trade-off, not token trade-off.

---

## 🛡️ Fallback Architecture

```
Normal:
  Bot → MemPalace (ChromaDB) → results

Crash:
  Bot → MemPalace (fail) → JSON fallback file → results
  
Recovery:
  Bot → MemPalace (back) → restore_from_fallback() → flush JSON → normal
```

**Fallback file:** `~/.hermes/memory/mempalace-fallback.json`
**Auto-created** on first migration, **auto-cleared** after successful restore.

---

## 📦 Migration

From 4 separate memory systems to 1:

```bash
# 1. Backup everything
python3 scripts/migrate.py --phase backup

# 2. Migrate data
python3 scripts/migrate.py --phase migrate

# 3. Clean test data
python3 scripts/migrate.py --phase clean

# 4. Index wiki pages
python3 scripts/migrate.py --phase index

# 5. Fix infrastructure
python3 scripts/migrate.py --phase fix

# 6. Verify
python3 scripts/migrate.py --phase verify
```

Or all at once:
```bash
python3 scripts/migrate.py --all
```

---

## 🧪 Testing

```bash
# Quick test (22 tests, ~18s)
python3 scripts/test-flow.py

# Hard test (stress + edge cases, ~30s)
python3 scripts/hard-flow-test.py

# Deep test (all flows, ~30s)
python3 scripts/deep-flow-test.py
```

**Test results:** 71/71 passed ✅

---

## 📁 Structure

```
~/.mempalace/
├── identity.txt                    # Bot identity
├── config.json
├── palace/                         # ChromaDB + KG
│   ├── chroma.sqlite3
│   ├── knowledge_graph.sqlite3
│   └── closets/

~/.hermes/memory/
├── _archived/                      # Old Light Memory (backup)
│   ├── user/
│   ├── agent/
│   └── openviking-concepts.md
├── mempalace-fallback.json         # Crash recovery
└── sessions/                       # Session logs
```

---

## 🎯 When to Use What

| Data Type | Store | Why |
|---|---|---|
| User profile/prefs | MemPalace (wing=user) | Semantic recall |
| Facts & conversations | MemPalace (any wing) | Core function |
| Research & analysis | MemPalace (wing=research) + Brain/Obsidian | Bot recall + human read |
| Config & IDs | MemPalace (wing=hermes) | Quick lookup |
| KG relationships | MemPalace (KG) | Temporal facts |
| Session logs | MemPalace (diary) | Agent memory |
| Human-readable docs | Brain (TLDR) + Obsidian (deep) | Manual reading |

---

## 🔗 Related

- [MemPalace](https://github.com/MemPalace/mempalace) — Core memory engine
- [Hermes Agent](https://github.com/joaompfp/hermes) — AI agent platform
- [Karpathy's LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — Wiki pattern inspiration

---

## 📝 License

MIT
