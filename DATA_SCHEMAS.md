# AGI-1 Data Schemas

## Thought Object

```text
Thought {
  thought_id: string
  summary: string
  focus: string
  rationale: string
  confidence: float
  uncertainty: float
  attention_weight: float
  created_at: timestamp
}
```

Implemented in [models.py](/Users/jatoine/Documents/AGI-1-SuperIntelligent-Mind/agi-core/runtime/models.py).

## Memory Object

```text
Memory {
  id: string
  type: working | episodic | semantic | skill | causal | goal
  embedding: optional vector
  importance: float
  timestamp: timestamp
  relationships: list
}
```

Working representation lives in [unified_memory.py](/Users/jatoine/Documents/AGI-1-SuperIntelligent-Mind/agi-core/memory/unified_memory.py) and the larger lifecycle system in [memory_os.py](/Users/jatoine/Documents/AGI-1-SuperIntelligent-Mind/packages/memory/src/memory_os/memory_os.py).

## Belief Graph Node

```text
BeliefNode {
  concept: string
  probability: float
  evidence_links: list[string]
  updated_at: timestamp
}
```

Implemented as `BeliefNode` in [models.py](/Users/jatoine/Documents/AGI-1-SuperIntelligent-Mind/agi-core/runtime/models.py) and persisted in [belief_store.py](/Users/jatoine/Documents/AGI-1-SuperIntelligent-Mind/belief_system/belief_store.py).

## Goal Representation

```text
Goal {
  goal_id: string
  description: string
  priority: float
  urgency: float
  reward: float
  source: string
  status: active | archived
  created_at: timestamp
  due_at: optional timestamp
}
```

Implemented in [models.py](/Users/jatoine/Documents/AGI-1-SuperIntelligent-Mind/agi-core/runtime/models.py).

## Internal Message

```text
AGI_Message {
  sender: string
  receiver: string
  intent: string
  data: map
  confidence: float
  priority: float
  timestamp: timestamp
}
```

Implemented in [models.py](/Users/jatoine/Documents/AGI-1-SuperIntelligent-Mind/agi-core/runtime/models.py) and [message_protocol.py](/Users/jatoine/Documents/AGI-1-SuperIntelligent-Mind/agi-core/runtime/message_protocol.py).
