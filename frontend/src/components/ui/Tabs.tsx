"use client";

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
  return (
    <div
      role="tablist"
      aria-label="Tabs"
      className={`flex gap-6 border-b border-navy/15 overflow-x-auto ${className}`}
    >
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
              "-mb-px px-1 pb-2.5 pt-1 text-sm font-semibold uppercase tracking-wider whitespace-nowrap",
              "border-b-2 transition-colors duration-150",
              isActive
                ? "border-terracotta text-navy"
                : "border-transparent text-navy/50 hover:text-navy hover:border-navy/30",
            ].join(" ")}
          >
            {tab.label}
          </button>
        );
      })}
    </div>
  );
}
