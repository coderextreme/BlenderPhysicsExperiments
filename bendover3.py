import bpy
import bmesh
import math
import mathutils
import os

# ==============================================================================
# 1. HANIM LOA4 HIERARCHY DATA
# ==============================================================================

def get_loa4_hierarchy():
    def get_hand_digits(side):
        digits = []
        for i in range(1, 6):
            y_offset = -0.015 * (i-1) if i > 1 else -0.01
            base = f"{side}_carpometacarpal_{i}" if i==1 else f"{side}_carpal_{i}"
            
            digits.append((base, (0.02, y_offset, 0.02), 0.02, [
                (f"{side}_metacarpal_{i}", (0.02, 0, 0), 0.018, [
                    (f"{side}_carpal_proximal_phalanx_{i}", (0.03, 0, 0), 0.015, [
                        (f"{side}_carpal_distal_phalanx_{i}", (0.02, 0, 0), 0.012, [])
                    ])
                ])
            ]))
        return digits

    def get_foot_digits(side):
        digits = []
        for i in range(1, 6):
            x_off = 0.02 if side == 'l' else -0.02
            y_off = 0.02 - (0.01 * i)
            digits.append((f"{side}_metatarsal_{i}", (x_off, 0.04, y_off), 0.02, [
                (f"{side}_tarsal_proximal_phalanx_{i}", (0, 0.04, 0), 0.015, [
                     (f"{side}_tarsal_distal_phalanx_{i}", (0, 0.03, 0), 0.015, [])
                ])
            ]))
        return digits

    def build_spine():
        head = ("skull", (0,0,0.08), 0.12, [("jaw", (0,-0.06,-0.02), 0.06, [])])
        c_spine = head
        for i in range(1, 8): c_spine = (f"c{i}", (0,0,0.03), 0.07, [c_spine])
            
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

        curr = (f"t1", (0,0,0.04), 0.09, [c_spine, l_arm, r_arm]) 
        for i in range(2, 13): curr = (f"t{i}", (0,0,0.04), 0.1, [curr])
        l_spine = curr
        for i in range(1, 6): l_spine = (f"l{i}", (0,0,0.05), 0.11, [l_spine])
        return l_spine

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

    return ("humanoid_root", (0,0,0.95), 0.01, [("sacrum", (0,0,0.05), 0.13, [build_spine(), legs[0]])])

# ==============================================================================
# 2. SCENE GENERATION
# ==============================================================================

def clean_scene():
    if bpy.context.active_object and bpy.context.active_object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    for col in [bpy.data.meshes, bpy.data.materials, bpy.data.armatures, bpy.data.objects, bpy.data.actions]:
        for block in col: col.remove(block)

def create_humanoid_system():
    # 1. Armature
    bpy.ops.object.armature_add(location=(0,0,0))
    arm_obj = bpy.context.active_object
    arm_obj.name = "HAnimHumanoid"
    arm = arm_obj.data
    arm.name = "HAnimArmature"
    
    bpy.ops.object.mode_set(mode='EDIT')
    for b in arm.edit_bones: arm.edit_bones.remove(b)
    
    hierarchy = get_loa4_hierarchy()
    bone_data = {} 
    
    def build_bone(node, parent):
        name, offset, rad, children = node
        eb = arm.edit_bones.new(name)
        if parent:
            eb.parent = parent
            eb.head = parent.head + mathutils.Vector(offset)
        else:
            eb.head = mathutils.Vector(offset)
            
        eb.tail = eb.head + (eb.head - eb.parent.head).normalized() * 0.03 if not children and parent else eb.head + mathutils.Vector((0,0,0.05))
        bone_data[name] = {'rad': rad, 'head': eb.head.copy(), 'tail': eb.tail.copy()}
        
        for c in children: build_bone(c, eb)
        if children:
            eb.tail = arm.edit_bones[children[0][0]].head
            bone_data[name]['tail'] = eb.tail.copy()

    build_bone(hierarchy, None)
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # 2. Smooth Skin Mesh
    mesh = bpy.data.meshes.new("SkinMesh")
    skin_obj = bpy.data.objects.new("HAnimSkin", mesh)
    bpy.context.collection.objects.link(skin_obj)
    bm = bmesh.new()
    
    bone_to_vert = {}
    for bone in arm.bones:
        v = bm.verts.new(bone.head_local)
        bone_to_vert[bone.name] = v
        
    bm.verts.ensure_lookup_table()
    for bone in arm.bones:
        v1 = bone_to_vert[bone.name]
        if bone.parent: bm.edges.new((bone_to_vert[bone.parent.name], v1))
        if not bone.children:
            v2 = bm.verts.new(bone.tail_local)
            bm.edges.new((v1, v2))
            
    bm.to_mesh(mesh)
    bm.free()
    
    # Modifiers
    bpy.ops.object.select_all(action='DESELECT')
    skin_obj.select_set(True)
    bpy.context.view_layer.objects.active = skin_obj
    
    bpy.ops.object.modifier_add(type='SKIN')
    
    # Apply Radii
    skin_verts = skin_obj.data.skin_vertices[0].data
    for i, v in enumerate(skin_obj.data.vertices):
        v_loc = v.co
        rad = 0.05
        for nm, data in bone_data.items():
            if (mathutils.Vector(data['head']) - v_loc).length < 0.001:
                rad = data['rad']
                break
            if (mathutils.Vector(data['tail']) - v_loc).length < 0.001:
                rad = data['rad'] * 0.6
                break
        skin_verts[i].radius = (rad, rad)
        
    bpy.ops.object.modifier_add(type='SUBSURF')
    skin_obj.modifiers["Subdivision"].levels = 1
    
    # Apply Modifiers
    bpy.ops.object.convert(target='MESH')
    
    for p in skin_obj.data.polygons: p.use_smooth = True
    mat = bpy.data.materials.new("SkinMat")
    mat.diffuse_color = (0.8, 0.65, 0.55, 1)
    skin_obj.data.materials.append(mat)
    
    # 3. Bind
    skin_obj.select_set(True)
    arm_obj.select_set(True)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.parent_set(type='ARMATURE_AUTO')
    
    # 4. Collision
    bpy.ops.object.select_all(action='DESELECT')
    skin_obj.select_set(True)
    bpy.context.view_layer.objects.active = skin_obj
    bpy.ops.object.modifier_add(type='COLLISION')
    # Extra thickness to keep poncho out
    skin_obj.modifiers["Collision"].settings.thickness_outer = 0.04
    skin_obj.modifiers["Collision"].settings.thickness_inner = 0.02
    
    return arm_obj, skin_obj

def create_poncho():
    bpy.ops.mesh.primitive_plane_add(size=1.9, location=(0,0,2.05))
    poncho = bpy.context.active_object
    poncho.name = "Poncho"
    
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.subdivide(number_cuts=30)
    bm = bmesh.from_edit_mesh(poncho.data)
    bm.faces.ensure_lookup_table()
    to_del = [f for f in bm.faces if abs(f.calc_center_median().x)<0.13 and abs(f.calc_center_median().y)<0.13]
    bmesh.ops.delete(bm, geom=to_del, context='FACES')
    bmesh.update_edit_mesh(poncho.data)
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # Solidify & Cloth
    bpy.ops.object.modifier_add(type='SOLIDIFY')
    poncho.modifiers["Solidify"].thickness = 0.005
    
    bpy.ops.object.modifier_add(type='CLOTH')
    cmod = poncho.modifiers["Cloth"]
    cmod.settings.quality = 8 
    cmod.settings.mass = 0.4
    cmod.settings.tension_stiffness = 5
    cmod.settings.compression_stiffness = 5
    cmod.settings.bending_model = 'ANGULAR'
    
    if hasattr(cmod, 'collision_settings'):
        cmod.collision_settings.use_self_collision = True
        cmod.collision_settings.distance_min = 0.02
        cmod.collision_settings.self_distance_min = 0.02
        
    mat = bpy.data.materials.new("PonchoMat")
    mat.diffuse_color = (0.1, 0.4, 0.7, 1)
    poncho.data.materials.append(mat)
    for p in poncho.data.polygons: p.use_smooth=True
    
    return poncho

# ==============================================================================
# 3. ANIMATION
# ==============================================================================

def animate_touch_toes(arm_obj, start_frame, end_frame):
    print("Animating Skeleton...")
    scene = bpy.context.scene
    
    # Set Active Object for Pose Mode
    bpy.ops.object.select_all(action='DESELECT')
    arm_obj.select_set(True)
    bpy.context.view_layer.objects.active = arm_obj
    
    bpy.ops.object.mode_set(mode='POSE')
    
    spine_bones = []
    for i in range(5, 0, -1): spine_bones.append(f"l{i}")
    for i in range(12, 0, -1): spine_bones.append(f"t{i}")
    for i in range(7, 0, -1): spine_bones.append(f"c{i}")
    
    key_bones = ['humanoid_root', 'sacrum', 'l_thigh', 'r_thigh', 'l_shoulder', 'r_shoulder', 'l_upperarm', 'r_upperarm'] + spine_bones
    
    # 1. Start Frame (Neutral)
    for f in [1, start_frame]:
        scene.frame_set(f)
        for bname in key_bones:
            pb = arm_obj.pose.bones.get(bname)
            if pb:
                pb.rotation_mode = 'XYZ'
                pb.location = (0,0,0)
                pb.rotation_euler = (0,0,0)
                pb.keyframe_insert(data_path="rotation_euler")
                pb.keyframe_insert(data_path="location")

    # 2. End Frame (Bent)
    scene.frame_set(end_frame)
    
    # Spine Curl
    spine_curl = math.radians(3.5) 
    for bname in spine_bones:
        pb = arm_obj.pose.bones.get(bname)
        if pb:
            pb.rotation_euler.x = spine_curl
            pb.keyframe_insert(data_path="rotation_euler")
    
    # Pelvis Tilt
    sacrum = arm_obj.pose.bones.get('sacrum')
    tilt_angle = math.radians(50)
    if sacrum:
        sacrum.rotation_euler.x = tilt_angle
        sacrum.keyframe_insert(data_path="rotation_euler")
        
    # Legs Counter-rotate
    for thigh in ['l_thigh', 'r_thigh']:
        pb = arm_obj.pose.bones.get(thigh)
        if pb:
            pb.rotation_euler.x = -tilt_angle
            pb.keyframe_insert(data_path="rotation_euler")

    # Root Shift
    root = arm_obj.pose.bones.get('humanoid_root')
    if root:
        root.location.y = -0.35
        root.location.z = -0.15
        root.keyframe_insert(data_path="location")

    # Arms Reach
    for arm in ['l_shoulder', 'r_shoulder', 'l_upperarm', 'r_upperarm']:
        pb = arm_obj.pose.bones.get(arm)
        if pb:
            pb.rotation_euler.x = math.radians(35)
            pb.keyframe_insert(data_path="rotation_euler")

    bpy.ops.object.mode_set(mode='OBJECT')

def bake_physics(start, end):
    print("Baking Physics...")
    scene = bpy.context.scene
    scene.frame_start = start
    scene.frame_end = end
    
    bpy.ops.object.select_all(action='SELECT')
    if bpy.ops.ptcache.bake_all.poll():
        bpy.ops.ptcache.bake_all(bake=True)
    else:
        for f in range(start, end+1): scene.frame_set(f)
    print("Baking Complete.")

# ==============================================================================
# 4. EXPORT LOGIC
# ==============================================================================

def export_complex_x3d(filepath, arm_obj, skin_obj, poncho_obj, start_frame, end_frame):
    print(f"Exporting to {filepath}...")
    
    def vec_str(v): return f"{v.x:.4f} {v.z:.4f} {-v.y:.4f}"
    
    def rot_str(quat):
        axis, angle = quat.to_axis_angle()
        return f"{axis.x:.4f} {axis.z:.4f} {-axis.y:.4f} {angle:.4f}"

    # --- Pre-calculate Poncho Animation & Points ---
    print("Sampling Poncho Animation...")
    poncho_keys = []
    poncho_kvs = []
    
    dg = bpy.context.evaluated_depsgraph_get()
    
    # Get initial topology and coords
    bpy.context.scene.frame_set(start_frame)
    eval_poncho = poncho_obj.evaluated_get(dg)
    pmesh = eval_poncho.to_mesh()
    p_ind = []
    for p in pmesh.polygons:
        p_ind.extend([str(pmesh.loops[li].vertex_index) for li in p.loop_indices] + ["-1"])
    
    # Store initial coords for the Coordinate point="" field
    initial_poncho_coords = " ".join([vec_str(poncho_obj.matrix_world @ v.co) for v in pmesh.vertices])
    
    eval_poncho.to_mesh_clear()
    
    # Loop frames
    for fr in range(start_frame, end_frame + 1):
        bpy.context.scene.frame_set(fr)
        eval_p = poncho_obj.evaluated_get(dg)
        tm = eval_p.to_mesh()
        
        poncho_keys.append(f"{(fr-start_frame)/(end_frame-start_frame):.4f}")
        coords = [vec_str(poncho_obj.matrix_world @ v.co) for v in tm.vertices]
        poncho_kvs.append(" ".join(coords))
        eval_p.to_mesh_clear()
    
    # --- Weights ---
    print("Extracting Skin Weights...")
    mesh = skin_obj.data
    vg_map = {vg.index: vg.name for vg in skin_obj.vertex_groups}
    bone_weights = {}
    
    for v in mesh.vertices:
        for g in v.groups:
            idx = g.group
            bname = vg_map.get(idx)
            if bname:
                if bname not in bone_weights: bone_weights[bname] = {'i':[], 'w':[]}
                bone_weights[bname]['i'].append(str(v.index))
                bone_weights[bname]['w'].append(f"{g.weight:.4f}")

    # --- Write X3D ---
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<!DOCTYPE X3D PUBLIC "ISO//Web3D//DTD X3D 3.3//EN" "https://www.web3d.org/specifications/x3d-3.3.dtd">\n')
        f.write('<X3D profile="Full" version="3.3">\n<head><component name="HAnim" level="3"/><meta name="generator" content="Blender LOA4 HAnim" /></head>\n<Scene>\n')
        f.write('<NavigationInfo type=\'"EXAMINE" "ANY"\' />\n')
        f.write('<Viewpoint description="Front" position="0 1.5 4.5" orientation="1 0 0 -0.15" />\n')
        duration = (end_frame - start_frame) / 24.0
        f.write(f'<TimeSensor DEF="AnimTimer" cycleInterval="{duration:.2f}" loop="true" />\n')
        
        f.write(f'<HAnimHumanoid DEF="HAnim_LOA4" name="Humanoid" version="2.0" info=\'"LOA4 Articulation"\' >\n')
        
        def write_joint(bone, indent):
            center = vec_str(bone.head_local)
            bw = bone_weights.get(bone.name)
            s_idx = " ".join(bw['i']) if bw else ""
            s_wgt = " ".join(bw['w']) if bw else ""
            
            container = "children"
            if bone.name == "humanoid_root": container = "skeleton"
                
            f.write(f'{indent}<HAnimJoint DEF="{bone.name}" name="{bone.name}" containerField="{container}" center="{center}" skinCoordIndex="{s_idx}" skinCoordWeight="{s_wgt}">\n')
            for child in bone.children:
                write_joint(child, indent + "  ")
            f.write(f'{indent}</HAnimJoint>\n')

        # Skeleton
        root = arm_obj.data.bones.get("humanoid_root")
        if root: write_joint(root, "  ")
        
        # Skin Coords
        bpy.context.scene.frame_set(1)
        verts = [vec_str(arm_obj.matrix_world @ v.co) for v in mesh.vertices]
        
        f.write(f'  <Coordinate DEF="Skin_Coord" containerField="skinCoord" point="{" ".join(verts)}" />\n')
        
        indices = []
        for p in mesh.polygons:
            indices.extend([str(mesh.loops[li].vertex_index) for li in p.loop_indices] + ["-1"])
            
        f.write(f'  <Group containerField="skin">\n')
        f.write(f'    <Shape>\n')
        f.write(f'      <Appearance><Material diffuseColor="0.75 0.6 0.5" /></Appearance>\n')
        f.write(f'      <IndexedFaceSet creaseAngle="3.14" coordIndex="{" ".join(indices)}">\n')
        f.write(f'        <Coordinate USE="Skin_Coord" />\n')
        f.write(f'      </IndexedFaceSet>\n')
        f.write(f'    </Shape>\n')
        f.write(f'  </Group>\n')
        f.write('</HAnimHumanoid>\n')

        # Animation (Skeleton)
        print("Exporting Skeleton Animation...")
        frame_keys = []
        for fr in range(start_frame, end_frame + 1):
            frame_keys.append(f"{(fr-start_frame)/(end_frame-start_frame):.4f}")
        keys_str = " ".join(frame_keys)
        
        for bone in arm_obj.pose.bones:
            rot_values = []
            for fr in range(start_frame, end_frame + 1):
                bpy.context.scene.frame_set(fr)
                if bone.rotation_mode == 'QUATERNION': q = bone.rotation_quaternion
                else: q = bone.rotation_euler.to_quaternion()
                rot_values.append(rot_str(q))
                
            kv_str = " ".join(rot_values)
            interp_def = f"{bone.name}_OrInt"
            f.write(f'<OrientationInterpolator DEF="{interp_def}" key="{keys_str}" keyValue="{kv_str}" />\n')
            f.write(f'<ROUTE fromNode="AnimTimer" fromField="fraction_changed" toNode="{interp_def}" toField="set_fraction" />\n')
            f.write(f'<ROUTE fromNode="{interp_def}" fromField="value_changed" toNode="{bone.name}" toField="rotation" />\n')
            
            if bone.name == "humanoid_root":
                pos_values = []
                for fr in range(start_frame, end_frame + 1):
                    bpy.context.scene.frame_set(fr)
                    l = bone.location
                    pos_values.append(f"{l.x:.4f} {l.z:.4f} {-l.y:.4f}")
                
                pos_str = " ".join(pos_values)
                f.write(f'<PositionInterpolator DEF="Root_PosInt" key="{keys_str}" keyValue="{pos_str}" />\n')
                f.write(f'<ROUTE fromNode="AnimTimer" fromField="fraction_changed" toNode="Root_PosInt" toField="set_fraction" />\n')
                f.write(f'<ROUTE fromNode="Root_PosInt" fromField="value_changed" toNode="humanoid_root" toField="translation" />\n')

        # Poncho Shape & Interpolator
        print("Writing Poncho Nodes...")
        f.write(f'<Transform DEF="Poncho_Trans">\n')
        f.write(f'  <Shape>\n')
        f.write(f'    <Appearance><Material diffuseColor="0.1 0.4 0.8" /></Appearance>\n')
        f.write(f'    <IndexedFaceSet creaseAngle="3.14" coordIndex="{" ".join(p_ind)}">\n')
        # Here we use the pre-calculated initial coordinates
        f.write(f'      <Coordinate DEF="Poncho_Coord" point="{initial_poncho_coords}" />\n')
        f.write(f'    </IndexedFaceSet>\n')
        f.write(f'  </Shape>\n')
        f.write(f'</Transform>\n')
        
        f.write(f'<CoordinateInterpolator DEF="Poncho_Int" key="{" ".join(poncho_keys)}" keyValue="{" ".join(poncho_kvs)}" />\n')
        f.write(f'<ROUTE fromNode="AnimTimer" fromField="fraction_changed" toNode="Poncho_Int" toField="set_fraction" />\n')
        f.write(f'<ROUTE fromNode="Poncho_Int" fromField="value_changed" toNode="Poncho_Coord" toField="point" />\n')
        
        f.write('</Scene>\n</X3D>\n')

# ==============================================================================
# MAIN EXECUTION
# ==============================================================================

if __name__ == "__main__":
    clean_scene()
    
    arm, skin = create_humanoid_system()
    poncho = create_poncho()
    
    animate_touch_toes(arm, 61, 120)
    
    bake_physics(1, 120)
    
    out = os.path.join(os.path.expanduser("~"), "hanim_loa4_final.x3d")
    export_complex_x3d(out, arm, skin, poncho, 1, 120)
    print("Script finished successfully.")
