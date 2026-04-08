"""
Incident Response Environment — models.py
Typed Pydantic models for Action, Observation, and State.
"""

from typing import Optional, List, Dict, Any
from pydantic import Field
from openenv.core.env_server.types import Action, Observation, State


class IncidentAction(Action):
    action_type: str = Field(..., description="One of: diagnose, restart_service, scale_up, rollback, ignore, alert_team, inspect_logs, kill_process, clear_cache, redeploy")
    target: str = Field(default="", description="Service or component to act on")
    reasoning: str = Field(default="", description="Why this action was chosen")


class IncidentObservation(Observation):
    log_snippet: str = Field(..., description="Raw log lines from the incident")
    system_metrics: Dict[str, Any] = Field(default_factory=dict)
    affected_services: List[str] = Field(default_factory=list)
    incident_status: str = Field(default="open")
    feedback: str = Field(default="")
    task_name: str = Field(default="")
    step_number: int = Field(default=0)
    done: bool = Field(default=False)
    reward: Optional[float] = Field(default=None)


class IncidentState(State):
    task_name: str = Field(default="")
    difficulty: str = Field(default="easy")
    root_cause: str = Field(default="")
    correct_action: str = Field(default="")
    correct_target: str = Field(default="")
    actions_taken: List[str] = Field(default_factory=list)
    cumulative_reward: float = Field(default=0.0)
    max_steps: int = Field(default=5)
    grader_score: float = Field(default=0.0)