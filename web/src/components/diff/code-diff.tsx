"use client";

import { useState, useMemo, useRef, useCallback, useEffect } from "react";
import { diffLines, diffWords, Change } from "diff";
import { cn } from "@/lib/utils";
import { useTranslations } from "@/lib/i18n";

interface CodeDiffProps {
  oldSource: string;
  newSource: string;
  oldLabel: string;
  newLabel: string;
}

export function CodeDiff({ oldSource, newSource, oldLabel, newLabel }: CodeDiffProps) {
  const t = useTranslations("diff");
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
      <div className="flex items-center justify-between gap-4 bg-zinc-50 dark:bg-zinc-900 px-4 py-3 border-b border-zinc-200 dark:border-zinc-700">
        {/* 左侧：文件名和统计 */}
        <div className="flex items-center gap-3 min-w-0">
          <div className="min-w-0 truncate text-sm">
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
        
        {/* 右侧：控制按钮 - 三个按钮放在同一个 flex 容器中 */}
        <div className="flex items-center gap-2 shrink-0">
          <button
            onClick={() => setShowInlineDiff(!showInlineDiff)}
            className={cn(
              "h-8 px-3 text-xs font-medium transition-colors rounded-md border inline-flex items-center justify-center",
              showInlineDiff
                ? "bg-green-600 text-white border-green-600 dark:bg-green-600 dark:border-green-600"
                : "bg-white text-zinc-600 border-zinc-200 hover:border-zinc-400 dark:bg-zinc-800 dark:text-zinc-400 dark:border-zinc-700 dark:hover:border-zinc-500"
            )}
          >
            {showInlineDiff ? t("inline_on") : t("inline_off")}
          </button>
          <button
            onClick={() => setViewMode("unified")}
            className={cn(
              "h-8 px-3 text-xs font-medium transition-colors rounded-md border inline-flex items-center justify-center",
              viewMode === "unified"
                ? "bg-green-600 text-white border-green-600 dark:bg-green-600 dark:border-green-600"
                : "bg-white text-zinc-600 border-zinc-200 hover:border-zinc-400 dark:bg-zinc-800 dark:text-zinc-400 dark:border-zinc-700 dark:hover:border-zinc-500"
            )}
          >
            {t("unified")}
          </button>
          <button
            onClick={() => setViewMode("split")}
            className={cn(
              "h-8 px-3 text-xs font-medium transition-colors rounded-md border sm:inline-flex hidden items-center justify-center",
              viewMode === "split"
                ? "bg-green-600 text-white border-green-600 dark:bg-green-600 dark:border-green-600"
                : "bg-white text-zinc-600 border-zinc-200 hover:border-zinc-400 dark:bg-zinc-800 dark:text-zinc-400 dark:border-zinc-700 dark:hover:border-zinc-500"
            )}
          >
            {t("split")}
          </button>
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
    <div className="overflow-auto scrollbar-thin scrollbar-thumb-zinc-300 dark:scrollbar-thumb-zinc-600" style={{ maxHeight: "70vh" }}>
      <table className="w-full border-collapse font-mono text-sm min-w-[600px]">
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
  const containerRef = useRef<HTMLDivElement>(null);
  const leftPaneRef = useRef<HTMLDivElement>(null);
  const rightPaneRef = useRef<HTMLDivElement>(null);
  const [splitRatio, setSplitRatio] = useState(50);
  const [isDragging, setIsDragging] = useState(false);
  const isDraggingRef = useRef(false);

  // Handle drag start
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    isDraggingRef.current = true;
    setIsDragging(true);
  }, []);

  // Handle drag movement - using refs to avoid re-renders during drag
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isDraggingRef.current || !containerRef.current || !leftPaneRef.current || !rightPaneRef.current) return;
      
      const rect = containerRef.current.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const ratio = Math.max(20, Math.min(80, (x / rect.width) * 100));
      
      // Direct DOM manipulation for smooth dragging (no React re-render)
      leftPaneRef.current.style.width = `${ratio}%`;
      rightPaneRef.current.style.width = `calc(${100 - ratio}% - 1rem)`;
    };

    const handleMouseUp = () => {
      if (isDraggingRef.current) {
        isDraggingRef.current = false;
        setIsDragging(false);
        document.body.style.cursor = "";
        document.body.style.userSelect = "";
        
        // Sync React state with final DOM value
        if (containerRef.current && leftPaneRef.current) {
          const rect = containerRef.current.getBoundingClientRect();
          const leftWidth = leftPaneRef.current.getBoundingClientRect().width;
          const ratio = Math.max(20, Math.min(80, (leftWidth / rect.width) * 100));
          setSplitRatio(ratio);
        }
      }
    };

    document.addEventListener("mousemove", handleMouseMove);
    document.addEventListener("mouseup", handleMouseUp);

    return () => {
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
    };
  }, []);

  // Apply body styles when dragging starts
  useEffect(() => {
    if (isDragging) {
      document.body.style.cursor = "col-resize";
      document.body.style.userSelect = "none";
    }
  }, [isDragging]);

  // Apply split ratio when it changes (and not dragging)
  useEffect(() => {
    if (!isDraggingRef.current && leftPaneRef.current && rightPaneRef.current) {
      leftPaneRef.current.style.width = `${splitRatio}%`;
      rightPaneRef.current.style.width = `calc(${100 - splitRatio}% - 1rem)`;
    }
  }, [splitRatio]);

  // Sync scroll between left and right panes
  const handleLeftScroll = useCallback(() => {
    if (rightPaneRef.current && leftPaneRef.current) {
      rightPaneRef.current.scrollTop = leftPaneRef.current.scrollTop;
    }
  }, []);

  const handleRightScroll = useCallback(() => {
    if (leftPaneRef.current && rightPaneRef.current) {
      leftPaneRef.current.scrollTop = rightPaneRef.current.scrollTop;
    }
  }, []);

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
    <div 
      ref={containerRef}
      className="flex"
      style={{ height: "70vh" }}
    >
      {/* Left side with its own scrollbar */}
      <div 
        ref={leftPaneRef}
        style={{ width: `${splitRatio}%` }} 
        className="flex-shrink-0 overflow-auto scrollbar-thin scrollbar-thumb-zinc-300 dark:scrollbar-thumb-zinc-600"
        onScroll={handleLeftScroll}
      >
        <table className="w-full border-collapse font-mono text-sm min-w-[300px]">
          <colgroup>
            <col className="w-12" />
            <col className="w-6" />
            <col className="w-full" />
          </colgroup>
          <tbody>
            {rows.map((row, i) => (
              <tr key={`left-${i}`}>
                <td className={cn(
                  "select-none px-2 text-right text-zinc-500 dark:text-zinc-600",
                  row.left.type === "remove" && "bg-red-50 dark:bg-red-950/20",
                  row.left.type === "context" && "bg-zinc-50 dark:bg-zinc-900",
                  row.left.type === "empty" && "bg-zinc-50 dark:bg-zinc-900"
                )}>
                  {row.left.num ?? ""}
                </td>
                <td className={cn(
                  "select-none text-center text-xs font-medium",
                  row.left.type === "remove" && "bg-red-50 text-red-600 dark:bg-red-950/20 dark:text-red-400",
                  row.left.type === "context" && "bg-zinc-50 text-zinc-400 dark:bg-zinc-900",
                  row.left.type === "empty" && "bg-zinc-50 dark:bg-zinc-900"
                )}>
                  {row.left.type === "remove" ? "-" : row.left.type === "context" ? " " : ""}
                </td>
                <td className={cn(
                  "whitespace-pre px-3 py-0.5",
                  row.left.type === "remove" && "bg-red-50 text-red-900 dark:bg-red-950/20 dark:text-red-200",
                  row.left.type === "context" && "text-zinc-800 dark:text-zinc-300",
                  row.left.type === "empty" && "bg-zinc-50 dark:bg-zinc-900"
                )}>
                  {row.left.text}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Draggable divider */}
      <div
        className={cn(
          "w-4 flex-shrink-0 cursor-col-resize flex items-center justify-center relative group bg-transparent",
          isDragging && "cursor-col-resize"
        )}
        onMouseDown={handleMouseDown}
        style={{ zIndex: 10 }}
      >
        {/* Visible divider line */}
        <div className={cn(
          "w-px h-full bg-zinc-300 dark:bg-zinc-600 transition-all",
          "group-hover:w-1 group-hover:bg-blue-400 dark:group-hover:bg-blue-500",
          isDragging && "w-1 bg-blue-500 dark:bg-blue-400"
        )} />
        {/* Drag handle indicator */}
        <div className={cn(
          "absolute w-4 h-8 rounded-full bg-zinc-200 dark:bg-zinc-700 flex items-center justify-center opacity-0 transition-opacity shadow-sm",
          "group-hover:opacity-100",
          isDragging && "opacity-100 bg-blue-100 dark:bg-blue-900"
        )}>
          <svg width="10" height="10" viewBox="0 0 10 10" className="text-zinc-500 dark:text-zinc-400">
            <path d="M3 2v6M7 2v6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
        </div>
      </div>

      {/* Right side with its own scrollbar */}
      <div 
        ref={rightPaneRef}
        style={{ width: `calc(${100 - splitRatio}% - 1rem)` }} 
        className="flex-shrink-0 flex-grow overflow-auto scrollbar-thin scrollbar-thumb-zinc-300 dark:scrollbar-thumb-zinc-600"
        onScroll={handleRightScroll}
      >
        <table className="w-full border-collapse font-mono text-sm min-w-[300px]">
          <colgroup>
            <col className="w-12" />
            <col className="w-6" />
            <col className="w-full" />
          </colgroup>
          <tbody>
            {rows.map((row, i) => (
              <tr key={`right-${i}`}>
                <td className={cn(
                  "select-none px-2 text-right text-zinc-500 dark:text-zinc-600",
                  row.right.type === "add" && "bg-green-50 dark:bg-green-950/20",
                  row.right.type === "context" && "bg-zinc-50 dark:bg-zinc-900",
                  row.right.type === "empty" && "bg-zinc-50 dark:bg-zinc-900"
                )}>
                  {row.right.num ?? ""}
                </td>
                <td className={cn(
                  "select-none text-center text-xs font-medium",
                  row.right.type === "add" && "bg-green-50 text-green-600 dark:bg-green-950/20 dark:text-green-400",
                  row.right.type === "context" && "bg-zinc-50 text-zinc-400 dark:bg-zinc-900",
                  row.right.type === "empty" && "bg-zinc-50 dark:bg-zinc-900"
                )}>
                  {row.right.type === "add" ? "+" : row.right.type === "context" ? " " : ""}
                </td>
                <td className={cn(
                  "whitespace-pre px-3 py-0.5",
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
