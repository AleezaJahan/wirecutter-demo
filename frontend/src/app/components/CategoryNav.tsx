"use client";

import Link from "next/link";
import { useState, useRef, useEffect } from "react";

type CategoryItem = {
  id: string;
  name: string;
  title: string;
};

type Department = {
  label: string;
  categories: CategoryItem[];
};

const DEPARTMENTS: Department[] = [
  {
    label: "Electronics",
    categories: [
      { id: "tv", name: "TVs", title: "The Best TVs" },
      { id: "headphones", name: "Headphones", title: "The Best Noise-Cancelling Headphones" },
      { id: "wireless_earbud", name: "Wireless Earbuds", title: "The Best Wireless Earbuds" },
      { id: "turntable", name: "Turntables", title: "The Best Turntables" },
      { id: "usb_battery_pack", name: "Battery Packs", title: "The Best USB Battery Packs" },
      { id: "fitness_tracker", name: "Fitness Trackers", title: "The Best Fitness Trackers" },
      { id: "exercise_bikes", name: "Exercise Bikes", title: "The Best Exercise Bikes" },
      { id: "password_manager", name: "Password Managers", title: "The Best Password Managers" },
    ],
  },
  {
    label: "Home",
    categories: [
      { id: "robot_vacuum", name: "Robot Vacuums", title: "The Best Robot Vacuums" },
      { id: "air_purifier", name: "Air Purifiers", title: "The Best Air Purifiers" },
      { id: "humidifier", name: "Humidifiers", title: "The Best Humidifiers" },
      { id: "mosquito_gear", name: "Mosquito Gear", title: "The Best Mosquito Repellents & Gear" },
      { id: "light_therapy_lamp", name: "Light Therapy Lamps", title: "The Best Light Therapy Lamps" },
      { id: "office_chairs", name: "Office Chairs", title: "The Best Office Chairs" },
      { id: "sofa", name: "Sofas", title: "The Best Sofas" },
    ],
  },
  {
    label: "Kitchen",
    categories: [
      { id: "drip_coffee_maker", name: "Coffee Makers", title: "The Best Coffee Makers" },
      { id: "refrigerators", name: "Refrigerators", title: "The Best Refrigerators" },
      { id: "nonstick_pan", name: "Non-Stick Pans", title: "The Best Non-Stick Pans" },
      { id: "water_bottle", name: "Water Bottles", title: "The Best Water Bottles" },
    ],
  },
  {
    label: "Sleep & Comfort",
    categories: [
      { id: "mattress", name: "Mattresses", title: "The Best Mattresses" },
      { id: "bed_sheets", name: "Bed Sheets", title: "The Best Bed Sheets" },
      { id: "bedside_lamps", name: "Bedside Lamps", title: "The Best Bedside Lamps" },
      { id: "alarm_clocks", name: "Alarm Clocks", title: "The Best Alarm Clocks" },
      { id: "slipper", name: "Slippers", title: "The Best Slippers" },
      { id: "travel_pillow", name: "Travel Pillows", title: "The Best Travel Pillows" },
    ],
  },
  {
    label: "Personal Care",
    categories: [
      { id: "vitamin_c_serum", name: "Vitamin C Serums", title: "The Best Vitamin C Serums" },
      { id: "red_light_therapy_device", name: "Red Light Therapy", title: "The Best Red Light Therapy Devices" },
      { id: "deodorant", name: "Deodorants", title: "The Best Deodorants" },
      { id: "electric_toothbrush", name: "Electric Toothbrushes", title: "The Best Electric Toothbrushes" },
      { id: "clothing_steamer", name: "Clothing Steamers", title: "The Best Clothing Steamers" },
      { id: "compression_socks", name: "Compression Socks", title: "The Best Compression Socks" },
    ],
  },
  {
    label: "Style",
    categories: [
      { id: "white_sneaker", name: "White Sneakers", title: "The Best White Sneakers" },
      { id: "white_t_shirts_for_men", name: "White T-Shirts (Men)", title: "The Best White T-Shirts for Men" },
      { id: "white_t_shirts_for_women", name: "White T-Shirts (Women)", title: "The Best White T-Shirts for Women" },
    ],
  },
];

export default function CategoryNav({ activeCategoryId }: { activeCategoryId?: string }) {
  const [openDept, setOpenDept] = useState<string | null>(null);
  const [mobileOpen, setMobileOpen] = useState(false);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const navRef = useRef<HTMLDivElement>(null);

  const activeDept = activeCategoryId
    ? DEPARTMENTS.find((d) => d.categories.some((c) => c.id === activeCategoryId))?.label ?? null
    : null;

  function handleMouseEnter(label: string) {
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    setOpenDept(label);
  }

  function handleMouseLeave() {
    timeoutRef.current = setTimeout(() => setOpenDept(null), 150);
  }

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (navRef.current && !navRef.current.contains(e.target as Node)) {
        setOpenDept(null);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <nav ref={navRef} className="border-b border-[var(--color-rule)] bg-white relative z-40">
      <div className="max-w-7xl mx-auto px-6">
        {/* Desktop nav */}
        <div className="hidden md:flex items-center gap-0 h-11 -mx-3">
          {DEPARTMENTS.map((dept) => (
            <div
              key={dept.label}
              className="relative"
              onMouseEnter={() => handleMouseEnter(dept.label)}
              onMouseLeave={handleMouseLeave}
            >
              <button
                className={`px-3 h-11 flex items-center text-[13px] transition-colors relative ${
                  activeDept === dept.label
                    ? "text-[var(--color-red)] font-medium"
                    : "text-[var(--color-secondary)] hover:text-[var(--color-ink)]"
                }`}
                onClick={() => setOpenDept(openDept === dept.label ? null : dept.label)}
              >
                {dept.label}
                <svg
                  className={`ml-1 w-3 h-3 transition-transform ${openDept === dept.label ? "rotate-180" : ""}`}
                  fill="none"
                  viewBox="0 0 12 12"
                  stroke="currentColor"
                  strokeWidth={2}
                >
                  <path d="M3 4.5l3 3 3-3" />
                </svg>
                {activeDept === dept.label && (
                  <span className="absolute bottom-0 left-3 right-3 h-[2px] bg-[var(--color-red)]" />
                )}
              </button>

              {/* Dropdown */}
              {openDept === dept.label && (
                <div
                  className="absolute top-full left-0 pt-1 z-50 animate-[fadeIn_0.15s_ease-out]"
                  onMouseEnter={() => handleMouseEnter(dept.label)}
                  onMouseLeave={handleMouseLeave}
                >
                  <div className="bg-white rounded-lg shadow-lg ring-1 ring-black/8 py-2 min-w-[240px]">
                    <div className="px-4 py-2 border-b border-[var(--color-rule)] mb-1">
                      <span className="text-[11px] font-bold uppercase tracking-wider text-[var(--color-muted)]">
                        {dept.label}
                      </span>
                    </div>
                    {dept.categories.map((cat) => (
                      <Link
                        key={cat.id}
                        href={`/category/${cat.id}`}
                        className={`block px-4 py-2 text-[14px] transition-colors ${
                          activeCategoryId === cat.id
                            ? "text-[var(--color-red)] bg-[var(--color-surface)] font-medium"
                            : "text-[var(--color-ink)] hover:bg-[var(--color-surface)] hover:text-[var(--color-red)]"
                        }`}
                        onClick={() => setOpenDept(null)}
                      >
                        {cat.name}
                      </Link>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Mobile nav toggle */}
        <div className="md:hidden flex items-center h-11">
          <button
            className="flex items-center gap-2 text-[13px] text-[var(--color-secondary)]"
            onClick={() => setMobileOpen(!mobileOpen)}
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              {mobileOpen ? (
                <path d="M6 18L18 6M6 6l12 12" />
              ) : (
                <path d="M4 6h16M4 12h16M4 18h16" />
              )}
            </svg>
            Browse categories
            {activeDept && (
              <span className="text-[var(--color-red)] font-medium">· {activeDept}</span>
            )}
          </button>
        </div>
      </div>

      {/* Mobile dropdown */}
      {mobileOpen && (
        <div className="md:hidden border-t border-[var(--color-rule)] bg-white max-h-[70vh] overflow-y-auto">
          <div className="max-w-7xl mx-auto px-6 py-4 space-y-4">
            {DEPARTMENTS.map((dept) => (
              <div key={dept.label}>
                <h4 className="text-[11px] font-bold uppercase tracking-wider text-[var(--color-muted)] mb-2">
                  {dept.label}
                </h4>
                <div className="grid grid-cols-2 gap-x-4 gap-y-1">
                  {dept.categories.map((cat) => (
                    <Link
                      key={cat.id}
                      href={`/category/${cat.id}`}
                      className={`text-[14px] py-1.5 transition-colors ${
                        activeCategoryId === cat.id
                          ? "text-[var(--color-red)] font-medium"
                          : "text-[var(--color-ink)] hover:text-[var(--color-red)]"
                      }`}
                      onClick={() => setMobileOpen(false)}
                    >
                      {cat.name}
                    </Link>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </nav>
  );
}
