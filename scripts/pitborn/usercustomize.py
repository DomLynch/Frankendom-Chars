import bpy

class PitbornEeveeAlias(bpy.types.RenderEngine):
    bl_idname = "BLENDER_EEVEE_NEXT"
    bl_label = "Pitborn Eevee compatibility alias"

    def render(self, depsgraph):
        scene = bpy.context.scene
        scene.render.engine = "BLENDER_EEVEE"
        bpy.ops.render.render(write_still=True)

try:
    bpy.utils.register_class(PitbornEeveeAlias)
except Exception:
    pass
