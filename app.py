import threading
import json
import time
import os
from flask import Flask, render_template, jsonify, request, Response, stream_with_context
from core.io_manager import IOManager
from config import MODEL_NAME, BASE_PROJECT_PATH, COMPANY_VAULT_PATH

app = Flask(__name__)

# ── Global State ──────────────────────────────────────────────
app_state = {
    "status": "idle",
    "project_name": "",
    "tasks": [],
    "agents": {
        "pm":       {"status": "waiting", "tasks_handled": 0, "output": "demand.txt"},
        "po":       {"status": "waiting", "tasks_handled": 0, "output": "tasks.json"},
        "analyst":  {"status": "waiting", "tasks_handled": 0, "output": "comments"},
        "developer":{"status": "waiting", "tasks_handled": 0, "output": "code"},
        "tester":   {"status": "waiting", "tasks_handled": 0, "output": "test results"},
    },
    "waiting_for_input": None,
    "user_response": None,
}

event_queue = []
queue_lock = threading.Lock()
input_event = threading.Event()


def push_event(data: dict):
    with queue_lock:
        event_queue.append(data)


def set_agent_status(agent_key: str, status: str):
    app_state["agents"][agent_key]["status"] = status
    push_event({"type": "agent_status", "agent": agent_key, "status": status})


def push_log(message: str):
    push_event({"type": "log", "message": message})


def push_task_progress(agent: str, index: int, total: int, task_id: str):
    push_event({"type": "task_progress", "agent": agent, "index": index, "total": total, "task_id": task_id})


def ask_user(question: str, input_type: str):
    app_state["status"] = "waiting_input"
    app_state["waiting_for_input"] = {"question": question, "type": input_type}
    app_state["user_response"] = None
    input_event.clear()
    push_event({"type": "waiting_input", "question": question, "input_type": input_type})
    push_log(f"⏸ Waiting for user input ({input_type})...")
    input_event.wait()
    response = app_state["user_response"]
    app_state["waiting_for_input"] = None
    app_state["status"] = "running"
    push_event({"type": "input_received"})
    push_log(f"▶ User responded, resuming pipeline...")
    return response


def run_pipeline_thread(project_name: str, customer_wish: str):
    try:
        app_state["status"] = "running"
        app_state["project_name"] = project_name
        for key in app_state["agents"]:
            app_state["agents"][key]["status"] = "waiting"
            app_state["agents"][key]["tasks_handled"] = 0

        push_log(f"Starting pipeline: {project_name}")

        from main import run_sdlc_simulation
        result = run_sdlc_simulation(
            project_name=project_name,
            initial_request=customer_wish,
            on_log=push_log,
            on_agent_status=set_agent_status,
            on_task_progress=push_task_progress,
            on_tasks_updated=lambda tasks: (
                app_state.__setitem__("tasks", tasks),
                push_event({"type": "tasks_updated", "tasks": tasks})
            ),
            on_ask_user=ask_user,
        )

        app_state["status"] = "finished"
        push_event({
            "type": "finished",
            "pass": result.get("pass", 0),
            "fail": result.get("fail", 0),
            "total": result.get("total", 0),
        })

    except Exception as e:
        app_state["status"] = "error"
        push_log(f"Pipeline error: {str(e)}")
        push_event({"type": "error", "message": str(e)})


# ── Routes ────────────────────────────────────────────────────
@app.route("/")
def dashboard():
    return render_template("dashboard.html", state=app_state)


@app.route("/agent/<key>")
def agent_page(key):
    if key not in app_state["agents"]:
        return "Agent not found", 404
    agent_names = {
        "pm": "Project Manager",
        "po": "Product Owner",
        "analyst": "System Analyst",
        "developer": "Developer",
        "tester": "Tester"
    }
    return render_template(
        "agent.html",
        agent_key=key,
        agent_name=agent_names.get(key, key.upper()),
        agent=app_state["agents"][key],
        tasks=app_state["tasks"],
        state=app_state
    )


@app.route("/api/state")
def api_state():
    return jsonify(app_state)


@app.route("/api/start", methods=["POST"])
def api_start():
    if app_state["status"] == "running":
        return jsonify({"error": "Pipeline already running"}), 400

    data = request.json
    project_name = data.get("project_name", "").strip()
    customer_wish = data.get("customer_wish", "").strip()
    if not project_name or not customer_wish:
        return jsonify({"error": "Missing project_name or customer_wish"}), 400

    with queue_lock:
        event_queue.clear()

    t = threading.Thread(target=run_pipeline_thread, args=(project_name, customer_wish), daemon=True)
    t.start()
    return jsonify({"ok": True})


@app.route("/api/respond", methods=["POST"])
def api_respond():
    if app_state["status"] != "waiting_input":
        return jsonify({"error": "Not waiting for input"}), 400
    data = request.json
    response = data.get("response", "").strip()
    if not response:
        return jsonify({"error": "Empty response"}), 400
    app_state["user_response"] = response
    input_event.set()
    return jsonify({"ok": True})


@app.route("/api/stream")
def api_stream():
    def generate():
        last_index = 0
        while True:
            with queue_lock:
                new_events = event_queue[last_index:]
                last_index = len(event_queue)

            for event in new_events:
                yield f"data: {json.dumps(event)}\n\n"

            if not new_events:
                yield f"data: {json.dumps({'type': 'ping'})}\n\n"

            if app_state["status"] in ("finished", "error") and not new_events:
                break

            time.sleep(0.5)

    return Response(stream_with_context(generate()),
                    content_type="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


if __name__ == "__main__":
    app.run(debug=False, threaded=True)