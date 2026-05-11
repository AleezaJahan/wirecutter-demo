import Link from "next/link";
import { readFileSync, existsSync } from "fs";
import { frontendSrcDataPath } from "@/lib/dataPaths";

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
  refrigerators:
    "https://images.unsplash.com/photo-1571175443880-49e1d01b3fb5?w=800&h=600&fit=crop&q=80",
  air_purifier:
    "https://images.unsplash.com/photo-1639224101391-ea1027959849?w=800&h=600&fit=crop&q=80",
  mosquito_gear:
    "https://images.unsplash.com/photo-1475855581690-8accf351648c?w=800&h=600&fit=crop&q=80",
  office_chairs:
    "https://images.unsplash.com/photo-1580480055273-228ff5388ef8?w=800&h=600&fit=crop&q=80",
  mattress:
    "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?w=800&h=600&fit=crop&q=80",
  bed_sheets:
    "https://images.unsplash.com/photo-1629949009765-40fc74c9ec21?w=800&h=600&fit=crop&q=80",
  bedside_lamps:
    "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=800&h=600&fit=crop&q=80",
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
  white_t_shirts_for_men:
    "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=800&h=600&fit=crop&q=80",
  white_t_shirts_for_women:
    "https://images.unsplash.com/photo-1564257648229-57765da07d52?w=800&h=600&fit=crop&q=80",
  fitness_tracker:
    "https://images.unsplash.com/photo-1576243345690-4e4b79b63288?w=800&h=600&fit=crop&q=80",
  exercise_bikes:
    "https://images.unsplash.com/photo-1534438327276-14e5300c3a48?w=800&h=600&fit=crop&q=80",
  alarm_clocks:
    "https://images.unsplash.com/photo-1563861826100-9cb868fdbe1c?w=800&h=600&fit=crop&q=80",
  deodorant:
    "https://images.unsplash.com/photo-1556228578-0d85b1a4d571?w=800&h=600&fit=crop&q=80",
  nonstick_pan:
    "https://images.unsplash.com/photo-1590794056226-79ef3a8147e1?w=800&h=600&fit=crop&q=80",
  light_therapy_lamp:
    "https://images.unsplash.com/photo-1513506003901-1e6a229e2d15?w=800&h=600&fit=crop&q=80",
  tv:
    "https://images.unsplash.com/photo-1593359677879-a4bb92f829d1?w=800&h=600&fit=crop&q=80",
  sofa:
    "https://images.unsplash.com/photo-1493666438817-866a91353ca9?w=800&h=600&fit=crop&q=80",
  compression_socks:
    "https://images.unsplash.com/photo-1576013551627-843ccfdb6fd8?w=800&h=600&fit=crop&q=80",
  electric_toothbrush:
    "https://images.unsplash.com/photo-1606811844079-7e2bdea3e71d?w=800&h=600&fit=crop&q=80",
};

const CATEGORY_TITLES: Record<string, string> = {
  robot_vacuum: "The Best Robot Vacuums",
  headphones: "The Best Noise-Cancelling Headphones",
  drip_coffee_maker: "The Best Coffee Makers",
  refrigerators: "The Best Refrigerators",
  air_purifier: "The Best Air Purifiers",
  mosquito_gear: "The Best Mosquito Repellents & Gear",
  office_chairs: "The Best Office Chairs",
  mattress: "The Best Mattresses",
  bed_sheets: "The Best Bed Sheets",
  bedside_lamps: "The Best Bedside Lamps",
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
  white_t_shirts_for_men: "The Best White T-Shirts for Men",
  white_t_shirts_for_women: "The Best White T-Shirts for Women",
  fitness_tracker: "The Best Fitness Trackers",
  exercise_bikes: "The Best Exercise Bikes",
  alarm_clocks: "The Best Alarm Clocks",
  deodorant: "The Best Deodorants",
  nonstick_pan: "The Best Non-Stick Pans",
  light_therapy_lamp: "The Best Light Therapy Lamps",
  tv: "The Best TVs",
  sofa: "The Best Sofas",
  compression_socks: "The Best Compression Socks",
  electric_toothbrush: "The Best Electric Toothbrushes",
};

const CATEGORY_TAGLINES: Record<string, string> = {
  robot_vacuum:
    "Our top picks for hands-free cleaning, verified for Canadian availability and pricing",
  headphones:
    "The best over-ear noise-cancelling headphones you can buy in Canada right now",
  drip_coffee_maker:
    "Top-rated drip coffee makers you can buy in Canada, from budget to premium",
  refrigerators:
    "French-door, counter-depth, and no-frills picks — lab-tested sources verified at Canadian retailers",
  air_purifier:
    "Wildfire smoke, winter allergies, and everyday air quality — our picks for Canadian homes",
  mosquito_gear:
    "Repellents, Thermacell-style devices, and traps — lab- and field-tested picks with Canadian stock",
  office_chairs:
    "Ergonomic picks at every budget, from home office to all-day desk work",
  mattress:
    "Canadian-made and shipped options for every sleep style and budget",
  bed_sheets:
    "Cotton percale, sateen, and linen sets tested for feel, durability, and Canadian availability",
  bedside_lamps:
    "Reading lights, smart wake-up lamps, and design-forward picks — editorial and lab sources verified in Canada",
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
  white_t_shirts_for_men:
    "Crew-neck staples from budget multipacks to premium cotton — ten expert sources cross-checked for Canada",
  white_t_shirts_for_women:
    "Crewnecks, baby tees, and scoop-necks from fashion and lab roundups — verified at Canadian retailers and Canadian-made options",
  fitness_tracker:
    "Heart rate, GPS, and sleep tracking tested for accuracy, from budget bands to smartwatches",
  exercise_bikes:
    "Spin bikes, smart bikes, and recumbents tested for ride quality — verified at Canadian retailers",
  alarm_clocks:
    "Sunrise lamps, smart clocks, and classic bedside models — tested picks with Canadian stock and pricing",
  deodorant:
    "Natural and antiperspirant picks tested for odor control, including Canadian-made options",
  nonstick_pan:
    "Ceramic, PTFE, and carbon steel pans tested with eggs and crepes, including Canadian-made Paderno",
  light_therapy_lamp:
    "10,000-lux SAD lamps tested for Canadian winters, from compact desk models to clinical-grade boxes",
  tv:
    "OLED, Mini-LED, and budget picks tested for picture quality, gaming, and bright-room viewing in Canada",
  sofa:
    "Modular, custom, and budget couches ranked for comfort and durability, with Canadian retailers verified",
  compression_socks:
    "Graduated compression for travel, workouts, and long days on your feet — expert picks verified in Canada",
  electric_toothbrush:
    "Sonic and oscillating picks tested for plaque removal, pressure sensors, and battery life — verified for Canada",
};

const CATEGORY_ORDER = [
  "robot_vacuum",
  "headphones",
  "air_purifier",
  "mosquito_gear",
  "drip_coffee_maker",
  "refrigerators",
  "office_chairs",
  "mattress",
  "bed_sheets",
  "turntable",
  "bedside_lamps",
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
  "white_t_shirts_for_men",
  "white_t_shirts_for_women",
  "fitness_tracker",
  "exercise_bikes",
  "alarm_clocks",
  "deodorant",
  "nonstick_pan",
  "light_therapy_lamp",
  "tv",
  "sofa",
  "compression_socks",
  "electric_toothbrush",
];

const FALLBACK_IMAGE =
  "https://images.unsplash.com/photo-1556228578-0d85b1a4d571?w=800&h=600&fit=crop&q=80";

function getCategories(): Category[] {
  const path = frontendSrcDataPath("categories.json");
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
                        <h3 className="text-[15px] font-normal text-[var(--color-muted)] mb-4" style={{ fontFamily: "var(--font-serif)" }}>
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
