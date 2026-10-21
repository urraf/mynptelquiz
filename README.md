# NPTEL Quiz Bench

Practice sites for the weekly assignment questions of five NPTEL courses:

| Page | Course | Questions |
|---|---|---|
| [index.html](index.html) | Introduction to Industry 4.0 and Industrial Internet of Things (Prof. Sudip Misra) | 1,582 from 2022–2026 |
| [psychology-of-learning.html](psychology-of-learning.html) | Psychology of Learning (Prof. Atasi Mohanty) | 478 from 2023–2026 |
| [responsible-safe-ai.html](responsible-safe-ai.html) | Responsible & Safe AI Systems (Prof. Ponnurangam Kumaraguru, Prof. Balaraman Ravindran, Prof. Arun Rajkumar) | 464 from 2024–2026 |
| [privacy-security-social-media.html](privacy-security-social-media.html) | Privacy and Security in Online Social Media (Prof. Ponnurangam Kumaraguru) | 784 from 2023–2026 |
| [organizational-behaviour.html](organizational-behaviour.html) | Organizational Behaviour (Prof. M. P. Ganesh, IIT Hyderabad) | 450 from 2022–2026 |

Open any of these files in a browser. No server or internet connection is needed.

## Features

- Practice mode (instant feedback), exam mode (score at the end) and study mode (answer sheet)
- Mixed drill across chosen runs and weeks, with an option to skip questions repeated across years
- "Must know" and "Repeated" badges on questions asked in more than one run
- A mistakes list that keeps the questions you got wrong until you answer them right
- A "Next week" button at the end of each weekly set
- Typed answers for numeric questions

## About the answers

The questions come from public answer-key sites and screen recordings of the assignments. Every answer was then checked against the lecture transcripts and slides. Answers marked "NPTEL accepted answer" come from NPTEL's own answer screens, and answers marked "Checked against lecture" are confirmed by the lecture. The few marked "Check this answer" are still uncertain. This is not NPTEL's official answer key.

## Editing

Question data lives in `data/` (IIoT), `data-psych/` (Psychology), `data-rsai/` (Responsible AI), `data-psosm/` (Privacy & Security) and `data-ob/` (Organizational Behaviour). After changing it, rebuild the pages and run the smoke test:

```
python3 build.py
for f in *.html; do node tools/smoke_test.js "$f"; done
```

`courses.json` holds each course's title, notes and colours, and `src/app.html` is the shared page template. `tools/mkverify.py` and `tools/apply_verify.py` prepare answer-checking batches and apply their verdicts.
