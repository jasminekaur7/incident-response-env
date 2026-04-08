"""
Inference Script — DevOps Incident Response Environment
========================================================
MANDATORY environment variables:
  API_BASE_URL   The API endpoint for the LLM.
  MODEL_NAME     The model identifier to use for inference.
  HF_TOKEN       Your Hugging Face / API key.

Run:
  API_BASE_URL=https://api.openai.com/v1 \
  MODEL_NAME=gpt-4o-mini \
  HF_TOKEN=hf_... \
  python inference.py
"""

import os
import sys
import json
import requests
from openai import OpenAI

# ---------------------------------------------------------------------------
# Configuration — read from environment (MANDATORY per competition rules)
# ---------------------------------------------------------------------------
API_BASE_URL = os.getenv("API_BASE_URL", "<your-active-endpoint>")
MODEL_NAME   = os.getenv("MODEL_NAME",   "<your-active-model>")
HF_TOKEN     = os.getenv("HF_TOKEN",     "")
ENV_BASE_URL = os.getenv("ENV_BASE_URL", "http://localhost:7860")

# ---------------------------------------------------------------------------
# OpenAI client (MUST use OpenAI client as per competition rules)
# ---------------------------------------------------------------------------
client = OpenAI(
    api_key=HF_TOKEN or "placeholder",
    base_url=API_BASE_URL,
)

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """\
You are a Senior Site Reliability Engineer (SRE) on an on-call shift.
You will receive server logs and system metrics showing a production incident.

Your job is to:
1. Analyse the logs and metrics carefully.
2. Identify the root cause.
3. Choose the single best remediation action.

Always respond with a JSON object containing exactly these keys:
{
  "action_type": "<one of: diagnose | restart_service | scale_up | rollback | ignore | alert_team | inspect_logs | kill_process | clear_cache | redeploy>",
  "target": "<name of the service or component to act on>",
  "reasoning": "<brief explanation of why>"
}

Do NOT include any text outside the JSON object.
"""


def call_llm(messages: list) -> dict:
    """Call the LLM via OpenAI client and parse JSON response."""
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        temperature=0.0,
        max_tokens=256,
    )
    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


def build_user_message(obs: dict) -> str:
    """Format observation into a user message for the LLM."""
    metrics_str = json.dumps(obs.get("system_metrics", {}), indent=2)
    services    = ", ".join(obs.get("affected_services", []))
    return (
        f"=== INCIDENT ALERT ===\n"
        f"Affected services: {services}\n\n"
        f"--- LOG SNIPPET ---\n{obs.get('log_snippet', '')}\n"
        f"--- SYSTEM METRICS ---\n{metrics_str}\n\n"
        f"Previous feedback: {obs.get('feedback', '')}\n\n"
        f"What is your diagnosis and remediation action?"
    )


def run_task(task_name: str, env_base_url: str) -> dict:
    """Run one full episode on the given task."""
    reset_resp = requests.post(
        f"{env_base_url}/reset",
        json={"task_name": task_name},
        timeout=30,
    )
    reset_resp.raise_for_status()
    obs = reset_resp.json().get("observation", reset_resp.json())

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    rewards  = []
    step_n   = 0
    done     = False

    # MANDATORY stdout format — [START]
    print(f"[START] task={task_name} env=incident-response-env model={MODEL_NAME}")
    sys.stdout.flush()

    while not done:
        step_n += 1
        user_msg = build_user_message(obs)
        messages.append({"role": "user", "content": user_msg})

        try:
            action_dict = call_llm(messages)
        except Exception as exc:
            action_dict = {
                "action_type": "diagnose",
                "target":      "unknown",
                "reasoning":   f"LLM parse error: {exc}",
            }

        messages.append({"role": "assistant", "content": json.dumps(action_dict)})

        step_resp = requests.post(
            f"{env_base_url}/step",
            json=action_dict,
            timeout=30,
        )
        step_resp.raise_for_status()
        result = step_resp.json()

        reward = result.get("reward", 0.0)
        done   = result.get("done", False)
        obs    = result.get("observation", {})
        rewards.append(reward)

        # MANDATORY stdout format — [STEP]
        print(
            f"[STEP]  step={step_n} "
            f"action={action_dict.get('action_type')} "
            f"reward={reward:.2f} "
            f"done={'true' if done else 'false'} "
            f"error=null"
        )
        sys.stdout.flush()

    # Fetch grader score from state
    state_resp   = requests.get(f"{env_base_url}/state", timeout=10)
    state        = state_resp.json() if state_resp.ok else {}
    grader_score = state.get("grader_score", 0.0)

    # MANDATORY stdout format — [END]
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(
        f"[END]   success={'true' if grader_score >= 0.8 else 'false'} "
        f"steps={step_n} "
        f"rewards={rewards_str}"
    )
    sys.stdout.flush()

    return {
        "task":         task_name,
        "steps":        step_n,
        "rewards":      rewards,
        "grader_score": grader_score,
    }


# ---------------------------------------------------------------------------
# Main — run all 3 tasks
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    tasks = [
        "cpu_spike_webserver",
        "memory_leak_cascade",
        "multi_service_outage_red_herring",
    ]

    results = []
    for task_name in tasks:
        try:
            result = run_task(task_name, ENV_BASE_URL)
            results.append(result)
        except Exception as exc:
            print(f"[ERROR] task={task_name} error={exc}", file=sys.stderr)
            results.append({"task": task_name, "grader_score": 0.0, "error": str(exc)})

    print("\n=== BASELINE SCORES ===")
    total = 0.0
    for r in results:
        score = r.get("grader_score", 0.0)
        total += score
        print(f"  {r['task']:<46} score={score:.2f}")
    print(f"  {'AVERAGE':<46} score={total / len(results):.2f}")