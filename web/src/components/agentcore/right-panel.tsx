"use client";

import { useState } from "react";
import { Session, ExecutionStep, ToolCall } from "./types";
import { MessageSquare, Terminal, Info } from "lucide-react";
import { ToolCallCard } from "./tool-call-card";

interface RightPanelProps {
  session: Session | null;
  selectedStep: ExecutionStep | null;
  toolCalls: ToolCall[];
  onRunAgent: (query: string) => Promise<void>;
}

export function RightPanel({
  session,
  selectedStep,
  toolCalls,
  onRunAgent,
}: RightPanelProps) {
  const [activeTab, setActiveTab] = useState<"details" | "chat" | "tools">("details");

  return (
    <aside className="w-80 bg-deep border-l border-border-subtle flex flex-col">
      {/* Tabs */}
      <div className="flex border-b border-border-subtle">
        <button
          onClick={() => setActiveTab("details")}
          className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
            activeTab === "details"
              ? "text-accent border-b-2 border-accent"
              : "text-secondary hover:text-primary"
          }`}
        >
          <div className="flex items-center justify-center gap-2">
            <Info className="w-4 h-4" />
            Details
          </div>
        </button>
        <button
          onClick={() => setActiveTab("tools")}
          className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
            activeTab === "tools"
              ? "text-accent border-b-2 border-accent"
              : "text-secondary hover:text-primary"
          }`}
        >
          <div className="flex items-center justify-center gap-2">
            <Terminal className="w-4 h-4" />
            Tools
          </div>
        </button>
        <button
          onClick={() => setActiveTab("chat")}
          className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
            activeTab === "chat"
              ? "text-accent border-b-2 border-accent"
              : "text-secondary hover:text-primary"
          }`}
        >
          <div className="flex items-center justify-center gap-2">
            <MessageSquare className="w-4 h-4" />
            Chat
          </div>
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto scrollbar-thin p-4">
        {activeTab === "details" && (
          <div className="space-y-4">
            {session ? (
              <>
                <div className="panel">
                  <div className="panel-header">Session Info</div>
                  <div className="panel-content space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-muted">Name</span>
                      <span className="text-primary">{session.name}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted">ID</span>
                      <span className="text-primary font-mono text-xs">
                        {session.id}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted">Model</span>
                      <span className="text-primary">{session.model}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted">Status</span>
                      <span className="text-success capitalize">{session.status}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted">Steps</span>
                      <span className="text-primary">{session.total_steps}</span>
                    </div>
                  </div>
                </div>

                {selectedStep && (
                  <div className="panel">
                    <div className="panel-header">Step Details</div>
                    <div className="panel-content space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-muted">Step #</span>
                        <span className="text-primary">{selectedStep.step_number}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted">Type</span>
                        <span className="text-primary capitalize">
                          {selectedStep.type}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted">Status</span>
                        <span className="text-primary capitalize">
                          {selectedStep.status}
                        </span>
                      </div>
                      {selectedStep.token_count && (
                        <div className="flex justify-between">
                          <span className="text-muted">Tokens</span>
                          <span className="text-primary">
                            {selectedStep.token_count}
                          </span>
                        </div>
                      )}
                      {selectedStep.duration_ms && (
                        <div className="flex justify-between">
                          <span className="text-muted">Duration</span>
                          <span className="text-primary">
                            {selectedStep.duration_ms}ms
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </>
            ) : (
              <div className="text-center text-muted py-8">
                No session selected
              </div>
            )}
          </div>
        )}

        {activeTab === "tools" && (
          <div className="space-y-2">
            {toolCalls.length > 0 ? (
              toolCalls.map((tool) => (
                <ToolCallCard
                  key={tool.id}
                  toolCall={tool}
                  defaultExpanded={false}
                />
              ))
            ) : (
              <div className="text-center text-muted py-8">
                No tool calls yet
              </div>
            )}
          </div>
        )}

        {activeTab === "chat" && (
          <div className="text-center text-muted py-8">
            Chat functionality coming soon...
          </div>
        )}
      </div>
    </aside>
  );
}
