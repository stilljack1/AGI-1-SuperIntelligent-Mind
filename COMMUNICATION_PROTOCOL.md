# AGI-1 Communication Protocol

AGI-1 uses asynchronous internal messages to coordinate perception, memory, reasoning, planning, learning, evaluation, and self-reflection.

## Message Format

```text
AGI_Message {
  sender
  receiver
  intent
  data
  confidence
  priority
  timestamp
}
```

## Priority Rules

- Higher `priority` is dispatched first.
- When priorities tie, higher `confidence` is dispatched first.
- Safety, alignment, and rollback messages should be published with priority above `0.9`.

## Example Intents

- `observation_ready`
- `memory_retrieval_request`
- `belief_revision`
- `plan_candidate`
- `alignment_review`
- `execution_result`
- `learning_update`
- `self_reflection`

## Module Routing

- Perception -> Memory: `observation_ready`
- Memory -> Reasoning: `context_bundle`
- Reasoning -> Planning: `reasoning_result`
- Strategic reasoning -> Planning: `long_horizon_strategy`
- Alignment -> Execution: `allow_or_block`
- Execution -> Feedback: `execution_result`
- Feedback -> Learning: `reward_signal`
- Learning -> Self Model: `capability_update`

Implementation lives in [message_protocol.py](/Users/jatoine/Documents/AGI-1-SuperIntelligent-Mind/agi-core/runtime/message_protocol.py).
