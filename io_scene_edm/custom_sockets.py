import bpy
from version_specific import InterfaceNodeSocket
from bpy.types import NodeSocket
from constants import (
    EmissionEnumItems, 
    GlassEnumItems,
    TransparencyEnumItems,
    TransparencyGlassEnumItems,
    ShadowCasterEnumItems,
    DeckTransparencyEnumItems
)


class EdmGlassTypeSocket(NodeSocket):
    bl_idname = "EdmSocketGlassType"
    bl_label = "EDM Glass Socket"

    def update_value(self, context):
        return None

    default_value: bpy.props.EnumProperty (
        name        = 'Glass Type',
        description = "Glass",
        items       = GlassEnumItems,
        update      = update_value
    )

    def draw(self, context, layout, node, text):
        if self.is_output or self.is_linked:
            layout.label(text=text)
        else:
            layout.prop(self, "default_value", text=text)

    def draw_color(self, context, node):
        return (1.0, 0.4, 0.216, 0.5)

class EdmGlassTypeSocketInterface(InterfaceNodeSocket):
    bl_idname = "EdmGlassTypeSocketInterface"
    bl_socket_idname = 'EdmSocketGlassType'
    bl_label = "GlassTypeSocket"

    default_value: bpy.props.EnumProperty (
        name        = 'Glass Type',
        description = "Default value for glass type",
        items       = GlassEnumItems,
        default     = 'GLASS_INSTRUMENTAL'
    )

    def draw(self, context, layout):
        layout.prop(self, "default_value")

    def init_socket(self, node, socket, data_path):
        socket.default_value = self.default_value

    def from_socket(self, node, socket):
        self.default_value = socket.default_value

    def draw_color(self, context):
        return (1.0, 0.8, 0.4, 1.0)

class EdmGlassTransparencySocket(NodeSocket):
    bl_idname = 'EdmGlassTransparencySocketType'
    bl_label = "EDM Node GLass Transparency Socket"
    
    def update_value(self, context):             
        return None
    
    default_value: bpy.props.EnumProperty(
        name        = 'Transparency',
        description = "Transparency/blending mode",
        items       = TransparencyGlassEnumItems,
        update      = update_value
    )

    def draw(self, context, layout, node, text):
        if self.is_output or self.is_linked:
            layout.label(text=text)
        else:
            layout.prop(self, "default_value", text=text)

    def draw_color(self, context, node):
        return (1.0, 0.4, 0.216, 0.5)
    
class EdmGlassTransparencySocketInterface(InterfaceNodeSocket):
    bl_idname = "EdmGlassTransparencySocketInterface"
    bl_socket_idname = 'EdmGlassTransparencySocketType'
    bl_label = "GlassTransparencySocket"

    default_value: bpy.props.EnumProperty(
        name    = 'Transparency',
        description = "Default value for transparency/blending mode",
        items   = TransparencyGlassEnumItems,
        default = 'ALPHA_BLENDING'
    )

    def init_socket(self, node, socket, data_path):
        socket.default_value = self.default_value

    def from_socket(self, node, socket):
        self.default_value = socket.default_value

    def draw_color(self, context):
        return (1.0, 0.8, 0.4, 1.0)
    
class EdmGlassShadowCasterSocket(NodeSocket):
    bl_idname = "EdmGlassSocketShadowCasterType"
    bl_label = "EDM NodeShadow Caster Socket"

    def update_value(self, context):
        return None

    default_value: bpy.props.EnumProperty (
        name        = 'Shadow Caster',
        description = "Does mesh cast shadow",
        items       = ShadowCasterEnumItems,
        update      = update_value
    )

    def draw(self, context, layout, node, text):
        if self.is_output or self.is_linked:
            layout.label(text=text)
        else:
            layout.prop(self, "default_value", text=text)

    def draw_color(self, context, node):
        return (1.0, 0.4, 0.216, 0.5)
    
class EdmGlassShadowCasterSocketInterface(InterfaceNodeSocket):
    bl_idname = "EdmGlassShadowCasterSocketInterface"
    bl_socket_idname = 'EdmGlassSocketShadowCasterType'
    bl_label = "ShadowCasterSocket"

    default_value: bpy.props.EnumProperty (
        name        = 'Shadow Caster',
        description = "Default value for shadow caster",
        items       = ShadowCasterEnumItems,
        default     = 'SHADOW_CASTER_YES'
    )

    def draw(self, context, layout):
        layout.prop(self, "default_value")

    def init_socket(self, node, socket, data_path):
        socket.default_value = self.default_value

    def from_socket(self, node, socket):
        self.default_value = socket.default_value

    def draw_color(self, context):
        return (1.0, 0.8, 0.4, 1.0)
        
#TODO-270: what's the difference between NodeSocket and InterfaceNodeSocket
class EdmShadowCasterSocket(NodeSocket):
    bl_idname = "EdmSocketShadowCasterType"
    bl_label = "EDM NodeShadow Caster Socket"

    def update_value(self, context):
        return None

    default_value: bpy.props.EnumProperty (
        name        = 'Shadow Caster',
        description = "Does mesh cast shadow",
        items       = ShadowCasterEnumItems,
        update      = update_value
    )

    def draw(self, context, layout, node, text):
        if self.is_output or self.is_linked:
            layout.label(text=text)
        else:
            layout.prop(self, "default_value", text=text)

    def draw_color(self, context, node):
        return (1.0, 0.4, 0.216, 0.5)
    
class EdmShadowCasterSocketInterface(InterfaceNodeSocket):
    bl_idname = "EdmShadowCasterSocketInterface"
    bl_socket_idname = 'EdmSocketShadowCasterType'
    bl_label = "ShadowCasterSocket"

    default_value: bpy.props.EnumProperty (
        name        = 'Shadow Caster',
        description = "Default value for shadow caster",
        items       = ShadowCasterEnumItems,
        default     = 'SHADOW_CASTER_YES'
    )

    def draw(self, context, layout):
        layout.prop(self, "default_value")

    def init_socket(self, node, socket, data_path):
        socket.default_value = self.default_value

    def from_socket(self, node, socket):
        self.default_value = socket.default_value

    def draw_color(self, context):
        return (1.0, 0.8, 0.4, 1.0)

class EdmBidirectionalCasterSocket(NodeSocket):
    bl_idname = "EdmSocketBidirectionalType"
    bl_label = "EDM Bidirectional Caster Socket"
    
    def update_value(self, context):
        return None
    
    default_value: bpy.props.BoolProperty(
        name    = 'Bidirectional',
        default = True,
        update  = update_value
    )
    
    def draw(self, context, layout, node, text):
        layout.prop(self, "default_value")

    def draw_color(self, context, node):
        return (1.0, 0.4, 0.216, 0.5)
    
class EdmBidirectionalCasterSocketInterface(InterfaceNodeSocket):
    bl_idname = "EdmBidirectionalCasterSocketInterface"
    bl_socket_idname = 'EdmSocketBidirectionalType'
    bl_label = "BidirectionalCasterSocket"

    def draw(self, context, layout):
        pass

    def draw_color(self, context):
        return (1.0, 0.8, 0.4, 1.0)

class EdmTransparencySocket(NodeSocket):
    bl_idname = 'EdmTransparencySocketType'
    bl_label = "EDM Node Transparency Socket"
    
    def update_value(self, context):             
        return None
    
    default_value: bpy.props.EnumProperty(
        name        = 'Transparency',
        description = "Transparency/blending mode",
        items       = TransparencyEnumItems,
        update      = update_value
    )

    def draw(self, context, layout, node, text):
        if self.is_output or self.is_linked:
            layout.label(text=text)
        else:
            layout.prop(self, "default_value", text=text)

    ## Color of socket in reference material.
    ## All default sockets have unique color. 
    ## Color of custom-socket EdmTransparencySocket has semi-transparent orange color. 
    def draw_color(self, context, node):
        return (1.0, 0.4, 0.216, 0.5)
    
class EdmTransparencySocketInterface(InterfaceNodeSocket):
    bl_idname = "EdmTransparencySocketInterface"
    bl_socket_idname = 'EdmTransparencySocketType'
    bl_label = "TransparencySocket"

    default_value: bpy.props.EnumProperty(
        name    = 'Transparency',
        description = "Default value for transparency/blending mode",
        items   = TransparencyEnumItems,
        default = 'OPAQUE'
    )

    def init_socket(self, node, socket, data_path):
        socket.default_value = self.default_value

    def from_socket(self, node, socket):
        self.default_value = socket.default_value

    def draw_color(self, context):
        return (1.0, 0.8, 0.4, 1.0)

class EdmDeckTransparencySocket(NodeSocket):
    bl_idname = 'EdmDeckTransparencySocketType'
    bl_label = "EDM Node Deck Transparency Socket"
    
    def update_value(self, context):             
        return None
    
    default_value: bpy.props.EnumProperty(
        name        = 'Transparency',
        description = "Transparency/blending mode",
        items       = DeckTransparencyEnumItems,
        update      = update_value
    )

    def draw(self, context, layout, node, text):
        if self.is_output or self.is_linked:
            layout.label(text=text)
        else:
            layout.prop(self, "default_value", text=text)

    def draw_color(self, context, node):
        return (1.0, 0.4, 0.216, 0.5)

class EdmDeckTransparencySocketInterface(InterfaceNodeSocket):
    bl_idname = "EdmDeckTransparencySocketInterface"
    bl_socket_idname = 'EdmDeckTransparencySocketType'
    bl_label = "DeckTransparencySocket"

    default_value: bpy.props.EnumProperty(
        name    = 'Transparency',
        description = "Default value for transparency/blending mode",
        items   = DeckTransparencyEnumItems,
        default = 'OPAQUE'
    )

    def init_socket(self, node, socket, data_path):
        socket.default_value = self.default_value
    
    # TODO: why 'node' parameter did not used?
    def from_socket(self, node, socket):
        self.default_value = socket.default_value

    def draw_color(self, context):
        return (1.0, 0.8, 0.4, 1.0)

class EdmEmissionTypeSocket(NodeSocket):
    bl_idname = 'EdmEmissionTypeSocketType'
    bl_label = "EDM Node Emission Type Socket"
    
    def update_value(self, context):             
        return None
    
    default_value: bpy.props.EnumProperty(
        name        = 'Self Illumination Type',
        description = "Illumination type",
        items       = EmissionEnumItems,
        update      = update_value
    )

    def draw(self, context, layout, node, text):
        if self.is_output or self.is_linked:
            layout.label(text=text)
        else:
            layout.prop(self, "default_value", text=text)

    def draw_color(self, context, node):
        return (1.0, 0.4, 0.216, 0.5)
    
class EdmEmissionTypeSocketInterface(InterfaceNodeSocket):
    bl_idname = "EdmEmissionTypeSocketInterface"
    bl_socket_idname = 'EdmEmissionTypeSocketType'
    bl_label = "EmissionTypeSocket"

    default_value: bpy.props.EnumProperty(
        name        = 'Self Illumination Type',
        description = "Default value for emission type",
        items       = EmissionEnumItems,
        default     = 'NONE'
    )

    def init_socket(self, node, socket, data_path):
        socket.default_value = self.default_value

    def from_socket(self, node, socket):
        self.default_value = socket.default_value

    def draw_color(self, context):
        return (1.0, 0.8, 0.4, 1.0)
    

def get_custom_sockets_classes():
    return [
        ## default material
        EdmShadowCasterSocket,
        EdmShadowCasterSocketInterface,
        EdmBidirectionalCasterSocket,
        EdmBidirectionalCasterSocketInterface,
        EdmTransparencySocket,
        EdmTransparencySocketInterface,
        ## deck material
        EdmDeckTransparencySocket,
        EdmDeckTransparencySocketInterface,
        ## glass material
        EdmGlassTypeSocket,
        EdmGlassTypeSocketInterface,
        EdmGlassTransparencySocket,
        EdmGlassTransparencySocketInterface,
        EdmGlassShadowCasterSocket,
        EdmGlassShadowCasterSocketInterface
    ]