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
    for coll in bpy.data.collections: bpy.data.collections.remove(coll)
    for block in bpy.data.meshes: bpy.data.meshes.remove(block)
    for block in bpy.data.armatures: bpy.data.armatures.remove(block)
    for block in bpy.data.materials: bpy.data.materials.remove(block)

    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = 120
    # Set standard gravity
    bpy.context.scene.gravity = (0, 0, -9.81)

# ==========================================
# 2. HANIM LOA4 SKELETON GENERATOR
# ==========================================
def generate_loa4_bones():
    """Generates standard HAnim LOA4 standard skeleton. Facing +X axis."""
    bones = []

    # Core Spine (Sacrum to Skull)
    bones.append(("hanim_HumanoidRoot", None, (0, 0, 0.95), (0, 0, 1.0)))
    bones.append(("hanim_sacrum", "hanim_HumanoidRoot", (0, 0, 1.0), (0, 0, 1.05)))
    bones.append(("hanim_pelvis", "hanim_sacrum", (0, 0, 1.05), (0, 0, 1.1)))

    prev = "hanim_pelvis"
    z_curr = 1.1
    for i in range(5, 0, -1): # Lumbar
        name, z_next = f"hanim_vl{i}", z_curr + 0.03
        bones.append((name, prev, (0, 0, z_curr), (0, 0, z_next)))
        prev, z_curr = name, z_next
    for i in range(12, 0, -1): # Thoracic
        name, z_next = f"hanim_vt{i}", z_curr + 0.02
        bones.append((name, prev, (0, 0, z_curr), (0, 0, z_next)))
        prev, z_curr = name, z_next
    for i in range(7, 0, -1): # Cervical
        name, z_next = f"hanim_vc{i}", z_curr + 0.015
        bones.append((name, prev, (0, 0, z_curr), (0, 0, z_next)))
        prev, z_curr = name, z_next

    bones.append(("hanim_skullbase", prev, (0, 0, z_curr), (0, 0, z_curr + 0.02)))
    bones.append(("hanim_skull", "hanim_skullbase", (0, 0, z_curr + 0.02), (0, 0, z_curr + 0.15)))

    # Limbs (X is Forward, Y is Lateral +/-)
    def build_arm(side, y_dir, parent):
        sy = y_dir
        bones.append((f"hanim_{side}_clavicle", parent, (0, 0.02*sy, 1.45), (0, 0.15*sy, 1.45)))
        bones.append((f"hanim_{side}_scapula", f"hanim_{side}_clavicle", (0, 0.15*sy, 1.45), (0, 0.16*sy, 1.43)))
        bones.append((f"hanim_{side}_upperarm", f"hanim_{side}_scapula", (0, 0.16*sy, 1.43), (0, 0.22*sy, 1.15)))
        bones.append((f"hanim_{side}_forearm", f"hanim_{side}_upperarm", (0, 0.22*sy, 1.15), (0, 0.24*sy, 0.9)))
        bones.append((f"hanim_{side}_carpal", f"hanim_{side}_forearm", (0, 0.24*sy, 0.9), (0, 0.25*sy, 0.88)))

        for idx, finger in enumerate(["thumb", "index", "middle", "ring", "pinky"]):
            f_sy = sy * (0.23 + idx*0.01)
            b_parent = f"hanim_{side}_carpal"
            num = idx + 1
            bones.append((f"hanim_{side}_metacarpal_{num}", b_parent, (0, 0.25*sy, 0.88), (0, f_sy, 0.84)))
            bones.append((f"hanim_{side}_proximal_phalanx_{num}", f"hanim_{side}_metacarpal_{num}", (0, f_sy, 0.84), (0, f_sy, 0.81)))
            if finger != "thumb":
                bones.append((f"hanim_{side}_middle_phalanx_{num}", f"hanim_{side}_proximal_phalanx_{num}", (0, f_sy, 0.81), (0, f_sy, 0.79)))
                bones.append((f"hanim_{side}_distal_phalanx_{num}", f"hanim_{side}_middle_phalanx_{num}", (0, f_sy, 0.79), (0, f_sy, 0.77)))
            else:
                bones.append((f"hanim_{side}_distal_phalanx_{num}", f"hanim_{side}_proximal_phalanx_{num}", (0, f_sy, 0.81), (0, f_sy, 0.79)))

    def build_leg(side, y_dir, parent):
        sy = y_dir
        bones.append((f"hanim_{side}_hip", parent, (0, 0.08*sy, 1.05), (0, 0.12*sy, 1.0)))
        bones.append((f"hanim_{side}_thigh", f"hanim_{side}_hip", (0, 0.12*sy, 1.0), (0, 0.12*sy, 0.55)))
        bones.append((f"hanim_{side}_calf", f"hanim_{side}_thigh", (0, 0.12*sy, 0.55), (0, 0.12*sy, 0.15)))
        bones.append((f"hanim_{side}_talus", f"hanim_{side}_calf", (0, 0.12*sy, 0.15), (0.05, 0.12*sy, 0.08)))
        bones.append((f"hanim_{side}_navicular", f"hanim_{side}_talus", (0.05, 0.12*sy, 0.08), (0.1, 0.12*sy, 0.05)))
        bones.append((f"hanim_{side}_cuneiform_2", f"hanim_{side}_navicular", (0.1, 0.12*sy, 0.05), (0.13, 0.12*sy, 0.03)))

        for num in range(1, 6):
            f_sy = sy * (0.09 + num*0.015)
            bones.append((f"hanim_{side}_metatarsal_{num}", f"hanim_{side}_cuneiform_2", (0.13, 0.12*sy, 0.03), (0.18, f_sy, 0.02)))
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
    arm_obj = bpy.data.objects.new("FemaleArmature", arm_data)
    bpy.context.scene.collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='EDIT')

    bones_data = generate_loa4_bones()
    edit_bones = arm_data.edit_bones

    for name, parent, head, tail in bones_data:
        b = edit_bones.new(name)
        b.head, b.tail = head, tail
    for name, parent, head, tail in bones_data:
        if parent:
            edit_bones[name].parent = edit_bones[parent]
            edit_bones[name].use_connect = False

    bpy.ops.object.mode_set(mode='OBJECT')
    return arm_obj

# ==========================================
# 3. GEOMETRY, SKIN & FEATURES
# ==========================================
def build_skin(arm_obj):
    bm = bmesh.new()
    bpy.ops.object.mode_set(mode='EDIT')

    # Wrap bones to ensure armature is perfectly enclosed. Wider hips/bust, padded shoulders.
    for bone in arm_obj.data.edit_bones:
        r = 0.035 # Default radius
        if "pelvis" in bone.name or "sacrum" in bone.name: r = 0.16 # Wider hips
        elif "vl" in bone.name: r = 0.12 # Waist
        elif "vt" in bone.name: r = 0.14 # Bust / Chest
        elif "clavicle" in bone.name or "scapula" in bone.name: r = 0.08 # Solid shoulders to catch the poncho
        elif "thigh" in bone.name: r = 0.11 # Thighs
        elif "skull" in bone.name: r = 0.10 # Head
        elif "phalanx" in bone.name or "carpal" in bone.name: r = 0.008 # Fingers/Hands

        vec = bone.tail - bone.head
        length = vec.length
        if length < 0.001: continue

        rot = vec.to_track_quat('Z', 'Y').to_matrix().to_4x4()
        loc = mathutils.Matrix.Translation(bone.head + vec/2)
        mat = loc @ rot
        bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=12, radius1=r, radius2=r*0.8, depth=length, matrix=mat)

    bpy.ops.object.mode_set(mode='OBJECT')

    mesh = bpy.data.meshes.new("SkinMesh")
    bm.to_mesh(mesh)
    bm.free()

    skin_obj = bpy.data.objects.new("Skin", mesh)
    bpy.context.scene.collection.objects.link(skin_obj)

    # Voxel Remesh to make it watertight and perfectly manifold
    remesh = skin_obj.modifiers.new(name="Remesh", type='REMESH')
    remesh.mode = 'VOXEL'
    remesh.voxel_size = 0.015 # Fine enough to separate fingers, coarse enough to be smooth
    bpy.context.view_layer.objects.active = skin_obj
    bpy.ops.object.modifier_apply(modifier="Remesh")

    smooth = skin_obj.modifiers.new(name="Smooth", type='SMOOTH')
    smooth.factor = 0.8
    smooth.iterations = 8
    bpy.ops.object.modifier_apply(modifier="Smooth")

    return skin_obj

def build_face_and_hair(arm_obj):
    # Features parented directly to the skull bone per strict HAnim rules
    def add_feature(name, primitive_func, loc, scale, kwargs, rot=(0,0,0)):
        primitive_func(**kwargs)
        obj = bpy.context.active_object
        obj.name = name
        obj.location = loc
        obj.scale = scale
        obj.rotation_euler = rot
        obj.parent = arm_obj
        obj.parent_type = 'BONE'
        obj.parent_bone = "hanim_skull"
        return obj

    # X is Forward, Y is Lateral (+L, -R), Z is Up
    # Eyes
    add_feature("Eye_L", bpy.ops.mesh.primitive_uv_sphere_add, (0.09, 0.04, 1.62), (0.015, 0.015, 0.015), {})
    add_feature("Eye_R", bpy.ops.mesh.primitive_uv_sphere_add, (0.09, -0.04, 1.62), (0.015, 0.015, 0.015), {})

    # Nose
    add_feature("Nose", bpy.ops.mesh.primitive_cone_add, (0.11, 0, 1.58), (0.02, 0.02, 0.03), {'vertices': 4}, (0, math.radians(-15), 0))

    # Lips
    add_feature("Lips", bpy.ops.mesh.primitive_torus_add, (0.1, 0, 1.54), (0.02, 0.04, 0.02), {'major_radius': 0.5, 'minor_radius': 0.1}, (0, math.pi/2, 0))

    # Ears
    add_feature("Ear_L", bpy.ops.mesh.primitive_uv_sphere_add, (0, 0.1, 1.6), (0.02, 0.01, 0.03), {})
    add_feature("Ear_R", bpy.ops.mesh.primitive_uv_sphere_add, (0, -0.1, 1.6), (0.02, 0.01, 0.03), {})

    # Hair: Solid attached mesh, skinned like muscle to bone
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.11, location=(-0.02, 0, 1.65))
    hair = bpy.context.active_object
    hair.name = "Hair"
    hair.scale = (1.05, 1.1, 1.0)

    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(hair.data)
    bm.verts.ensure_lookup_table()
    # Pull lower rear vertices down for long back hair/bangs
    for v in bm.verts:
        if v.co.z < 0 and v.co.x < 0:
            v.co.z -= 0.35
            v.co.x -= 0.1
    bmesh.update_edit_mesh(hair.data)
    bpy.ops.object.mode_set(mode='OBJECT')

    hair.parent = arm_obj
    hair.parent_type = 'BONE'
    hair.parent_bone = "hanim_skull"

# ==========================================
# 4. CLOTHING GENERATION
# ==========================================
def extract_clothing(skin_obj, name, z_min, z_max, expand):
    new_obj = skin_obj.copy()
    new_obj.data = skin_obj.data.copy()
    new_obj.name = name
    bpy.context.scene.collection.objects.link(new_obj)

    bpy.context.view_layer.objects.active = new_obj
    bpy.ops.object.mode_set(mode='EDIT')

    bm = bmesh.from_edit_mesh(new_obj.data)
    bm.verts.ensure_lookup_table()

    to_delete = [v for v in bm.verts if v.co.z < z_min or v.co.z > z_max]
    bmesh.ops.delete(bm, geom=to_delete, context='VERTS')

    # Shrink/Fatten to sit outside the body
    for v in bm.verts:
        v.co += v.normal * expand

    bmesh.update_edit_mesh(new_obj.data)
    bpy.ops.object.mode_set(mode='OBJECT')

    sol = new_obj.modifiers.new(name="Solidify", type='SOLIDIFY')
    sol.thickness = 0.008
    bpy.ops.object.modifier_apply(modifier="Solidify")

    return new_obj

def build_shoes(arm_obj):
    def make_shoe(side, y_pos):
        bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=0.06, radius2=0.04, depth=0.1, location=(0.05, y_pos, 0.05))
        shoe = bpy.context.active_object
        shoe.name = f"Shoe_{side}"
        shoe.rotation_euler = (0, math.pi/4, 0)
        shoe.parent = arm_obj
        shoe.parent_type = 'BONE'
        shoe.parent_bone = f"hanim_{side}_talus"
    make_shoe("l", 0.12)
    make_shoe("r", -0.12)

def build_poncho():
    # Large plane above the humanoid. Drop onto shoulders from head height.
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=65, y_subdivisions=65, size=1.8, location=(0, 0, 1.85))
    poncho = bpy.context.active_object
    poncho.name = "Poncho"

    # Cut circular neck hole
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(poncho.data)
    bm.verts.ensure_lookup_table()
    center = mathutils.Vector((0, 0, 1.85))
    # Hole radius ~0.14m. Big enough to slip over head (r=0.10) but catches securely on shoulders (span = 0.44m)
    to_delete = [v for v in bm.verts if (v.co - center).length < 0.14]
    bmesh.ops.delete(bm, geom=to_delete, context='VERTS')
    bmesh.update_edit_mesh(poncho.data)
    bpy.ops.object.mode_set(mode='OBJECT')

    # Advanced Cloth Modifiers
    cloth = poncho.modifiers.new(name="Cloth", type='CLOTH')
    cloth.settings.quality = 10
    cloth.settings.mass = 0.3
    cloth.settings.tension_stiffness = 15.0
    cloth.settings.compression_stiffness = 15.0
    cloth.settings.shear_stiffness = 5.0
    cloth.settings.bending_stiffness = 0.1 # Silk/Velvet (very low resistance allows tight draping)

    cloth.collision_settings.use_collision = True
    cloth.collision_settings.use_self_collision = True
    cloth.collision_settings.friction = 40.0 # High friction so it grabs the shoulders and doesn't slip off
    cloth.collision_settings.distance_min = 0.015

    sol = poncho.modifiers.new(name="Solidify", type='SOLIDIFY')
    sol.thickness = 0.004

    sub = poncho.modifiers.new(name="Subsurf", type='SUBSURF')
    sub.levels = 1

    return poncho

# ==========================================
# 5. RIGGING & PHYSICS
# ==========================================
def bind_and_physics(arm_obj, skin, blouse, pants):
    # Bind meshes to armature
    for obj in [skin, blouse, pants]:
        obj.select_set(True)
    arm_obj.select_set(True)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.parent_set(type='ARMATURE_AUTO')

    # Collision setup for the body to catch the cloth securely
    for obj in [skin, blouse, pants]:
        col = obj.modifiers.new(name="Collision", type='COLLISION')
        col.settings.thickness_outer = 0.03 # Boundary to prevent clipping through skin
        col.settings.cloth_friction = 35.0 # CORRECT API CALL

    # Floor to ensure cloth/feet don't drop endlessly
    bpy.ops.mesh.primitive_plane_add(size=10, location=(0,0,0))
    floor = bpy.context.active_object
    floor.name = "Floor"
    floor_col = floor.modifiers.new(name="Collision", type='COLLISION')
    floor_col.settings.cloth_friction = 50.0

# ==========================================
# 6. ANIMATION
# ==========================================
def animate_humanoid(arm_obj):
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='POSE')

    # Insert Neutral T-Pose at Frame 1 & 60 (Allows cloth to settle perfectly on shoulders first)
    for pb in arm_obj.pose.bones:
        pb.rotation_mode = 'QUATERNION'
        pb.keyframe_insert(data_path="rotation_quaternion", frame=1)
        pb.keyframe_insert(data_path="rotation_quaternion", frame=60)
        pb.keyframe_insert(data_path="location", frame=1)
        pb.keyframe_insert(data_path="location", frame=60)

    # Frame 120: Bend at waist to touch toes
    bpy.context.scene.frame_set(120)

    root = arm_obj.pose.bones["hanim_HumanoidRoot"]
    root.location = (-0.25, 0, -0.3) # Shift back in -X and down in -Z to maintain Center of Mass
    root.keyframe_insert(data_path="location", frame=120)

    # Cumulative spine bend forward (Rotation around Y axis)
    bend_angle = math.radians(10)
    for b in arm_obj.pose.bones:
        if any(spine in b.name for spine in ["vt", "vl", "sacrum"]):
            b.rotation_quaternion = mathutils.Euler((0, bend_angle, 0), 'XYZ').to_quaternion()
            b.keyframe_insert(data_path="rotation_quaternion", frame=120)

    # Pelvis forward tilt
    pelvis = arm_obj.pose.bones["hanim_pelvis"]
    pelvis.rotation_quaternion = mathutils.Euler((0, math.radians(45), 0), 'XYZ').to_quaternion()
    pelvis.keyframe_insert(data_path="rotation_quaternion", frame=120)

    # Counter-rotate thighs backward so legs remain vertical and firmly planted
    for side in ['l', 'r']:
        thigh = arm_obj.pose.bones[f"hanim_{side}_thigh"]
        thigh.rotation_quaternion = mathutils.Euler((0, math.radians(-50), 0), 'XYZ').to_quaternion()
        thigh.keyframe_insert(data_path="rotation_quaternion", frame=120)

    bpy.ops.object.mode_set(mode='OBJECT')

def bake_physics():
    print("Baking Cloth Physics...")

    poncho = bpy.data.objects["Poncho"]
    bpy.context.view_layer.objects.active = poncho
    poncho.select_set(True)

    # Update cache frame bounds directly on the cloth modifier
    cloth_mod = poncho.modifiers.get("Cloth")
    if cloth_mod and hasattr(cloth_mod, 'point_cache'):
        cloth_mod.point_cache.frame_start = 1
        cloth_mod.point_cache.frame_end = 120

    # Safe baking execution using overrides for Blender 4.x/5.0
    with bpy.context.temp_override(active_object=poncho, selected_objects=[poncho]):
        bpy.ops.ptcache.bake_all(bake=True)

# ==========================================
# 7. CUSTOM X3D EXPORTER
# ==========================================
def quat_to_axis_angle(q):
    angle = 2 * math.acos(max(min(q.w, 1.0), -1.0))
    s = math.sqrt(1 - q.w * q.w)
    if s < 0.001: return (0.0, 1.0, 0.0, 0.0)
    return (q.x / s, q.y / s, q.z / s, angle)

def export_x3d(filepath, arm_obj, skin_obj, poncho_obj):
    print(f"Exporting strict HAnim X3D to {filepath}...")

    xml = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<!DOCTYPE X3D PUBLIC "ISO//Web3D//DTD X3D 4.0//EN" "http://www.web3d.org/specifications/x3d-4.0.dtd">',
           '<X3D profile="Full" version="4.0">',
           '<Scene>',
           '<NavigationInfo type=\'"EXAMINE" "ANY"\'/>',
           '<DirectionalLight direction="0 -1 -1" intensity="0.8"/>',
           '<DirectionalLight direction="0 1 -0.5" intensity="0.5"/>',
           '<Viewpoint position="3 1.5 3" orientation="0 1 0 0.8" description="Perspective View"/>']

    # Pre-calculate Vertex Weights for Skin
    vg_dict = {vg.index: vg.name for vg in skin_obj.vertex_groups}
    joint_weights = {} # bone_name -> (indices_str, weights_str)

    for v in skin_obj.data.vertices:
        for g in v.groups:
            bname = vg_dict.get(g.group)
            if bname:
                if bname not in joint_weights: joint_weights[bname] = ([], [])
                joint_weights[bname][0].append(str(v.index))
                joint_weights[bname][1].append(f"{g.weight:.4f}")

    # Recursive Bone hierarchy builder for standard HAnim Structure
    def build_joint_xml(bone, is_root=False):
        c_field = "skeleton" if is_root else "children"
        center = f"{bone.head.x:.5f} {bone.head.y:.5f} {bone.head.z:.5f}"

        idx_str = " ".join(joint_weights[bone.name][0]) if bone.name in joint_weights else ""
        w_str = " ".join(joint_weights[bone.name][1]) if bone.name in joint_weights else ""

        attr_str = f'DEF="{bone.name}" name="{bone.name.replace("hanim_", "")}" containerField="{c_field}" center="{center}"'
        if idx_str:
            attr_str += f' skinCoordIndex="{idx_str}" skinCoordWeight="{w_str}"'

        xml.append(f'<HAnimJoint {attr_str}>')
        for child in bone.children:
            build_joint_xml(child)
        xml.append('</HAnimJoint>')

    # 1. Base HAnimHumanoid Definition
    xml.append('<HAnimHumanoid DEF="FemaleHumanoid" name="Female" version="2.0">')

    # 2. Add Skeleton Container
    root_bone = arm_obj.data.bones["hanim_HumanoidRoot"]
    build_joint_xml(root_bone, is_root=True)

    # 3. Add USE Definitions (Strict requirement for HAnim binding)
    for bone in arm_obj.data.bones:
        xml.append(f'<HAnimJoint USE="{bone.name}" containerField="joints"/>')

    xml.append('</HAnimHumanoid>')

    # 4. Export Rigidbody Animation via OrientationInterpolators
    bpy.context.scene.frame_set(1)
    keys = " ".join([f"{(f-1)/119.0:.4f}" for f in range(1, 121)])

    anim_data = {bone.name: [] for bone in arm_obj.pose.bones}

    for f in range(1, 121):
        bpy.context.scene.frame_set(f)
        bpy.context.view_layer.update()
        for bone in arm_obj.pose.bones:
            q = bone.rotation_quaternion
            ax, ay, az, angle = quat_to_axis_angle(q)
            anim_data[bone.name].append(f"{ax:.5f} {ay:.5f} {az:.5f} {angle:.5f}")

    xml.append('<TimeSensor DEF="AnimClock" cycleInterval="5.0" loop="true"/>')
    for bname, vals in anim_data.items():
        if all(v == "0.0000 1.0000 0.0000 0.0000" for v in vals): continue # Skip if unmoving
        val_str = "  ".join(vals)
        xml.append(f'<OrientationInterpolator DEF="{bname}_anim" key="{keys}" keyValue="{val_str}"/>')
        xml.append(f'<ROUTE fromNode="AnimClock" fromField="fraction_changed" toNode="{bname}_anim" toField="set_fraction"/>')
        xml.append(f'<ROUTE fromNode="{bname}_anim" fromField="value_changed" toNode="{bname}" toField="rotation"/>')

    # 5. Extract and Export Evaluated Cloth Vertex Animation
    poncho_coords = []
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

    # 6. Build Renderable Poncho Shape
    xml.append('<Transform DEF="PonchoTransform">')
    xml.append('<Shape>')
    xml.append('<Appearance><Material diffuseColor="0.8 0.1 0.3" shininess="0.4" specularColor="0.2 0.2 0.2"/></Appearance>')

    mesh = poncho_obj.data
    faces = [" ".join(str(v) for v in p.vertices) + " -1" for p in mesh.polygons]
    xml.append(f'<IndexedFaceSet coordIndex="{" ".join(faces)}" solid="false">')

    base_pts = poncho_coords[0]
    xml.append(f'<Coordinate DEF="PonchoCoord" point="{base_pts}"/>')
    xml.append('</IndexedFaceSet></Shape></Transform>')

    # Route for cloth playback
    xml.append('<ROUTE fromNode="AnimClock" fromField="fraction_changed" toNode="PonchoAnim" toField="set_fraction"/>')
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

    # 1. Build Framework
    arm_obj = create_armature()

    # 2. Build Characters & Features
    skin_obj = build_skin(arm_obj)
    build_face_and_hair(arm_obj)

    # 3. Build Attire & Props
    blouse = extract_clothing(skin_obj, "Blouse", 0.9, 1.45, 0.006)
    pants = extract_clothing(skin_obj, "Pants", 0.1, 0.95, 0.007)
    build_shoes(arm_obj)
    poncho = build_poncho()

    # 4. Setup Simulation Links
    bind_and_physics(arm_obj, skin_obj, blouse, pants)
    animate_humanoid(arm_obj)

    # 5. Calculate Physics Cache
    bake_physics()

    # 6. Frame evaluation & standards-compliant export
    home_dir = os.path.expanduser("~")
    export_path = os.path.join(home_dir, "hanim_poncho_simulation.x3d")
    export_x3d(export_path, arm_obj, skin_obj, poncho)

    # Set to final pose frame to view in Blender
    bpy.context.scene.frame_set(120)
    print(f"Success! X3D Output saved to {export_path}")

if __name__ == "__main__":
    main()
