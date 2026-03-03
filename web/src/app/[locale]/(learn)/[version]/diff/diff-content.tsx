"use client";

import Link from "next/link";
import { useLocale } from "@/lib/i18n";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { LayerBadge } from "@/components/ui/badge";
import { CodeDiff } from "@/components/diff/code-diff";
import { ArrowLeft, Plus, Minus, FileCode, Wrench, Box, FunctionSquare } from "lucide-react";
import type { AgentVersion } from "@/lib/api-service";

interface VersionMeta {
  title: string;
  subtitle: string;
  coreAddition: string;
  keyInsight: string;
  layer: "tools" | "planning" | "memory" | "concurrency" | "collaboration";
  prevVersion: string | null;
}

interface DiffPageContentProps {
  version: string;
  prevVersion: AgentVersion;
  currentVersion: AgentVersion;
  prevMeta: VersionMeta | null;
  currentMeta: VersionMeta;
}

export function DiffPageContent({
  version,
  prevVersion,
  currentVersion,
  prevMeta,
  currentMeta,
}: DiffPageContentProps) {
  const locale = useLocale();

  // 计算差异
  const locDelta = currentVersion.loc - prevVersion.loc;
  const newTools = currentVersion.tools.filter(t => !prevVersion.tools.includes(t));
  const newClasses = currentVersion.classes.filter(c => !prevVersion.classes.includes(c));
  const newFunctions = currentVersion.functions.filter(f => !prevVersion.functions.includes(f));

  return (
    <div>
      {/* Structural Diff */}
      <div className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2 text-zinc-500 dark:text-zinc-400">
              <FileCode size={16} />
              <span className="text-sm">LOC Delta</span>
            </div>
          </CardHeader>
          <CardTitle>
            <span className={locDelta >= 0 ? "text-green-600 dark:text-green-400" : "text-red-600 dark:text-red-400"}>
              {locDelta >= 0 ? "+" : ""}{locDelta}
            </span>
            <span className="ml-2 text-sm font-normal text-zinc-500">lines</span>
          </CardTitle>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center gap-2 text-zinc-500 dark:text-zinc-400">
              <Wrench size={16} />
              <span className="text-sm">New Tools</span>
            </div>
          </CardHeader>
          <CardTitle>
            <span className="text-blue-600 dark:text-blue-400">{newTools.length}</span>
          </CardTitle>
          {newTools.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1">
              {newTools.map((tool) => (
                <span key={tool} className="rounded bg-blue-100 px-1.5 py-0.5 text-xs text-blue-700 dark:bg-blue-900/30 dark:text-blue-300">
                  {tool}
                </span>
              ))}
            </div>
          )}
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center gap-2 text-zinc-500 dark:text-zinc-400">
              <Box size={16} />
              <span className="text-sm">New Classes</span>
            </div>
          </CardHeader>
          <CardTitle>
            <span className="text-purple-600 dark:text-purple-400">{newClasses.length}</span>
          </CardTitle>
          {newClasses.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1">
              {newClasses.map((cls) => (
                <span key={cls} className="rounded bg-purple-100 px-1.5 py-0.5 text-xs text-purple-700 dark:bg-purple-900/30 dark:text-purple-300">
                  {cls}
                </span>
              ))}
            </div>
          )}
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center gap-2 text-zinc-500 dark:text-zinc-400">
              <FunctionSquare size={16} />
              <span className="text-sm">New Functions</span>
            </div>
          </CardHeader>
          <CardTitle>
            <span className="text-amber-600 dark:text-amber-400">{newFunctions.length}</span>
          </CardTitle>
          {newFunctions.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1">
              {newFunctions.map((fn) => (
                <span key={fn} className="rounded bg-amber-100 px-1.5 py-0.5 text-xs text-amber-700 dark:bg-amber-900/30 dark:text-amber-300">
                  {fn}
                </span>
              ))}
            </div>
          )}
        </Card>
      </div>

      {/* Version Info Comparison */}
      <div className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Card className="border-l-4 border-l-red-300 dark:border-l-red-700">
          <CardHeader>
            <CardTitle>{prevMeta?.title || prevVersion.id}</CardTitle>
            <p className="text-sm text-zinc-500">{prevMeta?.subtitle}</p>
          </CardHeader>
          <div className="space-y-1 text-sm text-zinc-600 dark:text-zinc-400">
            <p>{prevVersion.loc} LOC</p>
            <p>{prevVersion.tools.length} tools: {prevVersion.tools.join(", ")}</p>
            <LayerBadge layer={prevVersion.layer}>{prevVersion.layer}</LayerBadge>
          </div>
        </Card>
        <Card className="border-l-4 border-l-green-300 dark:border-l-green-700">
          <CardHeader>
            <CardTitle>{currentMeta.title}</CardTitle>
            <p className="text-sm text-zinc-500">{currentMeta.subtitle}</p>
          </CardHeader>
          <div className="space-y-1 text-sm text-zinc-600 dark:text-zinc-400">
            <p>{currentVersion.loc} LOC</p>
            <p>{currentVersion.tools.length} tools: {currentVersion.tools.join(", ")}</p>
            <LayerBadge layer={currentVersion.layer}>{currentVersion.layer}</LayerBadge>
          </div>
        </Card>
      </div>

      {/* Code Diff */}
      <div>
        <h2 className="mb-4 text-xl font-semibold">Source Code Diff</h2>
        <CodeDiff
          oldSource={prevVersion.source}
          newSource={currentVersion.source}
          oldLabel={`${prevVersion.id} (${prevVersion.filename})`}
          newLabel={`${version} (${currentVersion.filename})`}
        />
      </div>
    </div>
  );
}
