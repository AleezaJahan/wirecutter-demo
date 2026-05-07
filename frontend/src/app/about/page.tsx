import Link from "next/link";

export default function AboutPage() {
  return (
    <main className="flex-1">
      <header className="border-b border-[var(--color-rule)]">
        <div className="max-w-3xl mx-auto px-6 py-5 flex items-center justify-between">
          <Link
            href="/"
            className="text-[18px] text-[var(--color-ink)] hover:text-[var(--color-red)] transition-colors"
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

      <section className="max-w-3xl mx-auto px-6 pt-14 pb-16">
        <h1 className="text-[2.5rem] leading-[1.1] font-normal text-[var(--color-ink)] mb-6">
          About Canada Picks
        </h1>
        <div className="space-y-5 text-[15px] leading-[1.75] text-[var(--color-secondary)]">
          <p>
            Canada Picks helps Canadian shoppers quickly find products that are
            both highly rated and actually purchasable in Canada.
          </p>
          <p>
            We aggregate recommendations from independent review sources, then
            verify Canadian pricing, availability, and retailer links before a
            product appears in our guides.
          </p>
          <p>
            We may earn commission through affiliate links, but compensation
            does not influence what we recommend.
          </p>
        </div>
      </section>
    </main>
  );
}
