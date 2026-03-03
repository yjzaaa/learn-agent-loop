"use client";

/**
 * Header Component
 * 
 * 顶部导航栏 - 包含 Logo、会话选择、搜索和操作按钮
 */

import { useState, useRef, useEffect } from "react";
import {
  Search,
  Settings,
  Plus,
  Play,
  ChevronDown,
  Sparkles,
  Cpu,
} from "lucide-react";
import { Session } from "./types";

interface HeaderProps {
  currentSession: Session | null;
  sessions: Session[];
  isConnected: boolean;
  onSessionSelect: (session: Session) => void;
  onCreateSession: (name: string, workdir: string) => Promise<string | undefined>;
  onRunAgent: (query: string) => Promise<void>;
}

export function Header({
  currentSession,
  sessions,
  isConnected,
  onSessionSelect,
  onCreateSession,
  onRunAgent,
}: HeaderProps) {
  const [isSessionDropdownOpen, setIsSessionDropdownOpen] = useState(false);
  const [isNewSessionModalOpen, setIsNewSessionModalOpen] = useState(false);
  const [newSessionName, setNewSessionName] = useState("");
  const [newSessionWorkdir, setNewSessionWorkdir] = useState("./workspace");
  const [query, setQuery] = useState("");
  const dropdownRef = useRef<HTMLDivElement>(null);

  // 点击外部关闭下拉菜单
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsSessionDropdownOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleCreateSession = async () => {
    const name = newSessionName || `Session ${sessions.length + 1}`;
    await onCreateSession(name, newSessionWorkdir);
    setIsNewSessionModalOpen(false);
    setNewSessionName("");
  };

  const handleRun = async () => {
    if (!query.trim()) return;
    await onRunAgent(query);
    setQuery("");
  };

  return (
    <header className="flex items-center justify-between px-5 py-3 bg-deep border-b border-dashed border-border-subtle">
      {/* Left Section - Logo & Session Selector */}
      <div className="flex items-center gap-4">
        {/* Logo */}
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 flex items-center justify-center bg-gradient-to-br from-accent to-node-interface rounded-lg shadow-glow text-white text-sm font-bold">
            <Cpu className="w-4 h-4" />
          </div>
          <span className="font-semibold text-[15px] tracking-tight text-primary">
            AgentCore
          </span>
        </div>

        {/* Session Selector */}
        <div className="relative" ref={dropdownRef}>
          <button
            onClick={() => setIsSessionDropdownOpen(!isSessionDropdownOpen)}
            className="flex items-center gap-2 px-3 py-1.5 bg-surface border border-border-subtle rounded-lg text-sm text-secondary transition-colors hover:bg-hover"
          >
            <span
              className={`w-1.5 h-1.5 rounded-full ${
                currentSession?.status === "active"
                  ? "bg-node-function animate-pulse"
                  : "bg-text-muted"
              }`}
            />
            <span className="truncate max-w-[180px]">
              {currentSession?.name || "Select Session"}
            </span>
            <ChevronDown
              className={`w-3.5 h-3.5 text-muted transition-transform ${
                isSessionDropdownOpen ? "rotate-180" : ""
              }`}
            />
          </button>

          {/* Session Dropdown */}
          {isSessionDropdownOpen && (
            <div className="absolute top-full left-0 mt-1 w-72 bg-surface border border-border-subtle rounded-lg shadow-xl overflow-hidden z-50">
              {/* New Session Button */}
              <button
                onClick={() => {
                  setIsNewSessionModalOpen(true);
                  setIsSessionDropdownOpen(false);
                }}
                className="w-full px-4 py-3 flex items-center gap-3 text-left hover:bg-hover border-b border-border-subtle"
              >
                <Plus className="w-4 h-4 text-accent" />
                <span className="text-sm font-medium text-primary">
                  New Session
                </span>
              </button>

              {/* Session List */}
              <div className="max-h-64 overflow-y-auto">
                {sessions.map((session) => (
                  <button
                    key={session.id}
                    onClick={() => {
                      onSessionSelect(session);
                      setIsSessionDropdownOpen(false);
                    }}
                    className={`w-full px-4 py-3 flex items-center gap-3 text-left transition-colors ${
                      currentSession?.id === session.id
                        ? "bg-accent/10 border-l-2 border-accent"
                        : "hover:bg-hover border-l-2 border-transparent"
                    }`}
                  >
                    <span
                      className={`w-2 h-2 rounded-full ${
                        session.status === "active"
                          ? "bg-node-function animate-pulse"
                          : "bg-text-muted"
                      }`}
                    />
                    <div className="flex-1 min-w-0">
                      <div
                        className={`text-sm font-medium truncate ${
                          currentSession?.id === session.id
                            ? "text-accent"
                            : "text-primary"
                        }`}
                      >
                        {session.name}
                      </div>
                      <div className="text-xs text-muted mt-0.5">
                        {session.total_steps} steps · {session.model}
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Center - Query Input */}
      <div className="flex-1 max-w-2xl mx-6">
        <div className="flex items-center gap-2 px-4 py-2 bg-surface border border-border-subtle rounded-lg focus-within:border-accent focus-within:ring-2 focus-within:ring-accent/20 transition-all">
          <Sparkles className="w-4 h-4 text-muted" />
          <input
            type="text"
            placeholder={currentSession ? "Enter your query..." : "Select a session first..."}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleRun()}
            className="flex-1 bg-transparent border-none outline-none text-sm text-primary placeholder:text-muted"
            disabled={!currentSession}
          />
          <button
            onClick={handleRun}
            disabled={!currentSession || !query.trim()}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-accent text-white text-sm font-medium rounded-md hover:bg-accent-dim disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Play className="w-3.5 h-3.5" />
            Run
          </button>
        </div>
      </div>

      {/* Right Section - Actions */}
      <div className="flex items-center gap-3">
        {/* Connection Status */}
        <div className="flex items-center gap-2 px-3 py-1.5 bg-surface rounded-lg">
          <div
            className={`w-2 h-2 rounded-full ${
              isConnected
                ? "bg-green-500 animate-pulse"
                : "bg-gray-500"
            }`}
          />
          <span className="text-xs text-muted">
            {isConnected ? "Live" : "Offline"}
          </span>
        </div>
        
        <button className="w-9 h-9 flex items-center justify-center rounded-md text-secondary hover:bg-hover hover:text-primary transition-colors">
          <Search className="w-[18px] h-[18px]" />
        </button>
        <button className="w-9 h-9 flex items-center justify-center rounded-md text-secondary hover:bg-hover hover:text-primary transition-colors">
          <Settings className="w-[18px] h-[18px]" />
        </button>
      </div>

      {/* New Session Modal */}
      {isNewSessionModalOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-surface border border-border-subtle rounded-lg p-6 w-96">
            <h3 className="text-lg font-semibold text-primary mb-4">
              New Session
            </h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-secondary mb-1">
                  Name
                </label>
                <input
                  type="text"
                  value={newSessionName}
                  onChange={(e) => setNewSessionName(e.target.value)}
                  placeholder="Session name"
                  className="w-full px-3 py-2 bg-elevated border border-border-subtle rounded-md text-sm text-primary placeholder:text-muted focus:outline-none focus:border-accent"
                />
              </div>
              <div>
                <label className="block text-sm text-secondary mb-1">
                  Working Directory
                </label>
                <input
                  type="text"
                  value={newSessionWorkdir}
                  onChange={(e) => setNewSessionWorkdir(e.target.value)}
                  placeholder="./workspace"
                  className="w-full px-3 py-2 bg-elevated border border-border-subtle rounded-md text-sm text-primary placeholder:text-muted focus:outline-none focus:border-accent"
                />
              </div>
            </div>
            <div className="flex justify-end gap-2 mt-6">
              <button
                onClick={() => setIsNewSessionModalOpen(false)}
                className="px-4 py-2 text-sm text-secondary hover:text-primary transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateSession}
                className="px-4 py-2 bg-accent text-white text-sm font-medium rounded-md hover:bg-accent-dim transition-colors"
              >
                Create
              </button>
            </div>
          </div>
        </div>
      )}
    </header>
  );
}
