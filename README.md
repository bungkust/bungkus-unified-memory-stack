# 🧠 Bungkus Unified Memory Stack

> One memory system for AI agents. Stop checking 3 different places.

**Problem:** AI agents juggle multiple overlapping memory systems — vector DBs, file stores, knowledge graphs, wikis. Data scatters, tokens balloon, nothing stays in sync.

**Solution:** Single source of truth (MemPalace) + hybrid search + fallback recovery + auto-indexing wiki.

---

## 📊 Memory Systems Compared

| | Hermes Default | MemPalace (raw) | LLM Wiki | Vector DB (raw) | **Unified Stack** |
|---|---|---|---|---|---|
| **Storage** | System memory (2200 chars) | ChromaDB + KG | Markdown files | ChromaDB only | **MemPalace (vector+KG) + wiki index** |
| **Search** | Injected every turn (fixed) | Semantic (basic) | Grep / file read | Semantic (basic) | **Hybrid: basic → MQE auto-escalation** |
| **Tokens/query** | ~550 (always loaded) | ~200-300 | ~200-500 (file read) | ~200-300 | **~125 (semantic, precise)** |
| **Tokens/session (10q)** | ~5,500 | ~3,000 | ~4,000 | ~3,000 | **~2,533** |
| **Knowledge graph** | ❌ | ✅ | ❌ (wikilinks only) | ❌ | **✅ temporal KG** |
| **Fallback** | ❌ | ❌ | Git (manual) | ❌ | **✅ auto JSON + restore** |
| **Wiki indexing** | ❌ | ❌ | ✅ (own format) | ❌ | **✅ auto-index to vector DB** |
| **Deduplication** | ❌ | ❌ | Manual | ❌ | **Similarity threshold** |
| **Session persistence** | ❌ (resets) | ✅ diary | ❌ | ❌ | **✅ diary + session logs** |
| **Data loss risk** | High (char limit) | Medium (no backup) | Low (git) | Medium (no backup) | **Low (fallback+archive)** |
| **Scalability** | Poor (2200 chars max) | Good | Medium (grep slow) | Good | **Good** |
| **Setup complexity** | Zero | Medium | Low | Low | **Medium (one-time migration)** |

---

## 🏗️ Architecture

```
                        ┌───────────────────┐
                        │    USER INPUT     │
                        └─────────┬─────────┘
                                  │
                    ┌─────────────▼─────────────┐
                    │       MEMORY ROUTER       │
                    │  (what type of data?)     │
                    └─────────────┬─────────────┘
                                  │
              ┌───────────────────┼───────────────────┐
              ▼                   ▼                   ▼
        ┌───────────┐     ┌───────────┐      ┌─────────────┐
        │  PROFILE  │     │  FACTS &  │      │  HUMAN-     │
        │  CONFIG   │     │  CONVO &  │      │  READABLE   │
        │  PREFS    │     │  RESEARCH │      │  DOCS       │
        └─────┬─────┘     └─────┬─────┘      └──────┬──────┘
              │                 │                    │
              ▼                 ▼                    ▼
        ┌──────────────────────────────┐    ┌──────────────┐
        │        MEMPALACE             │    │  Brain +     │
        │    (single source of truth)  │    │  Obsidian    │
        │                              │    │  (git repos) │
        │  ┌────────────────────────┐  │    └──────┬───────┘
        │  │ ChromaDB (vector)      │  │           │
        │  │ Knowledge Graph (temporal)│ │    ◄─────┘
        │  │ Diary (session logs)   │  │    auto-index
        │  └────────────────────────┘  │    on create
        │                              │
        │  ┌────────────────────────┐  │
        │  │ JSON Fallback          │  │
        │  │ (crash recovery)       │  │
        │  └────────────────────────┘  │
        └──────────────────────────────┘
                      │
                      ▼
            ┌───────────────────┐
            │   BungkusSearch   │
            │   Hybrid Mode:    │
            │   Basic → MQE     │
            └───────────────────┘
```

---

## 🔍 Deep Dive: What Each System Does

### Hermes Default Memory
- **What:** 2,200 character string injected into system prompt every turn
- **Pros:** Zero setup, always available, no dependencies
- **Cons:** Fixed size (hard limit), no search, no structure, no persistence across sessions, every character costs tokens whether relevant or not
- **Best for:** Tiny config snippets, bot identity

### MemPalace (standalone)
- **What:** ChromaDB vector store + temporal knowledge graph + agent diary
- **Pros:** Semantic search, KG with time-travel queries, diary for session continuity, 96.6% recall on benchmarks
- **Cons:** No fallback (ChromaDB crash = data loss), no wiki integration, basic search only (no query expansion), 0.558 avg similarity (mediocre)
- **Best for:** Core memory engine (as we use it)

### LLM Wiki (Karpathy pattern)
- **What:** Markdown files with YAML frontmatter, wikilinks, SCHEMA.md conventions
- **Pros:** Human-readable, git-backed, Obsidian-compatible, structured organization
- **Cons:** No semantic search (grep only), no KG (wikilinks are weak edges), manual maintenance, staleness without recompilation
- **Best for:** Reference documentation, knowledge that humans also read

### Raw Vector DB (ChromaDB standalone)
- **What:** Embedding-based similarity search over document chunks
- **Pros:** Fast, scalable, good recall
- **Cons:** No structure (flat chunks), no relationships, no temporal queries, no fallback, chunk fragmentation
- **Best for:** RAG pipelines, document search

### Unified Stack (this project)
- **What:** MemPalace as core + hybrid search + fallback + wiki auto-indexing
- **Pros:** All benefits of MemPalace + better search + crash recovery + wiki integration + 61% fewer tokens
- **Cons:** More complex setup (one-time migration), MemPalace dependency
- **Best for:** Production AI agent memory

---

## 🎯 Use Cases

### 1. AI Agent Long-Term Memory
Store conversations, decisions, and facts across sessions. Semantic search finds relevant context without loading entire history.

### 2. Knowledge Base with Search
Index wiki pages (Brain, Obsidian, Notion export) into vector DB. Bot can answer questions about your documentation without manual file reading.

### 3. Multi-Project Tracking
Different wings for different projects (kulino, hermes, research). Filtered search keeps results relevant.

### 4. Entity Relationship Tracking
Knowledge graph tracks who-what-when. "What do we know about X?" returns temporal facts.

### 5. Crash-Resilient Memory
Fallback JSON catches writes when ChromaDB is down. Auto-restores on recovery. No data loss.

---

## 📈 Token Consumption

### Per Query

| Step | Old (multi-store) | New (unified) |
|---|---|---|
| Load system memory | 550 tokens | 543 tokens |
| Load file-based memory | 200-400 tokens | 0 (not needed) |
| Search vector DB | 200-300 tokens | 125 tokens |
| Merge results | 100-200 tokens | 0 (single source) |
| **Total** | **~950-1250** | **~668** |

### Per Session (10 queries)

| | Old | New | Savings |
|---|---|---|---|
| System memory | 550 | 543 | -7 |
| Wake-up context | 0 | 740 | +740 |
| Per-query average | 600 | 125 | -475 |
| **Session total** | **~6,550** | **~2,533** | **-61%** |

### Why New Saves Tokens

| Old Approach | New Approach |
|---|---|
| Load 1-3 markdown files per query | Zero files loaded |
| Grep for keywords (imprecise, noisy) | Semantic search (precise) |
| Search 2-3 separate stores | 1 store only |
| Merge + deduplicate results | 1 result set, no dupes |
| Load irrelevant context | Only relevant chunks |

---

## ⚡ Hybrid Search (BungkusSearch)

```
Query received
      │
      ▼
Step 1: Basic search (1 ChromaDB call, ~0.35s)
      │
      ├─ Top result similarity >= 0.4 → Return ✅ (fast path, ~80% of queries)
      │
      └─ Top result similarity < 0.4 → Step 2
                                          │
                                          ▼
                                  Multi-Query Expansion + RRF
                                  (8 parallel searches, ~1.44s)
                                          │
                                          ├─ Original query (weight 1.0)
                                          ├─ Keyword extraction (weight 0.6 ×3)
                                          ├─ Phrase variations (weight 0.7 ×2)
                                          ├─ Domain expansion (weight 0.5 ×2)
                                          │
                                          ▼
                                  Weighted RRF merge → Return
```

**Key design decisions:**
- Expansion uses dictionary-based rules (NO LLM calls = 0 extra tokens)
- Trade-off is latency, not tokens
- Auto-escalation: 80% of queries use fast path (0.35s), only hard queries pay the 1.44s cost
- Average hybrid latency: ~0.55s

---

## 🛡️ Fallback & Recovery

```
Normal:     Bot → MemPalace (ChromaDB) → results
Crash:      Bot → MemPalace (fail) → JSON fallback → results
Recovery:   Bot → MemPalace (back) → restore_from_fallback() → flush JSON → normal
```

**Fallback file:** `~/.hermes/memory/mempalace-fallback.json`
**Auto-created** on first migration, **auto-cleared** after successful restore.

---

## 🚀 Performance

| Operation | Latency | Notes |
|---|---|---|
| Wake-up (session start) | 0.01s | Load identity + top memories |
| Basic search | 0.35s | 1 ChromaDB call |
| MQE search (hard queries) | 1.44s | 8 parallel calls + RRF |
| Hybrid (auto) | ~0.55s | Weighted average |
| Store fact | 0.37s | Embed + insert |
| KG query | <0.01s | SQLite lookup |
| Diary write | 0.37s | Embed + insert |

---

## 🔄 Migration

From 4 separate memory systems to 1:

```bash
# Full migration (all phases)
python3 scripts/migrate.py --all

# Or individual phases
python3 scripts/migrate.py --phase backup    # Phase 1: Backup everything
python3 scripts/migrate.py --phase migrate   # Phase 2: Migrate data
python3 scripts/migrate.py --phase index     # Phase 4: Index wiki pages
python3 scripts/migrate.py --phase verify    # Phase 6: Verify
```

---

## 🧪 Testing

```bash
# Flow tests (22 tests, ~18s)
python3 scripts/test-flow.py

# Hard tests (stress + edge cases, ~30s)
python3 scripts/hard-flow-test.py

# Deep tests (all flows, ~30s)
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
├── _archived/                      # Old file-based memory (backup)
│   ├── user/
│   ├── agent/
│   └── openviking-concepts.md
├── mempalace-fallback.json         # Crash recovery
└── sessions/                       # Session logs
```

---

## 🧩 Components

| File | Role |
|---|---|
| [bungkus_mempalace.py](src/bungkus_mempalace.py) | Enhanced MemPalace wrapper with fallback + restore |
| [bungkus_search.py](src/bungkus_search.py) | Hybrid search: basic → MQE auto-escalation |
| [wiki_ingest_patch.py](src/wiki_ingest_patch.py) | Auto-index wiki pages to MemPalace on create |
| [migrate.py](scripts/migrate.py) | One-click migration orchestrator |
| [deep-flow-test.py](scripts/deep-flow-test.py) | Comprehensive flow test suite |
| [hard-flow-test.py](scripts/hard-flow-test.py) | Stress test + edge cases |

---

## 🔗 Related Projects

- [MemPalace](https://github.com/MemPalace/mempalace) — Core memory engine (46.2k stars)
- [Hermes Agent](https://github.com/joaompfp/hermes) — AI agent platform
- [Hermes VS Code](https://github.com/joaompfp/hermes-vscode) — VS Code extension for Hermes
- [Karpathy's LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — Wiki pattern inspiration

---

## 📝 License

MIT
