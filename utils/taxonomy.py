"""Approved Creative OS taxonomy.

Source of truth: data/approved_taxonomy.json generated from
Creative_OS_Approved_Taxonomy_Handover.md. Do not rewrite taxonomy copy here;
the JSON preserves the exact names and table cells from the approved handover.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path


DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "approved_taxonomy.json"

PRODUCT_KIND_KEYS = {
    "angles": ("Code", "MA Name"),
    "beliefs": ("Code", "Belief Name"),
    "cohorts": ("Code", "Cohort Name", "Cohort"),
    "drivers": ("Code", "Driver Name", "Driver"),
    "claims": ("Proof Code", "Proof / Claim"),
}

UNIVERSAL_KIND_KEYS = {
    "video_subtypes": ("Code", "Name"),
    "static_subtypes": ("Code", "Name"),
    "visual_hook_types": ("Code", "Name"),
    "content_hook_types": ("Code", "Name"),
    "emotional_arcs": ("Code", "Name"),
    "funnel_stages": ("Code", "Name"),
    "creator_archetypes": ("Code", "Name"),
    "influence_modes": ("Code", "Name"),
    "visual_treatments": ("Code", "Name"),
    "cta_formats": ("Code", "Name"),
    "cta_message_types": ("Code", "Name"),
    "static_message_types": ("Code", "Name"),
}

DEFINITION_FIELDS = [
    "One-line definition",
    "Simple definition",
    "Definition",
    "Belief shift: from -> to",
    "Belief shift: from → to",
    "Belief shift",
    "Core pain / desire",
    "Core pain",
    "Core tension",
    "Trigger",
    "Trigger evidence",
    "Required context / caveat",
    "Required context",
    "Can be used for",
]


@lru_cache(maxsize=1)
def _data() -> dict:
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


def _rows(table: dict) -> list[dict]:
    return list(table.get("rows", [])) if table else []


def _code(row: dict) -> str:
    return str(row.get("Code") or row.get("Proof Code") or row.get("Product Code") or "").strip()


def _name(row: dict, *candidates: str) -> str:
    for key in candidates:
        value = str(row.get(key, "") or "").strip()
        if value:
            return value
    return ""


def item(code: str, label: str) -> str:
    return f"{code} - {label}" if code else label


def _item_from_row(row: dict, kind: str, universal: bool = False) -> str:
    keys = UNIVERSAL_KIND_KEYS.get(kind) if universal else PRODUCT_KIND_KEYS.get(kind)
    if not keys:
        return ""
    code = _name(row, keys[0])
    label = _name(row, *keys[1:])
    return item(code, label)


def _table(product: str, kind: str) -> dict:
    product_label = canonical_product(product)
    return _data().get("product_taxonomy", {}).get(product_label, {}).get(kind, {"headers": [], "rows": []})


def _universal_table(kind: str) -> dict:
    return _data().get("universal", {}).get(kind, {"headers": [], "rows": []})


def _values(product: str, kind: str) -> list[str]:
    return [_item_from_row(row, kind) for row in _rows(_table(product, kind))]


def _universal_values(kind: str) -> list[str]:
    return [_item_from_row(row, kind, universal=True) for row in _rows(_universal_table(kind))]


@lru_cache(maxsize=1)
def _index_rows() -> dict[str, dict]:
    indexed: dict[str, dict] = {}
    for product, groups in _data().get("product_taxonomy", {}).items():
        for kind, table in groups.items():
            for row in _rows(table):
                code = _code(row)
                if code:
                    enriched = dict(row)
                    enriched["_Product"] = product
                    enriched["_Kind"] = kind
                    enriched["_Headers"] = table.get("headers", [])
                    indexed[code] = enriched
    for kind, table in _data().get("universal", {}).items():
        for row in _rows(table):
            code = _code(row)
            if code:
                enriched = dict(row)
                enriched["_Kind"] = kind
                enriched["_Headers"] = table.get("headers", [])
                indexed[code] = enriched
    return indexed


def code_of(value: str) -> str:
    text = str(value or "").strip()
    if " - " in text:
        return text.split(" - ", 1)[0].strip()
    return text


def label_of(value: str) -> str:
    text = str(value or "").strip()
    if " - " in text:
        return text.split(" - ", 1)[1].strip()
    return text


def metadata_for(value: str) -> dict:
    return _index_rows().get(code_of(value), {})


def define(value: str) -> str:
    row = metadata_for(value)
    for field in DEFINITION_FIELDS:
        value = str(row.get(field, "") or "").strip()
        if value:
            return value
    return ""


def tooltip_for(value: str, fields: list[str] | None = None) -> str:
    row = metadata_for(value)
    if not row:
        return ""
    ordered = fields or [field for field in row.get("_Headers", []) if field not in {"Code", "Proof Code", "Name", "MA Name", "Belief Name", "Cohort Name", "Cohort", "Driver Name", "Driver", "Proof / Claim"}]
    lines = []
    for field in ordered:
        cell = str(row.get(field, "") or "").strip()
        if cell:
            lines.append(f"{field}: {cell}")
    return "\n\n".join(lines)


def table_rows_for_product(product: str, kind: str) -> tuple[list[str], list[dict]]:
    table = _table(product, kind)
    return list(table.get("headers", [])), _rows(table)


def universal_table_rows(kind: str) -> tuple[list[str], list[dict]]:
    table = _universal_table(kind)
    return list(table.get("headers", [])), _rows(table)


def options_with_blank(options: list[str]) -> list[str]:
    """Use for optional selectboxes: blank is not a taxonomy value."""
    return options if options else [""]


def selected_info(value: str) -> str:
    """Short exact-source info block for UI captions under dropdowns."""
    if not str(value or "").strip():
        return ""
    definition = define(value)
    tooltip = tooltip_for(value)
    if tooltip and definition and definition in tooltip:
        return tooltip
    if tooltip:
        return tooltip
    return definition


PRODUCTS = [row["App Label"] for row in _data().get("products", [])]

PRODUCT_META = {
    row["App Label"]: {
        "code": row.get("Product Code", ""),
        "name": row.get("Product Name", ""),
        "priority": row.get("Priority", ""),
        "confidence": row.get("Taxonomy Confidence", ""),
        "notes": row.get("Notes", ""),
    }
    for row in _data().get("products", [])
}

PRODUCT_ALIASES: dict[str, str] = {}
for row in _data().get("products", []):
    label = row.get("App Label", "")
    for key in ("Product Code", "Product Name", "App Label"):
        value = str(row.get(key, "") or "").strip()
        if value:
            PRODUCT_ALIASES[value.lower()] = label

PRODUCT_ALIASES.update({
    "rcf": "Rapid Clear Facewash",
    "rapid clear face wash": "Rapid Clear Facewash",
    "rapid clear facewash": "Rapid Clear Facewash",
    "lpp": "Liquid Pimple Patch",
    "sfa": "SpotFade Serum",
    "sfar": "SpotFade Serum",
    "sfars": "SpotFade Serum",
    "sfs": "SpotFade Serum",
    "spot fade serum": "SpotFade Serum",
    "spotfade serum": "SpotFade Serum",
    "emc": "Effortless Melting Cleanser",
    "clear protect gel sunscreen": "Clear Protect Sunscreen",
    "clear protect sunscreen": "Clear Protect Sunscreen",
    "cpg": "Clear Protect Sunscreen",
    "cpgs": "Clear Protect Sunscreen",
    "sunscreen": "Clear Protect Sunscreen",
    "brgm": "Barrier Repair Moisturiser",
    "barrier repair gel moisturiser": "Barrier Repair Moisturiser",
    "barrier repair moisturiser": "Barrier Repair Moisturiser",
    "kit": "Acne Kits",
    "kits": "Acne Kits",
    "combo": "Acne Kits",
    "acne kit": "Acne Kits",
    "clear protect kit": "Acne Kits",
    "clear and protect kit": "Acne Kits",
    "emergency acne kit": "Emergency Acne Kit",
    "eak": "Emergency Acne Kit",
    "mini": "Minis",
    "minis": "Minis",
    "minis & bundles": "Minis",
    "barrier soothing cleanser": "Barrier Soothing Cleanser",
    "bsc": "Barrier Soothing Cleanser",
    "ultra smooth cleanser": "Ultra Smooth Cleanser",
    "ultra smooth daily cleanser": "Ultra Smooth Cleanser",
    "usdc": "Ultra Smooth Cleanser",
    "usc": "Ultra Smooth Cleanser",
})

BUCKETS = ["Performance", "Organic"]
CHANNELS = ["In-house", "Porcellia", "Influencer-Direct", "Influencer-Agency"]


def canonical_product(product: str) -> str:
    raw = str(product or "").strip()
    if raw in PRODUCTS:
        return raw
    lowered = raw.lower()
    if lowered in PRODUCT_ALIASES:
        return PRODUCT_ALIASES[lowered]
    if not lowered:
        return PRODUCTS[0]
    if "emergency" in lowered:
        return "Emergency Acne Kit"
    if "combo" in lowered or "kit" in lowered or " + " in lowered:
        return "Acne Kits"
    if "sunscreen" in lowered or "cpg" in lowered:
        return "Clear Protect Sunscreen"
    if "lpp" in lowered or "liquid pimple" in lowered:
        return "Liquid Pimple Patch"
    if "emc" in lowered or "melting cleanser" in lowered:
        return "Effortless Melting Cleanser"
    if "sfar" in lowered or "spot fade" in lowered or "spotfade" in lowered:
        return "SpotFade Serum"
    if "barrier repair" in lowered or "brgm" in lowered:
        return "Barrier Repair Moisturiser"
    if "barrier soothing" in lowered:
        return "Barrier Soothing Cleanser"
    if "ultra smooth" in lowered:
        return "Ultra Smooth Cleanser"
    if "mini" in lowered or "bundle" in lowered:
        return "Minis"
    if "rcf" in lowered or "rapid clear" in lowered:
        return "Rapid Clear Facewash"
    return raw


def product_code(product: str) -> str:
    label = canonical_product(product)
    return PRODUCT_META.get(label, {}).get("code", "TSS")


def product_label(product: str) -> str:
    return canonical_product(product)


def get_cohorts(product: str) -> list[str]:
    return _values(product, "cohorts")


def get_angles(product: str) -> list[str]:
    return _values(product, "angles")


def get_drivers(product: str) -> list[str]:
    return _values(product, "drivers")


def get_beliefs(product: str) -> list[str]:
    return _values(product, "beliefs")


def get_claims(product: str) -> list[str]:
    return _values(product, "claims")


FORMATS = [row.get("Name", "") for row in _rows(_universal_table("formats"))]
VIDEO_SUBTYPES = _universal_values("video_subtypes")
STATIC_SUBTYPES = _universal_values("static_subtypes")
VISUAL_HOOK_TYPES = _universal_values("visual_hook_types")
CONTENT_HOOK_TYPES = _universal_values("content_hook_types")
EMOTIONAL_ARCS = _universal_values("emotional_arcs")
FUNNEL_STAGES = [_name(row, "Code") for row in _rows(_universal_table("funnel_stages"))]
ARCHETYPES = _universal_values("creator_archetypes")
INFLUENCE_MODES = _universal_values("influence_modes")
VISUAL_TREATMENTS = _universal_values("visual_treatments")
CTA_FORMATS = _universal_values("cta_formats")
CTA_MESSAGE_TYPES = _universal_values("cta_message_types")
STATIC_MESSAGE_TYPES = _universal_values("static_message_types")

TAXONOMY_CONFIDENCE = ["High", "Medium", "Low", "Needs Review"]
AI_GENERATED_OPTIONS = ["No", "Yes", "Partially"]

# Backward-compatible aliases used by older pages and older sheet columns.
HOOK_TYPES = CONTENT_HOOK_TYPES
VISUAL_STYLES = VISUAL_TREATMENTS
CALL_TO_ACTION_STYLES = CTA_MESSAGE_TYPES
CTA_STYLES = CTA_MESSAGE_TYPES
CREATIVE_TYPES = VIDEO_SUBTYPES + STATIC_SUBTYPES
VIDEO_TYPES = set(VIDEO_SUBTYPES)

ANGLES_RCF = get_angles("Rapid Clear Facewash")
BELIEFS_RCF = get_beliefs("Rapid Clear Facewash")
COHORTS_RCF = get_cohorts("Rapid Clear Facewash")
DRIVERS_RCF = get_drivers("Rapid Clear Facewash")
CLAIMS_RCF = get_claims("Rapid Clear Facewash")

ANGLES_LPP = get_angles("Liquid Pimple Patch")
BELIEFS_LPP = get_beliefs("Liquid Pimple Patch")
COHORTS_LPP = get_cohorts("Liquid Pimple Patch")
DRIVERS_LPP = get_drivers("Liquid Pimple Patch")
CLAIMS_LPP = get_claims("Liquid Pimple Patch")

ANGLES_SFA = get_angles("SpotFade Serum")
BELIEFS_SFA = get_beliefs("SpotFade Serum")
COHORTS_SFA = get_cohorts("SpotFade Serum")
DRIVERS_SFA = get_drivers("SpotFade Serum")
CLAIMS_SFA = get_claims("SpotFade Serum")
ANGLES_SFS = ANGLES_SFA
BELIEFS_SFS = BELIEFS_SFA
COHORTS_SFS = COHORTS_SFA
DRIVERS_SFS = DRIVERS_SFA

ANGLES_EMC = get_angles("Effortless Melting Cleanser")
BELIEFS_EMC = get_beliefs("Effortless Melting Cleanser")
COHORTS_EMC = get_cohorts("Effortless Melting Cleanser")
DRIVERS_EMC = get_drivers("Effortless Melting Cleanser")
CLAIMS_EMC = get_claims("Effortless Melting Cleanser")

ANGLES_CPG = get_angles("Clear Protect Sunscreen")
BELIEFS_CPG = get_beliefs("Clear Protect Sunscreen")
COHORTS_CPG = get_cohorts("Clear Protect Sunscreen")
DRIVERS_CPG = get_drivers("Clear Protect Sunscreen")
CLAIMS_CPG = get_claims("Clear Protect Sunscreen")
ANGLES_SUNSCREEN = ANGLES_CPG
BELIEFS_SS = BELIEFS_CPG
COHORTS_SS = COHORTS_CPG
DRIVERS_SS = DRIVERS_CPG
CLAIMS_SUNSCREEN = CLAIMS_CPG

ANGLES_BRG = get_angles("Barrier Repair Moisturiser")
BELIEFS_BRG = get_beliefs("Barrier Repair Moisturiser")
COHORTS_BRG = get_cohorts("Barrier Repair Moisturiser")
DRIVERS_BRG = get_drivers("Barrier Repair Moisturiser")
CLAIMS_BRG = get_claims("Barrier Repair Moisturiser")
ANGLES_BRGM = ANGLES_BRG
BELIEFS_BRGM = BELIEFS_BRG
COHORTS_BRGM = COHORTS_BRG
DRIVERS_BRGM = DRIVERS_BRG

ANGLES_KIT = get_angles("Acne Kits")
BELIEFS_KIT = get_beliefs("Acne Kits")
COHORTS_KIT = get_cohorts("Acne Kits")
DRIVERS_KIT = get_drivers("Acne Kits")

ANGLES_EAK = get_angles("Emergency Acne Kit")
BELIEFS_EAK = get_beliefs("Emergency Acne Kit")
COHORTS_EAK = get_cohorts("Emergency Acne Kit")
DRIVERS_EAK = get_drivers("Emergency Acne Kit")

ANGLES_MIN = get_angles("Minis")
BELIEFS_MIN = get_beliefs("Minis")
COHORTS_MIN = get_cohorts("Minis")
DRIVERS_MIN = get_drivers("Minis")

ANGLES_USC = get_angles("Ultra Smooth Cleanser")
BELIEFS_USC = get_beliefs("Ultra Smooth Cleanser")
COHORTS_USC = get_cohorts("Ultra Smooth Cleanser")
DRIVERS_USC = get_drivers("Ultra Smooth Cleanser")

ANGLES_BSC = get_angles("Barrier Soothing Cleanser")
BELIEFS_BSC = get_beliefs("Barrier Soothing Cleanser")
COHORTS_BSC = get_cohorts("Barrier Soothing Cleanser")
DRIVERS_BSC = get_drivers("Barrier Soothing Cleanser")

BELIEFS = BELIEFS_RCF

DEFINITIONS = {code: define(code) for code in _index_rows()}
TAXONOMY_BY_PRODUCT = {
    product: {
        "angles": get_angles(product),
        "beliefs": get_beliefs(product),
        "cohorts": get_cohorts(product),
        "drivers": get_drivers(product),
        "claims": get_claims(product),
    }
    for product in PRODUCTS
}

VARIANT_LETTERS = ["A", "B", "C", "D"]
EXPERIMENT_VARIABLES = [
    "Marketing Angle",
    "Belief",
    "Cohort",
    "Situational Driver",
    "Static Subtype",
    "Visual Hook Type",
    "Content Hook Type",
    "Visual Treatment",
    "CTA Message Type",
]
EXPERIMENT_STATUSES = ["Planning", "Live", "In Review", "Decided", "Published", "Killed"]
NEXT_ACTIONS = ["Scale", "Iterate", "Kill", "Retest", "Needs More Data"]
SOURCE_TYPES = ["Consumer Interview", "Amazon Review", "Website Review", "Google Meet", "WhatsApp", "DM / Social Comment", "Other"]
STORY_STRENGTHS = ["1", "2", "3", "4", "5"]
