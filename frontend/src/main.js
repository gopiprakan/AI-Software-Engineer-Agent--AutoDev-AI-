// Initialize Lucide icons
lucide.createIcons();

const AGENT_PIPELINE = [
  { name: "Requirement Analyzer", role: "Business Analyst", icon: "file-text", color: "#f97316" },
  { name: "Project Planner", role: "Software Architect", icon: "help-circle", color: "#ca8a04" },
  { name: "Database Designer", role: "Database Admin", icon: "database", color: "#84cc16" },
  { name: "Backend Generator", role: "Backend Dev", icon: "code", color: "#ff6b00" },
  { name: "Frontend Generator", role: "Frontend Dev", icon: "file-code", color: "#ea580c" },
  { name: "Code Reviewer", role: "Security Auditor", icon: "shield-alert", color: "#ef4444" },
  { name: "Test Generator", role: "QA Engineer", icon: "check-circle", color: "#a3e635" },
  { name: "Documentation Generator", role: "Technical Writer", icon: "book-open", color: "#f59e0b" }
];

// State variables
let taskId = "";
let taskStatus = "idle";
let currentAgentIndex = -1;
let logs = [];
let filesList = [];
let activeTab = "requirements";
let activeFile = "";
let activeFileContent = "";
let originalFileContent = "";
let saveStatus = "";
let pollingInterval = null;

// DOM Elements
const providerSelect = document.getElementById("provider");
const apiKeyContainer = document.getElementById("apiKeyContainer");
const apiKeyInput = document.getElementById("apiKey");
const apiUrlContainer = document.getElementById("apiUrlContainer");
const apiUrlInput = document.getElementById("apiUrl");
const modelContainer = document.getElementById("modelContainer");
const modelInput = document.getElementById("model");
const deployBtn = document.getElementById("deployBtn");
const promptInput = document.getElementById("promptInput");
const agentPipelineContainer = document.getElementById("agentPipeline");
const terminalConsole = document.getElementById("terminalConsole");
const fileExplorer = document.getElementById("fileExplorer");
const exportZipBtn = document.getElementById("exportZipBtn");
const logStatusText = document.getElementById("logStatusText");

const workspaceTabs = document.querySelectorAll(".workspace-tab");
const editorTab = document.getElementById("editorTab");
const editorTabName = document.getElementById("editorTabName");
const editorView = document.getElementById("editorView");
const markdownView = document.getElementById("markdownView");
const emptyView = document.getElementById("emptyView");
const markdownContent = document.getElementById("markdownContent");
const codeTextarea = document.getElementById("codeTextarea");
const saveBtn = document.getElementById("saveBtn");
const saveBtnText = document.getElementById("saveBtnText");
const discardBtn = document.getElementById("discardBtn");

// Event Listeners
providerSelect.addEventListener("change", handleProviderChange);
deployBtn.addEventListener("click", handleDeployAgents);
exportZipBtn.addEventListener("click", handleExportZip);
saveBtn.addEventListener("click", handleSaveFile);
discardBtn.addEventListener("click", () => {
  activeFileContent = originalFileContent;
  codeTextarea.value = activeFileContent;
  updateEditorActions();
});
codeTextarea.addEventListener("input", (e) => {
  activeFileContent = e.target.value;
  updateEditorActions();
});

document.querySelectorAll(".template-btn").forEach(btn => {
  btn.addEventListener("click", (e) => {
    promptInput.value = e.target.getAttribute("data-prompt");
  });
});

workspaceTabs.forEach(tab => {
  tab.addEventListener("click", (e) => {
    activeTab = e.target.closest('.workspace-tab').getAttribute("data-tab");
    updateTabs();
    renderContent();
  });
});

function handleProviderChange() {
  const provider = providerSelect.value;
  apiKeyContainer.style.display = (provider !== "simulated" && provider !== "ollama") ? "flex" : "none";
  apiUrlContainer.style.display = (provider === "ollama") ? "flex" : "none";
  modelContainer.style.display = (provider !== "simulated") ? "flex" : "none";
  
  if (provider === "gemini") modelInput.placeholder = "gemini-3.5-flash";
  else if (provider === "openai") modelInput.placeholder = "gpt-4o";
  else if (provider === "ollama") modelInput.placeholder = "llama3";
}

function renderAgentPipeline() {
  agentPipelineContainer.innerHTML = "";
  AGENT_PIPELINE.forEach((agent, index) => {
    const isActive = taskStatus === "running" && currentAgentIndex === index;
    const isCompleted = currentAgentIndex > index || taskStatus === "completed";
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
    agentPipelineContainer.appendChild(el);
  });
  lucide.createIcons();
}

async function handleDeployAgents() {
  if (taskStatus === "running") return;
  
  taskStatus = "running";
  currentAgentIndex = 0;
  logs = ["[System] Initializing AutoDev AI pipeline..."];
  filesList = [];
  taskId = "";
  activeFile = "";
  activeFileContent = "";
  
  deployBtn.style.opacity = "0.6";
  logStatusText.innerText = "Compiling...";
  logStatusText.style.color = "var(--color-primary)";
  
  renderAgentPipeline();
  renderLogs();
  renderFileExplorer();
  renderContent();

  try {
    const response = await fetch("/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        prompt: promptInput.value,
        settings: {
          provider: providerSelect.value,
          apiKey: apiKeyInput.value,
          model: modelInput.value,
          apiUrl: apiUrlInput.value
        }
      })
    });

    if (!response.ok) {
      const errData = await response.json();
      throw new Error(errData.detail || "Server failed to initiate generation");
    }

    const data = await response.json();
    taskId = data.task_id;
    startPolling(taskId);
  } catch (err) {
    taskStatus = "failed";
    logs.push(`[System Error] Failed to launch backend agents: ${err.message}`);
    logStatusText.innerText = "Failed";
    logStatusText.style.color = "var(--text-muted)";
    deployBtn.style.opacity = "1";
    renderLogs();
    renderAgentPipeline();
  }
}

function startPolling(tid) {
  if (pollingInterval) clearInterval(pollingInterval);
  
  pollingInterval = setInterval(async () => {
    try {
      const res = await fetch(`/api/status/${tid}`);
      if (!res.ok) throw new Error("Status fetch error");
      const data = await res.json();
      
      taskStatus = data.status;
      currentAgentIndex = data.current_agent_index;
      logs = data.logs;
      filesList = data.files;
      
      renderAgentPipeline();
      renderLogs();
      renderFileExplorer();
      
      if (taskStatus === "completed" || taskStatus === "failed") {
        clearInterval(pollingInterval);
        deployBtn.style.opacity = "1";
        logStatusText.innerText = taskStatus === "completed" ? "Success" : "Failed";
        logStatusText.style.color = taskStatus === "completed" ? "var(--color-success)" : "var(--text-muted)";
        exportZipBtn.style.display = filesList.length > 0 ? "flex" : "none";
        
        if (filesList && filesList.length > 0 && !activeFile) {
          handleFileSelect(filesList[0]);
        } else {
          renderContent();
        }
      } else {
        renderContent();
      }
    } catch (err) {
      console.error("Polling error:", err);
    }
  }, 1000);
}

function renderLogs() {
  terminalConsole.innerHTML = "";
  if (logs.length === 0) {
    terminalConsole.innerHTML = `<div class="terminal-line system">Ready. Start agent deployment to view logs.</div>`;
    return;
  }
  
  logs.forEach(log => {
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
  if (filesList.length === 0) {
    fileExplorer.innerHTML = `<div style="color: var(--text-muted); font-size: 0.85rem; padding: 10px;">No generated files yet. Start the pipeline first!</div>`;
    return;
  }

  const folders = {};
  const rootFiles = [];

  filesList.forEach(file => {
    const parts = file.split('/');
    if (parts.length > 1) {
      const folderName = parts[0];
      if (!folders[folderName]) folders[folderName] = [];
      folders[folderName].push(file);
    } else {
      rootFiles.push(file);
    }
  });

  fileExplorer.innerHTML = "";
  
  const createItem = (filepath, name) => {
    const div = document.createElement("div");
    div.className = `file-item ${activeFile === filepath ? 'active' : ''}`;
    div.innerHTML = `<i data-lucide="file" style="width: 13px; height: 13px;"></i> ${name}`;
    div.onclick = () => handleFileSelect(filepath);
    return div;
  };

  Object.keys(folders).forEach(folder => {
    const folderContainer = document.createElement("div");
    folderContainer.style.marginBottom = "8px";
    folderContainer.innerHTML = `
      <div style="display: flex; align-items: center; gap: 6px; font-size: 0.8rem; font-weight: bold; color: var(--color-secondary); text-transform: uppercase; letter-spacing: 0.5px; padding: 4px 8px;">
        <i data-lucide="folder" style="width: 14px; height: 14px;"></i> ${folder}
      </div>
    `;
    const listDiv = document.createElement("div");
    listDiv.style.paddingLeft = "8px";
    listDiv.style.display = "flex";
    listDiv.style.flexDirection = "column";
    listDiv.style.gap = "2px";
    
    folders[folder].forEach(filepath => {
      listDiv.appendChild(createItem(filepath, filepath.substring(folder.length + 1)));
    });
    folderContainer.appendChild(listDiv);
    fileExplorer.appendChild(folderContainer);
  });

  if (rootFiles.length > 0) {
    const rootContainer = document.createElement("div");
    rootContainer.innerHTML = `
      <div style="display: flex; align-items: center; gap: 6px; font-size: 0.8rem; font-weight: bold; color: var(--color-secondary); text-transform: uppercase; letter-spacing: 0.5px; padding: 4px 8px;">
        Root Files
      </div>
    `;
    const listDiv = document.createElement("div");
    listDiv.style.display = "flex";
    listDiv.style.flexDirection = "column";
    listDiv.style.gap = "2px";
    rootFiles.forEach(filepath => {
      listDiv.appendChild(createItem(filepath, filepath));
    });
    rootContainer.appendChild(listDiv);
    fileExplorer.appendChild(rootContainer);
  }
  
  lucide.createIcons();
}

async function handleFileSelect(filepath) {
  activeFile = filepath;
  saveStatus = "";
  
  document.querySelectorAll(".file-item").forEach(item => item.classList.remove("active"));
  renderFileExplorer();
  
  activeTab = "editor";
  updateTabs();
  
  try {
    const res = await fetch(`/api/file/${taskId}?path=${encodeURIComponent(filepath)}`);
    if (!res.ok) throw new Error("Could not load file content");
    const data = await res.json();
    activeFileContent = data.content;
    originalFileContent = data.content;
    codeTextarea.value = activeFileContent;
    updateEditorActions();
    renderContent();
  } catch (err) {
    console.error(err);
    activeFileContent = `// Error loading file: ${err.message}`;
    codeTextarea.value = activeFileContent;
    updateEditorActions();
    renderContent();
  }
}

async function handleSaveFile() {
  if (!activeFile || !taskId) return;
  saveStatus = "saving";
  saveBtnText.innerText = "Saving...";
  saveBtn.disabled = true;

  try {
    const res = await fetch(`/api/file/${taskId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        path: activeFile,
        content: activeFileContent
      })
    });

    if (!res.ok) throw new Error("Save error");
    saveStatus = "saved";
    saveBtnText.innerText = "Saved!";
    saveBtn.style.background = "var(--color-success)";
    originalFileContent = activeFileContent;
    logs.push(`[System] Saved edits to '${activeFile}'`);
    renderLogs();
    
    updateEditorActions();
    setTimeout(() => {
      saveStatus = "";
      saveBtnText.innerText = "Save Changes";
      saveBtn.style.background = "";
      saveBtn.disabled = false;
    }, 2000);
  } catch (err) {
    saveStatus = "error";
    saveBtnText.innerText = "Error Saving";
    setTimeout(() => {
      saveStatus = "";
      saveBtnText.innerText = "Save Changes";
      saveBtn.disabled = false;
    }, 2000);
  }
}

function handleExportZip() {
  if (!taskId) return;
  window.location.href = `/api/export/${taskId}`;
}

function updateTabs() {
  workspaceTabs.forEach(tab => {
    if (tab.getAttribute("data-tab") === activeTab) tab.classList.add("active");
    else tab.classList.remove("active");
  });
  
  if (activeFile) {
    editorTab.style.display = "flex";
    editorTabName.innerText = activeFile.split('/').pop();
    if (activeTab === "editor") {
      editorTab.style.background = "#080c16";
    } else {
      editorTab.style.background = "rgba(255,255,255,0.01)";
    }
  } else {
    editorTab.style.display = "none";
  }
}

function getTabMarkdownFile() {
  if (!filesList || filesList.length === 0) return "";
  if (activeTab === "requirements") return filesList.find(f => f === "requirements.md");
  if (activeTab === "plan") return filesList.find(f => f === "project_plan.md");
  if (activeTab === "database") return filesList.find(f => f === "database_schema.sql");
  if (activeTab === "review") return filesList.find(f => f === "code_review.md");
  return "";
}

async function renderContent() {
  if (activeTab === "editor" && activeFile) {
    editorView.style.display = "flex";
    markdownView.style.display = "none";
    emptyView.style.display = "none";
    return;
  }
  
  const mdFile = getTabMarkdownFile();
  if (mdFile) {
    editorView.style.display = "none";
    markdownView.style.display = "block";
    emptyView.style.display = "none";
    
    markdownContent.innerHTML = `<div style="color: var(--text-muted); font-size: 0.85rem;">Reading document...</div>`;
    
    try {
      const res = await fetch(`/api/file/${taskId}?path=${encodeURIComponent(mdFile)}`);
      if (res.ok) {
        const data = await res.json();
        markdownContent.innerHTML = parseMarkdown(data.content);
      } else {
        markdownContent.innerHTML = `<div style="color: var(--text-muted); font-size: 0.85rem;">Failed to read file.</div>`;
      }
    } catch (e) {
      markdownContent.innerHTML = `<div style="color: var(--text-muted); font-size: 0.85rem;">Failed to read file.</div>`;
    }
  } else if (filesList.length > 0) {
    editorView.style.display = "none";
    markdownView.style.display = "block";
    emptyView.style.display = "none";
    markdownContent.innerHTML = `<div style="color: var(--text-muted); font-size: 0.85rem;">Awaiting Agent output for this section...</div>`;
  } else {
    editorView.style.display = "none";
    markdownView.style.display = "none";
    emptyView.style.display = "flex";
  }
}

function parseMarkdown(md) {
  if (!md) return `<div style="color: #64748b;">Awaiting Agent output...</div>`;

  const lines = md.split('\\n');
  let inTable = false;
  let tableHeaders = [];
  let tableRows = [];
  let listItems = [];
  let inList = false;
  let inCode = false;
  let codeBlock = [];
  
  let html = "";

  const processInlineBold = (text) => {
    return text.replace(/\\*\\*(.*?)\\*\\*/g, '<strong style="color: #fff">$1</strong>');
  };

  const flushList = () => {
    if (listItems.length > 0) {
      html += `<ul style="margin-left: 24px; margin-bottom: 16px;">`;
      listItems.forEach(item => html += `<li style="margin-bottom: 4px;">${item}</li>`);
      html += `</ul>`;
      listItems = [];
      inList = false;
    }
  };

  const flushTable = () => {
    if (tableHeaders.length > 0 || tableRows.length > 0) {
      html += `<table style="width: 100%; border-collapse: collapse; margin: 16px 0;"><thead><tr style="background: rgba(255,255,255,0.03);">`;
      tableHeaders.forEach(th => html += `<th style="border: 1px solid rgba(255,255,255,0.07); padding: 10px; text-align: left;">${th}</th>`);
      html += `</tr></thead><tbody>`;
      tableRows.forEach(row => {
        html += `<tr>`;
        row.forEach(td => html += `<td style="border: 1px solid rgba(255,255,255,0.07); padding: 10px;">${td}</td>`);
        html += `</tr>`;
      });
      html += `</tbody></table>`;
      tableHeaders = [];
      tableRows = [];
      inTable = false;
    }
  };

  const flushCode = () => {
    if (codeBlock.length > 0) {
      const code = codeBlock.join('\\n').replace(/</g, "&lt;").replace(/>/g, "&gt;");
      html += `<pre style="background: #050811; border: 1px solid rgba(255,255,255,0.07); border-radius: 6px; padding: 16px; margin: 16px 0; overflow-x: auto;">`;
      html += `<code style="font-family: 'Fira Code', monospace; color: #38bdf8; font-size: 0.85rem;">${code}</code></pre>`;
      codeBlock = [];
      inCode = false;
    }
  };

  lines.forEach(line => {
    if (line.trim().startsWith('\`\`\`')) {
      if (inCode) { flushCode(); } 
      else { flushList(); flushTable(); inCode = true; }
      return;
    }
    if (inCode) { codeBlock.push(line); return; }

    if (line.startsWith('# ')) {
      flushList(); flushTable();
      html += `<h1 style="border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 8px; margin-top: 24px; margin-bottom: 16px; color: #fff; font-size: 1.6rem; font-family: 'Outfit';">${line.replace('# ', '')}</h1>`;
      return;
    }
    if (line.startsWith('## ')) {
      flushList(); flushTable();
      html += `<h2 style="margin-top: 20px; margin-bottom: 12px; color: #fff; font-size: 1.25rem; font-family: 'Outfit';">${line.replace('## ', '')}</h2>`;
      return;
    }
    if (line.startsWith('### ')) {
      flushList(); flushTable();
      html += `<h3 style="margin-top: 16px; margin-bottom: 8px; color: #fff; font-size: 1.05rem; font-family: 'Outfit';">${line.replace('### ', '')}</h3>`;
      return;
    }
    if (line.trim().startsWith('- ') || line.trim().startsWith('* ')) {
      flushTable();
      inList = true;
      listItems.push(processInlineBold(line.replace(/^[\\s]*[-*]\\s+/, '')));
      return;
    }
    if (line.trim().startsWith('|')) {
      flushList();
      inTable = true;
      const cols = line.split('|').map(c => c.trim()).filter((c, i, a) => i > 0 && i < a.length - 1);
      if (line.includes('---')) return;
      if (tableHeaders.length === 0) tableHeaders = cols;
      else tableRows.push(cols);
      return;
    }
    if (line.trim() === '') {
      flushList(); flushTable();
      return;
    }
    if (!inTable && !inList && !inCode) {
      html += `<p style="margin-bottom: 12px; line-height: 1.6; font-size: 0.92rem;">${processInlineBold(line)}</p>`;
    }
  });

  flushList();
  flushTable();
  flushCode();

  return html;
}

// Initial render
renderAgentPipeline();
handleProviderChange();
