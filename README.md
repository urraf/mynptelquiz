# NPTEL Quiz Bench

Practice sites for the weekly assignment questions of two NPTEL courses (IIT Kharagpur):

| Page | Course | Questions |
|---|---|---|
| [index.html](index.html) | Introduction to Industry 4.0 and Industrial Internet of Things (Prof. Sudip Misra) | 1,582 from 2022–2026 |
| [psychology-of-learning.html](psychology-of-learning.html) | Psychology of Learning (Prof. Atasi Mohanty) | 478 from 2023–2026 |

Open either file in a browser. No server or internet connection is needed.

## Features

- Practice mode (instant feedback), exam mode (score at the end) and study mode (answer sheet)
- Mixed drill across chosen runs and weeks, with an option to skip questions repeated across years
- "Must know" and "Repeated" badges on questions asked in more than one run
- A mistakes list that keeps the questions you got wrong until you answer them right
- A "Next week" button at the end of each weekly set

## About the answers

The questions come from public answer-key sites and screen recordings of the assignments. Every answer was then checked against the lecture transcripts and slides. Answers marked "Checked against lecture" are confirmed by the lecture. The few marked "Check this answer" are still uncertain. This is not NPTEL's official answer key.

## Editing

Question data lives in `data/` (IIoT) and `data-psych/` (Psychology), one JSON file per year. After changing it, rebuild both pages:

```
python3 build.py
```

`courses.json` holds each course's title, notes and colours, and `src/app.html` is the shared page template.
