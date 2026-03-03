"use client";

import { useState, useMemo } from "react";
import { diffLines, diffWords, Change } from "diff";
import { cn } from "@/lib/utils";

interface CodeDiffProps {
  oldSource: string;
  newSource: string;
  oldLabel: string;
  newLabel: string;
}

export function CodeDiff({ oldSource, newSource, oldLabel, newLabel }: CodeDiffProps) {
  const [viewMode, setViewMode] = useState<"unified" | "split">("unified");
  const [showInlineDiff, setShowInlineDiff] = useState(false);

  const changes = useMemo(() => diffLines(oldSource, newSource), [oldSource, newSource]);

  // 统计信息
  const stats = useMemo(() => {
    let added = 0;
    let removed = 0;
    for (const change of changes) {
      const lines = change.value.split('\n').filter(l => l.length > 0 || change.value.includes('\n'));
      if (change.added) added += lines.length;
      if (change.removed) removed += lines.length;
    }
    return { added, removed };
  }, [changes]);

  return (
    <div className="rounded-lg border border-zinc-200 dark:border-zinc-700 overflow-hidden">
      {/* Header */}
      <div className="flex flex-col gap-3 bg-zinc-50 dark:bg-zinc-900 px-4 py-3 border-b border-zinc-200 dark:border-zinc-700">
        {/* 第一行：文件名和统计 */}
        <div className="flex items-center gap-3 min-w-0">
          <div className="min-w-0 flex-1 truncate text-sm">
            <span className="font-medium text-zinc-700 dark:text-zinc-300">{oldLabel}</span>
            <span className="mx-2 text-zinc-400">→</span>
            <span className="font-medium text-zinc-700 dark:text-zinc-300">{newLabel}</span>
          </div>
          {/* 统计 */}
          <div className="flex items-center gap-2 text-xs shrink-0">
            {stats.removed > 0 && (
              <span className="px-1.5 py-0.5 rounded bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-400 font-medium">
                -{stats.removed}
              </span>
            )}
            {stats.added > 0 && (
              <span className="px-1.5 py-0.5 rounded bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-400 font-medium">
                +{stats.added}
              </span>
            )}
          </div>
        </div>
        
        {/* 第二行：控制按钮 */}
        <div className="flex items-center gap-2 flex-wrap">
          {/* 内联差异开关 - 改为按钮风格 */}
          <button
            onClick={() => setShowInlineDiff(!showInlineDiff)}
            className={cn(
              "min-h-[32px] px-3 text-xs font-medium transition-colors rounded-md border",
              showInlineDiff
                ? "bg-green-600 text-white border-green-600 dark:bg-green-600 dark:border-green-600"
                : "bg-white text-zinc-600 border-zinc-200 hover:border-zinc-400 dark:bg-zinc-800 dark:text-zinc-400 dark:border-zinc-700 dark:hover:border-zinc-500"
            )}
          >
            {showInlineDiff ? "Inline: On" : "Inline: Off"}
          </button>
          
          {/* 视图模式切换 */}
          <div className="flex shrink-0 gap-2">
            <button
              onClick={() => setViewMode("unified")}
              className={cn(
                "min-h-[32px] px-3 text-xs font-medium transition-colors rounded-md border",
                viewMode === "unified"
                  ? "bg-green-600 text-white border-green-600 dark:bg-green-600 dark:border-green-600"
                  : "bg-white text-zinc-600 border-zinc-200 hover:border-zinc-400 dark:bg-zinc-800 dark:text-zinc-400 dark:border-zinc-700 dark:hover:border-zinc-500"
              )}
            >
              Unified
            </button>
            <button
              onClick={() => setViewMode("split")}
              className={cn(
                "min-h-[32px] px-3 text-xs font-medium transition-colors rounded-md border sm:inline-flex hidden",
                viewMode === "split"
                  ? "bg-green-600 text-white border-green-600 dark:bg-green-600 dark:border-green-600"
                  : "bg-white text-zinc-600 border-zinc-200 hover:border-zinc-400 dark:bg-zinc-800 dark:text-zinc-400 dark:border-zinc-700 dark:hover:border-zinc-500"
              )}
            >
              Split
            </button>
          </div>
        </div>
      </div>

      {/* Diff Content */}
      {viewMode === "unified" ? (
        <UnifiedView 
          changes={changes} 
          oldSource={oldSource}
          newSource={newSource}
          showInlineDiff={showInlineDiff} 
        />
      ) : (
        <SplitView changes={changes} />
      )}
    </div>
  );
}

function UnifiedView({ 
  changes, 
  oldSource,
  newSource,
  showInlineDiff 
}: { 
  changes: Change[]; 
  oldSource: string;
  newSource: string;
  showInlineDiff: boolean;
}) {
  let oldLine = 1;
  let newLine = 1;

  // 收集所有行
  const rows: { 
    oldNum: number | null; 
    newNum: number | null; 
    type: "add" | "remove" | "context"; 
    text: string;
    oldText?: string;
    newText?: string;
  }[] = [];

  // 先收集所有变更块
  const changeBlocks: { type: "add" | "remove" | "context"; lines: string[] }[] = [];
  
  for (const change of changes) {
    const lines = change.value.replace(/\n$/, "").split("\n");
    if (change.added) {
      changeBlocks.push({ type: "add", lines });
    } else if (change.removed) {
      changeBlocks.push({ type: "remove", lines });
    } else {
      changeBlocks.push({ type: "context", lines });
    }
  }

  // 处理行，配对删除和添加
  for (let i = 0; i < changeBlocks.length; i++) {
    const block = changeBlocks[i];
    
    if (block.type === "remove") {
      // 检查下一个块是否是添加（配对修改）
      const nextBlock = changeBlocks[i + 1];
      if (nextBlock?.type === "add") {
        // 这是修改：删除 + 添加
        const maxLines = Math.max(block.lines.length, nextBlock.lines.length);
        for (let j = 0; j < maxLines; j++) {
          const oldText = block.lines[j] ?? "";
          const newText = nextBlock.lines[j] ?? "";
          rows.push({
            oldNum: j < block.lines.length ? oldLine++ : null,
            newNum: j < nextBlock.lines.length ? newLine++ : null,
            type: j < block.lines.length ? "remove" : "add",
            text: j < block.lines.length ? oldText : newText,
            oldText,
            newText,
          });
        }
        i++; // 跳过下一个块（已处理）
      } else {
        // 纯删除
        for (const line of block.lines) {
          rows.push({ oldNum: oldLine++, newNum: null, type: "remove", text: line, oldText: line, newText: "" });
        }
      }
    } else if (block.type === "add") {
      // 纯添加（未配对的）
      for (const line of block.lines) {
        rows.push({ oldNum: null, newNum: newLine++, type: "add", text: line, oldText: "", newText: line });
      }
    } else {
      // 上下文
      for (const line of block.lines) {
        rows.push({ oldNum: oldLine++, newNum: newLine++, type: "context", text: line });
      }
    }
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse font-mono text-sm">
        <tbody>
          {rows.map((row, i) => (
            <DiffRow 
              key={i} 
              row={row} 
              showInlineDiff={showInlineDiff}
            />
          ))}
        </tbody>
      </table>
    </div>
  );
}

function SplitView({ changes }: { changes: Change[] }) {
  let oldLine = 1;
  let newLine = 1;

  type SplitRow = {
    left: { num: number | null; text: string; type: "remove" | "context" | "empty" };
    right: { num: number | null; text: string; type: "add" | "context" | "empty" };
  };

  const rows: SplitRow[] = [];

  for (const change of changes) {
    const lines = change.value.replace(/\n$/, "").split("\n");
    if (change.removed) {
      for (const line of lines) {
        rows.push({
          left: { num: oldLine++, text: line, type: "remove" },
          right: { num: null, text: "", type: "empty" },
        });
      }
    } else if (change.added) {
      let filled = 0;
      for (const line of lines) {
        const lastUnfilled = rows.length - lines.length + filled;
        if (
          lastUnfilled >= 0 &&
          lastUnfilled < rows.length &&
          rows[lastUnfilled].right.type === "empty" &&
          rows[lastUnfilled].left.type === "remove"
        ) {
          rows[lastUnfilled].right = { num: newLine++, text: line, type: "add" };
        } else {
          rows.push({
            left: { num: null, text: "", type: "empty" },
            right: { num: newLine++, text: line, type: "add" },
          });
        }
        filled++;
      }
    } else {
      for (const line of lines) {
        rows.push({
          left: { num: oldLine++, text: line, type: "context" },
          right: { num: newLine++, text: line, type: "context" },
        });
      }
    }
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse font-mono text-sm">
        <tbody>
          {rows.map((row, i) => (
            <tr key={i}>
              {/* Left side */}
              <td className={cn(
                "w-12 select-none px-2 text-right text-zinc-500 dark:text-zinc-600",
                row.left.type === "remove" && "bg-red-50 dark:bg-red-950/20",
                row.left.type === "context" && "bg-zinc-50 dark:bg-zinc-900",
                row.left.type === "empty" && "bg-zinc-50 dark:bg-zinc-900"
              )}>
                {row.left.num ?? ""}
              </td>
              <td className={cn(
                "w-6 select-none text-center text-xs font-medium",
                row.left.type === "remove" && "bg-red-50 text-red-600 dark:bg-red-950/20 dark:text-red-400",
                row.left.type === "context" && "bg-zinc-50 text-zinc-400 dark:bg-zinc-900",
                row.left.type === "empty" && "bg-zinc-50 dark:bg-zinc-900"
              )}>
                {row.left.type === "remove" ? "-" : row.left.type === "context" ? " " : ""}
              </td>
              <td className={cn(
                "w-1/2 border-r border-zinc-200 dark:border-zinc-700 whitespace-pre px-3 py-0.5",
                row.left.type === "remove" && "bg-red-50 text-red-900 dark:bg-red-950/20 dark:text-red-200",
                row.left.type === "context" && "text-zinc-800 dark:text-zinc-300",
                row.left.type === "empty" && "bg-zinc-50 dark:bg-zinc-900"
              )}>
                {row.left.text}
              </td>

              {/* Right side */}
              <td className={cn(
                "w-12 select-none px-2 text-right text-zinc-500 dark:text-zinc-600",
                row.right.type === "add" && "bg-green-50 dark:bg-green-950/20",
                row.right.type === "context" && "bg-zinc-50 dark:bg-zinc-900",
                row.right.type === "empty" && "bg-zinc-50 dark:bg-zinc-900"
              )}>
                {row.right.num ?? ""}
              </td>
              <td className={cn(
                "w-6 select-none text-center text-xs font-medium",
                row.right.type === "add" && "bg-green-50 text-green-600 dark:bg-green-950/20 dark:text-green-400",
                row.right.type === "context" && "bg-zinc-50 text-zinc-400 dark:bg-zinc-900",
                row.right.type === "empty" && "bg-zinc-50 dark:bg-zinc-900"
              )}>
                {row.right.type === "add" ? "+" : row.right.type === "context" ? " " : ""}
              </td>
              <td className={cn(
                "w-1/2 whitespace-pre px-3 py-0.5",
                row.right.type === "add" && "bg-green-50 text-green-900 dark:bg-green-950/20 dark:text-green-200",
                row.right.type === "context" && "text-zinc-800 dark:text-zinc-300",
                row.right.type === "empty" && "bg-zinc-50 dark:bg-zinc-900"
              )}>
                {row.right.text}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// 内联高亮组件
function InlineDiff({ oldText, newText }: { oldText: string; newText: string }) {
  const parts = useMemo(() => {
    return diffWords(oldText, newText);
  }, [oldText, newText]);

  return (
    <span>
      {parts.map((part, i) => {
        if (part.added) {
          return (
            <ins 
              key={i} 
              className="bg-green-400/40 dark:bg-green-500/50 text-green-900 dark:text-green-100 rounded px-0.5 no-underline font-semibold"
            >
              {part.value}
            </ins>
          );
        }
        if (part.removed) {
          return (
            <del 
              key={i} 
              className="bg-red-400/40 dark:bg-red-500/50 text-red-900 dark:text-red-100 rounded px-0.5 line-through"
            >
              {part.value}
            </del>
          );
        }
        return <span key={i}>{part.value}</span>;
      })}
    </span>
  );
}

// 统一的行组件
function DiffRow({ 
  row, 
  showInlineDiff,
}: { 
  row: { 
    oldNum: number | null; 
    newNum: number | null; 
    type: "add" | "remove" | "context"; 
    text: string;
    oldText?: string;
    newText?: string;
  };
  showInlineDiff: boolean;
}) {
  // 渲染内容，支持内联差异
  const renderContent = () => {
    // 只有修改的行才显示内联差异
    if (showInlineDiff && row.type !== "context" && row.oldText !== undefined && row.newText !== undefined) {
      if (row.type === "remove") {
        return <InlineDiff oldText={row.oldText} newText={row.newText} />;
      } else {
        return <InlineDiff oldText={row.oldText} newText={row.newText} />;
      }
    }
    return <span>{row.text}</span>;
  };

  return (
    <tr
      className={cn(
        row.type === "add" && "bg-green-100/50 dark:bg-green-900/20",
        row.type === "remove" && "bg-red-100/50 dark:bg-red-900/20",
        "hover:bg-opacity-80 transition-colors"
      )}
    >
      {/* 左侧行号 */}
      <td className={cn(
        "w-14 select-none px-3 text-right text-xs text-zinc-500 dark:text-zinc-600 border-r border-zinc-200 dark:border-zinc-700",
        row.type === "add" && "bg-green-100 dark:bg-green-900/30",
        row.type === "remove" && "bg-red-100 dark:bg-red-900/30",
        row.type === "context" && "bg-zinc-50 dark:bg-zinc-900/50"
      )}>
        {row.oldNum ?? ""}
      </td>

      {/* 右侧行号 */}
      <td className={cn(
        "w-14 select-none px-3 text-right text-xs text-zinc-500 dark:text-zinc-600 border-r border-zinc-200 dark:border-zinc-700",
        row.type === "add" && "bg-green-100 dark:bg-green-900/30",
        row.type === "remove" && "bg-red-100 dark:bg-red-900/30",
        row.type === "context" && "bg-zinc-50 dark:bg-zinc-900/50"
      )}>
        {row.newNum ?? ""}
      </td>

      {/* 标记 */}
      <td className={cn(
        "w-8 select-none text-center text-xs font-bold border-r border-zinc-200 dark:border-zinc-700",
        row.type === "add" && "text-green-600 dark:text-green-400",
        row.type === "remove" && "text-red-600 dark:text-red-400",
        row.type === "context" && "text-zinc-400 dark:text-zinc-600"
      )}>
        {row.type === "add" ? "+" : row.type === "remove" ? "−" : " "}
      </td>

      {/* 代码内容 */}
      <td className={cn(
        "whitespace-pre px-4 py-0.5",
        row.type === "add" && "text-green-900 dark:text-green-200",
        row.type === "remove" && "text-red-900 dark:text-red-200",
        row.type === "context" && "text-zinc-800 dark:text-zinc-300"
      )}>
        {renderContent()}
      </td>
    </tr>
  );
}
