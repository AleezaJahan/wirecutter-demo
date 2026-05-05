import Link from "next/link";
import { readFileSync, existsSync } from "fs";
import { join } from "path";

type Category = {
  id: string;
  name: string;
  product_count: number;
};

function getCategories(): Category[] {
  const path = join(process.cwd(), "public", "categories.json");
  if (!existsSync(path)) return [];
  return JSON.parse(readFileSync(path, "utf-8"));
}

export default function Home() {
  const categories = getCategories();

  return (
    <main className="flex-1">
      {/* Masthead */}
      <header className="border-b border-[var(--color-rule)] py-5">
        <div className="max-w-2xl mx-auto px-6">
          <span className="text-[13px] font-semibold tracking-[0.2em] uppercase text-[var(--color-red)]">
            Canada Picks
          </span>
        </div>
      </header>

      {/* Hero */}
      <section className="max-w-2xl mx-auto px-6 pt-16 pb-12">
        <h1 className="text-[2.75rem] leading-[1.08] font-normal text-[var(--color-ink)] mb-5">
          Independent product recommendations,
          <br />
          <em>verified for Canadian pricing and availability.</em>
        </h1>
        <p className="text-[17px] leading-[1.65] text-[var(--color-secondary)] max-w-lg">
          We research what the best reviewers recommend, check that you can
          actually buy it in Canada, and tell you what to get. We make money
          through affiliate links, but they never influence our picks.
        </p>
      </section>

      {/* How we pick */}
      <section className="border-y border-[var(--color-rule)]">
        <div className="max-w-2xl mx-auto px-6 py-12">
          <h2 className="text-sm font-semibold tracking-[0.12em] uppercase text-[var(--color-muted)] mb-8 font-[family-name:var(--font-inter)]">
            How we pick
          </h2>
          <div className="space-y-8">
            <div className="border-l-2 border-[var(--color-ink)] pl-5">
              <h3 className="text-lg font-normal text-[var(--color-ink)] mb-1">
                We read the reviewers so you don&apos;t have to
              </h3>
              <p className="text-[15px] text-[var(--color-secondary)] leading-relaxed">
                Wirecutter, RTINGS, Consumer Reports, Vacuum Wars, and more.
                We cross-reference their picks to find what the experts
                actually agree on.
              </p>
            </div>
            <div className="border-l-2 border-[var(--color-ink)] pl-5">
              <h3 className="text-lg font-normal text-[var(--color-ink)] mb-1">
                We check Canadian retailers directly
              </h3>
              <p className="text-[15px] text-[var(--color-secondary)] leading-relaxed">
                Best Buy Canada, Canadian Tire, brand sites, and major
                retailers — not just Amazon. Real prices in CAD, real stock
                status.
              </p>
            </div>
            <div className="border-l-2 border-[var(--color-ink)] pl-5">
              <h3 className="text-lg font-normal text-[var(--color-ink)] mb-1">
                We give you one pick, not a list of 12
              </h3>
              <p className="text-[15px] text-[var(--color-secondary)] leading-relaxed">
                One best overall, one budget, one upgrade. If you just want to
                know what to buy, we get you there fast.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Categories */}
      <section className="max-w-2xl mx-auto px-6 py-14">
        {categories.length === 0 ? (
          <p className="text-[var(--color-muted)]">
            No categories yet. Run the pipeline with{" "}
            <code className="text-sm font-mono text-[var(--color-ink)] bg-[var(--color-surface)] px-1 py-0.5">
              --category your_category
            </code>{" "}
            to add one.
          </p>
        ) : (
          <div className="space-y-5">
            {categories.map((cat) => (
              <Link
                key={cat.id}
                href={`/category/${cat.id}`}
                className="block border-l-[3px] border-[var(--color-red)] bg-[var(--color-surface)] px-6 py-6 hover:bg-[#f0ece7] transition-colors group"
              >
                <span className="text-[11px] font-semibold tracking-[0.15em] uppercase text-[var(--color-red)] font-[family-name:var(--font-inter)]">
                  Latest guide
                </span>
                <h3 className="text-[1.5rem] leading-tight font-normal text-[var(--color-ink)] mt-2 mb-2">
                  Best {cat.name} for Canadians
                </h3>
                <p className="text-[15px] text-[var(--color-secondary)] mb-4">
                  {cat.product_count} products researched, verified for
                  Canadian pricing and availability.
                </p>
                <span className="text-[13px] font-semibold text-[var(--color-red)] font-[family-name:var(--font-inter)] group-hover:underline">
                  Read our picks &rarr;
                </span>
              </Link>
            ))}
          </div>
        )}
      </section>

      {/* Footer */}
      <footer className="border-t border-[var(--color-rule)] mt-auto bg-[var(--color-surface)]">
        <div className="max-w-2xl mx-auto px-6 py-8 text-[13px] text-[var(--color-muted)]">
          <p>Canada Picks &middot; Prices in CAD &middot; May 2026</p>
        </div>
      </footer>
    </main>
  );
}
