"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";
import { Tabs } from "@/components/ui";
import { useDomainView } from "@/hooks/useDomainView";
import { useLanguage } from "@/lib/i18n/LanguageContext";
import type { DomainId } from "@/lib/domain-guides";

/** Sticky offset of the switcher, in px. Matches `top-16` below the masthead. */
const STICKY_OFFSET = 64;

/**
 * Distance from the top of the document, read from layout boxes so a CSS
 * transform on the element itself does not contaminate the measurement.
 */
function documentTop(element: HTMLElement) {
  let top = 0;
  let node: HTMLElement | null = element;
  while (node) {
    top += node.offsetTop;
    node = node.offsetParent as HTMLElement | null;
  }
  return top;
}

const COPY = {
  es: {
    case: "Caso explicado",
    workbench: "Workbench",
    caseHint: "La decisión, los flujos, los supuestos, el método, la interpretación y los límites, leídos como un solo recorrido.",
    workbenchHint: "Elige un modelo, revisa qué calcula y para qué sirve, y después prueba con tus propios supuestos.",
  },
  en: {
    case: "Explained case",
    workbench: "Workbench",
    caseHint: "Read the decision, cash flows, assumptions, method, interpretation, and limits as one continuous case.",
    workbenchHint: "Select a model, review what it calculates and why it matters, then test your own assumptions.",
  },
} as const;

export function DomainWorkspace({
  domain,
  caseView,
  children,
}: {
  domain: DomainId;
  caseView: ReactNode;
  children: ReactNode;
}) {
  const { lang } = useLanguage();
  const copy = COPY[lang];
  const [activeView, setActiveView] = useDomainView();
  const [tabsHidden, setTabsHidden] = useState(false);
  const switcherRef = useRef<HTMLDivElement>(null);
  const tabs = [
    { id: "case", label: copy.case },
    { id: "workbench", label: copy.workbench },
  ];

  useEffect(() => {
    let previousY = window.scrollY;
    let frame = 0;

    const updateVisibility = () => {
      frame = 0;
      const currentY = window.scrollY;
      const switcher = switcherRef.current;
      // Only tuck the switcher away while it is pinned below the masthead.
      // Still in normal flow, the transform does not hide it: it drags the bar
      // up over the text above and leaves a gap where the bar used to sit.
      const pinned =
        switcher !== null && currentY + STICKY_OFFSET >= documentTop(switcher);

      if (!pinned || currentY <= 24) {
        setTabsHidden(false);
      } else if (currentY > previousY + 4) {
        setTabsHidden(true);
      } else if (currentY < previousY - 4) {
        setTabsHidden(false);
      }
      previousY = currentY;
    };

    const onScroll = () => {
      if (frame === 0) frame = window.requestAnimationFrame(updateVisibility);
    };

    window.addEventListener("scroll", onScroll, { passive: true });
    return () => {
      window.removeEventListener("scroll", onScroll);
      if (frame !== 0) window.cancelAnimationFrame(frame);
    };
  }, []);

  return (
    <div className="space-y-7" data-domain={domain}>
      <div
        ref={switcherRef}
        className={`sticky top-16 z-30 border-y border-navy/15 bg-white/90 px-4 pt-4 shadow-sm backdrop-blur-sm transition-transform duration-300 motion-reduce:transition-none ${tabsHidden ? "-translate-y-[calc(100%+5rem)]" : "translate-y-0"}`}
      >
        <Tabs tabs={tabs} activeTab={activeView} onTabChange={(id) => setActiveView(id as "case" | "workbench")} />
        <p className="py-3 text-sm leading-relaxed text-navy/60">
          {activeView === "case" ? copy.caseHint : copy.workbenchHint}
        </p>
      </div>

      {activeView === "case" ? (
        <div id="case" className="scroll-mt-28">{caseView}</div>
      ) : (
        <div className="space-y-8">{children}</div>
      )}
    </div>
  );
}
