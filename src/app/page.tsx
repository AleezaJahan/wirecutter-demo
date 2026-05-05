import Link from "next/link";
import { readFileSync, existsSync } from "fs";
import { join } from "path";

type Category = {
  id: string;
  name: string;
  product_count: number;
};

const CATEGORY_IMAGES: Record<string, string> = {
  robot_vacuum:
    "https://images.unsplash.com/photo-1558317374-067fb5f30001?w=800&h=600&fit=crop&q=80",
  headphones:
    "https://images.unsplash.com/photo-1546435770-a3e426bf472b?w=800&h=600&fit=crop&q=80",
};

const CATEGORY_TAGLINES: Record<string, string> = {
  robot_vacuum: "Our pick and alternatives for hands-free cleaning",
  headphones: "The best noise-cancelling headphones you can buy in Canada",
};

const FALLBACK_IMAGE =
  "https://images.unsplash.com/photo-1556228578-0d85b1a4d571?w=800&h=600&fit=crop&q=80";

function getCategories(): Category[] {
  const path = join(process.cwd(), "public", "categories.json");
  if (!existsSync(path)) return [];
  return JSON.parse(readFileSync(path, "utf-8"));
}

export default function Home() {
  const categories = getCategories();

  return (
    <main className="flex-1">
      {/* Nav */}
      <header className="border-b border-[var(--color-rule)]">
        <div className="max-w-6xl mx-auto px-6 py-5 flex items-center justify-between">
          <span className="text-[17px] text-[var(--color-ink)]" style={{ fontFamily: "var(--font-serif)" }}>
            Canada Picks
          </span>
          <nav className="flex items-center gap-6 text-[13px] font-[family-name:var(--font-inter)]">
            <Link
              href="/"
              className="text-[var(--color-ink)] hover:text-[var(--color-red)] transition-colors"
            >
              Guides
            </Link>
            <span className="border border-[var(--color-ink)] text-[var(--color-ink)] px-3.5 py-1.5 text-[12px] font-semibold tracking-wide uppercase hover:bg-[var(--color-ink)] hover:text-[var(--color-card)] transition-colors cursor-default">
              About
            </span>
          </nav>
        </div>
      </header>

      {/* Hero - full width, compact */}
      <section className="max-w-6xl mx-auto px-6 pt-14 pb-10">
        <h1 className="text-[3.5rem] leading-[1.06] font-normal text-[var(--color-ink)] mb-4">
          Independent product recommendations,{" "}
          <em>verified for Canada.</em>
        </h1>
        <p className="text-[16px] leading-[1.65] text-[var(--color-secondary)] max-w-xl">
          We research what the best reviewers recommend, check that you can
          actually buy it in Canada, and tell you what to get.
        </p>
      </section>

      {/* Category cards - full width grid */}
      <section className="max-w-6xl mx-auto px-6 pb-16">
        {categories.length === 0 ? (
          <p className="text-[var(--color-muted)]">
            No categories yet. Run the pipeline to add one.
          </p>
        ) : (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5 mb-5">
              {categories.slice(0, 2).map((cat) => (
                <Link
                  key={cat.id}
                  href={`/category/${cat.id}`}
                  className="group block overflow-hidden"
                >
                  <div className="aspect-[4/3] overflow-hidden">
                    <img
                      src={CATEGORY_IMAGES[cat.id] || FALLBACK_IMAGE}
                      alt={cat.name}
                      className="w-full h-full object-cover group-hover:scale-[1.03] transition-transform duration-500"
                    />
                  </div>
                  <div className="pt-4 pb-2">
                    <span className="text-[13px] text-[var(--color-muted)]">
                      Guide
                    </span>
                    <h2 className="text-xl font-normal text-[var(--color-ink)] mt-1 mb-1 group-hover:text-[var(--color-red)] transition-colors">
                      Best {cat.name} for Canadians
                    </h2>
                    <p className="text-[14px] text-[var(--color-muted)] leading-relaxed">
                      {CATEGORY_TAGLINES[cat.id] ||
                        "Our top pick and alternatives, verified for Canada."}
                    </p>
                  </div>
                </Link>
              ))}
            </div>
            {categories.length > 2 && (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
                {categories.slice(2).map((cat) => (
                  <Link
                    key={cat.id}
                    href={`/category/${cat.id}`}
                    className="group block overflow-hidden"
                  >
                    <div className="aspect-[4/3] overflow-hidden">
                      <img
                        src={CATEGORY_IMAGES[cat.id] || FALLBACK_IMAGE}
                        alt={cat.name}
                        className="w-full h-full object-cover group-hover:scale-[1.03] transition-transform duration-500"
                      />
                    </div>
                    <div className="pt-4 pb-2">
                      <span className="text-[13px] text-[var(--color-muted)]">
                        Guide
                      </span>
                      <h3 className="text-lg font-normal text-[var(--color-ink)] mt-1 group-hover:text-[var(--color-red)] transition-colors">
                        Best {cat.name} for Canadians
                      </h3>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </>
        )}
      </section>

      {/* How we pick */}
      <section className="border-y border-[var(--color-rule)] bg-[var(--color-surface)]">
        <div className="max-w-6xl mx-auto px-6 py-16">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-12 items-start">
            <div>
              <span className="text-[13px] text-[var(--color-muted)] mb-4 block">
                How we pick
              </span>
              <h2 className="text-[2rem] leading-[1.15] font-normal text-[var(--color-ink)]">
                We do the research.
                <br />
                You get the answer.
              </h2>
            </div>
            <div className="space-y-6">
              <div>
                <p className="text-[15px] font-semibold text-[var(--color-ink)] mb-1">
                  We read the reviewers so you don&apos;t have to
                </p>
                <p className="text-[14px] text-[var(--color-secondary)] leading-relaxed">
                  Wirecutter, RTINGS, Consumer Reports, Vacuum Wars, and more.
                  We cross-reference their picks to find what the experts
                  actually agree on.
                </p>
              </div>
              <div>
                <p className="text-[15px] font-semibold text-[var(--color-ink)] mb-1">
                  We check Canadian retailers directly
                </p>
                <p className="text-[14px] text-[var(--color-secondary)] leading-relaxed">
                  Best Buy Canada, Canadian Tire, brand sites, and major
                  retailers, not just Amazon. Real prices in CAD, real stock
                  status.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-[var(--color-rule)] bg-[var(--color-surface)]">
        <div className="max-w-6xl mx-auto px-6 py-10 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 text-[13px] text-[var(--color-muted)]">
          <p>Canada Picks &middot; Prices in CAD &middot; May 2026</p>
          <p>
            We make money through affiliate links, but they never influence our
            picks.
          </p>
        </div>
      </footer>
    </main>
  );
}
