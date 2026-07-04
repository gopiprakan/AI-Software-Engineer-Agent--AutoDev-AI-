import React, { useState, useEffect, useRef } from 'react';
import { 
  Play, 
  Settings, 
  Terminal as TerminalIcon, 
  Folder, 
  File, 
  FileText, 
  Download, 
  CheckCircle, 
  AlertTriangle, 
  Code, 
  FileCode, 
  Database, 
  ShieldAlert, 
  HelpCircle,
  Save,
  BookOpen
} from 'lucide-react';

const AGENT_PIPELINE = [
  { name: "Requirement Analyzer", role: "Business Analyst", icon: FileText, color: "#f97316" },
  { name: "Project Planner", role: "Software Architect", icon: HelpCircle, color: "#ca8a04" },
  { name: "Database Designer", role: "Database Admin", icon: Database, color: "#84cc16" },
  { name: "Backend Generator", role: "Backend Dev", icon: Code, color: "#ff6b00" },
  { name: "Frontend Generator", role: "Frontend Dev", icon: FileCode, color: "#ea580c" },
  { name: "Code Reviewer", role: "Security Auditor", icon: ShieldAlert, color: "#ef4444" },
  { name: "Test Generator", role: "QA Engineer", icon: CheckCircle, color: "#a3e635" },
  { name: "Documentation Generator", role: "Technical Writer", icon: BookOpen, color: "#f59e0b" }
];

export default function App() {
  // Input parameters
  const [prompt, setPrompt] = useState("Build a Hospital Management System.");
  const [provider, setProvider] = useState("gemini");
  const [apiKey, setApiKey] = useState("");
  const [model, setModel] = useState("gemini-3.5-flash");
  const [apiUrl, setApiUrl] = useState("http://localhost:11434");

  // State control
  const [taskId, setTaskId] = useState("");
  const [taskStatus, setTaskStatus] = useState("idle"); // idle, running, completed, failed
  const [currentAgentIndex, setCurrentAgentIndex] = useState(-1);
  const [logs, setLogs] = useState([]);
  const [filesList, setFilesList] = useState([]);
  const [activeTab, setActiveTab] = useState("requirements"); // requirements, plan, database, review, editor
  
  // File details
  const [activeFile, setActiveFile] = useState("");
  const [activeFileContent, setActiveFileContent] = useState("");
  const [originalFileContent, setOriginalFileContent] = useState("");
  const [saveStatus, setSaveStatus] = useState(""); // "", "saving", "saved", "error"

  const logsEndRef = useRef(null);
  const pollingRef = useRef(null);

  // Auto-scroll logs
  useEffect(() => {
    if (logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs]);

  // Clean polling on unmount
  useEffect(() => {
    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, []);

  // Poll status endpoint
  const startPolling = (tid) => {
    if (pollingRef.current) clearInterval(pollingRef.current);

    pollingRef.current = setInterval(async () => {
      try {
        const res = await fetch(`http://127.0.0.1:8000/api/status/${tid}`);
        if (!res.ok) throw new Error("Status fetch error");
        const data = await res.json();
        
        setTaskStatus(data.status);
        setCurrentAgentIndex(data.current_agent_index);
        setLogs(data.logs);
        setFilesList(data.files);

        // Check if finished
        if (data.status === "completed" || data.status === "failed") {
          clearInterval(pollingRef.current);
          // Set requirements or main.py as active default file if populated
          if (data.files && data.files.length > 0) {
            handleFileSelect(data.files[0], tid);
          }
        }
      } catch (err) {
        console.error("Polling error:", err);
      }
    }, 1000);
  };

  // Trigger agent deployment
  const handleDeployAgents = async () => {
    setTaskStatus("running");
    setCurrentAgentIndex(0);
    setLogs(["[System] Initializing AutoDev AI pipeline..."]);
    setFilesList([]);
    setTaskId("");
    setActiveFile("");
    setActiveFileContent("");

    try {
      const response = await fetch("http://127.0.0.1:8000/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          prompt: prompt,
          settings: {
            provider,
            apiKey,
            model,
            apiUrl
          }
        })
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || "Server failed to initiate generation");
      }

      const data = await response.json();
      setTaskId(data.task_id);
      startPolling(data.task_id);
    } catch (err) {
      setTaskStatus("failed");
      setLogs(prev => [...prev, `[System Error] Failed to launch backend agents: ${err.message}`]);
    }
  };

  // Load code content
  const handleFileSelect = async (filepath, tid = taskId) => {
    setActiveFile(filepath);
    setSaveStatus("");
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/file/${tid}?path=${encodeURIComponent(filepath)}`);
      if (!res.ok) throw new Error("Could not load file content");
      const data = await res.json();
      setActiveFileContent(data.content);
      setOriginalFileContent(data.content);
      
      // Auto toggle to editor tab
      setActiveTab("editor");
    } catch (err) {
      console.error(err);
      setActiveFileContent(`// Error loading file: ${err.message}`);
    }
  };

  // Save changes to files
  const handleSaveFile = async () => {
    if (!activeFile || !taskId) return;
    setSaveStatus("saving");

    try {
      const res = await fetch(`http://127.0.0.1:8000/api/file/${taskId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          path: activeFile,
          content: activeFileContent
        })
      });

      if (!res.ok) throw new Error("Save error");
      setSaveStatus("saved");
      setOriginalFileContent(activeFileContent);
      setLogs(prev => [...prev, `[System] Saved edits to '${activeFile}'`]);
      setTimeout(() => setSaveStatus(""), 2000);
    } catch (err) {
      setSaveStatus("error");
      setTimeout(() => setSaveStatus(""), 2000);
    }
  };

  // Trigger server zip download
  const handleExportZip = () => {
    if (!taskId) return;
    window.location.href = `http://127.0.0.1:8000/api/export/${taskId}`;
  };

  // Template select shortcuts
  const selectTemplate = (title) => {
    setPrompt(title);
  };

  // Custom Inline Markdown renderer
  const renderMarkdown = (md) => {
    if (!md) return <div style={{ color: '#64748b' }}>Awaiting Agent output...</div>;

    const lines = md.split('\n');
    let inTable = false;
    let tableHeaders = [];
    let tableRows = [];
    let listItems = [];
    let inList = false;
    let inCode = false;
    let codeBlock = [];

    const elements = [];

    const flushList = (key) => {
      if (listItems.length > 0) {
        elements.push(
          <ul key={`ul-${key}`} style={{ marginLeft: '24px', marginBottom: '16px' }}>
            {listItems.map((item, idx) => <li key={idx} style={{ marginBottom: '4px' }}>{item}</li>)}
          </ul>
        );
        listItems = [];
        inList = false;
      }
    };

    const flushTable = (key) => {
      if (tableHeaders.length > 0 || tableRows.length > 0) {
        elements.push(
          <table key={`table-${key}`} style={{ width: '100%', borderCollapse: 'collapse', margin: '16px 0' }}>
            <thead>
              <tr style={{ background: 'rgba(255,255,255,0.03)' }}>
                {tableHeaders.map((th, idx) => (
                  <th key={idx} style={{ border: '1px solid rgba(255,255,255,0.07)', padding: '10px', textAlign: 'left' }}>{th}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {tableRows.map((row, rIdx) => (
                <tr key={rIdx}>
                  {row.map((td, cIdx) => (
                    <td key={cIdx} style={{ border: '1px solid rgba(255,255,255,0.07)', padding: '10px' }}>{td}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        );
        tableHeaders = [];
        tableRows = [];
        inTable = false;
      }
    };

    const flushCode = (key) => {
      if (codeBlock.length > 0) {
        elements.push(
          <pre key={`code-${key}`} style={{ background: '#050811', border: '1px solid rgba(255,255,255,0.07)', borderRadius: '6px', padding: '16px', margin: '16px 0', overflowX: 'auto' }}>
            <code style={{ fontFamily: 'Fira Code, monospace', color: '#38bdf8', fontSize: '0.85rem' }}>
              {codeBlock.join('\n')}
            </code>
          </pre>
        );
        codeBlock = [];
        inCode = false;
      }
    };

    lines.forEach((line, index) => {
      // Code blocks
      if (line.trim().startsWith('```')) {
        if (inCode) {
          flushCode(index);
        } else {
          flushList(index);
          flushTable(index);
          inCode = true;
        }
        return;
      }

      if (inCode) {
        codeBlock.push(line);
        return;
      }

      // Headers
      if (line.startsWith('# ')) {
        flushList(index);
        flushTable(index);
        elements.push(<h1 key={index} style={{ borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '8px', marginTop: '24px', marginBottom: '16px', color: '#fff', fontSize: '1.6rem', fontFamily: 'Outfit' }}>{line.replace('# ', '')}</h1>);
        return;
      }
      if (line.startsWith('## ')) {
        flushList(index);
        flushTable(index);
        elements.push(<h2 key={index} style={{ marginTop: '20px', marginBottom: '12px', color: '#fff', fontSize: '1.25rem', fontFamily: 'Outfit' }}>{line.replace('## ', '')}</h2>);
        return;
      }
      if (line.startsWith('### ')) {
        flushList(index);
        flushTable(index);
        elements.push(<h3 key={index} style={{ marginTop: '16px', marginBottom: '8px', color: '#fff', fontSize: '1.05rem', fontFamily: 'Outfit' }}>{line.replace('### ', '')}</h3>);
        return;
      }

      // Lists
      if (line.trim().startsWith('- ') || line.trim().startsWith('* ')) {
        flushTable(index);
        inList = true;
        // Simple bold processing in lists
        const cleanText = line.replace(/^[\s]*[-*]\s+/, '');
        listItems.push(processInlineBold(cleanText));
        return;
      }

      // Table lines
      if (line.trim().startsWith('|')) {
        flushList(index);
        inTable = true;
        // Parse row values
        const cols = line.split('|').map(c => c.trim()).filter((c, i, a) => i > 0 && i < a.length - 1);
        
        // Skip separator line |---|---|
        if (line.includes('---')) {
          return;
        }

        if (tableHeaders.length === 0) {
          tableHeaders = cols;
        } else {
          tableRows.push(cols);
        }
        return;
      }

      // Break table/list structures on empty line
      if (line.trim() === '') {
        flushList(index);
        flushTable(index);
        return;
      }

      // Regular text
      if (!inTable && !inList && !inCode) {
        elements.push(<p key={index} style={{ marginBottom: '12px', lineHeight: '1.6', fontSize: '0.92rem' }}>{processInlineBold(line)}</p>);
      }
    });

    // Cleanup remainders
    flushList('end');
    flushTable('end');
    flushCode('end');

    return <div className="markdown-preview">{elements}</div>;
  };

  // Replace **bold** with React strong nodes
  const processInlineBold = (text) => {
    const parts = text.split(/\*\*([^*]+)\*\*/g);
    if (parts.length === 1) return text;
    return parts.map((part, i) => i % 2 === 1 ? <strong key={i} style={{ color: '#fff' }}>{part}</strong> : part);
  };

  // Helper to construct a clean file structure view grouping files in folders
  const renderFileExplorer = () => {
    if (filesList.length === 0) {
      return <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', padding: '10px' }}>No generated files yet. Start the pipeline first!</div>;
    }

    // Group files by root directories
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

    return (
      <div className="file-tree">
        {Object.keys(folders).map(folder => (
          <div key={folder} style={{ marginBottom: '8px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.8rem', fontWeight: 'bold', color: 'var(--color-secondary)', textTransform: 'uppercase', letterSpacing: '0.5px', padding: '4px 8px' }}>
              <Folder size={14} /> {folder}
            </div>
            <div style={{ paddingLeft: '8px', display: 'flex', flexDirection: 'column', gap: '2px' }}>
              {folders[folder].map(filepath => {
                const name = filepath.substring(folder.length + 1);
                return (
                  <div 
                    key={filepath} 
                    className={`file-item ${activeFile === filepath ? 'active' : ''}`}
                    onClick={() => handleFileSelect(filepath)}
                  >
                    <File size={13} /> {name}
                  </div>
                );
              })}
            </div>
          </div>
        ))}
        {rootFiles.length > 0 && (
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.8rem', fontWeight: 'bold', color: 'var(--color-secondary)', textTransform: 'uppercase', letterSpacing: '0.5px', padding: '4px 8px' }}>
              Root Files
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
              {rootFiles.map(filepath => (
                <div 
                  key={filepath} 
                  className={`file-item ${activeFile === filepath ? 'active' : ''}`}
                  onClick={() => handleFileSelect(filepath)}
                >
                  <File size={13} /> {filepath}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  // Find markdown contents for tabs
  const getTabMarkdownContent = (tab) => {
    if (!filesList || filesList.length === 0) return "";
    
    if (tab === "requirements") {
      const match = filesList.find(f => f === "requirements.md");
      return match;
    }
    if (tab === "plan") {
      const match = filesList.find(f => f === "project_plan.md");
      return match;
    }
    if (tab === "database") {
      const match = filesList.find(f => f === "database_schema.sql");
      return match;
    }
    if (tab === "review") {
      const match = filesList.find(f => f === "code_review.md");
      return match;
    }
    return "";
  };

  const mdFile = getTabMarkdownContent(activeTab);
  const tabContentKey = activeFile + "_" + activeTab;

  return (
    <div className="app-container">
      {/* Top Header Navigation */}
      <header className="header">
        <div className="logo-section">
          <span style={{ fontSize: '1.5rem' }}>🚀</span>
          <span className="logo-title">AutoDev AI</span>
          <span className="logo-badge">Multi-Agent Engine</span>
        </div>

        <div className="settings-bar">
          {/* LLM Provider Selection */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Provider:</span>
            <select 
              className="settings-input" 
              value={provider} 
              onChange={(e) => setProvider(e.target.value)}
              style={{ background: '#1e293b' }}
            >
              <option value="simulated">Simulated Mode (Fast & Offline)</option>
              <option value="gemini">Gemini API</option>
              <option value="openai">OpenAI API</option>
              <option value="ollama">Ollama (Local LLM)</option>
            </select>
          </div>

          {/* Conditional Inputs */}
          {provider !== "simulated" && provider !== "ollama" && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>API Key:</span>
              <input 
                type="password" 
                className="settings-input" 
                placeholder="Using server key (.env)"
                value={apiKey} 
                onChange={(e) => setApiKey(e.target.value)}
              />
            </div>
          )}

          {provider === "ollama" && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Ollama URL:</span>
              <input 
                type="text" 
                className="settings-input" 
                placeholder="http://localhost:11434"
                value={apiUrl} 
                onChange={(e) => setApiUrl(e.target.value)}
              />
            </div>
          )}

          {provider !== "simulated" && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Model:</span>
              <input 
                type="text" 
                className="settings-input" 
                placeholder={provider === "gemini" ? "gemini-3.5-flash" : provider === "openai" ? "gpt-4o" : "llama3"}
                value={model} 
                onChange={(e) => setModel(e.target.value)}
                style={{ width: '130px' }}
              />
            </div>
          )}

          {/* Play Trigger */}
          <button 
            className="btn btn-primary"
            onClick={handleDeployAgents}
            disabled={taskStatus === "running"}
            style={{ opacity: taskStatus === "running" ? 0.6 : 1 }}
          >
            <Play size={16} fill="white" /> Deploy Agents
          </button>
        </div>
      </header>

      {/* Main Grid Dashboard */}
      <main className="dashboard-grid">
        
        {/* Panel 1: Prompt & Agent Pipeline */}
        <section className="panel">
          <div className="panel-header">
            <h2 className="panel-title">Orchestration Control</h2>
          </div>
          
          <div className="panel-content" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <div className="prompt-container">
              <span style={{ fontSize: '0.8rem', fontWeight: 'bold', color: 'var(--color-secondary)' }}>Project Description</span>
              <textarea 
                className="prompt-textarea"
                placeholder="Describe the application you want to build..."
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
              />
              
              {/* Quick Template Shortcuts */}
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '4px' }}>
                <button 
                  onClick={() => selectTemplate("Build a Hospital Management System")}
                  style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-color)', borderRadius: '4px', fontSize: '0.72rem', padding: '3px 8px', color: 'var(--text-main)', cursor: 'pointer' }}
                >
                  🏥 Hospital
                </button>
                <button 
                  onClick={() => selectTemplate("Build an E-commerce Platform with stripe checkout")}
                  style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-color)', borderRadius: '4px', fontSize: '0.72rem', padding: '3px 8px', color: 'var(--text-main)', cursor: 'pointer' }}
                >
                  🛒 E-Commerce
                </button>
                <button 
                  onClick={() => selectTemplate("Build a Trello-like Task Planner App")}
                  style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-color)', borderRadius: '4px', fontSize: '0.72rem', padding: '3px 8px', color: 'var(--text-main)', cursor: 'pointer' }}
                >
                  📅 Task Planner
                </button>
              </div>
            </div>

            {/* Visual Node Agent Stack */}
            <div>
              <h3 style={{ fontSize: '0.85rem', fontWeight: 'bold', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '12px', letterSpacing: '0.5px' }}>
                Agent Execution Pipeline
              </h3>
              
              <div className="agent-flow-list">
                {AGENT_PIPELINE.map((agent, index) => {
                  const AgentIcon = agent.icon;
                  const isActive = taskStatus === "running" && currentAgentIndex === index;
                  const isCompleted = currentAgentIndex > index || taskStatus === "completed";
                  const nodeClass = `agent-node ${isActive ? 'active' : ''} ${isCompleted ? 'completed' : ''}`;

                  return (
                    <div key={agent.name} className={nodeClass}>
                      <div className="agent-info">
                        <div className="agent-status-dot" />
                        <div style={{ display: 'flex', flexDirection: 'column' }}>
                          <span className="agent-name" style={{ color: isActive ? agent.color : '' }}>{agent.name}</span>
                          <span className="agent-role">{agent.role}</span>
                        </div>
                      </div>
                      <AgentIcon size={18} style={{ color: isActive || isCompleted ? agent.color : 'var(--text-muted)' }} />
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </section>

        {/* Panel 2: Code Explorer, Tabs, Editor Content */}
        <section className="panel" style={{ background: '#0a0d16' }}>
          {/* Top Tabs to browse code/designs */}
          <div className="workspace-tabs">
            <div 
              className={`workspace-tab ${activeTab === "requirements" ? "active" : ""}`}
              onClick={() => setActiveTab("requirements")}
            >
              Requirements
            </div>
            <div 
              className={`workspace-tab ${activeTab === "plan" ? "active" : ""}`}
              onClick={() => setActiveTab("plan")}
            >
              Architecture Plan
            </div>
            <div 
              className={`workspace-tab ${activeTab === "database" ? "active" : ""}`}
              onClick={() => setActiveTab("database")}
            >
              DB Schema
            </div>
            <div 
              className={`workspace-tab ${activeTab === "review" ? "active" : ""}`}
              onClick={() => setActiveTab("review")}
            >
              Code Review
            </div>
            {activeFile && (
              <div 
                className={`workspace-tab ${activeTab === "editor" ? "active" : ""}`}
                onClick={() => setActiveTab("editor")}
                style={{ borderLeft: '1px solid rgba(255,255,255,0.07)', background: activeTab === 'editor' ? '#080c16' : 'rgba(255,255,255,0.01)' }}
              >
                💻 {activeFile.split('/').pop()}
              </div>
            )}
          </div>

          <div style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
            {activeTab === "editor" && activeFile ? (
              <div className="editor-container">
                <textarea
                  className="code-textarea"
                  value={activeFileContent}
                  onChange={(e) => setActiveFileContent(e.target.value)}
                />
                
                {/* Save code action */}
                <div className="editor-actions">
                  {activeFileContent !== originalFileContent && (
                    <button 
                      className="btn btn-secondary"
                      onClick={() => setActiveFileContent(originalFileContent)}
                      style={{ padding: '6px 12px', fontSize: '0.8rem' }}
                    >
                      Discard
                    </button>
                  )}
                  <button 
                    className="btn btn-primary"
                    onClick={handleSaveFile}
                    disabled={saveStatus === "saving"}
                    style={{ padding: '6px 12px', fontSize: '0.8rem', background: saveStatus === 'saved' ? 'var(--color-success)' : '' }}
                  >
                    <Save size={13} /> {saveStatus === "saving" ? "Saving..." : saveStatus === "saved" ? "Saved!" : "Save Changes"}
                  </button>
                </div>
              </div>
            ) : mdFile ? (
              <div style={{ flex: 1, overflowY: 'auto', background: 'var(--bg-card)' }}>
                {/* Dynamically extract mock code/requirements content from active generated files */}
                {filesList.length > 0 ? (
                  <FileLoader 
                    taskId={taskId} 
                    filepath={mdFile} 
                    key={tabContentKey} 
                    render={renderMarkdown} 
                  />
                ) : (
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', padding: '24px' }}>
                    Awaiting Agent output...
                  </div>
                )}
              </div>
            ) : (
              <div style={{ display: 'flex', flex1: 1, alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--text-muted)', fontSize: '0.9rem', padding: '40px', textAlign: 'center' }}>
                <div>
                  <TerminalIcon size={40} style={{ margin: '0 auto 16px', color: 'var(--color-primary)', opacity: 0.5 }} />
                  <p>Awaiting pipeline output files.</p>
                  <p style={{ fontSize: '0.8rem', marginTop: '6px' }}>Type a prompt on the left and click "Deploy Agents" to compile a project.</p>
                </div>
              </div>
            )}
          </div>
        </section>

        {/* Panel 3: File Explorer & Terminal logs */}
        <section className="panel" style={{ width: '380px' }}>
          
          {/* Section A: Workspace Directory Tree */}
          <div style={{ flex: 1, borderBottom: '1px solid var(--border-color)', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
            <div className="panel-header" style={{ borderBottom: '1px solid var(--border-color)' }}>
              <h2 className="panel-title">Generated Workspace Explorer</h2>
              {filesList.length > 0 && (
                <button 
                  className="btn btn-secondary" 
                  onClick={handleExportZip}
                  style={{ padding: '4px 10px', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '4px' }}
                >
                  <Download size={12} /> Export ZIP
                </button>
              )}
            </div>
            
            <div className="panel-content" style={{ overflowY: 'auto' }}>
              {renderFileExplorer()}
            </div>
          </div>

          {/* Section B: Log Console / Stream */}
          <div style={{ height: '350px', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
            <div className="panel-header">
              <h2 className="panel-title"><TerminalIcon size={16} /> Agent Log Output</h2>
              <span style={{ 
                fontSize: '0.75rem', 
                color: taskStatus === 'running' ? 'var(--color-primary)' : taskStatus === 'completed' ? 'var(--color-success)' : 'var(--text-muted)' 
              }}>
                {taskStatus === 'running' ? 'Compiling...' : taskStatus === 'completed' ? 'Success' : 'Idle'}
              </span>
            </div>
            
            <div className="panel-content" style={{ padding: '12px' }}>
              <div className="terminal-console">
                {logs.length === 0 ? (
                  <div className="terminal-line system">Ready. Start agent deployment to view logs.</div>
                ) : (
                  logs.map((log, index) => {
                    let className = "terminal-line";
                    if (log.startsWith("[System]")) className += " system";
                    else if (log.includes("Error") || log.startsWith("[System Error]")) className += " error";
                    else if (log.includes("successfully") || log.includes("completed")) className += " success";
                    
                    return (
                      <div key={index} className={className}>
                        {log}
                      </div>
                    );
                  })
                )}
                <div ref={logsEndRef} />
              </div>
            </div>
          </div>
        </section>

      </main>
    </div>
  );
}

// Subcomponent to fetch file content asynchronously on tab switches
function FileLoader({ taskId, filepath, render }) {
  const [content, setContent] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    const fetchContent = async () => {
      if (!taskId || !filepath) return;
      try {
        setLoading(true);
        const res = await fetch(`http://127.0.0.1:8000/api/file/${taskId}?path=${encodeURIComponent(filepath)}`);
        if (!res.ok) throw new Error();
        const data = await res.json();
        if (active) {
          setContent(data.content);
          setLoading(false);
        }
      } catch (err) {
        if (active) {
          setContent("Error loading file content.");
          setLoading(false);
        }
      }
    };

    fetchContent();
    return () => {
      active = false;
    };
  }, [taskId, filepath]);

  if (loading) {
    return <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', padding: '24px' }}>Reading document structure...</div>;
  }

  return render(content);
}
