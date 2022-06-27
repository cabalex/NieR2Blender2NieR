bl_info = {
    "name": "Nier2Blender2NieR (NieR:Automata Data Exporter)",
    "author": "Woeful_Wolf",
    "version": (0, 3, 0),
    "blender": (2, 80, 0),
    "description": "Import/Export NieR:Automata WMB/WTP/WTA/DTT/DAT/COL files.",
    "category": "Import-Export"}

import traceback

import bpy
import os
from bpy.props import StringProperty
from bpy_extras.io_utils import ExportHelper, ImportHelper

from . import util
from .col.exporter import col_ui_manager, col_exporter
from .dat_dtt.exporter import dat_dtt_ui_manager
from .wta_wtp.exporter import wta_wtp_ui_manager


class ExportBlender2NieRLay(bpy.types.Operator, ExportHelper):
    '''Export a NieR:Automata LAY File'''
    bl_idname = "export.lay_data"
    bl_label = "Export LAY File"
    bl_options = {'PRESET'}
    filename_ext = ".lay"
    filter_glob: StringProperty(default="*.lay", options={'HIDDEN'})

    def execute(self, context):
        from .lay.exporter import lay_exporter

        lay_exporter.main(self.filepath)
        return {'FINISHED'}

class ExportBlender2NieRCol(bpy.types.Operator, ExportHelper):
    '''Export a NieR:Automata COL File'''
    bl_idname = "export.col_data"
    bl_label = "Export COL File"
    bl_options = {'PRESET'}
    filename_ext = ".col"
    filter_glob: StringProperty(default="*.col", options={'HIDDEN'})

    generateColTree: bpy.props.BoolProperty(name="Generate Collision Tree", description="This automatically generates colTreeNodes based on your geometry and assignes the right meshes to the right colTreeNodes. Only disable it if you are manually adjusting them", default=True)
    centre_origins: bpy.props.BoolProperty(name="Centre Origins", description="This automatically centres the origins of all your objects. (Recommended)", default=True)
    triangluate_meshes: bpy.props.BoolProperty(name="Triangulate Meshes", description="This automatically adds and applies the Triangulate Modifier on all your objects. (Slow)", default=True)

    def execute(self, context):

        if self.centre_origins:
            print("Centering origins...")
            col_exporter.centre_origins()

        if self.triangluate_meshes:
            print("Triangulating meshes...")
            col_exporter.triangulate_meshes() 

        col_exporter.main(self.filepath, self.generateColTree)
        return {'FINISHED'}

class ExportBlender2NieR(bpy.types.Operator, ExportHelper):
    '''Export a NieR:Automata WMB File'''
    bl_idname = "export.wmb_data"
    bl_label = "Export WMB File"
    bl_options = {'PRESET'}
    filename_ext = ".wmb"
    filter_glob: StringProperty(default="*.wmb", options={'HIDDEN'})

    centre_origins: bpy.props.BoolProperty(name="Centre Origins", description="This automatically centres the origins of all your objects. (Recommended)", default=True)
    #purge_materials: bpy.props.BoolProperty(name="Purge Materials", description="This permanently removes all unused materials from the .blend file before exporting. Enable if you have invalid materials remaining in your project", default=False)
    triangluate_meshes: bpy.props.BoolProperty(name="Triangulate Meshes", description="This automatically adds and applies the Triangulate Modifier on all your objects. Only disable if you know your meshes are triangulated and you wish to reduce export times", default=True)
    delete_loose_geometry: bpy.props.BoolProperty(name="Delete Loose Geometry", description="This automatically runs the Blender2NieR 'Delete Loose Geometry (All)' operator before exporting. It deletes all loose vertices or edges that could result in unwanted results in-game", default=True)

    def execute(self, context):
        from .wmb.exporter import wmb_exporter
        from . import util
        
        bpy.data.collections['WMB'].all_objects[0].select_set(True)

        if self.centre_origins:
            print("Centering origins...")
            wmb_exporter.centre_origins()

        """
        if self.purge_materials:
            print("Purging materials...")
            wmb_exporter.purge_unused_materials()
        """

        if self.triangluate_meshes:
            print("Triangulating meshes...")
            wmb_exporter.triangulate_meshes() 

        if self.delete_loose_geometry:
            print("Deleting loose geometry...")
            bpy.ops.b2n.deleteloosegeometryall()
        
        try:
            print("Starting export...")
            wmb_exporter.main(self.filepath)
            return wmb_exporter.restore_blend()
        except:
            print(traceback.format_exc())
            util.show_message('Error: An unexpected error has occurred during export. Please check the console for more info.', 'WMB Export Error', 'ERROR')
            return {'CANCELLED'}

class B2NObjectMenu(bpy.types.Menu):
    bl_idname = 'OBJECT_MT_b2n'
    bl_label = 'Nier2Blender2NieR'
    def draw(self, context):
        self.layout.operator(util.B2NRecalculateObjectIndices.bl_idname)
        self.layout.operator(util.B2NRemoveUnusedVertexGroups.bl_idname)
        self.layout.operator(util.B2NMergeVertexGroupCopies.bl_idname)
        self.layout.operator(util.B2NDeleteLooseGeometrySelected.bl_idname)
        self.layout.operator(util.B2NDeleteLooseGeometryAll.bl_idname)
        self.layout.operator(util.B2NRipMeshByUVIslands.bl_idname)
        pcoll = preview_collections["main"]
        yorha_icon = pcoll["yorha"]
        self.layout.menu(N2BLayoutObjectMenu.bl_idname, icon_value=yorha_icon.icon_id)


class ImportNier2blender(bpy.types.Operator, ImportHelper):
    '''Load a Nier:Automata WMB File.'''
    bl_idname = "import_scene.wmb_data"
    bl_label = "Import WMB Data"
    bl_options = {'PRESET'}
    filename_ext = ".wmb"
    filter_glob: StringProperty(default="*.wmb", options={'HIDDEN'})

    reset_blend: bpy.props.BoolProperty(name="Reset Blender Scene on Import", default=True)

    def execute(self, context):
        from .wmb.importer import wmb_importer
        if self.reset_blend:
            wmb_importer.reset_blend()
        return wmb_importer.main(False, self.filepath)

def importDat(only_extract, filepath):
    head = os.path.split(filepath)[0]
    tail = os.path.split(filepath)[1]
    tailless_tail = tail[:-4]
    dat_filepath = head + '\\' + tailless_tail + '.dat'
    extract_dir = head + '\\nier2blender_extracted'
    from .dat_dtt.importer import dat_unpacker
    if os.path.isfile(dat_filepath):
        dat_unpacker.main(dat_filepath, extract_dir + '\\' + tailless_tail + '.dat', dat_filepath)   # dat
    else:
        print('DAT not found. Only extracting DTT. (No materials, collisions or layouts will automatically be imported)')

    last_filename = dat_unpacker.main(filepath, extract_dir + '\\' + tailless_tail + '.dtt', filepath)       # dtt

    wmb_filepath = extract_dir + '\\' + tailless_tail + '.dtt\\' + last_filename[:-4] + '.wmb'
    if not os.path.exists(wmb_filepath):
        wmb_filepath = extract_dir + '\\' + tailless_tail + '.dat\\' + last_filename[:-4] + '.wmb'                     # if not in dtt, then must be in dat

    # WMB
    from .wmb.importer import wmb_importer
    wmb_importer.main(only_extract, wmb_filepath)

    if only_extract:
        return {'FINISHED'}

    # COL
    col_filepath = extract_dir + '\\' + tailless_tail + '.dat\\' + tailless_tail + '.col'
    if os.path.isfile(col_filepath):
        from .col.importer import col_importer
        col_importer.main(col_filepath)

    # LAY
    lay_filepath = extract_dir + '\\' + tailless_tail + '.dat\\' + 'Layout.lay'
    if os.path.isfile(lay_filepath):
        from .lay.importer import lay_importer
        lay_importer.main(lay_filepath, __name__)

    return {'FINISHED'}

class ImportDATNier2blender(bpy.types.Operator, ImportHelper):
    '''Load a Nier:Automata DTT (and DAT) File.'''
    bl_idname = "import_scene.dtt_data"
    bl_label = "Import DTT (and DAT) Data"
    bl_options = {'PRESET'}
    filename_ext = ".dtt"
    filter_glob: StringProperty(default="*.dtt", options={'HIDDEN'})

    reset_blend: bpy.props.BoolProperty(name="Reset Blender Scene on Import", default=True)
    bulk_import: bpy.props.BoolProperty(name="Bulk Import All DTT/DATs In Folder (Experimental)", default=False)
    only_extract: bpy.props.BoolProperty(name="Only Extract DTT/DAT Contents. (Experimental)", default=False)

    def execute(self, context):
        from .wmb.importer import wmb_importer
        if self.reset_blend and not self.only_extract:
            wmb_importer.reset_blend()
        if self.bulk_import:
            folder = os.path.split(self.filepath)[0]
            for filename in os.listdir(folder):
                if filename[-4:] == '.dtt':
                    try:
                        filepath = folder + '\\' + filename
                        importDat(self.only_extract, filepath)
                    except:
                        print('ERROR: FAILED TO IMPORT', filename)
            return {'FINISHED'}

        else:
            return importDat(self.only_extract, self.filepath)

class ImportActualDATNier2blender(bpy.types.Operator, ImportHelper):
    '''Load a Nier:Automata DAT File.'''
    bl_idname = "import_scene.dat_data"
    bl_label = "Import DAT Data"
    bl_options = {'PRESET'}
    filename_ext = ".dat"
    filter_glob: StringProperty(default="*.dat", options={'HIDDEN'})

    reset_blend: bpy.props.BoolProperty(name="Reset Blender Scene on Import", default=True)
    bulk_import: bpy.props.BoolProperty(name="Bulk Import All DTT/DATs In Folder (Experimental)", default=False)
    only_extract: bpy.props.BoolProperty(name="Only Extract DTT/DAT Contents. (Experimental)", default=False)

    def doImport(self, onlyExtract, filepath):
        head = os.path.split(filepath)[0]
        tail = os.path.split(filepath)[1]
        tailless_tail = tail[:-4]
        dat_filepath = head + '\\' + tailless_tail + '.dat'
        extract_dir = head + '\\nier2blender_extracted'
        from .dat_dtt.importer import dat_unpacker
        if os.path.isfile(dat_filepath):
            dat_unpacker.main(dat_filepath, extract_dir + '\\' + tailless_tail + '.dat', dat_filepath)   # dat

        if onlyExtract:
            return {'FINISHED'}

        # COL
        col_filepath = extract_dir + '\\' + tailless_tail + '.dat\\' + tailless_tail + '.col'
        if os.path.isfile(col_filepath):
            from .col.importer import col_importer
            col_importer.main(col_filepath)

        # LAY
        lay_filepath = extract_dir + '\\' + tailless_tail + '.dat\\' + 'Layout.lay'
        if os.path.isfile(lay_filepath):
            from .lay.importer import lay_importer
            lay_importer.main(lay_filepath, __name__)

        return {'FINISHED'}

    def execute(self, context):
        from .wmb.importer import wmb_importer
        if self.reset_blend and not self.only_extract:
            wmb_importer.reset_blend()
        if self.bulk_import:
            folder = os.path.split(self.filepath)[0]
            for filename in os.listdir(folder):
                if filename[-4:] == '.dat':
                    try:
                        filepath = folder + '\\' + filename
                        return self.doImport(self.only_extract, filepath)
                    except:
                        print('ERROR: FAILED TO IMPORT', filename)
            return {'FINISHED'}

        else:
            return self.doImport(self.only_extract, self.filepath)

class ImportColNier2Blender(bpy.types.Operator, ImportHelper):
    '''Load a Nier:Automata Col (Collision) File.'''
    bl_idname = "import_scene.col_data"
    bl_label = "Import Col Data"
    bl_options = {'PRESET'}
    filename_ext = ".col"
    filter_glob: StringProperty(default="*.col", options={'HIDDEN'})

    def execute(self, context):
        from .col.importer import col_importer
        return col_importer.main(self.filepath)

class ImportLayNier2Blender(bpy.types.Operator, ImportHelper):
    '''Load a Nier:Automata Lay (Layout) File.'''
    bl_idname = "import_scene.lay_data"
    bl_label = "Import Lay Data"
    bl_options = {'PRESET'}
    filename_ext = ".lay"
    filter_glob: StringProperty(default="*.lay", options={'HIDDEN'})

    def execute(self, context):
        from .lay.importer import lay_importer
        return lay_importer.main(self.filepath, __name__)

class SelectDirectory(bpy.types.Operator, ImportHelper):
    '''Select Directory'''
    bl_idname = "n2b.folder_select"
    bl_label = "Select Directory"
    filename_ext = ""
    dirpath : StringProperty(name = "", description="Choose directory:", subtype='DIR_PATH')

    target : bpy.props.StringProperty(options={'HIDDEN'})

    def execute(self, context):
        directory = os.path.dirname(self.filepath)
        if self.target == "data005":
            context.preferences.addons[__name__].preferences.data005_dir = directory
        elif self.target == "data015":
            context.preferences.addons[__name__].preferences.data015_dir = directory
        else:
            print("Invalid target", self.target)
            return {"CANCELLED"}

        return {'FINISHED'}

class NieR2BlenderPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__
    data005_dir : StringProperty(options={'HIDDEN'})
    data015_dir : StringProperty(options={'HIDDEN'})

    def draw(self, context):
        layout = self.layout
        
        layout.label(text="Assign Directories Below If You Wish To Enable Bounding Box Visualization With Layout Import:")
        box = layout.box()
        box.label(text="Path To Extracted data005.cpk Directory:")
        row = box.row(align=True)
        row.prop(self, "data005_dir", text="")
        row.operator("n2b.folder_select", icon="FILE_FOLDER", text="").target = "data005"

        box.label(text="Path To Extracted data015.cpk Directory:")
        row = box.row(align=True)
        row.prop(self, "data015_dir", text="")
        row.operator("n2b.folder_select", icon="FILE_FOLDER", text="").target = "data015"

class NieR2BlenderCreateObjBBox(bpy.types.Operator):
    """Create Layout Object Bounding Box"""
    bl_idname = "n2b.create_lay_bb"
    bl_label = "Create Layout Object Bounding Box"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        from .lay.importer.lay_importer import getModelBoundingBox, createBoundingBoxObject
        for obj in bpy.context.selected_objects:
            boundingBox = getModelBoundingBox(obj.name.split("_")[0], __name__)
            if boundingBox:
                createBoundingBoxObject(obj, obj.name + "-BoundingBox", bpy.data.collections.get("lay_layAssets"), boundingBox)
            else:
                self.report({'WARNING'}, "Couldn't find dtt of " + obj.name)
        return {'FINISHED'}

class N2BLayoutObjectMenu(bpy.types.Menu):
    bl_idname = 'OBJECT_MT_n2blayout'
    bl_label = 'NieR2Blender'
    def draw(self, context):
        self.layout.operator(NieR2BlenderCreateObjBBox.bl_idname, icon="CUBE")

def menu_func_import(self, context):
    pcoll = preview_collections["main"]
    yorha_icon = pcoll["yorha"]
    self.layout.operator(ImportDATNier2blender.bl_idname, text="DTT File for Nier:Automata (.dtt)", icon_value=yorha_icon.icon_id)
    self.layout.operator(ImportNier2blender.bl_idname, text="WMB File for Nier:Automata (.wmb)", icon_value=yorha_icon.icon_id)
    self.layout.operator(ImportActualDATNier2blender.bl_idname, text="DAT File for Nier:Automata (col+lay) (.dat)", icon_value=yorha_icon.icon_id)
    self.layout.operator(ImportColNier2Blender.bl_idname, text="Collision File for Nier:Automata (.col)", icon_value=yorha_icon.icon_id)
    self.layout.operator(ImportLayNier2Blender.bl_idname, text="Layout File for Nier:Automata (.lay)", icon_value=yorha_icon.icon_id)

def menu_func_export(self, context):
    pcoll = preview_collections["main"]
    emil_icon = pcoll["emil"]
    self.layout.operator_context = 'INVOKE_DEFAULT'
    self.layout.operator(ExportBlender2NieR.bl_idname, text="WMB File for NieR:Automata (.wmb)", icon_value=emil_icon.icon_id)
    self.layout.operator(ExportBlender2NieRCol.bl_idname, text="Collision File for NieR:Automata (.col)", icon_value=emil_icon.icon_id)
    self.layout.operator(ExportBlender2NieRLay.bl_idname, text="Layout File for NieR:Automata (.lay)", icon_value=emil_icon.icon_id)

def menu_func_utils(self, context):
    self.layout.menu(B2NObjectMenu.bl_idname)

classes = (
    ImportNier2blender,
    ImportDATNier2blender,
    ImportActualDATNier2blender,
    ImportColNier2Blender,
    ImportLayNier2Blender,
    SelectDirectory,
    NieR2BlenderPreferences,
    NieR2BlenderCreateObjBBox,
    N2BLayoutObjectMenu,
    ExportBlender2NieR,
    ExportBlender2NieRCol,
    ExportBlender2NieRLay,
    B2NObjectMenu,
    util.B2NRecalculateObjectIndices,
    util.B2NRemoveUnusedVertexGroups,
    util.B2NMergeVertexGroupCopies,
    util.B2NDeleteLooseGeometrySelected,
    util.B2NDeleteLooseGeometryAll,
    util.B2NRipMeshByUVIslands,
)

preview_collections = {}


def register():
    # Custom icons
    import bpy.utils.previews
    pcoll = bpy.utils.previews.new()
    my_icons_dir = os.path.join(os.path.dirname(__file__), "icons")
    pcoll.load("emil", os.path.join(my_icons_dir, "emil.png"), 'IMAGE')
    pcoll.load("yorha", os.path.join(my_icons_dir, "yorha-filled.png"), 'IMAGE')
    preview_collections["main"] = pcoll

    for cls in classes:
        bpy.utils.register_class(cls)

    wta_wtp_ui_manager.register()
    dat_dtt_ui_manager.register()
    col_ui_manager.register()
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)
    bpy.types.VIEW3D_MT_object.append(menu_func_utils)

    bpy.types.Object.collisionType = bpy.props.EnumProperty(name="Collision Type", items=collisionTypes, update=updateCollisionType)
    bpy.types.Object.UNKNOWN_collisionType = bpy.props.IntProperty(name="Unknown Collision Type", min=0, max=255, update=updateCollisionType)
    bpy.types.Object.slidable = bpy.props.BoolProperty(name="Slidable/Modifier")
    bpy.types.Object.surfaceType = bpy.props.EnumProperty(name="Surface Type", items=surfaceTypes)

def unregister():
    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    preview_collections.clear()

    for cls in classes:
        bpy.utils.unregister_class(cls)

    wta_wtp_ui_manager.unregister()
    dat_dtt_ui_manager.unregister()
    col_ui_manager.unregister()
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    bpy.types.VIEW3D_MT_object.remove(menu_func_utils)

if __name__ == '__main__':
    register()


## Extras
def setColourByCollisionType(obj):
    opacity = 1.0
    collisionType = int(obj.collisionType)
    if collisionType == 127:
        obj.color = [0.0, 1.0, 0.0, opacity]
    elif collisionType == 88:
        obj.color = [0.0, 0.5, 1.0, opacity]
    elif collisionType == 3:
        obj.color = [1.0, 0.5, 0.0, opacity]
    elif collisionType == 255:
        obj.color = [1.0, 0.0, 0.0, opacity]
    else:
        obj.color = [1.0, 0.45, 1.0, opacity]

def updateCollisionType(self, context):
    setColourByCollisionType(self)

collisionTypes = [
    ("-1", "UNKNOWN", ""),
    ("3", "Block Actors", "If modifier is enabled, this will not block players who are jumping (e.g. to prevent accidentally walking off ledges)."),
    ("88", "Water", ""),
    ("127", "Grabbable Block All", ""),
    ("255", "Block All", "")
]

# Identified by NSA Cloud
surfaceTypes = [
    ("-1", "UNKNOWN", ""),
    ("0", "Concrete1", ""),
    ("1", "Dirt", ""),
    ("2", "Concrete2", ""),
    ("3", "Metal Floor", ""),
    ("4", "Rubble", ""),
    ("5", "Metal Grate", ""),
    ("6", "Gravel", ""),
    ("7", "Rope Bridge", ""),
    ("8", "Grass", ""),
    ("9", "Wood Plank", ""),
    ("11", "Water", ""),
    ("12", "Sand", ""),
    ("13", "Rocky Gravel 1", ""),
    ("15", "Mud", ""),
    ("16", "Rocky Gravel 2", ""),
    ("17", "Concrete 3", ""),
    ("18", "Bunker Floor", ""),
    ("22", "Concrete 4", ""),
    ("23", "Car", ""),
    ("24", "Flowers", "")
]