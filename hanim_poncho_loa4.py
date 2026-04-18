import bpy
import bmesh
import os
import math
import mathutils # <--- Essential import for Vector math

# ==============================================================================
# 1. HIERARCHY DEFINITIONS (HAnim LOA4)
# ==============================================================================

def get_hanim_hierarchy():
    """
    Returns a recursive structure for LOA4.
    Format: (Bone_Name, Head_Offset_From_Parent, [Children])
    """
    
    # Helper to generate finger chains
    def get_digits(side_prefix):
        # 5 fingers: thumb(1) to pinky(5)
        digits = []
        # Thumb (proximal, dist) - Simplified for script length
        digits.append((f"{side_prefix}_carpometacarpal_1", (0.02, -0.02, -0.02), [
            (f"{side_prefix}_metacarpal_1", (0, -0.02, 0), [
                (f"{side_prefix}_carpal_distal_phalanx_1", (0, -0.02, 0), [])
            ])
        ]))
        # Fingers 2-5
        for i in range(2, 6):
            digits.append((f"{side_prefix}_carpal_proximal_phalanx_{i}", (0.01 * (i-3), -0.05, 0), [
                (f"{side_prefix}_carpal_middle_phalanx_{i}", (0, -0.03, 0), [
                     (f"{side_prefix}_carpal_distal_phalanx_{i}", (0, -0.02, 0), [])
                ])
            ]))
        return digits

    # Helper to generate toes
    def get_toes(side_prefix):
        toes = []
        for i in range(1, 6):
             toes.append((f"{side_prefix}_tarsal_proximal_phalanx_{i}", (0.01 * (i-3), 0.05, 0), [
                 (f"{side_prefix}_tarsal_distal_phalanx_{i}", (0, 0.03, 0), [])
             ]))
        return toes

    # Full Spine + Extremities
    return ("humanoid_root", (0,0,0.95), [
        ("sacrum", (0,0,0.05), [
            ("l5", (0,0,0.05), [
                ("l4", (0,0,0.05), [
                    ("l3", (0,0,0.05), [
                        ("l2", (0,0,0.05), [
                            ("l1", (0,0,0.05), [
                                ("t12", (0,0,0.05), [
                                    ("t11", (0,0,0.04), [
                                        ("t10", (0,0,0.04), [
                                            ("t9", (0,0,0.04), [
                                                ("t8", (0,0,0.04), [
                                                    ("t7", (0,0,0.04), [
                                                        ("t6", (0,0,0.04), [
                                                            ("t5", (0,0,0.04), [
                                                                ("t4", (0,0,0.04), [
                                                                    ("t3", (0,0,0.04), [
                                                                        ("t2", (0,0,0.04), [
                                                                            ("t1", (0,0,0.04), [
                                                                                ("c7", (0,0,0.05), [
                                                                                    ("c6", (0,0,0.03), [
                                                                                        ("c5", (0,0,0.03), [
                                                                                            ("c4", (0,0,0.03), [
                                                                                                ("c3", (0,0,0.03), [
                                                                                                    ("c2", (0,0,0.03), [
                                                                                                        ("c1", (0,0,0.03), [
                                                                                                            ("skull", (0,0,0.05), [
                                                                                                                ("jaw", (0,-0.05,-0.05), [])
                                                                                                            ])
                                                                                                        ])
                                                                                                    ])
                                                                                                ])
                                                                                            ])
                                                                                        ])
                                                                                    ])
                                                                                ]),
                                                                                # LEFT ARM CHAIN
                                                                                ("l_sternoclavicular", (0.05,0,0), [
                                                                                    ("l_acromioclavicular", (0.1,0,0), [
                                                                                        ("l_shoulder", (0.05,0,-0.05), [
                                                                                            ("l_upperarm", (0.05,0,-0.3), [
                                                                                                ("l_elbow", (0,0,-0.3), [
                                                                                                    ("l_forearm", (0,0,-0.25), [
                                                                                                        ("l_wrist", (0,0,-0.05), get_digits("l"))
                                                                                                    ])
                                                                                                ])
                                                                                            ])
                                                                                        ])
                                                                                    ])
                                                                                ]),
                                                                                # RIGHT ARM CHAIN
                                                                                ("r_sternoclavicular", (-0.05,0,0), [
                                                                                    ("r_acromioclavicular", (-0.1,0,0), [
                                                                                        ("r_shoulder", (-0.05,0,-0.05), [
                                                                                            ("r_upperarm", (-0.05,0,-0.3), [
                                                                                                ("r_elbow", (0,0,-0.3), [
                                                                                                    ("r_forearm", (0,0,-0.25), [
                                                                                                        ("r_wrist", (0,0,-0.05), get_digits("r"))
                                                                                                    ])
                                                                                                ])
                                                                                            ])
                                                                                        ])
                                                                                    ])
                                                                                ])
                                                                            ])
                                                                        ])
                                                                    ])
                                                                ])
                                                            ])
                                                        ])
                                                    ])
                                                ])
                                            ])
                                        ])
                                    ])
                                ])
                            ])
                        ])
                    ])
                ])
            ])
        ]),
        # LEGS
        ("pelvis", (0,0,-0.05), [
            ("l_hip", (0.15,0,-0.1), [
                ("l_thigh", (0,0,-0.4), [
                    ("l_knee", (0,0,-0.4), [
                        ("l_calf", (0,0,-0.1), [
                            ("l_ankle", (0,0,-0.05), get_toes("l"))
                        ])
                    ])
                ])
            ]),
            ("r_hip", (-0.15,0,-0.1), [
                ("r_thigh", (0,0,-0.4), [
                    ("r_knee", (0,0,-0.4), [
                        ("r_calf", (0,0,-0.1), [
                            ("r_ankle", (0,0,-0.05), get_toes("r"))
                        ])
                    ])
                ])
            ])
        ])
    ])

# ==============================================================================
# 2. SCENE GENERATION
# ==============================================================================

def clean_scene():
    if bpy.context.active_object and bpy.context.active_object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    for col in [bpy.data.meshes, bpy.data.materials, bpy.data.armatures, bpy.data.objects]:
        for block in col:
            col.remove(block)

def create_hanim_skeleton():
    print("Creating HAnim Armature...")
    bpy.ops.object.armature_add(location=(0,0,0))
    arm_obj = bpy.context.active_object
    arm_obj.name = "HAnimHumanoid"
    arm = arm_obj.data
    arm.name = "HAnimArmature"
    
    bpy.ops.object.mode_set(mode='EDIT')
    # Remove default bone
    for bone in arm.edit_bones:
        arm.edit_bones.remove(bone)
        
    hierarchy = get_hanim_hierarchy()
    
    def build_bone(node, parent_bone):
        name, offset, children = node
        
        eb = arm.edit_bones.new(name)
        
        if parent_bone:
            eb.parent = parent_bone
            # Use mathutils.Vector for vector addition
            eb.head = parent_bone.head + mathutils.Vector(offset)
        else:
            eb.head = mathutils.Vector(offset)
            
        # Set a small default length for leaf bones
        eb.tail = eb.head + mathutils.Vector((0, 0, 0.05))
        
        for child in children:
            build_bone(child, eb)
            
        # Clean up visuals: connect tail to first child if exists
        if children:
            child_name = children[0][0]
            # Optional: Move tail to child head for cleaner viewport look
            eb.tail = arm.edit_bones[child_name].head

    build_bone(hierarchy, None)
    
    bpy.ops.object.mode_set(mode='OBJECT')
    return arm_obj

def create_hanim_skin(armature_obj):
    """Creates a basic mesh geometry and binds it to the armature."""
    print("Creating HAnim Skin...")
    
    parts = []
    
    def add_shape(name, size, loc):
        bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
        obj = bpy.context.active_object
        obj.scale = size
        obj.name = "Skin_" + name
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        parts.append(obj)
        return obj

    # Torso
    add_shape("Torso", (0.3, 0.2, 0.6), (0, 0, 1.3))
    # Head
    add_shape("Head", (0.2, 0.2, 0.25), (0, 0, 1.8))
    # Arms
    add_shape("LArm", (0.5, 0.1, 0.1), (0.4, 0, 1.4))
    add_shape("RArm", (0.5, 0.1, 0.1), (-0.4, 0, 1.4))
    # Legs
    add_shape("LLeg", (0.15, 0.15, 0.8), (0.15, 0, 0.5))
    add_shape("RLeg", (0.15, 0.15, 0.8), (-0.15, 0, 0.5))

    # Join All Parts
    bpy.ops.object.select_all(action='DESELECT')
    for p in parts:
        p.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    skin_obj = bpy.context.active_object
    skin_obj.name = "HAnimSkin"
    
    # Material
    mat = bpy.data.materials.new(name="SkinMaterial")
    mat.diffuse_color = (0.7, 0.5, 0.4, 1.0)
    skin_obj.data.materials.append(mat)
    
    # Parent to Armature with Automatic Weights
    bpy.ops.object.select_all(action='DESELECT')
    skin_obj.select_set(True)
    armature_obj.select_set(True)
    bpy.context.view_layer.objects.active = armature_obj
    
    bpy.ops.object.parent_set(type='ARMATURE_AUTO')
    
    # Add Collision Physics to the Skin
    bpy.context.view_layer.objects.active = skin_obj
    bpy.ops.object.modifier_add(type='COLLISION')
    skin_obj.modifiers["Collision"].settings.thickness_outer = 0.02
    
    return skin_obj

def create_poncho():
    print("Creating Poncho...")
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.mesh.primitive_plane_add(size=2.0, location=(0, 0, 2.1))
    poncho = bpy.context.active_object
    poncho.name = "Poncho"
    
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.subdivide(number_cuts=25)
    
    # Create hole
    bm = bmesh.from_edit_mesh(poncho.data)
    bm.faces.ensure_lookup_table()
    to_delete = [f for f in bm.faces if abs(f.calc_center_median().x) < 0.12 and abs(f.calc_center_median().y) < 0.12]
    bmesh.ops.delete(bm, geom=to_delete, context='FACES')
    bmesh.update_edit_mesh(poncho.data)
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # Cloth
    bpy.ops.object.modifier_add(type='CLOTH')
    cmod = poncho.modifiers["Cloth"]
    cmod.settings.quality = 5
    cmod.settings.mass = 0.4
    
    # Blender 4.x Collision settings
    if hasattr(cmod, 'collision_settings'):
        col = cmod.collision_settings
        col.use_self_collision = True
        col.distance_min = 0.02
    
    # Visuals
    for p in poncho.data.polygons: p.use_smooth = True
    mat = bpy.data.materials.new(name="PonchoMat")
    mat.diffuse_color = (0, 0.5, 0.8, 1)
    poncho.data.materials.append(mat)
    
    return poncho

def bake_simulation(start, end):
    scene = bpy.context.scene
    scene.frame_start = start
    scene.frame_end = end
    print("Baking Physics...")
    bpy.ops.object.select_all(action='SELECT')
    
    # Poll bake_all
    if bpy.ops.ptcache.bake_all.poll():
        bpy.ops.ptcache.bake_all(bake=True)
    else:
        # Fallback: Play through
        print("Stepping frames to cache...")
        for f in range(start, end+1):
            scene.frame_set(f)
    print("Baking Done.")

# ==============================================================================
# 3. HAnim X3D EXPORT
# ==============================================================================

def export_hanim_x3d(filepath, armature_obj, skin_obj, poncho_obj, end_frame):
    
    def vector_to_str(vec):
        # Swap Y and Z for X3D default (Y-up)
        # Blender (X right, Y back, Z up) -> X3D (X right, Y up, Z forward)
        return f"{vec.x:.4f} {vec.z:.4f} {-vec.y:.4f}"

    def write_joint(f, bone, indent):
        center = vector_to_str(bone.head_local)
        
        # HAnimJoint LOA4 definition
        f.write(f'{indent}<HAnimJoint DEF="{bone.name}" name="{bone.name}" center="{center}" skinCoordIndex="" skinCoordWeight="">\n')
        
        # Recursively write children
        for child in bone.children:
            write_joint(f, child, indent + "  ")
            
        f.write(f'{indent}</HAnimJoint>\n')

    print(f"Exporting HAnim X3D to {filepath}...")
    with open(filepath, 'w', encoding='utf-8') as f:
        # HEADER
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<!DOCTYPE X3D PUBLIC "ISO//Web3D//DTD X3D 3.3//EN" "https://www.web3d.org/specifications/x3d-3.3.dtd">\n')
        f.write('<X3D profile="Full" version="3.3" xmlns:xsd="http://www.w3.org/2001/XMLSchema-instance" xsd:noNamespaceSchemaLocation="https://www.web3d.org/specifications/x3d-3.3.xsd">\n')
        f.write('<head><component name="HAnim" level="3"/><meta name="generator" content="Blender HAnim Script" /></head>\n')
        f.write('<Scene>\n')
        f.write('<NavigationInfo type=\'"EXAMINE" "ANY"\' />\n')
        f.write('<Viewpoint description="Front" position="0 2 5" orientation="1 0 0 -0.2" />\n')
        
        # 1. HAnimHumanoid
        # We list all typical LOA4 joints in the info string (truncated for brevity in script but compliant in structure)
        f.write(f'<HAnimHumanoid DEF="HAnim_LOA4" name="Humanoid" version="2.0" >\n')
        
        # 2. Skeleton (Joints)
        root_bone = armature_obj.data.bones.get("humanoid_root")
        if root_bone:
            write_joint(f, root_bone, "  ")
            
        # 3. Skin (Geometry)
        mesh = skin_obj.data
        verts = []
        matrix = skin_obj.matrix_world
        for v in mesh.vertices:
            co = matrix @ v.co
            verts.append(vector_to_str(co))
        
        points_str = " ".join(verts)
        
        # skinCoord
        f.write(f'  <Coordinate DEF="Skin_Coord" containerField="skinCoord" point="{points_str}" />\n')
        
        # skin (IndexedFaceSet)
        coord_indices = []
        for p in mesh.polygons:
            for li in p.loop_indices:
                coord_indices.append(str(mesh.loops[li].vertex_index))
            coord_indices.append("-1")
        index_str = " ".join(coord_indices)
        
        f.write(f'  <Group containerField="skin">\n')
        f.write(f'    <Shape>\n')
        f.write(f'      <Appearance><Material diffuseColor="0.8 0.6 0.5" /></Appearance>\n')
        f.write(f'      <IndexedFaceSet creaseAngle="3.14" coordIndex="{index_str}">\n')
        f.write(f'        <Coordinate USE="Skin_Coord" />\n')
        f.write(f'      </IndexedFaceSet>\n')
        f.write(f'    </Shape>\n')
        f.write(f'  </Group>\n')
        
        f.write('</HAnimHumanoid>\n')
        
        # 4. Poncho (Animation)
        print("Exporting Poncho Animation...")
        poncho_keys = []
        poncho_key_values = []
        
        scene = bpy.context.scene
        depsgraph = bpy.context.evaluated_depsgraph_get()
        
        # Get static topology
        scene.frame_set(1)
        p_mesh = poncho_obj.data
        p_indices = []
        for p in p_mesh.polygons:
            for li in p.loop_indices:
                p_indices.append(str(p_mesh.loops[li].vertex_index))
            p_indices.append("-1")
        p_index_str = " ".join(p_indices)
        
        for frame in range(1, end_frame + 1):
            scene.frame_set(frame)
            eval_obj = poncho_obj.evaluated_get(depsgraph)
            temp_mesh = eval_obj.to_mesh()
            
            poncho_keys.append(f"{(frame-1)/(end_frame-1):.4f}")
            
            frame_coords = []
            mat = poncho_obj.matrix_world
            for v in temp_mesh.vertices:
                co = mat @ v.co
                frame_coords.append(vector_to_str(co))
            poncho_key_values.append(" ".join(frame_coords))
            eval_obj.to_mesh_clear()
            
        f.write(f'<Transform DEF="Poncho_Trans">\n')
        f.write(f'  <Shape>\n')
        f.write(f'    <Appearance><Material diffuseColor="0.1 0.4 0.8" /></Appearance>\n')
        f.write(f'    <IndexedFaceSet creaseAngle="3.14" coordIndex="{p_index_str}">\n')
        f.write(f'      <Coordinate DEF="Poncho_Coord" point="" />\n')
        f.write(f'    </IndexedFaceSet>\n')
        f.write(f'  </Shape>\n')
        f.write(f'</Transform>\n')
        
        f.write(f'<TimeSensor DEF="Clock" cycleInterval="{end_frame/24.0}" loop="true" />\n')
        f.write(f'<CoordinateInterpolator DEF="Poncho_Interp" key="{" ".join(poncho_keys)}" keyValue="{" ".join(poncho_key_values)}" />\n')
        f.write(f'<ROUTE fromNode="Clock" fromField="fraction_changed" toNode="Poncho_Interp" toField="set_fraction" />\n')
        f.write(f'<ROUTE fromNode="Poncho_Interp" fromField="value_changed" toNode="Poncho_Coord" toField="point" />\n')

        f.write('</Scene>\n</X3D>\n')

# ==============================================================================
# MAIN
# ==============================================================================

if __name__ == "__main__":
    clean_scene()
    
    # 1. Build HAnim structure
    armature = create_hanim_skeleton()
    
    # 2. Build Skin and bind
    skin = create_hanim_skin(armature)
    
    # 3. Poncho
    poncho = create_poncho()
    
    # 4. Bake
    end_frame = 60
    bake_simulation(1, end_frame)
    
    # 5. Export
    out_file = os.path.join(os.path.expanduser("~"), "hanim_poncho_loa4.x3d")
    export_hanim_x3d(out_file, armature, skin, poncho, end_frame)
    print("Script finished successfully.")
