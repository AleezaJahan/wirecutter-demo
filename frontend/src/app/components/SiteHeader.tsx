"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import CategoryNav from "./CategoryNav";

export default function SiteHeader() {
  const pathname = usePathname();

  const categoryMatch = pathname.match(/^\/category\/([^/]+)/);
  const activeCategoryId = categoryMatch ? categoryMatch[1] : undefined;

  return (
    <header className="sticky top-0 z-50 bg-white/98 backdrop-blur-sm">
      {/* Masthead */}
      <div className="border-b border-[var(--color-rule)]">
        <div className="max-w-7xl mx-auto px-6">
          <div className="py-4 flex items-center justify-between">
            <Link
              href="/"
              className="text-[22px] font-normal text-[var(--color-ink)]"
              style={{ fontFamily: "var(--font-serif)" }}
            >
              Canada Picks
            </Link>
            <nav className="flex items-center gap-5 text-[13px]">
              <Link
                href="/"
                className={`transition-colors ${
                  pathname === "/"
                    ? "text-[var(--color-red)] font-medium"
                    : "text-[var(--color-secondary)] hover:text-[var(--color-ink)]"
                }`}
              >
                All Guides
              </Link>
              <Link
                href="/about"
                className="border border-[var(--color-rule)] text-[var(--color-secondary)] px-3.5 py-1.5 rounded-full text-[12px] font-medium hover:border-[var(--color-ink)] hover:text-[var(--color-ink)] transition-colors"
              >
                About
              </Link>
            </nav>
          </div>
        </div>
      </div>

      {/* Category navigation bar */}
      <CategoryNav activeCategoryId={activeCategoryId} />
    </header>
  );
}
