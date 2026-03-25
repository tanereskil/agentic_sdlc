import os
import json
import time
from core.agent import AIAgent
from core.io_manager import IOManager
from config import BASE_PROJECT_PATH, COMPANY_VAULT_PATH


# ── Dil → uzantı eşlemesi ────────────────────────────────────
LANG_EXTENSIONS = {
    "python": "py", "javascript": "js", "typescript": "ts",
    "java": "java", "go": "go", "rust": "rs", "kotlin": "kt",
    "swift": "swift", "php": "php", "ruby": "rb", "html": "html",
    "c#": "cs", "csharp": "cs", "c++": "cpp", "cpp": "cpp",
    "dart": "dart", "scala": "scala", "r": "r"
}

def detect_language(text):
    """Metinden programlama dilini tespit et, uzantısını döndür."""
    text_lower = text.lower()
    for lang, ext in LANG_EXTENSIONS.items():
        if lang in text_lower:
            return ext
    return "py"  # varsayılan


def clean_json_string(raw):
    """Strip markdown code fences and any leading text before JSON."""
    raw = raw.strip()
    # Markdown fence temizle
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
    if raw.endswith("```"):
        raw = raw.rsplit("\n", 1)[0]
    raw = raw.strip()
    # JSON başlamadan önce gelen metni temizle
    # [ veya { karakterini bul, oradan başlat
    for i, char in enumerate(raw):
        if char in ("[", "{"):
            raw = raw[i:]
            break
    return raw.strip()


def load_input(path=None):
    """Read project name and customer wish from a file."""
    if path is None:
        path = input("Input file path (press Enter for input.txt): ").strip()
        if not path:
            path = "input.txt"
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return "", ""
    content = open(path, "r", encoding="utf-8").read()
    project_name = ""
    customer_wish = ""
    for line in content.splitlines():
        if line.startswith("project_name:"):
            project_name = line.split(":", 1)[1].strip()
        elif line.startswith("customer_wish:"):
            customer_wish = line.split(":", 1)[1].strip()
    return project_name, customer_wish


def run_sdlc_simulation(
    project_name,
    initial_request,
    on_log=None,
    on_agent_status=None,
    on_task_progress=None,
    on_tasks_updated=None,
    on_ask_user=None,
):
    # ── Helpers ──────────────────────────────────────────────
    def log(msg):
        if on_log:
            on_log(msg)
        else:
            print(msg)

    def set_status(agent_key, status):
        if on_agent_status:
            on_agent_status(agent_key, status)

    def task_progress(agent, idx, total, task_id):
        if on_task_progress:
            on_task_progress(agent, idx, total, task_id)

    def tasks_updated(tasks):
        if on_tasks_updated:
            on_tasks_updated(tasks)

    def ask_user(question, input_type):
        if on_ask_user:
            return on_ask_user(question, input_type)
        else:
            prefix = "CLARIFICATION" if input_type == "clarification" else "BLOCKED"
            print(f"\n{prefix}: {question}")
            return input("Your answer: ").strip()

    # ── Setup ────────────────────────────────────────────────
    log(f"--- Starting SDLC Simulation: {project_name} ---")
    io = IOManager()
    project_path = io.create_project_structure(project_name)

    pm_agent      = AIAgent("Project Manager", "agents/pm_prompt.txt")
    po_agent      = AIAgent("Product Owner",   "agents/po_prompt.txt")
    analyst_agent = AIAgent("System Analyst",  "agents/analyst_prompt.txt")
    dev_agent     = AIAgent("Developer",       "agents/developer_prompt.txt")
    test_agent    = AIAgent("Tester",          "agents/tester_prompt.txt")

    company_context = ""
    for root, dirs, files in os.walk(COMPANY_VAULT_PATH):
        for file in files:
            if file.endswith(".txt") or file.endswith(".md"):
                company_context += io.read_file(os.path.join(root, file)) + "\n"

    start_time = time.time()

    # ── PHASE 1: PM ──────────────────────────────────────────
    log("\n[PM Phase] Analyzing customer demand...")
    set_status("pm", "active")

    current_request = initial_request

    for round_num in range(2):
        demand_raw = pm_agent.execute_task(current_request, company_context)

        if "CLARIFICATION_NEEDED:" in demand_raw:
            questions_part = demand_raw.replace("CLARIFICATION_NEEDED:", "").strip()
            questions = [q.strip() for q in questions_part.split("|") if q.strip()]
            question_text = "\n".join(f"- {q}" for q in questions)

            log(f"  PM asking clarification (round {round_num + 1})...")
            user_answer = ask_user(question_text, "clarification")

            current_request = (
                f"{current_request}\n\n"
                f"[Customer answers to PM - Round {round_num + 1}]\n"
                f"Questions:\n{question_text}\n\n"
                f"Answers:\n{user_answer}"
            )
        else:
            break

    io.write_file(f"{project_path}/demand.txt", demand_raw)
    set_status("pm", "done")
    log("✔ demand.txt created")

    # Dili demand.txt'den tespit et — tüm pipeline boyunca kullanılacak
    code_ext = detect_language(demand_raw + " " + initial_request)
    log(f"  Detected language extension: .{code_ext}")

    # ── PHASE 2: PO ──────────────────────────────────────────
    log("\n[PO Phase] Creating tasks from demand...")
    set_status("po", "active")

    tasks_raw = po_agent.execute_task(demand_raw, company_context)
    log(f"  PO raw response: {tasks_raw[:200] if tasks_raw else 'EMPTY'}")
    tasks_json_string = clean_json_string(tasks_raw)

    try:
        tasks = json.loads(tasks_json_string)
    except json.JSONDecodeError as e:
        log(f"PO JSON parse error: {e}")
        tasks = []

    if not tasks:
        log("No tasks generated, aborting.")
        return {"pass": 0, "fail": 0, "total": 0}

    io.write_file(f"{project_path}/tasks/001_project_tasks.json", json.dumps(tasks, indent=4))
    tasks_updated(tasks)
    set_status("po", "done")
    log(f"✔ {len(tasks)} tasks created")

    # ── PHASE 3: Analyst ─────────────────────────────────────
    log("\n[Analyst Phase] Performing technical analysis per task...")
    set_status("analyst", "active")

    for i, task in enumerate(tasks):
        task_progress("analyst", i, len(tasks), task["id"])
        log(f"  Analyst -> [{i+1}/{len(tasks)}] {task['id']} - {task['title']}")
        time.sleep(2)

        task_input = json.dumps(task)
        analyst_raw = analyst_agent.execute_task(task_input, company_context)

        try:
            analyst_comment = json.loads(clean_json_string(analyst_raw))
        except json.JSONDecodeError:
            analyst_comment = {"author": "analyst", "content": analyst_raw, "assigned_to": "developer"}

        # Escalation: Analyst -> PO
        if "ESCALATE_TO_PO:" in analyst_comment.get("content", ""):
            reason = analyst_comment["content"].replace("ESCALATE_TO_PO:", "").strip()
            log(f"  ^ Analyst escalating to PO: {reason}")

            po_response_raw = po_agent.execute_task(
                f"{task_input}\n\n[Analyst needs PO clarification]: {reason}",
                company_context
            )
            try:
                po_response = json.loads(clean_json_string(po_response_raw))
            except json.JSONDecodeError:
                po_response = {"author": "po", "content": po_response_raw}

            task.setdefault("comments", []).append(po_response)
            log(f"  v PO responded, re-running analyst...")

            analyst_raw = analyst_agent.execute_task(
                f"{task_input}\n\n[PO clarification]: {po_response.get('content', '')}",
                company_context
            )
            try:
                analyst_comment = json.loads(clean_json_string(analyst_raw))
            except json.JSONDecodeError:
                analyst_comment = {"author": "analyst", "content": analyst_raw, "assigned_to": "developer"}

            # Escalation: PO -> PM
            if "ESCALATE_TO_PO:" in analyst_comment.get("content", "") or \
               "ESCALATE_TO_PM:" in analyst_comment.get("content", ""):
                reason2 = analyst_comment["content"].split(":", 1)[-1].strip()
                log(f"  ^ PO escalating to PM: {reason2}")

                pm_response_raw = pm_agent.execute_task(
                    f"{task_input}\n\n[PO needs PM clarification]: {reason2}",
                    company_context
                )
                task.setdefault("comments", []).append({
                    "author": "pm", "content": pm_response_raw, "assigned_to": "analyst"
                })
                log(f"  v PM responded, re-running analyst...")

                if "CLARIFICATION_NEEDED:" in pm_response_raw:
                    question = pm_response_raw.replace("CLARIFICATION_NEEDED:", "").strip()
                    log(f"  ^ PM escalating to customer for task {task['id']}")
                    user_answer = ask_user(question, "clarification")
                    enriched = f"{task_input}\n\n[Customer additional info]: {user_answer}"
                else:
                    enriched = f"{task_input}\n\n[PM clarification]: {pm_response_raw}"

                analyst_raw = analyst_agent.execute_task(enriched, company_context)
                try:
                    analyst_comment = json.loads(clean_json_string(analyst_raw))
                except json.JSONDecodeError:
                    analyst_comment = {"author": "analyst", "content": analyst_raw, "assigned_to": "developer"}

        task.setdefault("comments", []).append(analyst_comment)
        task["assigned_to"] = analyst_comment.get("assigned_to", "developer")
        tasks_updated(tasks)

    set_status("analyst", "done")
    log("✔ Analysis complete")

    # ── PHASE 4: Developer ───────────────────────────────────
    log("\n[Developer Phase] Writing code per task...")
    set_status("developer", "active")

    for i, task in enumerate(tasks):
        task_progress("developer", i, len(tasks), task["id"])
        log(f"  Developer -> [{i+1}/{len(tasks)}] {task['id']}")
        time.sleep(2)

        dev_raw = dev_agent.execute_task(json.dumps(task), company_context)
        try:
            dev_comment = json.loads(clean_json_string(dev_raw))
        except json.JSONDecodeError:
            dev_comment = {"author": "developer", "content": dev_raw, "code": "", "assigned_to": "tester"}

        # Escalation: Developer -> Analyst
        if "ESCALATE_TO_ANALYST:" in dev_comment.get("content", ""):
            reason = dev_comment["content"].replace("ESCALATE_TO_ANALYST:", "").strip()
            log(f"  ^ Developer escalating to Analyst: {reason}")

            analyst_response_raw = analyst_agent.execute_task(
                f"{json.dumps(task)}\n\n[Developer needs clarification]: {reason}",
                company_context
            )
            try:
                analyst_response = json.loads(clean_json_string(analyst_response_raw))
            except json.JSONDecodeError:
                analyst_response = {"author": "analyst", "content": analyst_response_raw, "assigned_to": "developer"}

            task.setdefault("comments", []).append(analyst_response)
            log(f"  v Analyst responded, re-running developer...")

            dev_raw = dev_agent.execute_task(json.dumps(task), company_context)
            try:
                dev_comment = json.loads(clean_json_string(dev_raw))
            except json.JSONDecodeError:
                dev_comment = {"author": "developer", "content": dev_raw, "code": "", "assigned_to": "tester"}

        code = dev_comment.get("code", "")
        if code:
            # Uzantıyı developer comment'inden veya demand'dan tespit et
            comment_ext = detect_language(dev_comment.get("content", ""))
            final_ext = comment_ext if comment_ext != "py" else code_ext
            io.write_file(f"{project_path}/codes/{task['id']}_code.{final_ext}", code)
            log(f"    Code saved as .{final_ext}")

        task["comments"].append(dev_comment)
        task["assigned_to"] = dev_comment.get("assigned_to", "tester")
        tasks_updated(tasks)

    set_status("developer", "done")
    log("✔ Code generation complete")

    # ── PHASE 5: Tester ──────────────────────────────────────
    log("\n[Tester Phase] Testing per task...")
    set_status("tester", "active")

    pass_count = 0
    fail_count = 0

    for i, task in enumerate(tasks):
        task_progress("tester", i, len(tasks), task["id"])
        log(f"  Tester -> [{i+1}/{len(tasks)}] {task['id']}")
        time.sleep(2)

        test_raw = test_agent.execute_task(json.dumps(task), company_context)
        try:
            test_comment = json.loads(clean_json_string(test_raw))
        except json.JSONDecodeError:
            test_comment = {"author": "tester", "content": test_raw, "status": "FAIL", "assigned_to": "developer"}

        task["comments"].append(test_comment)
        test_status = test_comment.get("status", "FAIL")
        assigned_to = test_comment.get("assigned_to", "developer")

        if test_status == "PASS":
            pass_count += 1
            task["assigned_to"] = "closed"
            log(f"    PASS: {task['id']}")

        elif assigned_to == "analyst" or "ESCALATE_TO_ANALYST:" in test_comment.get("content", ""):
            reason = test_comment["content"].replace("ESCALATE_TO_ANALYST:", "").strip()
            log(f"  ^ Tester escalating to Analyst (spec issue): {reason}")
            fail_count += 1

            analyst_fix_raw = analyst_agent.execute_task(
                f"{json.dumps(task)}\n\n[Tester found spec issue]: {reason}",
                company_context
            )
            try:
                analyst_fix = json.loads(clean_json_string(analyst_fix_raw))
            except json.JSONDecodeError:
                analyst_fix = {"author": "analyst", "content": analyst_fix_raw, "assigned_to": "closed"}

            analyst_fix["assigned_to"] = "closed"
            task["comments"].append(analyst_fix)
            task["assigned_to"] = "closed"
            log(f"  v Analyst addressed spec issue, task closed")

        else:
            fail_count += 1
            log(f"    FAIL: {task['id']} -> sending back to developer")
            time.sleep(2)

            dev_review_raw = dev_agent.execute_task(json.dumps(task), company_context)
            try:
                dev_review = json.loads(clean_json_string(dev_review_raw))
            except json.JSONDecodeError:
                dev_review = {"author": "developer", "content": dev_review_raw, "code": "", "assigned_to": "analyst"}

            task["comments"].append(dev_review)
            log(f"  ^ Developer reviewed failure, escalating to Analyst")
            time.sleep(2)

            analyst_defense_raw = analyst_agent.execute_task(json.dumps(task), company_context)
            try:
                analyst_defense = json.loads(clean_json_string(analyst_defense_raw))
            except json.JSONDecodeError:
                analyst_defense = {"author": "analyst", "content": analyst_defense_raw, "assigned_to": "closed"}


            analyst_defense["assigned_to"] = "closed"
            task["comments"].append(analyst_defense)
            task["assigned_to"] = "closed"
            log(f"  v Analyst defense complete, task closed")

        tasks_updated(tasks)

    io.save_json(f"{project_path}/tasks/001_project_tasks.json", tasks)
    set_status("tester", "done")

    elapsed = round(time.time() - start_time, 1)
    log(f"\n--- Pipeline Finished in {elapsed}s | PASS: {pass_count} | FAIL: {fail_count} | Total: {len(tasks)} ---")

    return {"pass": pass_count, "fail": fail_count, "total": len(tasks)}


if __name__ == "__main__":
    target_project, customer_wish = load_input()
    print(f"Project: {target_project}")
    print(f"Request: {customer_wish}")
    run_sdlc_simulation(target_project, customer_wish)