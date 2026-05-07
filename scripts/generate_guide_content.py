"""
Script 8: generate_guide_content.py

Generate Wirecutter-voiced editorial content for each category guide.
Two-pass pipeline:
  1. Draft: structured rationale + prose, with voice library examples in context
  2. De-AI rewrite: cleanup pass focused on removing AI tells

Uses OpenAI Responses API with gpt-4o and structured outputs (two-pass draft + rewrite).

Usage: python3 scripts/generate_guide_content.py --category robot_vacuum
"""

import json
import os
import re
import sys
from pathlib import Path
from dotenv import load_dotenv

sys.stdout.reconfigure(line_buffering=True)
from openai import OpenAI
from config import get_category_config

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

VOICE_LIBRARY = Path(__file__).resolve().parent / "voice_library"
FRONTEND_DATA = Path(__file__).resolve().parent.parent / "frontend" / "src" / "data"

PICK_OBJECT_SCHEMA = {
    "type": "object",
    "properties": {
        "headline": {"type": "string"},
        "writeup": {"type": "string"},
        "best_for": {"type": "string"},
        "skip_if": {"type": "string"},
    },
    "required": ["headline", "writeup", "best_for", "skip_if"],
    "additionalProperties": False,
}


def build_schema(active_roles):
    """Build JSON schema dynamically so only active pick roles are required."""
    picks_props = {role: PICK_OBJECT_SCHEMA for role in active_roles}
    return {
        "type": "object",
        "properties": {
            "intro": {"type": "string"},
            "picks": {
                "type": "object",
                "properties": picks_props,
                "required": list(active_roles),
                "additionalProperties": False,
            },
            "who_this_is_for": {"type": "string"},
            "how_we_picked": {"type": "string"},
        },
        "required": ["intro", "picks", "who_this_is_for", "how_we_picked"],
        "additionalProperties": False,
    }


def load_voice_file(name):
    path = VOICE_LIBRARY / name
    if path.exists():
        return path.read_text()
    return ""


def build_pick_data(picks, products):
    product_by_id = {p["id"]: p for p in products}
    pick_summaries = []
    for pick in picks:
        if not pick.get("name"):
            continue
        product = product_by_id.get(pick.get("id"), {})
        sources = product.get("sources", [])
        positives = product.get("positives_detail", []) or product.get("positives", [])
        negatives = product.get("negatives_detail", []) or product.get("negatives", [])
        pick_summaries.append({
            "role": pick["role"],
            "name": pick["name"],
            "price_cad": pick.get("price_cad"),
            "retailer": pick.get("retailer"),
            "use_case": pick.get("use_case"),
            "sources": sources,
            "source_count": len(sources),
            "positives": positives[:6],
            "negatives": negatives[:4],
            "canadian_company": product.get("canadian_company", False),
            "made_in_canada": product.get("made_in_canada", False),
            "in_stock": product.get("in_stock", False),
            "recommendations": product.get("recommendations", []),
        })
    return pick_summaries


def build_draft_prompt(category_name, source_names, pick_data, product_count):
    rules = load_voice_file("rules.md")

    voice_examples = []
    for name in ["intro.md", "best_overall.md", "budget_pick.md", "upgrade_pick.md",
                  "also_great.md", "canadian_pick.md", "who_this_is_for.md", "methodology.md"]:
        content = load_voice_file(name)
        if content.strip():
            voice_examples.append(f"--- {name} ---\n{content}")

    picks_json = json.dumps(pick_data, indent=2)

    return f"""You are writing editorial content for a Canada Picks product guide about {category_name}.

Canada Picks is a Canadian product recommendation site. We do NOT test products ourselves.
We aggregate recommendations from independent expert reviewers and verify Canadian
availability and pricing. Our sources for this guide: {', '.join(source_names)}.

We looked at {product_count} products total across those sources.

IMPORTANT FORMATTING RULES (violating any of these is a failure):
1. NEVER use em dashes. Use commas, periods, or parentheses instead.
2. NEVER use markdown formatting. No **bold**, no *italics*, no ## headings, no bullet
   points inside writeups. Output plain prose paragraphs only.
3. NEVER start a paragraph with a bold summary sentence. Just write the paragraph normally.

=== VOICE RULES ===
{rules}

===============================================================================
=== STYLE REFERENCE EXAMPLES (DO NOT USE THESE PRODUCTS) =====================
===============================================================================

The examples below are from DIFFERENT guides and categories. They show the WRITING
STYLE you must follow: the sentence structure, paragraph flow, headline patterns,
claim-then-evidence rhythm, and tone.

The product names in these examples (Roborock Q7, Coway Mighty2, Sony WH-1000XM6,
OXO Brew, etc.) are NOT your products. DO NOT mention them in your output. Study
only HOW the prose is written, not WHAT products it describes.

{chr(10).join(voice_examples)}

===============================================================================
=== END OF STYLE REFERENCES ==================================================
===============================================================================

=== HEADLINE RULES ===
Headlines must pass this test: could this headline apply to a DIFFERENT product in the
category? If yes, it's too generic. Rewrite it.

Formula: [specific trait] + [specific trait], often with a "but" or contrast.

GOOD (each one could only describe ONE product):
- "A smart, quick robot that empties itself" (specific: self-emptying + fast)
- "Solid performer, less refined" (specific: honest contrast)
- "Tiny standout for small rooms" (specific: size + use case)
- "Good coffee, great features" (specific: honest trade-off)
- "Strong suction at half the price" (specific: value claim)
- "Hot-water mopping with 3-hour battery" (specific: two measurable traits)

BAD (could describe literally any product):
- "A powerful cleaner with useful features"
- "Affordable with competitive features"
- "Premium features for serious cleaning"
- "Advanced features at a competitive price"
- "A local option with strong features"
- "High-performance option for large spaces"

To write a good headline, pick the ONE thing this product does that others don't,
or the ONE trade-off that defines it. Name that thing.

===============================================================================
=== YOUR ACTUAL PRODUCT DATA (USE ONLY THESE) =================================
===============================================================================

The following products are the ONLY products in this guide. Every product name,
price, feature, and reviewer attribution in your output MUST come from this data.
If a fact isn't in this data, don't invent it.

{picks_json}

===============================================================================

=== INSTRUCTIONS ===

For each pick, first think through:
- Why it won its role (cite specific reviewer findings, not vague praise)
- The main trade-off or flaw
- Who it's best for (specific person or situation, not "families seeking a reliable cleaner")
- Who should skip it

Then write the prose based on that thinking.

Generate the following sections:

1. "intro": 2-3 short paragraphs introducing {category_name} for Canadian buyers.
   Open with a specific, interesting truth about the category (study the Wirecutter
   intro examples above for the pattern, but write about YOUR category).
   Set expectations honestly. End by naming your top pick confidently.
   Use our aggregator voice (we cross-referenced sources, we didn't test).

2. "picks": For each active pick role, generate:
   - "headline": A specific, vivid claim. NOT generic ("A powerful cleaner with useful features").
     YES specific ("Quiet, thorough, and it empties itself" or "Strong suction at half the price").
     The headline should tell the reader something concrete about THIS product that isn't true
     of other products in the category. Study the example headlines above for the pattern.
   - "writeup": 2-3 paragraphs. Lead each paragraph with a bold, specific claim, then back it
     up (study the example writeups for this rhythm).
     ALWAYS name the reviewer source by name: "RTINGS rated...", "Vacuum Wars ranked...",
     "Consumer Reports scored...". NEVER write "some reviewers noted" or "reviewers highlighted".
     Name them. Include at least one specific flaw, stated directly (not softened with "however").
   - "best_for": One sentence. Be specific about the person or situation.
     BAD: "Great for families seeking a reliable cleaner." (generic, could be any vacuum)
     GOOD: "If you have pets and hardwood floors, this handles fur without scratching."
   - "skip_if": One sentence. Be specific.
     BAD: "Those looking for top-tier performance might want more."
     GOOD: "Not worth the premium if you only vacuum once a week on hard floors."

   Only generate pick content for roles that have products in the data above.

3. "who_this_is_for": 1-2 paragraphs. Name specific people and situations.
   Always include who does NOT need this product. Be honest about limitations.

4. "how_we_picked": 1-2 paragraphs explaining our process. Name the sources.
   Mention Canadian verification as our unique step.

=== ANTI-AI CHECKLIST (check every sentence against these) ===
- NO em dashes. Ever. Use commas, periods, or parentheses.
- NO "we tested" or "in our tests". We aggregate.
- NO banned words (see rules).
- NO generic phrases: "an appealing choice", "a versatile solution", "a reliable option",
  "an impressive performer", "a solid choice", "a worthy contender", "a compelling option".
  These are empty. Replace with something specific to THIS product.
- NO "ideal for" or "perfect for". Write "If you [situation], this [specific benefit]."
- NO "This model is great for..." or "This is the right pick for...". Just say who and why.
- ALWAYS name the reviewer: "RTINGS", "Vacuum Wars", "Consumer Reports". Not "reviewers".
- Every flaw must be stated plainly. Not "while it performs well, it may occasionally struggle"
  but "its obstacle avoidance misses furniture legs in tight layouts."
- Vary sentence openings. Absolutely no two consecutive sentences starting with "The", "It",
  "Its", or "This".
"""


def build_rewrite_prompt(draft_json):
    return f"""You are a ruthless copy editor who hates AI-sounding writing. Your ONLY job is
to make this text sound like it was written by a human editor, not generated by AI.

The content below is a JSON object with editorial text for a product guide.

Go sentence by sentence and fix these problems:

1. KILL EM DASHES. Replace every single one with a comma, period, or parentheses.

1b. KILL MARKDOWN. Remove all **bold**, *italics*, ## headings, or any markdown formatting.
    These are plain text strings inside JSON. No formatting markup of any kind.

2. KILL GENERIC PHRASES. These must be removed or rewritten:
   - "an appealing choice" / "a compelling option" / "a solid choice" / "a versatile solution"
   - "an impressive performer" / "a worthy contender" / "a reliable option"
   - "ideal for" / "perfect for those who" / "great for" / "making it ideal"
   - "This model is great for..." / "This is the right pick for..."
   Replace with something specific to the actual product.

3. KILL VAGUE ATTRIBUTION. "Some reviewers noted" / "Reviewers highlighted" / "reviewers mentioned"
   must become a specific source name: RTINGS, Vacuum Wars, Consumer Reports, etc.

4. KILL FILLER. Cut: actually, really, truly, certainly, definitely, quite, rather, somewhat.
   Also cut "ensuring that", "allowing for", "providing you with".

5. KILL SOFTENED FLAWS. "While it performs well, it may occasionally struggle" becomes
   "Its obstacle avoidance misses furniture legs in tight layouts."
   State the flaw directly. No hedging.

6. FIX REPETITIVE OPENINGS. If two sentences in a row start with "The", "It", "Its", or
   "This", rewrite one of them.

7. BANNED WORDS (remove or replace): boasts, elevate, seamless, game-changer, landscape,
   cutting-edge, innovative, dive into, plethora, comprehensive, robust, leverage,
   revolutionize, unparalleled, best-in-class, holistic, synergy, paradigm, state-of-the-art,
   world-class, must-have, ensure, utilize, moreover, furthermore, additionally, notably,
   streamlined, navigate (metaphorical), designed to, stands out as.

8. NO TESTING CLAIMS. We aggregate reviews, we don't test. Fix any sentence that implies
   we used the product.

Return the exact same JSON structure. Only edit the string values.

=== CONTENT TO CLEAN ===
{draft_json}
"""


def minimal_guide_stub(category_name, source_names, product_count):
    src = ", ".join(source_names) if source_names else "our sources"
    return {
        "intro": (
            f"This guide covers {category_name} for Canadians. We aggregate picks from reviewers "
            f"including {src} and verify Canadian listings where possible. Browse the picks below "
            f"once featured slots are populated."
        ),
        "picks": {},
        "who_this_is_for": (
            f"Readers who want a short list of reviewer-backed {category_name.lower()} options "
            f"with Canadian availability checks."
        ),
        "how_we_picked": (
            "Canada Picks scores how often independent reviewers converge on each product, then "
            f"checks buyability and stock for Canada ({product_count} products in this dataset)."
        ),
    }


def generate_guide(category_name, source_names, pick_data, product_count):
    active_roles = [p["role"] for p in pick_data]
    if not active_roles:
        print(
            "  WARNING: No featured picks with names; writing minimal guide stub (no LLM calls)."
        )
        return minimal_guide_stub(category_name, source_names, product_count)

    schema = build_schema(active_roles)

    print("  Pass 1: Drafting editorial content...")
    draft_prompt = build_draft_prompt(category_name, source_names, pick_data, product_count)

    for attempt in range(2):
        try:
            draft_response = client.responses.create(
                model="gpt-4o",
                input=[{"role": "user", "content": draft_prompt}],
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "guide_content",
                        "strict": True,
                        "schema": schema,
                    }
                },
            )
            draft_text = draft_response.output_text
            draft = json.loads(draft_text)
            break
        except Exception as e:
            if attempt == 0:
                print(f"    Draft attempt failed ({e}), retrying...")
                continue
            print(f"    ERROR: Draft generation failed after 2 attempts: {e}")
            return None

    print(f"    Draft complete. Intro: {len(draft['intro'])} chars, "
          f"Picks: {len(draft.get('picks', {}))} roles")

    print("  Pass 2: De-AI rewrite pass...")
    rewrite_prompt = build_rewrite_prompt(draft_text)

    for attempt in range(2):
        try:
            rewrite_response = client.responses.create(
                model="gpt-4o",
                input=[{"role": "user", "content": rewrite_prompt}],
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "guide_content",
                        "strict": True,
                        "schema": schema,
                    }
                },
            )
            final = json.loads(rewrite_response.output_text)
            break
        except Exception as e:
            if attempt == 0:
                print(f"    Rewrite attempt failed ({e}), retrying...")
                continue
            print(f"    WARNING: Rewrite failed, using draft as final: {e}")
            return draft

    print(f"    Rewrite complete. Intro: {len(final['intro'])} chars")

    final = strip_markdown_from_guide(final)
    return final


def strip_markdown_from_guide(guide):
    """Remove markdown bold/italic/heading markup from all string values."""
    def clean(text):
        if not isinstance(text, str):
            return text
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
        text = re.sub(r'\*(.+?)\*', r'\1', text)
        text = re.sub(r'^#{1,3}\s+', '', text, flags=re.MULTILINE)
        text = text.replace('\u2014', ', ').replace('\u2013', ', ')
        return text

    cleaned = {}
    for key, val in guide.items():
        if isinstance(val, str):
            cleaned[key] = clean(val)
        elif isinstance(val, dict):
            cleaned[key] = {}
            for k2, v2 in val.items():
                if isinstance(v2, dict):
                    cleaned[key][k2] = {k3: clean(v3) for k3, v3 in v2.items()}
                else:
                    cleaned[key][k2] = clean(v2)
        else:
            cleaned[key] = val
    return cleaned


def main():
    cfg = get_category_config()
    category_id = cfg["_category_id"]
    category_name = cfg.get("category_name", category_id.replace("_", " ").title())

    print("=" * 60)
    print(f"Script 8: Generating guide content [{category_id}]")
    print("=" * 60)

    out_dir = FRONTEND_DATA / category_id
    picks_path = out_dir / "site_featured_picks.json"
    products_path = out_dir / "site_products.json"

    if not picks_path.exists() or not products_path.exists():
        print(f"ERROR: Missing site data. Run build_site_data.py first.")
        sys.exit(1)

    with open(picks_path) as f:
        picks = json.load(f)
    with open(products_path) as f:
        products = json.load(f)

    source_names = [
        s["source_name"]
        for s in cfg.get("reviewer_sources") or []
        if isinstance(s, dict) and s.get("source_name")
    ]
    pick_data = build_pick_data(picks, products)
    product_count = len(products)

    print(f"  Category: {category_name}")
    print(f"  Sources: {', '.join(source_names)}")
    print(f"  Active picks: {len(pick_data)}")
    print(f"  Total products: {product_count}")
    print()

    guide = generate_guide(category_name, source_names, pick_data, product_count)

    if guide is None:
        print("\n  ERROR: Guide generation failed. Skipping guide_content.json.")
        print("  The guide page will still render without editorial content.")
        sys.exit(1)

    output_path = out_dir / "guide_content.json"
    with open(output_path, "w") as f:
        json.dump(guide, f, indent=2)

    print(f"\n  Wrote guide content to {output_path}")
    print("Done.")


if __name__ == "__main__":
    main()
