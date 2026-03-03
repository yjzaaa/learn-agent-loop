"use client";

/**
 * AgentCore Dashboard
 * 
 * 主仪表板组件 - 三栏布局
 */

import { useState } from "react";
import { Header } from "./header";
import { LeftPanel } from "./left-panel";
import { RightPanel } from "./right-panel";
import { GraphCanvas } from "./graph-canvas";
import { StatusBar } from "./status-bar";
import { useAgentCore, ExecutionStep } from "@/hooks/useAgentCore";

export function AgentCoreDashboard() {
  const {
    sessions,
    currentSession,
    steps,
    toolCalls,
    isLoading,
    error,
    isConnected,
    createSession,
    runAgent,
    selectSession,
  } = useAgentCore();

  const [selectedStep, setSelectedStep] = useState<ExecutionStep | null>(null);

  return (
    <div className="flex flex-col h-screen bg-void">
      {/* Error Toast */}
      {error && (
        <div className="fixed top-4 right-4 z-50 px-4 py-3 bg-error/10 border border-error/30 rounded-lg">
          <span className="text-sm text-error">{error}</span>
        </div>
      )}

      {/* Header */}
      <Header
        currentSession={currentSession}
        sessions={sessions}
        isConnected={isConnected}
        onSessionSelect={selectSession}
        onCreateSession={createSession}
        onRunAgent={runAgent}
      />

      {/* Main Content */}
      <main className="flex-1 flex min-h-0">
        {/* Left Panel */}
        <LeftPanel
          sessions={sessions}
          currentSession={currentSession}
          steps={steps}
          selectedStep={selectedStep}
          onSessionSelect={selectSession}
          onStepSelect={setSelectedStep}
        />

        {/* Graph Canvas */}
        <div className="flex-1 relative min-w-0">
          <GraphCanvas
            session={currentSession}
            steps={steps}
            toolCalls={toolCalls}
            selectedStep={selectedStep}
            onStepSelect={setSelectedStep}
            isLoading={isLoading}
          />
        </div>

        {/* Right Panel */}
        <RightPanel
          session={currentSession}
          selectedStep={selectedStep}
          toolCalls={toolCalls}
          onRunAgent={runAgent}
        />
      </main>

      {/* Status Bar */}
      <StatusBar
        session={currentSession}
        stepCount={steps.length}
        toolCallCount={toolCalls.length}
        isConnected={isConnected}
      />
    </div>
  );
}
