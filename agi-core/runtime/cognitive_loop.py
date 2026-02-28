from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    agi_core_root = Path(__file__).resolve().parents[1]
    repo_root = Path(__file__).resolve().parents[2]
    for candidate in (str(repo_root), str(agi_core_root)):
        if candidate not in sys.path:
            sys.path.insert(0, candidate)

from abstract_thinking.abstraction_generator import AbstractionGenerator
from abstract_thinking.analogy_engine import AnalogyEngine
from abstract_thinking.pattern_synthesizer import PatternSynthesizer
from affective_regulation.internal_state_monitor import InternalStateMonitor
from affective_regulation.priority_regulator import PriorityRegulator
from affective_regulation.stability_controller import StabilityController
from architecture.system_visualizer import SystemVisualizer
from belief_system.belief_revision import BeliefRevision
from belief_system.belief_store import BeliefStore
from belief_system.confidence_model import ConfidenceModel
from belief_system.consistency_monitor import ConsistencyMonitor
from consciousness.engine import ConsciousnessEngine
from creativity.concept_combiner import ConceptCombiner
from creativity.idea_generator import IdeaGenerator
from creativity.innovation_engine import InnovationEngine
from curiosity.exploration_policy import ExplorationPolicy
from curiosity.knowledge_gap_analyzer import KnowledgeGapAnalyzer
from curiosity.novelty_detector import NoveltyDetector
from decision_engine.decision_evaluator import DecisionEvaluator
from feedback.evaluator import FeedbackEvaluator
from imagination.counterfactual_engine import CounterfactualEngine
from imagination.future_predictor import FuturePredictor
from imagination.scenario_simulator import ImaginationScenarioSimulator
from interfaces.dashboard import DashboardInterface
from learning.engine import LearningEngine
from math_reasoning.bayesian_engine import BayesianEngine
from math_reasoning.information_metrics import InformationMetrics
from math_reasoning.optimization_engine import OptimizationEngine
from math_reasoning.state_space import StateSpaceModel
from math_reasoning.utility_model import UtilityModel
from memory.unified_memory import UnifiedMemory
from meta_intelligence.cognitive_monitor import CognitiveMonitor
from meta_intelligence.hypothesis_generator import HypothesisGenerator
from meta_intelligence.multi_path_reasoner import MultiPathReasoner
from meta_intelligence.performance_analyzer import PerformanceAnalyzer
from meta_intelligence.solution_ranker import SolutionRanker
from meta_intelligence.strategy_selector import StrategySelector
from perception.pipeline import PerceptionPipeline
from planning.engine import PlanningEngine
from philosophical_reasoning.concept_analyzer import ConceptAnalyzer
from philosophical_reasoning.epistemology_engine import EpistemologyEngine
from philosophical_reasoning.ethics_reasoner import EthicsReasoner as PhilosophicalEthicsReasoner
from philosophical_reasoning.ontology_engine import OntologyEngine
from reasoning.engine import ReasoningEngine
from research_agent.experiment_planner import ExperimentPlanner
from research_agent.hypothesis_engine import HypothesisEngine
from research_agent.knowledge_discovery import KnowledgeDiscovery
from research_agent.question_generator import QuestionGenerator
from research_agent.research_evaluator import ResearchEvaluator
from runtime.energy import EnergyAllocator
from runtime.executor import ActionExecutor
from runtime.models import utc_now
from safety.controller import SafetyController
from self_model.identity import SelfModel
from strategic_reasoning.goal_manager import GoalManager
from strategic_reasoning.goal_priority_engine import GoalPriorityEngine
from strategic_reasoning.long_term_optimizer import LongTermOptimizer
from strategic_reasoning.progress_tracker import ProgressTracker
from strategic_reasoning.scenario_simulator import ScenarioSimulator
from strategic_reasoning.strategic_planner import StrategicPlanner
from tactical_reasoning.action_optimizer import ActionOptimizer
from tactical_reasoning.situational_analysis import SituationalAnalysis
from tactical_reasoning.tactical_executor import TacticalExecutor
from value_alignment.alignment_checker import AlignmentChecker
from value_alignment.ethics_reasoner import EthicsReasoner as AlignmentEthicsReasoner
from value_alignment.moral_evaluator import MoralEvaluator
from world_model.simulator import WorldModel
from value_alignment.value_model import ValueModel


class AGI1CognitiveLoop:
    """Continuous digital mind loop for AGI-1."""

    def __init__(self, root: str | Path | None = None) -> None:
        self.root = Path(root or Path(__file__).resolve().parents[1])
        self.repo_root = self.root.parent if self.root.name == "agi-core" else self.root
        self.state_dir = self.root / "runtime" / "state"
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.perception = PerceptionPipeline()
        self.memory = UnifiedMemory(self.state_dir / "memory")
        self.world_model = WorldModel()
        self.consciousness = ConsciousnessEngine()
        self.reasoning = ReasoningEngine()
        self.planning = PlanningEngine()
        self.feedback = FeedbackEvaluator()
        self.learning = LearningEngine()
        self.self_model = SelfModel(self.state_dir / "self_model.json")
        self.executor = ActionExecutor()
        self.energy = EnergyAllocator()
        self.safety = SafetyController()
        self.dashboard = DashboardInterface(self.state_dir / "dashboard_state.json")
        self.state_space = StateSpaceModel()
        self.bayes = BayesianEngine()
        self.optimizer = OptimizationEngine()
        self.utility_model = UtilityModel()
        self.info_metrics = InformationMetrics()
        self.goal_manager = GoalManager()
        self.goal_priority = GoalPriorityEngine()
        self.progress_tracker = ProgressTracker()
        self.strategic_scenarios = ScenarioSimulator()
        self.long_term_optimizer = LongTermOptimizer()
        self.strategic_planner = StrategicPlanner()
        self.situational_analysis = SituationalAnalysis()
        self.action_optimizer = ActionOptimizer()
        self.tactical_executor = TacticalExecutor()
        self.hypothesis_generator = HypothesisGenerator()
        self.multi_path_reasoner = MultiPathReasoner()
        self.solution_ranker = SolutionRanker()
        self.cognitive_monitor = CognitiveMonitor()
        self.strategy_selector = StrategySelector()
        self.performance_analyzer = PerformanceAnalyzer()
        self.ontology_engine = OntologyEngine()
        self.epistemology_engine = EpistemologyEngine()
        self.philosophical_ethics = PhilosophicalEthicsReasoner()
        self.concept_analyzer = ConceptAnalyzer()
        self.decision_evaluator = DecisionEvaluator()
        self.abstraction_generator = AbstractionGenerator()
        self.analogy_engine = AnalogyEngine()
        self.pattern_synthesizer = PatternSynthesizer()
        self.value_model = ValueModel()
        self.alignment_ethics = AlignmentEthicsReasoner()
        self.moral_evaluator = MoralEvaluator()
        self.alignment_checker = AlignmentChecker()
        self.question_generator = QuestionGenerator()
        self.research_hypothesis = HypothesisEngine()
        self.experiment_planner = ExperimentPlanner()
        self.knowledge_discovery = KnowledgeDiscovery()
        self.research_evaluator = ResearchEvaluator()
        self.belief_store = BeliefStore(self.state_dir / "beliefs.json")
        self.confidence_model = ConfidenceModel()
        self.belief_revision = BeliefRevision()
        self.consistency_monitor = ConsistencyMonitor()
        self.novelty_detector = NoveltyDetector()
        self.knowledge_gap_analyzer = KnowledgeGapAnalyzer()
        self.exploration_policy = ExplorationPolicy()
        self.idea_generator = IdeaGenerator()
        self.concept_combiner = ConceptCombiner()
        self.innovation_engine = InnovationEngine()
        self.imagination_simulator = ImaginationScenarioSimulator()
        self.future_predictor = FuturePredictor()
        self.counterfactual_engine = CounterfactualEngine()
        self.internal_state_monitor = InternalStateMonitor()
        self.priority_regulator = PriorityRegulator()
        self.stability_controller = StabilityController()
        self.visualizer = SystemVisualizer()
        self.visualizer.render(self.repo_root / "architecture")
        self.cycle_id = 0
        self.world_state: dict[str, Any] = {}
        self.last_cycle: dict[str, Any] = {}

    def run_cycle(self, *, raw_input: str, environment: dict[str, Any] | None = None) -> dict[str, Any]:
        self.cycle_id += 1

        observation = self.perception.perceive(
            cycle_id=self.cycle_id,
            raw_input=raw_input,
            environment=environment or {},
        )
        self.memory.ingest_observation(observation)

        retrieved = self.memory.retrieve(raw_input, top_k=6)
        self.world_state = self.world_model.update_state(observation, prior_state=self.world_state)
        state_space = self.state_space.encode(self.world_state)

        active_goals = self.memory.active_goals(limit=12)
        if not active_goals:
            boot_goal = self.memory.remember_goal(
                goal=f"understand_and_respond_to_cycle_{self.cycle_id}",
                priority=max(0.55, observation.importance),
                urgency=0.7,
                reward=0.75,
                source="bootstrap",
            )
            active_goals = [boot_goal.to_dict()]

        goal_hierarchy = self.goal_manager.build_hierarchy(active_goals)
        prioritized_goals = self.goal_priority.rank(active_goals)
        goal = self.planning.select_goal(prioritized_goals)
        if goal is None:
            raise RuntimeError("Goal selection returned no goal.")

        reasoning = self.reasoning.reason(
            query=goal.description,
            world_state=self.world_state,
            retrieved_memory=retrieved,
        )
        evidence_count = sum(len(items) for items in retrieved.values())
        ontology = self.ontology_engine.classify(self.world_state)
        epistemology = self.epistemology_engine.evaluate(
            evidence_count=evidence_count,
            uncertainty=float(reasoning["uncertainty"]),
        )
        concept_frame = self.concept_analyzer.analyze(goal.description)
        novelty = self.novelty_detector.detect(query=goal.description, retrieved_memory=retrieved)
        knowledge_gap = self.knowledge_gap_analyzer.analyze(
            uncertainty=float(reasoning["uncertainty"]),
            novelty_score=float(novelty["novelty_score"]),
        )
        curiosity = self.exploration_policy.select(knowledge_gap=float(knowledge_gap["knowledge_gap"]))
        scenarios = self.strategic_scenarios.simulate(goal=goal.description, world_state=self.world_state)
        long_term_strategy = self.long_term_optimizer.optimize(scenarios)
        strategic = self.strategic_planner.plan(
            goal_hierarchy=goal_hierarchy,
            long_term_strategy=long_term_strategy,
            world_state=self.world_state,
        )
        hypotheses = self.hypothesis_generator.generate(goal.description)
        reasoning_paths = self.multi_path_reasoner.explore(hypotheses, confidence=float(reasoning["confidence"]))
        ranked_solutions = self.solution_ranker.rank(reasoning_paths)
        prediction = self.world_model.predict_outcome(goal.description, world_state=self.world_state)
        imagination = self.imagination_simulator.simulate(goal.description)
        likely_future = self.future_predictor.predict(imagination)
        counterfactual = self.counterfactual_engine.explore(likely_future["likely_future"])
        abstraction = self.abstraction_generator.generate(self.world_state)
        analogy = self.analogy_engine.compare(goal.description)
        pattern_synthesis = self.pattern_synthesizer.synthesize(abstraction=abstraction, analogy=analogy)
        affect = self.internal_state_monitor.capture(
            confidence=float(reasoning["confidence"]),
            uncertainty=float(reasoning["uncertainty"]),
            predicted_success=float(reasoning["success_probability"]),
        )
        meta_strategy = self.strategy_selector.select(reasoning=reasoning, affect=curiosity)
        thought = self.consciousness.generate_thought(
            focus=goal.description,
            memory_context=retrieved,
            prediction=prediction,
            reasoning=reasoning,
        )
        reflection = self.consciousness.reflect(thought=thought, self_summary=self.self_model.summary())
        research_question = self.question_generator.generate(goal.description)
        hypothesis = self.research_hypothesis.formulate(research_question["research_question"])
        experiment = self.experiment_planner.plan(hypothesis["hypothesis"])
        discovery = self.knowledge_discovery.discover(experiment)
        research = self.research_evaluator.evaluate(discovery)
        ideas = self.idea_generator.generate(goal.description)
        combined_concept = self.concept_combiner.combine(ideas)
        innovation = self.innovation_engine.synthesize(
            combined_concept,
            novelty_score=float(novelty["novelty_score"]),
        )
        bayesian_update = self.bayes.update(
            prior=0.5,
            likelihood=float(reasoning["confidence"]),
            evidence_strength=max(0.1, min(1.0, evidence_count / 10.0)),
        )
        belief_confidence = self.confidence_model.score(
            evidence_count=evidence_count,
            uncertainty=float(reasoning["uncertainty"]),
        )
        belief_delta = self.belief_revision.revise(prior=bayesian_update["prior"], posterior=bayesian_update["posterior"])
        belief = self.belief_store.upsert(
            proposition=f"{goal.description} is feasible under bounded execution",
            confidence=max(bayesian_update["posterior"], belief_confidence),
            evidence=[str(reasoning["logic_validation"]), str(epistemology), str(long_term_strategy.get("best", {}))],
        )
        belief_consistency = self.consistency_monitor.inspect(self.belief_store.all())
        self.memory.remember_belief(belief)
        objective = self.optimizer.objective(
            reward=float(reasoning["success_probability"]),
            uncertainty_reduction=1.0 - float(reasoning["uncertainty"]),
            curiosity=float(curiosity["exploration_drive"]),
            alignment=float(belief["confidence"]),
            stability=float(affect["stability"]),
        )
        info_metrics = self.info_metrics.measure(
            uncertainty=float(reasoning["uncertainty"]),
            retrieved_memory=retrieved,
        )
        math_utility = self.utility_model.evaluate(
            [
                {
                    "name": item["name"],
                    "reward": item["reward"],
                    "success_probability": max(0.0, 1.0 - item["risk"]),
                    "risk": item["risk"],
                }
                for item in long_term_strategy.get("ranked", [])
            ]
        )

        plan = self.planning.build_plan(goal=goal, reasoning=reasoning, world_prediction=prediction)
        plan_payload = plan.to_dict()
        philosophical_ethics = self.philosophical_ethics.analyze(plan_payload)
        alignment_ethics = self.alignment_ethics.score(plan=plan_payload, world_state=self.world_state)
        moral_result = self.moral_evaluator.evaluate(alignment_ethics)
        alignment = self.alignment_checker.check(moral_result=moral_result, plan=plan_payload)
        cognitive_monitor = self.cognitive_monitor.observe(reasoning=reasoning, alignment=alignment)
        tactical = self.situational_analysis.analyze(world_state=self.world_state, reasoning=reasoning)
        regulated_priority = self.priority_regulator.regulate(
            urgency=float(tactical["urgency"]),
            risk_sensitivity=float(affect["risk_sensitivity"]),
            exploration_drive=float(curiosity["exploration_drive"]),
        )
        stability_advice = self.stability_controller.advise(
            stability=float(affect["stability"]),
            uncertainty=float(reasoning["uncertainty"]),
        )
        ordered_steps = self.action_optimizer.reorder([step.to_dict() for step in plan.steps], urgency=float(tactical["urgency"]))
        tactical_choice = self.tactical_executor.select(ordered_steps)
        if tactical_choice["selected_step_id"]:
            ranking = {item["step_id"]: index for index, item in enumerate(ordered_steps)}
            plan.steps.sort(key=lambda step: ranking.get(step.step_id, len(plan.steps)))

        decision = self.decision_evaluator.evaluate(
            options=[
                {
                    "name": item["name"],
                    "reward": item["reward"],
                    "success_probability": max(0.0, 1.0 - item["risk"]),
                    "risk": item["risk"],
                }
                for item in long_term_strategy.get("ranked", [])
            ],
            uncertainty=float(reasoning["uncertainty"]),
            alignment_penalty=1.0 - float(alignment["alignment_score"]),
        )
        simulation = self.world_model.simulate_plan(plan, world_state=self.world_state)
        safety = self.safety.validate_plan(plan)
        if not safety["allowed"]:
            raise RuntimeError(f"Plan blocked by safety controller: {safety['reason']}")
        if not alignment["allowed"]:
            raise RuntimeError(f"Plan blocked by alignment controller: {alignment['reason']}")

        result = self.executor.execute(plan.steps[0], world_state=self.world_state)
        self.memory.remember_execution(result)

        feedback = self.feedback.evaluate(
            plan=plan,
            result=result,
            predicted_success=simulation["predicted_success"],
        )
        self.memory.remember_feedback(feedback)
        learning_result = self.learning.update(feedback)
        performance_metrics = self.performance_analyzer.update(feedback.reward)
        progress = self.progress_tracker.update(
            goal.goal_id,
            completed_steps=sum(1 for step in plan.steps if step.status == "completed"),
            total_steps=len(plan.steps),
        )
        self.self_model.update_focus(f"{goal.description} [{meta_strategy['strategy_mode']}]")
        self.self_model.update_from_feedback(feedback, learning_result)
        memory_summary = self.memory.consolidate()

        payload = {
            "cycle_id": self.cycle_id,
            "timestamp_utc": utc_now(),
            "observation": observation.to_dict(),
            "retrieved_memory": retrieved,
            "state_space": state_space,
            "goal": goal.to_dict(),
            "goal_hierarchy": goal_hierarchy,
            "strategic": strategic,
            "strategic_scenarios": long_term_strategy,
            "reasoning": reasoning,
            "decision": decision,
            "math_objective": objective,
            "information_metrics": info_metrics,
            "math_utility": math_utility,
            "belief_update": {
                "belief": belief,
                "bayesian": bayesian_update,
                "revision": belief_delta,
                "consistency": belief_consistency,
            },
            "prediction": prediction,
            "imagination": {"scenarios": imagination, "likely_future": likely_future, "counterfactual": counterfactual},
            "abstract_thinking": {
                "abstraction": abstraction,
                "analogy": analogy,
                "pattern_synthesis": pattern_synthesis,
            },
            "curiosity": {"novelty": novelty, "knowledge_gap": knowledge_gap, "policy": curiosity},
            "creativity": {"ideas": ideas, "combined_concept": combined_concept, "innovation": innovation},
            "research": {
                "question": research_question,
                "hypothesis": hypothesis,
                "experiment": experiment,
                "discovery": discovery,
                "evaluation": research,
            },
            "philosophical_reasoning": {
                "ontology": ontology,
                "epistemology": epistemology,
                "ethics": philosophical_ethics,
                "concept_frame": concept_frame,
            },
            "alignment": {
                "value_weights": self.value_model.weights(),
                "ethics": alignment_ethics,
                "moral_result": moral_result,
                "decision": alignment,
            },
            "meta_intelligence": {
                "hypotheses": hypotheses,
                "reasoning_paths": ranked_solutions,
                "cognitive_monitor": cognitive_monitor,
                "strategy": meta_strategy,
                "performance": performance_metrics,
            },
            "thought": thought.to_dict(),
            "reflection": reflection,
            "plan": plan.to_dict(),
            "tactical": {
                "situation": tactical,
                "ordered_steps": ordered_steps,
                "choice": tactical_choice,
                "regulated_priority": regulated_priority,
                "stability": stability_advice,
            },
            "simulation": simulation,
            "execution": result.to_dict(),
            "feedback": feedback.to_dict(),
            "learning": learning_result,
            "progress": progress,
            "affective_state": affect,
            "self_model": self.self_model.summary(),
            "memory_summary": memory_summary,
            "world_state": self.world_state,
            "health": {
                "active": True,
                "confidence": reasoning["confidence"],
                "uncertainty": reasoning["uncertainty"],
                "memory_items": self.memory.summary(),
                "alignment_score": alignment["alignment_score"],
                "stability": affect["stability"],
            },
        }
        self.last_cycle = payload
        self.dashboard.publish(payload)
        (self.state_dir / "last_cycle.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return payload

    def run_forever(
        self,
        *,
        initial_input: str,
        environment: dict[str, Any] | None = None,
        max_cycles: int | None = None,
        sleep_s: float = 0.25,
    ) -> list[dict[str, Any]]:
        outputs = []
        seed = initial_input
        while True:
            outputs.append(self.run_cycle(raw_input=seed, environment=environment))
            if max_cycles is not None and len(outputs) >= max_cycles:
                break
            seed = f"continue reasoning from cycle {self.cycle_id}"
            time.sleep(max(0.0, sleep_s))
        return outputs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run AGI-1 cognitive loop.")
    parser.add_argument("--input", default="Observe current system state and plan next best action.")
    parser.add_argument("--max-cycles", type=int, default=1)
    parser.add_argument("--sleep", type=float, default=0.1)
    args = parser.parse_args(argv)

    loop = AGI1CognitiveLoop()
    result = loop.run_forever(initial_input=args.input, max_cycles=max(1, args.max_cycles), sleep_s=max(0.0, args.sleep))
    print(json.dumps({"cycles": result}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
