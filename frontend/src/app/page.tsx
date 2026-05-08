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
  drip_coffee_maker:
    "https://images.unsplash.com/photo-1497935586351-b67a49e012bf?w=800&h=600&fit=crop&q=80",
  air_purifier:
    "https://images.unsplash.com/photo-1639224101391-ea1027959849?w=800&h=600&fit=crop&q=80",
  office_chairs:
    "https://images.unsplash.com/photo-1580480055273-228ff5388ef8?w=800&h=600&fit=crop&q=80",
  mattress:
    "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?w=800&h=600&fit=crop&q=80",
  turntable:
    "https://images.unsplash.com/photo-1539375665275-f9de415ef9ac?w=800&h=600&fit=crop&q=80",
  vitamin_c_serum:
    "https://images.unsplash.com/photo-1620916566398-39f1143ab7be?w=800&h=600&fit=crop&q=80",
  humidifier:
    "https://images.unsplash.com/photo-1585771724684-38269d6639fd?w=800&h=600&fit=crop&q=80",
  slipper:
    "https://images.unsplash.com/photo-1631467146595-56e0b0c8b1e1?w=800&h=600&fit=crop&q=80",
  usb_battery_pack:
    "https://images.unsplash.com/photo-1609091839311-d5365f9ff1c5?w=800&h=600&fit=crop&q=80",
  clothing_steamer:
    "https://images.unsplash.com/photo-1558171813-4c088753af8f?w=800&h=600&fit=crop&q=80",
  travel_pillow:
    "https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?w=800&h=600&fit=crop&q=80",
  water_bottle:
    "https://images.unsplash.com/photo-1602143407151-7111542de6e8?w=800&h=600&fit=crop&q=80",
  red_light_therapy_device:
    "https://images.unsplash.com/photo-1616394584738-fc6e612e71b9?w=800&h=600&fit=crop&q=80",
  wireless_earbud:
    "https://images.unsplash.com/photo-1590658268037-6bf12f032f55?w=800&h=600&fit=crop&q=80",
  password_manager:
    "https://images.unsplash.com/photo-1555949963-ff9fe0c870eb?w=800&h=600&fit=crop&q=80",
  white_sneaker:
    "https://images.unsplash.com/photo-1595950653106-6c9ebd614d3a?w=800&h=600&fit=crop&q=80",
  fitness_tracker:
    "https://images.unsplash.com/photo-1576243345690-4e4b79b63288?w=800&h=600&fit=crop&q=80",
  deodorant:
    "https://images.unsplash.com/photo-1556228578-0d85b1a4d571?w=800&h=600&fit=crop&q=80",
  nonstick_pan:
    "https://images.unsplash.com/photo-1590794056226-79ef3a8147e1?w=800&h=600&fit=crop&q=80",
};

const CATEGORY_TITLES: Record<string, string> = {
  robot_vacuum: "The Best Robot Vacuums",
  headphones: "The Best Noise-Cancelling Headphones",
  drip_coffee_maker: "The Best Coffee Makers",
  air_purifier: "The Best Air Purifiers",
  office_chairs: "The Best Office Chairs",
  mattress: "The Best Mattresses",
  turntable: "The Best Turntables",
  vitamin_c_serum: "The Best Vitamin C Serums",
  humidifier: "The Best Humidifiers",
  slipper: "The Best Slippers",
  usb_battery_pack: "The Best USB Battery Packs",
  clothing_steamer: "The Best Clothing Steamers",
  travel_pillow: "The Best Travel Pillows",
  water_bottle: "The Best Water Bottles",
  red_light_therapy_device: "The Best Red Light Therapy Devices",
  wireless_earbud: "The Best Wireless Earbuds",
  password_manager: "The Best Password Managers",
  white_sneaker: "The Best White Sneakers",
  fitness_tracker: "The Best Fitness Trackers",
  deodorant: "The Best Deodorants",
  nonstick_pan: "The Best Non-Stick Pans",
};

const CATEGORY_TAGLINES: Record<string, string> = {
  robot_vacuum:
    "Our top picks for hands-free cleaning, verified for Canadian availability and pricing",
  headphones:
    "The best over-ear noise-cancelling headphones you can buy in Canada right now",
  drip_coffee_maker:
    "Top-rated drip coffee makers you can buy in Canada, from budget to premium",
  air_purifier:
    "Wildfire smoke, winter allergies, and everyday air quality — our picks for Canadian homes",
  office_chairs:
    "Ergonomic picks at every budget, from home office to all-day desk work",
  mattress:
    "Canadian-made and shipped options for every sleep style and budget",
  turntable:
    "From entry-level to audiophile, the best turntables you can buy in Canada",
  vitamin_c_serum:
    "Dermatologist-recommended serums at Canadian prices, from drugstore to luxury",
  humidifier:
    "The best humidifiers for Canadian winters, from compact bedroom units to whole-room",
  slipper:
    "Cozy picks for Canadian winters, including shearling, wool, and Canadian-made options",
  usb_battery_pack:
    "Portable chargers and power banks tested for real-world capacity, available in Canada",
  clothing_steamer:
    "Handheld and standing steamers tested on real fabrics, from travel to professional",
  travel_pillow:
    "Neck pillows tested on real flights, from compact budget picks to memory foam upgrades",
  water_bottle:
    "Insulated, filtered, and everyday bottles tested for durability and temperature retention",
  red_light_therapy_device:
    "LED masks and panels tested for collagen, acne, and anti-aging results",
  wireless_earbud:
    "Lab-tested earbuds ranked for sound, ANC, and battery life, available in Canada",
  password_manager:
    "Security-tested managers for individuals and families, including a Canadian-made top pick",
  white_sneaker:
    "Classic leather, canvas, and retro picks from budget to designer, available in Canada",
  fitness_tracker:
    "Heart rate, GPS, and sleep tracking tested for accuracy, from budget bands to smartwatches",
  deodorant:
    "Natural and antiperspirant picks tested for odor control, including Canadian-made options",
  nonstick_pan:
    "Ceramic, PTFE, and carbon steel pans tested with eggs and crepes, including Canadian-made Paderno",
};

const CATEGORY_ORDER = [
  "robot_vacuum",
  "headphones",
  "air_purifier",
  "drip_coffee_maker",
  "office_chairs",
  "mattress",
  "turntable",
  "vitamin_c_serum",
  "humidifier",
  "slipper",
  "usb_battery_pack",
  "clothing_steamer",
  "travel_pillow",
  "water_bottle",
  "red_light_therapy_device",
  "wireless_earbud",
  "password_manager",
  "white_sneaker",
  "fitness_tracker",
  "deodorant",
  "nonstick_pan",
];

const FALLBACK_IMAGE =
  "https://images.unsplash.com/photo-1556228578-0d85b1a4d571?w=800&h=600&fit=crop&q=80";

function getCategories(): Category[] {
  const path = join(process.cwd(), "src", "data", "categories.json");
  if (!existsSync(path)) return [];
  const raw: Category[] = JSON.parse(readFileSync(path, "utf-8"));
  return raw.sort((a, b) => {
    const ai = CATEGORY_ORDER.indexOf(a.id);
    const bi = CATEGORY_ORDER.indexOf(b.id);
    return (ai === -1 ? 999 : ai) - (bi === -1 ? 999 : bi);
  });
}

function FeaturedArticle({ cat }: { cat: Category }) {
  return (
    <Link href={`/category/${cat.id}`} className="group block">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-0 bg-[var(--color-card)] rounded-xl overflow-hidden ring-1 ring-[var(--color-rule)]">
        <div className="aspect-[4/3] lg:aspect-auto overflow-hidden">
          <img
            src={CATEGORY_IMAGES[cat.id] || FALLBACK_IMAGE}
            alt={CATEGORY_TITLES[cat.id] || cat.name}
            className="w-full h-full object-cover group-hover:scale-[1.03] transition-transform duration-700"
            loading="eager"
          />
        </div>
        <div className="p-8 lg:p-12 flex flex-col justify-center">
          <span className="text-[11px] font-bold uppercase tracking-wider text-[var(--color-red)] mb-4">
            Featured Guide
          </span>
          <h2 className="text-[2rem] lg:text-[2.5rem] leading-[1.1] font-normal text-[var(--color-ink)] mb-4 group-hover:text-[var(--color-red)] transition-colors" style={{ fontFamily: "var(--font-serif)" }}>
            {CATEGORY_TITLES[cat.id] || `Best ${cat.name}`}
          </h2>
          <p className="text-[15px] leading-[1.7] text-[var(--color-secondary)] mb-6 max-w-md">
            {CATEGORY_TAGLINES[cat.id] || "Our top picks, verified for Canadian availability."}
          </p>
          <div className="flex items-center gap-4">
            <span className="text-[13px] font-semibold text-[var(--color-red)] group-hover:underline">
              Read the guide →
            </span>
            <span className="text-[12px] text-[var(--color-muted)]">
              {cat.product_count} products reviewed
            </span>
          </div>
        </div>
      </div>
    </Link>
  );
}

function EditorialCard({ cat, size = "normal" }: { cat: Category; size?: "normal" | "compact" }) {
  if (size === "compact") {
    return (
      <Link href={`/category/${cat.id}`} className="group flex gap-4 items-start py-4 border-b border-[var(--color-rule)] last:border-b-0">
        <div className="w-20 h-20 rounded-lg overflow-hidden shrink-0">
          <img
            src={CATEGORY_IMAGES[cat.id] || FALLBACK_IMAGE}
            alt={CATEGORY_TITLES[cat.id] || cat.name}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
            loading="lazy"
          />
        </div>
        <div className="flex-1 min-w-0 pt-0.5">
          <h3 className="text-[15px] font-medium text-[var(--color-ink)] group-hover:text-[var(--color-red)] transition-colors leading-snug mb-1">
            {CATEGORY_TITLES[cat.id] || `Best ${cat.name}`}
          </h3>
          <p className="text-[13px] text-[var(--color-muted)] leading-snug line-clamp-2">
            {CATEGORY_TAGLINES[cat.id] || "Our top picks, verified for Canadian availability."}
          </p>
        </div>
      </Link>
    );
  }

  return (
    <Link href={`/category/${cat.id}`} className="group block">
      <div className="rounded-lg overflow-hidden ring-1 ring-[var(--color-rule)] bg-[var(--color-card)] h-full flex flex-col">
        <div className="aspect-[16/10] overflow-hidden">
          <img
            src={CATEGORY_IMAGES[cat.id] || FALLBACK_IMAGE}
            alt={CATEGORY_TITLES[cat.id] || cat.name}
            className="w-full h-full object-cover group-hover:scale-[1.03] transition-transform duration-600"
            loading="lazy"
          />
        </div>
        <div className="p-5 flex-1 flex flex-col">
          <span className="text-[11px] font-bold uppercase tracking-wider text-[var(--color-red)] mb-2">
            Guide
          </span>
          <h3 className="text-[17px] leading-[1.25] font-normal text-[var(--color-ink)] mb-2 group-hover:text-[var(--color-red)] transition-colors" style={{ fontFamily: "var(--font-serif)" }}>
            {CATEGORY_TITLES[cat.id] || `Best ${cat.name}`}
          </h3>
          <p className="text-[13px] text-[var(--color-muted)] leading-[1.55] flex-1">
            {CATEGORY_TAGLINES[cat.id] || "Our top picks, verified for Canadian availability."}
          </p>
          <div className="mt-4 pt-3 border-t border-[var(--color-rule)] flex items-center justify-between">
            <span className="text-[12px] text-[var(--color-muted)]">
              {cat.product_count} products
            </span>
            <span className="text-[12px] font-medium text-[var(--color-link)] group-hover:text-[var(--color-red)] transition-colors">
              Read →
            </span>
          </div>
        </div>
      </div>
    </Link>
  );
}

export default function Home() {
  const categories = getCategories();
  const featured = categories[0];
  const secondary = categories.slice(1, 4);
  const rest = categories.slice(4);
  const sidebarPicks = rest.slice(0, 6);
  const gridRemainder = rest.slice(6);

  return (
    <main className="flex-1">
      {/* Masthead */}
      <header className="border-b border-[var(--color-rule)]">
        <div className="max-w-7xl mx-auto px-6">
          <div className="py-6 flex items-center justify-between">
            <Link
              href="/"
              className="text-[22px] font-normal text-[var(--color-ink)]"
              style={{ fontFamily: "var(--font-serif)" }}
            >
              Canada Picks
            </Link>
            <nav className="flex items-center gap-6 text-[13px]">
              <Link href="/" className="text-[var(--color-ink)] font-medium hover:text-[var(--color-red)] transition-colors">
                All Guides
              </Link>
              <Link
                href="/about"
                className="border border-[var(--color-ink)] text-[var(--color-ink)] px-4 py-1.5 rounded text-[12px] font-medium hover:bg-[var(--color-ink)] hover:text-white transition-colors"
              >
                About
              </Link>
            </nav>
          </div>
          <div className="border-t border-[var(--color-rule)] py-3 flex items-center gap-2">
            <span className="text-[12px] text-[var(--color-muted)]">
              Independent product recommendations, verified for Canada
            </span>
            <span className="text-[12px] text-[var(--color-rule)]">·</span>
            <span className="text-[12px] text-[var(--color-muted)]">
              Updated {new Date().toLocaleDateString("en-US", { month: "long", year: "numeric" })}
            </span>
          </div>
        </div>
      </header>

      {categories.length === 0 ? (
        <section className="max-w-7xl mx-auto px-6 py-20">
          <p className="text-[var(--color-muted)]">
            No categories yet. Run the pipeline to add one.
          </p>
        </section>
      ) : (
        <>
          {/* Featured hero article */}
          {featured && (
            <section className="max-w-7xl mx-auto px-6 pt-10 pb-12">
              <FeaturedArticle cat={featured} />
            </section>
          )}

          {/* Secondary stories row — 3 cards */}
          {secondary.length > 0 && (
            <section className="max-w-7xl mx-auto px-6 pb-14">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {secondary.map((cat) => (
                  <EditorialCard key={cat.id} cat={cat} />
                ))}
              </div>
            </section>
          )}

          {/* Divider + section title */}
          {rest.length > 0 && (
            <section className="border-t border-[var(--color-rule)]">
              <div className="max-w-7xl mx-auto px-6 pt-12 pb-14">
                <h2 className="text-[1.5rem] font-normal text-[var(--color-ink)] mb-8" style={{ fontFamily: "var(--font-serif)" }}>
                  More guides
                </h2>

                <div className="flex flex-col lg:flex-row gap-10">
                  {/* Main grid */}
                  <div className="flex-1">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                      {gridRemainder.map((cat) => (
                        <EditorialCard key={cat.id} cat={cat} />
                      ))}
                    </div>
                  </div>

                  {/* Sidebar — compact list */}
                  {sidebarPicks.length > 0 && (
                    <aside className="lg:w-[300px] shrink-0">
                      <div className="sticky top-6">
                        <h3 className="text-[12px] font-bold uppercase tracking-wider text-[var(--color-muted)] mb-4">
                          Popular guides
                        </h3>
                        <div>
                          {sidebarPicks.map((cat) => (
                            <EditorialCard key={cat.id} cat={cat} size="compact" />
                          ))}
                        </div>
                      </div>
                    </aside>
                  )}
                </div>
              </div>
            </section>
          )}

          {/* How we work — editorial credibility section */}
          <section className="border-t border-[var(--color-rule)] bg-[var(--color-surface)]">
            <div className="max-w-7xl mx-auto px-6 py-16">
              <div className="max-w-4xl mx-auto text-center">
                <h2 className="text-[2rem] leading-[1.15] font-normal text-[var(--color-ink)] mb-6" style={{ fontFamily: "var(--font-serif)" }}>
                  We do the research. You get the answer.
                </h2>
                <p className="text-[15px] text-[var(--color-secondary)] leading-[1.7] max-w-2xl mx-auto mb-10">
                  We cross-reference expert reviewers like Wirecutter, RTINGS, and Consumer Reports, verify Canadian pricing and stock, and highlight Canadian-owned options when they earn it.
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 text-left">
                  <div className="bg-white rounded-lg p-6 ring-1 ring-[var(--color-rule)]">
                    <span className="block text-[2rem] mb-2">📋</span>
                    <h3 className="text-[15px] font-normal text-[var(--color-ink)] mb-1.5" style={{ fontFamily: "var(--font-serif)" }}>Cross-referenced</h3>
                    <p className="text-[13px] text-[var(--color-muted)] leading-relaxed">
                      We find where expert reviewers agree, not just one opinion.
                    </p>
                  </div>
                  <div className="bg-white rounded-lg p-6 ring-1 ring-[var(--color-rule)]">
                    <span className="block text-[2rem] mb-2">🇨🇦</span>
                    <h3 className="text-[15px] font-normal text-[var(--color-ink)] mb-1.5" style={{ fontFamily: "var(--font-serif)" }}>Canada-verified</h3>
                    <p className="text-[13px] text-[var(--color-muted)] leading-relaxed">
                      Every product is checked for Canadian pricing, stock, and shipping.
                    </p>
                  </div>
                  <div className="bg-white rounded-lg p-6 ring-1 ring-[var(--color-rule)]">
                    <span className="block text-[2rem] mb-2">🍁</span>
                    <h3 className="text-[15px] font-normal text-[var(--color-ink)] mb-1.5" style={{ fontFamily: "var(--font-serif)" }}>Canadian-owned picks</h3>
                    <p className="text-[13px] text-[var(--color-muted)] leading-relaxed">
                      We surface Canadian companies when they genuinely earn a spot.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </section>
        </>
      )}

      {/* Footer */}
      <footer className="bg-[var(--color-ink)] text-[#b5b0a8]">
        <div className="max-w-7xl mx-auto px-6 py-10">
          <div className="flex flex-col sm:flex-row sm:justify-between gap-4 text-[13px]">
            <div>
              <p className="text-white font-medium mb-1" style={{ fontFamily: "var(--font-serif)" }}>Canada Picks</p>
              <p>Independent product recommendations for Canadians</p>
            </div>
            <div className="sm:text-right">
              <p>Prices in CAD · {new Date().getFullYear()}</p>
              <p className="mt-1 text-[12px] opacity-70">
                We may earn a commission through affiliate links, but they never influence our picks.
              </p>
            </div>
          </div>
        </div>
      </footer>
    </main>
  );
}
