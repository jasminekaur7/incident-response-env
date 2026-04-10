"""
incident_response_env — server/incident_environment.py
Core Environment logic: reset(), step(), state property.
"""

import uuid
from typing import List, Dict

try:
    from ..models import IncidentAction, IncidentObservation, IncidentState
    from ..tasks  import TASKS, Task, grade
except ImportError:
    from models import IncidentAction, IncidentObservation, IncidentState
    from tasks  import TASKS, Task, grade

from openenv.core.env_server import Environment


VALID_ACTION_TYPES = {
    "diagnose", "restart_service", "scale_up", "rollback",
    "ignore", "alert_team", "inspect_logs", "kill_process",
    "clear_cache", "redeploy",
}

REWARD_CORRECT      =  0.99
REWARD_PARTIAL      =  0.3
REWARD_WRONG        = -0.2
REWARD_STEP_PENALTY = -0.05


class IncidentResponseEnvironment(Environment):
    """DevOps Incident Response OpenEnv environment."""

    def __init__(self) -> None:
        super().__init__()
        self._task_names: List[str] = list(TASKS.keys())
        self._task_index: int = 0
        self._task: Task = TASKS[self._task_names[0]]
        self._state = IncidentState()
        self._actions_taken: List[Dict[str, str]] = []

    # ── reset ──────────────────────────────────────────────────────────────

    def reset(self, task_name: str = None) -> IncidentObservation:
        if task_name and task_name in TASKS:
            self._task = TASKS[task_name]
        else:
            self._task = TASKS[self._task_names[self._task_index % len(self._task_names)]]
            self._task_index += 1

        self._actions_taken = []

        self._state = IncidentState(
            episode_id=str(uuid.uuid4()),
            step_count=0,
            task_name=self._task.name,
            difficulty=self._task.difficulty,
            root_cause=self._task.root_cause,
            correct_action=self._task.correct_action,
            correct_target=self._task.correct_target,
            actions_taken=[],
            cumulative_reward=0.0,
            max_steps=self._task.max_steps,
            grader_score=0.0,
        )

        return IncidentObservation(
            log_snippet=self._task.log_snippet,
            system_metrics=self._task.system_metrics,
            affected_services=self._task.affected_services,
            incident_status="open",
            feedback=(
                f"🚨 New incident — Task: '{self._task.name}' "
                f"[{self._task.difficulty.upper()}]. "
                f"Analyse the logs and metrics, then take action."
            ),
            task_name=self._task.name,
            step_number=0,
            done=False,
            reward=0.01,
        )

    # ── step ───────────────────────────────────────────────────────────────

    def step(self, action: IncidentAction) -> IncidentObservation:
        self._state.step_count += 1
        step_n = self._state.step_count

        # Validate action type
        if action.action_type not in VALID_ACTION_TYPES:
            reward = -0.3
            self._state.cumulative_reward += reward
            return IncidentObservation(
                log_snippet=self._task.log_snippet,
                system_metrics=self._task.system_metrics,
                affected_services=self._task.affected_services,
                incident_status="open",
                feedback=(
                    f"❌ Unknown action_type '{action.action_type}'. "
                    f"Valid: {sorted(VALID_ACTION_TYPES)}"
                ),
                task_name=self._task.name,
                step_number=step_n,
                done=False,
                reward=reward,
            )

        # Record action
        self._actions_taken.append({
            "action_type": action.action_type,
            "target":      action.target,
            "reasoning":   action.reasoning,
        })
        self._state.actions_taken.append(f"{action.action_type}:{action.target}")

        # Evaluate
        correct_action = self._task.correct_action
        correct_target = self._task.correct_target

        if action.action_type == correct_action and action.target == correct_target:
            reward          = max(round(REWARD_CORRECT + REWARD_STEP_PENALTY * (step_n - 1), 3), 0.01)
            reward = min(reward,0.99)

            done            = True
            incident_status = "resolved"
            feedback        = (
                f"✅ Correct! '{action.action_type}' on '{action.target}'. "
                f"Incident resolved in {step_n} step(s)."
            )

        elif action.action_type == correct_action:
            reward          = round(0.4 + REWARD_STEP_PENALTY * step_n, 3)
            done            = False
            incident_status = "open"
            feedback        = (
                f"🟡 Right action ('{action.action_type}') but wrong target "
                f"('{action.target}'). Re-examine which service is the root cause."
            )

        elif action.action_type in self._task.partial_actions:
            reward          = round(REWARD_PARTIAL + REWARD_STEP_PENALTY * step_n, 3)
            done            = False
            incident_status = "open"
            feedback        = (
                f"🔍 '{action.action_type}' is a reasonable investigative step. "
                f"Now determine the correct fix."
            )

        else:
            reward          = round(REWARD_WRONG + REWARD_STEP_PENALTY * step_n, 3)
            done            = False
            incident_status = "open"
            feedback        = (
                f"❌ '{action.action_type}' on '{action.target}' did not help. "
                f"Re-read the logs carefully."
            )

        self._state.cumulative_reward += reward

        # Max steps
        if not done and step_n >= self._task.max_steps:
            done            = True
            incident_status = "escalated"
            feedback       += (
                f"\n⏰ Max steps reached. Incident escalated. "
                f"Root cause was: {self._task.root_cause}"
            )

        if done:
            self._state.grader_score = grade(self._task, self._actions_taken)

        return IncidentObservation(
            log_snippet=self._task.log_snippet,
            system_metrics=self._task.system_metrics,
            affected_services=self._task.affected_services,
            incident_status=incident_status,
            feedback=feedback,
            task_name=self._task.name,
            step_number=step_n,
            done=done,
            reward=reward,
        )

    # ── state ──────────────────────────────────────────────────────────────

    @property
    def state(self) -> IncidentState:
        return self._state
