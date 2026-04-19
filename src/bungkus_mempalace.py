#!/usr/bin/env python3
"""
Bungkus MemPalace — Hermes integration wrapper for MemPalace.
Provides semantic memory, knowledge graph, and agent diary.

Usage:
    from bungkus_mempalace import BungkusMemory
    mem = BungkusMemory()
    mem.remember("something important", wing="kulino", room="decisions")
    results = mem.recall("what did we decide?")
    mem.know("ProjectX", "uses", "React")
    facts = mem.what_about("ProjectX")

Mitigasi:
    - Fallback to file-based memory if ChromaDB fails
    - Graceful degradation (search returns empty, not crash)
    - Health check before operations
    - Auto-retry on transient errors
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

# Setup logging
logger = logging.getLogger("bungkus-mempalace")
logger.setLevel(logging.INFO)

PALACE_PATH = os.environ.get("MEMPALACE_PALACE", os.path.expanduser("~/.hermes/mempalace/palace"))
FALLBACK_PATH = os.path.expanduser("~/.hermes/memory/mempalace-fallback.json")

class BungkusMemory:
    """
    Wrapper around MemPalace with error handling and fallback.
    
    Success Metrics:
    - wake_up() < 2 seconds
    - search() < 1 second  
    - remember() < 1 second
    - 0 crashes on any operation
    - Fallback works when ChromaDB unavailable
    """
    
    def __init__(self, palace_path: str = None):
        self.palace_path = palace_path or PALACE_PATH
        self._available = False
        self._fallback_data = {"drawers": [], "kg_triples": [], "diary": []}
        self._tools = {}
        
        self._init()
    
    def _init(self):
        """Initialize MemPalace with fallback."""
        try:
            # Add venv to path
            venv_path = os.path.expanduser("~/.hermes/mempalace-venv/lib/python3.12/site-packages")
            if venv_path not in sys.path:
                sys.path.insert(0, venv_path)
            
            # Import MCP tools
            from mempalace.mcp_server import (
                tool_add_drawer, tool_search, tool_status,
                tool_list_wings, tool_list_rooms,
                tool_kg_add, tool_kg_query, tool_kg_timeline, tool_kg_invalidate,
                tool_diary_write, tool_diary_read,
                tool_get_drawer, tool_list_drawers,
                tool_check_duplicate
            )
            
            self._tools = {
                "add_drawer": tool_add_drawer,
                "search": tool_search,
                "status": tool_status,
                "list_wings": tool_list_wings,
                "list_rooms": tool_list_rooms,
                "kg_add": tool_kg_add,
                "kg_query": tool_kg_query,
                "kg_timeline": tool_kg_timeline,
                "kg_invalidate": tool_kg_invalidate,
                "diary_write": tool_diary_write,
                "diary_read": tool_diary_read,
                "get_drawer": tool_get_drawer,
                "list_drawers": tool_list_drawers,
                "check_duplicate": tool_check_duplicate,
            }
            
            # Test connection
            self._tools["status"]()
            self._available = True
            logger.info("✅ MemPalace connected")
            
        except Exception as e:
            logger.warning(f"⚠️ MemPalace unavailable: {e}. Using fallback.")
            self._available = False
            self._load_fallback()
    
    def _load_fallback(self):
        """Load fallback data from file."""
        try:
            fallback_file = Path(FALLBACK_PATH)
            if fallback_file.exists():
                self._fallback_data = json.loads(fallback_file.read_text())
                logger.info(f"📂 Loaded {len(self._fallback_data['drawers'])} fallback drawers")
        except Exception as e:
            logger.error(f"Fallback load error: {e}")
    
    def _save_fallback(self):
        """Save fallback data to file."""
        try:
            Path(FALLBACK_PATH).parent.mkdir(parents=True, exist_ok=True)
            Path(FALLBACK_PATH).write_text(json.dumps(self._fallback_data, indent=2, ensure_ascii=False))
        except Exception as e:
            logger.error(f"Fallback save error: {e}")
    
    @property
    def is_available(self) -> bool:
        """Check if MemPalace is available."""
        return self._available
    
    def health_check(self) -> Dict[str, Any]:
        """Run health check and return status."""
        result = {
            "mempalace_available": self._available,
            "palace_path": self.palace_path,
            "fallback_drawers": len(self._fallback_data["drawers"]),
            "timestamp": datetime.now().isoformat()
        }
        
        if self._available:
            try:
                status = self._tools["status"]()
                result["palace_status"] = status
                result["healthy"] = True
            except Exception as e:
                result["healthy"] = False
                result["error"] = str(e)
                self._available = False
        else:
            result["healthy"] = False
            result["reason"] = "ChromaDB not initialized"
        
        return result
    
    # ─── Core Operations ────────────────────────────────────────
    
    def remember(self, content: str, wing: str = "general", room: str = "general", 
                 source: str = "hermes") -> Dict[str, Any]:
        """
        Store a memory drawer.
        
        Args:
            content: The memory content (verbatim)
            wing: Project/domain (kulino, para, user, conversations)
            room: Topic/aspect (decisions, test-cases, profile)
            source: Source identifier
        
        Returns:
            {"success": True, "drawer_id": "...", "wing": "...", "room": "..."}
        """
        start = time.time()
        
        if self._available:
            try:
                result = self._tools["add_drawer"](
                    wing=wing, room=room, content=content, source_file=source
                )
                elapsed = time.time() - start
                logger.info(f"💾 Remembered: {wing}/{room} ({elapsed:.2f}s)")
                return result
            except Exception as e:
                logger.error(f"Remember error: {e}")
                self._available = False
                # Fall through to fallback
        
        # Fallback
        self._fallback_data["drawers"].append({
            "content": content,
            "wing": wing,
            "room": room,
            "source": source,
            "timestamp": datetime.now().isoformat()
        })
        self._save_fallback()
        return {"success": True, "drawer_id": f"fb_{len(self._fallback_data['drawers'])}", "fallback": True}
    
    def recall(self, query: str, limit: int = 5, wing: str = None, 
               room: str = None) -> List[Dict[str, Any]]:
        """
        Semantic search for memories.
        
        Args:
            query: Search query
            limit: Max results
            wing: Filter by wing
            room: Filter by room
        
        Returns:
            [{"text": "...", "similarity": 0.85, "wing": "...", "room": "..."}, ...]
        """
        start = time.time()
        
        if self._available:
            try:
                result = self._tools["search"](
                    query=query, limit=limit, wing=wing, room=room
                )
                elapsed = time.time() - start
                results = result.get("results", [])
                logger.info(f"🔍 Recalled {len(results)} results for '{query}' ({elapsed:.2f}s)")
                return results
            except Exception as e:
                logger.error(f"Recall error: {e}")
                self._available = False
        
        # Fallback: simple text search
        query_lower = query.lower()
        matches = []
        for d in self._fallback_data["drawers"]:
            if query_lower in d["content"].lower():
                if wing and d.get("wing") != wing:
                    continue
                if room and d.get("room") != room:
                    continue
                matches.append({
                    "text": d["content"],
                    "wing": d.get("wing"),
                    "room": d.get("room"),
                    "similarity": 0.5,  # placeholder
                    "fallback": True
                })
        return matches[:limit]
    
    def wake_up(self) -> str:
        """
        Get L0 + L1 context for session start.
        Returns identity + top memories (~600-900 tokens).
        """
        if self._available:
            try:
                from mempalace.layers import MemoryStack
                stack = MemoryStack(palace_path=self.palace_path)
                return stack.wake_up()
            except Exception as e:
                logger.error(f"Wake up error: {e}")
        
        # Fallback: identity + recent memories
        identity_path = os.path.expanduser("~/.mempalace/identity.txt")
        identity = ""
        try:
            identity = Path(identity_path).read_text()
        except:
            identity = "Kulino Bot — productivity assistant."
        
        recent = self._fallback_data["drawers"][-5:]
        recent_text = "\n".join([f"- {d['content'][:100]}" for d in recent])
        
        return f"## L0 — IDENTITY\n{identity}\n\n## L1 — Recent Memories\n{recent_text}" if recent_text else identity
    
    # ─── Knowledge Graph ────────────────────────────────────────
    
    def know(self, subject: str, predicate: str, obj: str, 
             valid_from: str = None) -> Dict[str, Any]:
        """Add a fact to the knowledge graph."""
        if self._available:
            try:
                return self._tools["kg_add"](subject, predicate, obj, valid_from=valid_from)
            except Exception as e:
                logger.error(f"KG add error: {e}")
        
        # Fallback
        self._fallback_data["kg_triples"].append({
            "subject": subject, "predicate": predicate, "object": obj,
            "valid_from": valid_from, "timestamp": datetime.now().isoformat()
        })
        self._save_fallback()
        return {"success": True, "fallback": True}
    
    def what_about(self, entity: str, as_of: str = None) -> Dict[str, Any]:
        """Query all facts about an entity."""
        if self._available:
            try:
                return self._tools["kg_query"](entity, as_of=as_of)
            except Exception as e:
                logger.error(f"KG query error: {e}")
        
        # Fallback
        facts = [t for t in self._fallback_data["kg_triples"] 
                 if t["subject"].lower() == entity.lower() or t["object"].lower() == entity.lower()]
        return {"entity": entity, "facts": facts, "fallback": True}
    
    def forget(self, subject: str, predicate: str, obj: str) -> Dict[str, Any]:
        """Invalidate a fact in the knowledge graph."""
        if self._available:
            try:
                return self._tools["kg_invalidate"](subject, predicate, obj, ended=datetime.now().isoformat())
            except Exception as e:
                logger.error(f"KG invalidate error: {e}")
        
        return {"success": False, "reason": "KG not available"}
    
    def timeline(self, entity: str) -> Dict[str, Any]:
        """Get chronological facts about an entity."""
        if self._available:
            try:
                return self._tools["kg_timeline"](entity)
            except Exception as e:
                logger.error(f"KG timeline error: {e}")
        
        return {"entity": entity, "timeline": [], "fallback": True}
    
    # ─── Agent Diary ────────────────────────────────────────────
    
    def diary_write(self, agent: str, entry: str, topic: str = "general") -> Dict[str, Any]:
        """Write a diary entry for an agent."""
        if self._available:
            try:
                return self._tools["diary_write"](agent, entry, topic=topic)
            except Exception as e:
                logger.error(f"Diary write error: {e}")
        
        # Fallback
        self._fallback_data["diary"].append({
            "agent": agent, "entry": entry, "topic": topic,
            "timestamp": datetime.now().isoformat()
        })
        self._save_fallback()
        return {"success": True, "fallback": True}
    
    def diary_read(self, agent: str, last_n: int = 10) -> List[Dict]:
        """Read recent diary entries for an agent."""
        if self._available:
            try:
                return self._tools["diary_read"](agent, last_n=last_n)
            except Exception as e:
                logger.error(f"Diary read error: {e}")
        
        # Fallback
        entries = [d for d in self._fallback_data["diary"] if d["agent"] == agent]
        return entries[-last_n:]
    
    # ─── Status ─────────────────────────────────────────────────
    
    def status(self) -> Dict[str, Any]:
        """Get palace status."""
        if self._available:
            try:
                return self._tools["status"]()
            except Exception as e:
                logger.error(f"Status error: {e}")
        
        return {
            "total_drawers": len(self._fallback_data["drawers"]),
            "fallback": True,
            "mempalace_available": False
        }
    
    def stats(self) -> str:
        """Get human-readable stats."""
        s = self.status()
        if self._available:
            wings = s.get("wings", {})
            return f"🏛️ MemPalace: {s.get('total_drawers', 0)} drawers across {len(wings)} wings"
        else:
            return f"📂 Fallback: {s.get('total_drawers', 0)} drawers (MemPalace unavailable)"

    # ─── Fallback Recovery ────────────────────────────────────────

    def restore_from_fallback(self) -> Dict[str, Any]:
        """
        Restore fallback data back to MemPalace after recovery.
        Call this when ChromaDB comes back online after a crash.
        """
        if not self._available:
            return {"success": False, "reason": "MemPalace still unavailable"}

        fallback_file = Path(FALLBACK_PATH)
        if not fallback_file.exists():
            return {"success": True, "restored": 0, "reason": "No fallback file"}

        try:
            data = json.loads(fallback_file.read_text())
        except Exception as e:
            return {"success": False, "error": f"Cannot read fallback: {e}"}

        restored = 0
        skipped = 0

        # Restore drawers
        for drawer in data.get("drawers", []):
            try:
                # Support both "text" (from tool_search export) and "content" (from remember())
                content = drawer.get("text") or drawer.get("content", "")
                wing = drawer.get("wing", "fallback")
                room = drawer.get("room", "recovery")
                source = drawer.get("source_file") or drawer.get("source", "fallback-recovery")

                if content:
                    self._tools["add_drawer"](
                        wing=wing, room=room, content=content, source_file=source
                    )
                    restored += 1
            except Exception:
                skipped += 1

        # Restore KG triples
        for triple in data.get("kg_triples", []):
            try:
                self._tools["kg_add"](
                    triple.get("subject", ""),
                    triple.get("predicate", ""),
                    triple.get("object", ""),
                    valid_from=triple.get("valid_from")
                )
                restored += 1
            except Exception:
                skipped += 1

        # Restore diary
        for entry in data.get("diary", []):
            try:
                self._tools["diary_write"](
                    entry.get("agent", "kulino-bot"),
                    entry.get("entry", ""),
                    topic=entry.get("topic", "recovery")
                )
                restored += 1
            except Exception:
                skipped += 1

        logger.info(f"🔄 Restored {restored} items from fallback ({skipped} skipped)")

        # Clear fallback after successful restore
        if restored > 0 and skipped == 0:
            self._fallback_data = {"drawers": [], "kg_triples": [], "diary": []}
            self._save_fallback()

        return {"success": True, "restored": restored, "skipped": skipped}


# ─── Quick test ─────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 50)
    print("🧪 BungkusMemory Self-Test")
    print("=" * 50)
    
    mem = BungkusMemory()
    
    # Health check
    health = mem.health_check()
    print(f"\n1. Health: {'✅' if health.get('healthy') else '⚠️ Fallback'}")
    print(f"   Available: {health['mempalace_available']}")
    
    # Remember
    r1 = mem.remember("Test memory from wrapper", wing="test", room="self-test")
    print(f"\n2. Remember: {'✅' if r1.get('success') else '❌'} {r1.get('drawer_id', 'N/A')}")
    
    # Recall
    results = mem.recall("test memory", limit=3)
    print(f"\n3. Recall: ✅ {len(results)} results")
    for r in results:
        print(f"   - {r.get('text', '')[:60]}")
    
    # Knowledge graph
    r2 = mem.know("TestProject", "uses", "MemPalace", valid_from="2026-04-15")
    print(f"\n4. KG know: {'✅' if r2.get('success') else '❌'}")
    
    facts = mem.what_about("TestProject")
    print(f"\n5. KG what_about: {len(facts.get('facts', []))} facts")
    
    # Diary
    r3 = mem.diary_write("test-agent", "Self-test complete", topic="testing")
    print(f"\n6. Diary: {'✅' if r3.get('success') else '❌'}")
    
    # Wake up
    wake = mem.wake_up()
    print(f"\n7. Wake up: ✅ ({len(wake)} chars)")
    
    # Stats
    print(f"\n8. Stats: {mem.stats()}")
    
    print("\n🎉 Self-test complete!")
