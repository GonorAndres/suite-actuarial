"use client";

import { useEffect, useState, type ReactNode } from "react";
import { Tabs } from "@/components/ui";
import { useDomainView } from "@/hooks/useDomainView";
import { useLanguage } from "@/lib/i18n/LanguageContext";
import type { DomainId } from "@/lib/domain-guides";

const COPY = {
  es: {
    case: "Caso explicado",
    workbench: "Workbench",
    caseHint: "Lea la decisión, los flujos, los supuestos, el método, la interpretación y los límites como un solo recorrido.",
    workbenchHint: "Seleccione un modelo, revise qué calcula y para qué sirve, y después pruebe sus propios supuestos.",
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
      if (currentY <= 24) {
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
        className={`sticky top-16 z-30 border-y border-navy/15 bg-white/90 px-4 pt-4 shadow-sm backdrop-blur-sm transition-transform duration-300 motion-reduce:transition-none ${tabsHidden ? "-translate-y-[calc(100%+1rem)]" : "translate-y-0"}`}
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
