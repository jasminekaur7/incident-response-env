from openenv.core.env_client import EnvClient
from openenv.core.client_types import StepResult

try:
    from .models import IncidentAction, IncidentObservation, IncidentState
except ImportError:
    from models import IncidentAction, IncidentObservation, IncidentState


class IncidentResponseEnv(EnvClient[IncidentAction, IncidentObservation, IncidentState]):

    def _step_payload(self, action: IncidentAction) -> dict:
        return {"action_type": action.action_type, "target": action.target, "reasoning": action.reasoning}

    def _parse_result(self, payload: dict) -> StepResult[IncidentObservation]:
        obs_data = payload.get("observation", {})
        obs = IncidentObservation(
            log_snippet=obs_data.get("log_snippet", ""),
            system_metrics=obs_data.get("system_metrics", {}),
            affected_services=obs_data.get("affected_services", []),
            incident_status=obs_data.get("incident_status", "open"),
            feedback=obs_data.get("feedback", ""),
            task_name=obs_data.get("task_name", ""),
            step_number=obs_data.get("step_number", 0),
            done=payload.get("done", False),
            reward=payload.get("reward"),
        )
        return StepResult(observation=obs, reward=payload.get("reward"), done=payload.get("done", False))

    def _parse_state(self, payload: dict) -> IncidentState:
        return IncidentState(
            episode_id=payload.get("episode_id"),
            step_count=payload.get("step_count", 0),
            task_name=payload.get("task_name", ""),
            difficulty=payload.get("difficulty", "easy"),
            root_cause=payload.get("root_cause", ""),
            correct_action=payload.get("correct_action", ""),
            correct_target=payload.get("correct_target", ""),
            actions_taken=payload.get("actions_taken", []),
            cumulative_reward=payload.get("cumulative_reward", 0.0),
            max_steps=payload.get("max_steps", 5),
            grader_score=payload.get("grader_score", 0.0),
        )