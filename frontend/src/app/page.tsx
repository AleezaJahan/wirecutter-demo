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
};

const CATEGORY_TAGLINES: Record<string, string> = {
  robot_vacuum:
    "Our top picks for hands-free cleaning, verified for Canadian availability and pricing",
  headphones:
    "The best over-ear noise-cancelling headphones you can buy in Canada right now",
  drip_coffee_maker:
    "Top-rated drip coffee makers you can buy in Canada, from budget to premium",
  air_purifier:
    "Wildfire smoke, winter allergies, and everyday air quality, our picks for Canadian homes",
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

export default function Home() {
  const categories = getCategories();

  return (
    <main className="flex-1">
      {/* Nav */}
      <header className="border-b border-[var(--color-rule)]">
        <div className="max-w-6xl mx-auto px-6 py-5 flex items-center justify-between">
          <Link
            href="/"
            className="text-[18px] text-[var(--color-ink)] hover:text-[var(--color-red)] transition-colors"
            style={{ fontFamily: "var(--font-serif)" }}
          >
            Canada Picks
          </Link>
          <nav className="flex items-center gap-6 text-[13px]">
            <Link
              href="/"
              className="text-[var(--color-ink)] hover:text-[var(--color-red)] transition-colors"
            >
              Guides
            </Link>
            <Link
              href="/about"
              className="border border-[var(--color-red)] text-[var(--color-red)] px-3.5 py-1.5 text-[12px] font-medium hover:bg-[var(--color-red)] hover:text-white transition-colors"
            >
              About
            </Link>
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
          We cross-reference expert reviewers, verify Canadian pricing and
          stock, and give you the answer.
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
            {categories.map((cat, i) => (
              <Link
                key={cat.id}
                href={`/category/${cat.id}`}
                className="group block overflow-hidden"
              >
                <div className="aspect-[4/3] overflow-hidden relative">
                  <img
                    src={CATEGORY_IMAGES[cat.id] || FALLBACK_IMAGE}
                    alt={CATEGORY_TITLES[cat.id] || cat.name}
                    className="w-full h-full object-cover group-hover:scale-[1.03] transition-transform duration-500"
                    loading={i < 2 ? "eager" : "lazy"}
                  />
                  <div className="absolute bottom-0 left-0 right-0 h-1 bg-[var(--color-red)] scale-x-0 group-hover:scale-x-100 transition-transform duration-300 origin-left" />
                </div>
                <div className="pt-4 pb-2">
                  <span className="text-[13px] text-[var(--color-red)]">
                    Guide
                  </span>
                  {i < 2 ? (
                    <h2 className="text-xl font-normal text-[var(--color-ink)] mt-1 mb-1 group-hover:text-[var(--color-red)] transition-colors">
                      {CATEGORY_TITLES[cat.id] || `Best ${cat.name}`}
                    </h2>
                  ) : (
                    <h3 className="text-lg font-normal text-[var(--color-ink)] mt-1 mb-1 group-hover:text-[var(--color-red)] transition-colors">
                      {CATEGORY_TITLES[cat.id] || `Best ${cat.name}`}
                    </h3>
                  )}
                  <p className="text-[14px] text-[var(--color-muted)] leading-relaxed">
                    {CATEGORY_TAGLINES[cat.id] ||
                      "Our top picks, verified for Canadian availability."}
                  </p>
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
                We read Wirecutter, RTINGS, Consumer Reports, and category
                specialists, then cross-reference their picks to find what
                the experts actually agree on.
              </p>
              <p>
                Every product gets checked for Canadian pricing and
                availability — not just Amazon, but Best Buy Canada, Canadian
                Tire, brand sites, and specialty retailers.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-[var(--color-ink)] text-[#b5b0a8]">
        <div className="max-w-6xl mx-auto px-6 py-10 flex flex-col sm:flex-row sm:justify-between gap-4 text-[13px]">
          <p>
            Canada Picks &middot; Prices in CAD &middot;{" "}
            {new Date().getFullYear()}
          </p>
          <p className="sm:text-right max-w-sm">
            We may earn a commission through affiliate links, but they never
            influence our picks.
          </p>
        </div>
      </footer>
    </main>
  );
}
