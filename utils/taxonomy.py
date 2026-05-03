"""Creative OS approved taxonomy.

Source of truth: Creative_OS_Approved_Taxonomy_Handover.md, v1.0.
Keep active dropdown labels stable as "CODE - Label"; legacy helpers still
accept older labels already present in Google Sheets.
"""

# Products --------------------------------------------------------------------

PRODUCTS = [
    "RCF",
    "Liquid Pimple Patch",
    "SpotFade Serum",
    "Effortless Melting Cleanser",
    "Clear Protect Sunscreen",
    "Barrier Repair Moisturiser",
    "Acne Kits",
    "Emergency Acne Kit",
    "Minis",
    "Barrier Soothing Cleanser",
    "Ultra Smooth Cleanser",
]

PRODUCT_META = {
    "RCF": {"code": "RCF", "name": "Rapid Clear Facewash", "priority": "P1", "confidence": "Strong"},
    "Liquid Pimple Patch": {"code": "LPP", "name": "Liquid Pimple Patch", "priority": "P1", "confidence": "Medium-Strong"},
    "SpotFade Serum": {"code": "SFARS", "name": "SpotFade Advanced Repair Serum", "priority": "P1", "confidence": "Medium"},
    "Effortless Melting Cleanser": {"code": "EMC", "name": "Effortless Melting Cleanser", "priority": "P1", "confidence": "Medium"},
    "Clear Protect Sunscreen": {"code": "CPG", "name": "Clear Protect Gel Sunscreen", "priority": "P2", "confidence": "Strong"},
    "Barrier Repair Moisturiser": {"code": "BRGM", "name": "Barrier Repair Gel Moisturiser", "priority": "P2", "confidence": "Medium"},
    "Acne Kits": {"code": "KIT", "name": "Kits / Combo / Clear & Protect", "priority": "P2", "confidence": "Medium"},
    "Emergency Acne Kit": {"code": "EAK", "name": "Emergency Acne Kit", "priority": "P3", "confidence": "Medium"},
    "Minis": {"code": "MIN", "name": "Minis & Bundles", "priority": "P3", "confidence": "Low"},
    "Barrier Soothing Cleanser": {"code": "BSC", "name": "Barrier Soothing Cleanser", "priority": "P3", "confidence": "Low-Medium"},
    "Ultra Smooth Cleanser": {"code": "USC", "name": "Ultra Smooth Daily Cleanser", "priority": "P3", "confidence": "Low"},
}

PRODUCT_ALIASES = {
    "rapid clear facewash": "RCF",
    "rapid clear face wash": "RCF",
    "rcf": "RCF",
    "liquid pimple patch": "Liquid Pimple Patch",
    "lpp": "Liquid Pimple Patch",
    "spot fade serum": "SpotFade Serum",
    "spotfade serum": "SpotFade Serum",
    "spotfade advanced repair serum": "SpotFade Serum",
    "sfars": "SpotFade Serum",
    "sfs": "SpotFade Serum",
    "effortless melting cleanser": "Effortless Melting Cleanser",
    "emc": "Effortless Melting Cleanser",
    "clear protect gel sunscreen": "Clear Protect Sunscreen",
    "clear protect sunscreen": "Clear Protect Sunscreen",
    "sunscreen": "Clear Protect Sunscreen",
    "cpg": "Clear Protect Sunscreen",
    "cpgs": "Clear Protect Sunscreen",
    "barrier repair gel moisturiser": "Barrier Repair Moisturiser",
    "barrier repair moisturiser": "Barrier Repair Moisturiser",
    "brgm": "Barrier Repair Moisturiser",
    "acne kits": "Acne Kits",
    "kits": "Acne Kits",
    "kit": "Acne Kits",
    "clear and repair combo": "Acne Kits",
    "clear + repair combo": "Acne Kits",
    "acne care combo kit": "Acne Kits",
    "emergency acne kit": "Emergency Acne Kit",
    "eak": "Emergency Acne Kit",
    "minis": "Minis",
    "minis & bundles": "Minis",
    "minis and bundles": "Minis",
    "barrier soothing cleanser": "Barrier Soothing Cleanser",
    "bsc": "Barrier Soothing Cleanser",
    "ultra smooth daily cleanser": "Ultra Smooth Cleanser",
    "ultra smooth cleanser": "Ultra Smooth Cleanser",
    "usdc": "Ultra Smooth Cleanser",
    "usc": "Ultra Smooth Cleanser",
}

BUCKETS = ["Performance", "Organic"]
CHANNELS = ["In-house", "Porcellia", "Influencer-Direct", "Influencer-Agency"]


def item(code: str, label: str) -> str:
    return f"{code} - {label}"


# Universal cuts --------------------------------------------------------------

FORMATS = ["Video", "Static"]

VIDEO_SUBTYPES = [
    item("VS1", "Consumer Testimonial"),
    item("VS2", "Founder-Led"),
    item("VS3", "Expert / Dermat"),
    item("VS4", "Creator / UGC"),
    item("VS5", "Product Demo"),
    item("VS6", "Skit / Scenario"),
    item("VS7", "AI Video"),
    item("VS8", "Event Coverage"),
]

STATIC_SUBTYPES = [
    item("SS1", "Single Image"),
    item("SS2", "Carousel"),
    item("SS3", "Before / After"),
    item("SS4", "Proof Screenshot"),
    item("SS5", "Comparison"),
    item("SS6", "Meme / Topical"),
    item("SS7", "Educational / Data"),
    item("SS8", "Ingredient Focus"),
    item("SS9", "Offer / Promotional"),
]

VISUAL_HOOK_TYPES = [
    item("VH1", "Skin Visual"),
    item("VH2", "Before / After"),
    item("VH3", "Product In Use"),
    item("VH4", "Text / Super Dominant"),
    item("VH5", "Screenshot / Proof on Screen"),
    item("VH6", "Demo Object"),
    item("VH7", "Relatable Scene"),
    item("VH8", "Face to Camera"),
    item("VH9", "Pattern Interrupt"),
]

CONTENT_HOOK_TYPES = [
    item("CH1", "Pain Named"),
    item("CH2", "Functional Payoff Open"),
    item("CH3", "Objection First"),
    item("CH4", "Curiosity Gap / Secret"),
    item("CH5", "Myth / Comparison / Reframe"),
    item("CH6", "Relatable Scenario"),
    item("CH7", "Authority / Credibility"),
    item("CH8", "Social Proof"),
    item("CH9", "Urgency / Panic"),
    item("CH10", "Dark Humour / Irony"),
    item("CH11", "Emotional Payoff Open"),
    item("CH12", "Price / Value Lead"),
    item("CH13", "Negative Trigger / Challenge"),
]

EMOTIONAL_ARCS = [
    item("EA1", "Pain -> Relief"),
    item("EA2", "Confusion -> Clarity"),
    item("EA3", "Skepticism -> Belief"),
    item("EA4", "Fear -> Safety"),
    item("EA5", "Shame -> Confidence"),
    item("EA6", "Resignation -> Hope"),
    item("EA7", "Discovery -> Decision"),
    item("EA8", "Dark Humour -> Vindication"),
    item("EA9", "Loyalty -> Advocacy"),
]

FUNNEL_STAGES = ["TOFU", "MOFU", "BOFU", "CONV"]
LEGACY_FUNNEL_STAGES = ["TSOF"]

ARCHETYPES = [
    item("AA", "Authority Anchor"),
    item("LEV", "Lived Experience Validator"),
    item("FO", "Founder-Operator"),
    item("IC", "Influencer / Creator"),
    item("CSA", "Situational Relatable"),
    item("BRAND", "Brand / No Creator"),
]

INFLUENCE_MODES = [
    item("M1", "Permission / De-risking"),
    item("M2", "Reassurance / Anti-Panic"),
    item("M3", "Belief Reframe"),
    item("M4", "Demonstration"),
    item("M5", "Proof Delivery"),
    item("M6", "Objection Handling"),
    item("M7", "Acute Stabiliser"),
    item("M8", "Social Proof Loop"),
    item("M9", "Conversion Close"),
    item("M10", "Cost / Value Contrast"),
    item("M11", "Dark Humour / Irony"),
]

VISUAL_TREATMENTS = [
    item("VT1", "Skin-Led"),
    item("VT2", "Product-Led"),
    item("VT3", "Text-Led"),
    item("VT4", "Lifestyle / Scene"),
    item("VT5", "Data / Proof Visual"),
    item("VT6", "Illustration / AI"),
]

CTA_FORMATS = [
    item("CF1", "AI Voiceover Slide"),
    item("CF2", "Creator Spoken"),
    item("CF3", "Text End Card"),
    item("CF4", "No Explicit CTA"),
]

CTA_MESSAGE_TYPES = [
    item("CM1", "Direct Buy"),
    item("CM2", "Soft Permission"),
    item("CM3", "Social Proof Close"),
    item("CM4", "Problem Restate"),
    item("CM5", "Viewer Direct Address"),
    item("CM6", "Urgency"),
    item("CM7", "Risk Reversal"),
    item("CM8", "Offer / Deal"),
]

STATIC_MESSAGE_TYPES = [
    item("SPM1", "Offer / Promotional"),
    item("SPM2", "Price / Value"),
    item("SPM3", "Clinical / Data Proof"),
    item("SPM4", "Consumer / Social Proof"),
    item("SPM5", "Product Education"),
    item("SPM6", "Problem / Pain"),
    item("SPM7", "Differentiation"),
]

TAXONOMY_CONFIDENCE = ["High", "Medium", "Low", "Needs Review"]
AI_GENERATED_OPTIONS = ["No", "Yes", "Partially"]

# Legacy aliases still imported by older pages.
HOOK_TYPES = CONTENT_HOOK_TYPES
VISUAL_STYLES = VISUAL_TREATMENTS + ["N/A - video"]
CALL_TO_ACTION_STYLES = CTA_MESSAGE_TYPES
CTA_STYLES = CTA_MESSAGE_TYPES
CREATIVE_TYPES = VIDEO_SUBTYPES + STATIC_SUBTYPES
VIDEO_TYPES = set(VIDEO_SUBTYPES)


# Product-specific taxonomy ---------------------------------------------------

ANGLES_RCF = [
    item("RCF-MA-01", "SA, Dermats, Procedures - Didn't Work"),
    item("RCF-MA-02", "Clears Acne. Won't Destroy Your Skin."),
    item("RCF-MA-03", "Early Proof, Not Just Hope"),
    item("RCF-MA-04", "India's First Micronised BPO"),
    item("RCF-MA-05", "Clinically Proven on Indian Skin"),
    item("RCF-MA-06", "Face Wash Can Treat Acne"),
    item("RCF-MA-07", "Hormonal / Cycle / Stress-Triggered Acne"),
    item("RCF-MA-08", "The 2-Minute Protocol"),
    item("RCF-MA-09", "How to Use It Without Wrecking Your Skin"),
    item("RCF-MA-10", "Ceramides, Allantoin, Panthenol, Cica"),
]

BELIEFS_RCF = [
    item("RCF-B-01", "I was using the wrong tool - my skin isn't the problem"),
    item("RCF-B-02", "My acne treatment doesn't have to destroy my skin to work"),
    item("RCF-B-03", "If my skin is calming down early, it's working"),
    item("RCF-B-04", "One right product beats five wrong ones"),
    item("RCF-B-05", "A face wash can treat my acne - if it's designed to stay on"),
    item("RCF-B-06", "My hormonal acne is manageable"),
    item("RCF-B-07", "Initial tingling or dryness doesn't mean I should stop"),
]

COHORTS_RCF = [
    item("RCF-C01", "Hormonal / Painful Inflamed"),
    item("RCF-C02", "Long-term Burnt Out"),
    item("RCF-C03", "Event-Driven / Panic"),
    item("RCF-C04", "Barrier-Compromised / Sensitive"),
    item("RCF-C05", "Teen / New to Acne"),
    item("RCF-C06", "Men / Low Involvement"),
    item("RCF-C07", "Postpartum / Post-Contraceptive"),
    item("RCF-C08", "Advice-Fatigued / Culturally Over-Advised"),
    item("RCF-C09", "Accidental Discoverer"),
]

DRIVERS_RCF = [
    "None",
    item("SD-RCF-01", "Pre-Event Panic"),
    item("SD-RCF-02", "Hormonal Cycle Flare"),
    item("SD-RCF-03", "New Product Backfired"),
    item("SD-RCF-04", "Social Comment Trigger"),
    item("SD-RCF-05", "Relapse After Good Skin"),
    item("SD-RCF-06", "Life Transition"),
    item("SD-RCF-07", "Post-Active Sensitivity"),
    item("SD-RCF-08", "Mirror Spiral"),
    item("SD-RCF-09", "Oral Medication Stopped"),
    item("SD-RCF-10", "Saw Someone Else's Result"),
]

CLAIMS_RCF = [
    item("RCF-CLM-01", "Visible reduction in acne in just 4 days"),
    item("RCF-CLM-02", "Calms Active Acne in 4 days"),
    item("RCF-CLM-03", "Kills 93% acne-causing bacteria in 1 minute"),
    item("RCF-CLM-04", "Prevents breakouts for 78% clearer skin in 6 weeks"),
    item("RCF-CLM-05", "47% reduction in active acne in 1 week"),
    item("RCF-CLM-06", "India's first face wash with Patented Micronised BPO"),
]

ANGLES_LPP = [
    item("LPP-MA-01", "Hide It While You Heal It"),
    item("LPP-MA-02", "Shields From Outside"),
    item("LPP-MA-03", "Works Under Makeup"),
    item("LPP-MA-04", "Fits Any Pimple"),
    item("LPP-MA-05", "Stops Accidental Damage"),
    item("LPP-MA-06", "Fewer Marks After"),
]

BELIEFS_LPP = [
    item("LPP-B-01", "I can treat my pimple and still show up"),
    item("LPP-B-02", "Accidental contact keeps making my pimple worse"),
    item("LPP-B-03", "A liquid film fits my pimple. A sticker can't."),
    item("LPP-B-04", "How I heal determines what I am left with after"),
    item("LPP-B-05", "Liquid patch is better value than sticker patches"),
    item("LPP-B-06", "My patch can be invisible under makeup"),
]

COHORTS_LPP = [
    item("LPP-C01", "Makeup Wearer With Active Breakout"),
    item("LPP-C02", "Pre-Event Panic"),
    item("LPP-C03", "PIH Protector / Mark Preventer"),
    item("LPP-C04", "Consistent Spot User"),
    item("LPP-C05", "Accidental Toucher"),
    item("LPP-C06", "Outdoor / Commuter"),
]

DRIVERS_LPP = [
    "None",
    item("SD-LPP-01", "Pre-Event / Important Day"),
    item("SD-LPP-02", "Active Breakout While Working"),
    item("SD-LPP-03", "Post-Treatment Sensitivity"),
    item("SD-LPP-04", "Makeup Application Day"),
    item("SD-LPP-05", "Outdoor / Commute Day"),
    item("SD-LPP-06", "Night Picker Risk"),
]

CLAIMS_LPP = [
    item("LPP-CLM-01", "India's first Liquid Pimple Patch"),
    item("LPP-CLM-02", "300+ patches per tube"),
    item("LPP-CLM-03", "Clinically tested"),
]

ANGLES_SFA = [
    item("SFA-MA-01", "Cleared Acne Isn't Solved Skin"),
    item("SFA-MA-02", "PIH From Treatment"),
    item("SFA-MA-03", "Black -> Brown -> Pink -> Gone"),
]

BELIEFS_SFA = [
    item("SFA-B-01", "Marks are a separate battle after acne clearing"),
    item("SFA-B-02", "PIH marks are not permanent with the right treatment"),
]

COHORTS_SFA = [
    item("SFA-C01", "Post-Acne Mark Frustrated"),
    item("SFA-C02", "Long-term PIH Carrier"),
    item("SFA-C03", "Marks-Led Social Avoider"),
]

DRIVERS_SFA = [
    "None",
    item("SD-SFA-01", "Post-Acne Marks Visible"),
    item("SD-SFA-02", "Persistent PIH Not Moving"),
    item("SD-SFA-03", "Photo or Event Trigger"),
    item("SD-SFA-04", "Filter Dependency Noticed"),
    item("SD-SFA-05", "Someone Commented on Marks"),
]

CLAIMS_SFA = [
    item("SFA-CLM-01", "India's first serum with 8% Solubilized Azelaic Acid"),
    item("SFA-CLM-02", "4% Niacinamide"),
    item("SFA-CLM-03", "Clinically designed to reduce post-acne pigmentation and redness"),
]

ANGLES_EMC = [
    item("EMC-MA-01", "Kajal, SPF, Makeup - One Step, Everything Off"),
    item("EMC-MA-02", "Safe for Acne-Prone Skin"),
    item("EMC-MA-03", "Double Cleanse - Without the Double Step"),
    item("EMC-MA-04", "Too Tired to Make It Complicated"),
    item("EMC-MA-05", "Cleanse Right, Everything After Works Better"),
]

BELIEFS_EMC = [
    item("EMC-B-01", "I can remove everything without irritating my skin"),
    item("EMC-B-02", "What I don't remove properly affects what works next"),
    item("EMC-B-03", "Removing makeup doesn't have to be a ritual I dread"),
]

COHORTS_EMC = [
    item("EMC-C01", "Makeup Wearer, Acne-Prone"),
    item("EMC-C02", "Double Cleanse Seeker"),
    item("EMC-C03", "Barrier-Compromised Cleanser User"),
    item("EMC-C04", "Active Treatment User"),
    item("EMC-C05", "SPF + Sebum Buildup"),
]

DRIVERS_EMC = [
    "None",
    item("SD-EMC-01", "Heavy / Full-Coverage Makeup Day"),
    item("SD-EMC-02", "Starting Active Treatment Routine"),
    item("SD-EMC-03", "History of Tightness / Over-Stripping"),
    item("SD-EMC-04", "Transitioning From Wipes / Micellar"),
    item("SD-EMC-05", "End-of-Day Exhaustion"),
]

CLAIMS_EMC = [
    item("EMC-CLM-01", "Removes kajal, SPF, and waterproof makeup"),
    item("EMC-CLM-02", "Non-comedogenic, oil-free formula"),
    item("EMC-CLM-03", "Dermatologist tested"),
]

ANGLES_CPG = [
    item("CPG-MA-01", "Won't Break You Out"),
    item("CPG-MA-02", "Zero White Cast"),
    item("CPG-MA-03", "Feels Like Nothing"),
    item("CPG-MA-04", "Real SPF, Not Just a Feeling"),
    item("CPG-MA-05", "Works Under Makeup"),
    item("CPG-MA-06", "Protection Without the Compromise"),
]

BELIEFS_CPG = [
    item("CPG-B-01", "Old-gen filters broke me out, not SPF itself"),
    item("CPG-B-02", "This sunscreen was made for Indian skin tones"),
    item("CPG-B-03", "A weightless SPF can still be full protection"),
    item("CPG-B-04", "Protection and comfort can coexist"),
]

COHORTS_CPG = [
    item("CPG-C01", "Acne-Prone SPF Avoider"),
    item("CPG-C02", "Sensitive Skin SPF Avoider"),
    item("CPG-C03", "White Cast Sufferer"),
    item("CPG-C04", "Texture Hater"),
    item("CPG-C05", "Makeup-First SPF User"),
]

DRIVERS_CPG = [
    "None",
    item("SD-CPG-01", "Starting Acne Treatment"),
    item("SD-CPG-02", "Summer / Heat Season"),
    item("SD-CPG-03", "Last Sunscreen Broke Them Out"),
    item("SD-CPG-04", "White Cast Discovery"),
    item("SD-CPG-05", "Reapplication Reminder"),
    item("SD-CPG-06", "Post-Tan Regret"),
]

CLAIMS_CPG = [
    item("CPG-CLM-01", "SPF 57.65 in-vitro tested"),
    item("CPG-CLM-02", "PA++++"),
    item("CPG-CLM-03", "Dermatologically tested on sensitive skin - non-irritant"),
    item("CPG-CLM-04", "Non-comedogenic"),
    item("CPG-CLM-05", "6 microencapsulated UV filters"),
]

ANGLES_BRG = [
    item("BRG-MA-01", "Make Your Acne Treatment Work Better"),
    item("BRG-MA-02", "Stop the Acne Cycle"),
    item("BRG-MA-03", "Calm Skin, Every Day"),
    item("BRG-MA-04", "Oil-Free Repair"),
    item("BRG-MA-05", "Why You Need to Switch Moisturisers"),
    item("BRG-MA-06", "1% Ceramide Complex, Cica, Niacinamide"),
]

BELIEFS_BRG = [
    item("BRG-B-01", "Acne treatment works better when my barrier is healthy"),
    item("BRG-B-02", "Barrier damage is part of why acne keeps returning"),
    item("BRG-B-03", "A moisturiser can repair without breaking me out"),
    item("BRG-B-04", "My current moisturiser hydrates but doesn't repair"),
]

COHORTS_BRG = [
    item("BRG-C01", "Active Treatment User"),
    item("BRG-C02", "Post-Treatment Rebuilder"),
    item("BRG-C03", "Moisturiser Avoider"),
    item("BRG-C04", "Chronic Rebound Acne"),
]

DRIVERS_BRG = [
    "None",
    item("SD-BRG-01", "Skin Reacting to RCF or Actives"),
    item("SD-BRG-02", "Post-Treatment Damage"),
    item("SD-BRG-03", "Dry and Flaky Despite Everything"),
    item("SD-BRG-04", "Acne Cleared, Skin Still Rough"),
    item("SD-BRG-05", "Breaking Out After Adding a Product"),
]

CLAIMS_BRG = [
    item("BRG-CLM-01", "1% Ceramide Complex"),
    item("BRG-CLM-02", "S.M.A.R.T. Delivery System"),
    item("BRG-CLM-03", "Reduces skin damage by 70% in 4 weeks"),
    item("BRG-CLM-04", "Non-comedogenic, fragrance-free"),
]

ANGLES_KIT = [
    item("KIT-MA-01", "No Confusion About What to Pair"),
    item("KIT-MA-02", "Better Results Together"),
    item("KIT-MA-03", "Value Routine"),
    item("KIT-MA-04", "The Complete Acne System"),
]

BELIEFS_KIT = [
    item("KIT-B-01", "Designed-together products beat self-assembled routines"),
    item("KIT-B-02", "I don't need to research routine compatibility"),
]

COHORTS_KIT = [
    item("KIT-C01", "Routine Builder"),
    item("KIT-C02", "Upgrader / System Buyer"),
    item("KIT-C03", "Lazy Researcher"),
]

DRIVERS_KIT = [
    "None",
    item("SD-KIT-01", "Starting From Scratch"),
    item("SD-KIT-02", "Ready to Upgrade"),
    item("SD-KIT-03", "Gifting Occasion"),
]

ANGLES_EAK = [
    item("EAK-MA-01", "Treat It and Hide It"),
    item("EAK-MA-02", "Always-Ready Backup"),
]

BELIEFS_EAK = BELIEFS_KIT
COHORTS_EAK = COHORTS_KIT
DRIVERS_EAK = DRIVERS_KIT

ANGLES_MIN = [
    item("MIN-MA-01", "Try Before You Commit"),
    item("MIN-MA-02", "Travel Ready"),
    item("MIN-MA-03", "Gateway to the Routine"),
]

BELIEFS_MIN = [
    item("MIN-B-01", "I can test this before committing to the full size"),
]

COHORTS_MIN = [
    item("MIN-C01", "Skeptical First-Timer"),
    item("MIN-C02", "Traveller"),
]

DRIVERS_MIN = [
    "None",
    item("SD-MIN-01", "First Touch With TSS"),
    item("SD-MIN-02", "Travelling"),
    item("SD-MIN-03", "Wants to Try Before Full Kit"),
]

ANGLES_USC = [
    item("USC-MA-01", "Smoother Skin From the First Wash"),
    item("USC-MA-02", "Clears Without Stripping"),
    item("USC-MA-03", "For Blackheads and Clogged Pores"),
]

BELIEFS_USC = [
    item("USC-B-01", "My rough texture and blackheads can change"),
    item("USC-B-02", "I can clear pores daily without irritation"),
]

COHORTS_USC = [
    item("USC-C01", "Texture and Blackhead Sufferer"),
    item("USC-C02", "Post-Acne Texture Carrier"),
    item("USC-C03", "Oily / Congested"),
]

DRIVERS_USC = [
    "None",
    item("SD-USC-01", "Blackheads Noticed or Worsened"),
    item("SD-USC-02", "Skin Texture Frustration"),
    item("SD-USC-03", "Post-Acne Texture Left Behind"),
    item("SD-USC-04", "Oiliness Getting Worse"),
]

ANGLES_BSC = [
    item("BSC-MA-01", "Clean Without the Tightness"),
    item("BSC-MA-02", "The Safe Daily Reset"),
    item("BSC-MA-03", "Gentle Enough for Every Day"),
    item("BSC-MA-04", "Safe for Sensitive Skin"),
]

BELIEFS_BSC = [
    item("BSC-B-01", "My skin can feel clean and comfortable after washing"),
]

COHORTS_BSC = [
    item("BSC-C01", "Active Treatment Companion Seeker"),
    item("BSC-C02", "Post-Inflammation Soother"),
    item("BSC-C03", "CeraVe Upgrader"),
]

DRIVERS_BSC = [
    "None",
    item("SD-BSC-01", "Current Cleanser Causing Tightness"),
    item("SD-BSC-02", "Actives Made Skin More Sensitive"),
    item("SD-BSC-03", "Switching From CeraVe or Similar"),
]

# Legacy product aliases used by old code/tests.
ANGLES_SUNSCREEN = ANGLES_CPG
BELIEFS_SS = BELIEFS_CPG
COHORTS_SUNSCREEN = COHORTS_CPG
DRIVERS_SUNSCREEN = DRIVERS_CPG
CLAIMS_SUNSCREEN = CLAIMS_CPG

ANGLES_BRGM = ANGLES_BRG
BELIEFS_BRGM = BELIEFS_BRG
COHORTS_BRGM = COHORTS_BRG
DRIVERS_BRGM = DRIVERS_BRG

ANGLES_SFS = ANGLES_SFA
BELIEFS_SFS = BELIEFS_SFA
COHORTS_SFS = COHORTS_SFA
DRIVERS_SFS = DRIVERS_SFA

BELIEFS = BELIEFS_RCF


# Definitions -----------------------------------------------------------------

DEFINITIONS = {
    # Universal
    "FMT-V": "Any moving creative: testimonial, demo, skit, founder, AI video, or event footage.",
    "FMT-S": "Any single frame or swipeable still sequence: image, carousel, proof card, or infographic.",
    "VS1": "Real consumer telling a lived product or problem story.",
    "VS2": "Founder speaking about intent, accountability, product rationale, or behind-the-scenes thinking.",
    "VS3": "Credentialed dermatologist, scientist, or expert explaining proof or mechanism.",
    "VS4": "Creator or influencer content built as routine, POV, or UGC-style usage.",
    "VS5": "Product-first application, texture, formula, or use demonstration.",
    "VS6": "Scripted or acted character-led scene.",
    "VS7": "AI-generated or AI-heavy moving creative.",
    "VS8": "Real-world event, launch, or behind-the-scenes footage.",
    "SS1": "One hero frame, including product, skin, headline-led, or product-only shots.",
    "SS2": "Multi-frame swipeable sequence.",
    "SS3": "Visual contrast of two skin or routine states.",
    "SS4": "Review, DM, clinical certificate, or testimonial screenshot used as proof.",
    "SS5": "Versus competitor, old routine, category myth, or wrong tool.",
    "SS6": "Cultural reference or trending format adapted to TSS messaging.",
    "SS7": "Teaches a concept, protocol, ingredient, or clinical/data proof point.",
    "SS8": "Single ingredient or formula spotlight.",
    "SS9": "Price deal, bundle discount, limited offer, or promotional static.",
    "VH1": "The first visual is acne, marks, texture, redness, or a skin close-up.",
    "VH2": "The first visual is a before/after or split contrast.",
    "VH3": "The first visual shows product dispensed, applied, or washed off.",
    "VH4": "Bold text overlay is what registers before anything else.",
    "VH5": "Review, DM, clinical result, or screenshot appears immediately.",
    "VH6": "Unusual prop or demo object creates immediate curiosity.",
    "VH7": "Recognisable setting such as mirror, makeup desk, gym, commute, or bedtime.",
    "VH8": "A person faces the camera and speaks directly to the viewer.",
    "VH9": "Unexpected framing, meme, hard cut, or visual pattern break.",
    "CH1": "Opens by naming the exact frustration or problem.",
    "CH2": "Opens with a tangible result already achieved.",
    "CH3": "Opens with the viewer's doubt, fear, or reason not to believe.",
    "CH4": "Opens by withholding information to create curiosity.",
    "CH5": "Opens by challenging a belief or comparing two ideas.",
    "CH6": "Opens with a specific lived moment the viewer recognises.",
    "CH7": "Opens with expert, clinical, founder, or credentialed proof.",
    "CH8": "Opens with what someone else experienced.",
    "CH9": "Opens with a deadline, event, or sudden problem.",
    "CH10": "Uses sardonic or comedic framing to land a real problem.",
    "CH11": "Opens with confidence, freedom, relief, or another emotional payoff.",
    "CH12": "Opens with cost comparison or value.",
    "CH13": "Opens with a challenge or negative trigger that creates action pressure.",
    "EA1": "Starts in discomfort or frustration and ends in relief.",
    "EA2": "Starts with confusion and ends with sense-making.",
    "EA3": "Starts doubtful and ends convinced by evidence or experience.",
    "EA4": "Starts afraid of a product, category, or outcome and ends reassured.",
    "EA5": "Starts hiding or embarrassed and ends with confidence.",
    "EA6": "Starts resigned and ends with a reason to try again.",
    "EA7": "Starts unaware and ends ready to decide.",
    "EA8": "Starts with irony or dark humour and ends vindicated.",
    "EA9": "Starts already convinced and ends advocating or restocking.",
    "TOFU": "Cold audience; problem-aware but not solution-aware.",
    "MOFU": "Solution-aware audience comparing options and building trust.",
    "BOFU": "Warm audience ready to buy but needing final reassurance.",
    "CONV": "Cold conversion creative with enough specificity and proof to convert directly.",
    "AA": "Credentialed expert voice trusted for correctness.",
    "LEV": "Real consumer trusted for honesty and lived experience.",
    "FO": "Founder voice trusted for intent, accountability, and behind-the-scenes rationale.",
    "IC": "Influencer or creator trusted for lifestyle integration or POV.",
    "CSA": "Creator mirroring an everyday situation or scenario.",
    "BRAND": "Brand-produced, AI, product-only, or no-human-delivery asset.",
    "M1": "Makes trying feel safer and lowers perceived risk.",
    "M2": "Calms panic and prevents quitting or over-reacting.",
    "M3": "Shifts a held belief so the product becomes logical.",
    "M4": "Shows the product visibly working.",
    "M5": "Transfers credibility through evidence, proof, or numbers.",
    "M6": "Neutralises the main reason not to buy.",
    "M7": "Meets the consumer in an urgent or panic moment.",
    "M8": "Builds trust through people like me using it.",
    "M9": "Pushes immediate action through offer, urgency, or direct ask.",
    "M10": "Reframes spend by contrasting cost of inaction vs solution.",
    "M11": "Uses humour or irony to create recognition.",
    "VT1": "Skin, marks, texture, or face is the dominant visual.",
    "VT2": "Product shot is the dominant visual.",
    "VT3": "Copy or headline is the primary element.",
    "VT4": "Person or real-life setting dominates.",
    "VT5": "Numbers, chart, label, or clinical proof is the hero.",
    "VT6": "Illustrated or AI-generated visual treatment.",
    "CF1": "AI voiceover read over a closing card.",
    "CF2": "Talent delivers CTA in-frame in their own voice.",
    "CF3": "Closing card with text only.",
    "CF4": "Content ends without a direct ask.",
    "CM1": "Direct call to purchase.",
    "CM2": "Low-pressure invitation to try.",
    "CM3": "CTA anchored to other people's results.",
    "CM4": "CTA echoes the hook pain before asking.",
    "CM5": "CTA speaks directly to the viewer's turn.",
    "CM6": "Time, stock, or event pressure.",
    "CM7": "Reduces the cost or fear of trying.",
    "CM8": "CTA leads with price, bundle, or offer.",
    "SPM1": "Body message is a price deal, bundle discount, or limited offer.",
    "SPM2": "Body message is cost comparison, price per use, or affordability.",
    "SPM3": "Body message uses study data, lab results, or specific proof numbers.",
    "SPM4": "Body message uses consumer testimonials, reviews, ratings, or before/after proof.",
    "SPM5": "Body message explains how the product works, what it contains, or how to use it.",
    "SPM6": "Body message deepens the consumer problem before presenting the solution.",
    "SPM7": "Body message shows how this product differs from alternatives.",
}


def code_of(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if " - " in text:
        return text.split(" - ", 1)[0].strip()
    if " — " in text:
        return text.split(" — ", 1)[0].strip()
    return text.strip()


def label_of(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if " - " in text:
        return text.split(" - ", 1)[1].strip()
    if " — " in text:
        return text.split(" — ", 1)[1].strip()
    return text


def _add_definitions(items: list[str], definition: str | None = None):
    for entry in items:
        code = code_of(entry)
        DEFINITIONS.setdefault(code, definition or label_of(entry))


for _items in [
    ANGLES_RCF, BELIEFS_RCF, COHORTS_RCF, DRIVERS_RCF, CLAIMS_RCF,
    ANGLES_LPP, BELIEFS_LPP, COHORTS_LPP, DRIVERS_LPP, CLAIMS_LPP,
    ANGLES_SFA, BELIEFS_SFA, COHORTS_SFA, DRIVERS_SFA, CLAIMS_SFA,
    ANGLES_EMC, BELIEFS_EMC, COHORTS_EMC, DRIVERS_EMC, CLAIMS_EMC,
    ANGLES_CPG, BELIEFS_CPG, COHORTS_CPG, DRIVERS_CPG, CLAIMS_CPG,
    ANGLES_BRG, BELIEFS_BRG, COHORTS_BRG, DRIVERS_BRG, CLAIMS_BRG,
    ANGLES_KIT, BELIEFS_KIT, COHORTS_KIT, DRIVERS_KIT,
    ANGLES_EAK, ANGLES_MIN, BELIEFS_MIN, COHORTS_MIN, DRIVERS_MIN,
    ANGLES_USC, BELIEFS_USC, COHORTS_USC, DRIVERS_USC,
    ANGLES_BSC, BELIEFS_BSC, COHORTS_BSC, DRIVERS_BSC,
]:
    _add_definitions(_items)


# Static reference maps --------------------------------------------------------

TAXONOMY_BY_PRODUCT = {
    "RCF": {
        "angles": ANGLES_RCF,
        "beliefs": BELIEFS_RCF,
        "cohorts": COHORTS_RCF,
        "drivers": DRIVERS_RCF,
        "claims": CLAIMS_RCF,
    },
    "Liquid Pimple Patch": {
        "angles": ANGLES_LPP,
        "beliefs": BELIEFS_LPP,
        "cohorts": COHORTS_LPP,
        "drivers": DRIVERS_LPP,
        "claims": CLAIMS_LPP,
    },
    "SpotFade Serum": {
        "angles": ANGLES_SFA,
        "beliefs": BELIEFS_SFA,
        "cohorts": COHORTS_SFA,
        "drivers": DRIVERS_SFA,
        "claims": CLAIMS_SFA,
    },
    "Effortless Melting Cleanser": {
        "angles": ANGLES_EMC,
        "beliefs": BELIEFS_EMC,
        "cohorts": COHORTS_EMC,
        "drivers": DRIVERS_EMC,
        "claims": CLAIMS_EMC,
    },
    "Clear Protect Sunscreen": {
        "angles": ANGLES_CPG,
        "beliefs": BELIEFS_CPG,
        "cohorts": COHORTS_CPG,
        "drivers": DRIVERS_CPG,
        "claims": CLAIMS_CPG,
    },
    "Barrier Repair Moisturiser": {
        "angles": ANGLES_BRG,
        "beliefs": BELIEFS_BRG,
        "cohorts": COHORTS_BRG,
        "drivers": DRIVERS_BRG,
        "claims": CLAIMS_BRG,
    },
    "Acne Kits": {
        "angles": ANGLES_KIT,
        "beliefs": BELIEFS_KIT,
        "cohorts": COHORTS_KIT,
        "drivers": DRIVERS_KIT,
        "claims": [],
    },
    "Emergency Acne Kit": {
        "angles": ANGLES_EAK,
        "beliefs": BELIEFS_EAK,
        "cohorts": COHORTS_EAK,
        "drivers": DRIVERS_EAK,
        "claims": [],
    },
    "Minis": {
        "angles": ANGLES_MIN,
        "beliefs": BELIEFS_MIN,
        "cohorts": COHORTS_MIN,
        "drivers": DRIVERS_MIN,
        "claims": [],
    },
    "Ultra Smooth Cleanser": {
        "angles": ANGLES_USC,
        "beliefs": BELIEFS_USC,
        "cohorts": COHORTS_USC,
        "drivers": DRIVERS_USC,
        "claims": [],
    },
    "Barrier Soothing Cleanser": {
        "angles": ANGLES_BSC,
        "beliefs": BELIEFS_BSC,
        "cohorts": COHORTS_BSC,
        "drivers": DRIVERS_BSC,
        "claims": [],
    },
}


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
        return "RCF"
    return raw


def product_code(product: str) -> str:
    label = canonical_product(product)
    return PRODUCT_META.get(label, {}).get("code", "TSS")


def product_label(product: str) -> str:
    return canonical_product(product)


def _values(product: str, key: str) -> list[str]:
    label = canonical_product(product)
    return TAXONOMY_BY_PRODUCT.get(label, TAXONOMY_BY_PRODUCT["RCF"])[key]


def get_cohorts(product: str) -> list[str]:
    return _values(product, "cohorts")


def get_angles(product: str) -> list[str]:
    return _values(product, "angles")


def get_drivers(product: str) -> list[str]:
    return _values(product, "drivers")


def get_beliefs(product: str) -> list[str]:
    return _values(product, "beliefs")


def get_claims(product: str) -> list[str]:
    return ["None"] + _values(product, "claims")


def define(value: str) -> str:
    return DEFINITIONS.get(code_of(value), "")


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
