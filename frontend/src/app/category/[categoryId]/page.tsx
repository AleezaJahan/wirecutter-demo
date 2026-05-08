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

type AltRetailer = {
  retailer: string;
  product_url: string;
  price_display: string | null;
};

type Product = {
  id: string;
  name: string;
  brand: string;
  model: string;
  price_cad: number | null;
  price_display: string;
  original_price_display: string | null;
  is_on_sale: boolean;
  retailer: string;
  product_url: string;
  in_stock: boolean;
  canada_verified: boolean;
  canadian_company: boolean;
  made_in_canada: boolean;
  canadianness_tier: string | null;
  alternative_retailers: AltRetailer[];
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

type PickContent = {
  headline: string;
  writeup: string;
  best_for: string;
  skip_if: string;
};

type GuideContent = {
  intro: string;
  picks: Record<string, PickContent>;
  who_this_is_for: string;
  how_we_picked: string;
} | null;

const ROLE_LABELS: Record<string, string> = {
  best_overall: "Our pick",
  best_budget: "Budget pick",
  best_upgrade: "Upgrade pick",
  best_for_specific_use_case: "Also great",
  best_canadian_option: "Canadian-owned pick",
};

const ROLE_ICONS: Record<string, string> = {
  best_overall: "★",
  best_budget: "$",
  best_upgrade: "↑",
  best_for_specific_use_case: "◆",
  best_canadian_option: "🍁",
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
    title: `The Best ${name} for Canadians (${new Date().getFullYear()}) — Canada Picks`,
    description: `Independent, reviewer-backed ${name.toLowerCase()} recommendations verified for Canadian availability and pricing.`,
  };
}

function PickCard({
  pick,
  product,
  guideContent,
}: {
  pick: Pick;
  product: Product | null;
  guideContent?: PickContent;
}) {
  const label = ROLE_LABELS[pick.role] || pick.role_display;
  const icon = ROLE_ICONS[pick.role] || "•";
  const isCanadian = pick.role === "best_canadian_option" || !!pick.is_canadian_owned || !!product?.canadian_company;
  const pros: string[] = (pick as Record<string, unknown>).positives as string[] ?? product?.positives ?? [];
  const cons: string[] = (pick as Record<string, unknown>).negatives as string[] ?? product?.negatives ?? [];

  if (!pick.name) {
    return null;
  }

  return (
    <article id={`pick-${pick.role}`} className="scroll-mt-24">
      {/* Role badge + headline */}
      <div className="mb-5">
        <div className="flex items-center gap-3 mb-2">
          <span className={`inline-flex items-center justify-center w-8 h-8 rounded-full text-sm font-bold ${
            isCanadian
              ? "bg-[var(--color-red)]/10 text-[var(--color-red)]"
              : "bg-[var(--color-link)]/10 text-[var(--color-link)]"
          }`}>
            {icon}
          </span>
          <span className={`text-[13px] font-semibold uppercase tracking-wide ${
            isCanadian ? "text-[var(--color-red)]" : "text-[var(--color-link)]"
          }`}>
            {label}
          </span>
        </div>
        {guideContent?.headline && (
          <p className="text-[22px] leading-[1.3] text-[var(--color-ink)]" style={{ fontFamily: "var(--font-serif)" }}>
            {guideContent.headline}
          </p>
        )}
      </div>

      {/* Product card — two-column layout */}
      <div className={`rounded-lg overflow-hidden ${
        isCanadian ? "ring-2 ring-[var(--color-red)]" : "ring-1 ring-[var(--color-rule)]"
      } bg-[var(--color-card)]`}>
        <div className="flex flex-col md:flex-row">
          {/* Image column */}
          {pick.image_url && (
            <div className="md:w-[280px] shrink-0 bg-white flex items-center justify-center p-6 md:p-8 border-b md:border-b-0 md:border-r border-[var(--color-rule)]">
              <img
                src={pick.image_url}
                alt={pick.name ?? ""}
                className="max-h-[180px] md:max-h-[200px] w-auto object-contain"
                loading="lazy"
              />
            </div>
          )}

          {/* Details column */}
          <div className="flex-1 p-6 md:p-8">
            <h3 className="text-[20px] leading-snug font-semibold text-[var(--color-ink)] mb-1">
              {pick.name}
            </h3>

            {isCanadian && (
              <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-[var(--color-red)] bg-[var(--color-red)]/8 px-2 py-0.5 rounded-sm mb-3">
                Canadian-owned
              </span>
            )}

            {pick.use_case && (
              <p className="text-[13px] text-[var(--color-link)] font-medium mb-3">
                {pick.use_case}
              </p>
            )}

            {/* Key specs */}
            {pick.specs && Object.keys(pick.specs).length > 0 && (
              <div className="flex flex-wrap gap-x-4 gap-y-1 mb-4">
                {Object.entries(pick.specs).map(([key, val]) => (
                  <span key={key} className="text-[12px] text-[var(--color-muted)] bg-[var(--color-surface)] px-2 py-0.5 rounded">
                    <span className="font-medium text-[var(--color-secondary)] capitalize">
                      {key.replace(/_/g, " ")}:
                    </span>{" "}
                    {val}
                  </span>
                ))}
              </div>
            )}

            {/* Buy row */}
            <div className="flex flex-wrap items-center gap-3 mt-auto pt-3 border-t border-[var(--color-rule)]">
              {product?.product_url ? (
                <a
                  href={product.product_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 text-[13px] font-semibold text-white bg-[var(--color-red)] px-5 py-2.5 rounded hover:opacity-90 transition-opacity"
                >
                  {product.is_on_sale && product.original_price_display && (
                    <span className="line-through opacity-70">{product.original_price_display}</span>
                  )}
                  {pick.price_display && pick.price_display !== "N/A"
                    ? `${pick.price_display} at ${pick.retailer}`
                    : `View at ${pick.retailer}`}
                  {product.is_on_sale && (
                    <span className="text-[10px] bg-white/20 px-1.5 py-0.5 rounded">Sale</span>
                  )}
                </a>
              ) : (
                pick.price_display && pick.price_display !== "N/A" && (
                  <span className="text-[14px] font-medium text-[var(--color-ink)]">
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

            {/* Alt retailers */}
            {product && product.alternative_retailers?.length > 0 && (
              <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mt-3 text-[12px]">
                <span className="text-[var(--color-muted)]">Also at:</span>
                {product.alternative_retailers.map((alt, i) => (
                  <a
                    key={i}
                    href={alt.product_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-[var(--color-link)] hover:underline"
                  >
                    {alt.price_display ? `${alt.retailer} (${alt.price_display})` : alt.retailer}
                  </a>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Pros / Cons bar */}
        {(pros.length > 0 || cons.length > 0) && (
          <div className="border-t border-[var(--color-rule)] bg-[var(--color-surface)]/50 px-6 md:px-8 py-5">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              {pros.length > 0 && (
                <div>
                  <h4 className="text-[12px] font-bold uppercase tracking-wide text-[var(--color-link)] mb-2">
                    Why it&apos;s great
                  </h4>
                  <ul className="space-y-1.5">
                    {pros.slice(0, 4).map((p, i) => (
                      <li key={i} className="text-[13px] leading-snug text-[var(--color-secondary)] flex gap-2">
                        <span className="text-[var(--color-link)] shrink-0 mt-0.5">+</span>
                        <span>{p}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {cons.length > 0 && (
                <div>
                  <h4 className="text-[12px] font-bold uppercase tracking-wide text-[var(--color-muted)] mb-2">
                    Flaws but not dealbreakers
                  </h4>
                  <ul className="space-y-1.5">
                    {cons.slice(0, 4).map((c, i) => (
                      <li key={i} className="text-[13px] leading-snug text-[var(--color-muted)] flex gap-2">
                        <span className="text-[var(--color-muted)] shrink-0 mt-0.5">−</span>
                        <span>{c}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Editorial writeup — below card */}
      {(pick.context || guideContent?.writeup || guideContent?.best_for || guideContent?.skip_if) && (
        <div className="mt-6 space-y-4 max-w-[640px]">
          {pick.context && (
            <p className="text-[15px] leading-[1.7] text-[var(--color-secondary)]">
              {pick.context}
            </p>
          )}

          {guideContent?.writeup && (
            <div className="space-y-3">
              {guideContent.writeup.split("\n\n").map((para, i) => (
                <p key={i} className="text-[15px] leading-[1.7] text-[var(--color-secondary)]">
                  {para}
                </p>
              ))}
            </div>
          )}

          {(guideContent?.best_for || guideContent?.skip_if) && (
            <div className="flex flex-col sm:flex-row gap-3 mt-4">
              {guideContent.best_for && (
                <div className="flex-1 bg-[var(--color-link)]/5 border border-[var(--color-link)]/20 rounded-md px-4 py-3">
                  <span className="block text-[11px] font-bold uppercase tracking-wide text-[var(--color-link)] mb-1">
                    Best for
                  </span>
                  <p className="text-[13px] leading-snug text-[var(--color-secondary)]">
                    {guideContent.best_for}
                  </p>
                </div>
              )}
              {guideContent.skip_if && (
                <div className="flex-1 bg-[var(--color-surface)] border border-[var(--color-rule)] rounded-md px-4 py-3">
                  <span className="block text-[11px] font-bold uppercase tracking-wide text-[var(--color-muted)] mb-1">
                    Skip if
                  </span>
                  <p className="text-[13px] leading-snug text-[var(--color-muted)]">
                    {guideContent.skip_if}
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </article>
  );
}

function ProductRow({ product }: { product: Product }) {
  return (
    <div className="py-3.5 border-b border-[var(--color-rule)] last:border-b-0 flex items-center gap-4">
      <div className="flex-1 min-w-0">
        <div className="flex items-baseline gap-2">
          <span className="font-medium text-[14px] text-[var(--color-ink)] truncate">
            {product.name}
          </span>
          {product.canadian_company && (
            <span className="text-[10px] font-bold uppercase text-[var(--color-red)] shrink-0">
              CA
            </span>
          )}
          {product.is_on_sale && (
            <span className="text-[10px] font-bold text-[var(--color-link)] bg-[var(--color-link)]/10 px-1.5 py-0.5 rounded shrink-0">
              Sale
            </span>
          )}
        </div>
        <div className="flex items-center gap-2 mt-0.5 text-[12px] text-[var(--color-muted)]">
          {product.product_url ? (
            <a href={product.product_url} target="_blank" rel="noopener noreferrer" className="text-[var(--color-link)] hover:underline">
              {product.retailer}
            </a>
          ) : (
            <span>{product.retailer}</span>
          )}
          {product.alternative_retailers?.length > 0 && (
            <span>+ {product.alternative_retailers.length} more</span>
          )}
          <span className="text-[var(--color-rule)]">·</span>
          {product.in_stock ? (
            <span className="text-[var(--color-link)]">In stock</span>
          ) : product.canada_verified ? (
            <span className="text-amber-600">Out of stock</span>
          ) : (
            <span>Unverified</span>
          )}
        </div>
      </div>
      <div className="text-right shrink-0">
        {product.is_on_sale && product.original_price_display && (
          <span className="block text-[11px] tabular-nums text-[var(--color-muted)] line-through">
            {product.original_price_display}
          </span>
        )}
        <span className="text-[15px] tabular-nums font-medium text-[var(--color-ink)]">
          {product.price_display}
        </span>
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
  const guide = loadJSON<NonNullable<GuideContent>>(join(baseDir, "guide_content.json"));

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
      {/* Hero */}
      <section className="max-w-4xl mx-auto px-6 pt-16 pb-12">
        <div className="max-w-3xl">
          <div className="flex items-center gap-3 mb-5">
            <span className="text-[12px] font-bold uppercase tracking-wider text-[var(--color-red)] bg-[var(--color-red)]/8 px-2.5 py-1 rounded">
              Buying Guide
            </span>
            <span className="text-[12px] text-[var(--color-muted)]">
              Updated {new Date().toLocaleDateString("en-US", { month: "long", year: "numeric" })}
            </span>
          </div>
          <h1 className="text-[3rem] md:text-[3.5rem] leading-[1.05] font-normal text-[var(--color-ink)] mb-6" style={{ fontFamily: "var(--font-serif)" }}>
            The Best {categoryName}
            <br />
            <span className="text-[var(--color-muted)]">for Canadians</span>
          </h1>
          {guide?.intro && (
            <div className="max-w-2xl space-y-3 border-l-[3px] border-[var(--color-red)] pl-5">
              {guide.intro.split("\n\n").map((para, i) => (
                <p key={i} className="text-[16px] text-[var(--color-secondary)] leading-[1.7]">
                  {para}
                </p>
              ))}
            </div>
          )}
        </div>
      </section>

      {/* Main content with sidebar layout */}
      <div className="max-w-6xl mx-auto px-6 pb-16">
        <div className="flex gap-12">
          {/* Sidebar — sticky TOC (desktop only) */}
          <aside className="hidden lg:block w-[220px] shrink-0">
            <div className="sticky top-[120px]">
              <h2 className="text-[11px] font-bold uppercase tracking-wider text-[var(--color-muted)] mb-4">
                In this guide
              </h2>
              <nav className="space-y-1">
                {activePicks.map((pick) => (
                  <a
                    key={pick.role}
                    href={`#pick-${pick.role}`}
                    className="block text-[13px] text-[var(--color-secondary)] hover:text-[var(--color-red)] py-1.5 border-l-2 border-transparent hover:border-[var(--color-red)] pl-3 transition-colors"
                  >
                    <span className="text-[var(--color-muted)] mr-1.5">{ROLE_ICONS[pick.role] || "•"}</span>
                    {ROLE_LABELS[pick.role] || pick.role_display}
                  </a>
                ))}
                <div className="border-t border-[var(--color-rule)] my-2" />
                <a href="#all-products" className="block text-[13px] text-[var(--color-secondary)] hover:text-[var(--color-red)] py-1.5 pl-3 transition-colors">
                  All products
                </a>
              </nav>
            </div>
          </aside>

          {/* Main column */}
          <div className="flex-1 min-w-0 max-w-3xl">
            {/* Quick verdict box */}
            <section className="mb-12">
              <div className="bg-[var(--color-card)] border border-[var(--color-rule)] rounded-lg overflow-hidden">
                <div className="bg-[var(--color-surface)] px-6 py-3 border-b border-[var(--color-rule)]">
                  <h2 className="text-[12px] font-bold uppercase tracking-wider text-[var(--color-muted)]">
                    Quick picks
                  </h2>
                </div>
                <div className="divide-y divide-[var(--color-rule)]">
                  {activePicks.map((pick) => (
                    <a
                      key={pick.role}
                      href={`#pick-${pick.role}`}
                      className="flex items-center gap-4 px-6 py-4 hover:bg-[var(--color-surface)]/50 transition-colors"
                    >
                      <span className="inline-flex items-center justify-center w-7 h-7 rounded-full text-[12px] font-bold bg-[var(--color-link)]/10 text-[var(--color-link)] shrink-0">
                        {ROLE_ICONS[pick.role] || "•"}
                      </span>
                      <div className="flex-1 min-w-0">
                        <span className="block text-[11px] font-semibold uppercase tracking-wide text-[var(--color-muted)]">
                          {ROLE_LABELS[pick.role] || pick.role_display}
                        </span>
                        <span className="block text-[15px] text-[var(--color-ink)] font-medium truncate">
                          {pick.name}
                        </span>
                      </div>
                      {pick.price_display && pick.price_display !== "N/A" && (
                        <span className="text-[14px] tabular-nums font-medium text-[var(--color-ink)] shrink-0">
                          {pick.price_display}
                        </span>
                      )}
                    </a>
                  ))}
                </div>
              </div>
            </section>

            {/* Who this is for + How we picked — as callout cards */}
            {(guide?.who_this_is_for || guide?.how_we_picked) && (
              <section className="mb-14 grid grid-cols-1 md:grid-cols-2 gap-4">
                {guide.who_this_is_for && (
                  <div className="bg-[var(--color-surface)] rounded-lg p-6">
                    <h2 className="text-[13px] font-bold uppercase tracking-wide text-[var(--color-ink)] mb-3" style={{ fontFamily: "var(--font-serif)" }}>
                      Who this is for
                    </h2>
                    <div className="space-y-2">
                      {guide.who_this_is_for.split("\n\n").map((para, i) => (
                        <p key={i} className="text-[14px] leading-[1.65] text-[var(--color-secondary)]">
                          {para}
                        </p>
                      ))}
                    </div>
                  </div>
                )}
                {guide.how_we_picked && (
                  <div className="bg-[var(--color-surface)] rounded-lg p-6">
                    <h2 className="text-[13px] font-bold uppercase tracking-wide text-[var(--color-ink)] mb-3" style={{ fontFamily: "var(--font-serif)" }}>
                      How we picked
                    </h2>
                    <div className="space-y-2">
                      {guide.how_we_picked.split("\n\n").map((para, i) => (
                        <p key={i} className="text-[14px] leading-[1.65] text-[var(--color-secondary)]">
                          {para}
                        </p>
                      ))}
                    </div>
                  </div>
                )}
              </section>
            )}

            {/* Detailed picks */}
            <section className="space-y-16">
              {activePicks.map((pick, i) => (
                <PickCard
                  key={pick.role}
                  pick={pick}
                  product={findProduct(products, pick.id)}
                  guideContent={guide?.picks?.[pick.role]}
                />
              ))}
            </section>

            {/* All products */}
            <section id="all-products" className="mt-16 scroll-mt-24">
              <div className="flex items-baseline justify-between mb-6">
                <h2 className="text-[1.4rem] font-normal text-[var(--color-ink)]" style={{ fontFamily: "var(--font-serif)" }}>
                  All products we considered
                </h2>
                <span className="text-[13px] text-[var(--color-muted)]">
                  {products.length} products
                </span>
              </div>
              <div className="bg-[var(--color-card)] border border-[var(--color-rule)] rounded-lg px-5">
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
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="border-t border-[var(--color-rule)] bg-[var(--color-surface)]">
        <div className="max-w-6xl mx-auto px-6 py-10 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <p className="text-[15px] font-medium text-[var(--color-ink)]" style={{ fontFamily: "var(--font-serif)" }}>
              Canada Picks
            </p>
            <p className="text-[13px] text-[var(--color-muted)] mt-1">
              Independent, reviewer-backed recommendations for Canadians.
            </p>
          </div>
          <p className="text-[12px] text-[var(--color-muted)]">
            Prices in CAD · {new Date().toLocaleDateString("en-US", { month: "long", year: "numeric" })}
          </p>
        </div>
      </footer>
    </main>
  );
}
