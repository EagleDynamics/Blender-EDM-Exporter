from bpy.types import PropertyGroup, Object
from bpy.props import StringProperty, BoolProperty, IntProperty, EnumProperty, FloatVectorProperty, FloatProperty

from enums import EDMPropsSpecialTypeStr

class EDM_PropsEnumValues(PropertyGroup):
    bl_idname = "edm.PropsEnumValues"

    mat_name_prop: StringProperty(name="new_mat_prop_name", default="New Material")
    socket_name_prop: StringProperty(name="new_socket_prop_name", default="New Socket")
    enum_name_prop: StringProperty(name="new_enum_prop_name", default="New Enumeration Item")

class EDMPropsGroup(PropertyGroup):
    bl_idname = "edm.EDMPropsGroup"

    SPECIAL_TYPE : EnumProperty(
        name = "Obj.type",
        description = "Choose the type of analysis this material do",
        items = [
            (EDMPropsSpecialTypeStr.UNKNOWN_TYPE,       'unknown_type',      "Unspecified object type: geometry/animation empty",                    0),
            (EDMPropsSpecialTypeStr.USER_BOX,           'user_box',          "Box covering only geometry. Is used for backlight",                    1),
            (EDMPropsSpecialTypeStr.BOUNDING_BOX,       'bounding_box',      "Box covering geometry and all animations. Is used for camera cutoff",  2),
            (EDMPropsSpecialTypeStr.COLLISION_LINE,     'collision_line',    "Geometry edge used for collision",                                     3),
            (EDMPropsSpecialTypeStr.COLLISION_SHELL,    'collision_shell',   "Geometry mesh used for collision",                                     4),
            (EDMPropsSpecialTypeStr.CONNECTOR,          'connector',         "Type Connector",                                                       5),
            (EDMPropsSpecialTypeStr.FAKE_LIGHT,         'fake_light',        "Type BANO",                                                            6),
            (EDMPropsSpecialTypeStr.LIGHT_BOX,          'light_box',         "Box - Limiter for light source",                                       7),
            (EDMPropsSpecialTypeStr.NUMBER_TYPE,        'number_type',       "Dynamic digits for bort number",                                       8),
            (EDMPropsSpecialTypeStr.SKIN_BOX,           'skin_box',          "Box covering bones geometry",                                          9),
            (EDMPropsSpecialTypeStr.WATER_MASK,         'water_mask',        "Plane to cover water in boats",                                        10),
            (EDMPropsSpecialTypeStr.TRANSPARENT_PIVOT,  'transparent_pivot', "Empty object setting sorting helper for transparent objects",          11),
        ],
        default = 'UNKNOWN_TYPE'
    ) # type: ignore

    TWO_SIDED : BoolProperty(
        name = "two sided object",
        default = False
    )
    
    SURFACE_MODE : BoolProperty(
        name = "surface mode",
        default = False
    )

    DAMAGE_ARG : IntProperty(
        name = 'Damage arg',
        min = -1,
        default = -1
    )

    AO_ARG : IntProperty(
        name = 'LightMap arg',
        min = -1,
        default = -1
    )

    COLOR_ARG : IntProperty(
        name = 'Base color arg',
        min = -1,
        default = -1
    )

    ## intensity of emissive
    EMISSIVE_ARG : IntProperty(
        name = 'Emissive value arg',
        min = -1,
        default = -1
    )

    EMISSIVE_COLOR_ARG : IntProperty(
        name = 'Emissive color arg',
        min = -1,
        default = -1
    )

    UV_LB : FloatVectorProperty(
        name = 'tex_coords_lb',
        precision = 2,
        size = 2,
        default = [0.0, 0.0],
        subtype = 'COORDINATES'
    )

    UV_RT : FloatVectorProperty(
        name = 'tex_coords_rt',
        precision = 2,
        size = 2,
        default = [1.0, 1.0],
        subtype = 'COORDINATES'
    )

    SIZE : FloatProperty(
        name = "size",
        default = 3.0,
        min = 0.0
    )

    UV_LB_BACK : FloatVectorProperty(
        name = 'tex_coords_lb_back',
        precision = 2,
        size = 2,
        default = [0.0, 0.0]
    )

    UV_RT_BACK : FloatVectorProperty(
        name = 'tex_coords_rt_back',
        precision = 2,
        size = 2,
        default = [1.0, 1.0]
    )

    ANIMATED_BRIGHTNESS : FloatProperty(
        name = "object luminance",
        default = 1.0,
        min = 0.0,
        options = {'ANIMATABLE'}
    )

    LIGHT_SOFTNESS : FloatProperty(
        name = "light softness",
        default = 0.0,
        min = 0.0,
        options = {'ANIMATABLE'},
        description = """If light softeness = 1, material roughftess of illuminated objects set to 1.
        If light softeness = 0, material roughftess of illuminated objects does not change."""
    )

    NUMBER_UV_X_ARG : IntProperty(
        name = "xArg",
        default = -1,
        min = -1
    )

    NUMBER_UV_X_SCALE : FloatProperty(
        name = "xScale",
        default = 0,
        min = 0,
        max = 1
    )

    NUMBER_UV_Y_ARG : IntProperty(
        name = "yArg",
        min = -1,
        default = -1
    )

    NUMBER_UV_Y_SCALE : FloatProperty(
        name = "yScale",
        default = 0,
        min = 0,
        max = 1
    )

    CONNECTOR_EXT : StringProperty(
        name="connector ext",
        default = ""
    )

    LIGHT_COLOR_ARG : IntProperty(
        name = 'color',
        min = -1,
        default = -1
    )

    LIGHT_POWER_ARG : IntProperty(
        name = 'power',
        min = -1,
        default = -1
    )

    LIGHT_SPOT_SHAPE_ARG : IntProperty(
        name = 'spot shape (size+blend)',
        min = -1,
        default = -1
    )

    LIGHT_DISTANCE_ARG : IntProperty(
        name = 'distance',
        min = -1,
        default = -1
    )

    LIGHT_SPECULAR_ARG : IntProperty(
        name = 'specular',
        min = -1,
        default = -1
    )
    ## ---- Volume light params ----
    
    ## radiusFactor - ratio of volumetric radius to omni/spot radius. 
    ##   if radiosFactor == 1, volumetric radius == light radius.
    ##   if radiusFactor == 0, volumetric is not used.
    LIGHT_VOLUME_RADIUS_FACTOR: FloatProperty(
        name = "radius factor",
        min = 0,
        default = 0,
        max = 1
    )

    ## volumetric density
    LIGHT_VOLUME_DENSITY_FACTOR: FloatProperty(
        name = "density factor",
        min = 0,
        default = 1,
        max = 1
    )
    
    ## distance
    LIGHT_VOLUME_NEAR_DISTANCE: FloatProperty(
        name = "near distance",
        min = 0,
        default = 0
    )

    LIGHT_VOLUME_TYPE: EnumProperty(
        name = "volume type",
        items = [
            #landing, nav, taxi, bano
            ('LANDING', 'landing',  "light type: landing",  0),
            ('NAV',     'nav',      "light type: nav",      1),
            ('TAXI',    'taxi',     "light type: taxi",     2),
            ('BANO',    'bano',     "light type: bano",     3),
            ('NONE',    'none',     "",                     4),

        ],
        default = 'NONE'
    ) 
    ## ---- Volume light params ----

    OPACITY_VALUE_ARG : IntProperty(
        name = 'Opacity value arg',
        min = -1,
        default = -1
    )

def get_edm_props(o: Object) -> EDMPropsGroup:
    return o.EDMProps

def get_objects_custom_props_classes():
    return [
        EDM_PropsEnumValues,
        EDMPropsGroup,
    ]