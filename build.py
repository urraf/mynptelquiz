"""Build one quiz page per course listed in courses.json.

For each course, its data folder's *.json files are merged into src/app.html and written as:
  <out>   - standalone page, open directly in a browser
  <dist>  - same page without the document skeleton (for publishing)

Usage: python3 build.py [slug ...]   (no slug = build every course)
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))


def clean(s):
    return re.sub(r"\s+", " ", str(s or "")).strip()


def load_sets(data_dir):
    sets, problems = [], []
    for path in sorted(glob.glob(os.path.join(ROOT, data_dir, "*.json"))):
        with open(path) as f:
            doc = json.load(f)
        for s in doc.get("sets", []):
            qs = []
            for i, q in enumerate(s.get("questions", [])):
                text = clean(q.get("q"))
                opts = [clean(o) for o in q.get("options", []) if clean(o)]
                ans = sorted({a for a in q.get("answer", []) if isinstance(a, int) and 0 <= a < len(opts)})
                where = f"{os.path.basename(path)} {s.get('session')} w{s.get('week')} q{i + 1}"
                if not text or not opts or not ans:
                    problems.append(f"dropped {where}: missing text/options/answer")
                    continue
                item = {"q": text, "options": opts, "answer": ans}
                if clean(q.get("explanation")):
                    item["explanation"] = clean(q["explanation"])
                if q.get("source"):
                    item["source"] = q["source"]
                if q.get("verified"):
                    item["verified"] = q["verified"]
                qs.append(item)
            if qs:
                sets.append({
                    "year": s.get("year"),
                    "session": clean(s.get("session")).replace("–", "-"),
                    "week": int(s.get("week")),
                    "source": s.get("source") or "",
                    "questions": qs,
                })
    # one set per session+week; if two files supply the same one, keep the larger
    merged = {}
    for s in sets:
        k = (s["session"], s["week"])
        if k not in merged or len(s["questions"]) > len(merged[k]["questions"]):
            merged[k] = s
    return list(merged.values()), problems


STOP = set("the of a an is are to in and or for which following what on by with as be that this "
           "it its from at true false state statement statements correct incorrect not none all "
           "above these those".split())


def toks(s):
    return {w for w in re.sub(r"[^a-z0-9]+", " ", s.lower()).split() if w not in STOP and len(w) > 1}


def jac(a, b):
    return len(a & b) / len(a | b) if a | b else 0


def mark_repeats(sets):
    """Link each question to similar ones from other runs.

    q["rel"] = [[session, week, exact], ...]  exact=1 for the same question, 0 for the same topic reworded
    q["c"]   = cluster id shared by exact repeats (used to skip duplicates)
    """
    qs = [(s["session"], s["week"], q, toks(q["q"]), toks(" ".join(q["options"])))
          for s in sets for q in s["questions"]]
    parent = list(range(len(qs)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    rel = [dict() for _ in qs]
    for i, a in enumerate(qs):
        for j in range(i + 1, len(qs)):
            b = qs[j]
            if a[0] == b[0]:
                continue
            jq = jac(a[3], b[3])
            if jq < 0.4:
                continue
            score = 0.5 * jq + 0.5 * jac(a[4], b[4])
            if score < 0.5:
                continue
            exact = int(score >= 0.7 and jq >= 0.5)
            # the syllabus keeps topics in the same week each run, so a reworded match must be close by
            if not exact and abs(a[1] - b[1]) > 1:
                continue
            if exact:
                parent[find(i)] = find(j)
            for x, y in ((i, b), (j, a)):
                k = (y[0], y[1])
                rel[x][k] = max(rel[x].get(k, 0), exact)
    for i, (_, _, q, _, _) in enumerate(qs):
        q["c"] = find(i)
        if rel[i]:
            q["rel"] = [[sess, wk, ex] for (sess, wk), ex in rel[i].items()]


def theme_css(theme):
    if not theme:
        return ""
    light = ";".join(f"{k}:{v}" for k, v in theme["light"].items())
    dark = ";".join(f"{k}:{v}" for k, v in theme["dark"].items())
    return (f":root{{{light}}}\n"
            f"@media (prefers-color-scheme: dark){{:root:not([data-theme=\"light\"]){{{dark}}}}}\n"
            f":root[data-theme=\"dark\"]{{{dark}}}")


def js(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def build(course, courses, template):
    sets, problems = load_sets(course["data"])
    mark_repeats(sets)

    def page(local):
        nav = [{"name": c["name"], "current": c is course,
                "href": c["out"] if local else (c.get("artifact") or "")}
               for c in courses]
        nav = [n for n in nav if n["current"] or n["href"]]
        cfg = {k: course.get(k, "") for k in ("lskey", "meta", "heading", "note")}
        cfg["nav"] = nav
        return (template.replace("__TITLE__", course["title"])
                .replace("/*__THEME__*/", theme_css(course.get("theme")))
                .replace("/*__DATA__*/", js({"sets": sets}))
                .replace("/*__COURSE__*/", js(cfg)))

    dist = os.path.join(ROOT, course["dist"])
    os.makedirs(os.path.dirname(dist), exist_ok=True)
    with open(dist, "w") as f:
        f.write(page(local=False))
    head, body = page(local=True).split('<div class="wrap" id="app"></div>', 1)
    full = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
            + head + '</head>\n<body>\n<div class="wrap" id="app"></div>' + body + '\n</body>\n</html>\n')
    with open(os.path.join(ROOT, course["out"]), "w") as f:
        f.write(full)
    total = sum(len(s["questions"]) for s in sets)
    print(f"{course['slug']}: {len(sets)} sets, {total} questions -> {course['out']}")
    for p in problems:
        print("  " + p, file=sys.stderr)


def main():
    with open(os.path.join(ROOT, "courses.json")) as f:
        courses = json.load(f)["courses"]
    with open(os.path.join(ROOT, "src", "app.html")) as f:
        template = f.read()
    wanted = set(sys.argv[1:])
    for course in courses:
        if not wanted or course["slug"] in wanted:
            build(course, courses, template)


if __name__ == "__main__":
    main()
