"""
incident_response_env — tasks.py
Defines 3 tasks (easy / medium / hard) with deterministic graders.
Each grader returns a float in [0.0, 1.0].
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any


# ---------------------------------------------------------------------------
# Task dataclass
# ---------------------------------------------------------------------------

@dataclass
class Task:
    name: str
    difficulty: str          # easy | medium | hard
    description: str
    log_snippet: str
    system_metrics: Dict[str, Any]
    affected_services: List[str]
    root_cause: str
    correct_action: str      # action_type that fully resolves the incident
    correct_target: str      # target that fully resolves the incident
    partial_actions: List[str]   # actions that earn partial credit
    max_steps: int = 5


# ---------------------------------------------------------------------------
# Task 1 — EASY: CPU spike on web-server
# ---------------------------------------------------------------------------

TASK_EASY = Task(
    name="cpu_spike_webserver",
    difficulty="easy",
    description=(
        "A single web-server pod is pegged at 99 % CPU. "
        "Response times have degraded but the service is still up. "
        "Identify the cause and take the correct remediation action."
    ),
    log_snippet="""\
[2025-04-01 03:12:01] web-server-1  INFO  Request received: GET /api/products
[2025-04-01 03:12:01] web-server-1  WARN  CPU usage: 99%
[2025-04-01 03:12:02] web-server-1  ERROR loop detected in product_catalog.handle_request()
[2025-04-01 03:12:02] web-server-1  ERROR Traceback: RecursionError: maximum recursion depth exceeded
[2025-04-01 03:12:03] web-server-1  WARN  CPU usage: 99%  response_time=4800ms
[2025-04-01 03:12:04] web-server-1  WARN  CPU usage: 99%  response_time=5200ms
[2025-04-01 03:12:05] load-balancer INFO  Marking web-server-1 as degraded
""",
    system_metrics={
        "web-server-1": {"cpu_pct": 99, "mem_pct": 42, "error_rate": 0.87, "latency_ms": 5200},
        "db-primary":   {"cpu_pct": 18, "mem_pct": 55, "error_rate": 0.00, "latency_ms": 12},
    },
    affected_services=["web-server-1"],
    root_cause="infinite recursion loop in product_catalog.handle_request()",
    correct_action="restart_service",
    correct_target="web-server-1",
    partial_actions=["inspect_logs", "diagnose", "alert_team", "kill_process"],
    max_steps=5,
)


# ---------------------------------------------------------------------------
# Task 2 — MEDIUM: Memory leak cascading into queue backup
# ---------------------------------------------------------------------------

TASK_MEDIUM = Task(
    name="memory_leak_cascade",
    difficulty="medium",
    description=(
        "The order-processing service is leaking memory. "
        "As it slows down, the message queue is backing up, "
        "causing downstream payment-service timeouts. "
        "Multiple services are affected — find the root cause and fix it."
    ),
    log_snippet="""\
[2025-04-01 08:00:10] order-processor  WARN  Heap usage 78% (threshold 70%)
[2025-04-01 08:05:22] order-processor  WARN  Heap usage 89%
[2025-04-01 08:10:44] order-processor  ERROR GC overhead limit exceeded
[2025-04-01 08:10:45] message-queue    WARN  Queue depth: 4200 (normal < 200)
[2025-04-01 08:10:50] payment-service  ERROR Timeout waiting for order-processor (30 s)
[2025-04-01 08:10:51] payment-service  ERROR Timeout waiting for order-processor (30 s)
[2025-04-01 08:11:00] payment-service  ERROR Circuit breaker OPEN — order-processor unreachable
[2025-04-01 08:11:05] order-processor  ERROR OutOfMemoryError: Java heap space
[2025-04-01 08:11:05] order-processor  ERROR Service crashed — PID 4419 terminated
[2025-04-01 08:11:10] message-queue    WARN  Queue depth: 6800 — producers blocked
""",
    system_metrics={
        "order-processor": {"cpu_pct": 14, "mem_pct": 99, "error_rate": 1.0,  "latency_ms": 0},
        "message-queue":   {"cpu_pct": 45, "mem_pct": 61, "error_rate": 0.12, "latency_ms": 800},
        "payment-service": {"cpu_pct": 22, "mem_pct": 38, "error_rate": 0.95, "latency_ms": 30100},
        "db-primary":      {"cpu_pct": 20, "mem_pct": 52, "error_rate": 0.00, "latency_ms": 15},
    },
    affected_services=["order-processor", "message-queue", "payment-service"],
    root_cause="memory leak in order-processor causing OOM crash and queue backup",
    correct_action="restart_service",
    correct_target="order-processor",
    partial_actions=["inspect_logs", "diagnose", "scale_up", "alert_team", "redeploy"],
    max_steps=6,
)


# ---------------------------------------------------------------------------
# Task 3 — HARD: Multi-service outage with red herrings
# ---------------------------------------------------------------------------

TASK_HARD = Task(
    name="multi_service_outage_red_herring",
    difficulty="hard",
    description=(
        "A database failover event triggered a cascade. "
        "Multiple services are logging errors at the same time, "
        "including misleading timeout errors in the API gateway and "
        "a coincidental (unrelated) disk warning on a backup server. "
        "Identify the actual root cause and apply the correct fix."
    ),
    log_snippet="""\
[2025-04-01 14:00:01] backup-server    WARN  Disk usage 91% on /mnt/backups (non-critical)
[2025-04-01 14:00:05] db-replica-2     ERROR Replication lag: 9800 ms
[2025-04-01 14:00:06] db-primary       ERROR Failover initiated — promoting db-replica-1
[2025-04-01 14:00:07] api-gateway      ERROR Connection pool exhausted — all DB connections waiting
[2025-04-01 14:00:08] auth-service     ERROR DB query timeout after 5000ms
[2025-04-01 14:00:08] user-service     ERROR DB query timeout after 5000ms
[2025-04-01 14:00:09] api-gateway      ERROR 503 Service Unavailable — auth-service not responding
[2025-04-01 14:00:09] api-gateway      ERROR 503 Service Unavailable — user-service not responding
[2025-04-01 14:00:10] db-replica-1     INFO  Promotion complete — now accepting writes
[2025-04-01 14:00:11] auth-service     WARN  Retrying DB connection (attempt 1/5)
[2025-04-01 14:00:13] auth-service     WARN  Retrying DB connection (attempt 2/5)
[2025-04-01 14:00:15] auth-service     INFO  DB connection restored — resuming normal operation
[2025-04-01 14:00:15] user-service     INFO  DB connection restored — resuming normal operation
[2025-04-01 14:00:16] api-gateway      WARN  Connection pool still recovering (28 % free)
[2025-04-01 14:00:20] api-gateway      INFO  Connection pool healthy (94 % free)
""",
    system_metrics={
        "db-primary":    {"cpu_pct": 0,  "mem_pct": 0,  "error_rate": 1.0,  "latency_ms": 0},
        "db-replica-1":  {"cpu_pct": 55, "mem_pct": 62, "error_rate": 0.02, "latency_ms": 22},
        "api-gateway":   {"cpu_pct": 71, "mem_pct": 49, "error_rate": 0.61, "latency_ms": 4800},
        "auth-service":  {"cpu_pct": 30, "mem_pct": 44, "error_rate": 0.40, "latency_ms": 3200},
        "user-service":  {"cpu_pct": 28, "mem_pct": 41, "error_rate": 0.38, "latency_ms": 3100},
        "backup-server": {"cpu_pct": 5,  "mem_pct": 35, "error_rate": 0.00, "latency_ms": 0},
    },
    affected_services=["db-primary", "api-gateway", "auth-service", "user-service"],
    root_cause="db-primary failover — transient outage while replica-1 was promoted",
    correct_action="rollback",
    correct_target="db-primary",
    partial_actions=["inspect_logs", "diagnose", "alert_team", "redeploy"],
    max_steps=7,
)


TASKS: Dict[str, Task] = {
    "cpu_spike_webserver":             TASK_EASY,
    "memory_leak_cascade":             TASK_MEDIUM,
    "multi_service_outage_red_herring": TASK_HARD,
}


# ---------------------------------------------------------------------------
# Grader
# ---------------------------------------------------------------------------

"""
incident_response_env — tasks.py
Defines 3 tasks (easy / medium / hard) with deterministic graders.
Each grader returns a float in [0.0, 1.0].
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any


# ---------------------------------------------------------------------------
# Task dataclass
# ---------------------------------------------------------------------------

@dataclass
class Task:
    name: str
    difficulty: str          # easy | medium | hard
    description: str
    log_snippet: str
    system_metrics: Dict[str, Any]
    affected_services: List[str]
    root_cause: str
    correct_action: str      # action_type that fully resolves the incident
    correct_target: str      # target that fully resolves the incident
    partial_actions: List[str]   # actions that earn partial credit
    max_steps: int = 5


# ---------------------------------------------------------------------------
# Task 1 — EASY: CPU spike on web-server
# ---------------------------------------------------------------------------

TASK_EASY = Task(
    name="cpu_spike_webserver",
    difficulty="easy",
    description=(
        "A single web-server pod is pegged at 99 % CPU. "
        "Response times have degraded but the service is still up. "
        "Identify the cause and take the correct remediation action."
    ),
    log_snippet="""\
[2025-04-01 03:12:01] web-server-1  INFO  Request received: GET /api/products
[2025-04-01 03:12:01] web-server-1  WARN  CPU usage: 99%
[2025-04-01 03:12:02] web-server-1  ERROR loop detected in product_catalog.handle_request()
[2025-04-01 03:12:02] web-server-1  ERROR Traceback: RecursionError: maximum recursion depth exceeded
[2025-04-01 03:12:03] web-server-1  WARN  CPU usage: 99%  response_time=4800ms
[2025-04-01 03:12:04] web-server-1  WARN  CPU usage: 99%  response_time=5200ms
[2025-04-01 03:12:05] load-balancer INFO  Marking web-server-1 as degraded
""",
    system_metrics={
        "web-server-1": {"cpu_pct": 99, "mem_pct": 42, "error_rate": 0.87, "latency_ms": 5200},
        "db-primary":   {"cpu_pct": 18, "mem_pct": 55, "error_rate": 0.00, "latency_ms": 12},
    },
    affected_services=["web-server-1"],
    root_cause="infinite recursion loop in product_catalog.handle_request()",
    correct_action="restart_service",
    correct_target="web-server-1",
    partial_actions=["inspect_logs", "diagnose", "alert_team", "kill_process"],
    max_steps=5,
)


# ---------------------------------------------------------------------------
# Task 2 — MEDIUM: Memory leak cascading into queue backup
# ---------------------------------------------------------------------------

TASK_MEDIUM = Task(
    name="memory_leak_cascade",
    difficulty="medium",
    description=(
        "The order-processing service is leaking memory. "
        "As it slows down, the message queue is backing up, "
        "causing downstream payment-service timeouts. "
        "Multiple services are affected — find the root cause and fix it."
    ),
    log_snippet="""\
[2025-04-01 08:00:10] order-processor  WARN  Heap usage 78% (threshold 70%)
[2025-04-01 08:05:22] order-processor  WARN  Heap usage 89%
[2025-04-01 08:10:44] order-processor  ERROR GC overhead limit exceeded
[2025-04-01 08:10:45] message-queue    WARN  Queue depth: 4200 (normal < 200)
[2025-04-01 08:10:50] payment-service  ERROR Timeout waiting for order-processor (30 s)
[2025-04-01 08:10:51] payment-service  ERROR Timeout waiting for order-processor (30 s)
[2025-04-01 08:11:00] payment-service  ERROR Circuit breaker OPEN — order-processor unreachable
[2025-04-01 08:11:05] order-processor  ERROR OutOfMemoryError: Java heap space
[2025-04-01 08:11:05] order-processor  ERROR Service crashed — PID 4419 terminated
[2025-04-01 08:11:10] message-queue    WARN  Queue depth: 6800 — producers blocked
""",
    system_metrics={
        "order-processor": {"cpu_pct": 14, "mem_pct": 99, "error_rate": 1.0,  "latency_ms": 0},
        "message-queue":   {"cpu_pct": 45, "mem_pct": 61, "error_rate": 0.12, "latency_ms": 800},
        "payment-service": {"cpu_pct": 22, "mem_pct": 38, "error_rate": 0.95, "latency_ms": 30100},
        "db-primary":      {"cpu_pct": 20, "mem_pct": 52, "error_rate": 0.00, "latency_ms": 15},
    },
    affected_services=["order-processor", "message-queue", "payment-service"],
    root_cause="memory leak in order-processor causing OOM crash and queue backup",
    correct_action="restart_service",
    correct_target="order-processor",
    partial_actions=["inspect_logs", "diagnose", "scale_up", "alert_team", "redeploy"],
    max_steps=6,
)


# ---------------------------------------------------------------------------
# Task 3 — HARD: Multi-service outage with red herrings
# ---------------------------------------------------------------------------

TASK_HARD = Task(
    name="multi_service_outage_red_herring",
    difficulty="hard",
    description=(
        "A database failover event triggered a cascade. "
        "Multiple services are logging errors at the same time, "
        "including misleading timeout errors in the API gateway and "
        "a coincidental (unrelated) disk warning on a backup server. "
        "Identify the actual root cause and apply the correct fix."
    ),
    log_snippet="""\
[2025-04-01 14:00:01] backup-server    WARN  Disk usage 91% on /mnt/backups (non-critical)
[2025-04-01 14:00:05] db-replica-2     ERROR Replication lag: 9800 ms
[2025-04-01 14:00:06] db-primary       ERROR Failover initiated — promoting db-replica-1
[2025-04-01 14:00:07] api-gateway      ERROR Connection pool exhausted — all DB connections waiting
[2025-04-01 14:00:08] auth-service     ERROR DB query timeout after 5000ms
[2025-04-01 14:00:08] user-service     ERROR DB query timeout after 5000ms
[2025-04-01 14:00:09] api-gateway      ERROR 503 Service Unavailable — auth-service not responding
[2025-04-01 14:00:09] api-gateway      ERROR 503 Service Unavailable — user-service not responding
[2025-04-01 14:00:10] db-replica-1     INFO  Promotion complete — now accepting writes
[2025-04-01 14:00:11] auth-service     WARN  Retrying DB connection (attempt 1/5)
[2025-04-01 14:00:13] auth-service     WARN  Retrying DB connection (attempt 2/5)
[2025-04-01 14:00:15] auth-service     INFO  DB connection restored — resuming normal operation
[2025-04-01 14:00:15] user-service     INFO  DB connection restored — resuming normal operation
[2025-04-01 14:00:16] api-gateway      WARN  Connection pool still recovering (28 % free)
[2025-04-01 14:00:20] api-gateway      INFO  Connection pool healthy (94 % free)
""",
    system_metrics={
        "db-primary":    {"cpu_pct": 0,  "mem_pct": 0,  "error_rate": 1.0,  "latency_ms": 0},
        "db-replica-1":  {"cpu_pct": 55, "mem_pct": 62, "error_rate": 0.02, "latency_ms": 22},
        "api-gateway":   {"cpu_pct": 71, "mem_pct": 49, "error_rate": 0.61, "latency_ms": 4800},
        "auth-service":  {"cpu_pct": 30, "mem_pct": 44, "error_rate": 0.40, "latency_ms": 3200},
        "user-service":  {"cpu_pct": 28, "mem_pct": 41, "error_rate": 0.38, "latency_ms": 3100},
        "backup-server": {"cpu_pct": 5,  "mem_pct": 35, "error_rate": 0.00, "latency_ms": 0},
    },
    affected_services=["db-primary", "api-gateway", "auth-service", "user-service"],
    root_cause="db-primary failover — transient outage while replica-1 was promoted",
    correct_action="rollback",
    correct_target="db-primary",
    partial_actions=["inspect_logs", "diagnose", "alert_team", "redeploy"],
    max_steps=7,
)


TASKS: Dict[str, Task] = {
    "cpu_spike_webserver":             TASK_EASY,
    "memory_leak_cascade":             TASK_MEDIUM,
    "multi_service_outage_red_herring": TASK_HARD,
}


# ---------------------------------------------------------------------------
# Grader
# ---------------------------------------------------------------------------

def grade(task: Task, actions_taken: List[Dict[str, str]]) -> float:
    """
    Deterministic grader. Returns score STRICTLY in (0.0, 1.0).
    Never returns exactly 0.0 or 1.0 as per competition requirements.

    0.95  — correct action_type AND correct target
    0.75  — correct action_type but wrong target
    0.40  — only partial / investigative actions
    0.10  — at least one action taken
    0.05  — no actions taken (minimum non-zero)
    """
    if not actions_taken:
        return 0.05

    action_types = [a.get("action_type", "") for a in actions_taken]
    targets      = [a.get("target", "")      for a in actions_taken]

    for at, tgt in zip(action_types, targets):
        if at == task.correct_action and tgt == task.correct_target:
            return 0.95

    if task.correct_action in action_types:
        return 0.75

    if any(at in task.partial_actions for at in action_types):
        return 0.40

    return 0.10
