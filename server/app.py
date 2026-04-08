try:
    from ..models import IncidentAction, IncidentObservation
    from .incident_environment import IncidentResponseEnvironment
except ImportError:
    from models import IncidentAction, IncidentObservation
    from server.incident_environment import IncidentResponseEnvironment

from openenv.core.env_server import create_app

app = create_app(
    IncidentResponseEnvironment,
    IncidentAction,
    IncidentObservation,
    env_name="incident-response-env",
)