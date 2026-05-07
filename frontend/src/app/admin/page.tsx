import { readFileSync, existsSync } from "fs";
import { join } from "path";
import Link from "next/link";
import { AdminDashboard } from "./dashboard";

type Category = { id: string; name: string; product_count: number };
type Pick = {
  role: string;
  role_display: string;
  id: string | null;
  name: string | null;
  price_cad?: number | null;
  price_display: string | null;
  retailer: string | null;
  context?: string;
  image_url?: string;
  canadianness_tier?: string | null;
  source_count?: number;
};
type Product = {
  id: string;
  name: string;
  brand: string;
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
  alternative_retailers: { retailer: string; product_url: string; price_display: string | null }[];
  positives: string[];
  negatives: string[];
};
type BrandOrigin = {
  brand_name: string;
  headquarters_location: string | null;
  canadian_company: boolean;
  made_in_canada: boolean;
  confidence: string;
  notes: string;
};

export type PurchasePath = {
  canonical_product_id: string;
  canonical_product_name: string;
  brand: string;
  retailer: string | null;
  product_url: string | null;
  price_cad: number | null;
  in_stock: boolean | null;
  canada_verified: boolean;
  canadian_company: boolean;
  made_in_canada: boolean;
  alternative_retailers: { retailer: string; product_url: string; price_cad: number | null }[];
  notes: string;
};

export type CategoryData = {
  id: string;
  name: string;
  picks: Pick[];
  products: Product[];
  brands: BrandOrigin[];
  scoring: string[][];
  purchasePaths: PurchasePath[];
};

export const metadata = {
  title: "Admin — Canada Picks Data Explorer",
};

function loadJSON<T>(path: string): T | null {
  if (!existsSync(path)) return null;
  return JSON.parse(readFileSync(path, "utf-8"));
}

function loadCSV(path: string): string[][] {
  if (!existsSync(path)) return [];
  const text = readFileSync(path, "utf-8").trim();
  if (!text) return [];
  return text.split("\n").map((line) => {
    const row: string[] = [];
    let current = "";
    let inQuotes = false;
    for (const ch of line) {
      if (ch === '"') {
        inQuotes = !inQuotes;
      } else if (ch === "," && !inQuotes) {
        row.push(current.trim());
        current = "";
      } else {
        current += ch;
      }
    }
    row.push(current.trim());
    return row;
  });
}

export default function AdminPage() {
  const dataRoot = join(process.cwd(), "..", "data");
  const frontendData = join(process.cwd(), "src", "data");

  const categoriesPath = join(frontendData, "categories.json");
  const categories: Category[] = existsSync(categoriesPath)
    ? JSON.parse(readFileSync(categoriesPath, "utf-8"))
    : [];

  const allData: CategoryData[] = categories.map((cat) => {
    const picks = loadJSON<Pick[]>(join(frontendData, cat.id, "site_featured_picks.json")) ?? [];
    const products = loadJSON<Product[]>(join(frontendData, cat.id, "site_products.json")) ?? [];
    const brandFile = loadJSON<{ brand_origins: BrandOrigin[] }>(join(dataRoot, cat.id, "brand_origins.json"));
    const brands = brandFile?.brand_origins ?? [];
    const scoring = loadCSV(join(dataRoot, cat.id, "scoring_breakdown.csv"));
    const ppFile = loadJSON<{ purchase_paths: PurchasePath[]; metadata: Record<string, unknown> }>(join(dataRoot, cat.id, "canada_purchase_paths.json"));
    const purchasePaths = ppFile?.purchase_paths ?? [];
    return { id: cat.id, name: cat.name, picks, products, brands, scoring, purchasePaths };
  });

  return (
    <main className="flex-1 bg-[var(--color-surface)]">
      <header className="border-b border-[var(--color-rule)] bg-white">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link
              href="/"
              className="text-[17px] text-[var(--color-ink)] hover:text-[var(--color-red)] transition-colors"
              style={{ fontFamily: "var(--font-serif)" }}
            >
              Canada Picks
            </Link>
            <span className="text-[var(--color-rule)]">/</span>
            <span className="text-[14px] font-medium text-[var(--color-muted)]">Data Explorer</span>
          </div>
          <Link href="/" className="text-[13px] text-[var(--color-muted)] hover:text-[var(--color-ink)]">
            Back to site
          </Link>
        </div>
      </header>
      <AdminDashboard data={allData} />
    </main>
  );
}
