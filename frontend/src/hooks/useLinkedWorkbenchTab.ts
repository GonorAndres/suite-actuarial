"use client";

import { useCallback, useSyncExternalStore } from "react";

const WORKBENCH_EVENT = "suite-actuarial:workbench-tab";

function subscribe(callback: () => void) {
  window.addEventListener("popstate", callback);
  window.addEventListener(WORKBENCH_EVENT, callback);
  return () => {
    window.removeEventListener("popstate", callback);
    window.removeEventListener(WORKBENCH_EVENT, callback);
  };
}

export function useLinkedWorkbenchTab<T extends string>(allowed: readonly T[], fallback: T) {
  const allowedKey = allowed.join("|");
  const getSnapshot = useCallback(() => {
    const requested = new URLSearchParams(window.location.search).get("model") as T | null;
    return requested && allowedKey.split("|").includes(requested) ? requested : fallback;
  }, [allowedKey, fallback]);
  const getServerSnapshot = useCallback(() => fallback, [fallback]);
  const activeTab = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);

  const setActiveTab = useCallback((tab: T) => {
    const url = new URL(window.location.href);
    url.searchParams.set("model", tab);
    window.history.replaceState(null, "", `${url.pathname}${url.search}${url.hash}`);
    window.dispatchEvent(new Event(WORKBENCH_EVENT));
  }, []);

  return [activeTab, setActiveTab] as const;
}
