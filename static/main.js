// ── Sidebar ──
function toggleSidebar() {
    const sidebar = document.getElementById("sidebar");
    const overlay = document.getElementById("overlay");
    sidebar.classList.toggle("open");
    overlay.classList.toggle("show");
}

// ── SSE Connection ──
function connectSSE() {
    const evtSource = new EventSource("/api/stream");

    evtSource.onmessage = (e) => {
        const data = JSON.parse(e.data);
        handleEvent(data);
    };

    evtSource.onerror = () => {
        console.log("SSE connection closed.");
        evtSource.close();
    };
}

function handleEvent(data) {
    switch (data.type) {
        case "log":
            appendLog(data.message);
            break;
        case "agent_status":
            updateAgentStatus(data.agent, data.status);
            break;
        case "tasks_updated":
            updateTaskCount(data.tasks);
            break;
        case "task_progress":
            updateTaskProgress(data);
            break;
        case "finished":
            onFinished(data);
            break;
        case "ping":
            break;
    }
}

// ── Log ──
function appendLog(message) {
    const container = document.getElementById("logContainer");
    if (!container) return;
    const line = document.createElement("div");
    line.className = "log-line";
    line.textContent = message;
    container.appendChild(line);
    container.scrollTop = container.scrollHeight;
}

// ── Agent Status ──
function updateAgentStatus(agentKey, status) {
    const dot = document.getElementById(`dot-${agentKey}`);
    if (dot) dot.className = `status-dot status-${status}`;

    const card = document.getElementById(`card-${agentKey}`);
    const indicator = document.getElementById(`indicator-${agentKey}`);
    const statusText = document.getElementById(`status-text-${agentKey}`);

    if (card) {
        card.classList.remove("waiting-card", "active-card", "done-card", "error-card");
        card.classList.add(`${status}-card`);
    }
    if (indicator) {
        indicator.className = `agent-indicator ${status}`;
    }
    if (statusText) {
        statusText.className = `agent-status-text ${status}`;
        statusText.textContent = status.toUpperCase();
    }

    const sidebarStatus = document.getElementById("sidebar-status");
    if (sidebarStatus) sidebarStatus.textContent = status.toUpperCase();

    const badge = document.getElementById("pipeline-status-badge");
    if (badge) {
        badge.className = `status-badge status-running`;
        badge.textContent = "RUNNING";
    }
}

// ── Task Count ──
function updateTaskCount(tasks) {
    // Update PO badge
    const poBadge = document.getElementById("badge-po");
    if (poBadge && tasks.length > 0) {
        poBadge.textContent = tasks.length + " tasks";
    }

    // Update each agent's task count in sidebar
    const agents = ["analyst", "developer", "tester"];
    agents.forEach(agent => {
        const count = tasks.filter(t => t.comments && t.comments.some(c => c.author === agent)).length;
        const badge = document.getElementById(`badge-${agent}`);
        if (badge && count > 0) badge.textContent = count + " tasks";
    });
}

// ── Task Progress ──
function updateTaskProgress(data) {
    const footer = document.getElementById(`footer-${data.agent}`);
    if (footer) {
        footer.textContent = `[${data.index + 1}/${data.total}] ${data.task_id}`;
    }
}

// ── Finished ──
function onFinished(data) {
    // Update badges
    const badge = document.getElementById("pipeline-status-badge");
    if (badge) {
        badge.className = "status-badge status-finished";
        badge.textContent = "FINISHED";
    }

    const sidebarStatus = document.getElementById("sidebar-status");
    if (sidebarStatus) sidebarStatus.textContent = "FINISHED";

    // Hide live dot
    const liveDot = document.getElementById("liveDot");
    if (liveDot) liveDot.style.display = "none";

    // Show summary
    const summaryCard = document.getElementById("summaryCard");
    const summaryStats = document.getElementById("summaryStats");
    if (summaryCard && summaryStats) {
        summaryStats.innerHTML = `
            <div class="stat-block stat-pass">
                <div class="stat-num">${data.pass}</div>
                <div class="stat-label">Pass</div>
            </div>
            <div class="stat-block stat-fail">
                <div class="stat-num">${data.fail}</div>
                <div class="stat-label">Fail</div>
            </div>
            <div class="stat-block stat-total">
                <div class="stat-num">${data.total}</div>
                <div class="stat-label">Total Tasks</div>
            </div>
        `;
        summaryCard.style.display = "block";
    }

    appendLog(`Pipeline finished. PASS: ${data.pass} | FAIL: ${data.fail} | Total: ${data.total}`);
}

// ── Auto-connect SSE if pipeline is already running ──
document.addEventListener("DOMContentLoaded", () => {
    fetch("/api/state").then(r => r.json()).then(state => {
        if (state.status === "running") {
            connectSSE();
        }
    });
});