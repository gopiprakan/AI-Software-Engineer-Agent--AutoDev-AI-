// Initialize Lucide icons
lucide.createIcons();

const API_BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
let authToken = localStorage.getItem("authToken");
let currentUser = null;

// Routing logic
const views = {
  login: document.getElementById("viewLogin"),
  dashboard: document.getElementById("viewDashboard"),
  wizard: document.getElementById("viewWizard"),
  vault: document.getElementById("viewVault"),
  ide: document.getElementById("viewIDE"),
};

const appHeader = document.getElementById("appHeader");

function showView(viewId) {
  Object.values(views).forEach(v => { if (v) v.style.display = "none"; });
  if (views[viewId]) views[viewId].style.display = viewId === "login" ? "flex" : "block";
  
  if (viewId === "login") {
    appHeader.style.display = "none";
  } else {
    appHeader.style.display = "flex";
  }
  
  if (viewId === "dashboard") loadDashboard();
  if (viewId === "vault") loadVault();
}

function handleRoute() {
  const hash = window.location.hash.replace("#", "") || "dashboard";
  
  if (!authToken) {
    showView("login");
    return;
  }
  
  if (hash.startsWith("ide/")) {
    const configId = hash.split("/")[1];
    showView("ide");
    initIDE(configId);
  } else {
    showView(hash);
  }
}

window.addEventListener("hashchange", handleRoute);

// API Helper
async function fetchAPI(endpoint, options = {}) {
  const headers = { ...options.headers };
  if (authToken) headers["Authorization"] = `Bearer ${authToken}`;
  if (options.body && typeof options.body === "object" && !(options.body instanceof URLSearchParams)) {
    options.body = JSON.stringify(options.body);
    headers["Content-Type"] = "application/json";
  }

  const res = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });
  if (res.status === 401) {
    logout();
    throw new Error("Unauthorized");
  }
  return res;
}

function logout() {
  authToken = null;
  localStorage.removeItem("authToken");
  window.location.hash = "";
  handleRoute();
}

document.getElementById("logoutBtn")?.addEventListener("click", logout);

// --- Auth View ---
const loginUsernameInput = document.getElementById("loginUsername");
const loginPasswordInput = document.getElementById("loginPassword");
const loginError = document.getElementById("loginError");

document.getElementById("loginBtn")?.addEventListener("click", async () => {
  const params = new URLSearchParams();
  params.append("username", loginUsernameInput.value);
  params.append("password", loginPasswordInput.value);
  
  try {
    const res = await fetch(`${API_BASE}/api/auth/token`, {
      method: "POST",
      body: params,
      headers: { "Content-Type": "application/x-www-form-urlencoded" }
    });
    if (!res.ok) throw new Error("Invalid credentials");
    const data = await res.json();
    authToken = data.access_token;
    localStorage.setItem("authToken", authToken);
    loginError.style.display = "none";
    window.location.hash = "#dashboard";
  } catch (e) {
    loginError.innerText = e.message;
    loginError.style.display = "block";
  }
});

document.getElementById("registerBtn")?.addEventListener("click", async () => {
  try {
    const res = await fetch(`${API_BASE}/api/auth/register`, {
      method: "POST",
      body: JSON.stringify({
        username: loginUsernameInput.value,
        password: loginPasswordInput.value
      }),
      headers: { "Content-Type": "application/json" }
    });
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || "Registration failed.");
    }
    document.getElementById("loginBtn").click(); // Auto login
  } catch (e) {
    loginError.innerText = e.message;
    loginError.style.display = "block";
  }
});

// --- Dashboard View ---
async function loadDashboard() {
  const buildsList = document.getElementById("buildsList");
  buildsList.innerHTML = "Loading...";
  try {
    const [buildsRes, agentsRes] = await Promise.all([
      fetchAPI("/api/dashboard/builds"),
      fetchAPI("/api/agents/")
    ]);
    const builds = await buildsRes.json();
    const agents = await agentsRes.json();
    
    const agentMap = {};
    agents.forEach(a => agentMap[a.id] = a.name);

    if (builds.length === 0 && agents.length === 0) {
      buildsList.innerHTML = `<p style="color: var(--text-muted);">No agents or builds found. Create a <a href="#wizard" style="color: var(--color-primary);">new agent</a> to get started!</p>`;
      return;
    }
    
    let html = `<h3>Your Agents</h3><div style="display:flex; gap:10px; flex-wrap: wrap; margin-bottom: 20px;">`;
    agents.forEach(a => {
      html += `<div class="build-card" style="flex-direction: column; align-items: flex-start; gap: 10px;">
        <strong>${a.name}</strong>
        <span style="font-size: 0.8rem; color: var(--text-muted);">${a.category} | ${a.api_selections.provider}</span>
        <button class="btn btn-primary" onclick="window.location.hash='#ide/${a.id}'">Launch IDE</button>
      </div>`;
    });
    html += `</div><h3>Recent Builds</h3>`;
    
    if (builds.length === 0) {
      html += `<p style="color: var(--text-muted);">No builds yet.</p>`;
    } else {
      builds.forEach(b => {
        html += `<div class="build-card">
          <div>
            <strong>Build ID:</strong> ${b.id.substring(0,8)}...<br>
            <span style="font-size: 0.8rem; color: var(--text-muted);">Agent: ${agentMap[b.agent_config_id] || "Unknown"}</span>
          </div>
          <div>
            <span style="margin-right: 15px; color: ${b.status === 'completed' ? 'var(--color-success)' : 'var(--text-muted)'}">${b.status.toUpperCase()}</span>
          </div>
        </div>`;
      });
    }
    buildsList.innerHTML = html;
  } catch (e) {
    buildsList.innerHTML = `<p style="color: #ef4444;">Error loading dashboard: ${e.message}</p>`;
  }
}

// --- API Vault View ---
async function loadVault() {
  const keysList = document.getElementById("keysList");
  keysList.innerHTML = "Loading...";
  try {
    const res = await fetchAPI("/api/keys/");
    const keys = await res.json();
    if (keys.length === 0) {
      keysList.innerHTML = `<p style="color: var(--text-muted);">No API keys saved.</p>`;
      return;
    }
    let html = "";
    keys.forEach(k => {
      html += `<div class="build-card">
        <strong>${k.category.toUpperCase()} Key</strong>
        <button class="btn btn-secondary" onclick="deleteKey(${k.id})">Delete</button>
      </div>`;
    });
    keysList.innerHTML = html;
  } catch (e) {
    keysList.innerHTML = `<p style="color: #ef4444;">Error loading keys</p>`;
  }
}

document.getElementById("addKeyBtn")?.addEventListener("click", async () => {
  const cat = document.getElementById("newKeyCategory").value;
  const val = document.getElementById("newKeyValue").value;
  if (!val) return;
  try {
    await fetchAPI("/api/keys/", {
      method: "POST",
      body: { category: cat, key_value: val }
    });
    document.getElementById("newKeyValue").value = "";
    loadVault();
  } catch (e) {
    alert("Error saving key");
  }
});

window.deleteKey = async (id) => {
  if (!confirm("Delete this key?")) return;
  try {
    await fetchAPI(`/api/keys/${id}`, { method: "DELETE" });
    loadVault();
  } catch (e) {
    alert("Error deleting key");
  }
};

// --- Wizard View ---
document.getElementById("createAgentBtn")?.addEventListener("click", async () => {
  const name = document.getElementById("wizardName").value;
  const cat = document.getElementById("wizardCategory").value;
  const provider = document.getElementById("wizardProvider").value;
  const behavior = document.getElementById("wizardBehavior").value;
  
  if (!name) { alert("Name is required"); return; }
  
  try {
    const res = await fetchAPI("/api/agents/", {
      method: "POST",
      body: {
        name: name,
        category: cat,
        api_selections: { provider: provider },
        behavior: behavior
      }
    });
    const agent = await res.json();
    window.location.hash = `#dashboard`;
  } catch (e) {
    alert("Error creating agent: " + e.message);
  }
});


// --- IDE / Tracker Logic ---
// We adapt the existing logic into a scoped function or vars
const AGENT_PIPELINE = [
  { name: "Requirement Analyzer", role: "Business Analyst", icon: "file-text", color: "#f97316" },
  { name: "Project Planner", role: "Software Architect", icon: "help-circle", color: "#ca8a04" },
  { name: "Database Designer", role: "Database Admin", icon: "database", color: "#84cc16" },
  { name: "Backend Generator", role: "Backend Dev", icon: "code", color: "#ff6b00" },
  { name: "Frontend Generator", role: "Frontend Dev", icon: "file-code", color: "#ea580c" },
  { name: "Code Reviewer", role: "Security Auditor", icon: "shield-alert", color: "#ef4444" },
  { name: "Test Generator", role: "QA Engineer", icon: "check-circle", color: "#a3e635" },
  { name: "Documentation Generator", role: "Technical Writer", icon: "book-open", color: "#f59e0b" },
  { name: "Deployment Configurator", role: "DevOps Engineer", icon: "server", color: "#3b82f6" }
];

let currentAgentConfigId = null;
let currentTaskId = null; // BuildLog ID
let ideState = {
  status: "idle", currentAgentIndex: -1, logs: [], filesList: [], activeTab: "requirements", activeFile: "",
  activeFileContent: "", originalFileContent: ""
};
let idePolling = null;

async function initIDE(agentConfigId) {
  currentAgentConfigId = agentConfigId;
  currentTaskId = null;
  ideState = { status: "idle", currentAgentIndex: -1, logs: [], filesList: [], activeTab: "requirements", activeFile: "" };
  if (idePolling) clearInterval(idePolling);
  
  document.getElementById("ideBuildStatus").innerText = "Status: Ready";
  
  // Fetch agent info
  try {
    const res = await fetchAPI("/api/agents/");
    const agents = await res.json();
    const agent = agents.find(a => a.id == agentConfigId);
    if (agent) {
      document.getElementById("ideAgentName").innerText = agent.name;
    }
  } catch (e) { }

  renderAgentPipeline();
  renderLogs();
  renderFileExplorer();
  renderContent();
}

function renderAgentPipeline() {
  const container = document.getElementById("agentPipeline");
  container.innerHTML = "";
  AGENT_PIPELINE.forEach((agent, index) => {
    const isActive = ideState.status === "running" && ideState.currentAgentIndex === index;
    const isCompleted = ideState.currentAgentIndex > index || ideState.status === "completed";
    let nodeClass = "agent-node";
    if (isActive) nodeClass += " active";
    if (isCompleted) nodeClass += " completed";
    
    const color = (isActive || isCompleted) ? agent.color : "var(--text-muted)";
    const nameColor = isActive ? agent.color : "";

    const el = document.createElement("div");
    el.className = nodeClass;
    el.innerHTML = `
      <div class="agent-info">
        <div class="agent-status-dot"></div>
        <div style="display: flex; flex-direction: column;">
          <span class="agent-name" style="color: ${nameColor}">${agent.name}</span>
          <span class="agent-role">${agent.role}</span>
        </div>
      </div>
      <i data-lucide="${agent.icon}" style="width: 18px; height: 18px; color: ${color};"></i>
    `;
    container.appendChild(el);
  });
  lucide.createIcons();
}

document.getElementById("deployBtn")?.addEventListener("click", async () => {
  if (ideState.status === "running") return;
  ideState.status = "running";
  ideState.currentAgentIndex = 0;
  ideState.logs = ["[System] Initiating generation..."];
  ideState.filesList = [];
  document.getElementById("ideBuildStatus").innerText = "Status: Running...";
  renderAgentPipeline();
  renderLogs();
  
  try {
    const res = await fetchAPI("/api/generate", {
      method: "POST",
      body: {
        prompt: document.getElementById("promptInput").value,
        settings: {},
        agent_config_id: parseInt(currentAgentConfigId)
      }
    });
    const data = await res.json();
    currentTaskId = data.id;
    startIdePolling();
  } catch (e) {
    ideState.status = "failed";
    ideState.logs.push(`[System Error] ${e.message}`);
    document.getElementById("ideBuildStatus").innerText = "Status: Failed";
    renderLogs();
  }
});

function startIdePolling() {
  if (idePolling) clearInterval(idePolling);
  idePolling = setInterval(async () => {
    try {
      const res = await fetchAPI(`/api/status/${currentTaskId}`);
      const data = await res.json();
      
      ideState.status = data.status;
      ideState.currentAgentIndex = data.current_agent_index;
      ideState.logs = data.logs;
      ideState.filesList = data.files;
      
      renderAgentPipeline();
      renderLogs();
      renderFileExplorer();
      
      document.getElementById("ideBuildStatus").innerText = `Status: ${ideState.status.toUpperCase()}`;
      
      if (ideState.status === "completed" || ideState.status === "failed") {
        clearInterval(idePolling);
        document.getElementById("exportZipBtn").style.display = ideState.filesList.length > 0 ? "flex" : "none";
        renderContent();
      }
    } catch (e) { }
  }, 1000);
}

function renderLogs() {
  const terminalConsole = document.getElementById("terminalConsole");
  terminalConsole.innerHTML = "";
  if (ideState.logs.length === 0) {
    terminalConsole.innerHTML = `<div class="terminal-line system">Ready. Start agent deployment to view logs.</div>`;
    return;
  }
  
  ideState.logs.forEach(log => {
    const div = document.createElement("div");
    let className = "terminal-line";
    if (log.startsWith("[System]")) className += " system";
    else if (log.includes("Error") || log.startsWith("[System Error]")) className += " error";
    else if (log.includes("successfully") || log.includes("completed")) className += " success";
    
    div.className = className;
    div.innerText = log;
    terminalConsole.appendChild(div);
  });
  terminalConsole.scrollTop = terminalConsole.scrollHeight;
}

function renderFileExplorer() {
  const fileExplorer = document.getElementById("fileExplorer");
  if (ideState.filesList.length === 0) {
    fileExplorer.innerHTML = `<div style="color: var(--text-muted); font-size: 0.85rem; padding: 10px;">No generated files yet.</div>`;
    return;
  }

  const rootFiles = [];
  ideState.filesList.forEach(file => rootFiles.push(file));

  fileExplorer.innerHTML = "";
  const listDiv = document.createElement("div");
  listDiv.style.display = "flex";
  listDiv.style.flexDirection = "column";
  listDiv.style.gap = "2px";
  
  rootFiles.forEach(filepath => {
    const div = document.createElement("div");
    div.className = `file-item ${ideState.activeFile === filepath ? 'active' : ''}`;
    div.innerHTML = `<i data-lucide="file" style="width: 13px; height: 13px;"></i> ${filepath}`;
    div.onclick = () => handleFileSelect(filepath);
    listDiv.appendChild(div);
  });
  
  fileExplorer.appendChild(listDiv);
  lucide.createIcons();
}

async function handleFileSelect(filepath) {
  ideState.activeFile = filepath;
  renderFileExplorer();
  
  ideState.activeTab = "editor";
  updateTabs();
  
  try {
    const res = await fetchAPI(`/api/file/${currentTaskId}?path=${encodeURIComponent(filepath)}`);
    const data = await res.json();
    ideState.activeFileContent = data.content;
    ideState.originalFileContent = data.content;
    document.getElementById("codeTextarea").value = ideState.activeFileContent;
    renderContent();
  } catch (err) { }
}

document.querySelectorAll(".workspace-tab").forEach(tab => {
  tab.addEventListener("click", (e) => {
    ideState.activeTab = e.target.closest('.workspace-tab').getAttribute("data-tab");
    updateTabs();
    renderContent();
  });
});

function updateTabs() {
  document.querySelectorAll(".workspace-tab").forEach(tab => {
    if (tab.getAttribute("data-tab") === ideState.activeTab) tab.classList.add("active");
    else tab.classList.remove("active");
  });
  
  const editorTab = document.getElementById("editorTab");
  if (ideState.activeFile) {
    editorTab.style.display = "flex";
    document.getElementById("editorTabName").innerText = ideState.activeFile.split('/').pop();
    editorTab.style.background = ideState.activeTab === "editor" ? "#080c16" : "rgba(255,255,255,0.01)";
  } else {
    editorTab.style.display = "none";
  }
}

async function renderContent() {
  const editorView = document.getElementById("editorView");
  const markdownView = document.getElementById("markdownView");
  const emptyView = document.getElementById("emptyView");
  const markdownContent = document.getElementById("markdownContent");

  if (ideState.activeTab === "editor" && ideState.activeFile) {
    editorView.style.display = "flex";
    markdownView.style.display = "none";
    emptyView.style.display = "none";
    return;
  }
  
  let mdFile = "";
  if (ideState.activeTab === "requirements") mdFile = "requirements.md";
  if (ideState.activeTab === "plan") mdFile = "project_plan.md";
  if (ideState.activeTab === "database") mdFile = "database_schema.sql";
  if (ideState.activeTab === "review") mdFile = "code_review.md";
  if (ideState.activeTab === "deploy") mdFile = "deploy.md";
  
  if (ideState.filesList.includes(mdFile)) {
    editorView.style.display = "none";
    markdownView.style.display = "block";
    emptyView.style.display = "none";
    
    try {
      const res = await fetchAPI(`/api/file/${currentTaskId}?path=${encodeURIComponent(mdFile)}`);
      const data = await res.json();
      markdownContent.innerHTML = `<pre style="white-space: pre-wrap; font-family: 'Inter';">${data.content}</pre>`; // Simplified parsing for now
    } catch (e) { }
  } else {
    editorView.style.display = "none";
    markdownView.style.display = "none";
    emptyView.style.display = "flex";
  }
}

document.getElementById("exportZipBtn")?.addEventListener("click", () => {
  if (currentTaskId && authToken) {
    // Basic redirect won't have auth headers, we should use a query param or fetch as blob.
    // For simplicity, we can fetch as blob and download it.
    fetch(`${API_BASE}/api/export/${currentTaskId}`, {
      headers: { "Authorization": `Bearer ${authToken}` }
    }).then(res => res.blob()).then(blob => {
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `autodev_${currentTaskId}.zip`;
      a.click();
    });
  }
});

// Initialization
handleRoute();
