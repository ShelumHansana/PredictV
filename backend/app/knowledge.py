"""
PredictV knowledge base (petrol motorbikes).

This part of the system is a transparent, rule-based expert system - it is
NOT machine learning. Each fault lists the evidence that points to it and how
strongly (weight 1-5). The weights encode standard workshop troubleshooting
practice for small petrol motorbike engines; they are not learned from data.

Every text has an English ("en") and Sinhala ("si") version.
"""

# ── Questions shown to the rider ─────────────────────────────────────────────

SYMPTOM_GROUPS = [
    {
        "id": "starting",
        "en": "Starting",
        "si": "ස්ටාර්ට් කිරීම",
        "symptoms": [
            {"id": "hard_start", "en": "Hard to start (many kicks or long cranking)",
             "si": "ස්ටාර්ට් වීම අමාරුයි (කික් කිහිපයක් ගහන්න වෙනවා)"},
            {"id": "weak_starter", "en": "Self-starter is slow or just clicks, lights are dim",
             "si": "සෙල්ෆ් ස්ටාර්ට් එක හෙමින් කැරකෙනවා / ටික් සද්දයක් විතරයි, ලයිට් අඳුරුයි"},
        ],
    },
    {
        "id": "running",
        "en": "While riding",
        "si": "පදවන අතරතුර",
        "symptoms": [
            {"id": "rough_idle", "en": "Idle is uneven, or engine stops when idling",
             "si": "අයිඩ්ලින් එක අස්ථාවරයි, නැත්නම් නැවතුණාම එන්ජිම ඕෆ් වෙනවා"},
            {"id": "power_loss", "en": "Less power / slow pick-up",
             "si": "බලය අඩුයි / පිකප් එක මදි"},
            {"id": "misfire", "en": "Engine jerks or misses while riding",
             "si": "පදවද්දී එන්ජිම ගැස්සෙනවා / මිස් වෙනවා"},
            {"id": "stalls", "en": "Engine cuts out suddenly while riding",
             "si": "පදවද්දී එන්ජිම එකපාරටම ඕෆ් වෙනවා"},
            {"id": "high_fuel", "en": "Uses more petrol than before",
             "si": "පෙට්‍රල් වැය වීම කලින්ට වඩා වැඩියි"},
            {"id": "overheating", "en": "Engine gets unusually hot",
             "si": "එන්ජිම අසාමාන්‍ය ලෙස රත් වෙනවා"},
        ],
    },
    {
        "id": "exhaust",
        "en": "Smoke and smell",
        "si": "දුම සහ ගන්ධය",
        "symptoms": [
            {"id": "black_smoke", "en": "Black smoke from the exhaust",
             "si": "සයිලන්සරයෙන් කළු දුමක් එනවා"},
            {"id": "blue_smoke", "en": "Blue or white smoke, and engine oil level keeps dropping",
             "si": "නිල් / සුදු දුමක් එනවා, එන්ජින් ඔයිල් අඩු වෙනවා"},
            {"id": "fuel_smell", "en": "Strong petrol smell",
             "si": "තද පෙට්‍රල් ගන්ධයක් එනවා"},
        ],
    },
    {
        "id": "sounds",
        "en": "Sounds",
        "si": "ශබ්ද",
        "symptoms": [
            {"id": "backfire", "en": "Popping or banging from the exhaust",
             "si": "සයිලන්සරයෙන් පුපුරන / වෙඩි වගේ සද්ද එනවා"},
            {"id": "tapping", "en": "Ticking / tapping noise from the top of the engine",
             "si": "එන්ජිමේ උඩ කොටසින් ටික් ටික් සද්දයක් එනවා"},
            {"id": "loud_exhaust", "en": "Exhaust is louder than normal",
             "si": "සයිලන්සර් සද්දය සාමාන්‍යයට වඩා වැඩියි"},
        ],
    },
]

# "When was it last done?" questions. Answers: recent / due / overdue / unknown
SERVICE_ITEMS = [
    {"id": "oil", "en": "Engine oil changed", "si": "එන්ජින් ඔයිල් මාරු කළේ",
     "limits_km": [2000, 3500]},
    {"id": "air_filter", "en": "Air filter cleaned or changed", "si": "එයාර් ෆිල්ටරය පිරිසිදු කළේ / මාරු කළේ",
     "limits_km": [4000, 8000]},
    {"id": "spark_plug", "en": "Spark plug changed", "si": "ස්පාර්ක් ප්ලග් එක මාරු කළේ",
     "limits_km": [8000, 12000]},
]
# limits_km = [still fine below this, overdue above this]. These are typical
# small-motorbike service intervals; the owner's manual always wins.

# ── Faults ───────────────────────────────────────────────────────────────────
# evidence keys:
#   symptom ids                      -> ticked by the rider
#   svc:<item>:overdue / svc:<item>:due
#   ml:rich / ml:lean_or_ignition    -> from the trained model (optional step)
#   gas:hc_high / gas:co_high        -> reading above the legal limit
#   high_mileage                     -> odometer above 60,000 km

FAULTS = [
    {
        "id": "air_filter",
        "en": "Dirty or blocked air filter",
        "si": "එයාර් ෆිල්ටරය අපිරිසිදු වීම / අවහිර වීම",
        "what_en": "The engine cannot breathe properly, so it burns too much petrol for the air it gets.",
        "what_si": "එන්ජිමට අවශ්‍ය තරම් වාතය ලැබෙන්නේ නැති නිසා පෙට්‍රල් වැඩිපුර දැවෙනවා.",
        "fix_en": [
            "Open the air filter box and take the filter out.",
            "Foam filter: wash, dry and lightly oil it. Paper filter: replace it.",
            "Refit it properly so no air gets around the filter.",
        ],
        "fix_si": [
            "එයාර් ෆිල්ටර් බොක්ස් එක ඇරලා ෆිල්ටරය එළියට ගන්න.",
            "ෆෝම් ෆිල්ටරයක් නම් හෝදලා වේලලා තෙල් ටිකක් ගාන්න. කඩදාසි ෆිල්ටරයක් නම් අලුත් එකක් දාන්න.",
            "ෆිල්ටරය පැත්තෙන් වාතය යන්නේ නැති වෙන්න හරියට ෆිට් කරන්න.",
        ],
        "who": "diy", "urgency": "medium",
        "evidence": {"black_smoke": 3, "high_fuel": 3, "power_loss": 2, "fuel_smell": 1,
                     "svc:air_filter:overdue": 4, "svc:air_filter:due": 2, "ml:rich": 3},
    },
    {
        "id": "rich_mixture",
        "en": "Fuel mixture too rich (carburettor / injector / choke)",
        "si": "ඉන්ධන මිශ්‍රණය වැඩියි (කාබරේටරය / ඉන්ජෙක්ටරය / චෝක් එක)",
        "what_en": "Too much petrol is going in. Common causes: carburettor out of tune, choke stuck on, or a leaking injector.",
        "what_si": "එන්ජිමට පෙට්‍රල් වැඩියෙන් යනවා. කාබරේටරය ටියුන් නැතිවීම, චෝක් එක හිරවීම හෝ ඉන්ජෙක්ටරය ලීක් වීම පොදු හේතු.",
        "fix_en": [
            "Check the choke lever returns fully to OFF.",
            "Clean the air filter first - it causes the same signs.",
            "Have a mechanic clean and tune the carburettor (or test the injector and sensors on FI bikes).",
        ],
        "fix_si": [
            "චෝක් ලීවරය සම්පූර්ණයෙන්ම OFF වෙනවද බලන්න.",
            "මුලින්ම එයාර් ෆිල්ටරය පිරිසිදු කරන්න - ඒකෙනුත් මේ ලක්ෂණම එනවා.",
            "කාර්මිකයෙකු ලවා කාබරේටරය පිරිසිදු කර ටියුන් කරගන්න (FI බයික් වල ඉන්ජෙක්ටරය සහ සෙන්සර් පරීක්ෂා කරගන්න).",
        ],
        "who": "mechanic", "urgency": "medium",
        "evidence": {"black_smoke": 4, "fuel_smell": 3, "high_fuel": 3, "rough_idle": 1,
                     "ml:rich": 5, "gas:co_high": 4},
    },
    {
        "id": "spark_plug",
        "en": "Worn or dirty spark plug",
        "si": "ස්පාර්ක් ප්ලග් එක ගෙවී යාම / අපිරිසිදු වීම",
        "what_en": "The spark is weak, so petrol does not burn completely.",
        "what_si": "ස්පාර්ක් එක දුර්වල නිසා පෙට්‍රල් සම්පූර්ණයෙන් දැවෙන්නේ නැහැ.",
        "fix_en": [
            "Remove the spark plug and look at the tip: black and sooty, oily, or a worn electrode means replace it.",
            "Fit the plug type given in the owner's manual and set the gap.",
            "A plug that goes black again quickly means the mixture is too rich - check the air filter and carburettor.",
        ],
        "fix_si": [
            "ස්පාර්ක් ප්ලග් එක ගලවලා තුඩ බලන්න: කළු දැලි, තෙල්, හෝ ගෙවුණු ඉලෙක්ට්‍රෝඩයක් තියෙනවා නම් මාරු කරන්න.",
            "අත්පොතේ සඳහන් වර්ගයේ ප්ලග් එකක් දාලා ගැප් එක හදන්න.",
            "ප්ලග් එක ඉක්මනට ආයෙත් කළු වෙනවා නම් මිශ්‍රණය වැඩියි - එයාර් ෆිල්ටරය සහ කාබරේටරය බලන්න.",
        ],
        "who": "diy", "urgency": "medium",
        "evidence": {"hard_start": 3, "misfire": 3, "rough_idle": 2, "power_loss": 2, "high_fuel": 1,
                     "svc:spark_plug:overdue": 4, "svc:spark_plug:due": 2,
                     "ml:lean_or_ignition": 2, "gas:hc_high": 3},
    },
    {
        "id": "ignition",
        "en": "Weak ignition (plug cap, HT lead, coil or CDI)",
        "si": "ඉග්නිෂන් පද්ධතියේ දුර්වලතාවක් (ප්ලග් කැප්, වයරය, කොයිල් හෝ CDI)",
        "what_en": "The spark cuts in and out, usually worse when hot or in the rain.",
        "what_si": "ස්පාර්ක් එක ඉඳහිට නැති වෙනවා; රත් වුණාම හෝ වැස්සට වැඩි වෙනවා.",
        "fix_en": [
            "Push the plug cap on firmly and check the lead for cracks.",
            "Try a new spark plug first - it is the cheapest part.",
            "If it still misses, have a mechanic test the coil and CDI.",
        ],
        "fix_si": [
            "ප්ලග් කැප් එක තදින් ගහලා, වයරයේ පැලුම් තියෙනවද බලන්න.",
            "මුලින්ම අලුත් ස්පාර්ක් ප්ලග් එකක් දාලා බලන්න - ලාභම කොටස ඒකයි.",
            "තවමත් මිස් වෙනවා නම් කාර්මිකයෙකු ලවා කොයිල් එක සහ CDI එක පරීක්ෂා කරගන්න.",
        ],
        "who": "mechanic", "urgency": "medium",
        "evidence": {"misfire": 4, "stalls": 3, "backfire": 2, "hard_start": 2,
                     "ml:lean_or_ignition": 2, "gas:hc_high": 2},
    },
    {
        "id": "battery",
        "en": "Weak battery or charging problem",
        "si": "බැටරිය දුර්වල වීම / චාජ් නොවීම",
        "what_en": "Low voltage makes the starter slow and the spark weak.",
        "what_si": "වෝල්ටීයතාව අඩු වුණාම ස්ටාටරය හෙමින් කැරකෙනවා, ස්පාර්ක් එකත් දුර්වල වෙනවා.",
        "fix_en": [
            "Clean and tighten the battery terminals.",
            "Charge the battery and measure it: about 12.6 V when resting is healthy.",
            "With the engine running it should rise to roughly 13.5-14.5 V. If not, have the charging system checked.",
        ],
        "fix_si": [
            "බැටරි ටර්මිනල් පිරිසිදු කරලා තද කරන්න.",
            "බැටරිය චාජ් කරලා මැනලා බලන්න: එන්ජිම ඕෆ් කරලා 12.6 V විතර තියෙනවා නම් හොඳයි.",
            "එන්ජිම වැඩ කරද්දී 13.5-14.5 V විතර වෙන්න ඕන. නැත්නම් චාජින් පද්ධතිය පරීක්ෂා කරගන්න.",
        ],
        "who": "diy", "urgency": "medium",
        "evidence": {"weak_starter": 5, "hard_start": 1, "ml:lean_or_ignition": 2},
    },
    {
        "id": "lean_mixture",
        "en": "Fuel mixture too lean (air leak or blocked jet)",
        "si": "ඉන්ධන මිශ්‍රණය මදි (වාත කාන්දුවක් හෝ ජෙට් එක අවහිර වීම)",
        "what_en": "Too much air for the petrol. The engine runs hot and pops on the exhaust.",
        "what_si": "පෙට්‍රල් වලට සාපේක්ෂව වාතය වැඩියි. එන්ජිම රත් වෙනවා, සයිලන්සරයෙන් පුපුරන සද්ද එනවා.",
        "fix_en": [
            "Check the rubber joint between carburettor and engine for cracks or a loose clamp.",
            "Have the carburettor jets cleaned.",
            "Do not ride hard until fixed - a lean engine overheats.",
        ],
        "fix_si": [
            "කාබරේටරය සහ එන්ජිම අතර රබර් සන්ධියේ පැලුම් හෝ ලිහිල් ක්ලැම්ප් තියෙනවද බලන්න.",
            "කාබරේටර් ජෙට් පිරිසිදු කරගන්න.",
            "හදනකම් වේගයෙන් පදවන්න එපා - මිශ්‍රණය මදි වුණාම එන්ජිම අධික ලෙස රත් වෙනවා.",
        ],
        "who": "mechanic", "urgency": "high",
        "evidence": {"backfire": 4, "overheating": 3, "rough_idle": 2, "power_loss": 2, "stalls": 1,
                     "ml:lean_or_ignition": 3},
    },
    {
        "id": "fuel_supply",
        "en": "Petrol not reaching the engine properly",
        "si": "එන්ජිමට පෙට්‍රල් හරියට නොලැබීම",
        "what_en": "A blocked fuel filter, fuel tap or tank cap vent starves the engine.",
        "what_si": "ෆියුල් ෆිල්ටරය, ෆියුල් ටැප් එක හෝ ටැංකි මූඩියේ වාත සිදුර අවහිර වුණාම එන්ජිමට පෙට්‍රල් මදි වෙනවා.",
        "fix_en": [
            "Open the tank cap and try again - if it runs better, the cap vent is blocked.",
            "Check petrol flows freely from the fuel tap / hose.",
            "Replace the fuel filter and drain any water or dirt from the carburettor bowl.",
        ],
        "fix_si": [
            "ටැංකි මූඩිය ඇරලා ආයෙත් බලන්න - හොඳට වැඩ කරනවා නම් මූඩියේ වාත සිදුර අවහිර වෙලා.",
            "ෆියුල් ටැප් එකෙන් / හෝස් එකෙන් පෙට්‍රල් හොඳට ගලනවද බලන්න.",
            "ෆියුල් ෆිල්ටරය මාරු කරලා, කාබරේටර් බෝල් එකේ වතුර / කුණු අයින් කරන්න.",
        ],
        "who": "diy", "urgency": "medium",
        "evidence": {"stalls": 4, "power_loss": 2, "hard_start": 2, "misfire": 1},
    },
    {
        "id": "oil_burning",
        "en": "Engine burning oil (piston rings or valve seals)",
        "si": "එන්ජිම ඔයිල් දවනවා (පිස්ටන් රින්ග්ස් හෝ වෑල්ව් සීල්)",
        "what_en": "Oil gets into the combustion chamber and burns. This is wear inside the engine.",
        "what_si": "ඔයිල් දහන කුටීරයට ගිහින් දැවෙනවා. මේක එන්ජිම ඇතුළේ ගෙවීමක්.",
        "fix_en": [
            "Check the oil level every week and top up - never run it low.",
            "Have a mechanic do a compression test to confirm.",
            "The repair is new piston rings and/or valve seals.",
        ],
        "fix_si": [
            "සතියකට වරක් ඔයිල් මට්ටම බලලා අඩු නම් දාන්න - කවදාවත් අඩුවෙන් තියන්න එපා.",
            "තහවුරු කරගන්න කාර්මිකයෙකු ලවා කම්ප්‍රෙෂන් ටෙස්ට් එකක් කරගන්න.",
            "අලුත්වැඩියාව: අලුත් පිස්ටන් රින්ග්ස් සහ/හෝ වෑල්ව් සීල් දැමීම.",
        ],
        "who": "mechanic", "urgency": "high",
        "evidence": {"blue_smoke": 6, "power_loss": 1, "high_mileage": 1, "gas:hc_high": 3},
    },
    {
        "id": "old_oil",
        "en": "Engine oil is old or low",
        "si": "එන්ජින් ඔයිල් පරණයි / අඩුයි",
        "what_en": "Old oil protects the engine less and makes it run hotter and noisier.",
        "what_si": "පරණ ඔයිල් වලින් එන්ජිම හරියට ආරක්ෂා වෙන්නේ නැහැ; රත් වීම සහ සද්දය වැඩි වෙනවා.",
        "fix_en": [
            "Check the level with the dipstick or sight glass.",
            "Change the oil using the grade in the owner's manual (commonly 10W-30 or 20W-40 4T).",
            "Clean or replace the oil filter / strainer at the same time.",
        ],
        "fix_si": [
            "ඩිප්ස්ටික් එකෙන් / වීදුරුවෙන් ඔයිල් මට්ටම බලන්න.",
            "අත්පොතේ සඳහන් ග්‍රේඩ් එකේ ඔයිල් දාන්න (සාමාන්‍යයෙන් 10W-30 හෝ 20W-40 4T).",
            "ඒ එක්කම ඔයිල් ෆිල්ටරය / ස්ට්‍රේනරය පිරිසිදු කරන්න හෝ මාරු කරන්න.",
        ],
        "who": "diy", "urgency": "medium",
        "evidence": {"svc:oil:overdue": 5, "svc:oil:due": 2, "overheating": 2, "tapping": 2},
    },
    {
        "id": "valve_clearance",
        "en": "Valve (tappet) clearance needs adjusting",
        "si": "වෑල්ව් (ටැපට්) ක්ලියරන්ස් එක හදන්න ඕන",
        "what_en": "The gap at the valves has changed with wear, giving a ticking noise and harder starting.",
        "what_si": "ගෙවීම නිසා වෑල්ව් වල ගැප් එක වෙනස් වෙලා; ටික් ටික් සද්දයක් සහ ස්ටාර්ට් අමාරුවක් එනවා.",
        "fix_en": [
            "Have a mechanic check and set the tappet clearance with the engine cold.",
            "Change the oil first if it is overdue - old oil also causes ticking.",
        ],
        "fix_si": [
            "එන්ජිම සීතල වෙලාවේ කාර්මිකයෙකු ලවා ටැපට් ක්ලියරන්ස් එක බලලා හදාගන්න.",
            "ඔයිල් මාරු කරන්න කල් ගිහින් නම් මුලින් ඒක කරන්න - පරණ ඔයිල් වලිනුත් ටික් සද්දය එනවා.",
        ],
        "who": "mechanic", "urgency": "low",
        "evidence": {"tapping": 5, "hard_start": 1, "power_loss": 1, "high_mileage": 1},
    },
    {
        "id": "exhaust_leak",
        "en": "Exhaust leak or damaged silencer",
        "si": "සයිලන්සරයේ කාන්දුවක් / හානියක්",
        "what_en": "Gas escapes before the end of the exhaust. It is loud and can also make an emission test read wrongly.",
        "what_si": "සයිලන්සරයේ කෙළවරට කලින් දුම පිටවෙනවා. සද්දය වැඩියි; දුම් පරීක්ෂණයේ අගයත් වැරදි වෙන්න පුළුවන්.",
        "fix_en": [
            "Look for black soot marks at the joint between engine and exhaust pipe.",
            "Tighten the exhaust nuts and replace the gasket.",
            "Weld or replace a rusted silencer.",
        ],
        "fix_si": [
            "එන්ජිම සහ සයිලන්සර් බටය සම්බන්ධ වන තැන කළු දැලි පැල්ලම් තියෙනවද බලන්න.",
            "සයිලන්සර් නට් තද කරලා ගැස්කට් එක මාරු කරන්න.",
            "මලකඩ කාපු සයිලන්සරයක් නම් වෙල්ඩ් කරන්න හෝ මාරු කරන්න.",
        ],
        "who": "mechanic", "urgency": "low",
        "evidence": {"loud_exhaust": 5, "backfire": 2},
    },
]

# Sri Lankan in-use limits for petrol motorcycles (idle and 2,500 rpm, no load)
# as published by the emission-testing operator: https://ecosri.lk/?p=5723
SL_LIMITS = {"co_percent": 4.0, "hc_ppm": 6000.0}

ML_LABELS = {
    "normal": {"en": "Burning normally", "si": "සාමාන්‍ය ලෙස දැවෙනවා"},
    "rich": {"en": "Too much petrol (rich mixture)", "si": "පෙට්‍රල් වැඩියි (රිච් මිශ්‍රණය)"},
    "lean_or_ignition": {"en": "Too little petrol or weak spark", "si": "පෙට්‍රල් මදි හෝ ස්පාර්ක් දුර්වලයි"},
}
