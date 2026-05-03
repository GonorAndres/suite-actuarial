"use client";

import Link from "next/link";
import { useState, useEffect } from "react";
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
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  // Close mobile menu on route change
  useEffect(() => {
    setMobileOpen(false);
  }, [pathname]);

  return (
    <>
      <header
        className={[
          "sticky top-0 z-50 border-b transition-all duration-300",
          scrolled
            ? "bg-cream/90 backdrop-blur-md border-amber/20 shadow-sm"
            : "bg-cream/80 backdrop-blur-sm border-amber/10",
        ].join(" ")}
        style={{
          backgroundImage: scrolled
            ? "linear-gradient(to bottom, rgba(245,240,234,0.95), rgba(232,224,215,0.90))"
            : undefined,
        }}
      >
        <div className="max-w-6xl mx-auto px-6 flex items-center justify-between h-16">
          {/* Logo */}
          <Link
            href="/"
            className="font-heading font-bold text-2xl text-navy shrink-0 hover:scale-[1.03] transition-transform duration-200"
          >
            suite_actuarial
          </Link>

          {/* Desktop nav */}
          <nav className="hidden lg:flex items-center gap-0.5">
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
                    "relative px-3 py-2 text-sm font-medium transition-colors rounded-md",
                    isActive
                      ? "text-terracotta"
                      : "text-navy/70 hover:text-terracotta",
                  ].join(" ")}
                >
                  {t(item.key)}
                  {/* Active underline indicator */}
                  <span
                    className={[
                      "absolute bottom-0 left-1/2 -translate-x-1/2 h-[3px] bg-terracotta rounded-full transition-all duration-300",
                      isActive ? "w-3/4 opacity-100" : "w-0 opacity-0",
                    ].join(" ")}
                  />
                </Link>
              );
            })}
          </nav>

          {/* Right side: language toggle + mobile hamburger */}
          <div className="flex items-center gap-3">
            {/* Language pill toggle */}
            <div className="flex items-center bg-navy/5 rounded-full p-0.5">
              <button
                onClick={() => setLang("es")}
                className={[
                  "px-3 py-1 text-xs font-bold rounded-full transition-all duration-200",
                  lang === "es"
                    ? "bg-terracotta text-cream shadow-sm"
                    : "text-navy/50 hover:text-navy",
                ].join(" ")}
                aria-label="Espanol"
              >
                ES
              </button>
              <button
                onClick={() => setLang("en")}
                className={[
                  "px-3 py-1 text-xs font-bold rounded-full transition-all duration-200",
                  lang === "en"
                    ? "bg-terracotta text-cream shadow-sm"
                    : "text-navy/50 hover:text-navy",
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
      </header>

      {/* Mobile overlay backdrop */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-navy/30 backdrop-blur-sm lg:hidden"
          onClick={() => setMobileOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Mobile slide-in menu */}
      <div
        className={[
          "fixed top-0 right-0 z-50 h-full w-72 bg-cream shadow-2xl lg:hidden transition-transform duration-300 ease-out",
          mobileOpen ? "translate-x-0" : "translate-x-full",
        ].join(" ")}
      >
        <div className="flex items-center justify-between px-6 h-16 border-b border-amber/20">
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
        <nav className="px-4 py-4 flex flex-col gap-1">
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
                  "px-4 py-3 text-sm font-medium rounded-lg transition-all duration-200",
                  isActive
                    ? "bg-terracotta/10 text-terracotta border-l-4 border-terracotta"
                    : "text-navy/70 hover:text-terracotta hover:bg-amber/5",
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
