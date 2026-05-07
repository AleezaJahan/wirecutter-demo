"use client";

import { useState } from "react";
import type { CategoryData, PurchasePath } from "./page";

const ROLE_LABELS: Record<string, string> = {
  best_overall: "Our pick",
  best_budget: "Budget pick",
  best_upgrade: "Upgrade pick",
  best_for_specific_use_case: "Also great",
  best_canadian_option: "Canadian-owned pick",
};

function Badge({ color, children }: { color: string; children: React.ReactNode }) {
  const colors: Record<string, string> = {
    green: "bg-emerald-50 text-emerald-700 border-emerald-200",
    red: "bg-red-50 text-red-700 border-red-200",
    yellow: "bg-amber-50 text-amber-700 border-amber-200",
    blue: "bg-blue-50 text-blue-700 border-blue-200",
    gray: "bg-gray-50 text-gray-500 border-gray-200",
  };
  return (
    <span className={`text-[11px] font-medium px-2 py-0.5 border rounded ${colors[color] ?? colors.gray}`}>
      {children}
    </span>
  );
}

function OverviewTable({ data }: { data: CategoryData[] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-[13px]">
        <thead>
          <tr className="border-b border-[var(--color-rule)] text-left text-[var(--color-muted)]">
            <th className="py-3 pr-4 font-medium">Category</th>
            <th className="py-3 px-4 font-medium text-center">Products</th>
            <th className="py-3 px-4 font-medium text-center">Picks filled</th>
            <th className="py-3 px-4 font-medium text-center">CDN brands</th>
            <th className="py-3 px-4 font-medium text-center">Verified</th>
            <th className="py-3 px-4 font-medium text-center">URL failed</th>
            <th className="py-3 px-4 font-medium text-center">Not found</th>
            <th className="py-3 px-4 font-medium text-center">In stock</th>
          </tr>
        </thead>
        <tbody>
          {data.map((cat) => {
            const filledPicks = cat.picks.filter((p) => p.name);
            const cdnBrands = cat.brands.filter((b) => b.canadian_company);
            const pp = cat.purchasePaths;
            const verified = pp.filter((p) => p.canada_verified);
            const urlFailed = pp.filter((p) => (p.notes || "").includes("URL validation failed"));
            const noRetailer = pp.filter((p) => !p.canada_verified && !p.retailer);
            const inStock = pp.filter((p) => p.in_stock);
            return (
              <tr key={cat.id} className="border-b border-[var(--color-rule)] hover:bg-white/60">
                <td className="py-3 pr-4 font-medium text-[var(--color-ink)]">{cat.name}</td>
                <td className="py-3 px-4 text-center">{pp.length}</td>
                <td className="py-3 px-4 text-center">
                  <Badge color={filledPicks.length >= 4 ? "green" : filledPicks.length >= 2 ? "yellow" : "red"}>
                    {filledPicks.length}/{cat.picks.length}
                  </Badge>
                </td>
                <td className="py-3 px-4 text-center">
                  <Badge color={cdnBrands.length > 0 ? "green" : "gray"}>
                    {cdnBrands.length}
                  </Badge>
                </td>
                <td className="py-3 px-4 text-center">{verified.length}/{pp.length}</td>
                <td className="py-3 px-4 text-center">
                  {urlFailed.length > 0 ? <Badge color="red">{urlFailed.length}</Badge> : <span className="text-[var(--color-muted)]">0</span>}
                </td>
                <td className="py-3 px-4 text-center">
                  {noRetailer.length > 0 ? <Badge color="yellow">{noRetailer.length}</Badge> : <span className="text-[var(--color-muted)]">0</span>}
                </td>
                <td className="py-3 px-4 text-center">{inStock.length}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function PicksTable({ picks }: { picks: CategoryData["picks"] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-[13px]">
        <thead>
          <tr className="border-b border-[var(--color-rule)] text-left text-[var(--color-muted)]">
            <th className="py-2 pr-3 font-medium">Role</th>
            <th className="py-2 px-3 font-medium">Product</th>
            <th className="py-2 px-3 font-medium">Price</th>
            <th className="py-2 px-3 font-medium">Retailer</th>
            <th className="py-2 px-3 font-medium">Context</th>
          </tr>
        </thead>
        <tbody>
          {picks.map((p) => (
            <tr key={p.role} className="border-b border-[var(--color-rule)]">
              <td className="py-2 pr-3">
                <span className="text-[var(--color-red)] font-medium">
                  {ROLE_LABELS[p.role] ?? p.role_display}
                </span>
              </td>
              <td className="py-2 px-3 text-[var(--color-ink)] font-medium max-w-[250px] truncate">
                {p.name ?? <span className="text-[var(--color-muted)] italic">empty</span>}
              </td>
              <td className="py-2 px-3 tabular-nums">{p.price_display ?? "—"}</td>
              <td className="py-2 px-3">{p.retailer ?? "—"}</td>
              <td className="py-2 px-3 text-[var(--color-muted)] max-w-[300px] truncate">{p.context ?? "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ProductsTable({ products }: { products: CategoryData["products"] }) {
  const [sortKey, setSortKey] = useState<"name" | "price" | "brand">("price");

  const sorted = [...products].sort((a, b) => {
    if (sortKey === "price") {
      if (a.price_cad === null && b.price_cad === null) return 0;
      if (a.price_cad === null) return 1;
      if (b.price_cad === null) return -1;
      return a.price_cad - b.price_cad;
    }
    if (sortKey === "brand") return (a.brand ?? "").localeCompare(b.brand ?? "");
    return (a.name ?? "").localeCompare(b.name ?? "");
  });

  return (
    <div className="overflow-x-auto">
      <div className="flex gap-2 mb-3 text-[12px]">
        <span className="text-[var(--color-muted)]">Sort:</span>
        {(["price", "name", "brand"] as const).map((k) => (
          <button
            key={k}
            onClick={() => setSortKey(k)}
            className={`px-2 py-0.5 rounded ${sortKey === k ? "bg-[var(--color-ink)] text-white" : "bg-white border border-[var(--color-rule)] text-[var(--color-muted)] hover:text-[var(--color-ink)]"}`}
          >
            {k}
          </button>
        ))}
      </div>
      <table className="w-full text-[13px]">
        <thead>
          <tr className="border-b border-[var(--color-rule)] text-left text-[var(--color-muted)]">
            <th className="py-2 pr-2 font-medium w-8">ID</th>
            <th className="py-2 px-2 font-medium">Product</th>
            <th className="py-2 px-2 font-medium">Brand</th>
            <th className="py-2 px-2 font-medium">Price</th>
            <th className="py-2 px-2 font-medium">Retailer</th>
            <th className="py-2 px-2 font-medium text-center">Stock</th>
            <th className="py-2 px-2 font-medium text-center">Verified</th>
            <th className="py-2 px-2 font-medium text-center">CDN</th>
            <th className="py-2 px-2 font-medium text-center">Alts</th>
            <th className="py-2 px-2 font-medium text-center">Pros</th>
            <th className="py-2 px-2 font-medium text-center">Cons</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((p) => (
            <tr key={p.id} className="border-b border-[var(--color-rule)] hover:bg-white/60">
              <td className="py-1.5 pr-2 text-[11px] text-[var(--color-muted)] font-mono">{p.id}</td>
              <td className="py-1.5 px-2 text-[var(--color-ink)] max-w-[220px] truncate">
                {p.product_url ? (
                  <a href={p.product_url} target="_blank" rel="noopener noreferrer" className="hover:underline text-[var(--color-link)]">
                    {p.name}
                  </a>
                ) : p.name}
                {p.is_on_sale && <span className="ml-1 text-[10px] text-blue-600 font-medium">SALE</span>}
              </td>
              <td className="py-1.5 px-2">{p.brand}</td>
              <td className="py-1.5 px-2 tabular-nums">
                {p.is_on_sale && p.original_price_display && (
                  <span className="line-through text-[var(--color-muted)] mr-1">{p.original_price_display}</span>
                )}
                {p.price_display}
              </td>
              <td className="py-1.5 px-2">{p.retailer}</td>
              <td className="py-1.5 px-2 text-center">
                {p.in_stock ? <Badge color="green">yes</Badge> : <Badge color="yellow">no</Badge>}
              </td>
              <td className="py-1.5 px-2 text-center">
                {p.canada_verified ? <Badge color="green">yes</Badge> : <Badge color="red">no</Badge>}
              </td>
              <td className="py-1.5 px-2 text-center">
                {p.canadian_company ? <Badge color="green">CDN</Badge> : null}
                {p.made_in_canada ? <Badge color="blue">MiC</Badge> : null}
              </td>
              <td className="py-1.5 px-2 text-center">{p.alternative_retailers?.length || 0}</td>
              <td className="py-1.5 px-2 text-center">{p.positives?.length || 0}</td>
              <td className="py-1.5 px-2 text-center">{p.negatives?.length || 0}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ScoringTable({ scoring, paths }: { scoring: string[][]; paths: PurchasePath[] }) {
  if (scoring.length === 0) return <p className="text-[13px] text-[var(--color-muted)] italic">No scoring data available.</p>;
  const headers = scoring[0];
  const rows = scoring.slice(1);

  const pathByName: Record<string, PurchasePath> = {};
  for (const p of paths) {
    pathByName[p.canonical_product_name] = p;
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-[12px]">
        <thead>
          <tr className="border-b border-[var(--color-rule)]">
            {headers.map((h, i) => (
              <th key={i} className="py-2 px-2 text-left font-medium text-[var(--color-muted)] whitespace-nowrap">
                {h}
              </th>
            ))}
            <th className="py-2 px-2 text-center font-medium text-[var(--color-muted)] whitespace-nowrap">Buyable in CA</th>
            <th className="py-2 px-2 text-center font-medium text-[var(--color-muted)] whitespace-nowrap">In stock</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row, ri) => {
            const productName = row[0];
            const role = row[1];
            const isHighlighted = role && role.length > 0;
            const pp = pathByName[productName];
            const verified = pp?.canada_verified;
            const inStock = pp?.in_stock;
            const isFiltered = pp && !verified;
            return (
              <tr key={ri} className={`border-b border-[var(--color-rule)] ${isHighlighted ? "bg-red-50/40" : isFiltered ? "bg-amber-50/30" : "hover:bg-white/60"}`}>
                {row.map((cell, ci) => (
                  <td key={ci} className={`py-1.5 px-2 whitespace-nowrap ${ci === 0 ? "font-medium text-[var(--color-ink)] max-w-[200px] truncate" : ci === 1 && cell ? "text-[var(--color-red)] font-medium" : "tabular-nums"}`}>
                    {cell || "—"}
                  </td>
                ))}
                <td className="py-1.5 px-2 text-center">
                  {pp ? (verified ? <Badge color="green">yes</Badge> : <Badge color="red">no</Badge>) : <span className="text-[var(--color-muted)]">—</span>}
                </td>
                <td className="py-1.5 px-2 text-center">
                  {pp ? (inStock ? <Badge color="green">yes</Badge> : <Badge color="yellow">no</Badge>) : <span className="text-[var(--color-muted)]">—</span>}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function BrandsTable({ brands }: { brands: CategoryData["brands"] }) {
  if (brands.length === 0) return <p className="text-[13px] text-[var(--color-muted)] italic">No brand origin data.</p>;
  const sorted = [...brands].sort((a, b) => {
    if (a.canadian_company && !b.canadian_company) return -1;
    if (!a.canadian_company && b.canadian_company) return 1;
    return (a.brand_name ?? "").localeCompare(b.brand_name ?? "");
  });

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-[13px]">
        <thead>
          <tr className="border-b border-[var(--color-rule)] text-left text-[var(--color-muted)]">
            <th className="py-2 pr-3 font-medium">Brand</th>
            <th className="py-2 px-3 font-medium">HQ</th>
            <th className="py-2 px-3 font-medium text-center">Canadian</th>
            <th className="py-2 px-3 font-medium text-center">Made in Canada</th>
            <th className="py-2 px-3 font-medium">Confidence</th>
            <th className="py-2 px-3 font-medium">Notes</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((b, i) => (
            <tr key={i} className={`border-b border-[var(--color-rule)] ${b.canadian_company ? "bg-emerald-50/40" : ""}`}>
              <td className="py-1.5 pr-3 font-medium text-[var(--color-ink)]">{b.brand_name}</td>
              <td className="py-1.5 px-3 text-[var(--color-muted)]">{b.headquarters_location ?? "—"}</td>
              <td className="py-1.5 px-3 text-center">
                {b.canadian_company ? <Badge color="green">yes</Badge> : <span className="text-[var(--color-muted)]">no</span>}
              </td>
              <td className="py-1.5 px-3 text-center">
                {b.made_in_canada ? <Badge color="blue">yes</Badge> : <span className="text-[var(--color-muted)]">no</span>}
              </td>
              <td className="py-1.5 px-3">{b.confidence}</td>
              <td className="py-1.5 px-3 text-[var(--color-muted)] max-w-[300px] truncate">{b.notes || "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function PurchasePathsTable({ paths }: { paths: PurchasePath[] }) {
  const [filter, setFilter] = useState<"all" | "verified" | "failed" | "url_failed">("all");

  const filtered = paths.filter((p) => {
    if (filter === "verified") return p.canada_verified;
    if (filter === "failed") return !p.canada_verified;
    if (filter === "url_failed") return (p.notes || "").includes("URL validation failed");
    return true;
  });

  const sorted = [...filtered].sort((a, b) => {
    if (a.canada_verified && !b.canada_verified) return -1;
    if (!a.canada_verified && b.canada_verified) return 1;
    return (a.canonical_product_name ?? "").localeCompare(b.canonical_product_name ?? "");
  });

  return (
    <div className="overflow-x-auto">
      <div className="flex gap-2 mb-3 text-[12px]">
        <span className="text-[var(--color-muted)]">Filter:</span>
        {([
          ["all", `All (${paths.length})`],
          ["verified", `Verified (${paths.filter((p) => p.canada_verified).length})`],
          ["failed", `Failed (${paths.filter((p) => !p.canada_verified).length})`],
          ["url_failed", `URL failed (${paths.filter((p) => (p.notes || "").includes("URL validation")).length})`],
        ] as const).map(([key, label]) => (
          <button
            key={key}
            onClick={() => setFilter(key)}
            className={`px-2 py-0.5 rounded ${filter === key ? "bg-[var(--color-ink)] text-white" : "bg-white border border-[var(--color-rule)] text-[var(--color-muted)] hover:text-[var(--color-ink)]"}`}
          >
            {label}
          </button>
        ))}
      </div>
      <table className="w-full text-[13px]">
        <thead>
          <tr className="border-b border-[var(--color-rule)] text-left text-[var(--color-muted)]">
            <th className="py-2 pr-2 font-medium w-10">ID</th>
            <th className="py-2 px-2 font-medium">Product</th>
            <th className="py-2 px-2 font-medium">Brand</th>
            <th className="py-2 px-2 font-medium">Retailer</th>
            <th className="py-2 px-2 font-medium">Price</th>
            <th className="py-2 px-2 font-medium text-center">Verified</th>
            <th className="py-2 px-2 font-medium text-center">Stock</th>
            <th className="py-2 px-2 font-medium text-center">Alts</th>
            <th className="py-2 px-2 font-medium">Notes</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((p) => {
            const isUrlFail = (p.notes || "").includes("URL validation failed");
            return (
              <tr
                key={p.canonical_product_id}
                className={`border-b border-[var(--color-rule)] ${
                  isUrlFail ? "bg-red-50/40" : !p.canada_verified ? "bg-amber-50/30" : "hover:bg-white/60"
                }`}
              >
                <td className="py-1.5 pr-2 text-[11px] text-[var(--color-muted)] font-mono">{p.canonical_product_id}</td>
                <td className="py-1.5 px-2 text-[var(--color-ink)] max-w-[200px] truncate">
                  {p.product_url ? (
                    <a href={p.product_url} target="_blank" rel="noopener noreferrer" className="hover:underline text-[var(--color-link)]">
                      {p.canonical_product_name}
                    </a>
                  ) : p.canonical_product_name}
                </td>
                <td className="py-1.5 px-2">{p.brand}</td>
                <td className="py-1.5 px-2">{p.retailer ?? <span className="text-[var(--color-muted)] italic">none</span>}</td>
                <td className="py-1.5 px-2 tabular-nums">
                  {p.price_cad != null ? `$${p.price_cad.toFixed(2)}` : "—"}
                </td>
                <td className="py-1.5 px-2 text-center">
                  {p.canada_verified ? <Badge color="green">yes</Badge> : <Badge color="red">no</Badge>}
                </td>
                <td className="py-1.5 px-2 text-center">
                  {p.in_stock === true ? <Badge color="green">yes</Badge> : p.in_stock === false ? <Badge color="yellow">no</Badge> : <span className="text-[var(--color-muted)]">—</span>}
                </td>
                <td className="py-1.5 px-2 text-center">{p.alternative_retailers?.length || 0}</td>
                <td className="py-1.5 px-2 text-[var(--color-muted)] max-w-[250px] truncate text-[12px]">
                  {p.notes || "—"}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

type Tab = "overview" | "picks" | "products" | "scoring" | "brands" | "purchase_paths";

export function AdminDashboard({ data }: { data: CategoryData[] }) {
  const [selectedCategory, setSelectedCategory] = useState<string>(data[0]?.id ?? "");
  const [tab, setTab] = useState<Tab>("overview");

  const cat = data.find((d) => d.id === selectedCategory);
  const tabs: { id: Tab; label: string }[] = [
    { id: "overview", label: "Overview" },
    { id: "picks", label: "Featured Picks" },
    { id: "scoring", label: "Scoring" },
    { id: "purchase_paths", label: "Purchase Paths" },
    { id: "products", label: "All Products" },
    { id: "brands", label: "Brand Origins" },
  ];

  return (
    <div className="max-w-7xl mx-auto px-6 py-8">
      {/* Stats row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
        {[
          { label: "Categories", value: data.length },
          { label: "Total products", value: data.reduce((s, d) => s + d.products.length, 0) },
          { label: "Featured picks", value: data.reduce((s, d) => s + d.picks.filter((p) => p.name).length, 0) },
          { label: "Canadian brands", value: data.reduce((s, d) => s + d.brands.filter((b) => b.canadian_company).length, 0) },
        ].map((stat) => (
          <div key={stat.label} className="bg-white border border-[var(--color-rule)] p-4 rounded">
            <div className="text-[24px] font-medium text-[var(--color-ink)] tabular-nums">{stat.value}</div>
            <div className="text-[12px] text-[var(--color-muted)] mt-0.5">{stat.label}</div>
          </div>
        ))}
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1 border-b border-[var(--color-rule)] mb-6">
        {tabs.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`px-4 py-2.5 text-[13px] font-medium transition-colors border-b-2 -mb-px ${
              tab === t.id
                ? "border-[var(--color-red)] text-[var(--color-ink)]"
                : "border-transparent text-[var(--color-muted)] hover:text-[var(--color-ink)]"
            }`}
          >
            {t.label}
          </button>
        ))}

        {tab !== "overview" && (
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="ml-auto text-[13px] border border-[var(--color-rule)] rounded px-3 py-1.5 text-[var(--color-ink)] bg-white"
          >
            {data.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name}
              </option>
            ))}
          </select>
        )}
      </div>

      {/* Content */}
      <div className="bg-white border border-[var(--color-rule)] rounded p-6">
        {tab === "overview" && <OverviewTable data={data} />}
        {tab === "picks" && cat && <PicksTable picks={cat.picks} />}
        {tab === "products" && cat && <ProductsTable products={cat.products} />}
        {tab === "scoring" && cat && <ScoringTable scoring={cat.scoring} paths={cat.purchasePaths} />}
        {tab === "purchase_paths" && cat && <PurchasePathsTable paths={cat.purchasePaths} />}
        {tab === "brands" && cat && <BrandsTable brands={cat.brands} />}
      </div>
    </div>
  );
}
