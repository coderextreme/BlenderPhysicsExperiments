import bpy
import bmesh
import mathutils
import math
import os

# ==========================================
# 1. SCENE CLEANUP & SETUP
# ==========================================
def cleanup_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    for coll in bpy.data.collections:
        bpy.data.collections.remove(coll)
    for block in bpy.data.meshes: bpy.data.meshes.remove(block)
    for block in bpy.data.armatures: bpy.data.armatures.remove(block)
    for block in bpy.data.materials: bpy.data.materials.remove(block)

    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = 120

# ==========================================
# 2. HANIM LOA4 SKELETON GENERATOR
# ==========================================
def generate_loa4_bones():
    """Generates standard HAnim LOA4 bones with female hourglass offsets"""
    bones = []
    
    # Core Spine (Simplified for procedural loop but strictly named)
    bones.append(("hanim_HumanoidRoot", None, (0, 0, 0.95), (0, 0, 1.0)))
    bones.append(("hanim_sacrum", "hanim_HumanoidRoot", (0, 0, 1.0), (0, 0, 1.05)))
    bones.append(("hanim_pelvis", "hanim_sacrum", (0, 0, 1.05), (0, 0, 1.1)))
    
    prev = "hanim_pelvis"
    z_curr = 1.1
    
    # 5 Lumbar
    for i in range(5, 0, -1):
        z_next = z_curr + 0.03
        name = f"hanim_vl{i}"
        bones.append((name, prev, (0, 0, z_curr), (0, 0, z_next)))
        prev, z_curr = name, z_next
        
    # 12 Thoracic
    for i in range(12, 0, -1):
        z_next = z_curr + 0.02
        name = f"hanim_vt{i}"
        bones.append((name, prev, (0, 0, z_curr), (0, 0, z_next)))
        prev, z_curr = name, z_next
        
    # 7 Cervical + Skull
    for i in range(7, 0, -1):
        z_next = z_curr + 0.015
        name = f"hanim_vc{i}"
        bones.append((name, prev, (0, 0, z_curr), (0, 0, z_next)))
        prev, z_curr = name, z_next
        
    bones.append(("hanim_skullbase", prev, (0, 0, z_curr), (0, 0, z_curr + 0.02)))
    bones.append(("hanim_skull", "hanim_skullbase", (0, 0, z_curr + 0.02), (0, 0, z_curr + 0.15)))
    
    # Limbs procedural builder
    def build_arm(side, y_dir, parent):
        sy = y_dir
        bones.append((f"hanim_{side}_clavicle", parent, (0, 0.02*sy, 1.45), (0, 0.15*sy, 1.45)))
        bones.append((f"hanim_{side}_scapula", f"hanim_{side}_clavicle", (0, 0.15*sy, 1.45), (0, 0.16*sy, 1.43)))
        bones.append((f"hanim_{side}_upperarm", f"hanim_{side}_scapula", (0, 0.16*sy, 1.43), (0, 0.2*sy, 1.15)))
        bones.append((f"hanim_{side}_forearm", f"hanim_{side}_upperarm", (0, 0.2*sy, 1.15), (0, 0.22*sy, 0.9)))
        bones.append((f"hanim_{side}_carpal", f"hanim_{side}_forearm", (0, 0.22*sy, 0.9), (0, 0.23*sy, 0.88)))
        
        fingers = ["thumb", "index", "middle", "ring", "pinky"]
        for idx, finger in enumerate(fingers):
            f_sy = sy * (0.21 + idx*0.01)
            b_parent = f"hanim_{side}_carpal"
            num = idx + 1
            bones.append((f"hanim_{side}_metacarpal_{num}", b_parent, (0, 0.23*sy, 0.88), (0, f_sy, 0.84)))
            bones.append((f"hanim_{side}_proximal_phalanx_{num}", f"hanim_{side}_metacarpal_{num}", (0, f_sy, 0.84), (0, f_sy, 0.81)))
            if finger != "thumb":
                bones.append((f"hanim_{side}_middle_phalanx_{num}", f"hanim_{side}_proximal_phalanx_{num}", (0, f_sy, 0.81), (0, f_sy, 0.79)))
                bones.append((f"hanim_{side}_distal_phalanx_{num}", f"hanim_{side}_middle_phalanx_{num}", (0, f_sy, 0.79), (0, f_sy, 0.77)))
            else:
                bones.append((f"hanim_{side}_distal_phalanx_{num}", f"hanim_{side}_proximal_phalanx_{num}", (0, f_sy, 0.81), (0, f_sy, 0.79)))

    def build_leg(side, y_dir, parent):
        sy = y_dir
        bones.append((f"hanim_{side}_hip", parent, (0, 0.05*sy, 1.05), (0, 0.1*sy, 1.0)))
        bones.append((f"hanim_{side}_thigh", f"hanim_{side}_hip", (0, 0.1*sy, 1.0), (0, 0.1*sy, 0.55)))
        bones.append((f"hanim_{side}_calf", f"hanim_{side}_thigh", (0, 0.1*sy, 0.55), (0, 0.1*sy, 0.15)))
        bones.append((f"hanim_{side}_talus", f"hanim_{side}_calf", (0, 0.1*sy, 0.15), (0.05, 0.1*sy, 0.08)))
        bones.append((f"hanim_{side}_navicular", f"hanim_{side}_talus", (0.05, 0.1*sy, 0.08), (0.1, 0.1*sy, 0.05)))
        bones.append((f"hanim_{side}_cuneiform_2", f"hanim_{side}_navicular", (0.1, 0.1*sy, 0.05), (0.13, 0.1*sy, 0.03)))
        
        for num in range(1, 6):
            f_sy = sy * (0.07 + num*0.015)
            b_parent = f"hanim_{side}_cuneiform_2"
            bones.append((f"hanim_{side}_metatarsal_{num}", b_parent, (0.13, 0.1*sy, 0.03), (0.18, f_sy, 0.02)))
            bones.append((f"hanim_{side}_proximal_phalanx_{num}", f"hanim_{side}_metatarsal_{num}", (0.18, f_sy, 0.02), (0.21, f_sy, 0.01)))
            if num != 1:
                bones.append((f"hanim_{side}_middle_phalanx_{num}", f"hanim_{side}_proximal_phalanx_{num}", (0.21, f_sy, 0.01), (0.23, f_sy, 0.01)))
                bones.append((f"hanim_{side}_distal_phalanx_{num}", f"hanim_{side}_middle_phalanx_{num}", (0.23, f_sy, 0.01), (0.25, f_sy, 0.01)))
            else:
                bones.append((f"hanim_{side}_distal_phalanx_{num}", f"hanim_{side}_proximal_phalanx_{num}", (0.21, f_sy, 0.01), (0.24, f_sy, 0.01)))

    build_arm("l", 1, "hanim_vt4")
    build_arm("r", -1, "hanim_vt4")
    build_leg("l", 1, "hanim_pelvis")
    build_leg("r", -1, "hanim_pelvis")
    
    return bones

def create_armature():
    arm_data = bpy.data.armatures.new("HAnimSkeleton")
    arm_obj = bpy.data.objects.new("HumanoidArmature", arm_data)
    bpy.context.scene.collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='EDIT')
    
    bones_data = generate_loa4_bones()
    edit_bones = arm_data.edit_bones
    
    for name, parent, head, tail in bones_data:
        b = edit_bones.new(name)
        b.head = head
        b.tail = tail
    
    for name, parent, head, tail in bones_data:
        if parent:
            edit_bones[name].parent = edit_bones[parent]
            edit_bones[name].use_connect = False
            
    bpy.ops.object.mode_set(mode='OBJECT')
    return arm_obj

# ==========================================
# 3. GEOMETRY, SKIN & ATTACHMENTS
# ==========================================
def build_skin(arm_obj):
    bm = bmesh.new()
    
    # Procedurally generate base mesh by wrapping bones with variable radius
    bpy.ops.object.mode_set(mode='EDIT')
    bone_coords = []
    for bone in arm_obj.data.edit_bones:
        r = 0.03 # default radius
        if "pelvis" in bone.name or "sacrum" in bone.name: r = 0.17 # Hips
        elif "vl" in bone.name: r = 0.12 # Waist
        elif "vt" in bone.name: r = 0.15 # Bust
        elif "thigh" in bone.name: r = 0.11 # Thighs
        elif "skull" in bone.name: r = 0.11 # Head
        elif "phalanx" in bone.name: r = 0.006 # Fingers
        
        vec = bone.tail - bone.head
        length = vec.length
        if length < 0.001: continue
        
        rot = vec.to_track_quat('Z', 'Y').to_matrix().to_4x4()
        loc = mathutils.Matrix.Translation(bone.head + vec/2)
        mat = loc @ rot
        bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=8, radius1=r, radius2=r*0.8, depth=length, matrix=mat)

    bpy.ops.object.mode_set(mode='OBJECT')
    
    mesh = bpy.data.meshes.new("SkinMesh")
    bm.to_mesh(mesh)
    bm.free()
    
    skin_obj = bpy.data.objects.new("Skin", mesh)
    bpy.context.scene.collection.objects.link(skin_obj)
    
    # Voxel Remesh to make it watertight and perfectly manifold
    remesh = skin_obj.modifiers.new(name="Remesh", type='REMESH')
    remesh.mode = 'VOXEL'
    remesh.voxel_size = 0.018 # High enough to separate fingers, low enough for smooth skin
    bpy.context.view_layer.objects.active = skin_obj
    bpy.ops.object.modifier_apply(modifier="Remesh")
    
    smooth = skin_obj.modifiers.new(name="Smooth", type='SMOOTH')
    smooth.factor = 0.8
    smooth.iterations = 5
    bpy.ops.object.modifier_apply(modifier="Smooth")
    
    return skin_obj

def build_face_and_hair(arm_obj):
    # Features parented directly to the skull bone per requirements
    def add_feature(name, primitive_func, loc, scale, kwargs):
        primitive_func(**kwargs)
        obj = bpy.context.active_object
        obj.name = name
        obj.location = loc
        obj.scale = scale
        obj.parent = arm_obj
        obj.parent_type = 'BONE'
        obj.parent_bone = "hanim_skull"
        return obj

    # Eyes
    add_feature("Eye_L", bpy.ops.mesh.primitive_uv_sphere_add, (0.09, 0.04, 1.62), (0.015, 0.015, 0.015), {})
    add_feature("Eye_R", bpy.ops.mesh.primitive_uv_sphere_add, (0.09, -0.04, 1.62), (0.015, 0.015, 0.015), {})
    
    # Nose (Geometric)
    add_feature("Nose", bpy.ops.mesh.primitive_cone_add, (0.11, 0, 1.58), (0.02, 0.02, 0.03), {'vertices': 4})
    
    # Lips (Torus)
    add_feature("Lips", bpy.ops.mesh.primitive_torus_add, (0.1, 0, 1.54), (0.02, 0.04, 0.02), {'major_radius': 0.5, 'minor_radius': 0.1})
    bpy.context.active_object.rotation_euler = (0, math.pi/2, 0)
    
    # Ears
    add_feature("Ear_L", bpy.ops.mesh.primitive_uv_sphere_add, (0, 0.1, 1.6), (0.02, 0.01, 0.03), {})
    add_feature("Ear_R", bpy.ops.mesh.primitive_uv_sphere_add, (0, -0.1, 1.6), (0.02, 0.01, 0.03), {})
    
    # Long Hair
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.12, location=(-0.02, 0, 1.65))
    hair = bpy.context.active_object
    hair.name = "Hair"
    hair.scale = (1.1, 1.1, 1.0)
    
    # Extrude down for bangs and back
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(hair.data)
    bm.verts.ensure_lookup_table()
    bottom_verts = [v for v in bm.verts if v.co.z < 0]
    bmesh.ops.extrude_vert_indiv(bm, verts=bottom_verts)
    for v in bottom_verts: v.co.z -= 0.3
    bmesh.update_edit_mesh(hair.data)
    bpy.ops.object.mode_set(mode='OBJECT')
    
    hair.parent = arm_obj
    hair.parent_type = 'BONE'
    hair.parent_bone = "hanim_skull"

# ==========================================
# 4. CLOTHING GENERATION
# ==========================================
def extract_clothing(skin_obj, name, z_min, z_max, expand):
    # Duplicate skin
    new_obj = skin_obj.copy()
    new_obj.data = skin_obj.data.copy()
    new_obj.name = name
    bpy.context.scene.collection.objects.link(new_obj)
    
    bpy.context.view_layer.objects.active = new_obj
    bpy.ops.object.mode_set(mode='EDIT')
    
    bm = bmesh.from_edit_mesh(new_obj.data)
    bm.verts.ensure_lookup_table()
    
    # Delete verts outside bounds
    to_delete = [v for v in bm.verts if v.co.z < z_min or v.co.z > z_max]
    bmesh.ops.delete(bm, geom=to_delete, context='VERTS')
    
    # Shrink/Fatten (Inflate)
    for v in bm.verts:
        v.co += v.normal * expand
        
    bmesh.update_edit_mesh(new_obj.data)
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # Solidify
    sol = new_obj.modifiers.new(name="Solidify", type='SOLIDIFY')
    sol.thickness = 0.01
    bpy.ops.object.modifier_apply(modifier="Solidify")
    
    return new_obj

def build_shoes(arm_obj):
    # Simple high heels parented to feet
    def make_shoe(side, y_pos):
        bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=0.06, radius2=0.04, depth=0.1, location=(0.05, y_pos, 0.05))
        shoe = bpy.context.active_object
        shoe.name = f"Shoe_{side}"
        shoe.rotation_euler = (0, math.pi/4, 0)
        shoe.parent = arm_obj
        shoe.parent_type = 'BONE'
        shoe.parent_bone = f"hanim_{side}_talus"
    make_shoe("l", 0.1)
    make_shoe("r", -0.1)

def build_poncho():
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=45, y_subdivisions=45, size=1.6, location=(0, 0, 1.95))
    poncho = bpy.context.active_object
    poncho.name = "Poncho"
    
    # Cut circular neck hole
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(poncho.data)
    bm.verts.ensure_lookup_table()
    center = mathutils.Vector((0, 0, 1.95))
    to_delete = [v for v in bm.verts if (v.co - center).length < 0.18]
    bmesh.ops.delete(bm, geom=to_delete, context='VERTS')
    bmesh.update_edit_mesh(poncho.data)
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # Cloth Mod
    cloth = poncho.modifiers.new(name="Cloth", type='CLOTH')
    cloth.settings.quality = 7
    cloth.settings.mass = 0.4
    cloth.settings.tension_stiffness = 15.0
    cloth.settings.compression_stiffness = 15.0
    cloth.settings.shear_stiffness = 5.0
    cloth.settings.bending_stiffness = 0.5 # Silk/Velvet
    # cloth.settings.use_internal_friction = True
    cloth.collision_settings.use_self_collision = True
    
    # Thickness
    sol = poncho.modifiers.new(name="Solidify", type='SOLIDIFY')
    sol.thickness = 0.005
    
    # Subsurf for beauty
    sub = poncho.modifiers.new(name="Subsurf", type='SUBSURF')
    sub.levels = 1
    
    return poncho

# ==========================================
# 5. RIGGING & PHYSICS
# ==========================================
def bind_and_physics(arm_obj, skin, blouse, pants):
    # Automatic Weights Binding
    for obj in [skin, blouse, pants]:
        obj.select_set(True)
    arm_obj.select_set(True)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.parent_set(type='ARMATURE_AUTO')
    
    # Add Collision for Cloth
    for obj in [skin, blouse, pants]:
        col = obj.modifiers.new(name="Collision", type='COLLISION')
        col.settings.thickness_outer = 0.045 # Prevents clipping
        
    # Floor collision
    bpy.ops.mesh.primitive_plane_add(size=10, location=(0,0,0))
    floor = bpy.context.active_object
    floor.name = "Floor"
    floor.modifiers.new(name="Collision", type='COLLISION')

# ==========================================
# 6. ANIMATION
# ==========================================
def animate_humanoid(arm_obj):
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='POSE')
    
    # Neutral T-Pose Frames 1 to 60
    for pb in arm_obj.pose.bones:
        pb.rotation_mode = 'QUATERNION'
        pb.keyframe_insert(data_path="rotation_quaternion", frame=1)
        pb.keyframe_insert(data_path="rotation_quaternion", frame=60)
        pb.keyframe_insert(data_path="location", frame=1)
        pb.keyframe_insert(data_path="location", frame=60)
        
    # Frame 120: Bending over
    bpy.context.scene.frame_set(120)
    
    root = arm_obj.pose.bones["hanim_HumanoidRoot"]
    root.location = (0, -0.25, -0.2) # Shift back to balance COM
    root.rotation_quaternion = mathutils.Euler((0, math.radians(10), 0), 'XYZ').to_quaternion()
    
    # Curving the spine dynamically
    for b in arm_obj.pose.bones:
        if "vt" in b.name or "vl" in b.name or "sacrum" in b.name:
            b.rotation_quaternion = mathutils.Euler((0, math.radians(6), 0), 'XYZ').to_quaternion()
            b.keyframe_insert(data_path="rotation_quaternion", frame=120)
            
    # Pelvis forward tilt
    pelvis = arm_obj.pose.bones["hanim_pelvis"]
    pelvis.rotation_quaternion = mathutils.Euler((0, math.radians(30), 0), 'XYZ').to_quaternion()
    pelvis.keyframe_insert(data_path="rotation_quaternion", frame=120)
    
    # Thigh counter-rotation to keep legs straight
    for side in ['l', 'r']:
        thigh = arm_obj.pose.bones[f"hanim_{side}_thigh"]
        thigh.rotation_quaternion = mathutils.Euler((0, math.radians(-40), 0), 'XYZ').to_quaternion()
        thigh.keyframe_insert(data_path="rotation_quaternion", frame=120)
        
    root.keyframe_insert(data_path="location", frame=120)
    root.keyframe_insert(data_path="rotation_quaternion", frame=120)
    
    bpy.ops.object.mode_set(mode='OBJECT')

def bake_physics():
    print("Baking Cloth Physics...")
    #for scene in bpy.data.scenes:
    #    for pt in scene.point_cache:
    #        pt.frame_start = 1
    #        pt.frame_end = 120
    # Override context to ensure bake executes properly
    ctx = bpy.context.copy()
    ctx['point_cache'] = bpy.context.active_object.modifiers["Cloth"].point_cache
    bpy.ops.ptcache.bake_all(ctx, bake=True)

# ==========================================
# 7. CUSTOM X3D EXPORTER
# ==========================================
def quat_to_axis_angle(q):
    angle = 2 * math.acos(max(min(q.w, 1.0), -1.0))
    s = math.sqrt(1 - q.w * q.w)
    if s < 0.001:
        return (0.0, 0.0, 1.0, 0.0)
    return (q.x / s, q.y / s, q.z / s, angle)

def export_x3d(filepath, arm_obj, skin_obj, poncho_obj):
    print(f"Exporting X3D to {filepath}...")
    
    xml = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<X3D profile="Full" version="4.0">',
           '<Scene>',
           '<NavigationInfo type=\'"EXAMINE" "ANY"\'/>',
           '<DirectionalLight direction="0 -1 -1" intensity="1.0"/>',
           '<Viewpoint position="2 1 4" orientation="0 1 0 0.5" description="Side View"/>',
           '<Viewpoint position="0 1 5" description="Front View"/>']
           
    # Fetch weights
    vg_dict = {vg.index: vg.name for vg in skin_obj.vertex_groups}
    joint_weights = {} # bone_name -> (indices, weights)
    
    for v in skin_obj.data.vertices:
        for g in v.groups:
            bname = vg_dict.get(g.group)
            if bname:
                if bname not in joint_weights: joint_weights[bname] = ([], [])
                joint_weights[bname][0].append(str(v.index))
                joint_weights[bname][1].append(str(round(g.weight, 4)))

    # Recursive Bone hierarchy builder
    def build_joint_xml(bone, is_root=False):
        c_field = "skeleton" if is_root else "children"
        center = f"{bone.head.x:.4f} {bone.head.y:.4f} {bone.head.z:.4f}"
        
        idx_str, w_str = "", ""
        if bone.name in joint_weights:
            idx_str = " ".join(joint_weights[bone.name][0])
            w_str = " ".join(joint_weights[bone.name][1])
            
        xml.append(f'<HAnimJoint DEF="{bone.name}" name="{bone.name.replace("hanim_", "")}" containerField="{c_field}" center="{center}" skinCoordIndex="{idx_str}" skinCoordWeight="{w_str}">')
        for child in bone.children:
            build_joint_xml(child)
        xml.append('</HAnimJoint>')

    # 1. Base HAnimHumanoid
    xml.append('<HAnimHumanoid DEF="FemaleHumanoid" name="Female" version="2.0">')
    
    # 2. Add Skeleton
    root_bone = arm_obj.data.bones["hanim_HumanoidRoot"]
    build_joint_xml(root_bone, is_root=True)
    
    # 3. Add USE definitions strictly below skeleton
    for bone in arm_obj.data.bones:
        xml.append(f'<HAnimJoint USE="{bone.name}" containerField="joints"/>')
        
    xml.append('</HAnimHumanoid>')
    
    # 4. Skeleton Animation (OrientationInterpolators)
    bpy.context.scene.frame_set(1)
    keys = " ".join([f"{f/120.0:.3f}" for f in range(1, 121)])
    
    anim_data = {}
    for bone in arm_obj.pose.bones: anim_data[bone.name] = []

    for f in range(1, 121):
        bpy.context.scene.frame_set(f)
        bpy.context.view_layer.update()
        for bone in arm_obj.pose.bones:
            q = bone.rotation_quaternion
            ax, ay, az, angle = quat_to_axis_angle(q)
            anim_data[bone.name].append(f"{ax:.4f} {ay:.4f} {az:.4f} {angle:.4f}")

    xml.append(f'<TimeSensor DEF="Clock" cycleInterval="4.0" loop="true"/>')
    for bname, vals in anim_data.items():
        if all(v == "0.0000 0.0000 1.0000 0.0000" for v in vals): continue # Skip motionless
        val_str = "  ".join(vals)
        xml.append(f'<OrientationInterpolator DEF="{bname}_anim" key="{keys}" keyValue="{val_str}"/>')
        xml.append(f'<ROUTE fromNode="Clock" fromField="fraction_changed" toNode="{bname}_anim" toField="set_fraction"/>')
        # In a full engine, ROUTE sets the rotation of the HAnimJoint, X3D requires routing to 'rotation' field.
        xml.append(f'<ROUTE fromNode="{bname}_anim" fromField="value_changed" toNode="{bname}" toField="rotation"/>')

    # 5. Baked Cloth Vertex Animation (CoordinateInterpolator)
    poncho_coords = []
    # To extract evaluated cloth points frame-by-frame
    dg = bpy.context.evaluated_depsgraph_get()
    for f in range(1, 121):
        bpy.context.scene.frame_set(f)
        eval_poncho = poncho_obj.evaluated_get(dg)
        mesh = eval_poncho.to_mesh()
        frame_pts = [f"{v.co.x:.4f} {v.co.y:.4f} {v.co.z:.4f}" for v in mesh.vertices]
        poncho_coords.append(", ".join(frame_pts))
        eval_poncho.to_mesh_clear()
        
    all_coords = "  ".join(poncho_coords)
    xml.append(f'<CoordinateInterpolator DEF="PonchoAnim" key="{keys}" keyValue="{all_coords}"/>')
    
    xml.append('<Transform DEF="PonchoTransform">')
    xml.append('<Shape>')
    xml.append('<Appearance><Material diffuseColor="0.8 0.1 0.2" shininess="0.9"/></Appearance>')
    
    # Base faces
    mesh = poncho_obj.data
    faces = []
    for p in mesh.polygons:
        faces.append(" ".join(str(v) for v in p.vertices) + " -1")
    xml.append(f'<IndexedFaceSet coordIndex="{" ".join(faces)}" solid="false">')
    
    base_pts = poncho_coords[0]
    xml.append(f'<Coordinate DEF="PonchoCoord" point="{base_pts}"/>')
    xml.append('</IndexedFaceSet></Shape></Transform>')
    
    xml.append('<ROUTE fromNode="Clock" fromField="fraction_changed" toNode="PonchoAnim" toField="set_fraction"/>')
    xml.append('<ROUTE fromNode="PonchoAnim" fromField="value_changed" toNode="PonchoCoord" toField="point"/>')

    xml.append('</Scene></X3D>')
    
    with open(filepath, 'w') as f:
        f.write("\n".join(xml))
    print("X3D Export Complete.")

# ==========================================
# MAIN EXECUTION
# ==========================================
def main():
    cleanup_scene()
    
    # Build Armature
    arm_obj = create_armature()
    
    # Build Geometry
    skin_obj = build_skin(arm_obj)
    build_face_and_hair(arm_obj)
    
    # Build Clothing
    blouse = extract_clothing(skin_obj, "Blouse", 0.9, 1.45, 0.005)
    pants = extract_clothing(skin_obj, "Pants", 0.1, 0.95, 0.006)
    build_shoes(arm_obj)
    poncho = build_poncho()
    
    # Rigging & Physics Setup
    bind_and_physics(arm_obj, skin_obj, blouse, pants)
    animate_humanoid(arm_obj)
    
    # Bake Simulations
    bake_physics()
    
    # X3D Export
    home_dir = os.path.expanduser("~")
    export_path = os.path.join(home_dir, "hanim_cloth_simulation.x3d")
    export_x3d(export_path, arm_obj, skin_obj, poncho)
    
    # Final View
    bpy.context.scene.frame_set(60)

if __name__ == "__main__":
    main()
