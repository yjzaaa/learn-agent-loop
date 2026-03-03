/**
 * AgentCore 页面
 * 
 * 基于知识图谱的 Agent 可视化界面
 */

import { AgentCoreDashboard } from "@/components/agentcore/agentcore-dashboard";

export default function AgentCorePage() {
  return (
    <div className="h-screen bg-void text-text-primary overflow-hidden">
      <AgentCoreDashboard />
    </div>
  );
}
