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
  coffee:
    "https://images.unsplash.com/photo-1497935586351-b67a49e012bf?w=800&h=600&fit=crop&q=80",
  air_purifier:
    "https://images.unsplash.com/photo-1585771724684-38269d6639fd?w=800&h=600&fit=crop&q=80",
};

const CATEGORY_TAGLINES: Record<string, string> = {
  robot_vacuum: "Our pick and alternatives for hands-free cleaning",
  headphones: "The best noise-cancelling headphones you can buy in Canada",
  coffee:
    "Drip, budget drip, espresso with grinder, French press, and Nespresso—one Canadian-first guide",
  air_purifier:
    "The best air purifiers for Canadian homes — wildfire smoke, winter allergies, and everyday air quality",
};

const FALLBACK_IMAGE =
  "https://images.unsplash.com/photo-1556228578-0d85b1a4d571?w=800&h=600&fit=crop&q=80";

function getCategories(): Category[] {
  const path = join(process.cwd(), "src", "data", "categories.json");
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
          <span
            className="text-[18px] text-[var(--color-ink)]"
            style={{ fontFamily: "var(--font-serif)" }}
          >
            Canada Picks
          </span>
          <nav className="flex items-center gap-6 text-[13px]">
            <Link
              href="/"
              className="text-[var(--color-ink)] hover:text-[var(--color-red)] transition-colors"
            >
              Guides
            </Link>
            <span className="border border-[var(--color-red)] text-[var(--color-red)] px-3.5 py-1.5 text-[12px] font-medium hover:bg-[var(--color-red)] hover:text-white transition-colors cursor-default">
              About
            </span>
          </nav>
        </div>
      </header>

      {/* Hero */}
      <section className="max-w-6xl mx-auto px-6 pt-14 pb-10">
        <h1 className="text-[3.5rem] leading-[1.06] font-normal text-[var(--color-ink)] mb-4">
          Independent product recommendations,{" "}
          <em className="text-[var(--color-red)]">verified for Canada.</em>
        </h1>
        <p className="text-[16px] leading-[1.65] text-[var(--color-secondary)] max-w-xl">
          We research what the best reviewers recommend, check that you can
          actually buy it in Canada, and tell you what to get.
        </p>
      </section>

      {/* Category cards */}
      <section className="max-w-6xl mx-auto px-6 pb-20">
        {categories.length === 0 ? (
          <p className="text-[var(--color-muted)]">
            No categories yet. Run the pipeline to add one.
          </p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {categories.slice(0, 2).map((cat) => (
              <Link
                key={cat.id}
                href={`/category/${cat.id}`}
                className="group block overflow-hidden"
              >
                <div className="aspect-[4/3] overflow-hidden relative">
                  <img
                    src={CATEGORY_IMAGES[cat.id] || FALLBACK_IMAGE}
                    alt={cat.name}
                    className="w-full h-full object-cover group-hover:scale-[1.03] transition-transform duration-500"
                  />
                  <div className="absolute bottom-0 left-0 right-0 h-1 bg-[var(--color-red)] scale-x-0 group-hover:scale-x-100 transition-transform duration-300 origin-left" />
                </div>
                <div className="pt-4 pb-2">
                  <span className="text-[13px] text-[var(--color-red)]">
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
            {categories.length > 2 &&
              categories.slice(2).map((cat) => (
                <Link
                  key={cat.id}
                  href={`/category/${cat.id}`}
                  className="group block overflow-hidden"
                >
                  <div className="aspect-[4/3] overflow-hidden relative">
                    <img
                      src={CATEGORY_IMAGES[cat.id] || FALLBACK_IMAGE}
                      alt={cat.name}
                      className="w-full h-full object-cover group-hover:scale-[1.03] transition-transform duration-500"
                    />
                    <div className="absolute bottom-0 left-0 right-0 h-1 bg-[var(--color-red)] scale-x-0 group-hover:scale-x-100 transition-transform duration-300 origin-left" />
                  </div>
                  <div className="pt-4 pb-2">
                    <span className="text-[13px] text-[var(--color-red)]">
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
      </section>

      {/* How we pick */}
      <section className="border-t border-[var(--color-rule)] bg-[var(--color-surface)]">
        <div className="max-w-6xl mx-auto px-6 py-16">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-12 items-start">
            <div>
              <h2 className="text-[2rem] leading-[1.15] font-normal text-[var(--color-ink)]">
                We do the research.
                <br />
                You get the answer.
              </h2>
            </div>
            <div className="space-y-5 text-[14px] text-[var(--color-secondary)] leading-[1.7]">
              <p>
                We read Wirecutter, RTINGS, Consumer Reports, Vacuum Wars, and
                others, then cross-reference their picks to find what the
                experts actually agree on.
              </p>
              <p>
                Every product gets checked for Canadian pricing and availability
                at Best Buy Canada, Canadian Tire, brand sites, and major
                retailers, not just Amazon.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-[var(--color-ink)] text-[#b5b0a8]">
        <div className="max-w-6xl mx-auto px-6 py-10 flex flex-col sm:flex-row sm:justify-between gap-4 text-[13px]">
          <p>Canada Picks &middot; Prices in CAD &middot; May 2026</p>
          <p className="sm:text-right max-w-sm">
            We make money through affiliate links, but they never influence
            our picks.
          </p>
        </div>
      </footer>
    </main>
  );
}
