"use client";

/**
 * ToolCallCard Component
 * 
 * 显示工具调用的卡片组件
 */

import { useState } from "react";
import { ChevronDown, ChevronRight, Terminal, Check, X, Loader2 } from "lucide-react";

interface ToolCallCardProps {
  toolCall: {
    id: string;
    name: string;
    arguments: string;
    output?: string;
    status: string;
    duration_ms?: number;
  };
  defaultExpanded?: boolean;
}

export function ToolCallCard({ toolCall, defaultExpanded = false }: ToolCallCardProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);

  const getStatusIcon = () => {
    switch (toolCall.status) {
      case "running":
        return <Loader2 className="w-4 h-4 text-warning animate-spin" />;
      case "success":
        return <Check className="w-4 h-4 text-success" />;
      case "error":
        return <X className="w-4 h-4 text-error" />;
      default:
        return <Terminal className="w-4 h-4 text-muted" />;
    }
  };

  const getStatusColor = () => {
    switch (toolCall.status) {
      case "running":
        return "bg-warning/10 border-warning/30";
      case "success":
        return "bg-success/10 border-success/30";
      case "error":
        return "bg-error/10 border-error/30";
      default:
        return "bg-surface border-border-subtle";
    }
  };

  const formatArgs = (args: string) => {
    try {
      const parsed = JSON.parse(args);
      return JSON.stringify(parsed, null, 2);
    } catch {
      return args;
    }
  };

  return (
    <div
      className={`rounded-lg border overflow-hidden transition-all ${getStatusColor()}`}
    >
      {/* Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center gap-2 px-3 py-2.5 text-left hover:bg-white/5 transition-colors"
      >
        {isExpanded ? (
          <ChevronDown className="w-4 h-4 text-muted" />
        ) : (
          <ChevronRight className="w-4 h-4 text-muted" />
        )}
        
        {getStatusIcon()}
        
        <span className="flex-1 text-sm font-medium text-primary truncate">
          {toolCall.name}
        </span>
        
        {toolCall.duration_ms && (
          <span className="text-xs text-muted">
            {toolCall.duration_ms}ms
          </span>
        )}
        
        <span
          className={`text-xs capitalize ${
            toolCall.status === "success"
              ? "text-success"
              : toolCall.status === "error"
              ? "text-error"
              : "text-warning"
          }`}
        >
          {toolCall.status}
        </span>
      </button>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="border-t border-border-subtle/50">
          {/* Arguments */}
          <div className="px-3 py-2 border-b border-border-subtle/50">
            <div className="text-[10px] uppercase tracking-wider text-muted mb-1.5">
              Arguments
            </div>
            <pre className="text-xs text-secondary bg-elevated/50 rounded p-2 overflow-x-auto font-mono">
              {formatArgs(toolCall.arguments)}
            </pre>
          </div>

          {/* Output */}
          {toolCall.output && (
            <div className="px-3 py-2">
              <div className="text-[10px] uppercase tracking-wider text-muted mb-1.5">
                Output
              </div>
              <div className="max-h-[300px] overflow-y-auto">
                <pre className="text-xs text-secondary bg-elevated/50 rounded p-2 overflow-x-auto font-mono whitespace-pre-wrap">
                  {toolCall.output.length > 2000
                    ? toolCall.output.slice(0, 2000) + "\n\n... (truncated)"
                    : toolCall.output}
                </pre>
              </div>
            </div>
          )}

          {/* Running State */}
          {toolCall.status === "running" && !toolCall.output && (
            <div className="px-3 py-3 flex items-center gap-2 text-xs text-muted">
              <Loader2 className="w-3 h-3 animate-spin" />
              <span>Executing...</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
