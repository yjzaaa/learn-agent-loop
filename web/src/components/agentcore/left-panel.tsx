"use client";

import { Session, ExecutionStep } from "./types";
import { Clock, ChevronRight, Circle, CheckCircle2, Loader2 } from "lucide-react";

interface LeftPanelProps {
  sessions: Session[];
  currentSession: Session | null;
  steps: ExecutionStep[];
  selectedStep: ExecutionStep | null;
  onSessionSelect: (session: Session) => void;
  onStepSelect: (step: ExecutionStep) => void;
}

export function LeftPanel({
  sessions,
  currentSession,
  steps,
  selectedStep,
  onSessionSelect,
  onStepSelect,
}: LeftPanelProps) {
  return (
    <aside className="w-72 bg-deep border-r border-border-subtle flex flex-col">
      {/* Sessions Section */}
      <div className="flex-1 overflow-y-auto scrollbar-thin">
        <div className="px-4 py-3 text-xs font-semibold text-muted uppercase tracking-wider">
          Sessions ({sessions.length})
        </div>
        
        <div className="px-2 pb-4">
          {sessions.map((session) => (
            <button
              key={session.id}
              onClick={() => onSessionSelect(session)}
              className={`w-full px-3 py-2 rounded-md text-left transition-colors ${
                currentSession?.id === session.id
                  ? "bg-accent/20 text-accent"
                  : "hover:bg-hover text-secondary"
              }`}
            >
              <div className="flex items-center gap-2">
                <div
                  className={`w-2 h-2 rounded-full ${
                    session.status === "active" ? "bg-green-500" : "bg-gray-500"
                  }`}
                />
                <span className="text-sm font-medium truncate">
                  {session.name}
                </span>
              </div>
              <div className="text-xs text-muted mt-1 pl-4">
                {session.total_steps} steps
              </div>
            </button>
          ))}
        </div>

        {/* Steps Section */}
        {currentSession && steps.length > 0 && (
          <>
            <div className="px-4 py-3 text-xs font-semibold text-muted uppercase tracking-wider border-t border-border-subtle">
              Execution Steps
            </div>
            <div className="px-2 pb-4 space-y-1">
              {steps.map((step, index) => (
                <button
                  key={`${step.step_number}-${step.type}-${index}`}
                  onClick={() => onStepSelect(step)}
                  className={`w-full px-3 py-2 rounded-md text-left transition-colors ${
                    selectedStep?.step_number === step.step_number
                      ? "bg-accent/20 border-l-2 border-accent"
                      : "hover:bg-hover border-l-2 border-transparent"
                  }`}
                >
                  <div className="flex items-center gap-2">
                    {step.status === "running" ? (
                      <Loader2 className="w-3.5 h-3.5 text-warning animate-spin" />
                    ) : step.status === "completed" ? (
                      <CheckCircle2 className="w-3.5 h-3.5 text-success" />
                    ) : (
                      <Circle className="w-3.5 h-3.5 text-muted" />
                    )}
                    <span className="text-sm text-secondary">
                      Step {step.step_number}
                    </span>
                    <span className="text-xs text-muted capitalize ml-auto">
                      {step.type}
                    </span>
                  </div>
                  {step.token_count && (
                    <div className="text-xs text-muted mt-1 pl-5">
                      {step.token_count} tokens · {step.duration_ms}ms
                    </div>
                  )}
                </button>
              ))}
            </div>
          </>
        )}
      </div>
    </aside>
  );
}
