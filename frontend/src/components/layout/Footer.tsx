"use client";

import Link from "next/link";
import { useLanguage } from "@/lib/i18n/LanguageContext";

export function Footer() {
  const { lang, href } = useLanguage();
  return (
    <footer className="bg-navy text-offwhite/80 mt-16">
      {/* Thin gold rule */}
      <div className="h-[2px] bg-amber" aria-hidden="true" />

      <div className="max-w-6xl mx-auto px-6 py-10">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-6">
          {/* Left: wordmark + version */}
          <div className="flex items-baseline gap-3">
            <span className="font-heading font-bold text-lg text-offwhite">
              suite_actuarial · {lang === "es" ? "modelación actuarial en código abierto" : "open actuarial platform"}
            </span>
            <span className="text-sm text-offwhite/40 tabular-nums">
              v2.2.0
            </span>
          </div>

          {/* Center: links */}
          <div className="flex items-center gap-8 text-xs font-semibold uppercase tracking-wider">
            <Link href={href("/biblioteca")} className="text-offwhite/60 hover:text-offwhite transition-colors">
              {lang === "es" ? "Biblioteca" : "Library"}
            </Link>
            <Link href={href("/evidencia")} className="text-offwhite/60 hover:text-offwhite transition-colors">
              {lang === "es" ? "Evidencia" : "Evidence"}
            </Link>
            <a
              href="https://github.com/GonorAndres/suite-actuarial"
              target="_blank"
              rel="noopener noreferrer"
              className="text-offwhite/60 hover:text-offwhite transition-colors"
            >
              GitHub
            </a>
            <Link
              href={href("/api-docs")}
              className="text-offwhite/60 hover:text-offwhite transition-colors"
            >
              {lang === "es" ? "Referencia técnica" : "Developer reference"}
            </Link>
          </div>

          {/* Right: copyright */}
          <p className="text-sm text-offwhite/40">
            (c) 2026 Andres Gonzalez Ortega
          </p>
        </div>
      </div>
    </footer>
  );
}
