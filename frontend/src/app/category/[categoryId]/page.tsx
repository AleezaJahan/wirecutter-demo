import { readFileSync, existsSync } from "fs";
import { join } from "path";
import { notFound } from "next/navigation";
import Link from "next/link";

type Pick = {
  role: string;
  role_display: string;
  badge?: string;
  id: string | null;
  name: string | null;
  price_cad?: number | null;
  price_display: string | null;
  retailer: string | null;
  use_case?: string | null;
  reason?: string;
  context?: string;
  specs?: Record<string, string>;
  image_url?: string;
  is_canadian_owned?: boolean;
  source_count?: number;
  canadianness_tier?: string | null;
  recommendations?: string[];
};

type Product = {
  id: string;
  name: string;
  brand: string;
  model: string;
  price_cad: number | null;
  price_display: string;
  retailer: string;
  product_url: string;
  in_stock: boolean;
  canada_verified: boolean;
  canadian_company: boolean;
  made_in_canada: boolean;
  canadianness_tier: string | null;
  sources: string[];
  source_count: number;
  recommendations: string[];
  positives: string[];
  negatives: string[];
  notes: string;
};

type Category = {
  id: string;
  name: string;
  product_count: number;
};

const ROLE_LABELS: Record<string, string> = {
  best_overall: "Our pick",
  best_budget: "Budget pick",
  best_upgrade: "Upgrade pick",
  best_for_specific_use_case: "Also great",
  best_canadian_option: "Canadian-owned pick",
};

function loadJSON<T>(path: string): T | null {
  if (!existsSync(path)) return null;
  return JSON.parse(readFileSync(path, "utf-8"));
}

function findProduct(
  products: Product[],
  pickId: string | null
): Product | null {
  if (!pickId) return null;
  return products.find((p) => p.id === pickId) ?? null;
}

export async function generateStaticParams() {
  const categoriesPath = join(process.cwd(), "src", "data", "categories.json");
  if (!existsSync(categoriesPath)) return [];
  const categories: Category[] = JSON.parse(
    readFileSync(categoriesPath, "utf-8")
  );
  return categories.map((c) => ({ categoryId: c.id }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ categoryId: string }>;
}) {
  const { categoryId } = await params;
  const categoriesPath = join(process.cwd(), "src", "data", "categories.json");
  const categories: Category[] = existsSync(categoriesPath)
    ? JSON.parse(readFileSync(categoriesPath, "utf-8"))
    : [];
  const cat = categories.find((c) => c.id === categoryId);
  const name = cat?.name ?? categoryId.replace(/_/g, " ");
  return {
    title: `The Best ${name} for Canadians (2026) — Canada Picks`,
    description: `Independent, reviewer-backed ${name.toLowerCase()} recommendations verified for Canadian availability and pricing.`,
  };
}

function PickSection({
  pick,
  product,
  index,
}: {
  pick: Pick;
  product: Product | null;
  index: number;
}) {
  const label = ROLE_LABELS[pick.role] || pick.role_display;
  /** Only show a small “eyebrow” when JSON supplies a distinct badge — avoids repeating e.g. “Our pick” twice. */
  const eyebrowText =
    typeof pick.badge === "string" ? pick.badge.trim() : "";
  const showEyebrow =
    eyebrowText.length > 0 && eyebrowText !== label.trim();

  if (!pick.name) {
    return (
      <div className="py-8 border-t border-[var(--color-rule)]">
        <span className="text-[13px] text-[var(--color-muted)]">
          {label}
        </span>
        <p className="mt-2 text-[15px] text-[var(--color-muted)] italic">
          We haven&apos;t found a strong pick for this category yet.
        </p>
      </div>
    );
  }

  const pros: string[] = (pick as Record<string, unknown>).positives as string[] ?? product?.positives ?? [];
  const cons: string[] = (pick as Record<string, unknown>).negatives as string[] ?? product?.negatives ?? [];

  const isCanadian = pick.role === "best_canadian_option" || !!pick.is_canadian_owned || !!product?.canadian_company;

  return (
    <div>
      {/* Section heading — Wirecutter style */}
      <div className="mb-6">
        <div
          className={`border-t-[3px] ${isCanadian ? "border-[var(--color-red)]" : "border-[var(--color-ink)]"} pt-5`}
        >
          {showEyebrow && (
            <span className="block text-[11px] font-semibold tracking-[0.12em] uppercase text-[var(--color-muted)] mb-2">
              {eyebrowText}
            </span>
          )}
          <h3
            className={`text-[1.6rem] leading-[1.2] font-normal ${
              isCanadian ? "text-[var(--color-red)]" : "text-[var(--color-ink)]"
            }`}
          >
            {label}
          </h3>
        </div>
      </div>

      {/* Product card */}
      <div className={`bg-[var(--color-card)] p-8 ${isCanadian ? "border-2 border-[var(--color-red)]" : "border border-[var(--color-rule)]"}`}>
        {pick.image_url && (
          <div className="mb-5 bg-[var(--color-surface)] flex items-center justify-center p-4">
            <img
              src={pick.image_url}
              alt={pick.name ?? ""}
              className="max-h-[200px] w-auto object-contain"
              loading="lazy"
            />
          </div>
        )}
        <p className="text-[20px] leading-snug font-medium text-[var(--color-ink)]">
          {pick.name}
        </p>

        {isCanadian && (
          <span className="inline-block text-[11px] font-medium text-[var(--color-red)] border border-[var(--color-red)] px-2 py-0.5 mt-2">
            Canadian-owned
          </span>
        )}

        {/* Context blurb — what this pick is and who it's for */}
        {pick.context && (
          <p className="text-[15px] leading-[1.65] text-[var(--color-secondary)] mt-3">
            {pick.context}
          </p>
        )}

        {pick.use_case && (
          <p className="text-sm text-[var(--color-link)] mt-2">
            Best for: {pick.use_case}
          </p>
        )}

        {/* Key specs */}
        {pick.specs && Object.keys(pick.specs).length > 0 && (
          <div className="flex flex-wrap gap-x-5 gap-y-1.5 mt-3">
            {Object.entries(pick.specs).map(([key, val]) => (
              <span key={key} className="text-[13px] text-[var(--color-muted)]">
                <span className="font-medium text-[var(--color-secondary)] capitalize">
                  {key.replace(/_/g, " ")}:
                </span>{" "}
                {val}
              </span>
            ))}
          </div>
        )}

        {/* Buy link + stock status */}
        <div className="flex flex-wrap items-center gap-x-4 gap-y-2 mt-5 mb-6">
          {product?.product_url ? (
            <a
              href={product.product_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-block text-[13px] font-semibold text-white bg-[var(--color-red)] px-5 py-2.5 hover:opacity-90 transition-opacity"
            >
              {pick.price_display && pick.price_display !== "N/A"
                ? `${pick.price_display} at ${pick.retailer}`
                : `View at ${pick.retailer}`}
            </a>
          ) : (
            pick.price_display &&
            pick.price_display !== "N/A" && (
              <span className="text-sm text-[var(--color-muted)]">
                {pick.price_display} at {pick.retailer}
              </span>
            )
          )}
          {product && (
            <span className="text-[12px]">
              {product.in_stock ? (
                <span className="text-[var(--color-link)] font-medium">In stock</span>
              ) : product.canada_verified ? (
                <span className="text-amber-600 font-medium">Out of stock</span>
              ) : (
                <span className="text-[var(--color-muted)]">Availability unverified</span>
              )}
            </span>
          )}
        </div>

        {/* Pros and Cons */}
        {(pros.length > 0 || cons.length > 0) && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-8 pt-5 border-t border-[var(--color-rule)]">
            {pros.length > 0 && (
              <div>
                <h4 className="text-[13px] font-semibold text-[var(--color-muted)] mb-3">
                  Why it&apos;s great
                </h4>
                <ul className="space-y-1.5">
                  {pros.slice(0, 5).map((p, i) => (
                    <li
                      key={i}
                      className="text-[14px] leading-snug text-[var(--color-secondary)] pl-4 border-l-2 border-[var(--color-link)]"
                    >
                      {p}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {cons.length > 0 && (
              <div>
                <h4 className="text-[13px] font-semibold text-[var(--color-muted)] mb-3">
                  Flaws but not dealbreakers
                </h4>
                <ul className="space-y-1.5">
                  {cons.slice(0, 5).map((c, i) => (
                    <li
                      key={i}
                      className="text-[14px] leading-snug text-[var(--color-muted)] pl-4 border-l-2 border-[var(--color-rule)]"
                    >
                      {c}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function StockIndicator({
  inStock,
  canadaVerified,
}: {
  inStock: boolean;
  canadaVerified: boolean;
}) {
  if (inStock)
    return (
      <span className="text-[12px] text-[var(--color-link)] font-medium">
        In stock
      </span>
    );
  if (canadaVerified)
    return (
      <span className="text-[12px] text-amber-600 font-medium">
        Out of stock
      </span>
    );
  return (
    <span className="text-[12px] text-[var(--color-muted)]">Not in Canada</span>
  );
}

function ProductRow({ product }: { product: Product }) {
  return (
    <div className="py-4 border-b border-[var(--color-rule)] last:border-b-0">
      <div className="flex items-baseline justify-between gap-4">
        <div className="min-w-0">
          <span className="font-normal text-[var(--color-ink)]">
            {product.name}
          </span>
          {product.canadian_company && (
            <span className="ml-2 text-[11px] font-semibold tracking-wide uppercase text-[var(--color-red)]">
              Canadian
            </span>
          )}
        </div>
        <span className="text-[15px] tabular-nums text-[var(--color-ink)] shrink-0">
          {product.price_display}
        </span>
      </div>

      <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mt-1.5 text-[13px]">
        {product.product_url ? (
          <a
            href={product.product_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-[var(--color-link)] hover:underline"
          >
            {product.retailer}
          </a>
        ) : (
          <span className="text-[var(--color-muted)]">{product.retailer}</span>
        )}
        <span className="text-[var(--color-rule)]">/</span>
        <StockIndicator
          inStock={product.in_stock}
          canadaVerified={product.canada_verified}
        />
      </div>
    </div>
  );
}

export default async function CategoryPage({
  params,
}: {
  params: Promise<{ categoryId: string }>;
}) {
  const { categoryId } = await params;
  const baseDir = join(process.cwd(), "src", "data", categoryId);

  const picks = loadJSON<Pick[]>(join(baseDir, "site_featured_picks.json"));
  const products = loadJSON<Product[]>(join(baseDir, "site_products.json"));

  if (!picks || !products) notFound();

  const categoriesPath = join(process.cwd(), "src", "data", "categories.json");
  const categories: Category[] = existsSync(categoriesPath)
    ? JSON.parse(readFileSync(categoriesPath, "utf-8"))
    : [];
  const cat = categories.find((c) => c.id === categoryId);
  const categoryName = cat?.name ?? categoryId.replace(/_/g, " ");

  const activePicks = picks.filter((p) => p.name !== null);
  const inactivePicks = picks.filter((p) => p.name === null);

  return (
    <main className="flex-1">
      {/* Nav */}
      <header className="border-b border-[var(--color-rule)]">
        <div className="max-w-6xl mx-auto px-6 py-5 flex items-center justify-between">
          <Link
            href="/"
            className="text-[17px] text-[var(--color-ink)] hover:text-[var(--color-red)] transition-colors"
            style={{ fontFamily: "var(--font-serif)" }}
          >
            Canada Picks
          </Link>
          <Link
            href="/"
            className="text-[13px] text-[var(--color-muted)] hover:text-[var(--color-ink)] transition-colors"
          >
            All guides
          </Link>
        </div>
      </header>

      {/* Title */}
      <section className="max-w-3xl mx-auto px-6 pt-14 pb-10">
        <span className="text-[13px] text-[var(--color-red)] mb-3 block">
          Guide
        </span>
        <h1 className="text-[2.75rem] leading-[1.06] font-normal text-[var(--color-ink)] mb-3">
          The Best {categoryName}
          <br />
          for Canadians
        </h1>
        <p className="text-[15px] text-[var(--color-muted)] leading-[1.6] mb-2">
          Updated May 2026
        </p>
        {categoryId === "coffee" && (
          <p className="text-[15px] text-[var(--color-secondary)] leading-[1.65] mt-4 max-w-xl">
            We cross-referenced Wirecutter, Consumer Reports, America&apos;s
            Test Kitchen, CNN Underscored, Tom&apos;s Guide, and James
            Hoffmann, then verified every pick is available in Canada at a
            Canadian retailer with CAD pricing.
          </p>
        )}
      </section>

      {/* Quick summary */}
      <section className="max-w-3xl mx-auto px-6 pb-8">
        <div className="bg-[var(--color-card)] border border-[var(--color-rule)] p-6">
          <h2 className="text-[13px] font-semibold text-[var(--color-muted)] mb-5">
            {categoryId === "coffee"
              ? "Find the right coffee maker for your needs"
              : "What we recommend"}
          </h2>
          {activePicks.map((pick) => (
            <div
              key={pick.role}
              className="flex items-baseline gap-4 py-2.5 border-b border-[var(--color-rule)] last:border-b-0"
            >
              <span className="shrink-0 text-[13px] text-[var(--color-red)] min-w-[6rem]">
                {(typeof pick.badge === "string" ? pick.badge.trim() : "") ||
                  ROLE_LABELS[pick.role] ||
                  pick.role_display}
              </span>
              <span className="text-[var(--color-ink)]">{pick.name}</span>
              {pick.price_display && pick.price_display !== "N/A" && (
                <span className="text-[13px] text-[var(--color-muted)] ml-auto shrink-0">
                  {pick.price_display}
                </span>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* Detailed picks */}
      <section className="max-w-3xl mx-auto px-6 pb-10">
        <div className="space-y-12">
          {activePicks.map((pick, i) => (
            <PickSection
              key={pick.role}
              pick={pick}
              product={findProduct(products, pick.id)}
              index={i}
            />
          ))}
          {inactivePicks.map((pick) => (
            <PickSection
              key={pick.role}
              pick={pick}
              product={null}
              index={99}
            />
          ))}
        </div>
      </section>

      {/* All products */}
      <section className="max-w-3xl mx-auto px-6 py-12">
        <h2 className="text-xl font-normal text-[var(--color-ink)] mb-8">
          Other products we considered
        </h2>
        <div className="bg-[var(--color-card)] border border-[var(--color-rule)] px-6">
          {[...products]
            .sort((a, b) => {
              if (a.price_cad === null && b.price_cad === null) return 0;
              if (a.price_cad === null) return 1;
              if (b.price_cad === null) return -1;
              return a.price_cad - b.price_cad;
            })
            .map((product) => (
              <ProductRow key={product.id} product={product} />
            ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-[var(--color-rule)] bg-[var(--color-surface)]">
        <div className="max-w-6xl mx-auto px-6 py-8 text-[13px] text-[var(--color-muted)]">
          <p>Canada Picks &middot; Prices in CAD &middot; May 2026</p>
        </div>
      </footer>
    </main>
  );
}
