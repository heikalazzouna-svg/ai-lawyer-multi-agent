"use client";

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { UploadCloud, MessageSquare, FileText, Scale, Loader2, FileCheck2, Search, ShieldAlert, PenTool, Bot, CheckCircle2, Sparkles, Send, ChevronDown, Activity, Clock, Zap, Menu, Download, History, X, Lock, User, LogOut, GitCompare } from 'lucide-react';

// ─── Types ───────────────────────────────────────────────────────────────────
interface TraceStep {
  node: string;
  status: 'waiting' | 'running' | 'done';
  label?: string;
  elapsed?: number;
  agent?: string;
  verified?: boolean;
}

interface ChatMessage {
  role: 'user' | 'ai';
  content: string;
  agent?: string;
  citationsVerified?: boolean;
  trace?: TraceStep[];
  isStreaming?: boolean;
}

interface ChatSession {
  session_id: number;
  created_at: string;
  messages: {
    role: 'user' | 'ai';
    content: string;
    agent?: string;
    verified?: boolean;
  }[];
}

// ─── Agent Trace Component ───────────────────────────────────────────────────
function AgentTrace({ steps }: { steps: TraceStep[] }) {
  return (
    <div className="mb-5 rounded-lg border border-[#1a1f3c] bg-[#0a0d1a] p-4 space-y-2">
      <div className="flex items-center gap-2 mb-3 pb-2 border-b border-[#1a1f3c]">
        <Activity className="w-3.5 h-3.5 text-[#f3d36b]" />
        <span className="text-[10px] font-bold uppercase tracking-widest text-[#f3d36b]">Agent Pipeline</span>
      </div>
      {steps.map((step, i) => (
        <div key={i} className="flex items-center gap-3 text-xs">
          {step.status === 'done' ? (
            <div className="w-5 h-5 rounded-full bg-emerald-500/15 border border-emerald-500/30 flex items-center justify-center shrink-0">
              <CheckCircle2 className="w-3 h-3 text-emerald-400" />
            </div>
          ) : step.status === 'running' ? (
            <div className="w-5 h-5 rounded-full bg-[#f3d36b]/15 border border-[#f3d36b]/30 flex items-center justify-center shrink-0">
              <Loader2 className="w-3 h-3 text-[#f3d36b] animate-spin" />
            </div>
          ) : (
            <div className="w-5 h-5 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center shrink-0">
              <div className="w-1.5 h-1.5 rounded-full bg-slate-600" />
            </div>
          )}

          <span className={`flex-1 font-medium ${
            step.status === 'done' ? 'text-slate-400' :
            step.status === 'running' ? 'text-slate-200' :
            'text-slate-600'
          }`}>
            {step.node === 'supervisor' && 'Supervisor'}
            {step.node === 'specialist' && (step.agent || 'Specialist')}
            {step.node === 'citator' && 'Citator'}
            {step.label && step.status === 'running' && <span className="ml-2 text-slate-500 font-normal">{step.label}</span>}
            {step.node === 'supervisor' && step.status === 'done' && step.agent && <span className="ml-2 text-slate-500 font-normal">→ {step.agent}</span>}
          </span>

          {step.status === 'done' && step.elapsed !== undefined && (
            <span className="flex items-center gap-1 text-slate-600 text-[10px] tabular-nums shrink-0">
              <Clock className="w-2.5 h-2.5" />
              {step.elapsed}s
            </span>
          )}

          {step.node === 'citator' && step.status === 'done' && step.verified && (
            <span className="flex items-center gap-1 text-emerald-400 text-[10px] shrink-0">
              <Zap className="w-2.5 h-2.5" />
              Verified
            </span>
          )}
        </div>
      ))}
    </div>
  );
}

function parseSSE(text: string): { event: string; data: string }[] {
  const events: { event: string; data: string }[] = [];
  const blocks = text.split('\n\n');
  for (const block of blocks) {
    if (!block.trim()) continue;
    const lines = block.split('\n');
    let event = 'message';
    let data = '';
    for (const line of lines) {
      if (line.startsWith('event: ')) event = line.slice(7).trim();
      if (line.startsWith('data: ')) data = line.slice(6).trim();
    }
    if (data) events.push({ event, data });
  }
  return events;
}

// ─── Main App ────────────────────────────────────────────────────────────────
export default function AILawyerApp() {
  const [token, setToken] = useState<string | null>(null);
  
  // Auth State
  const [authFirstName, setAuthFirstName] = useState('');
  const [authLastName, setAuthLastName] = useState('');
  const [authEmail, setAuthEmail] = useState('');
  const [authPassword, setAuthPassword] = useState('');
  const [authConfirmPassword, setAuthConfirmPassword] = useState('');
  const [isLoginMode, setIsLoginMode] = useState(true);
  const [authError, setAuthError] = useState('');
  const [authSuccess, setAuthSuccess] = useState('');
  const [registrationSuccess, setRegistrationSuccess] = useState(false);

  // App State
  const [files, setFiles] = useState<File[]>([]);
  const [filenames, setFilenames] = useState<string[]>([]);
  const [activePdf, setActivePdf] = useState<string | null>(null);
  
  const [isUploading, setIsUploading] = useState(false);
  const [scanResult, setScanResult] = useState<string | null>(null);
  
  const [chatInput, setChatInput] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const [activeSessionId, setActiveSessionId] = useState<number | null>(null);
  
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [history, setHistory] = useState<ChatSession[]>([]);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const savedToken = localStorage.getItem('ai_lawyer_token');
    if (savedToken) setToken(savedToken);
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const verifyToken = params.get('token');
    if (verifyToken) {
      fetch(`http://localhost:8000/verify/${verifyToken}`)
        .then(res => res.json())
        .then(data => {
          if (data.message) {
            setAuthSuccess(data.message);
            setIsLoginMode(true);
            setRegistrationSuccess(false);
          } else {
            setAuthError(data.detail || "Invalid verification link.");
          }
          // Clean up URL
          window.history.replaceState({}, document.title, window.location.pathname);
        })
        .catch(() => setAuthError("Failed to verify email."));
    }
  }, []);

  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    setAuthError('');
    try {
      if (isLoginMode) {
        const formData = new URLSearchParams();
        formData.append('username', authEmail);
        formData.append('password', authPassword);

        const res = await fetch('http://localhost:8000/token', {
          method: 'POST',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          body: formData.toString()
        });
        const data = await res.json();
        if (res.ok) {
          setToken(data.access_token);
          localStorage.setItem('ai_lawyer_token', data.access_token);
        } else {
          setAuthError(data.detail || "Login failed");
        }
      } else {
        if (authPassword !== authConfirmPassword) {
          setAuthError("Passwords do not match.");
          return;
        }
        
        const res = await fetch('http://localhost:8000/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ 
            first_name: authFirstName,
            last_name: authLastName,
            email: authEmail, 
            password: authPassword 
          })
        });
        const data = await res.json();
        if (res.ok) {
          setRegistrationSuccess(true);
          setAuthSuccess(data.message);
        } else {
          setAuthError(data.detail || "Registration failed");
        }
      }
    } catch (err) {
      setAuthError("Failed to connect to API server.");
    }
  };

  const handleLogout = () => {
    setToken(null);
    localStorage.removeItem('ai_lawyer_token');
    setMessages([]);
    setActiveSessionId(null);
    setFilenames([]);
    setActivePdf(null);
    setScanResult(null);
  };

  const startNewSession = () => {
    setMessages([]);
    setActiveSessionId(null);
    setFilenames([]);
    setFiles([]);
    setActivePdf(null);
    setScanResult(null);
    setIsSidebarOpen(false);
  };

  const loadHistory = async () => {
    if (!token) return;
    try {
      const res = await fetch('http://localhost:8000/history', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setHistory(data.history);
      } else if (res.status === 401) {
        handleLogout();
      }
    } catch (err) {
      console.error("Could not load history", err);
    }
  };

  useEffect(() => {
    if (isSidebarOpen && token) loadHistory();
  }, [isSidebarOpen, token]);

  const loadPastSession = (session: ChatSession) => {
    const formattedMessages: ChatMessage[] = session.messages.map(m => ({
      role: m.role,
      content: m.content,
      agent: m.agent,
      citationsVerified: m.verified,
      isStreaming: false
    }));
    setMessages(formattedMessages);
    setActiveSessionId(session.session_id);
    setIsSidebarOpen(false);
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0 || !token) return;
    
    const selectedFiles = Array.from(e.target.files);
    setFiles(selectedFiles);
    setIsUploading(true);
    setScanResult(null);
    
    const formData = new FormData();
    selectedFiles.forEach(file => formData.append('files', file));

    try {
      const res = await fetch('http://localhost:8000/upload', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData,
      });
      const data = await res.json();
      if (res.ok) {
        setFilenames(data.filenames);
        setScanResult(data.scan_result);
        if (data.filenames.length > 0) setActivePdf(data.filenames[0]);
      } else if (res.status === 401) {
        handleLogout();
      } else {
        alert(data.detail || 'Upload failed');
      }
    } catch (error) {
      alert("Failed to connect to API server.");
    } finally {
      setIsUploading(false);
    }
  };

  const handleDownloadDocx = async (content: string) => {
    if (!token) return;
    try {
      const res = await fetch('http://localhost:8000/export/docx', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ content, title: 'Legal_Draft' })
      });
      if (res.ok) {
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'Legal_Draft.docx';
        document.body.appendChild(a);
        a.click();
        a.remove();
      }
    } catch (err) {
      alert("Failed to download document.");
    }
  };

  const handleSendMessage = useCallback(async () => {
    if (!chatInput.trim() || filenames.length === 0 || !token) return;
    
    const userMsg = chatInput;
    setChatInput('');
    setIsTyping(true);

    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);

    const aiMsgIndex = messages.length + 1; 
    setMessages(prev => [
      ...prev,
      {
        role: 'ai',
        content: '',
        agent: undefined,
        citationsVerified: false,
        isStreaming: true,
        trace: [
          { node: 'supervisor', status: 'waiting' },
          { node: 'specialist', status: 'waiting' },
          { node: 'citator', status: 'waiting' },
        ],
      },
    ]);

    try {
      const res = await fetch('http://localhost:8000/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ query: userMsg, filenames, session_id: activeSessionId }),
      });

      if (!res.ok) {
        if (res.status === 401) handleLogout();
        const errorData = await res.json();
        setMessages(prev => {
          const updated = [...prev];
          updated[aiMsgIndex] = {
            ...updated[aiMsgIndex],
            content: `Error: ${errorData.detail || 'Unknown error'}`,
            isStreaming: false,
          };
          return updated;
        });
        setIsTyping(false);
        return;
      }

      const reader = res.body?.getReader();
      if (!reader) throw new Error('No response body');

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        const lastDoubleNewline = buffer.lastIndexOf('\n\n');
        if (lastDoubleNewline === -1) continue;

        const completePart = buffer.slice(0, lastDoubleNewline + 2);
        buffer = buffer.slice(lastDoubleNewline + 2);

        const events = parseSSE(completePart);

        for (const sseEvent of events) {
          try {
            const payload = JSON.parse(sseEvent.data);
            setMessages(prev => {
              const updated = [...prev];
              const msg = { ...updated[aiMsgIndex] };
              const trace = msg.trace ? [...msg.trace] : [];

              if (sseEvent.event === 'trace') {
                const stepIndex = trace.findIndex(s => s.node === payload.node);
                if (stepIndex >= 0) {
                  trace[stepIndex] = {
                    ...trace[stepIndex],
                    status: payload.status,
                    label: payload.label || trace[stepIndex].label,
                    elapsed: payload.elapsed,
                    agent: payload.agent_display || payload.agent || trace[stepIndex].agent,
                    verified: payload.verified,
                  };
                }
                if (payload.node === 'supervisor' && payload.status === 'done') {
                  msg.agent = payload.agent_display;
                  const specIdx = trace.findIndex(s => s.node === 'specialist');
                  if (specIdx >= 0) trace[specIdx] = { ...trace[specIdx], agent: payload.agent_display };
                }
                msg.trace = trace;
              } else if (sseEvent.event === 'token') {
                msg.content = (msg.content || '') + payload.chunk;
              } else if (sseEvent.event === 'done') {
                msg.agent = payload.agent;
                msg.citationsVerified = payload.citations_verified;
                msg.isStreaming = false;
                if (payload.final_answer && payload.final_answer !== msg.content) {
                  msg.content = payload.final_answer;
                }
                if (payload.session_id) {
                  setActiveSessionId(payload.session_id);
                }
              }
              updated[aiMsgIndex] = msg;
              return updated;
            });
          } catch { }
        }
      }
    } catch (error) {
      setMessages(prev => {
        const updated = [...prev];
        if (updated[aiMsgIndex]) {
          updated[aiMsgIndex] = {
            ...updated[aiMsgIndex],
            content: updated[aiMsgIndex].content || 'Stream disconnected.',
            isStreaming: false,
          };
        }
        return updated;
      });
    } finally {
      setIsTyping(false);
    }
  }, [chatInput, filenames, messages.length, token, activeSessionId]);


  // ─── AUTH SCREEN ──────────────────────────────────────────────
  if (!token) {
    if (registrationSuccess) {
      return (
        <div className="flex h-screen w-full bg-[#05060b] text-slate-300 items-center justify-center font-sans">
          <div className="w-full max-w-md p-10 rounded-2xl border border-[#1a1f3c] bg-[#0b0e1a] shadow-[0_0_50px_rgba(243,211,107,0.05)] text-center">
            <div className="w-20 h-20 mx-auto rounded-full border border-emerald-500/30 flex items-center justify-center mb-6 bg-emerald-500/10">
               <FileCheck2 className="w-10 h-10 text-emerald-400" />
            </div>
            <h2 className="text-2xl font-serif text-white mb-4">Check your Inbox</h2>
            <p className="text-sm text-slate-400 mb-8 leading-relaxed">
              We've sent a verification link to <strong className="text-white">{authEmail}</strong>. 
              Please click the link to activate your AI Lawyer account.
            </p>
            <button 
              onClick={() => { setRegistrationSuccess(false); setIsLoginMode(true); }}
              className="px-6 py-2.5 rounded-lg border border-[#f3d36b]/30 text-[#f3d36b] hover:bg-[#f3d36b]/10 transition-colors text-sm font-bold uppercase tracking-wider"
            >
              Back to Login
            </button>
          </div>
        </div>
      );
    }

    return (
      <div className="flex h-screen w-full bg-[#05060b] text-slate-300 items-center justify-center font-sans">
        <div className="w-full max-w-md p-8 rounded-2xl border border-[#1a1f3c] bg-[#0b0e1a] shadow-[0_0_50px_rgba(243,211,107,0.05)]">
          <div className="flex flex-col items-center mb-8">
            <div className="p-4 bg-[#f3d36b]/10 rounded-full border border-[#f3d36b]/20 mb-4 shadow-[0_0_20px_rgba(243,211,107,0.1)]">
              <Scale className="w-8 h-8 text-[#f3d36b]" />
            </div>
            <h1 className="text-3xl font-serif text-[#f3d36b]">AI Lawyer</h1>
            <p className="text-xs text-slate-500 uppercase tracking-widest mt-2">Enterprise Gateway</p>
          </div>

          <form onSubmit={handleAuth} className="space-y-4">
            {authError && (
              <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm text-center">
                {authError}
              </div>
            )}
            {authSuccess && (
              <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-sm text-center">
                {authSuccess}
              </div>
            )}
            
            {!isLoginMode && (
              <div className="flex gap-4">
                <div className="flex-1">
                  <label className="text-xs font-bold text-slate-400 uppercase tracking-wider">First Name</label>
                  <input 
                    type="text" 
                    value={authFirstName}
                    onChange={e => setAuthFirstName(e.target.value)}
                    required={!isLoginMode}
                    className="w-full mt-1 bg-[#111424] border border-[#1a1f3c] rounded-lg py-3 px-4 text-slate-200 focus:outline-none focus:border-[#f3d36b]/40"
                    placeholder="Harvey"
                  />
                </div>
                <div className="flex-1">
                  <label className="text-xs font-bold text-slate-400 uppercase tracking-wider">Last Name</label>
                  <input 
                    type="text" 
                    value={authLastName}
                    onChange={e => setAuthLastName(e.target.value)}
                    required={!isLoginMode}
                    className="w-full mt-1 bg-[#111424] border border-[#1a1f3c] rounded-lg py-3 px-4 text-slate-200 focus:outline-none focus:border-[#f3d36b]/40"
                    placeholder="Specter"
                  />
                </div>
              </div>
            )}

            <div>
              <label className="text-xs font-bold text-slate-400 uppercase tracking-wider">Email</label>
              <div className="relative mt-1 flex items-center">
                <User className="absolute left-3 w-4 h-4 text-slate-500" />
                <input 
                  type="email" 
                  value={authEmail}
                  onChange={e => setAuthEmail(e.target.value)}
                  required
                  className="w-full bg-[#111424] border border-[#1a1f3c] rounded-lg py-3 pl-10 pr-4 text-slate-200 focus:outline-none focus:border-[#f3d36b]/40"
                  placeholder="lawyer@firm.com"
                />
              </div>
            </div>
            <div>
              <label className="text-xs font-bold text-slate-400 uppercase tracking-wider">Password</label>
              <div className="relative mt-1 flex items-center">
                <Lock className="absolute left-3 w-4 h-4 text-slate-500" />
                <input 
                  type="password" 
                  value={authPassword}
                  onChange={e => setAuthPassword(e.target.value)}
                  required
                  className="w-full bg-[#111424] border border-[#1a1f3c] rounded-lg py-3 pl-10 pr-4 text-slate-200 focus:outline-none focus:border-[#f3d36b]/40"
                  placeholder="••••••••"
                />
              </div>
            </div>
            {!isLoginMode && (
              <div>
                <label className="text-xs font-bold text-slate-400 uppercase tracking-wider">Confirm Password</label>
                <div className="relative mt-1 flex items-center">
                  <Lock className="absolute left-3 w-4 h-4 text-slate-500" />
                  <input 
                    type="password" 
                    value={authConfirmPassword}
                    onChange={e => setAuthConfirmPassword(e.target.value)}
                    required={!isLoginMode}
                    className="w-full bg-[#111424] border border-[#1a1f3c] rounded-lg py-3 pl-10 pr-4 text-slate-200 focus:outline-none focus:border-[#f3d36b]/40"
                    placeholder="••••••••"
                  />
                </div>
              </div>
            )}
            
            <button 
              type="submit"
              className="w-full py-3 mt-4 bg-[#f3d36b] hover:bg-[#e3c05f] text-[#080a15] rounded-lg font-bold transition-all shadow-[0_0_15px_rgba(243,211,107,0.2)]"
            >
              {isLoginMode ? 'Secure Login' : 'Create Account'}
            </button>
          </form>

          <p className="text-center mt-6 text-sm text-slate-500">
            {isLoginMode ? "Don't have an account? " : "Already registered? "}
            <button onClick={() => { setIsLoginMode(!isLoginMode); setAuthError(''); setAuthSuccess(''); }} className="text-[#f3d36b] hover:underline">
              {isLoginMode ? 'Sign Up' : 'Log In'}
            </button>
          </p>
        </div>
      </div>
    );
  }

  // ─── MAIN APP SCREEN ──────────────────────────────────────────
  return (
    <div className="flex h-screen w-full bg-[#080a15] text-slate-300 overflow-hidden font-sans">
      
      {/* ─── SIDEBAR (History) ─────────────────────────────── */}
      <div className={`absolute top-0 left-0 h-full bg-[#030408] border-r border-[#1a1f3c] transition-all duration-300 z-50 shadow-2xl flex flex-col ${isSidebarOpen ? 'w-72 translate-x-0' : 'w-72 -translate-x-full'}`}>
        <div className="p-4 border-b border-[#1a1f3c] flex items-center justify-between shrink-0">
          <div className="flex items-center gap-2 text-slate-300">
            <History className="w-5 h-5 text-[#f3d36b]" />
            <h2 className="font-serif font-bold tracking-wide">Session History</h2>
          </div>
          <div className="flex items-center gap-1">
            <button onClick={startNewSession} className="p-1.5 hover:bg-[#13162b] rounded-md transition-colors text-[#f3d36b] tooltip" title="New Chat">
              <MessageSquare className="w-4 h-4" />
            </button>
            <button onClick={() => setIsSidebarOpen(false)} className="p-1.5 hover:bg-[#13162b] rounded-md transition-colors">
              <X className="w-5 h-5 text-slate-500 hover:text-slate-300" />
            </button>
          </div>
        </div>
        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          {history.length === 0 ? (
            <p className="text-xs text-slate-500 text-center mt-10">No history found.</p>
          ) : (
            history.map((session) => (
              <button 
                key={session.session_id}
                onClick={() => loadPastSession(session)}
                className="w-full text-left p-3 rounded-lg bg-[#0b0e1a] border border-[#1a1f3c] hover:border-[#f3d36b]/40 hover:bg-[#13162b] transition-all group"
              >
                <div className="text-xs text-slate-400 group-hover:text-slate-200 line-clamp-2">
                  {session.messages.find(m => m.role === 'user')?.content || "Empty Session"}
                </div>
                <div className="text-[9px] text-slate-600 mt-2 uppercase tracking-wider">
                  {new Date(session.created_at).toLocaleDateString()}
                </div>
              </button>
            ))
          )}
        </div>
        <div className="p-4 border-t border-[#1a1f3c]">
          <button 
            onClick={handleLogout}
            className="w-full flex items-center justify-center gap-2 py-2.5 rounded-lg bg-red-500/10 text-red-400 hover:bg-red-500/20 transition-colors text-xs font-bold uppercase tracking-wider"
          >
            <LogOut className="w-4 h-4" /> Sign Out
          </button>
        </div>
      </div>

      {/* ─── LEFT PANE (Chat) ─────────────────────────────── */}
      <div className="w-[60%] h-screen flex flex-col gap-2 bg-[#05060b] shadow-2xl relative z-10 p-4 transition-all">
        
        {/* Header */}
        <div className="shrink-0 px-4 py-2.5 rounded-xl border border-[#1a1f3c] bg-[#0b0e1a] flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button onClick={() => setIsSidebarOpen(true)} className="p-2 -ml-2 rounded-lg text-slate-400 hover:text-white hover:bg-[#13162b] transition-colors">
              <Menu className="w-5 h-5" />
            </button>
            <div className="p-2 bg-[#f3d36b]/10 rounded-full border border-[#f3d36b]/20 shadow-[0_0_20px_rgba(243,211,107,0.1)]">
              <Scale className="w-4 h-4 text-[#f3d36b]" />
            </div>
            <button onClick={startNewSession} className="text-left group transition-all">
              <h1 className="text-xl font-serif text-[#f3d36b] tracking-wide group-hover:text-white transition-colors">AI Lawyer</h1>
              <p className="text-[9px] text-slate-400 font-medium tracking-[0.2em] uppercase mt-0.5 group-hover:text-[#f3d36b] transition-colors">New Session</p>
            </button>
          </div>
        </div>

        {/* Upload Zone moved to right pane for more space */}
        {filenames.length > 0 && (
          <div className="shrink-0 px-4 py-2 flex flex-wrap gap-2 border-b border-[#1a1f3c]">
            {filenames.map(name => (
              <button 
                key={name}
                onClick={() => setActivePdf(name)}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium border transition-all duration-300 ${activePdf === name ? 'bg-[#f3d36b]/10 border-[#f3d36b]/40 text-[#f3d36b] shadow-[0_0_10px_rgba(243,211,107,0.1)]' : 'bg-[#13162b] border-[#1a1f3c] text-slate-400'}`}
              >
                <FileText className="w-3.5 h-3.5" /> {name}
              </button>
            ))}
          </div>
        )}

        {scanResult && (
          <details className="shrink-0 rounded-xl bg-[#f3d36b]/5 border border-[#f3d36b]/10 group transition-all duration-300">
            <summary className="flex items-center gap-2 px-4 py-3 cursor-pointer select-none outline-none list-none [&::-webkit-details-marker]:hidden hover:bg-[#f3d36b]/10 transition-colors rounded-xl">
              <Sparkles className="w-3.5 h-3.5 text-[#f3d36b]" />
              <h3 className="text-xs font-bold uppercase tracking-wider text-[#f3d36b]">View Initial Counsel</h3>
              <ChevronDown className="w-3.5 h-3.5 text-[#f3d36b] ml-auto transition-transform duration-300 group-open:-rotate-180" />
            </summary>
            <div className="px-4 pb-4 text-xs text-slate-300 whitespace-pre-wrap leading-relaxed font-serif italic border-t border-[#f3d36b]/10 pt-3 mt-1">
              &quot;{scanResult}&quot;
            </div>
          </details>
        )}

        {filenames.length >= 2 && (
          <div className="shrink-0 px-4 py-2 bg-indigo-500/10 border border-indigo-500/20 rounded-lg flex items-center gap-2 text-indigo-300 text-xs font-medium">
            <GitCompare className="w-4 h-4 text-indigo-400" />
            Comparison Mode Active. Ask the AI to compare the documents above!
          </div>
        )}

        <div className="flex-1 min-h-0 overflow-y-auto p-6 rounded-xl border border-[#1a1f3c] bg-[#0b0e1a] scroll-smooth">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center max-w-md mx-auto space-y-6">
              <div className="w-16 h-16 rounded-full border border-[#f3d36b]/20 flex items-center justify-center bg-[#13162b] shadow-[0_0_30px_rgba(243,211,107,0.05)]">
                <Scale className="w-6 h-6 text-[#f3d36b]" />
              </div>
              <h2 className="text-4xl font-serif text-white leading-tight">Expert analysis for <span className="text-[#f3d36b]">complex legal</span> documents.</h2>
              <p className="text-sm text-slate-400">Upload your contracts or agreements to identify risks, extract key obligations, and draft professional legal summaries.</p>
            </div>
          ) : (
            <div className="space-y-8">
              {messages.map((msg, i) => (
                <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  {msg.role === 'user' ? (
                    <div className="max-w-[80%] rounded-2xl rounded-tr-sm px-6 py-4 border border-[#f3d36b]/20 bg-[#13162b]/50 backdrop-blur-sm text-slate-200 shadow-lg">
                       <p className="text-[10px] font-bold text-[#f3d36b] mb-2 uppercase tracking-widest">You Ask</p>
                       <p className="text-[15px] leading-relaxed italic font-serif">&quot;{msg.content}&quot;</p>
                    </div>
                  ) : (
                    <div className="max-w-[90%] w-full rounded-xl px-6 py-5 border border-[#1a1f3c] bg-[#111424] shadow-[0_8px_30px_rgb(0,0,0,0.5)] group hover:border-[#f3d36b]/30 transition-colors duration-500">
                      {msg.trace && msg.trace.length > 0 && <AgentTrace steps={msg.trace} />}
                      <div className="flex items-center gap-3 mb-4 pb-4 border-b border-[#1a1f3c]">
                        <div className="w-10 h-10 rounded-full bg-[#1a1e36] border border-[#f3d36b]/20 flex items-center justify-center overflow-hidden">
                           {msg.agent === 'Legal Researcher' && <Search className="w-4 h-4 text-[#f3d36b]" />}
                           {msg.agent === 'Risk Assessor' && <ShieldAlert className="w-4 h-4 text-[#f3d36b]" />}
                           {msg.agent === 'Legal Drafter' && <PenTool className="w-4 h-4 text-[#f3d36b]" />}
                           {msg.agent === 'Contract Comparator' && <GitCompare className="w-4 h-4 text-[#f3d36b]" />}
                           {msg.agent === 'Assistant' && <Bot className="w-4 h-4 text-[#f3d36b]" />}
                           {(!msg.agent || msg.agent === 'Unknown') && <Scale className="w-4 h-4 text-[#f3d36b]" />}
                        </div>
                        <div>
                          <h3 className="font-serif text-[#f3d36b] text-lg">{msg.agent || 'AI Counsel'}</h3>
                          <p className="text-[10px] text-slate-500 tracking-widest uppercase mt-0.5">{msg.isStreaming ? 'Streaming...' : 'Specialist Counsel • Complete'}</p>
                        </div>
                      </div>
                      <div className="text-[15px] leading-loose text-slate-300 font-serif whitespace-pre-wrap">
                        {msg.content}
                        {msg.isStreaming && msg.content && <span className="inline-block w-2 h-5 bg-[#f3d36b] ml-0.5 animate-pulse rounded-sm" />}
                      </div>
                      {!msg.isStreaming && msg.agent === 'Legal Drafter' && msg.content && (
                        <div className="mt-6 pt-4 border-t border-[#1a1f3c]">
                          <button 
                            onClick={() => handleDownloadDocx(msg.content)}
                            className="flex items-center gap-2 px-4 py-2 bg-[#f3d36b]/10 text-[#f3d36b] rounded-lg border border-[#f3d36b]/30 hover:bg-[#f3d36b]/20 hover:border-[#f3d36b]/50 transition-all text-xs font-bold uppercase tracking-wider"
                          >
                            <Download className="w-4 h-4" /> Download as .docx
                          </button>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        <div className="shrink-0 p-3 rounded-xl border border-[#1a1f3c] bg-[#0b0e1a]">
          <div className="relative flex items-center max-w-4xl mx-auto">
            <textarea 
              value={chatInput}
              onChange={e => setChatInput(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSendMessage(); } }}
              placeholder={filenames.length > 0 ? "Ask a question about your documents..." : "Upload a document to begin..."}
              disabled={filenames.length === 0 || isTyping}
              className="w-full bg-[#111424] border border-[#1a1f3c] rounded-full py-3 pl-5 pr-12 text-sm text-slate-200 placeholder:text-slate-600 focus:outline-none focus:border-[#f3d36b]/40 resize-none h-12 disabled:opacity-50 disabled:cursor-not-allowed shadow-inner transition-all"
            />
            <button 
              onClick={handleSendMessage}
              disabled={!chatInput.trim() || filenames.length === 0 || isTyping}
              className="absolute right-1.5 p-2 bg-[#f3d36b] hover:bg-[#e3c05f] text-[#080a15] rounded-full disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
            >
              <Send className="w-4 h-4 ml-0.5" />
            </button>
          </div>
        </div>

      </div>

      {/* ─── RIGHT PANE (PDF Viewer) ─────────────────────────────── */}
      <div className="w-[40%] bg-[#05060b] flex flex-col relative border-l border-[#1a1f3c]/50">
        {activePdf ? (
          <div className="w-full h-full p-6 pb-0">
             <div className="w-full h-full rounded-t-xl overflow-hidden shadow-[0_0_40px_rgba(0,0,0,0.8)] border-x border-t border-[#1a1f3c]">
                <iframe src={`http://localhost:8000/pdfs/${activePdf}`} className="w-full h-full border-none bg-[#111424]" title="PDF Viewer" />
             </div>
          </div>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center p-12">
            <div className="w-full max-w-md p-8 rounded-2xl border border-[#1a1f3c] bg-[#0b0e1a] shadow-2xl flex flex-col items-center text-center">
              <div className="w-20 h-20 rounded-full border border-[#f3d36b]/20 flex items-center justify-center mb-6 bg-[#13162b] shadow-[0_0_30px_rgba(243,211,107,0.05)]">
                 <FileText className="w-8 h-8 text-[#f3d36b]" />
              </div>
              <h2 className="text-2xl font-serif text-white mb-2">Workspace Setup</h2>
              <p className="text-sm text-slate-400 mb-8">Upload your legal documents, contracts, or case files to begin analysis.</p>
              
              <label className="flex flex-col items-center justify-center w-full h-32 border border-[#f3d36b]/30 border-dashed rounded-xl cursor-pointer bg-[#13162b]/50 hover:bg-[#1a1e36] hover:border-[#f3d36b] transition-all group">
                <div className="flex flex-col items-center justify-center pt-5 pb-6">
                  {isUploading ? (
                    <Loader2 className="w-8 h-8 text-[#f3d36b] animate-spin mb-3" />
                  ) : (
                    <UploadCloud className="w-8 h-8 text-[#f3d36b]/60 group-hover:text-[#f3d36b] transition-colors mb-3" />
                  )}
                  <p className="text-sm font-medium text-slate-300 group-hover:text-white transition-colors">
                    {isUploading ? "Uploading & Scanning..." : "Click or drag PDFs here"}
                  </p>
                </div>
                <input type="file" className="hidden" accept=".pdf" multiple onChange={handleFileUpload} disabled={isUploading} />
              </label>
            </div>
          </div>
        )}
      </div>
      
    </div>
  );
}
