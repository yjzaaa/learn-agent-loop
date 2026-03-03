"use client";

import { Session } from "./types";
import { Activity, Terminal, Layers } from "lucide-react";

interface StatusBarProps {
  session: Session | null;
  stepCount: number;
  toolCallCount: number;
  isConnected: boolean;
}

export function StatusBar({
  session,
  stepCount,
  toolCallCount,
  isConnected,
}: StatusBarProps) {
  return (
    <footer className="flex items-center justify-between px-5 py-2 bg-deep border-t border-dashed border-border-subtle text-[11px] text-muted">
      {/* Left - Status */}
      <div className="flex items-center gap-4">
        {session ? (
          <div className="flex items-center gap-1.5">
            <div
              className={`w-1.5 h-1.5 rounded-full ${
                session.status === "active"
                  ? "bg-green-500 animate-pulse"
                  : "bg-gray-500"
              }`}
            />
            <span>Ready</span>
          </div>
        ) : (
          <span>Not connected</span>
        )}
      </div>

      {/* Center - Info */}
      <div className="flex items-center gap-6">
        {session && (
          <>
            <div className="flex items-center gap-1.5">
              <Activity className="w-3 h-3" />
              <span>{session.model}</span>
            </div>
            <div className="flex items-center gap-1.5">
              <Layers className="w-3 h-3" />
              <span>{stepCount} steps</span>
            </div>
            <div className="flex items-center gap-1.5">
              <Terminal className="w-3 h-3" />
              <span>{toolCallCount} tool calls</span>
            </div>
          </>
        )}
      </div>

      {/* Right - Connection & Version */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1.5">
          <div
            className={`w-1.5 h-1.5 rounded-full ${
              isConnected ? "bg-green-500" : "bg-red-500"
            }`}
          />
          <span>{isConnected ? "Connected" : "Disconnected"}</span>
        </div>
        <span className="text-border-default">•</span>
        <span>AgentCore v0.1.0</span>
      </div>
    </footer>
  );
}
