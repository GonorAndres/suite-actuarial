"use client";

import Link from "next/link";
import { useState } from "react";
import { usePathname } from "next/navigation";
import { useLanguage } from "@/lib/i18n/LanguageContext";
import type { TranslationKey } from "@/lib/i18n/translations";

const NAV_ITEMS: { key: TranslationKey; href: string }[] = [
  { key: "nav_inicio", href: "/" },
  { key: "nav_vida", href: "/vida" },
  { key: "nav_danos", href: "/danos" },
  { key: "nav_salud", href: "/salud" },
  { key: "nav_pensiones", href: "/pensiones" },
  { key: "nav_reservas", href: "/reservas" },
  { key: "nav_regulatorio", href: "/regulatorio" },
  { key: "nav_reaseguro", href: "/reaseguro" },
  { key: "nav_api", href: "/api-docs" },
];

export function Header() {
  const { lang, setLang, t } = useLanguage();
  const [mobileOpen, setMobileOpen] = useState(false);
  const pathname = usePathname();

  return (
    <>
      {/* Masthead: paper surface with a classic double rule underneath */}
      <header className="sticky top-0 z-50 bg-offwhite/95 backdrop-blur-sm">
        <div className="max-w-6xl mx-auto px-6 flex items-center justify-between h-16">
          {/* Wordmark */}
          <Link
            href="/"
            className="font-heading font-bold text-2xl text-navy shrink-0"
          >
            Suite Actuarial
          </Link>

          {/* Desktop nav */}
          <nav className="hidden lg:flex items-center gap-1">
            {NAV_ITEMS.map((item) => {
              const isActive =
                item.href === "/"
                  ? pathname === "/"
                  : pathname.startsWith(item.href);
              return (
                <Link
                  key={item.key}
                  href={item.href}
                  className={[
                    "relative px-2.5 py-2 text-xs font-semibold uppercase tracking-wider transition-colors",
                    isActive
                      ? "text-terracotta"
                      : "text-navy/65 hover:text-navy",
                  ].join(" ")}
                >
                  {t(item.key)}
                  {/* Active underline indicator */}
                  <span
                    className={[
                      "absolute bottom-0 left-2.5 right-2.5 h-[2px] bg-terracotta transition-opacity duration-200",
                      isActive ? "opacity-100" : "opacity-0",
                    ].join(" ")}
                  />
                </Link>
              );
            })}
          </nav>

          {/* Right side: language toggle + mobile hamburger */}
          <div className="flex items-center gap-3">
            {/* Language toggle */}
            <div className="flex items-center border border-navy/25 rounded-sm overflow-hidden">
              <button
                onClick={() => setLang("es")}
                className={[
                  "px-2.5 py-1 text-xs font-bold transition-colors duration-150",
                  lang === "es"
                    ? "bg-navy text-offwhite"
                    : "text-navy/60 hover:text-navy",
                ].join(" ")}
                aria-label="Espanol"
              >
                ES
              </button>
              <button
                onClick={() => setLang("en")}
                className={[
                  "px-2.5 py-1 text-xs font-bold transition-colors duration-150",
                  lang === "en"
                    ? "bg-navy text-offwhite"
                    : "text-navy/60 hover:text-navy",
                ].join(" ")}
                aria-label="English"
              >
                EN
              </button>
            </div>

            {/* Mobile hamburger */}
            <button
              onClick={() => setMobileOpen(!mobileOpen)}
              className="lg:hidden p-2 text-navy hover:text-terracotta transition-colors"
              aria-label="Toggle menu"
            >
              <svg
                className="w-6 h-6"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                {mobileOpen ? (
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                ) : (
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 6h16M4 12h16M4 18h16"
                  />
                )}
              </svg>
            </button>
          </div>
        </div>

        {/* Classic double rule */}
        <div className="border-t-2 border-navy" aria-hidden="true">
          <div className="border-t border-navy mt-[2px]" />
        </div>
      </header>

      {/* Mobile overlay backdrop */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-navy/40 lg:hidden"
          onClick={() => setMobileOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Mobile slide-in menu */}
      <div
        className={[
          "fixed top-0 right-0 z-50 h-full w-72 bg-offwhite border-l border-navy/15 shadow-2xl lg:hidden transition-transform duration-300 ease-out",
          mobileOpen ? "translate-x-0" : "translate-x-full",
        ].join(" ")}
      >
        <div className="flex items-center justify-between px-6 h-16 border-b-2 border-navy">
          <span className="font-heading font-bold text-lg text-navy">
            Menu
          </span>
          <button
            onClick={() => setMobileOpen(false)}
            className="p-2 text-navy hover:text-terracotta transition-colors"
            aria-label="Close menu"
          >
            <svg
              className="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>
        <nav className="px-4 py-4 flex flex-col">
          {NAV_ITEMS.map((item) => {
            const isActive =
              item.href === "/"
                ? pathname === "/"
                : pathname.startsWith(item.href);
            return (
              <Link
                key={item.key}
                href={item.href}
                onClick={() => setMobileOpen(false)}
                className={[
                  "px-3 py-3 text-sm font-semibold uppercase tracking-wider border-b border-navy/10 transition-colors duration-150",
                  isActive
                    ? "text-terracotta border-l-2 border-l-terracotta pl-4"
                    : "text-navy/70 hover:text-navy",
                ].join(" ")}
              >
                {t(item.key)}
              </Link>
            );
          })}
        </nav>
      </div>
    </>
  );
}
