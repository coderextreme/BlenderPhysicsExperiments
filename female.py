import bpy
import bmesh
import math
import os
import xml.etree.ElementTree as ET
from mathutils import Vector, Quaternion, Matrix

# --- CONFIGURATION ---
EXPORT_FILENAME = "hanim_female_loa4.x3d"
START_FRAME = 1
END_FRAME = 120
ANIM_START_FRAME = 40 # Allow time for poncho to drape
GENDER_PROPORTIONS = {
    'hips': 1.6,
    'waist': 0.75,
    'chest': 1.3,
    'shoulders': 0.9
}

def clear_scene():
    if bpy.context.active_object and bpy.context.active_object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for col in bpy.data.collections:
        if col.name != "Collection": bpy.data.collections.remove(col)
    for mesh in bpy.data.meshes: bpy.data.meshes.remove(mesh)
    for arm in bpy.data.armatures: bpy.data.armatures.remove(arm)
    for mat in bpy.data.materials: bpy.data.materials.remove(mat)

def ensure_lookup(bm):
    if hasattr(bm, "ensure_lookup_table"):
        bm.ensure_lookup_table()

def find_view3d():
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D': return area
    return None

# --- ARMATURE ---
def create_hanim_skeleton():
    bpy.ops.object.armature_add(enter_editmode=True, align='WORLD', location=(0, 0, 0))
    arm_obj = bpy.context.active_object
    arm_obj.name = "HAnimHumanoid"
    amt = arm_obj.data
    amt.name = "HAnimArmature"
    for bone in amt.edit_bones: amt.edit_bones.remove(bone)

    def add_bone(name, head, tail, parent_arg=None):
        bone = amt.edit_bones.new(name)
        bone.head = head
        bone.tail = tail
        parent = None
        if isinstance(parent_arg, str):
            if parent_arg in amt.edit_bones: parent = amt.edit_bones[parent_arg]
        elif hasattr(parent_arg, "name"): parent = parent_arg
        if parent:
            bone.parent = parent
            bone.use_connect = True
        return bone

    h = 1.75
    # Spine
    root = add_bone("humanoid_root", (0, 0, h*0.58), (0, 0, h*0.62), None)
    sacroiliac = add_bone("sacroiliac", (0, 0, h*0.58), (0, 0, h*0.585), "humanoid_root")
    l5 = add_bone("l5", (0, 0, h*0.62), (0, 0, h*0.65), "humanoid_root")
    l1 = add_bone("l1", (0, 0, h*0.65), (0, 0, h*0.70), "l5")
    t12 = add_bone("t12", (0, 0, h*0.70), (0, 0, h*0.75), "l1")
    t6 = add_bone("t6", (0, 0, h*0.75), (0, 0, h*0.82), "t12")
    t1 = add_bone("t1", (0, 0, h*0.82), (0, 0, h*0.88), "t6")
    c7 = add_bone("c7", (0, 0, h*0.88), (0, 0, h*0.92), "t1")
    c1 = add_bone("c1", (0, 0, h*0.92), (0, 0, h*0.95), "c7")
    skull = add_bone("skull", (0, 0, h*0.95), (0, 0, h*1.0), "c1")

    # Legs
    hip_width = 0.16 * GENDER_PROPORTIONS['hips']
    for side, prefix, mult in [('l', 'l', 1), ('r', 'r', -1)]:
        hip = add_bone(f"{prefix}_hip", (0, 0, h*0.58), (mult * hip_width, 0, h*0.53), "sacroiliac")
        knee = add_bone(f"{prefix}_knee", (mult * hip_width, 0, h*0.53), (mult * hip_width, 0.02, h*0.28), hip)
        talus = add_bone(f"{prefix}_talus", (mult * hip_width, 0.02, h*0.28), (mult * hip_width, 0.04, h*0.06), knee)
        metatarsal = add_bone(f"{prefix}_metatarsal", (mult * hip_width, 0.04, h*0.06), (mult * hip_width, -0.12, 0.0), talus)
        add_bone(f"{prefix}_tarsal_distal_phalanx", (mult * hip_width, -0.12, 0.0), (mult * hip_width, -0.18, 0.0), metatarsal)

    # Arms
    shoulder_width = 0.18 * GENDER_PROPORTIONS['shoulders']
    for side, prefix, mult in [('l', 'l', 1), ('r', 'r', -1)]:
        clavicle = add_bone(f"{prefix}_sternoclavicular", (0, 0, h*0.86), (mult * 0.05, -0.02, h*0.87), "t1")
        shoulder = add_bone(f"{prefix}_acromioclavicular", (mult * 0.05, -0.02, h*0.87), (mult * shoulder_width, 0, h*0.87), clavicle)
        elbow = add_bone(f"{prefix}_elbow", (mult * shoulder_width, 0, h*0.87), (mult * (shoulder_width + 0.05), 0, h*0.65), shoulder)
        wrist = add_bone(f"{prefix}_wrist", (mult * (shoulder_width + 0.05), 0, h*0.65), (mult * (shoulder_width + 0.08), 0.05, h*0.48), elbow)
        add_bone(f"{prefix}_carpal", (mult * (shoulder_width + 0.08), 0.05, h*0.48), (mult * (shoulder_width + 0.08), 0.05, h*0.40), wrist)

    bpy.ops.object.mode_set(mode='OBJECT')
    return arm_obj

# --- BODY GEOMETRY ---
def create_body_mesh(arm_obj):
    mesh = bpy.data.meshes.new("SkinMesh")
    obj = bpy.data.objects.new("Skin", mesh)
    bpy.context.collection.objects.link(obj)

    # 1. Ensure obj is Active AND Selected
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    bm = bmesh.new()
    vertex_map = {}
    def get_vert(co):
        k = (round(co.x, 4), round(co.y, 4), round(co.z, 4))
        if k not in vertex_map: vertex_map[k] = bm.verts.new(co)
        return vertex_map[k]

    amt = arm_obj.data
    radius_data = {}
    root_coord_key = None

    for bone in amt.bones:
        v1 = get_vert(bone.head_local)
        v2 = get_vert(bone.tail_local)
        if bone.name == "humanoid_root":
            root_coord_key = (round(v1.co.x, 4), round(v1.co.y, 4), round(v1.co.z, 4))
        try: bm.edges.new((v1, v2))
        except ValueError: pass

        r1, r2 = 0.05, 0.05
        n = bone.name
        if "hip" in n: r1, r2 = 0.08 * 1.6, 0.07 * 1.6
        elif "knee" in n: r1, r2 = 0.06, 0.04
        elif "spine" in n or "l1" in n or "l5" in n: r1, r2 = 0.12*1.6, 0.09*0.75
        elif "t12" in n or "t6" in n: r1, r2 = 0.10*0.75, 0.13*1.3
        elif "t1" in n: r1, r2 = 0.13*1.3, 0.06
        elif "skull" in n: r1, r2 = 0.06, 0.10
        elif "wrist" in n: r1, r2 = 0.03, 0.02

        for v, r in [(v1, r1), (v2, r2)]:
            k = (round(v.co.x, 4), round(v.co.y, 4), round(v.co.z, 4))
            radius_data[k] = max(radius_data.get(k, 0), r)

    ensure_lookup(bm)
    bm.to_mesh(mesh)
    bm.free()

    mod = obj.modifiers.new("Skin", 'SKIN')
    mod.use_smooth_shade = True
    obj.modifiers.new("Subsurf", 'SUBSURF').levels = 1

    # Mark Root in Edit Mode
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bm = bmesh.from_edit_mesh(mesh)
    ensure_lookup(bm)
    layer = bm.verts.layers.skin.verify()
    root_vert = None
    for v in bm.verts:
        k = (round(v.co.x, 4), round(v.co.y, 4), round(v.co.z, 4))
        rad = radius_data.get(k, 0.05)
        v[layer].radius = (rad, rad)
        if k == root_coord_key: root_vert = v

    if root_vert:
        root_vert.select = True
        bmesh.update_edit_mesh(mesh)
        area = find_view3d()
        if area:
            with bpy.context.temp_override(area=area):
                try: bpy.ops.mesh.skin_root_mark()
                except Exception as e: print(f"Root warning: {e}")

    bpy.ops.object.mode_set(mode='OBJECT')

    # Convert to Mesh
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.convert(target='MESH')

    # --- CRITICAL FIX: RECALCULATE NORMALS ---
    # The Skin modifier often outputs inverted normals or chaotic winding.
    # We must force them to point OUTWARD for physics to work.
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    # ----------------------------------------

    bpy.ops.object.shade_smooth()
    return obj

def add_features(body_obj, arm_obj):
    head_bone = arm_obj.data.bones["skull"]
    head_loc = arm_obj.matrix_world @ head_bone.head_local
    head_top = arm_obj.matrix_world @ head_bone.tail_local

    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.12, location=(head_loc.x, head_loc.y + 0.02, head_top.z - 0.02))
    bun = bpy.context.active_object
    bun.scale = (0.9, 1.1, 0.8)

    z = head_loc.z + 0.05
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.015, location=(0.035, -0.09, z))
    el = bpy.context.active_object
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.015, location=(-0.035, -0.09, z))
    er = bpy.context.active_object

    for o in [bun, el, er]: o.select_set(True)
    body_obj.select_set(True)
    bpy.context.view_layer.objects.active = body_obj
    bpy.ops.object.join()

    # Recalculate normals again just in case join messed them up
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode='OBJECT')

def create_clothes(body_obj):
    bpy.ops.object.select_all(action='DESELECT')
    body_obj.select_set(True)
    bpy.context.view_layer.objects.active = body_obj
    bpy.ops.object.duplicate()
    clothes = bpy.context.active_object
    clothes.name = "Clothes_Tight"

    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(clothes.data)
    ensure_lookup(bm)
    dels = [f for f in bm.faces if f.calc_center_median().z > 1.62 or f.calc_center_median().z < 0.1 or abs(f.calc_center_median().x) > 0.35]
    bmesh.ops.delete(bm, geom=dels, context='FACES_KEEP_BOUNDARY')
    bmesh.update_edit_mesh(clothes.data)
    bpy.ops.object.mode_set(mode='OBJECT')

    clothes.modifiers.new("Inflate", 'DISPLACE').strength = 0.012
    bpy.ops.object.convert(target='MESH')

    # Fix Normals on Clothes too
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode='OBJECT')

    # Poncho
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=45, y_subdivisions=45, size=1.5, location=(0, 0, 1.58))
    poncho = bpy.context.active_object
    poncho.name = "Poncho"

    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(poncho.data)
    ensure_lookup(bm)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.calc_center_median().length < 0.13], context='FACES')
    bmesh.update_edit_mesh(poncho.data)
    bpy.ops.object.mode_set(mode='OBJECT')

    poncho.modifiers.new("Solidify", 'SOLIDIFY').thickness = 0.003
    cl = poncho.modifiers.new("Cloth", 'CLOTH')
    cl.settings.quality = 12
    cl.settings.mass = 0.3
    cl.settings.tension_stiffness = 15
    cl.settings.bending_model = 'ANGULAR'
    cl.settings.bending_stiffness = 0.1
    cl.collision_settings.use_self_collision = True
    cl.collision_settings.distance_min = 0.02

    return clothes, poncho

def setup_rig_and_bake_ik(arm_obj, body, clothes):
    # 1. Parenting
    for o in [body, clothes]:
        o.select_set(True)
        arm_obj.select_set(True)
        bpy.context.view_layer.objects.active = arm_obj
        bpy.ops.object.parent_set(type='ARMATURE_AUTO')
        col = o.modifiers.new("Collision", 'COLLISION')
        try:
            col.settings.thickness_outer = 0.03 # Increased buffer
            col.settings.thickness_inner = 0.01
        except:
            try: col.thickness_outer = 0.03
            except: pass

    # 2. Setup IK Targets
    ik_targets = []
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='POSE')

    for side in ['l', 'r']:
        bone_name = f"{side}_talus"
        bone = arm_obj.pose.bones.get(bone_name)
        if bone:
            loc = arm_obj.matrix_world @ bone.head
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.empty_add(type='PLAIN_AXES', location=loc)
            target = bpy.context.active_object
            target.name = f"IK_Target_{side}"
            ik_targets.append(target)

            bpy.context.view_layer.objects.active = arm_obj
            bpy.ops.object.mode_set(mode='POSE')

            knee_name = f"{side}_knee"
            p_knee = arm_obj.pose.bones.get(knee_name)
            if p_knee:
                ik = p_knee.constraints.new('IK')
                ik.target = target
                ik.chain_count = 2

    # 3. Animation
    bpy.context.scene.frame_start = START_FRAME
    bpy.context.scene.frame_end = END_FRAME

    def kf_bones(frame):
        for b in arm_obj.pose.bones:
            b.keyframe_insert("rotation_quaternion", frame=frame)
            b.keyframe_insert("location", frame=frame)

    for b in arm_obj.pose.bones: b.rotation_mode = 'QUATERNION'
    kf_bones(1)
    kf_bones(ANIM_START_FRAME)

    root = arm_obj.pose.bones.get("humanoid_root")
    root.location = (0, -0.6, -0.45)
    root.keyframe_insert("location", frame=END_FRAME)

    for b_name in ["l5", "l1", "t12", "t6", "t1", "c7"]:
        pb = arm_obj.pose.bones.get(b_name)
        if pb:
            pb.rotation_quaternion = Quaternion((1, 0, 0), math.radians(12))
            pb.keyframe_insert("rotation_quaternion", frame=END_FRAME)

    si = arm_obj.pose.bones.get("sacroiliac")
    si.rotation_quaternion = Quaternion((1, 0, 0), math.radians(85))
    si.keyframe_insert("rotation_quaternion", frame=END_FRAME)

    # 4. Bake Action
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    arm_obj.select_set(True)
    bpy.context.view_layer.objects.active = arm_obj

    print("Baking IK to FK Keyframes...")
    bpy.ops.nla.bake(
        frame_start=START_FRAME,
        frame_end=END_FRAME,
        visual_keying=True,
        clear_constraints=True,
        bake_types={'POSE'}
    )

    bpy.ops.object.mode_set(mode='OBJECT')
    for t in ik_targets:
        bpy.data.objects.remove(t)

def bake_physics():
    print(f"Baking Physics... (Wait ~30s)")
    for obj in bpy.context.scene.objects:
        for mod in obj.modifiers:
            if mod.type == 'CLOTH':
                try:
                    with bpy.context.temp_override(active_object=obj, point_cache=mod.point_cache):
                        bpy.ops.ptcache.bake(bake=True)
                except Exception as e: print(f"Bake warning: {e}")

# --- X3D EXPORT ---
def export_hanim(filepath, arm, body, poncho):
    root = ET.Element("X3D", profile="Full", version="3.3")
    scene = ET.SubElement(root, "Scene")
    def vec_str(v): return f"{v.x:.4f} {v.z:.4f} {-v.y:.4f}"

    humanoid = ET.SubElement(scene, "HAnimHumanoid", DEF="Female_LOA4", version="2.0")
    skeleton = ET.SubElement(humanoid, "HAnimJoint", containerField="skeleton")
    root_bone = arm.data.bones["humanoid_root"]
    skeleton.set("DEF", root_bone.name)
    skeleton.set("center", vec_str(arm.matrix_world @ root_bone.head_local))

    def rec_bones(bone, parent_el):
        for child in bone.children:
            j = ET.SubElement(parent_el, "HAnimJoint", DEF=child.name, containerField="children")
            j.set("center", vec_str(arm.matrix_world @ child.head_local))
            rec_bones(child, j)
    rec_bones(root_bone, skeleton)
    def rec_use(bone):
        ET.SubElement(humanoid, "HAnimJoint", USE=bone.name, containerField="joints")
        for c in bone.children: rec_use(c)
    rec_use(root_bone)

    shape = ET.SubElement(humanoid, "Shape", containerField="skin")
    ET.SubElement(ET.SubElement(shape, "Appearance"), "Material", diffuseColor="0.8 0.6 0.5")
    ifs = ET.SubElement(shape, "IndexedFaceSet", DEF="SkinGeo", creaseAngle="3.14")
    dg = bpy.context.evaluated_depsgraph_get()
    bpy.context.scene.frame_set(1)
    body_eval = body.evaluated_get(dg)
    pts = [vec_str(body.matrix_world @ v.co) for v in body_eval.data.vertices]
    ET.SubElement(ifs, "Coordinate", point=" ".join(pts))
    inds = [" ".join([str(x) for x in p.vertices]) + " -1" for p in body_eval.data.polygons]
    ifs.set("coordIndex", " ".join(inds))

    tr = ET.SubElement(scene, "Transform")
    pshape = ET.SubElement(tr, "Shape")
    ET.SubElement(ET.SubElement(pshape, "Appearance"), "Material", diffuseColor="0.2 0.5 0.2")
    pifs = ET.SubElement(pshape, "IndexedFaceSet", DEF="PonchoGeo", creaseAngle="3.14")
    peval_static = poncho.evaluated_get(dg)
    pinds = [" ".join([str(x) for x in p.vertices]) + " -1" for p in peval_static.data.polygons]
    pifs.set("coordIndex", " ".join(pinds))
    pcoord = ET.SubElement(pifs, "Coordinate", DEF="PonchoCoords")

    keys, vals = [], []
    for f in range(START_FRAME, END_FRAME + 1):
        bpy.context.scene.frame_set(f)
        peval = poncho.evaluated_get(dg)
        fpts = [vec_str(poncho.matrix_world @ v.co) for v in peval.data.vertices]
        if f == START_FRAME: pcoord.set("point", " ".join(fpts))
        keys.append(f"{ (f-START_FRAME)/(END_FRAME-START_FRAME) :.3f}")
        vals.append(" ".join(fpts))

    ci = ET.SubElement(scene, "CoordinateInterpolator", DEF="PonchoAnim", key=" ".join(keys), keyValue=" ".join(vals))
    ET.SubElement(scene, "ROUTE", fromNode="PonchoAnim", fromField="value_changed", toNode="PonchoCoords", toField="point")
    ts = ET.SubElement(scene, "TimeSensor", DEF="Timer", cycleInterval="5.0", loop="true")
    ET.SubElement(scene, "ROUTE", fromNode="Timer", fromField="fraction_changed", toNode="PonchoAnim", toField="set_fraction")

    for bone in arm.pose.bones:
        oi_def = f"OI_{bone.name}"
        oi = ET.SubElement(scene, "OrientationInterpolator", DEF=oi_def, key=" ".join(keys))
        rots = []
        for f in range(START_FRAME, END_FRAME + 1):
            bpy.context.scene.frame_set(f)
            ax, ang = bone.rotation_quaternion.to_axis_angle()
            rots.append(f"{ax.x:.4f} {ax.y:.4f} {ax.z:.4f} {ang:.4f}")
        oi.set("keyValue", " ".join(rots))
        ET.SubElement(scene, "ROUTE", fromNode="Timer", fromField="fraction_changed", toNode=oi_def, toField="set_fraction")
        ET.SubElement(scene, "ROUTE", fromNode=oi_def, fromField="value_changed", toNode=bone.name, toField="rotation")

    tree = ET.ElementTree(root)
    tree.write(filepath, encoding="UTF-8", xml_declaration=True)
    print(f"Exported: {filepath}")

def main():
    print("Start.")
    clear_scene()
    arm = create_hanim_skeleton()
    body = create_body_mesh(arm)
    add_features(body, arm)
    clothes, poncho = create_clothes(body)
    setup_rig_and_bake_ik(arm, body, clothes)
    bake_physics()
    out = os.path.join(os.path.expanduser("~"), EXPORT_FILENAME)
    export_hanim(out, arm, body, poncho)
    print("Done.")

if __name__ == "__main__":
    main()
