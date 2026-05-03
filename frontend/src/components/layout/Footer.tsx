import Link from "next/link";

export function Footer() {
  return (
    <footer className="bg-navy text-cream/80">
      {/* Top gradient border */}
      <div
        className="h-[2px]"
        style={{
          background:
            "linear-gradient(90deg, transparent 0%, #D4A574 30%, #C17654 50%, #D4A574 70%, transparent 100%)",
        }}
      />

      <div className="max-w-6xl mx-auto px-6 py-10">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-6">
          {/* Left: logo + version */}
          <div className="flex items-center gap-3">
            <span className="font-heading font-bold text-lg text-cream">
              suite_actuarial
            </span>
            <span className="text-sm text-cream/40">v2.0.0</span>
          </div>

          {/* Center: links */}
          <div className="flex items-center gap-8 text-sm">
            <a
              href="https://github.com/GonorAndres/suite-actuarial"
              target="_blank"
              rel="noopener noreferrer"
              className="relative text-cream/60 hover:text-cream transition-colors after:content-[''] after:absolute after:bottom-0 after:left-0 after:w-0 after:h-[1px] after:bg-amber after:transition-all after:duration-300 hover:after:w-full"
            >
              GitHub
            </a>
            <Link
              href="/docs"
              className="relative text-cream/60 hover:text-cream transition-colors after:content-[''] after:absolute after:bottom-0 after:left-0 after:w-0 after:h-[1px] after:bg-amber after:transition-all after:duration-300 hover:after:w-full"
            >
              API Docs
            </Link>
          </div>

          {/* Right: copyright */}
          <p className="text-sm text-cream/40">
            (c) 2026 Andres Gonzalez Ortega
          </p>
        </div>
      </div>
    </footer>
  );
}
