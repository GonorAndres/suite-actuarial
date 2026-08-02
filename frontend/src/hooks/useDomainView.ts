"use client";

import { useCallback, useSyncExternalStore } from "react";

export type DomainView = "case" | "workbench";

const DOMAIN_VIEW_EVENT = "suite-actuarial:domain-view";

function subscribe(callback: () => void) {
  window.addEventListener("popstate", callback);
  window.addEventListener(DOMAIN_VIEW_EVENT, callback);
  return () => {
    window.removeEventListener("popstate", callback);
    window.removeEventListener(DOMAIN_VIEW_EVENT, callback);
  };
}

function snapshot(): DomainView {
  const url = new URL(window.location.href);
  const requested = url.searchParams.get("view");
  if (requested === "case" || requested === "workbench") return requested;
  if (url.searchParams.has("model") || url.hash === "#workbench") return "workbench";
  return "case";
}

export function useDomainView() {
  const activeView = useSyncExternalStore(subscribe, snapshot, () => "case" as const);

  const setActiveView = useCallback((view: DomainView) => {
    const url = new URL(window.location.href);
    url.searchParams.set("view", view);
    url.hash = view === "workbench" ? "workbench" : "case";
    window.history.replaceState(null, "", `${url.pathname}${url.search}${url.hash}`);
    window.dispatchEvent(new Event(DOMAIN_VIEW_EVENT));
  }, []);

  return [activeView, setActiveView] as const;
}
