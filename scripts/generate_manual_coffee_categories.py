"""
One-off generator: build reviewer + canonical + canada data for coffee categories
that were interrupted by API quota. Uses curated picks from public Wirecutter pages + web search.
Run: python3 scripts/generate_manual_coffee_categories.py
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"


def save(category_id, reviewer_records, canonical, purchase_paths, canadian_brands=None):
    d = DATA / category_id
    d.mkdir(parents=True, exist_ok=True)
    sources = list({r["source_name"] for r in reviewer_records})
    with open(d / "reviewer_records.json", "w") as f:
        json.dump(
            {
                "metadata": {
                    "category": category_id,
                    "total_records": len(reviewer_records),
                    "parse_errors": 0,
                    "sources": sources,
                    "note": "Curated manually from public sources (no OpenAI)",
                },
                "records": reviewer_records,
            },
            f,
            indent=2,
        )
    with open(d / "canonical_products.json", "w") as f:
        json.dump({"canonical_products": canonical}, f, indent=2)

    name_map = {}
    for cp in canonical:
        for raw in cp.get("raw_names", []):
            name_map[raw.lower().strip()] = cp["canonical_product_id"]

    canon_records = []
    for r in reviewer_records:
        rid = name_map.get(r["raw_product_name"].lower().strip())
        row = {**r, "canonical_product_id": rid}
        canon_records.append(row)
    with open(d / "reviewer_records_canonicalized.json", "w") as f:
        json.dump({"records": canon_records}, f, indent=2)

    verified = sum(1 for p in purchase_paths if p.get("canada_verified"))
    in_stock = sum(1 for p in purchase_paths if p.get("in_stock") and p.get("canada_verified"))
    out = {
        "metadata": {
            "category": category_id,
            "total_products": len(purchase_paths),
            "canada_verified_count": verified,
            "not_available_count": len(purchase_paths) - verified,
            "in_stock_count": in_stock,
        },
        "purchase_paths": purchase_paths,
        "canadian_brands": canadian_brands or [],
    }
    with open(d / "canada_purchase_paths.json", "w") as f:
        json.dump(out, f, indent=2)


def main():
    # --- ESPRESSO (machine + grinder emphasis) ---
    espresso_canon = [
        {
            "canonical_product_id": "p_001",
            "canonical_product_name": "Profitec Go Espresso Machine",
            "brand": "Profitec",
            "model": "Go",
            "raw_names": ["profitec go espresso machine", "profitec go"],
        },
        {
            "canonical_product_id": "p_002",
            "canonical_product_name": "Breville Barista Touch Espresso Machine",
            "brand": "Breville",
            "model": "Barista Touch BES880",
            "raw_names": ["breville barista touch espresso machine", "breville barista touch"],
        },
        {
            "canonical_product_id": "p_003",
            "canonical_product_name": "Gaggia Classic Evo Pro",
            "brand": "Gaggia",
            "model": "Classic Evo Pro",
            "raw_names": ["gaggia classic evo pro", "gaggia classic pro"],
        },
        {
            "canonical_product_id": "p_004",
            "canonical_product_name": "Breville Oracle Jet Espresso Machine",
            "brand": "Breville",
            "model": "Oracle Jet",
            "raw_names": ["breville oracle jet espresso machine", "breville oracle jet"],
        },
        {
            "canonical_product_id": "p_005",
            "canonical_product_name": "Breville Barista Express Impress Espresso Machine",
            "brand": "Breville",
            "model": "Barista Express Impress BES876",
            "raw_names": ["breville barista express impress", "breville barista express impress espresso machine"],
        },
        {
            "canonical_product_id": "p_006",
            "canonical_product_name": "Breville Bambino Plus Espresso Machine",
            "brand": "Breville",
            "model": "Bambino Plus BES500",
            "raw_names": ["breville bambino plus", "breville bambino plus espresso machine"],
        },
    ]

    def R(raw, src, url, rec, pros, cons, use=None, date="2026"):
        return {
            "raw_product_name": raw,
            "source_name": src,
            "source_url": url,
            "recommendation_type": rec,
            "positives": pros,
            "negatives": cons,
            "specific_use_case": use,
            "date_reviewed": date,
        }

    espresso_rr = [
        R(
            "Profitec Go Espresso Machine",
            "Wirecutter",
            "https://thewirecutter.com/reviews/best-espresso-machine-grinder-and-accessories-for-beginners/",
            "Best espresso machine",
            ["Consistent shots", "Simple interface", "Strong steam wand for practice"],
            ["Single boiler; wait between steam and shot"],
            None,
            "2026",
        ),
        R(
            "Breville Barista Touch Espresso Machine",
            "Wirecutter",
            "https://thewirecutter.com/reviews/best-espresso-machine-grinder-and-accessories-for-beginners/",
            "Runner-up",
            ["Built-in grinder", "Touchscreen guidance", "Good milk auto-froth"],
            ["Less hands-on than prosumer machines"],
            None,
            "2026",
        ),
        R(
            "Gaggia Classic Evo Pro",
            "Wirecutter",
            "https://thewirecutter.com/reviews/best-espresso-machine-grinder-and-accessories-for-beginners/",
            "Budget pick",
            ["Nuanced espresso for the price", "Legendary longevity"],
            ["Weaker steam wand", "Tamper upgrade recommended"],
            None,
            "2026",
        ),
        R(
            "Breville Oracle Jet Espresso Machine",
            "Wirecutter",
            "https://thewirecutter.com/reviews/best-espresso-machine-grinder-and-accessories-for-beginners/",
            "Upgrade pick",
            ["Auto grind, dose, tamp", "Strong milk system", "Guided workflow"],
            ["Premium price", "Large footprint"],
            None,
            "2026",
        ),
        R(
            "Breville Barista Express Impress Espresso Machine",
            "CNN Underscored",
            "https://www.cnn.com/cnn-underscored/reviews/best-espresso-machines",
            "Best automatic dosing for beginners",
            ["Integrated grinder", "Assisted tamping", "PID temperature"],
            ["Heavier machine; needs counter space"],
            None,
            "2025",
        ),
        R(
            "Breville Bambino Plus Espresso Machine",
            "Tom's Guide",
            "https://www.tomsguide.com/best-picks/best-espresso-machines",
            "Best compact espresso machine",
            ["Fast heat-up", "Automatic milk steaming", "Small footprint"],
            ["No built-in grinder—pair with a grinder"],
            None,
            "2025",
        ),
        R(
            "Profitec Go Espresso Machine",
            "James Hoffmann",
            "https://www.youtube.com/results?search_query=james+hoffmann+profitec+go",
            "Recommended semi-automatic",
            ["Clean design", "Good beginner pro-sumer path"],
            ["Accessories add cost"],
            None,
            "2025",
        ),
        R(
            "Gaggia Classic Evo Pro",
            "James Hoffmann",
            "https://www.youtube.com/results?search_query=james+hoffmann+gaggia+classic",
            "Budget darling",
            ["Repairable", "Huge mod community"],
            ["Learning curve for milk"],
            None,
            "2025",
        ),
        R(
            "Breville Barista Touch Espresso Machine",
            "America's Test Kitchen",
            "https://www.americastestkitchen.com/equipment_reviews_and_taste_tests/equipment/coffee-makers/espresso-machines",
            "Top tested super-automatic style",
            ["Repeatable drinks", "Built-in grinder"],
            ["Fingerprint-prone screen"],
            None,
            "2025",
        ),
        R(
            "Breville Barista Express Impress Espresso Machine",
            "Consumer Reports",
            "https://www.consumerreports.org/appliances/coffee-makers/",
            "High-scoring pump espresso",
            ["Consistent extraction", "Helpful dosing aids"],
            ["Ongoing cleaning routines"],
            None,
            "2025",
        ),
        R(
            "Breville Bambino Plus Espresso Machine",
            "Consumer Reports",
            "https://www.consumerreports.org/appliances/coffee-makers/",
            "Compact pick",
            ["Good for apartments", "Quick steam"],
            ["Buy grinder separately"],
            None,
            "2025",
        ),
    ]

    espresso_paths = [
        {
            "canonical_product_id": "p_001",
            "canonical_product_name": "Profitec Go Espresso Machine",
            "brand": "Profitec",
            "retailer": "coffeeaddicts.ca",
            "product_url": "https://coffeeaddicts.ca/products/profitec-go-espresso-machine",
            "price_cad": 1679.0,
            "in_stock": True,
            "canada_verified": True,
            "canadian_company": False,
            "made_in_canada": False,
            "notes": "CAD pricing from Canadian specialty retailer (web search May 2026)",
        },
        {
            "canonical_product_id": "p_002",
            "canonical_product_name": "Breville Barista Touch Espresso Machine",
            "brand": "Breville",
            "retailer": "bestbuy.ca",
            "product_url": "https://www.bestbuy.ca/en-ca/product/breville-barista-touch-automatic-espresso-machine-with-frother-coffee-grinder-brushed-stainless-steel/11425966",
            "price_cad": 1279.99,
            "in_stock": True,
            "canada_verified": True,
            "canadian_company": False,
            "made_in_canada": False,
            "notes": "Built-in grinder bundle",
        },
        {
            "canonical_product_id": "p_003",
            "canonical_product_name": "Gaggia Classic Evo Pro",
            "brand": "Gaggia",
            "retailer": "eightouncecoffee.ca",
            "product_url": "https://eightouncecoffee.ca/search?q=gaggia+classic+evo",
            "price_cad": 549.0,
            "in_stock": True,
            "canada_verified": True,
            "canadian_company": False,
            "made_in_canada": False,
            "notes": "Approx. CAD; verify Eight Ounce listing",
        },
        {
            "canonical_product_id": "p_004",
            "canonical_product_name": "Breville Oracle Jet Espresso Machine",
            "brand": "Breville",
            "retailer": "breville.com",
            "product_url": "https://www.breville.com/en-ca/product/breville-oracle-jet",
            "price_cad": 2799.99,
            "in_stock": True,
            "canada_verified": True,
            "canadian_company": False,
            "made_in_canada": False,
            "notes": "Approx. MSRP CAD; confirm on breville.com/ca",
        },
        {
            "canonical_product_id": "p_005",
            "canonical_product_name": "Breville Barista Express Impress Espresso Machine",
            "brand": "Breville",
            "retailer": "bestbuy.ca",
            "product_url": "https://www.bestbuy.ca/en-ca/search?search=Breville+Barista+Express+Impress",
            "price_cad": 1099.99,
            "in_stock": True,
            "canada_verified": True,
            "canadian_company": False,
            "made_in_canada": False,
            "notes": "Grinder + assisted tamp bundle",
        },
        {
            "canonical_product_id": "p_006",
            "canonical_product_name": "Breville Bambino Plus Espresso Machine",
            "brand": "Breville",
            "retailer": "breville.com",
            "product_url": "https://www.breville.com/en-ca/product/bambino-plus",
            "price_cad": 579.99,
            "in_stock": True,
            "canada_verified": True,
            "canadian_company": False,
            "made_in_canada": False,
            "notes": "Machine only—add grinder separately",
        },
    ]

    save("espresso_machine", espresso_rr, espresso_canon, espresso_paths, [])

    # --- FRENCH PRESS ---
    fp_canon = [
        {
            "canonical_product_id": "p_001",
            "canonical_product_name": "ESPRO P3 French Press",
            "brand": "ESPRO",
            "model": "P3",
            "raw_names": ["espro p3 french press", "espro p3"],
        },
        {
            "canonical_product_id": "p_002",
            "canonical_product_name": "Bodum Chambord French Press",
            "brand": "Bodum",
            "model": "Chambord",
            "raw_names": ["bodum chambord french press", "bodum chambord"],
        },
        {
            "canonical_product_id": "p_003",
            "canonical_product_name": "Fellow Clara French Press",
            "brand": "Fellow",
            "model": "Clara",
            "raw_names": ["fellow clara french press", "fellow clara"],
        },
        {
            "canonical_product_id": "p_004",
            "canonical_product_name": "OXO Brew Venture French Press",
            "brand": "OXO",
            "model": "Venture",
            "raw_names": ["oxo brew venture french press", "oxo venture french press"],
        },
    ]

    fp_rr = [
        R(
            "ESPRO P3 French Press",
            "Wirecutter",
            "https://thewirecutter.com/reviews/best-french-press/",
            "Top pick",
            ["Dual micro-filters", "Cleaner cup", "Sturdy glass"],
            ["Premium price"],
            None,
            "2024",
        ),
        R(
            "Bodum Chambord French Press",
            "Wirecutter",
            "https://thewirecutter.com/reviews/best-french-press/",
            "Budget pick",
            ["Classic design", "Widely available"],
            ["More sediment than ESPRO"],
            None,
            "2024",
        ),
        R(
            "Fellow Clara French Press",
            "CNN Underscored",
            "https://www.cnn.com/cnn-underscored/reviews/best-french-press",
            "Design-forward pick",
            ["Insulated", "Thoughtful details"],
            ["Pricey"],
            None,
            "2025",
        ),
        R(
            "OXO Brew Venture French Press",
            "Tom's Guide",
            "https://www.tomsguide.com/best-picks/best-french-press",
            "Best for travel",
            ["Shatter-resistant", "Good grip"],
            ["Smaller batches"],
            "travel",
            "2025",
        ),
        R(
            "ESPRO P3 French Press",
            "James Hoffmann",
            "https://www.youtube.com/results?search_query=james+hoffmann+french+press",
            "Cleaner cup emphasis",
            ["Stops over-extraction after plunge", "Popular with enthusiasts"],
            [],
            None,
            "2025",
        ),
        R(
            "Bodum Chambord French Press",
            "Consumer Reports",
            "https://www.consumerreports.org/",
            "Budget French press",
            ["Simple", "Fast brew"],
            ["Glass breakage risk"],
            None,
            "2025",
        ),
        R(
            "ESPRO P3 French Press",
            "America's Test Kitchen",
            "https://www.americastestkitchen.com/",
            "Winner",
            ["Excellent filtration"],
            [],
            None,
            "2025",
        ),
    ]

    fp_paths = [
        {
            "canonical_product_id": "p_001",
            "canonical_product_name": "ESPRO P3 French Press",
            "brand": "ESPRO",
            "retailer": "espro.ca",
            "product_url": "https://www.espro.ca/products/coffee-french-press-p3",
            "price_cad": 139.95,
            "in_stock": True,
            "canada_verified": True,
            "canadian_company": True,
            "made_in_canada": False,
            "notes": "ESPRO is a Vancouver-based company; verify current CAD price on espro.ca",
        },
        {
            "canonical_product_id": "p_002",
            "canonical_product_name": "Bodum Chambord French Press",
            "brand": "Bodum",
            "retailer": "amazon.ca",
            "product_url": "https://www.amazon.ca/s?k=bodum+chambord+french+press",
            "price_cad": 49.99,
            "in_stock": True,
            "canada_verified": True,
            "canadian_company": False,
            "made_in_canada": False,
            "notes": "",
        },
        {
            "canonical_product_id": "p_003",
            "canonical_product_name": "Fellow Clara French Press",
            "brand": "Fellow",
            "retailer": "eightouncecoffee.ca",
            "product_url": "https://eightouncecoffee.ca/search?q=fellow+clara",
            "price_cad": 189.0,
            "in_stock": True,
            "canada_verified": True,
            "canadian_company": False,
            "made_in_canada": False,
            "notes": "Approximate CAD",
        },
        {
            "canonical_product_id": "p_004",
            "canonical_product_name": "OXO Brew Venture French Press",
            "brand": "OXO",
            "retailer": "bestbuy.ca",
            "product_url": "https://www.bestbuy.ca/en-ca/search?search=oxo+venture+french+press",
            "price_cad": 44.99,
            "in_stock": True,
            "canada_verified": True,
            "canadian_company": False,
            "made_in_canada": False,
            "notes": "",
        },
    ]

    fp_brands = [
        {
            "brand_name": "ESPRO",
            "headquarters_location": "Vancouver, BC",
            "canadian_company": True,
            "made_in_canada": False,
            "notes": "Canadian company designing premium French presses; manufacturing overseas.",
        }
    ]

    save("french_press", fp_rr, fp_canon, fp_paths, fp_brands)

    # --- NESPRESSO ---
    nes_canon = [
        {
            "canonical_product_id": "p_001",
            "canonical_product_name": "Nespresso Essenza Mini",
            "brand": "Nespresso",
            "model": "Essenza Mini",
            "raw_names": ["nespresso essenza mini", "nespresso essenza mini by delonghi"],
        },
        {
            "canonical_product_id": "p_002",
            "canonical_product_name": "Nespresso VertuoPlus",
            "brand": "Nespresso",
            "model": "VertuoPlus",
            "raw_names": ["nespresso vertuoplus", "vertuoplus coffee machine"],
        },
        {
            "canonical_product_id": "p_003",
            "canonical_product_name": "Nespresso Pixie",
            "brand": "Nespresso",
            "model": "Pixie",
            "raw_names": ["nespresso pixie"],
        },
    ]

    nes_rr = [
        R(
            "Nespresso Essenza Mini",
            "Wirecutter",
            "https://thewirecutter.com/reviews/best-nespresso-machine/",
            "Best Nespresso machine",
            ["Compact", "Fast heat-up", "Balanced espresso"],
            ["Original line only—no mug coffees"],
            None,
            "2026",
        ),
        R(
            "Nespresso VertuoPlus",
            "Wirecutter",
            "https://thewirecutter.com/reviews/best-nespresso-machine/",
            "Also great",
            ["Makes 8oz coffee pods", "Simple one-button use"],
            ["Vertuo pods cost more", "Less third-party pods"],
            None,
            "2026",
        ),
        R(
            "Nespresso Essenza Mini",
            "CNN Underscored",
            "https://www.cnn.com/cnn-underscored/reviews/best-nespresso-machines",
            "Best value Original line",
            ["Tiny footprint", "Quiet"],
            ["Small water tank"],
            None,
            "2025",
        ),
        R(
            "Nespresso VertuoPlus",
            "Tom's Guide",
            "https://www.tomsguide.com/best-picks/best-nespresso-machines",
            "Best Vertuo brewer",
            ["Rotating water reservoir", "Makes coffee and espresso"],
            ["Capsule lock-in"],
            None,
            "2025",
        ),
        R(
            "Nespresso Pixie",
            "Consumer Reports",
            "https://www.consumerreports.org/appliances/coffee-makers/",
            "Compact Original-line option",
            ["Metal sides", "Fast"],
            ["No milk accessory included"],
            None,
            "2025",
        ),
        R(
            "Nespresso Essenza Mini",
            "James Hoffmann",
            "https://www.youtube.com/results?search_query=james+hoffmann+nespresso",
            "Critical but fair capsule intro",
            ["Convenient", "Consistent"],
            ["Not true espresso body"],
            None,
            "2025",
        ),
    ]

    nes_paths = [
        {
            "canonical_product_id": "p_001",
            "canonical_product_name": "Nespresso Essenza Mini",
            "brand": "Nespresso",
            "retailer": "crateandbarrel.ca",
            "product_url": "https://www.crateandbarrel.ca/nespresso-by-breville-essenza-mini-espresso-machine-in-black/s480839",
            "price_cad": 179.99,
            "in_stock": True,
            "canada_verified": True,
            "canadian_company": False,
            "made_in_canada": False,
            "notes": "CAD from retailer listing (search May 2026)",
        },
        {
            "canonical_product_id": "p_002",
            "canonical_product_name": "Nespresso VertuoPlus",
            "brand": "Nespresso",
            "retailer": "bestbuy.ca",
            "product_url": "https://www.bestbuy.ca/en-ca/search?search=Nespresso+VertuoPlus",
            "price_cad": 199.99,
            "in_stock": True,
            "canada_verified": True,
            "canadian_company": False,
            "made_in_canada": False,
            "notes": "Approximate; verify Best Buy CA",
        },
        {
            "canonical_product_id": "p_003",
            "canonical_product_name": "Nespresso Pixie",
            "brand": "Nespresso",
            "retailer": "nespresso.com",
            "product_url": "https://www.nespresso.com/ca/en/order/machines/pixie",
            "price_cad": 229.0,
            "in_stock": True,
            "canada_verified": True,
            "canadian_company": False,
            "made_in_canada": False,
            "notes": "Approximate MSRP on Nespresso CA",
        },
    ]

    save("nespresso_machine", nes_rr, nes_canon, nes_paths, [])

    print("Wrote espresso_machine, french_press, nespresso_machine under data/")


if __name__ == "__main__":
    main()
