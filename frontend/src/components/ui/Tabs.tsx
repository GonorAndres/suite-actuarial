"use client";

import { useRef, useState, useEffect, useCallback } from "react";

interface Tab {
  id: string;
  label: string;
}

interface TabsProps {
  tabs: Tab[];
  activeTab: string;
  onTabChange: (id: string) => void;
  className?: string;
}

export default function Tabs({
  tabs,
  activeTab,
  onTabChange,
  className = "",
}: TabsProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [indicator, setIndicator] = useState({ left: 0, width: 0 });

  const updateIndicator = useCallback(() => {
    if (!containerRef.current) return;
    const activeEl = containerRef.current.querySelector(
      `[data-tab-id="${activeTab}"]`,
    ) as HTMLElement | null;
    if (activeEl) {
      const containerRect = containerRef.current.getBoundingClientRect();
      const activeRect = activeEl.getBoundingClientRect();
      setIndicator({
        left: activeRect.left - containerRect.left,
        width: activeRect.width,
      });
    }
  }, [activeTab]);

  useEffect(() => {
    updateIndicator();
    window.addEventListener("resize", updateIndicator);
    return () => window.removeEventListener("resize", updateIndicator);
  }, [updateIndicator]);

  return (
    <div
      ref={containerRef}
      role="tablist"
      aria-label="Tabs"
      className={`relative flex gap-1 bg-navy/5 rounded-full p-1 overflow-x-auto ${className}`}
    >
      {/* Sliding indicator */}
      <div
        className="absolute top-1 h-[calc(100%-8px)] bg-terracotta rounded-full shadow-sm transition-all duration-300 ease-out"
        style={{
          left: `${indicator.left}px`,
          width: `${indicator.width}px`,
        }}
        aria-hidden="true"
      />
      {tabs.map((tab) => {
        const isActive = tab.id === activeTab;
        return (
          <button
            key={tab.id}
            role="tab"
            type="button"
            data-tab-id={tab.id}
            aria-selected={isActive}
            aria-controls={`tabpanel-${tab.id}`}
            id={`tab-${tab.id}`}
            tabIndex={isActive ? 0 : -1}
            onClick={() => onTabChange(tab.id)}
            onKeyDown={(e) => {
              const currentIdx = tabs.findIndex((t) => t.id === tab.id);
              let nextIdx = -1;
              if (e.key === "ArrowRight") {
                nextIdx = (currentIdx + 1) % tabs.length;
              } else if (e.key === "ArrowLeft") {
                nextIdx = (currentIdx - 1 + tabs.length) % tabs.length;
              } else if (e.key === "Home") {
                nextIdx = 0;
              } else if (e.key === "End") {
                nextIdx = tabs.length - 1;
              }
              if (nextIdx >= 0) {
                e.preventDefault();
                onTabChange(tabs[nextIdx].id);
                const el = document.getElementById(`tab-${tabs[nextIdx].id}`);
                el?.focus();
              }
            }}
            className={[
              "relative z-10 px-4 py-2 rounded-full text-sm font-medium transition-all duration-200 whitespace-nowrap",
              isActive
                ? "text-cream"
                : "text-navy/60 hover:text-navy hover:bg-amber/10",
            ].join(" ")}
          >
            {tab.label}
          </button>
        );
      })}
    </div>
  );
}
