# ══════════════════════════════════════════════════════════════════════════════
# CREATIVE OS — TAXONOMY
# Every dropdown value lives here. Edit this file to update the system.
# ══════════════════════════════════════════════════════════════════════════════

# ── PRODUCTS ──────────────────────────────────────────────────────────────────
PRODUCTS = [
    "RCF",                          # Rapid Clear Face Wash
    "Clear Protect Gel Sunscreen",  # CPGS
    "Barrier Repair Gel Moisturiser",# BRGM
    "Liquid Pimple Patch",          # LPP
    "Effortless Melting Cleanser",  # EMC
    "Spot Fade Serum",              # SFS
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

# ── COHORTS ───────────────────────────────────────────────────────────────────
# RCF — 7 cohorts based on acne experience & trigger type
COHORTS_RCF = [
    "C1 — Hormonal / Painful Inflamed",       # Cystic, cyclical, tied to hormones
    "C2 — Long-term Burnt Out",               # Years of trying everything, resigned
    "C3 — Event-Driven / Panic",              # Sudden breakout before big moment
    "C4 — Barrier-Compromised / Sensitive",   # Skin that reacts to everything
    "C5 — Teen / New to Acne",                # First time dealing with acne
    "C6 — Men / Low Involvement",             # Not skincare-native, wants simple
    "C7 — Postpartum / Post-Contraceptive",   # Hormonal shift after pregnancy/stopping OCP
]

# Sunscreen — 6 cohorts based on SPF relationship & skin type
COHORTS_SUNSCREEN = [
    "SC1 — Sunscreen Avoider",       # Skips SPF entirely, multiple objections
    "SC2 — PIH Protector",           # Post-acne marks, knows SPF helps fade them
    "SC3 — Routine Completer",       # On actives, knows SPF is non-negotiable
    "SC4 — White Cast Avoider",      # Has been burned by chalky/greasy SPF before
    "SC5 — Humid Commuter",          # Outdoors, sweats, needs lightweight formula
    "SC6 — Makeup User",             # Needs SPF that works under / over makeup
]

# BRGM — borrows RCF cohorts (companion product)
COHORTS_BRGM = [
    "C1 — Hormonal / Painful Inflamed",
    "C2 — Long-term Burnt Out",
    "C4 — Barrier-Compromised / Sensitive",
]

# LPP — 6 cohorts based on usage scenario
COHORTS_LPP = [
    "LC1 — Makeup Wearer with Active Breakout",  # Treat + look presentable simultaneously
    "LC2 — Pre-Event / Panic Breakout",           # Social occasion coming up, needs fix now
    "LC3 — PIH Protector / Mark Preventer",       # Concerned about scarring post-pimple
    "LC4 — Daily Spot Manager",                   # Regular ongoing acne, consistent user
    "LC5 — Pimple Picker / Accidental Toucher",   # Needs physical barrier to stop damage
    "LC6 — Commuter / Outdoor Acne Sufferer",     # Dust, pollution exposure worsens acne
]

# EMC — 5 cohorts based on cleansing relationship
COHORTS_EMC = [
    "EC1 — Makeup Wearer, Acne-Prone",          # Daily full-face, scared of breakouts from cleansers
    "EC2 — Double Cleanse Seeker",               # Knows about oil + water cleanse, looking for right product
    "EC3 — Barrier-Compromised",                 # History of tightness / stripping from cleansers
    "EC4 — Active Treatment User",               # On RCF/actives, needs clean canvas without disruption
    "EC5 — SPF + Sebum Removal Seeker",          # Non-makeup but heavy SPF/sebum, wants thorough cleanse
]

# SFS (Spot Fade Serum) — 4 cohorts
COHORTS_SFS = [
    "SF1 — Post-Acne Mark Frustrated",           # Acne gone, marks remain, losing confidence
    "SF2 — PIH from Active Treatment",            # Actives cleared acne but left marks
    "SF3 — Long-term PIH Carrier",                # Marks from months/years ago still visible
    "SF4 — Barrier-Compromised (post-acne)",      # Sensitive skin post-treatment
]

# ── BELIEFS ───────────────────────────────────────────────────────────────────
# Beliefs are product-specific. Use get_beliefs(product) in the UI.

# RCF — 5-belief framework (frozen)
BELIEFS_RCF = [
    "B1 — Wrong Tool, Not Wrong You",    # It's not your skin's fault — BPO was always the right tool
    "B2 — Years of Nothing Working",     # Exhaustion from failed treatments, seeking something different
    "B3 — Effective ≠ Harsh",           # Clearing acne doesn't require burning your barrier
    "B4 — Early Proof, Not Just Hope",  # Small early signals (day 4) reassure before full clearing
    "B5 — One Right Step Beats Five",   # Simplicity that actually works beats complex multi-step routines
]

# Sunscreen — 4 beliefs addressing SPF resistance in acne-prone consumers
BELIEFS_SS = [
    "BS1 — SPF Can Be Acne-Safe",                       # Safe, non-comedogenic sunscreen exists for acne skin
    "BS2 — Sensory Sacrifice Is a Design Flaw, Not a Given", # Great SPF should feel invisible, not greasy
    "BS3 — Actives Without SPF Is Incomplete Treatment",  # SPF is what makes your BPO/retinol actually work
    "BS4 — Your Old SPF Was the Problem, Not SPF Itself", # The category didn't fail you — that product did
]

# LPP — 4 beliefs around protection, hiding vs healing, and format superiority
BELIEFS_LPP = [
    "BL1 — Visible Acne Doesn't Have to Be Your Reality",    # You can make acne invisible while it heals
    "BL2 — Accidental Damage Is the Silent Enemy of Healing", # Touching, dust, makeup contact slow recovery
    "BL3 — Makeup and Acne Care Are Not Mutually Exclusive",  # You don't have to choose between looking good and treating
    "BL4 — A Format That Adapts Protects Better",             # Liquid patches fit any size/shape; stickers can't
]

# EMC — 3 beliefs around cleansing and the first step
BELIEFS_EMC = [
    "BE1 — Thorough and Gentle Cleansing Are Not a Trade-Off", # One product can remove everything without stripping
    "BE2 — The Wrong First Step Undermines Everything After",   # Residue or damage from cleansing blocks treatment
    "BE3 — Your Barrier Survives Makeup Removal — With the Right Product", # Cleansing doesn't have to cost you your barrier
]

# BRGM — borrows relevant RCF beliefs + one BRGM-specific
BELIEFS_BRGM = [
    "B3 — Effective ≠ Harsh",
    "B5 — One Right Step Beats Five",
    "BB1 — Barrier Repair Is Prevention, Not Recovery",   # Fix your barrier now; stop future breakouts
    "BB2 — Your Actives Work Better on a Healthy Barrier", # BRGM makes RCF more effective, not redundant
]

# SFS — 3 beliefs around post-acne marks
BELIEFS_SFS = [
    "BF1 — Cleared Acne Is Not Solved Skin",             # Marks are the second chapter nobody prepares for
    "BF2 — Marks Fade Faster with the Right Intervention", # PIH responds to targeted treatment
    "BF3 — Your Barrier Needs to Be Ready Before You Fade", # Fading on a compromised barrier just irritates
]

# Backward-compatible alias (used in legacy code)
BELIEFS = BELIEFS_RCF

# ── MARKETING ANGLES ──────────────────────────────────────────────────────────

# RCF — 12 angles (8 original + 4 new)
ANGLES_RCF = [
    "MA-R1 — Wrong Tool (SA vs BPO mechanism)",   # Why salicylic acid failed; BPO addresses bacteria not just clog
    "MA-R2 — Calm Before Clear",                  # Calm inflammation first; clearing follows naturally
    "MA-R3 — Won't Backfire",                     # Safe for sensitive skin; won't cause purging or worsening
    "MA-R4 — Early Signal Matters",               # Day-4 early improvement as proof before full 6-week journey
    "MA-R5 — One Step, Right Problem",            # Replace the entire failed stack with one targeted product
    "MA-R6 — Barrier-First Design",               # Ceramides + gentle base; clears without destroying skin
    "MA-R7 — 4-Day Clinical Proof",               # 78% clearer in 6 weeks; clinically tested, starts at day 4
    "MA-R8 — Category Exoneration",               # Face washes can clear acne if designed to stay on for 2 min
    "MA-R9 — Overnight / Stress Triggered Acne",  # Sudden breakout from travel/stress/disruption — not a disorder
    "MA-R10 — The 2-Minute Protocol",             # How a face wash becomes a treatment: leave it on, let it work
    "MA-R11 — Won't Wreck Your Barrier",          # Ceramides + allantoin + gentle base address the harshness fear
    "MA-R12 — Alternative to Derm Procedures",    # Clinical results vs ₹8–16k in peel sessions — without escalating
]

# Sunscreen — 10 angles (6 original + 4 new)
ANGLES_SUNSCREEN = [
    "MA-S1 — Sensory Experience",                # Gel texture, no greasiness, no heaviness — feels like nothing
    "MA-S2 — No White Cast on Indian Skin",      # Specifically formulated for Indian skin tones
    "MA-S3 — Acne-Prone Safe",                   # No oil, no alcohol, no fragrance, no pore-clogging ingredients
    "MA-S4 — No Compromise",                     # Wear it without sacrificing comfort, finish, or acne safety
    "MA-S5 — Makeup Base",                       # Works as a primer/base; SPF without ruining makeup
    "MA-S6 — Efficacy / Invisible Protection",   # Protection that actually works without visual evidence
    "MA-S7 — Seasonal Need / Summer SPF",        # UV intensity + sweat + heat + acne actives = SPF non-negotiable
    "MA-S8 — Myth-Busting",                      # Your reasons to skip SPF are myths from old formulas
    "MA-S9 — Modern Formula",                    # Evolved stable filters; this is SPF designed for today's skin
    "MA-S10 — Proof of Claim",                   # Day-by-day documented UGC test: no breakouts confirmed
]

# BRGM — 5 angles
ANGLES_BRGM = [
    "MA-B1 — Barrier Support After Treatment",    # Repair damage caused by actives; make treatment sustainable
    "MA-B2 — Consistency Enabler",               # Barrier repair lets you stay on treatment without quitting
    "MA-B3 — Gentle Enough to Stay",             # Light gel formula; won't feel heavy or cause congestion
    "MA-B4 — Oil-Free Repair",                   # Moisturiser that repairs without adding oil or congestion
    "MA-B5 — Calm Skin Every Day",               # Daily habit for acne-prone skin that reacts to everything
]

# LPP — 11 angles (full Porcellia framework)
ANGLES_LPP = [
    "MA-L1 — Hide It While You Heal It",          # Acne becomes invisible visually; healing continues underneath
    "MA-L2 — Protect from Dust / Outdoor Exposure", # Environmental contact slows healing; liquid shields actively
    "MA-L3 — Makeup Friendly Patch",              # Makeup applies seamlessly over patch; no peeling or cracking
    "MA-L4 — Protects from Makeup Contact",       # Buffer between makeup and acne; healing undisturbed
    "MA-L5 — Adapts to Any Pimple Size / Shape",  # Liquid fits irregular pimples; rigid stickers can't
    "MA-L6 — India's First Liquid Pimple Patch",  # Credibility and format differentiation — never a standalone
    "MA-L7 — Pimple Picker Solution",             # Physical barrier removes the need for willpower
    "MA-L8 — Reduces Post-Acne Marks",            # Less irritation during healing = fewer marks after
    "MA-L9 — Consistent Healing",                 # Protection enables uninterrupted recovery over days
    "MA-L10 — Prevents Accidental Damage",        # Phone, sleep, clothing friction — patch removes daily risk
    "MA-L11 — Superior Adhesion vs Traditional Patch", # How long it protects vs how well it stays vs sticker
]

# EMC — 6 angles
ANGLES_EMC = [
    "MA-E1 — 100% Makeup Removal, Zero Barrier Damage", # Full removal without stripping — the core claim
    "MA-E2 — No Oil, No Alcohol, No Soap Formula",      # What's NOT in it is the proof of gentleness
    "MA-E3 — The Permanent Marker Proof",               # Demo: removes permanent marker = removes anything
    "MA-E4 — Double Cleanse in One Step",               # Replaces the oil cleanser + water cleanser combo
    "MA-E5 — Safe for Acne-Prone Skin",                 # Gentle enough for acne skin; no pore-clogging residue
    "MA-E6 — The Missing First Step for Active Users",   # Clean canvas = your RCF/actives work better
]

# SFS — 3 angles
ANGLES_SFS = [
    "MA-SF1 — Fade Marks, Not Confidence",   # Marks are the emotional scar that stays after acne is gone
    "MA-SF2 — Post-Acne Recovery",           # The chapter after clearing — marks respond to the right care
    "MA-SF3 — PIH After Treatment",          # Actives cleared acne but left hyperpigmentation — fix this
]

# ── SITUATIONAL DRIVERS ───────────────────────────────────────────────────────
# What trigger or life moment brought the consumer to the product today?

DRIVERS_RCF = [
    "None",
    "SD1 — Pre-Event Panic",           # Big day coming; sudden breakout
    "SD2 — Hormonal Cycle Flare",      # Monthly pattern; predictable but frustrating
    "SD3 — New Product Backfired",     # Tried something new; skin got worse
    "SD4 — Social Comment Trigger",    # Someone pointed out their acne
    "SD5 — Relapse After Good Skin",   # Had clear skin; now broken out again
    "SD6 — Life Transition",           # New city, job, college — skin changed
    "SD7 — Post-Active Sensitivity",   # On derm prescription; skin reacting
    "SD8 — Mirror Spiral",             # Fixation on skin; daily emotional distress
]

DRIVERS_SUNSCREEN = [
    "None",
    "SS1 — Post-Acne Clearing",           # Skin finally clearing; marks remain; SPF needed
    "SS2 — Started Active Treatment",      # Derm/RCF user; told SPF is mandatory
    "SS3 — Summer / Climate Change",       # Heat and UV increase creating urgency
    "SS4 — Breakout Suspected from SPF",   # Thinks their current SPF causes acne
    "SS5 — Morning Routine Building",      # Building a first routine; SPF is the last step
    "SS6 — Pre-Event / Vacation",          # Sun exposure coming; needs reliable protection
]

DRIVERS_LPP = [
    "None",
    "LD1 — Pre-Event / Important Day",     # Event tomorrow; pimple appeared today
    "LD2 — Active Breakout While Working", # Pimple during day; need to look presentable
    "LD3 — Post-Treatment Sensitivity",    # On actives; pimple appeared and is extra sensitive
    "LD4 — Makeup Application Day",        # Full-face makeup planned; want to treat + cover
    "LD5 — Outdoor / Commute Day",         # Long day outside; want protection from dust
]

DRIVERS_EMC = [
    "None",
    "DE1 — Heavy / Full-Coverage Makeup Day",       # Foundation, concealer, setting spray — full removal needed
    "DE2 — Starting Active Treatment Routine",       # Beginning RCF/retinol; clean canvas is now critical
    "DE3 — History of Tightness / Over-Stripping",  # Previous cleanser damaged barrier; looking for gentler option
    "DE4 — Transitioning from Wipes / Micellar",    # Knows wipes aren't enough; upgrading
]

DRIVERS_SFS = [
    "None",
    "SF1 — Post-Active Treatment Marks",   # Actives worked on acne; now marks are the problem
    "SF2 — Persistent PIH",                # Marks from months ago; haven't faded on their own
    "SF3 — Pre-Event / Photo Ready",       # Event coming; wants clearer, even skin tone
]

# ── HOOK TYPES ────────────────────────────────────────────────────────────────
# How the first 3 seconds stop the scroll — applies to both video and static.
HOOK_TYPES = [
    "H1 — Title Hook / Super (text overlay)",  # Bold text on screen in opening frames
    "H2 — Visual Hook (striking image/motion)", # Visual does the stopping — skin, product, contrast
    "H3 — Pain Statement",                      # Opens by naming the exact frustration
    "H4 — Curiosity Gap",                       # Withholds information to create a need to watch
    "H5 — Pattern Interrupt",                   # Unexpected visual or statement breaks scroll habit
    "H6 — Social Proof",                        # Opens with a result or testimonial signal
    "H7 — Objection Pre-empt",                  # Leads with the exact reason not to buy — then resolves it
    "H8 — Relatable Scenario",                  # Mirrors a specific lived moment the audience recognises
    "H9 — Authority / Credential",              # Expert, dermat, or clinical proof leads
    "H10 — Before-After Contrast",              # Visual or verbal contrast of before and after state
]

# ── EMOTIONAL ARCS ────────────────────────────────────────────────────────────
# The emotional journey a creative takes the viewer on, start → end.
EMOTIONAL_ARCS = [
    "E1 — Pain → Relief",           # Acne hurts; this relieves it
    "E2 — Confusion → Clarity",     # Didn't understand skin; now they do
    "E3 — Skepticism → Belief",     # Was doubtful; evidence changed their mind
    "E4 — Fear → Safety",           # Was scared of breakouts/products; now feels safe
    "E5 — Shame → Confidence",      # Acne made them hide; now they show up
    "E6 — Resignation → Hope",      # Had given up; a new option gives them reason to try
    "E7 — Urgency → Action",        # Time pressure or trigger creates immediate motivation
    "E8 — Unawareness → Decision",  # Didn't know this existed; now ready to buy
]

# ── FUNNEL STAGES ─────────────────────────────────────────────────────────────
# TOFU = cold audience, problem-aware. MOFU = solution-aware, comparing.
# BOFU = ready to buy, needs final push. TSOF = cold but high-intent, convert direct.
FUNNEL_STAGES = ["TOFU", "MOFU", "BOFU", "TSOF"]

# ── CREATOR ARCHETYPES ────────────────────────────────────────────────────────
# Who is delivering the message and why the audience trusts them.
ARCHETYPES = [
    "AA — Authority Anchor",         # Dermatologist, expert, scientist. Trusted for credentials.
    "LEV — Lived Experience Validator", # Consumer who endured the problem. Trusted for honesty.
    "FO — Founder-Operator",         # Brand founder. Trusted for intent and behind-the-scenes access.
    "CSA-R — Situational Relatable", # Creator who mirrors everyday acne moments. Trusted for recognition.
    "CSA-D — Discoverer",            # Creator who found something new. Trusted for curiosity and excitement.
    "N/A — No creator (AI-generated)", # No human presenter; product or text-led.
]

# ── INFLUENCE MODES ───────────────────────────────────────────────────────────
# What psychological job the creative is doing for the viewer.
INFLUENCE_MODES = [
    "M1 — Permission / De-risking",        # Makes trying feel safe; removes fear of wasting money/damaging skin
    "M2 — Reassurance / Anti-Panic",       # Calms anxiety; prevents impulse to quit or switch
    "M3 — Belief Installation / Reframe",  # Shifts a held belief (BPO > SA, face wash CAN treat acne)
    "M4 — Demonstration",                  # Shows how the product works in action; reduces usage uncertainty
    "M5 — Proof Delivery",                 # Evidence: clinical study, results, before-after, numbers
    "M6 — Objection Handling",             # Directly addresses and resolves the #1 reason not to buy
    "M7 — Acute Stabiliser",               # Meets the consumer in the panic moment; de-escalates, guides action
    "M8 — Social Proof Loop",              # Others like me used this and it worked; builds trust through volume
    "M9 — Conversion Close",              # Final push: urgency, offer, risk reversal, direct CTA
]

# ── VISUAL STYLES ─────────────────────────────────────────────────────────────
# Applies to statics, carousels, GIFs. For videos use N/A.
VISUAL_STYLES = [
    "V1 — Minimal Product Hero",     # Clean product shot; white or minimal background
    "V2 — Lifestyle Context",        # Product in real-life setting (bathroom, desk, outdoor)
    "V3 — Comparison Split",         # Side-by-side comparison (before/after, this vs that)
    "V4 — Text-Dominant",            # Copy is the hero; visual supports but text leads
    "V5 — Skin Closeup",             # Macro skin texture or transformation; no product in frame
    "V6 — Ingredient Visual",        # Ingredient highlighted (BPO crystal, ceramide, azelaic)
    "V7 — Protocol Card",            # Step-by-step usage guide in visual format
    "V8 — Data / Stats Card",        # Clinical number, percentage, or study result featured
    "V9 — Myth vs Fact",             # Myth busted visually; two-panel or call-out format
    "V10 — AI-Illustrative",         # AI-generated visual or illustration
    "V11 — Carousel Story Arc",      # Multi-frame carousel with narrative or educational arc
    "N/A — video",                   # Not applicable for video creative types
]

# ── CTA STYLES ────────────────────────────────────────────────────────────────
CALL_TO_ACTION_STYLES = [
    "C1 — AI Voiceover Slide",   # Closing slide with voiceover CTA
    "C2 — Creator Natural CTA",  # Talent speaks the CTA naturally in their own voice
    "C3 — Text-Only End Card",   # Static text card at end; no voiceover
    "C4 — Urgency CTA",          # Time-limited or stock-limited framing
    "C5 — Soft Permission CTA",  # Low-commitment ask: 'try it for 7 days'
    "C6 — Social Proof CTA",     # CTA anchored to results others got
    "C7 — Problem Restate CTA",  # Restate the pain right before the ask
    "C8 — Risk Reversal CTA",    # Money-back or try-before-you-buy framing
]
CTA_STYLES = CALL_TO_ACTION_STYLES  # alias

# ── SYSTEM FIELDS ─────────────────────────────────────────────────────────────
STATUSES = ["Draft", "Ready to Publish", "Published", "Paused", "Archived"]

VARIANT_LETTERS = ["A", "B", "C", "D"]

EXPERIMENT_VARIABLES = [
    "Hook Type", "Marketing Angle", "Visual Style", "CTA Style",
    "Emotional Arc", "Creator Archetype", "Cohort Framing", "Format", "Funnel Stage",
]

EXPERIMENT_STATUSES = ["Planning", "Live", "In Review", "Decided"]

NEXT_ACTIONS = ["Scale", "Iterate", "Kill", "Archive"]

SOURCE_TYPES = [
    "Amazon Review", "Website Review", "Google Meet",
    "WhatsApp", "DM / Social Comment", "Other",
]

STORY_STRENGTHS = [1, 2, 3, 4, 5]


# ── HELPER FUNCTIONS ──────────────────────────────────────────────────────────

def get_cohorts(product: str) -> list:
    if product == "RCF":
        return COHORTS_RCF
    if product == "Clear Protect Gel Sunscreen":
        return COHORTS_SUNSCREEN
    if product == "Liquid Pimple Patch":
        return COHORTS_LPP
    if product == "Effortless Melting Cleanser":
        return COHORTS_EMC
    if product == "Spot Fade Serum":
        return COHORTS_SFS
    return COHORTS_BRGM


def get_angles(product: str) -> list:
    if product == "RCF":
        return ANGLES_RCF
    if product == "Clear Protect Gel Sunscreen":
        return ANGLES_SUNSCREEN
    if product == "Liquid Pimple Patch":
        return ANGLES_LPP
    if product == "Effortless Melting Cleanser":
        return ANGLES_EMC
    if product == "Spot Fade Serum":
        return ANGLES_SFS
    return ANGLES_BRGM


def get_drivers(product: str) -> list:
    if product == "Clear Protect Gel Sunscreen":
        return DRIVERS_SUNSCREEN
    if product == "Liquid Pimple Patch":
        return DRIVERS_LPP
    if product == "Effortless Melting Cleanser":
        return DRIVERS_EMC
    if product == "Spot Fade Serum":
        return DRIVERS_SFS
    return DRIVERS_RCF


def get_beliefs(product: str) -> list:
    if product == "RCF":
        return BELIEFS_RCF
    if product == "Clear Protect Gel Sunscreen":
        return BELIEFS_SS
    if product == "Liquid Pimple Patch":
        return BELIEFS_LPP
    if product == "Effortless Melting Cleanser":
        return BELIEFS_EMC
    if product == "Spot Fade Serum":
        return BELIEFS_SFS
    return BELIEFS_BRGM
