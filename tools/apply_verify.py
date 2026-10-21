"""Apply verification verdicts to the quiz data files.

usage: python3 -I tools/apply_verify.py <verify_dir> [--only=<slug>] [--dry]
Reads <verify_dir>/<chunk>.json (inputs from mkverify.py) and <verify_dir>/out_<chunk>.json (verdicts),
then updates every copy of each question in data*/ *.json, matched by run + week + question number.
Official NPTEL answers are never overwritten. Copies whose options don't contain the verdict's answer
are listed in <verify_dir>/leftovers.json.txt for a manual check.
"""
import collections
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
vdir = sys.argv[1]
dry = '--dry' in sys.argv
only = [a.split('=', 1)[1] for a in sys.argv if a.startswith('--only=')]
DATA = {'psych': 'data-psych', 'rsai': 'data-rsai', 'psosm': 'data-psosm', 'ob': 'data-ob'}
QUOTES = str.maketrans({'‘': "'", '’': "'", '“': '"', '”': '"', '–': '-', '—': '-'})


def norm(t):
    return re.sub(r'\s+', ' ', str(t).translate(QUOTES).lower()).strip().rstrip('.')


files, index = {}, {}
for f in glob.glob(os.path.join(ROOT, 'data*', '*.json')):
    d = json.load(open(f))
    files[f] = d
    for s in d['sets']:
        sess = re.sub(r'\s+', ' ', s['session']).strip().replace('–', '-')
        for i, q in enumerate(s['questions']):
            index[(os.path.basename(os.path.dirname(f)), sess, int(s['week']), i + 1)] = q

stats = collections.Counter()
changes, problems, leftovers = [], [], []
for inp in sorted(glob.glob(os.path.join(vdir, '*.json'))):
    name = os.path.basename(inp)
    if name.startswith('out_') or (only and not name.startswith(only[0] + '_')):
        continue
    outp = os.path.join(vdir, 'out_' + name)
    if not os.path.exists(outp):
        print('no verdicts yet for', name)
        continue
    items = {it['id']: it for it in json.load(open(inp))['items']}
    ddir = DATA.get(name.split('_')[0], 'data')
    for r in json.load(open(outp))['results']:
        it = items.get(r['id'])
        if not it:
            problems.append(f"{name}: unknown id {r['id']}")
            continue
        want = [norm(a) for a in r.get('answer', [])]
        for loc in it['asked_in']:
            m = re.match(r'(.+?) W(\d+) Q(\d+)', loc)
            q = index.get((ddir, m.group(1), int(m.group(2)), int(m.group(3))))
            if q is None:
                problems.append(f'{name}: cannot find {loc}')
                continue
            onorm = [norm(o) for o in q['options']]
            # first option matching each wanted answer (an option list can repeat a text)
            new = sorted({onorm.index(w) for w in want if w in onorm})
            if len(new) != len(set(want)) or not new:
                problems.append(f"{name}: {loc}: answer {r.get('answer')} not in options {q['options']}")
                if q.get('verified') != 'official':
                    q['verified'] = 'unsure'
                stats['unmatched'] += 1
                leftovers.append({'id': f"{r['id']}|{loc.split(' (')[0]}", 'course': ddir, 'q': q['q'],
                                  'options': q['options'], 'current_answer': [q['options'][a] for a in q['answer']],
                                  'loc': loc.split(' (')[0]})
                continue
            old = sorted(q['answer'])
            if q.get('verified') == 'official':
                if new != old:
                    problems.append(f"{name}: {loc}: verdict {r.get('answer')} disagrees with the official key; kept official")
                stats['official'] += 1
                continue
            ev = (r.get('evidence') or '').strip()
            if new != old:
                was = ', '.join(q['options'][a] for a in old)
                changes.append(f"{loc}: {q['q'][:70]!r}: {was!r} -> {[q['options'][a] for a in new]}")
                q['answer'] = new
                q['explanation'] = f'Corrected after checking the lecture (was: {was}). {ev}'.strip()
                stats['changed'] += 1
            else:
                q['explanation'] = ev or q.get('explanation', '')
                stats['kept'] += 1
            q['verified'] = 'unsure' if r.get('verdict') == 'unsure' else r.get('basis', 'reasoning')

print(dict(stats))
print(f'{len(changes)} answer changes')
for c in changes:
    print('  ' + c)
for p in problems:
    print('  PROBLEM ' + p)
with open(os.path.join(vdir, 'leftovers.json.txt'), 'w') as f:
    json.dump({'items': leftovers}, f, ensure_ascii=False, indent=1)
print(len(leftovers), 'copies need their own check -> leftovers.json.txt')
if not dry:
    for f, d in files.items():
        with open(f, 'w') as fh:
            json.dump(d, fh, ensure_ascii=False, indent=1)
    print('written')
