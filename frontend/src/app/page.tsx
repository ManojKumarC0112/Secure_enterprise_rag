"use client";

import { useState, useRef, useEffect } from "react";
import { Search, Shield, UploadCloud, FileText, Database, Code, ShieldAlert, LogOut, MessageSquare, Plus, ChevronRight, ArrowRight } from "lucide-react";
import { useRouter } from "next/navigation";

interface AuditLog {
  id: string;
  time: string;
  role: string;
  action: string;
  status: string;
  statusCode: number;
}

interface ChatSession {
  id: number;
  title: string;
  created_at: string;
}

interface Message {
  id: number;
  role: string;
  content: string;
}

export default function Home() {
  const router = useRouter();

  const [token, setToken] = useState<string | null>(null);
  const [role, setRole] = useState<string>("");
  
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<number | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  
  const [query, setQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  
  const [displayedText, setDisplayedText] = useState("");
  const [latestAssistantMsg, setLatestAssistantMsg] = useState("");

  // Upload State
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadTargetRole, setUploadTargetRole] = useState<string>("employee");
  const [isUploading, setIsUploading] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // UI state
  const [isAuditOpen, setIsAuditOpen] = useState(true);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 1. Initial Auth Check & Fetch Data
  useEffect(() => {
    const t = localStorage.getItem("token");
    const r = localStorage.getItem("role");
    if (!t) {
      router.push("/login");
      return;
    }
    setToken(t);
    setRole(r || "employee");

    fetchSessions(t);
    fetchAuditLogs(t);
  }, [router]);

  const fetchSessions = async (t: string) => {
    try {
      const res = await fetch("http://127.0.0.1:8000/sessions", {
        headers: { Authorization: `Bearer ${t}` }
      });
      if (res.ok) {
        const data = await res.json();
        setSessions(data.sessions);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchAuditLogs = async (t: string) => {
    try {
      const res = await fetch("http://127.0.0.1:8000/audit_logs", {
        headers: { Authorization: `Bearer ${t}` }
      });
      if (res.ok) {
        const data = await res.json();
        setAuditLogs(data.logs);
      }
    } catch (e) {
      console.error(e);
    }
  };
  
  const loadSession = async (sessionId: number) => {
    if (!token) return;
    setActiveSessionId(sessionId);
    setMessages([]);
    setDisplayedText("");
    setLatestAssistantMsg("");
    try {
      const res = await fetch(`http://127.0.0.1:8000/sessions/${sessionId}/messages`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setMessages(data.messages);
      }
    } catch (e) {
      console.error(e);
    }
  };

  // Streaming Effect
  useEffect(() => {
    if (!latestAssistantMsg) {
      setDisplayedText("");
      return;
    }
    let i = 0;
    setDisplayedText("");
    const interval = setInterval(() => {
      setDisplayedText(latestAssistantMsg.slice(0, i + 1));
      i++;
      if (i > latestAssistantMsg.length) {
         clearInterval(interval);
         // Once finished typing, convert display text to formal message object
         setMessages(prev => [...prev, { id: Date.now(), role: "assistant", content: latestAssistantMsg }]);
         setLatestAssistantMsg(""); // Clear to stop streaming
      }
    }, 10);
    return () => clearInterval(interval);
  }, [latestAssistantMsg]);

  // Scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, displayedText]);

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("role");
    router.push("/login");
  };

  const isPdfFile = (file: File | null | undefined) => {
    if (!file) return false;
    return file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf");
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile || !token) return;
    
    setIsUploading(true);
    const formData = new FormData();
    formData.append("file", uploadFile);
    formData.append("target_role", "auto");

    try {
      const res = await fetch("http://127.0.0.1:8000/upload", {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });
      if (res.ok) {
        const data = await res.json();
        setUploadFile(null);
        if (fileInputRef.current) fileInputRef.current.value = "";
        alert(`Success! AI classified this document as: ${data.detected_role.toUpperCase()}`);
      } else {
        const d = await res.json();
        alert(d.detail || "Upload rejected");
      }
      fetchAuditLogs(token);
    } catch (err) {
      alert("Upload failed completely.");
    } finally {
      setIsUploading(false);
    }
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || !token) return;

    const q = query;
    setQuery("");
    setIsSearching(true);
    setLatestAssistantMsg("");
    
    // Add optimistic user message
    setMessages(prev => [...prev, { id: Date.now(), role: "user", content: q }]);

    try {
      const res = await fetch("http://127.0.0.1:8000/ask", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ question: q, session_id: activeSessionId }),
      });
      const data = await res.json();
      
      if (res.ok) {
        if (!activeSessionId && data.session_id) {
           setActiveSessionId(data.session_id);
           fetchSessions(token);
        }
        setLatestAssistantMsg(data.answer);
      } else {
        setLatestAssistantMsg(`[ERROR] ${data.detail || "Access Denied"}`);
      }
      fetchAuditLogs(token);
    } catch (err) {
      setLatestAssistantMsg("[CONNECTION ERROR] Target backend unreachable.");
    } finally {
      setIsSearching(false);
    }
  };

  if (!token) return <div className="min-h-screen bg-slate-900 flex items-center justify-center text-white">Authenticating...</div>;

  return (
    <div className="flex h-screen bg-slate-50 text-slate-900 font-sans overflow-hidden selection:bg-blue-200">
      
      {/* LEFT SIDEBAR - HISTORY */}
      <div className="w-72 bg-slate-900 text-slate-300 flex flex-col border-r border-slate-800 shadow-2xl relative z-20">
        <div className="p-4 border-b border-slate-800">
          <button 
            onClick={() => { setActiveSessionId(null); setMessages([]); setLatestAssistantMsg(""); }}
            className="w-full flex items-center gap-2 justify-center bg-slate-800 hover:bg-slate-700 text-white p-2.5 rounded-lg transition-colors font-medium cursor-pointer shadow-inner shadow-slate-700/50"
          >
            <Plus className="w-4 h-4" /> New Investigation
          </button>
        </div>
        <div className="flex-1 overflow-y-auto w-full p-2 space-y-1 scrollbar-thin scrollbar-thumb-slate-700">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider px-3 my-2">Case Files</p>
          {sessions.map(s => (
            <button
               key={s.id}
               onClick={() => loadSession(s.id)}
               className={`w-full flex items-center gap-2 px-3 py-2.5 rounded-lg text-left text-sm transition-all focus:outline-none ${activeSessionId === s.id ? 'bg-indigo-500/20 text-indigo-200 border border-indigo-500/30' : 'hover:bg-slate-800/80'}`}
            >
              <MessageSquare className="w-4 h-4 shrink-0 opacity-70" />
              <span className="truncate flex-1">{s.title}</span>
            </button>
          ))}
        </div>
        
        {/* LOGOUT FOOTER */}
        <div className="p-4 border-t border-slate-800 flex items-center gap-3 bg-slate-900/50">
           <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-indigo-500 to-purple-500 flex items-center justify-center text-white font-bold shrink-0">
              {role.charAt(0).toUpperCase()}
           </div>
           <div className="flex-1 flex flex-col">
              <span className="text-sm font-bold text-white">{role.toUpperCase()}</span>
              <span className="text-xs text-slate-500">Active Identity</span>
           </div>
           <button onClick={handleLogout} className="p-2 bg-slate-800 hover:bg-red-500/20 hover:text-red-400 rounded-lg transition-colors text-slate-400" title="Disconnect">
              <LogOut className="w-4 h-4" />
           </button>
        </div>
      </div>

      {/* MAIN CONTENT AREA */}
      <div className="flex-1 flex flex-col relative h-full">
        {/* HEADER */}
        <header className="flex justify-between items-center px-6 py-4 bg-white/80 backdrop-blur-md border-b border-slate-200 z-10 shadow-sm">
          <div className="flex items-center gap-2">
            <Shield className="w-5 h-5 text-indigo-600" />
            <span className="font-bold tracking-tight text-lg text-slate-900">SECURE <span className="text-slate-300 font-normal">|</span> RAG</span>
          </div>
          <div className={`px-3 py-1 rounded-full text-xs font-bold tracking-wider uppercase ring-1 shadow-sm flex items-center gap-1.5 ${role === 'admin' ? 'bg-red-50 text-red-700 ring-red-500/30' : role === 'manager' ? 'bg-purple-50 text-purple-700 ring-purple-500/30' : 'bg-blue-50 text-blue-700 ring-blue-500/30'}`}>
            <span className="w-1.5 h-1.5 rounded-full bg-current animate-pulse"></span>
            {role} Access Level
          </div>
        </header>

        {/* ADMIN DRAWER */}
        {role === 'admin' && (
          <div className="bg-slate-50 border-b border-slate-200 shadow-inner relative z-10 p-4">
            <form onSubmit={handleUpload} className="flex gap-4 items-end max-w-4xl mx-auto">
              <label htmlFor="pdf-file-input" className={`flex-1 border-2 border-dashed rounded-lg p-3 flex items-center gap-3 cursor-pointer transition-all select-none bg-white ${isDragging ? 'border-indigo-500 bg-indigo-50' : 'border-slate-300 hover:border-slate-400'}`}
                onDragOver={(e) => { e.preventDefault(); e.stopPropagation(); setIsDragging(true); }}
                onDragLeave={(e) => { e.preventDefault(); e.stopPropagation(); setIsDragging(false); }}
                onDrop={(e) => {
                  e.preventDefault(); e.stopPropagation(); setIsDragging(false);
                  const file = e.dataTransfer.files?.[0];
                  if (file && isPdfFile(file)) setUploadFile(file);
                }}>
                <input id="pdf-file-input" type="file" accept="application/pdf,.pdf" className="sr-only" onChange={(e) => { const f = e.target.files?.[0]; setUploadFile(isPdfFile(f) ? f : null); }} />
                <div className={`p-2 rounded-md transition-colors ${isDragging ? 'bg-indigo-100' : 'bg-slate-100'}`}>
                  {uploadFile ? <FileText className="w-4 h-4 text-slate-700" /> : <Database className={`w-4 h-4 ${isDragging ? 'text-indigo-600' : 'text-slate-400'}`} />}
                </div>
                <div className="flex-1 pointer-events-none">
                  <p className="text-sm font-medium text-slate-700">{uploadFile ? uploadFile.name : 'Ingest specific knowledge (PDF)...'}</p>
                </div>
              </label>

              <div className="flex flex-col gap-1 items-center justify-center px-4">
                 <div className="flex items-center gap-1.5 text-indigo-700 bg-indigo-50 px-3 py-1.5 rounded-full border border-indigo-200">
                    <span className="relative flex h-2 w-2">
                       <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
                       <span className="relative inline-flex rounded-full h-2 w-2 bg-indigo-500"></span>
                    </span>
                    <span className="text-[10px] font-bold uppercase tracking-widest">AI Auto-Classify Active</span>
                 </div>
              </div>

              <button type="submit" disabled={!uploadFile || isUploading} className="bg-slate-900 hover:bg-slate-800 disabled:bg-slate-300 text-white font-medium py-2 px-6 rounded-lg text-sm shadow transition-colors flex items-center gap-2">
                {isUploading ? 'Analyzing...' : 'Secure Insert'}
              </button>
            </form>
          </div>
        )}

        {/* CHAT LOG AREA */}
        <div className="flex-1 overflow-y-auto p-4 md:p-8 scrollbar-thin scrollbar-thumb-slate-200">
          <div className="max-w-3xl mx-auto space-y-6 pb-32">
            
            {messages.length === 0 && !displayedText && (
              <div className="h-full flex flex-col items-center justify-center mt-32 text-slate-400 space-y-4">
                <Shield className="w-16 h-16 opacity-20" />
                <p className="font-medium text-lg text-slate-500">Secure Environment Initialized.</p>
                <p className="text-sm">Assigned partition: {role.toUpperCase()}. Awaiting instructions...</p>
              </div>
            )}

            {messages.map((m) => (
              <div key={m.id} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[85%] rounded-2xl p-4 shadow-sm ${m.role === 'user' ? 'bg-indigo-600 text-white rounded-br-none' : 'bg-white border border-slate-200 text-slate-800 rounded-bl-none'}`}>
                  {m.role === 'assistant' && (
                    <div className="flex items-center gap-1.5 mb-2.5 pb-2 border-b border-slate-100 text-xs font-bold text-slate-400 uppercase tracking-widest">
                      <Code className="w-3 h-3" /> Core System
                    </div>
                  )}
                  <div className={`prose max-w-none text-sm leading-relaxed ${m.role === 'user' ? 'text-indigo-50' : m.content.includes('[ERROR]') ? 'text-red-600 font-medium' : 'text-slate-700'}`}>
                    {m.content}
                  </div>
                </div>
              </div>
            ))}

            {/* STREAMING MESSAGE BUBBLE */}
            {displayedText && (
              <div className="flex justify-start">
                <div className="max-w-[85%] rounded-2xl rounded-bl-none p-4 shadow-sm bg-white border border-slate-200 text-slate-800">
                  <div className="flex items-center gap-1.5 mb-2.5 pb-2 border-b border-slate-100 text-xs font-bold text-slate-400 uppercase tracking-widest">
                    <Code className="w-3 h-3 text-indigo-500 animate-pulse" /> Core System (Streaming)
                  </div>
                  <div className="prose max-w-none text-sm leading-relaxed text-slate-700">
                    {displayedText}
                    <span className="inline-block w-1.5 bg-slate-900 h-3.5 ml-1 align-middle animate-pulse"></span>
                  </div>
                </div>
              </div>
            )}

            {/* LOADING INDICATOR */}
            {isSearching && !displayedText && (
              <div className="flex justify-start">
                 <div className="bg-white border border-slate-200 rounded-2xl rounded-bl-none py-3 px-5 shadow-sm flex items-center gap-3">
                   <div className="w-4 h-4 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
                   <span className="text-xs font-medium text-slate-500">Accessing vector framework...</span>
                 </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* INPUT AREA */}
        <div className="absolute bottom-0 left-0 right-0 p-4 md:px-8 pb-6 bg-gradient-to-t from-slate-50 via-slate-50 to-transparent z-10 pointer-events-none">
          <div className="max-w-3xl mx-auto flex flex-col pointer-events-auto">
            
            {/* AUDIT LOG TOGGLE AND CONSOLE */}
            <div className="mb-2 w-full">
              <button 
                onClick={() => setIsAuditOpen(!isAuditOpen)} 
                className="flex items-center gap-1.5 text-[10px] uppercase font-bold tracking-widest text-slate-500 hover:text-slate-700 transition"
              >
                <ChevronRight className={`w-3 h-3 transition-transform ${isAuditOpen ? 'rotate-90' : ''}`} /> Security Console {auditLogs.length > 0 ? `(${auditLogs.length})` : ''}
              </button>
              
              {isAuditOpen && (
                <div className="mt-1 bg-slate-900 text-[10px] font-mono text-slate-300 p-2.5 rounded-lg max-h-32 overflow-y-auto border border-slate-700 shadow-xl scrollbar-thin scrollbar-thumb-slate-600">
                  {auditLogs.length === 0 && <span className="opacity-50">No logs found.</span>}
                  {auditLogs.map((log) => (
                    <div key={log.id} className="flex gap-2">
                       <span className="text-slate-500">[{log.time}]</span>
                       <span className={`${log.role === 'ADMIN' ? 'text-red-400' : 'text-blue-400'} w-12 shrink-0`}>{log.role}</span>
                       <span className="flex-1 truncate">{log.action}</span>
                       <span className={log.statusCode === 200 ? 'text-emerald-400' : 'text-red-400'}>{log.status}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <form onSubmit={handleSearch} className="relative bg-white rounded-xl shadow-lg border border-slate-200 overflow-hidden focus-within:ring-2 focus-within:ring-indigo-100 focus-within:border-indigo-400 transition-all flex items-center p-1.5">
              <div className="pl-3 pr-2 text-slate-400">
                <Search className="w-5 h-5" />
              </div>
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Query the secure intelligence..."
                className="w-full bg-transparent text-sm font-medium text-slate-900 border-none outline-none placeholder:text-slate-400 py-3 disabled:opacity-50"
                disabled={isSearching}
                autoFocus
              />
              <div className="pr-1">
                <button type="submit" disabled={isSearching || !query.trim()} className="bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-200 disabled:text-slate-400 text-white p-2 rounded-lg transition-colors shadow">
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>

    </div>
  );
}
