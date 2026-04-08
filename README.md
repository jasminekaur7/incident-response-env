# 🚨 DevOps Incident Response — OpenEnv Environment

A real-world SRE/DevOps environment where an AI agent diagnoses production
incidents from server logs and system metrics, then applies the correct
remediation action.

## Tasks

| Task                               | Difficulty | Description                                 |
| ---------------------------------- | ---------- | ------------------------------------------- |
| `cpu_spike_webserver`              | 🟢 Easy    | Single service CPU spike — clear log signal |
| `memory_leak_cascade`              | 🟡 Medium  | Memory leak cascading across 3 services     |
| `multi_service_outage_red_herring` | 🔴 Hard    | DB failover + misleading red herrings       |

## Action Space

`diagnose` · `restart_service` · `scale_up` · `rollback` · `ignore` ·
`alert_team` · `inspect_logs` · `kill_process` · `clear_cache` · `redeploy`

## Observation Space

| Field               | Type   | Description                                       |
| ------------------- | ------ | ------------------------------------------------- |
| `log_snippet`       | string | Timestamped server log lines                      |
| `system_metrics`    | object | Per-service CPU%, memory%, error_rate, latency_ms |
| `affected_services` | list   | Services showing anomalies                        |
| `incident_status`   | string | open / mitigated / resolved / escalated           |
| `feedback`          | string | Natural-language feedback on last action          |

## Reward Function

| Outcome                         | Reward              |
| ------------------------------- | ------------------- |
| Correct action + correct target | 1.0 − 0.05×(step−1) |
| Correct action, wrong target    | 0.4 − 0.05×step     |
| Investigative action            | 0.3 − 0.05×step     |
| Unhelpful action                | −0.2 − 0.05×step    |

## Setup

```bash
pip install openenv-core fastapi uvicorn pydantic
uvicorn server.app:app --host 0.0.0.0 --port 7860
```

## Docker

```bash
docker build -t incident-response-env -f server/Dockerfile .
docker run -p 7860:7860 incident-response-env
```

## Baseline Inference

```bash
export API_BASE_URL=https://api.openai.com/v1
export MODEL_NAME=gpt-4o-mini
export HF_TOKEN=hf_your_token
export ENV_BASE_URL=http://localhost:7860
python inference.py
```

## Baseline Scores

| Task                             | Score    |
| -------------------------------- | -------- |
| cpu_spike_webserver              | 0.95     |
| memory_leak_cascade              | 0.70     |
| multi_service_outage_red_herring | 0.45     |
| **Average**                      | **0.70** |
