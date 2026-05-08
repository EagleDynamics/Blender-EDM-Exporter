## This file contains constants used in several places.


## ----------------------> Drop-down lists constants <------------------------    

## 3 and 4 are the same  for blend_mode, 
## emissiveType ET_ADDITIVE_SELF_ILLUMINATION - 3 and 4 are not the same
TransparencyEnumItems = (
    ('OPAQUE',              "Opaque",                       "", 0),
    ('ALPHA_BLENDING',      "Alpha Blending",               "", 1),
    ('Z_TEST',              "Alpha test",                   "", 2),
    ('SUM_BLENDING',        "Sum Blending",                 "", 3),
    ('SUM_BLENDING_SI',     "Additive Self Illumination",   "", 4),
    ('SHADOWED_BLENDING',   "Shadowed Blending",            "", 6)
)

TransparencyGlassEnumItems = (
    ('ALPHA_BLENDING',      "Alpha Blending",               "", 0), #1
    ('SUM_BLENDING',        "Sum Blending",                 "", 1), #3
    ('SHADOWED_BLENDING',   "Shadowed Blending",            "", 2)  #6
)

DeckTransparencyEnumItems = (
    ('OPAQUE',          "Opaque",           "", 0),
    ('ALPHA_BLENDING',  "Alpha Blending",   "", 1),
    ('Z_TEST',          "Alpha test",       "", 2)
)

ShadowCasterEnumItems = (
    ('SHADOW_CASTER_YES',   "YES",          "Cast Shadows",         0),
    ('SHADOW_CASTER_NO',    "NO",           "Don't cast shadows",   1),
    ('SHADOW_CASTER_ONLY',  "ONLY_SHADOW",  "Cast shadows only",    2)
)

GlassEnumItems = (
    ('GLASS_INSTRUMENTAL',   "Instrumental",    "GLASS INSTRUMENTAL",   0),
    ('GLASS_COCKPIT',        "Cockpit ",        "GLASS COCKPIT",       1)
)

EmissionEnumItems = (
    ('NONE',                            "None",                             "", 0),
    ('DEFAULT',                         "Default Illumination",             "", 1),
    ('SELF_ILLUMINATION',               "Self Illumination",                "", 2),
    ('TRANSPARENT_SELF_ILLUMINATION',   "Transparent Self Illumination",    "", 3),
    ('ADDITIVE_SELF_ILLUMINATION',      "Additive Self Illumination",       "", 4)
)