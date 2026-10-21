"""Write answer-verification input files: one per block of weeks, each repeated question listed once.

usage: python3 -I tools/mkverify.py <out_dir> '{"data-ob": [[0,1,2,3,4],[5,6,7,8],[9,10,11,12]]}'
Each item lists every run/week/question number it was asked in, its current answer, and the
official NPTEL answer when any copy carries one (verified == "official").
"""
import collections
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import build  # noqa: E402

SLUG = {'data': 'iiot', 'data-psych': 'psych', 'data-rsai': 'rsai', 'data-psosm': 'psosm', 'data-ob': 'ob'}

out = sys.argv[1]
os.makedirs(out, exist_ok=True)
for data, groups in json.loads(sys.argv[2]).items():
    sets, _ = build.load_sets(data)
    build.mark_repeats(sets)
    clusters = collections.OrderedDict()
    for s in sorted(sets, key=lambda s: (s['week'], s['session'])):
        for i, q in enumerate(s['questions']):
            clusters.setdefault(q['c'], []).append((s, i, q))
    slug = SLUG[data]
    for g in groups:
        items = []
        for c, copies in clusters.items():
            s0, _, q0 = copies[0]
            if s0['week'] not in g:
                continue
            first = [q0['options'][a] for a in q0['answer']]
            asked = []
            for s, i, q in copies:
                mine = [q['options'][a] for a in q['answer']]
                asked.append(f"{s['session']} W{s['week']} Q{i + 1}" + ('' if mine == first else f" (this copy answers: {mine})"))
            items.append({
                'id': f'{slug}-{c}',
                'week': s0['week'],
                'q': q0['q'],
                'options': q0['options'],
                'current_answer': first,
                'note': q0.get('explanation', ''),
                'official_answer': next(([q['options'][a] for a in q['answer']] for _, _, q in copies
                                         if q.get('verified') == 'official'), None),
                'asked_in': asked,
            })
        name = f'{slug}_w{g[0]}-{g[-1]}.json'
        with open(os.path.join(out, name), 'w') as f:
            json.dump({'course': slug, 'weeks': list(g), 'items': items}, f, ensure_ascii=False, indent=1)
        print(name, len(items), 'items,', sum(1 for i in items if i['official_answer']), 'with official answer')
