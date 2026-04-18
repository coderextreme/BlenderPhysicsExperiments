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

# ==========================================
# 2. HANIM LOA4 SKELETON GENERATOR
# ==========================================
def generate_loa4_bones():
    """Generates standard HAnim LOA4 skeleton. Facing +X axis."""
    bones = []

    bones.append(("hanim_HumanoidRoot", None, (0, 0, 0.95), (0, 0, 1.0)))
    bones.append(("hanim_sacrum", "hanim_HumanoidRoot", (0, 0, 1.0), (0, 0, 1.05)))
    bones.append(("hanim_pelvis", "hanim_sacrum", (0, 0, 1.05), (0, 0, 1.1)))

    prev = "hanim_pelvis"
    z_curr = 1.1
    for i in range(5, 0, -1):
        name, z_next = f"hanim_vl{i}", z_curr + 0.03
        bones.append((name, prev, (0, 0, z_curr), (0, 0, z_next)))
        prev, z_curr = name, z_next
    for i in range(12, 0, -1):
        name, z_next = f"hanim_vt{i}", z_curr + 0.02
        bones.append((name, prev, (0, 0, z_curr), (0, 0, z_next)))
        prev, z_curr = name, z_next
    for i in range(7, 0, -1):
        name, z_next = f"hanim_vc{i}", z_curr + 0.015
        bones.append((name, prev, (0, 0, z_curr), (0, 0, z_next)))
        prev, z_curr = name, z_next

    bones.append(("hanim_skullbase", prev, (0, 0, z_curr), (0, 0, z_curr + 0.02)))
    bones.append(("hanim_skull", "hanim_skullbase", (0, 0, z_curr + 0.02), (0, 0, z_curr + 0.15)))

    def build_arm(side, y_dir, parent):
        sy = y_dir
        bones.append((f"hanim_{side}_clavicle", parent, (0, 0.02*sy, 1.45), (0, 0.15*sy, 1.45)))
        bones.append((f"hanim_{side}_scapula", f"hanim_{side}_clavicle", (0, 0.15*sy, 1.45), (0, 0.16*sy, 1.43)))
        bones.append((f"hanim_{side}_upperarm", f"hanim_{side}_scapula", (0, 0.16*sy, 1.43), (0, 0.22*sy, 1.15)))
        bones.append((f"hanim_{side}_forearm", f"hanim_{side}_upperarm", (0, 0.22*sy, 1.15), (0, 0.24*sy, 0.9)))
        bones.append((f"hanim_{side}_carpal", f"hanim_{side}_forearm", (0, 0.24*sy, 0.9), (0, 0.25*sy, 0.88)))

    def build_leg(side, y_dir, parent):
        sy = y_dir
        bones.append((f"hanim_{side}_hip", parent, (0, 0.08*sy, 1.05), (0, 0.12*sy, 1.0)))
        bones.append((f"hanim_{side}_thigh", f"hanim_{side}_hip", (0, 0.12*sy, 1.0), (0, 0.12*sy, 0.55)))
        bones.append((f"hanim_{side}_calf", f"hanim_{side}_thigh", (0, 0.12*sy, 0.55), (0, 0.12*sy, 0.15)))
        bones.append((f"hanim_{side}_talus", f"hanim_{side}_calf", (0, 0.12*sy, 0.15), (0.05, 0.12*sy, 0.08)))

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
        b.roll = 0 # Enforce 0 bone roll so local axes are fully predictable

    for name, parent, head, tail in bones_data:
        if parent:
            edit_bones[name].parent = edit_bones[parent]
            edit_bones[name].use_connect = False

    bpy.ops.object.mode_set(mode='OBJECT')
    return arm_obj

# ==========================================
# 3. GEOMETRY & SKINNING
# ==========================================
def build_skin(arm_obj):
    bm = bmesh.new()
    bpy.ops.object.mode_set(mode='EDIT')

    for bone in arm_obj.data.edit_bones:
        r = 0.035
        if "pelvis" in bone.name or "sacrum" in bone.name: r = 0.16
        elif "vl" in bone.name: r = 0.12
        elif "vt" in bone.name: r = 0.14
        elif "clavicle" in bone.name or "scapula" in bone.name: r = 0.08
        elif "thigh" in bone.name: r = 0.11
        elif "skull" in bone.name: r = 0.10

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

    remesh = skin_obj.modifiers.new(name="Remesh", type='REMESH')
    remesh.mode = 'VOXEL'
    remesh.voxel_size = 0.02
    bpy.context.view_layer.objects.active = skin_obj
    bpy.ops.object.modifier_apply(modifier="Remesh")

    smooth = skin_obj.modifiers.new(name="Smooth", type='SMOOTH')
    smooth.factor = 0.8
    smooth.iterations = 5
    bpy.ops.object.modifier_apply(modifier="Smooth")

    skin_obj.select_set(True)
    arm_obj.select_set(True)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.parent_set(type='ARMATURE_AUTO')

    return skin_obj

# ==========================================
# 4. ANIMATION (BENDING FORWARD)
# ==========================================
def animate_humanoid(arm_obj):
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='POSE')

    for pb in arm_obj.pose.bones:
        pb.rotation_mode = 'QUATERNION'
        pb.keyframe_insert(data_path="rotation_quaternion", frame=1)
        pb.keyframe_insert(data_path="rotation_quaternion", frame=60)
        pb.keyframe_insert(data_path="location", frame=1)
        pb.keyframe_insert(data_path="location", frame=60)

    bpy.context.scene.frame_set(120)
    root = arm_obj.pose.bones["hanim_HumanoidRoot"]
    root.location = (-0.25, 0, -0.3)
    root.keyframe_insert(data_path="location", frame=120)

    bend_angle = math.radians(10)
    for b in arm_obj.pose.bones:
        if any(spine in b.name for spine in ["vt", "vl", "sacrum"]):
            b.rotation_quaternion = mathutils.Euler((0, 0, bend_angle), 'XYZ').to_quaternion()
            b.keyframe_insert(data_path="rotation_quaternion", frame=120)

    pelvis = arm_obj.pose.bones["hanim_pelvis"]
    pelvis.rotation_quaternion = mathutils.Euler((0, 0, math.radians(45)), 'XYZ').to_quaternion()
    pelvis.keyframe_insert(data_path="rotation_quaternion", frame=120)

    for side in ['l', 'r']:
        thigh = arm_obj.pose.bones[f"hanim_{side}_thigh"]
        thigh.rotation_quaternion = mathutils.Euler((0, 0, math.radians(-50)), 'XYZ').to_quaternion()
        thigh.keyframe_insert(data_path="rotation_quaternion", frame=120)

    bpy.ops.object.mode_set(mode='OBJECT')

# ==========================================
# 5. X3D RIGID BODY EXPORTER
# ==========================================
def quat_to_axis_angle(q):
    angle = 2 * math.acos(max(min(q.w, 1.0), -1.0))
    s = math.sqrt(1 - q.w * q.w)
    if s < 0.001: return (0.0, 1.0, 0.0, 0.0)
    return (q.x / s, q.y / s, q.z / s, angle)

def export_x3d_physics(filepath, arm_obj, skin_obj):
    print(f"Exporting Physics X3D to {filepath}...")

    xml = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<!DOCTYPE X3D PUBLIC "ISO//Web3D//DTD X3D 4.0//EN" "http://www.web3d.org/specifications/x3d-4.0.dtd">',
           '<X3D profile="Full" version="4.0">',
           '<head><component name="HAnim" level="2"/><component name="RigidBodyPhysics" level="2"/></head>',
           '<Scene>',
           '<NavigationInfo type=\'"EXAMINE" "ANY"\'/>',
           '<DirectionalLight direction="0 -1 -1" intensity="0.8"/>',
           '<Viewpoint position="3 1.5 3" orientation="0 1 0 0.8" description="Perspective View"/>',

           # --- Coordinate System Converter: Maps Blender Z-Up to X3D Y-Up ---
           '<Transform DEF="Z_UP_TO_Y_UP" rotation="1 0 0 -1.5708">']

    # Kinematic Collision proxies
    kinematic_colliders = {
        "hanim_skull": (0.11, 0, 0, 0.05),
        "hanim_vt4": (0.15, 0, 0, -0.05),
        "hanim_vl3": (0.13, 0, 0, 0),
        "hanim_pelvis": (0.17, 0, 0, 0),
        "hanim_l_clavicle": (0.09, 0, 0.06, 0),
        "hanim_r_clavicle": (0.09, 0, -0.06, 0)
    }

    vg_dict = {vg.index: vg.name for vg in skin_obj.vertex_groups}
    joint_weights = {}
    for v in skin_obj.data.vertices:
        for g in v.groups:
            bname = vg_dict.get(g.group)
            if bname:
                if bname not in joint_weights: joint_weights[bname] = ([], [])
                joint_weights[bname][0].append(str(v.index))
                joint_weights[bname][1].append(f"{g.weight:.4f}")

    segments_created = []

    def build_joint_xml(bone, is_root=False):
        c_field = "skeleton" if is_root else "children"
        center = f"{bone.head.x:.5f} {bone.head.y:.5f} {bone.head.z:.5f}"

        idx_str = " ".join(joint_weights[bone.name][0]) if bone.name in joint_weights else ""
        w_str = " ".join(joint_weights[bone.name][1]) if bone.name in joint_weights else ""
        attr_str = f'DEF="{bone.name}" name="{bone.name.replace("hanim_", "")}" containerField="{c_field}" center="{center}"'
        if idx_str: attr_str += f' skinCoordIndex="{idx_str}" skinCoordWeight="{w_str}"'

        xml.append(f'<HAnimJoint {attr_str}>')

        # Inject HAnimSegment as the container for Geometry/Colliders
        if bone.name in kinematic_colliders:
            rad, ox, oy, oz = kinematic_colliders[bone.name]
            seg_def = f"{bone.name}_segment"
            seg_name = bone.name.replace("hanim_", "") + "_seg"
            segments_created.append(seg_def)

            xml.append(f'<HAnimSegment DEF="{seg_def}" name="{seg_name}" containerField="children">')
            xml.append(f'<Transform translation="{ox} {oy} {oz}">')
            xml.append(f'<CollidableShape DEF="CS_{bone.name}">')

            # Shape must have containerField="shape" inside CollidableShape
            xml.append(f'<Shape containerField="shape"><Sphere radius="{rad}"/></Shape>')

            xml.append('</CollidableShape></Transform>')
            xml.append('</HAnimSegment>')

        for child in bone.children: build_joint_xml(child)
        xml.append('</HAnimJoint>')

    xml.append('<HAnimHumanoid DEF="hanim_Female" name="Female" version="2.0">')
    build_joint_xml(arm_obj.data.bones["hanim_HumanoidRoot"], is_root=True)

    # Formally register all joints AND segments
    for bone in arm_obj.data.bones:
        xml.append(f'<HAnimJoint USE="{bone.name}" containerField="joints"/>')
    for seg_def in segments_created:
        xml.append(f'<HAnimSegment USE="{seg_def}" containerField="segments"/>')

    # skin is a containerField, not a Node
    xml.append('<Shape containerField="skin">')
    xml.append('<Appearance><Material diffuseColor="0.8 0.6 0.5" shininess="0.3"/></Appearance>')

    mesh = skin_obj.data
    faces = [" ".join(str(v) for v in p.vertices) + " -1" for p in mesh.polygons]
    verts = [f"{v.co.x:.4f} {v.co.y:.4f} {v.co.z:.4f}" for v in mesh.vertices]

    xml.append(f'<IndexedFaceSet DEF="SkinMesh" coordIndex="{" ".join(faces)}" solid="false">')
    xml.append(f'<Coordinate DEF="SkinCoord" point="{" ".join(verts)}"/>')
    xml.append('</IndexedFaceSet></Shape>')

    xml.append('</HAnimHumanoid>')

    # Export Skeletal Animation
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
        if all(v == "0.0000 1.0000 0.0000 0.0000" for v in vals): continue
        xml.append(f'<OrientationInterpolator DEF="{bname}_anim" key="{keys}" keyValue="{"  ".join(vals)}"/>')
        xml.append(f'<ROUTE fromNode="AnimClock" fromField="fraction_changed" toNode="{bname}_anim" toField="set_fraction"/>')
        xml.append(f'<ROUTE fromNode="{bname}_anim" fromField="value_changed" toNode="{bname}" toField="rotation"/>')

    # =========================================================
    # PROCEDURAL X3D RIGID BODY CLOTH GENERATOR
    # =========================================================
    GRID_SIZE = 12
    SPAN = 0.8
    SPACING = SPAN / (GRID_SIZE - 1)
    Z_HEIGHT = 1.55
    HOLE_RADIUS = 0.16

    nodes = {}
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            x = -SPAN/2 + r * SPACING
            y = -SPAN/2 + c * SPACING
            if math.sqrt(x*x + y*y) >= HOLE_RADIUS:
                nodes[(r, c)] = (x, y)

    # Visible representations of the Cloth Nodes
    for (r, c), (x, y) in nodes.items():
        node_def = f"ClothNode_{r}_{c}"
        rad = SPACING * 0.48
        xml.append(f'<Transform DEF="Vis_{node_def}" translation="{x:.4f} {y:.4f} {Z_HEIGHT}">')
        xml.append(f'<Shape><Appearance><Material diffuseColor="0.8 0.1 0.3" shininess="0.5"/></Appearance>')
        xml.append(f'<Sphere radius="{rad:.4f}"/></Shape></Transform>')

    # Physics Engine Implementation (gravity evaluates locally, so Z-down correctly maps to screen Y-down)
    xml.append('<RigidBodyCollection gravity="0 0 -9.81">')

    # Bind the Kinematic bodies to the CollidableShapes inside the HAnimSegments
    for bname in kinematic_colliders.keys():
        xml.append(f'<RigidBody DEF="RB_{bname}" mass="0" containerField="bodies">')
        xml.append(f'<CollidableShape USE="CS_{bname}" containerField="geometry"/>')
        xml.append('</RigidBody>')

    xml.append('<RigidBody DEF="RB_Floor" mass="0" position="0 0 -0.05" containerField="bodies">')
    xml.append('<CollidableShape containerField="geometry"><Shape containerField="shape"><Box size="10 10 0.1"/></Shape></CollidableShape>')
    xml.append('</RigidBody>')

    for (r, c), (x, y) in nodes.items():
        node_def = f"ClothNode_{r}_{c}"
        rad = SPACING * 0.48

        xml.append(f'<RigidBody DEF="{node_def}" containerField="bodies" position="{x:.4f} {y:.4f} {Z_HEIGHT}" mass="0.05" linearDampingFactor="0.6" angularDampingFactor="0.8">')
        xml.append(f'<CollidableShape containerField="geometry"><Shape containerField="shape"><Sphere radius="{rad:.4f}"/></Shape></CollidableShape></RigidBody>')

    for (r, c), (x, y) in nodes.items():
        if (r+1, c) in nodes:
            nx, ny = nodes[(r+1, c)]
            mx, my = (x+nx)/2, (y+ny)/2
            xml.append(f'<BallJoint containerField="joints" anchorPoint="{mx:.4f} {my:.4f} {Z_HEIGHT}">')
            xml.append(f'<RigidBody USE="ClothNode_{r}_{c}" containerField="body1"/>')
            xml.append(f'<RigidBody USE="ClothNode_{r+1}_{c}" containerField="body2"/>')
            xml.append('</BallJoint>')
        if (r, c+1) in nodes:
            nx, ny = nodes[(r, c+1)]
            mx, my = (x+nx)/2, (y+ny)/2
            xml.append(f'<BallJoint containerField="joints" anchorPoint="{mx:.4f} {my:.4f} {Z_HEIGHT}">')
            xml.append(f'<RigidBody USE="ClothNode_{r}_{c}" containerField="body1"/>')
            xml.append(f'<RigidBody USE="ClothNode_{r}_{c+1}" containerField="body2"/>')
            xml.append('</BallJoint>')

    xml.append('</RigidBodyCollection>')

    # Route physics simulation back to the visual scene graph
    for (r, c) in nodes.keys():
        node_def = f"ClothNode_{r}_{c}"
        xml.append(f'<ROUTE fromNode="{node_def}" fromField="position_changed" toNode="Vis_{node_def}" toField="set_translation"/>')
        xml.append(f'<ROUTE fromNode="{node_def}" fromField="orientation_changed" toNode="Vis_{node_def}" toField="set_rotation"/>')

    # Close the Z_UP_TO_Y_UP Converter Transform
    xml.append('</Transform>')

    xml.append('</Scene></X3D>')

    with open(filepath, 'w') as f:
        f.write("\n".join(xml))
    print("X3D Export Complete.")

# ==========================================
# MAIN EXECUTION
# ==========================================
def main():
    cleanup_scene()

    arm_obj = create_armature()
    skin_obj = build_skin(arm_obj)

    animate_humanoid(arm_obj)

    home_dir = os.path.expanduser("~")
    export_path = os.path.join(home_dir, "hanim_rigidbody_poncho3.x3d")
    export_x3d_physics(export_path, arm_obj, skin_obj)

    bpy.context.scene.frame_set(120)
    print(f"Success! Native X3D Physics scene saved to {export_path}")

if __name__ == "__main__":
    main()
