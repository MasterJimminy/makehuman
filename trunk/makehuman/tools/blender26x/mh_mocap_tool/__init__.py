# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# Project Name:        MakeHuman
# Product Home Page:   http://www.makehuman.org/
# Code Home Page:      http://code.google.com/p/makehuman/
# Authors:             Thomas Larsson
# Script copyright (C) MakeHuman Team 2001-2011
# Coding Standards:    See http://sites.google.com/site/makehumandocs/developers-guide

"""
Abstract
Tool for loading bvh files onto the MHX rig in Blender 2.5x
Version 0.8

Place the script in the .blender/scripts/addons dir
Activate the script in the "Add-Ons" tab (user preferences).
Access from UI panel (N-key) when MHX rig is active.

Alternatively, run the script in the script editor (Alt-P), and access from UI panel.
"""

bl_info = {
    "name": "MHX Mocap",
    "author": "Thomas Larsson",
    "version": "0.9",
    "blender": (2, 6, 3),
    "api": 44000,
    "location": "View3D > Properties > MHX Mocap",
    "description": "Mocap tool for MHX rig",
    "warning": "",
    'wiki_url': 'http://sites.google.com/site/makehumandocs/blender-export-and-mhx/mocap-tool',
    "category": "MakeHuman"}

"""
Properties:
Scale:    
    for BVH import. Choose scale so that the vertical distance between hands and feet
    are the same for MHX and BVH rigs.
    Good values are: CMU: 0.6, OSU: 0.1
Start frame:    
    for BVH import
Rot90:    
    for BVH import. Rotate armature 90 degrees, so Z points up.
Simplify FCurves:    
    Include FCurve simplifcation.
Max loc error:    
    Max error allowed for simplification of location FCurves
Max rot error:    
    Max error allowed for simplification of rotation FCurves

Buttons:
Load BVH file (.bvh): 
    Load bvh file with Z up
Silence constraints:
    Turn off constraints that may conflict with mocap data.
Retarget selected to MHX: 
    Retarget actions of selected BVH rigs to the active MHX rig.
Simplify FCurves:
    Simplifiy FCurves of active action, allowing max errors specified above.
Load, retarget, simplify:
    Load bvh file, retarget the action to the active MHX rig, and simplify FCurves.
Batch run:
    Load all bvh files in the given directory, whose name start with the
    given prefix, and create actions (with simplified FCurves) for the active MHX rig.
"""

# To support reload properly, try to access a package var, if it's there, reload everything
if "bpy" in locals():
    print("Reloading Mocap tool")
    import imp
    imp.reload(source_rigs)
    imp.reload(target_rigs)
    imp.reload(utils)
    imp.reload(globvar)
    imp.reload(props)
    imp.reload(load)
    #imp.reload(old_retarget)
    imp.reload(new_retarget)
    imp.reload(source)
    imp.reload(target)
    imp.reload(toggle)
    imp.reload(simplify)
    imp.reload(action)
    imp.reload(loop)
    imp.reload(edit)
    imp.reload(plant)
    imp.reload(sigproc)
else:
    print("Loading Mocap tool")
    import bpy, os
    from bpy_extras.io_utils import ImportHelper
    from bpy.props import *

    from . import source_rigs
    from . import target_rigs
    from . import utils
    from . import globvar as the
    from . import props
    from . import load
    #from . import old_retarget
    from . import new_retarget
    from . import source
    from . import target
    from . import toggle
    from . import simplify
    from . import action
    from . import loop
    from . import edit
    from . import plant
    from . import sigproc


#        
#    class MhxSourceBonesPanel(bpy.types.Panel):
#

class MhxSourceBonesPanel(bpy.types.Panel):
    bl_label = "MH Mocap: Source armature"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {'DEFAULT_CLOSED'}
    
    @classmethod
    def poll(cls, context):
        return False
        return (context.object and context.object.type == 'ARMATURE')

    def draw(self, context):
        layout = self.layout
        scn = context.scene
        rig = context.object
        if the.sourceProps:
            layout.operator("mcp.scan_rig", text="Rescan source rig")    
        else:
            layout.operator("mcp.scan_rig", text="Scan source rig")    
        layout.operator("mcp.load_save_source_bones", text='Load source bones').loadSave = 'load'        
        layout.operator("mcp.load_save_source_bones", text='Save source bones').loadSave = 'save'        
        if not the.sourceProps:
            return
        layout.separator()
        layout.prop(scn, 'McpGuessSrcRig')
        layout.label("Arms")
        row = layout.row()
        row.prop(scn, '["McpSrcArmBentDown"]', text='Down')
        row.prop(scn, '["McpSrcArmRoll"]', text='Roll')
        layout.label("Legs")
        row = layout.row()
        row.prop(scn, '["McpSrcLegBentOut"]', text='Out')
        row.prop(scn, '["McpSrcLegRoll"]', text='Roll')
        for prop in the.sourceProps:
            layout.prop_menu_enum(scn, prop)

########################################################################
#        
#    class MhxTargetBonesPanel(bpy.types.Panel):
#

class MhxTargetBonesPanel(bpy.types.Panel):
    bl_label = "MH Mocap: Target armature"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {'DEFAULT_CLOSED'}
    
    @classmethod
    def poll(cls, context):
        return False
        return (context.object and context.object.type == 'ARMATURE')

    def draw(self, context):
        layout = self.layout
        rig = context.object
        try:
            inited = rig["McpTargetRig"]
        except:
            inited = False

        if not inited:
            layout.operator("mcp.init_target_character", text='Initialize target character')
            return

        layout.operator("mcp.init_target_character", text='Reinitialize target character')        
        layout.operator("mcp.uninit_target_character")        
        layout.operator("mcp.load_save_target_bones", text='Load target bones').loadSave = 'load'        
        layout.operator("mcp.load_save_target_bones", text='Save target bones').loadSave = 'save'        
        layout.operator("mcp.make_assoc")        
        layout.operator("mcp.unroll_all")        
        #layout.prop(rig, McpArmBentDown, text='Arm bent down')
        #layout.prop(rig, McpLegBentOut, text='Leg bent out')

        layout.label("FK bones")
        for bn in target.TargetBoneNames:
            if bn:
                (mhx, text) = bn
                layout.prop(rig, '["%s"]' % mhx, text=text)
            else:
                layout.separator()
        layout.label("IK bones")
        for (mhx, text, fakePar, copyRot) in target.TargetIkBoneNames:
            layout.prop(rig, '["%s"]' % mhx, text=text)
        return

########################################################################
#
#   class LoadPanel(bpy.types.Panel):
#

class LoadPanel(bpy.types.Panel):
    bl_label = "MH Mocap: Load BVH"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    #bl_options = {'DEFAULT_CLOSED'}
    
    @classmethod
    def poll(cls, context):
        if context.object and context.object.type == 'ARMATURE':
            return True

    def draw(self, context):
        layout = self.layout
        scn = context.scene
        ob = context.object

        row = layout.row()
        row.prop(scn, "McpAutoScale")
        row.prop(scn, "McpBvhScale")
        row = layout.row()
        row.prop(scn, "McpStartFrame")
        row.prop(scn, "McpEndFrame")
        #layout.prop(scn, 'McpGuessSrcRig')
        layout.prop(scn, "McpRetargetIK")
        layout.prop(scn, "McpDoSimplify")
        layout.prop(scn, "McpDefaultSS")
        row = layout.row()
        row.prop(scn, "McpUseSpineOffset")
        row.prop(scn, "McpUseClavOffset")
        layout.separator()
        layout.operator("mcp.load_and_retarget")

        layout.separator()
        layout.label("Load BVH skeleton")
        layout.prop(scn, "McpRot90Anim")
        layout.operator("mcp.load_bvh")
        layout.operator("mcp.rename_bvh")
        layout.operator("mcp.load_and_rename_bvh")

        layout.separator()
        layout.operator("mcp.new_retarget_mhx")

        layout.separator()
        layout.label("IK retargeting")
        layout.operator("mcp.retarget_ik")


        if not scn.McpDefaultSS:
            layout.separator()
            layout.label("SubSample")
            row = layout.row()
            row.prop(scn, "McpSubsample")
            row.prop(scn, "McpSSFactor")
            row = layout.row()
            row.prop(scn, "McpRescale")
            row.prop(scn, "McpRescaleFactor")
            layout.operator("mcp.rescale_fcurves")

        layout.separator()
        layout.label("Simplification")
        row = layout.row()
        row.prop(scn, "McpErrorLoc")
        row.prop(scn, "McpErrorRot")
        row = layout.row()
        row.prop(scn, "McpSimplifyVisible")
        row.prop(scn, "McpSimplifyMarkers")
        layout.operator("mcp.simplify_fcurves")
        
        return

        layout.separator()
        layout.label("Toggle constraints")
        row = layout.row()
        row.label("Limit constraints")
        if ob.McpLimitsOn:
            row.operator("mcp.toggle_limits", text="ON").mute=True
        else:
            row.operator("mcp.toggle_limits", text="OFF").mute=False
        row = layout.row()
        row.label("Child-of constraints")
        if ob.McpChildOfsOn:
            row.operator("mcp.toggle_childofs", text="ON").mute=True
        else:
            row.operator("mcp.toggle_childofs", text="OFF").mute=False


########################################################################
#
#   class EditPanel(bpy.types.Panel):
#

class EditPanel(bpy.types.Panel):
    bl_label = "MH Mocap: Edit Actions"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    #bl_options = {'DEFAULT_CLOSED'}
    
    @classmethod
    def poll(cls, context):
        if context.object and context.object.type == 'ARMATURE':
            return True

    def draw(self, context):
        layout = self.layout
        scn = context.scene
        ob = context.object

        layout.label("Plant keys")
        row = layout.row()
        row.label("Source")
        row.prop(scn, "McpPlantFrom", expand=True)
        row = layout.row()
        row.prop(scn, "McpPlantLocX")
        row.prop(scn, "McpPlantLocY")
        row.prop(scn, "McpPlantLocZ")
        row = layout.row()
        row.prop(scn, "McpPlantRotX")
        row.prop(scn, "McpPlantRotY")
        row.prop(scn, "McpPlantRotZ")
        layout.operator("mcp.plant")
        
        layout.separator()
        layout.label("Global Edit")
        layout.operator("mcp.shift_bone")

        layout.separator()
        layout.label("Displace Animation")
        layout.operator("mcp.start_edit")
        layout.operator("mcp.undo_edit")
        row = layout.row()
        row.operator("mcp.insert_loc")
        row.operator("mcp.insert_rot")
        row.operator("mcp.insert_locrot")
        layout.operator("mcp.confirm_edit")

        layout.separator()
        layout.label("Signal Processing")        
        layout.operator("mcp.calc_filters")
        try:
            fd = the.filterData[ob.name]
        except:
            fd = None
        if fd:
            for k in range(fd.fb-1):
                layout.prop(ob, s_%d % k)
            layout.operator("mcp.reconstruct_action")

        layout.separator()
        layout.label("Loop Animation")
        layout.prop(scn, "McpLoopBlendRange")
        row = layout.row()
        row.prop(scn, "McpLoopLoc")
        row.prop(scn, "McpLoopRot")
        layout.prop(scn, "McpLoopInPlace")
        if scn.McpLoopInPlace:
            layout.prop(scn, "McpLoopZInPlace")
        layout.operator("mcp.loop_fcurves")

        layout.separator()
        layout.label("Repeat Animation")
        layout.prop(scn, "McpRepeatNumber")
        layout.operator("mcp.repeat_fcurves")

        layout.separator()
        layout.label("Stitch Animations")        
        layout.operator("mcp.update_action_list")
        layout.prop(scn, "McpFirstAction")
        row = layout.row()
        row.prop(scn, "McpFirstEndFrame")
        row.operator("mcp.set_current_action").prop = "McpFirstAction"
        layout.prop(scn, "McpSecondAction")
        row = layout.row()
        row.prop(scn, "McpSecondStartFrame")
        row.operator("mcp.set_current_action").prop = "McpSecondAction"        
        layout.prop(scn, "McpActionTarget")
        layout.prop(scn, "McpOutputActionName")        
        layout.operator("mcp.stitch_actions")

########################################################################
#
#   class UlitityPanel(bpy.types.Panel):
#

class UlitityPanel(bpy.types.Panel):
    bl_label = "MH Mocap: Utilities"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {'DEFAULT_CLOSED'}    
    
    @classmethod
    def poll(cls, context):
        if context.object and context.object.type == 'ARMATURE':
            return True

    def draw(self, context):
        layout = self.layout
        scn = context.scene
        ob = context.object
        layout.label("Initialization")
        layout.operator("mcp.init_interface")
        layout.operator("mcp.save_defaults")
        layout.operator("mcp.load_defaults")

        layout.separator()
        layout.label("Manage Actions")
        layout.prop_menu_enum(context.scene, "McpActions")
        layout.prop(scn, 'McpFilterActions')
        layout.operator("mcp.update_action_list")
        layout.operator("mcp.set_current_action").prop = 'McpActions'
        layout.prop(scn, "McpReallyDelete")
        layout.operator("mcp.delete")
        layout.operator("mcp.delete_hash")

        return
        layout.operator("mcp.copy_angles_fk_ik")

        layout.separator()
        layout.label("Batch conversion")
        layout.prop(scn, "McpDirectory")
        layout.prop(scn, "McpPrefix")
        layout.operator("mcp.batch")

#
#    Debugging
#
"""
def debugOpen():
    global theDbgFp
    theDbgFp = open("/home/thomas/myblends/debug.txt", "w")

def debugClose():
    global theDbgFp
    theDbgFp.close()

def debugPrint(string):
    global theDbgFp
    theDbgFp.write("%s\n" % string)

def debugPrintVec(vec):
    global theDbgFp
    theDbgFp.write("(%.3f %.3f %.3f)\n" % (vec[0], vec[1], vec[2]))

def debugPrintVecVec(vec1, vec2):
    global theDbgFp
    theDbgFp.write("(%.3f %.3f %.3f) (%.3f %.3f %.3f)\n" %
        (vec1[0], vec1[1], vec1[2], vec2[0], vec2[1], vec2[2]))
"""

#
#    init 
#

props.initInterface(bpy.context)

def register():
    bpy.utils.register_module(__name__)

def unregister():
    bpy.utils.unregister_module(__name__)

if __name__ == "__main__":
    register()

