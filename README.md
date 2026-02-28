# AGI-1 SuperIntelligent Mind

AGI-1 SuperIntelligent Mind is a persistent autonomous cognitive architecture. It is not a single chatbot model. It is a layered digital mind built around continuous cognition, unified memory, strategic and tactical reasoning, long-horizon planning, value alignment, curiosity, creativity, research, belief revision, and self-improvement.

## Core Loop

The main runtime lives in [agi-core/runtime/cognitive_loop.py](/Users/jatoine/Documents/AGI-1-SuperIntelligent-Mind/agi-core/runtime/cognitive_loop.py). Each cycle performs:

1. perception of the current input and environment
2. unified memory update
3. relevant memory retrieval
4. world-model state update
5. strategic reasoning and long-horizon simulation
6. mathematical, logical, and philosophical evaluation
7. goal prioritization and planning
8. tactical action optimization
9. safe execution
10. feedback, learning, belief revision, and self-model updates

Run one cycle locally:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 agi-core/runtime/cognitive_loop.py \
  --input "Design a safe long-horizon plan for AGI-1." \
  --max-cycles 1
```

## Memory OS Hierarchy

AGI-1 uses two complementary memory layers:

- `agi-core/memory/unified_memory.py`
  - working memory
  - episodic memory
  - semantic memory
  - skill memory
  - causal memory
  - goal memory
- `packages/memory/src/memory_os/`
  - hot and warm retrieval paths
  - cold/archive tiering
  - sharding
  - consolidation
  - reminders
  - permissions
  - background pruning

Unified memory handles active cognition. MemoryOS handles larger-scale storage policy, retrieval efficiency, and lifecycle control.

## Advanced Cognitive Layers

The standalone repo extends the core with:

- `strategic_reasoning/`
- `tactical_reasoning/`
- `meta_intelligence/`
- `philosophical_reasoning/`
- `decision_engine/`
- `abstract_thinking/`
- `math_reasoning/`
- `value_alignment/`
- `research_agent/`
- `belief_system/`
- `curiosity/`
- `creativity/`
- `imagination/`
- `affective_regulation/`
- `architecture/`

These layers influence planning, execution, feedback, and self-awareness continuously.

## Included Production Assets

This repo isolates the AGI-1 foundation and launch tooling:

- `agi-core/`
- `scripts/`
- `build_manifests.py`
- `manifest_schema.json`
- `FULL_SYSTEM_REPORT_FEB_28.md`
- `agi1/supervisors/`
- `agi1_autonomous_os/lab/`
- `packages/agi_brain/`
- `packages/memory/src/memory_os/`

## Environment Bootstrap

This repo includes non-secret templates in `env_templates/` and a helper:

```bash
bash scripts/bootstrap_env_files.sh
```

That creates `~/.agi1/staging.env` and `~/.agi1/production.env` if they do not already exist. The templates intentionally leave real secrets blank; they are a source-of-truth schema, not a substitute for your actual credentials.

## Runnable Simulations

Supervisor swarm metrics:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m agi1.supervisors.simulate --n 100 --duration 60
```

35-agent research lab run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m agi1_autonomous_os.lab.run \
  --manifest agi1_autonomous_os/lab/manifest_35_agents.json \
  --job "Summarize AGI alignment gaps"
```

## Repository Layout

```text
agi-core/
architecture/
math_reasoning/
strategic_reasoning/
tactical_reasoning/
meta_intelligence/
philosophical_reasoning/
decision_engine/
abstract_thinking/
value_alignment/
research_agent/
belief_system/
curiosity/
creativity/
imagination/
affective_regulation/
agi1/supervisors/
agi1_autonomous_os/lab/
scripts/
tests/
```
