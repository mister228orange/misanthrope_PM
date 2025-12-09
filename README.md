# Misanthope PM

*A lightweight system for analyzing engineering output, estimating task effort, and automating project-management bullshit.*

This project eliminates the need for slow, incompetent PM intermediaries by automatically extracting work metrics from Git history, matching closed tasks with real development effort, and generating LLM-based estimations.

## Project Structure
```text
.
├── closed_tasks
│   ├── november_25.txt
│   ├── october_25.txt
│   └── september_25.txt
├── git.logs
├── models.py
├── project_manager.py
├── pyproject.toml
├── README.md
├── todo
├── utils.py
└── uv.lock
```


## Core Idea

The system ingests **real engineering data**, not Jira fantasies:

### Closed Tasks
Stored in plain text. Each line contains: `Task description … F`
Where final letter is category:
- `I` — infrastructure tasks
- `F` — frontend tasks
- `B` — backend tasks

### Git Logs Parsing
`git.logs` is parsed to extract:
- commit hash, author, date, title
- number of insertions/deletions
- full diff text

### Daily Summary
The system aggregates per day:
| day | insertions | deletions | commits |
|-----|------------|-----------|---------|
| 2025-12-04 | 134 | 58 | 6 |

## LLM-Powered Planning & Estimation

Your code already loads an LLM model:
```python
client = Client(host='http://localhost:11434')
deepseek = "gemma3:12b"
```
# Project Manager Automation - Next Steps & Roadmap

## Next Steps

### 1) Task Estimation
**Using `ClosedTask` history, LLM derives:**
- Expected time
- Required minimum skill level  
- Probability of category (F/B/I)
- Anomaly detection

### 2) Velocity Modeling  
**LLM learns per-developer patterns:**
- Insertions/day, deletions/day, diff complexity
- Stability (ratio of bugfix commits)
- Quality signals

### 3) Prediction
**Given upcoming `todo` tasks + current velocity → automatic delivery forecasts**

## Roadmap

### Phase 1 — Stabilize Parsing (Done/In Progress)
- [x] Proper Git log parser
- [x] Insertions/deletions extraction  
- [x] Daily aggregation
- [x] Closed Task loader
- [ ] Link commits to task categories
- [ ] Detect "dead days" (no commits but tasks closed)

### Phase 2 — Developer Metrics
- [ ] Per-developer velocity
- [ ] Developer anomaly detection (big spikes = crunch/burnout)
- [ ] "Quality score" (ratio of bugfixes vs features)

### Phase 3 — Automatic Task Estimation (LLM)
- [ ] Feed historical closed tasks → build knowledge base
- [ ] LLM learns mapping (text → complexity category)
- [ ] Auto-generate:
  - Estimated hours
  - Required skill level
  - Risk score
  - Recommended developer

### Phase 4 — Project Planning
- [ ] Parse `todo`
- [ ] Auto-generate execution plan
- [ ] Auto-generate deadlines from velocity
- [ ] Auto-generate progress report in natural language
- [ ] Replace manual PM updates entirely

### Phase 5 — Automation
- [ ] Cron job to re-run analysis daily
- [ ] Produce a dashboard (streamlit or FastAPI+react)
- [ ] Send reports to Telegram or Slack

## Why This Replaces PMs

The system uses **actual developer behavior**, not pretend Jira statuses.

**Manual PMs fail because they:**
- Don't understand tech
- Can't estimate engineering effort
- Generate noise instead of value
- Slow down communication
- Add fake bureaucracy
- Rely on subjective "feels", not git graphs

**This system:**
- Sees exactly what work was done
- Knows who is productive
- Knows effort trends
- Generates estimations programmatically
- Produces forecasts automatically

## Planned Enhancements

### Semantic commit analysis
Tag commits as: Feature, Bugfix, Refactoring, Cleanup, Architectural, Trash spam

### Commit → Task matching
Via embedding similarity between commit titles, code diff, and task descriptions

### Weekly & monthly reports
Auto-generated: workload, top contributors, blockers, regressions, burn rate, risk forecast

### Replace "biotrash" PM
Complete automation of: planning, prioritization, estimation, reporting, quality control, timeline forecasting

## Installation

to be later

## Make sure you have an LLM endpoint running:

```bash
ollama run deepseek-r1:8b
```
*A lightweight system for analyzing engineering output, estimating task effort, and automating project-management bullshit.*
