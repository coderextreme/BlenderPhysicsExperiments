import bpy
import bmesh
import math
import mathutils
import os

# ==============================================================================
# 1. LOA4 HIERARCHY DATA GENERATOR
# ==============================================================================

def get_loa4_hierarchy():
    """
    Returns a recursive structure for HAnim LOA4.
    Format: (Bone_Name, Head_Offset_From_Parent, Radius_For_Skin, [Children])
    Radius_For_Skin is used to generate the watertight mesh thickness.
    """
    
    # Helper for 5-finger chains (Carpals -> Metacarpals -> Phalanges)
    def get_hand_digits(side):
        digits = []
        
        # Thumb (Ray 1) - shorter chain
        digits.append((f"{side}_carpometacarpal_1", (0.015, -0.01, 0.02), 0.02, [
            (f"{side}_metacarpal_1", (0.01, -0.01, 0.02), 0.018, [
                (f"{side}_carpal_proximal_phalanx_1", (0.01, -0.01, 0.02), 0.016, [
                    (f"{side}_carpal_distal_phalanx_1", (0.01, -0.01, 0.02), 0.015, [])
                ])
            ])
        ]))
        
        # Fingers 2-5
        for i in range(2, 6):
            # Spread fingers along Y slightly
            y_offset = -0.015 * (i-1)
            digits.append((f"{side}_carpal_{i}", (0.02, y_offset, 0), 0.02, [
                (f"{side}_metacarpal_{i}", (0.03, 0, 0), 0.018, [
                    (f"{side}_carpal_proximal_phalanx_{i}", (0.035, 0, 0), 0.015, [
                        (f"{side}_carpal_middle_phalanx_{i}", (0.025, 0, 0), 0.013, [
                            (f"{side}_carpal_distal_phalanx_{i}", (0.02, 0, 0), 0.012, [])
                        ])
                    ])
                ])
            ]))
        return digits

    # Helper for Feet (Tarsals -> Metatarsals -> Phalanges)
    def get_foot_digits(side):
        digits = []
        for i in range(1, 6):
            x_offset = 0.02 if side == 'l' else -0.02
            y_offset = 0.02 - (0.01 * i)
            digits.append((f"{side}_metatarsal_{i}", (x_offset, 0.04, y_offset), 0.02, [
                (f"{side}_tarsal_proximal_phalanx_{i}", (0, 0.04, 0), 0.015, [
                     (f"{side}_tarsal_distal_phalanx_{i}", (0, 0.03, 0), 0.015, [])
                ])
            ]))
        return digits

    # Define Spine Chain (L5 -> Skull)
    # Recursively builds spine up
    def build_spine():
        # C1-C7, T1-T12, L1-L5. 
        # For brevity in code, we build explicitly but compactly.
        
        # Head/Neck
        head_chain = ("skull", (0,0,0.08), 0.12, [
            ("jaw", (0,-0.06,-0.02), 0.06, [])
        ])
        
        c_spine = head_chain
        for i in range(1, 8): # c1 to c7
            c_spine = (f"c{i}", (0,0,0.03), 0.07, [c_spine]) if i == 1 else (f"c{i}", (0,0,0.03), 0.07, [c_spine])
            
        t_spine = c_spine
        # Upper T-spine connects to shoulders
        # We need to inject the shoulder connection at T2 or T1 usually. 
        # HAnim often branches sternoclavicular from t1 or c7. We will branch from t1.
        
        # Left Arm Branch
        l_arm = ("l_sternoclavicular", (0.04,0,0.02), 0.06, [
            ("l_acromioclavicular", (0.06,0,0), 0.05, [
                ("l_shoulder", (0.05,0,-0.02), 0.05, [
                    ("l_upperarm", (0.1,0,-0.05), 0.07, [
                        ("l_elbow", (0.28,0,0), 0.06, [
                            ("l_forearm", (0.25,0,0), 0.05, [
                                ("l_wrist", (0.05,0,0), 0.04, get_hand_digits("l"))
                            ])
                        ])
                    ])
                ])
            ])
        ])
        
        # Right Arm Branch
        r_arm = ("r_sternoclavicular", (-0.04,0,0.02), 0.06, [
            ("r_acromioclavicular", (-0.06,0,0), 0.05, [
                ("r_shoulder", (-0.05,0,-0.02), 0.05, [
                    ("r_upperarm", (-0.1,0,-0.05), 0.07, [
                        ("r_elbow", (-0.28,0,0), 0.06, [
                            ("r_forearm", (-0.25,0,0), 0.05, [
                                ("r_wrist", (-0.05,0,0), 0.04, get_hand_digits("r"))
                            ])
                        ])
                    ])
                ])
            ])
        ])

        # Build T Spine down
        # T1 has the arms as children, plus T2
        curr_node = (f"t1", (0,0,0.04), 0.09, [c_spine, l_arm, r_arm]) 
        
        for i in range(2, 13): # t2 to t12
            curr_node = (f"t{i}", (0,0,0.04), 0.1, [curr_node])
            
        l_spine = curr_node
        for i in range(1, 6): # l1 to l5
            l_spine = (f"l{i}", (0,0,0.05), 0.11, [l_spine])
            
        return l_spine

    spine_top = build_spine()

    # Define Pelvis/Legs
    # Note: HAnim hierarchy is Humanoid_Root -> Sacrum -> [L5..., Pelvis...]
    
    legs = [
        ("pelvis", (0,0,-0.05), 0.14, [
            ("l_hip", (0.1,0,-0.1), 0.1, [
                ("l_thigh", (0.05,0,-0.1), 0.11, [
                    ("l_knee", (0,0,-0.4), 0.09, [
                        ("l_calf", (0,0,-0.4), 0.08, [
                            ("l_ankle", (0,0,-0.05), 0.06, [
                                ("l_calcaneus", (0, -0.05, -0.05), 0.05, [
                                    ("l_navicular", (0, 0.05, 0), 0.04, get_foot_digits("l"))
                                ])
                            ])
                        ])
                    ])
                ])
            ]),
            ("r_hip", (-0.1,0,-0.1), 0.1, [
                ("r_thigh", (-0.05,0,-0.1), 0.11, [
                    ("r_knee", (0,0,-0.4), 0.09, [
                        ("r_calf", (0,0,-0.4), 0.08, [
                            ("r_ankle", (0,0,-0.05), 0.06, [
                                ("r_calcaneus", (0, -0.05, -0.05), 0.05, [
                                    ("r_navicular", (0, 0.05, 0), 0.04, get_foot_digits("r"))
                                ])
                            ])
                        ])
                    ])
                ])
            ])
        ])
    ]

    # Assemble Root
    # HumanoidRoot -> Sacrum -> [Spine_Bottom, Pelvis]
    return ("humanoid_root", (0,0,0.95), 0.01, [
        ("sacrum", (0,0,0.05), 0.13, [
            spine_top, 
            legs[0]
        ])
    ])

# ==============================================================================
# 2. SCENE & MESH GENERATION (SMOOTH SKIN)
# ==============================================================================

def clean_scene():
    if bpy.context.active_object and bpy.context.active_object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    for col in [bpy.data.meshes, bpy.data.materials, bpy.data.armatures, bpy.data.objects, bpy.data.collections]:
        for block in col:
            col.remove(block)

def create_loa4_humanoid():
    print("Generating LOA4 Skeleton...")
    bpy.ops.object.armature_add(location=(0,0,0))
    arm_obj = bpy.context.active_object
    arm_obj.name = "HAnimHumanoid"
    arm = arm_obj.data
    arm.name = "HAnimArmature"
    
    bpy.ops.object.mode_set(mode='EDIT')
    for bone in arm.edit_bones: arm.edit_bones.remove(bone)
    
    hierarchy = get_loa4_hierarchy()
    
    # We will store bone positions to generate the skin mesh later
    # Format: {bone_name: {'head': vec, 'tail': vec, 'radius': float}}
    bone_data_cache = {} 
    
    def build_bone(node, parent_bone):
        name, offset, radius, children = node
        
        eb = arm.edit_bones.new(name)
        if parent_bone:
            eb.parent = parent_bone
            eb.head = parent_bone.head + mathutils.Vector(offset)
        else:
            eb.head = mathutils.Vector(offset)
        
        # Determine tail - if no children, small offset
        if len(children) == 0:
            # Leaf bone
            eb.tail = eb.head + (eb.head - eb.parent.head).normalized() * 0.03
        else:
            # Temporary tail, will likely be overwritten by child connection visual logic
            eb.tail = eb.head + mathutils.Vector((0,0,0.05))
            
        bone_data_cache[name] = {'radius': radius, 'head': eb.head.copy(), 'tail': eb.tail.copy(), 'children': [c[0] for c in children]}

        for child in children:
            build_bone(child, eb)
            
        # Visual cleanup: Point tail to first child
        if children:
            child_name = children[0][0]
            child_head = arm.edit_bones[child_name].head
            eb.tail = child_head
            bone_data_cache[name]['tail'] = child_head.copy()

    build_bone(hierarchy, None)
    
    # Count joints
    joint_count = len(arm.edit_bones)
    print(f"Skeleton created with {joint_count} joints (LOA4 target approx 148).")
    
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # ---------------------------------------------------------
    # Create Smooth Watertight Skin using Skin Modifier
    # ---------------------------------------------------------
    print("Generating Watertight Skin...")
    
    # 1. Create a mesh with vertices at bone heads
    mesh = bpy.data.meshes.new("SkinMesh")
    skin_obj = bpy.data.objects.new("HAnimSkin", mesh)
    bpy.context.collection.objects.link(skin_obj)
    
    bm = bmesh.new()
    
    # Map bone names to BMesh vertices
    bone_to_vert = {}
    
    # Add vertices
    # To make a continuous skin modifier mesh, we need vertices at heads and tails, connected by edges.
    # Since bones share head/tail locations, we merge them.
    
    # We iterate the armature bones to build the graph
    arm = arm_obj.data
    
    # World matrix
    mw = arm_obj.matrix_world
    
    # Helper to find or create vert at location
    # Simple spatial hashing or name mapping? Name mapping is safer for hierarchy.
    
    # We will create a vertex for every bone HEAD. 
    # The Leaf bones need a vertex for their TAIL too.
    
    for bone in arm.bones:
        # Create vert at Head
        # We need the radius from our cache.
        # Since cache was built in recursive order, looking up by name works.
        rad = bone_data_cache.get(bone.name, {'radius': 0.05})['radius']
        
        v = bm.verts.new(bone.head_local)
        v.index = len(bm.verts) - 1 # Ensure index
        bone_to_vert[bone.name] = v
        
        # Skin Modifier Data layer for radius
        # We will apply this after creating the modifier, via verify()
        
    bm.verts.ensure_lookup_table()
    
    # Create Edges based on parent-child relationship
    for bone in arm.bones:
        v_head = bone_to_vert[bone.name]
        
        if bone.parent:
            v_parent = bone_to_vert[bone.parent.name]
            # Check if edge exists
            try:
                bm.edges.new((v_parent, v_head))
            except ValueError:
                pass # Edge exists
        
        # If it's a leaf bone (fingers/toes/skull/jaw), we need the tail segment
        if not bone.children:
            v_tail = bm.verts.new(bone.tail_local)
            bm.edges.new((v_head, v_tail))
            # Tag this tail vert to have radius of the bone
            # We'll handle radius application next
            
    bm.to_mesh(mesh)
    bm.free()
    
    # Apply Skin Radius
    # The Skin Modifier stores radius in a specific data layer
    bpy.context.view_layer.objects.active = skin_obj
    bpy.ops.object.modifier_add(type='SKIN')
    skin_mod = skin_obj.modifiers["Skin"]
    
    # Access the skin vertices layer
    skin_vertices = skin_obj.data.skin_vertices[0].data
    
    # This matches vertices by index, which is tricky.
    # Let's rely on coordinate proximity to apply radius.
    for i, v in enumerate(skin_obj.data.vertices):
        # Find closest bone
        min_dist = 100.0
        best_rad = 0.05
        
        v_loc = v.co
        
        for b_name, data in bone_data_cache.items():
            dist = (mathutils.Vector(data['head']) - v_loc).length
            if dist < 0.001:
                best_rad = data['radius']
                break
            # Check tail for leaf bones
            dist_tail = (mathutils.Vector(data['tail']) - v_loc).length
            if dist_tail < 0.001:
                best_rad = data['radius'] * 0.7 # Taper leaves
                break
                
        skin_vertices[i].radius = (best_rad, best_rad)

    # Add Subdivision Surface for smoothness
    bpy.ops.object.modifier_add(type='SUBSURF')
    skin_obj.modifiers["Subdivision"].levels = 1
    
    # Apply Modifiers to get the final mesh
    bpy.ops.object.convert(target='MESH')
    
    # Material
    mat = bpy.data.materials.new(name="HumanSkin")
    mat.diffuse_color = (0.8, 0.65, 0.55, 1.0)
    mat.roughness = 0.4
    skin_obj.data.materials.append(mat)
    
    # Smooth Shading
    for p in skin_obj.data.polygons: p.use_smooth = True
    
    # Bind to Armature
    bpy.ops.object.select_all(action='DESELECT')
    skin_obj.select_set(True)
    arm_obj.select_set(True)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.parent_set(type='ARMATURE_AUTO')
    
    # Add Collision Physics
    bpy.context.view_layer.objects.active = skin_obj
    bpy.ops.object.modifier_add(type='COLLISION')
    skin_obj.modifiers["Collision"].settings.thickness_outer = 0.015
    
    return arm_obj, skin_obj

def create_poncho():
    print("Creating Poncho...")
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.mesh.primitive_plane_add(size=1.8, location=(0, 0, 1.95)) # Adjusted for head height
    poncho = bpy.context.active_object
    poncho.name = "Poncho"
    
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.subdivide(number_cuts=30) # Higher res for better drape
    
    bm = bmesh.from_edit_mesh(poncho.data)
    bm.faces.ensure_lookup_table()
    to_delete = [f for f in bm.faces if abs(f.calc_center_median().x) < 0.12 and abs(f.calc_center_median().y) < 0.12]
    bmesh.ops.delete(bm, geom=to_delete, context='FACES')
    bmesh.update_edit_mesh(poncho.data)
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # Cloth
    bpy.ops.object.modifier_add(type='CLOTH')
    cmod = poncho.modifiers["Cloth"]
    cmod.settings.quality = 6
    cmod.settings.mass = 0.3
    cmod.settings.bending_model = 'ANGULAR' # Better folds
    
    if hasattr(cmod, 'collision_settings'):
        col = cmod.collision_settings
        col.use_self_collision = True
        col.distance_min = 0.015
        col.self_distance_min = 0.015
    
    # Visuals
    bpy.ops.object.modifier_add(type='SOLIDIFY')
    poncho.modifiers["Solidify"].thickness = 0.005
    
    for p in poncho.data.polygons: p.use_smooth = True
    mat = bpy.data.materials.new(name="PonchoMat")
    mat.diffuse_color = (0.1, 0.4, 0.7, 1)
    poncho.data.materials.append(mat)
    
    return poncho

def bake_simulation(start, end):
    scene = bpy.context.scene
    scene.frame_start = start
    scene.frame_end = end
    print("Baking Physics (this may take a moment)...")
    bpy.ops.object.select_all(action='SELECT')
    
    if bpy.ops.ptcache.bake_all.poll():
        bpy.ops.ptcache.bake_all(bake=True)
    else:
        for f in range(start, end+1):
            scene.frame_set(f)
    print("Baking Done.")

# ==============================================================================
# 3. X3D EXPORT (HAnim + Vertex Anim)
# ==============================================================================

def export_hanim_x3d(filepath, armature_obj, skin_obj, poncho_obj, end_frame):
    
    def vector_to_str(vec):
        return f"{vec.x:.4f} {vec.z:.4f} {-vec.y:.4f}"

    def write_joint(f, bone, indent):
        center = vector_to_str(bone.head_local)
        f.write(f'{indent}<HAnimJoint DEF="{bone.name}" name="{bone.name}" center="{center}" skinCoordIndex="" skinCoordWeight="">\n')
        for child in bone.children:
            write_joint(f, child, indent + "  ")
        f.write(f'{indent}</HAnimJoint>\n')

    print(f"Exporting to {filepath}...")
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<!DOCTYPE X3D PUBLIC "ISO//Web3D//DTD X3D 3.3//EN" "https://www.web3d.org/specifications/x3d-3.3.dtd">\n')
        f.write('<X3D profile="Full" version="3.3" xmlns:xsd="http://www.w3.org/2001/XMLSchema-instance" xsd:noNamespaceSchemaLocation="https://www.web3d.org/specifications/x3d-3.3.xsd">\n')
        f.write('<head><component name="HAnim" level="3"/><meta name="generator" content="Blender LOA4 Script" /></head>\n')
        f.write('<Scene>\n')
        f.write('<NavigationInfo type=\'"EXAMINE" "ANY"\' />\n')
        f.write('<Viewpoint description="Front" position="0 1.7 4" orientation="1 0 0 -0.1" />\n')
        
        # 1. Humanoid
        f.write(f'<HAnimHumanoid DEF="HAnim_LOA4" name="Humanoid" version="2.0" info=\'"LOA4 Articulation"\' >\n')
        
        # Skeleton
        root_bone = armature_obj.data.bones.get("humanoid_root")
        if root_bone:
            write_joint(f, root_bone, "  ")
            
        # Skin Geometry
        # We need to apply the modifier stack (except Armature) to get the watertight mesh coordinates
        # Actually, for X3D HAnim export, we usually want the bind-pose mesh (T-pose).
        # Since we are at frame 1 (or we can reset pose), we export the mesh data.
        
        bpy.context.scene.frame_set(1)
        # Temporarily disable armature modifier to get rest pose vertices
        skin_obj.modifiers["Armature"].show_viewport = False
        
        dg = bpy.context.evaluated_depsgraph_get()
        eval_skin = skin_obj.evaluated_get(dg)
        mesh = eval_skin.to_mesh()
        
        verts = []
        matrix = skin_obj.matrix_world
        for v in mesh.vertices:
            co = matrix @ v.co
            verts.append(vector_to_str(co))
        points_str = " ".join(verts)
        
        f.write(f'  <Coordinate DEF="Skin_Coord" containerField="skinCoord" point="{points_str}" />\n')
        
        coord_indices = []
        for p in mesh.polygons:
            for li in p.loop_indices:
                coord_indices.append(str(mesh.loops[li].vertex_index))
            coord_indices.append("-1")
        index_str = " ".join(coord_indices)
        
        f.write(f'  <Group containerField="skin">\n')
        f.write(f'    <Shape>\n')
        f.write(f'      <Appearance><Material diffuseColor="0.75 0.6 0.5" /></Appearance>\n')
        f.write(f'      <IndexedFaceSet creaseAngle="3.14" coordIndex="{index_str}">\n')
        f.write(f'        <Coordinate USE="Skin_Coord" />\n')
        f.write(f'      </IndexedFaceSet>\n')
        f.write(f'    </Shape>\n')
        f.write(f'  </Group>\n')
        
        # Restore Armature mod
        skin_obj.modifiers["Armature"].show_viewport = True
        eval_skin.to_mesh_clear()
        
        f.write('</HAnimHumanoid>\n')
        
        # 2. Poncho Animation
        print("Sampling Poncho Animation...")
        poncho_keys = []
        poncho_key_values = []
        
        # Static topology from frame 1
        bpy.context.scene.frame_set(1)
        # Note: We must export the render-mesh for poncho to capture Solidify/Cloth
        eval_poncho = poncho_obj.evaluated_get(dg)
        p_mesh = eval_poncho.to_mesh()
        
        p_indices = []
        for p in p_mesh.polygons:
            for li in p.loop_indices:
                p_indices.append(str(p_mesh.loops[li].vertex_index))
            p_indices.append("-1")
        p_index_str = " ".join(p_indices)
        eval_poncho.to_mesh_clear()
        
        for frame in range(1, end_frame + 1):
            bpy.context.scene.frame_set(frame)
            eval_obj = poncho_obj.evaluated_get(dg)
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
    
    # 1. Create LOA4 Humanoid with watertight skin
    armature, skin = create_loa4_humanoid()
    
    # 2. Poncho
    poncho = create_poncho()
    
    # 3. Bake
    end_frame = 60
    bake_simulation(1, end_frame)
    
    # 4. Export
    out_file = os.path.join(os.path.expanduser("~"), "hanim_loa4_poncho.x3d")
    export_hanim_x3d(out_file, armature, skin, poncho, end_frame)
    print("Script finished.")
