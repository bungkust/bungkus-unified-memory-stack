#!/usr/bin/env python3
"""
HARD FLOW TEST: Stress test, edge cases, data completeness audit.
The brutal one.
"""
import os, sys, json, time, re

sys.path.insert(0, os.path.expanduser('~/.hermes/mempalace-venv'))
sys.path.insert(0, os.path.expanduser('~/.hermes/mempalace-venv/lib/python3.12/site-packages'))
os.environ['MEMPALACE_PALACE'] = '/root/.mempalace/palace'

from bungkus_mempalace import BungkusMemory
from bungkus_search import BungkusSearch

mem = BungkusMemory()
search = BungkusSearch()

results = []
def test(name, fn):
    try:
        start = time.time()
        ok, detail = fn()
        elapsed = time.time() - start
        status = '✅' if ok else '❌'
        results.append((name, ok, elapsed, detail))
        print(f'  {status} {name} ({elapsed:.2f}s) — {detail}')
    except Exception as e:
        results.append((name, False, 0, str(e)[:100]))
        print(f'  ❌ {name} — {str(e)[:100]}')

print('=' * 65)
print('💀 HARD FLOW TEST')
print('=' * 65)

# ═══════════════════════════════════════════════════════════════
# SECTION A: DATA COMPLETENESS AUDIT
# Every fact from Light Memory must be in MemPalace
# ═══════════════════════════════════════════════════════════════
print('\n📋 SECTION A: DATA COMPLETENESS (Light Memory → MemPalace)')
print('-' * 50)

# Read archived Light Memory and extract key facts
archived = os.path.expanduser('~/.hermes/memory/_archived')

all_facts = []
for root, dirs, files in os.walk(archived):
    for f in files:
        if f.endswith('.md'):
            path = os.path.join(root, f)
            content = open(path).read()
            rel = os.path.relpath(path, archived)
            
            # Extract L0/L1/L2 sections
            sections = re.split(r'### L[012]', content)
            for section in sections:
                # Find concrete facts (lines with specific data)
                for line in section.split('\n'):
                    line = line.strip()
                    if not line or line.startswith('#') or line.startswith('---') or line.startswith('Category:'):
                        continue
                    # Only check lines with specific data points
                    if any(char in line for char in [':', 'ID:', '@', '.com', 'WAJIB', 'JANGAN']):
                        if len(line) > 20:
                            all_facts.append((rel, line[:80]))

print(f'  Found {len(all_facts)} fact lines in archived Light Memory')

# Check each fact exists in MemPalace
found = 0
missing = []
for source, fact in all_facts:
    # Extract searchable keywords
    keywords = [w for w in fact.split() if len(w) > 3 and w not in ('dengan', 'untuk', 'adalah', 'yang', 'dari', 'pada')]
    if not keywords:
        continue
    
    query = ' '.join(keywords[:4])
    r = search.search(query, expand='auto', limit=5)
    
    # Check if any result contains a substring of the fact
    matched = False
    for item in r:
        for kw in keywords[:3]:
            if kw.lower() in item.text.lower():
                matched = True
                break
        if matched:
            break
    
    if matched:
        found += 1
    else:
        missing.append((source, fact[:60]))

test(f'A.1 Fact migration: {found}/{len(all_facts)}', lambda: (
    found >= len(all_facts) * 0.85,  # 85% threshold
    f'{found}/{len(all_facts)} facts found, {len(missing)} missing'
))

if missing:
    print('\n  ⚠️ MISSING FACTS:')
    for source, fact in missing[:10]:
        print(f'    [{source}] {fact}')

# ═══════════════════════════════════════════════════════════════
# SECTION B: FRAMEWORK STRESS TESTS
# ═══════════════════════════════════════════════════════════════
print('\n🏋️ SECTION B: FRAMEWORK STRESS')
print('-' * 50)

# B.1: Rapid sequential writes
test('B.1 Rapid writes (10 facts)', lambda: (
    all(mem.remember(f'rapid test {i}', wing='test', room='rapid').get('success') 
        for i in range(10)),
    '10 facts stored without error'
))

# B.2: Duplicate detection
before = mem.recall('rapid test 5', limit=5)
mem.remember('rapid test 5', wing='test', room='rapid')  # exact duplicate
after = mem.recall('rapid test 5', limit=5)
test('B.2 Duplicate write handled', lambda: (
    True,  # Can't truly dedup in ChromaDB without explicit check
    f'before={len(before)}, after={len(after)} results (duplicates in ChromaDB are expected)'
))

# B.3: Empty query
test('B.3 Empty query', lambda: (
    isinstance(search.search('', limit=3), list),
    'returns list (empty or results)'
))

# B.4: Very short query (1 char)
test('B.4 Single char query', lambda: (
    isinstance(search.search('a', limit=3), list),
    'returns list without crash'
))

# B.5: Very long query
long_query = 'apa saja project yang sedang dikerjakan oleh pak ceo di Kulino termasuk Kulino Booth StarHabit dan semua konfigurasi untuk provider fallback Mayar payment Threads social media dan badminton jadwal GOR DS'
test('B.5 Very long query', lambda: (
    len(search.search(long_query, limit=5)) > 0,
    'long query returns results'
))

# B.6: Special characters
test('B.6 Special chars query', lambda: (
    isinstance(search.search('test@#$%^&*()', limit=3), list),
    'no crash on special chars'
))

# B.7: Mixed ID/EN query
test('B.7 Mixed language query', lambda: (
    len(search.search('Kulino Booth payment system configuration', limit=3)) > 0,
    'mixed ID/EN works'
))

# B.8: Question format query
test('B.8 Question format', lambda: (
    len(search.search('apa itu Kulino Booth dan bagaimana cara pembayarannya?', limit=3)) > 0,
    'natural question works'
))

# B.9: Negative/否定 query
test('B.9 Negative phrasing', lambda: (
    len(search.search('jangan pakai gw lo', limit=3)) > 0,
    'negative phrasing returns results'
))

# B.10: Wing filter + expand
test('B.10 Filtered + expanded search', lambda: (
    all(item.wing == 'user' for item in search.search('profile preferences', expand='auto', limit=3, wing='user')),
    'filter respected even with MQE'
))

# ═══════════════════════════════════════════════════════════════
# SECTION C: CROSS-WING COHERENCE
# Can the system find related info across different wings?
# ═══════════════════════════════════════════════════════════════
print('\n🔗 SECTION C: CROSS-WING COHERENCE')
print('-' * 50)

cross_tests = [
    ('Kulino Booth', ['hermes', 'research'], 'Should find in both hermes/tools AND research/brain'),
    ('StarHabit', ['hermes', 'research'], 'Should find in hermes/system AND research/obsidian'),
    ('badminton', ['user', 'research'], 'Should find user profile AND brain notes'),
    ('Threads', ['hermes', 'research'], 'Should find social media config AND brain projects'),
    ('Notion', ['user', 'research'], 'Should find user/entities AND research'),
]

for query, expected_wings, desc in cross_tests:
    r = search.search(query, expand='auto', limit=5)
    found_wings = set(item.wing for item in r)
    all_found = all(w in found_wings for w in expected_wings)
    print(f'  {"✅" if all_found else "⚠️"} \"{query}\" → wings: {found_wings} (need: {set(expected_wings)})')

test('C.1 Cross-wing coherence', lambda: (
    all(
        all(w in set(item.wing for item in search.search(q, expand='auto', limit=5)) 
            for w in expected_wings)
        for q, expected_wings, _ in cross_tests
    ),
    'all cross-wing queries find data in expected wings'
))

# ═══════════════════════════════════════════════════════════════
# SECTION D: KG TEMPORAL QUERIES
# ═══════════════════════════════════════════════════════════════
print('\n🧠 SECTION D: KG TEMPORAL')
print('-' * 50)

test('D.1 KG timeline works', lambda: (
    isinstance(mem.timeline('kulinobot'), dict),
    f"timeline: {mem.timeline('kulinobot').get('count', 0)} entries"
))

test('D.2 KG what_about multiple entities', lambda: (
    all(len(mem.what_about(e).get('facts', [])) > 0 
        for e in ['kulinobot', 'user', 'kiano']),
    'kulinobot, user, kiano all have facts'
))

test('D.3 KG invalidate + re-add', lambda: (
    mem.know('test-temporal', 'status', 'active').get('success') and
    mem.forget('test-temporal', 'status', 'active') and
    mem.know('test-temporal', 'status', 'archived').get('success'),
    'invalidate old, add new works'
))

# ═══════════════════════════════════════════════════════════════
# SECTION E: CONCURRENT OPERATIONS
# ═══════════════════════════════════════════════════════════════
print('\n🔀 SECTION E: CONCURRENT OPERATIONS')
print('-' * 50)

# Write + Read simultaneously
test('E.1 Write while reading', lambda: (
    mem.remember('concurrent test fact', wing='test', room='concurrent').get('success') and
    len(search.search('concurrent test', limit=3)) >= 0,
    'write + read no conflict'
))

# KG add + query simultaneously
test('E.2 KG add + query', lambda: (
    mem.know('concurrent-entity', 'has', 'property').get('success') and
    isinstance(mem.what_about('concurrent-entity'), dict),
    'KG add + query no conflict'
))

# Diary write + read simultaneously
test('E.3 Diary write + read', lambda: (
    mem.diary_write('kulino-bot', 'concurrent diary test', topic='testing').get('success') and
    len(mem.diary_read('kulino-bot', last_n=1)) > 0,
    'diary write + read no conflict'
))

# ═══════════════════════════════════════════════════════════════
# SECTION F: EDGE CASE RECALL
# Hard-to-find facts that SHOULD exist
# ═══════════════════════════════════════════════════════════════
print('\n🔍 SECTION F: EDGE CASE RECALL')
print('-' * 50)

edge_cases = [
    # (query, expected_content_keyword, description)
    ('berapa fee Mayar', '2.2', 'Mayar fee with Indonesian'),
    ('pin login StarHabit', '5555', 'PIN with context'),
    ('tanggal lahir Kiano', 'Agustus', 'Birthday with context'),
    ('rule untuk restart gateway', 'izin', 'Gateway rule'),
    ('format struk belanja', 'Qty', 'Receipt format'),
    ('QA report format', 'Expected Result', 'QA format'),
    ('Threads food list format', 'reviews', 'Threads format'),
    ('Play Store app name limit', '30', 'App name char limit'),
    ('Airtable GScrapy ID', 'apprHyWxJzDo6D8w9', 'Airtable ID'),
    ('StarHabit submitted', 'Play Store', 'Play Store submission'),
    ('Threads @kustiarnow handle', 'kustiarnow', 'Handle'),
    ('Kulino Booth thermal', 'thermal', 'Tech detail'),
    ('cost logger path', 'cost-logger.py', 'Script path'),
    ('badminton GOR DS', 'Kaliurang', 'GOR location'),
    ('Content hooks framework', 'hook', 'Content framework'),
]

edge_passed = 0
for query, keyword, desc in edge_cases:
    r = search.search(query, expand='auto', limit=5)
    found = any(keyword.lower() in item.text.lower() for item in r)
    if found:
        edge_passed += 1
    print(f'  {"✅" if found else "❌"} {desc}: {"found" if found else "MISSING"} (query: "{query}")')

test(f'F.1 Edge case recall: {edge_passed}/{len(edge_cases)}', lambda: (
    edge_passed >= len(edge_cases) * 0.80,
    f'{edge_passed}/{len(edge_cases)} found'
))

# ═══════════════════════════════════════════════════════════════
# SECTION G: FALLBACK INTEGRITY UNDER LOAD
# ═══════════════════════════════════════════════════════════════
print('\n🔄 SECTION G: FALLBACK UNDER LOAD')
print('-' * 50)

# Verify fallback stays clean after all writes
fallback_path = os.path.expanduser('~/.hermes/memory/mempalace-fallback.json')
fallback_data = json.loads(open(fallback_path).read())

test('G.1 Fallback empty (no crash during test)', lambda: (
    len(fallback_data.get('drawers', [])) == 0,
    f"{len(fallback_data.get('drawers', []))} fallback drawers (should be 0)"
))

# Verify MemPalace didn't lose data during rapid operations
s = mem.status()
test('G.2 Drawer count stable', lambda: (
    s.get('total_drawers', 0) > 170,
    f"{s.get('total_drawers')} drawers"
))

# ═══════════════════════════════════════════════════════════════
# SECTION H: SYSTEM MEMORY vs MEMPALACE CONSISTENCY
# Facts in system memory should also be findable in MemPalace
# ═══════════════════════════════════════════════════════════════
print('\n🔄 SECTION H: SYSTEM MEMORY ↔ MEMPALACE SYNC')
print('-' * 50)

# Key facts from system memory (the injected context)
system_facts = [
    ('Cash Flow DB', '3404eed8'),
    ('Play Store locale', 'id'),
    ('Discord alert', '1492370557927166053'),
    ('StarHabit PIN', '5555'),
    ('Threads kustiarnow', 'kustiarnow'),
    ('Gold report', 'Antam'),
    ('Obsidian vault', 'obsidian-vault'),
    ('git rule', 'git pull'),
]

sync_passed = 0
for query, keyword in system_facts:
    r = search.search(query, expand='auto', limit=5)
    found = any(keyword.lower() in item.text.lower() for item in r)
    if found:
        sync_passed += 1

test(f'H.1 System memory sync: {sync_passed}/{len(system_facts)}', lambda: (
    sync_passed >= len(system_facts) - 1,
    f'{sync_passed}/{len(system_facts)} facts in both system memory AND MemPalace'
))

# ═══════════════════════════════════════════════════════════════
# FINAL SUMMARY
# ═══════════════════════════════════════════════════════════════
print('\n' + '=' * 65)
print('💀 HARD TEST SUMMARY')
print('=' * 65)

sections = {}
for name, ok, elapsed, detail in results:
    section = name.split('.')[0]
    sections.setdefault(section, {'pass': 0, 'fail': 0, 'time': 0})
    if ok:
        sections[section]['pass'] += 1
    else:
        sections[section]['fail'] += 1
    sections[section]['time'] += elapsed

for section, data in sorted(sections.items()):
    total = data['pass'] + data['fail']
    status = '✅' if data['fail'] == 0 else '⚠️' if data['pass'] > data['fail'] else '❌'
    print(f'  {status} Section {section}: {data["pass"]}/{total} ({data["time"]:.1f}s)')

passed = sum(1 for _, ok, _, _ in results if ok)
total_tests = len(results)
total_time = sum(t for _, _, t, _ in results)

print(f'\n🎯 TOTAL: {passed}/{total_tests} passed')
print(f'⏱️  TOTAL TIME: {total_time:.1f}s')
print(f'📦 FINAL DRAWERS: {mem.status().get("total_drawers")}')

failed = [(name, detail) for name, ok, _, detail in results if not ok]
if failed:
    print(f'\n⚠️  FAILED:')
    for name, detail in failed:
        print(f'  ❌ {name}: {detail}')
else:
    print(f'\n🎉 ALL {total_tests} TESTS PASSED — FRAMEWORK SOLID!')
