PRODUCTS = [
    "RCF",
    "Clear Protect Gel Sunscreen",
    "Barrier Repair Gel Moisturiser",
]

BUCKETS = ["Performance", "Organic"]

CHANNELS = ["In-house", "Porcelia", "Influencer-Direct", "Influencer-Agency"]

CREATIVE_TYPES = [
    "Consumer Testimonial",
    "Brand-Led",
    "Founder-Led",
    "Skit",
    "Event Coverage",
    "Static",
    "Carousel",
    "GIF",
    "AI-Video",
    "AI-Static",
]

VIDEO_TYPES = {
    "Consumer Testimonial", "Brand-Led", "Founder-Led",
    "Skit", "Event Coverage", "AI-Video",
}

COHORTS_RCF = [
    "C1 — Hormonal / Painful Inflamed",
    "C2 — Long-term Burnt Out",
    "C3 — Event-Driven / Panic",
    "C4 — Barrier-Compromised / Sensitive",
    "C5 — Teen / New to Acne",
    "C6 — Men / Low Involvement",
    "C7 — Postpartum / Post-Contraceptive",
]

COHORTS_SUNSCREEN = [
    "SC1 — Sunscreen Avoider",
    "SC2 — PIH Protector",
    "SC3 — Routine Completer",
    "SC4 — White Cast Avoider",
    "SC5 — Humid Commuter",
    "SC6 — Makeup User",
]

COHORTS_BRGM = [
    "C1 — Hormonal / Painful Inflamed",
    "C2 — Long-term Burnt Out",
    "C4 — Barrier-Compromised / Sensitive",
]

BELIEFS = [
    "B1 — Wrong Tool, Not Wrong You",
    "B2 — Years of Nothing Working",
    "B3 — Effective ≠ Harsh",
    "B4 — Early Proof, Not Just Hope",
    "B5 — One Right Step Beats Five",
]

ANGLES_RCF = [
    "MA-R1 — Wrong Tool (SA vs BPO mechanism)",
    "MA-R2 — Calm Before Clear",
    "MA-R3 — Won't Backfire",
    "MA-R4 — Early Signal Matters",
    "MA-R5 — One Step, Right Problem",
    "MA-R6 — Barrier-First Design",
    "MA-R7 — 4-Day Clinical Proof",
    "MA-R8 — Category Exoneration",
]

ANGLES_SUNSCREEN = [
    "MA-S1 — Sensory Experience",
    "MA-S2 — No White Cast on Indian Skin",
    "MA-S3 — Acne-Prone Safe",
    "MA-S4 — No Compromise",
    "MA-S5 — Makeup Base",
    "MA-S6 — Efficacy / Invisible Protection",
]

ANGLES_BRGM = [
    "MA-B1 — Barrier Support After Treatment",
    "MA-B2 — Consistency Enabler",
    "MA-B3 — Gentle Enough to Stay",
]

DRIVERS_RCF = [
    "None",
    "SD1 — Pre-Event Panic",
    "SD2 — Hormonal Cycle Flare",
    "SD3 — New Product Backfired",
    "SD4 — Social Comment Trigger",
    "SD5 — Relapse After Good Skin",
    "SD6 — Life Transition",
    "SD7 — Post-Active Sensitivity",
    "SD8 — Mirror Spiral",
]

DRIVERS_SUNSCREEN = [
    "None",
    "SS1 — Post-Acne Clearing",
    "SS2 — Started Active Treatment",
    "SS3 — Summer / Climate Change",
    "SS4 — Breakout Suspected from SPF",
    "SS5 — Morning Routine Building",
    "SS6 — Pre-Event / Vacation",
]

HOOK_TYPES = [
    "H1 — Title Hook / Super (text overlay)",
    "H2 — Visual Hook (striking image/motion)",
    "H3 — Pain Statement",
    "H4 — Curiosity Gap",
    "H5 — Pattern Interrupt",
    "H6 — Social Proof",
    "H7 — Objection Pre-empt",
    "H8 — Relatable Scenario",
    "H9 — Authority / Credential",
    "H10 — Before-After Contrast",
]

EMOTIONAL_ARCS = [
    "E1 — Pain → Relief",
    "E2 — Confusion → Clarity",
    "E3 — Skepticism → Belief",
    "E4 — Fear → Safety",
    "E5 — Shame → Confidence",
    "E6 — Resignation → Hope",
    "E7 — Urgency → Action",
    "E8 — Unawareness → Decision",
]

FUNNEL_STAGES = ["TOFU", "MOFU", "BOFU", "TSOF"]

ARCHETYPES = [
    "AA — Authority Anchor",
    "LEV — Lived Experience Validator",
    "FO — Founder-Operator",
    "CSA-R — Situational Relatable",
    "CSA-D — Discoverer",
    "N/A — No creator (AI-generated)",
]

INFLUENCE_MODES = [
    "M1 — Permission / De-risking",
    "M2 — Reassurance / Anti-Panic",
    "M3 — Belief Installation / Reframe",
    "M4 — Demonstration",
    "M5 — Proof Delivery",
    "M6 — Objection Handling",
    "M7 — Acute Stabiliser",
    "M8 — Social Proof Loop",
    "M9 — Conversion Close",
]

VISUAL_STYLES = [
    "V1 — Minimal Product Hero",
    "V2 — Lifestyle Context",
    "V3 — Comparison Split",
    "V4 — Text-Dominant",
    "V5 — Skin Closeup",
    "V6 — Ingredient Visual",
    "V7 — Protocol Card",
    "V8 — Data / Stats Card",
    "V9 — Myth vs Fact",
    "V10 — AI-Illustrative",
    "V11 — Carousel Story Arc",
]

CTA_STYLES = [
    "C1 — AI Voiceover Slide",
    "C2 — Creator Natural CTA",
    "C3 — Text-Only End Card",
    "C4 — Urgency CTA",
    "C5 — Soft Permission CTA",
    "C6 — Social Proof CTA",
    "C7 — Problem Restate CTA",
    "C8 — Risk Reversal CTA",
]

STATUSES = ["Draft", "Ready to Publish", "Published", "Paused", "Archived"]

VARIANT_LETTERS = ["A", "B", "C", "D"]

EXPERIMENT_VARIABLES = [
    "Hook Type",
    "Marketing Angle",
    "Visual Style",
    "CTA Style",
    "Emotional Arc",
    "Creator Archetype",
    "Cohort Framing",
    "Format",
    "Funnel Stage",
]

EXPERIMENT_STATUSES = ["Planning", "Live", "In Review", "Decided"]

NEXT_ACTIONS = ["Scale", "Iterate", "Kill", "Archive"]

SOURCE_TYPES = [
    "Amazon Review",
    "Website Review",
    "Google Meet",
    "WhatsApp",
    "DM / Social Comment",
    "Other",
]

STORY_STRENGTHS = [1, 2, 3, 4, 5]


def get_cohorts(product: str) -> list:
    if product == "RCF":
        return COHORTS_RCF
    if product == "Clear Protect Gel Sunscreen":
        return COHORTS_SUNSCREEN
    return COHORTS_BRGM


def get_angles(product: str) -> list:
    if product == "RCF":
        return ANGLES_RCF
    if product == "Clear Protect Gel Sunscreen":
        return ANGLES_SUNSCREEN
    return ANGLES_BRGM


def get_drivers(product: str) -> list:
    if product == "Clear Protect Gel Sunscreen":
        return DRIVERS_SUNSCREEN
    return DRIVERS_RCF
