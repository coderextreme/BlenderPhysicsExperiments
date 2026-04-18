"""
=============================================================================
 Blender 4.x / 5.0 Python Script
 HAnim LOA4 Female Humanoid — Cloth Physics — Custom X3D Exporter
 Run:  blender --python hanim_female_complete.py
       or paste into Blender's Scripting editor and press Run Script
=============================================================================
"""

import bpy
import bmesh
import math
import os
import sys
import xml.etree.ElementTree as ET
from xml.dom import minidom
from mathutils import Vector, Matrix, Euler, Quaternion
from collections import OrderedDict

# ============================================================
# CONFIGURATION
# ============================================================
OUTPUT_PATH    = os.path.join(os.path.expanduser("~"), "hanim_female.x3d")
TOTAL_FRAMES   = 120
SETTLE_FRAMES  = 60
FPS            = 24

# ============================================================
# 1.  SCENE CLEANUP
# ============================================================
def clean_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for d in (bpy.data.meshes, bpy.data.armatures, bpy.data.materials,
              bpy.data.curves, bpy.data.cameras, bpy.data.lights):
        for item in list(d):
            d.remove(item)
    sc = bpy.context.scene
    sc.frame_start = 1
    sc.frame_end   = TOTAL_FRAMES
    sc.render.fps  = FPS

# ============================================================
# 2.  HAnim LOA4 JOINT HIERARCHY  (~148 joints)
# ============================================================
# Each entry: "joint_name": ("parent_name_or_None", (dx, dy, dz))
# Offsets are in metres from the parent joint's world position.
# Coordinate system: X = left, Y = forward/anterior, Z = up (Blender Z-up)
# Feminine proportions: pelvis wider (±0.11), shoulders narrower (±0.155),
# pronounced lumbar curve, narrow waist.

JOINTS_DEF = OrderedDict([
    # ── ROOT ──────────────────────────────────────────────────────────────
    ("HumanoidRoot",              (None,                        ( 0.000,  0.000,  0.000))),
    ("sacroiliac",                ("HumanoidRoot",              ( 0.000, -0.010,  0.927))),

    # ── LEFT LEG ──────────────────────────────────────────────────────────
    ("l_hip",                     ("sacroiliac",                (-0.110, -0.040, -0.070))),
    ("l_knee",                    ("l_hip",                     ( 0.000,  0.010, -0.430))),
    ("l_ankle",                   ("l_knee",                    ( 0.000,  0.015, -0.415))),
    ("l_subtalar",                ("l_ankle",                   (-0.013,  0.000, -0.030))),
    ("l_midtarsal",               ("l_subtalar",                ( 0.013,  0.025, -0.016))),
    ("l_metatarsal",              ("l_midtarsal",               ( 0.000,  0.060,  0.000))),
    ("l_toe",                     ("l_metatarsal",              ( 0.000,  0.040,  0.000))),
    # left toes (digits 1-5)
    ("l_tarsal_proximal_phalanx_1",("l_metatarsal",            (-0.050,  0.030,  0.000))),
    ("l_tarsal_distal_phalanx_1",  ("l_tarsal_proximal_phalanx_1",( 0.000, 0.025, 0.000))),
    ("l_tarsal_proximal_phalanx_2",("l_metatarsal",            (-0.030,  0.040,  0.000))),
    ("l_tarsal_middle_phalanx_2",  ("l_tarsal_proximal_phalanx_2",( 0.000, 0.025, 0.000))),
    ("l_tarsal_distal_phalanx_2",  ("l_tarsal_middle_phalanx_2",  ( 0.000, 0.015, 0.000))),
    ("l_tarsal_proximal_phalanx_3",("l_metatarsal",            (-0.010,  0.040,  0.000))),
    ("l_tarsal_middle_phalanx_3",  ("l_tarsal_proximal_phalanx_3",( 0.000, 0.025, 0.000))),
    ("l_tarsal_distal_phalanx_3",  ("l_tarsal_middle_phalanx_3",  ( 0.000, 0.015, 0.000))),
    ("l_tarsal_proximal_phalanx_4",("l_metatarsal",            ( 0.010,  0.040,  0.000))),
    ("l_tarsal_middle_phalanx_4",  ("l_tarsal_proximal_phalanx_4",( 0.000, 0.025, 0.000))),
    ("l_tarsal_distal_phalanx_4",  ("l_tarsal_middle_phalanx_4",  ( 0.000, 0.015, 0.000))),
    ("l_tarsal_proximal_phalanx_5",("l_metatarsal",            ( 0.030,  0.035,  0.000))),
    ("l_tarsal_middle_phalanx_5",  ("l_tarsal_proximal_phalanx_5",( 0.000, 0.022, 0.000))),
    ("l_tarsal_distal_phalanx_5",  ("l_tarsal_middle_phalanx_5",  ( 0.000, 0.013, 0.000))),

    # ── RIGHT LEG (mirrored X) ─────────────────────────────────────────────
    ("r_hip",                     ("sacroiliac",                ( 0.110, -0.040, -0.070))),
    ("r_knee",                    ("r_hip",                     ( 0.000,  0.010, -0.430))),
    ("r_ankle",                   ("r_knee",                    ( 0.000,  0.015, -0.415))),
    ("r_subtalar",                ("r_ankle",                   ( 0.013,  0.000, -0.030))),
    ("r_midtarsal",               ("r_subtalar",                (-0.013,  0.025, -0.016))),
    ("r_metatarsal",              ("r_midtarsal",               ( 0.000,  0.060,  0.000))),
    ("r_toe",                     ("r_metatarsal",              ( 0.000,  0.040,  0.000))),
    ("r_tarsal_proximal_phalanx_1",("r_metatarsal",            ( 0.050,  0.030,  0.000))),
    ("r_tarsal_distal_phalanx_1",  ("r_tarsal_proximal_phalanx_1",( 0.000, 0.025, 0.000))),
    ("r_tarsal_proximal_phalanx_2",("r_metatarsal",            ( 0.030,  0.040,  0.000))),
    ("r_tarsal_middle_phalanx_2",  ("r_tarsal_proximal_phalanx_2",( 0.000, 0.025, 0.000))),
    ("r_tarsal_distal_phalanx_2",  ("r_tarsal_middle_phalanx_2",  ( 0.000, 0.015, 0.000))),
    ("r_tarsal_proximal_phalanx_3",("r_metatarsal",            ( 0.010,  0.040,  0.000))),
    ("r_tarsal_middle_phalanx_3",  ("r_tarsal_proximal_phalanx_3",( 0.000, 0.025, 0.000))),
    ("r_tarsal_distal_phalanx_3",  ("r_tarsal_middle_phalanx_3",  ( 0.000, 0.015, 0.000))),
    ("r_tarsal_proximal_phalanx_4",("r_metatarsal",            (-0.010,  0.040,  0.000))),
    ("r_tarsal_middle_phalanx_4",  ("r_tarsal_proximal_phalanx_4",( 0.000, 0.025, 0.000))),
    ("r_tarsal_distal_phalanx_4",  ("r_tarsal_middle_phalanx_4",  ( 0.000, 0.015, 0.000))),
    ("r_tarsal_proximal_phalanx_5",("r_metatarsal",            (-0.030,  0.035,  0.000))),
    ("r_tarsal_middle_phalanx_5",  ("r_tarsal_proximal_phalanx_5",( 0.000, 0.022, 0.000))),
    ("r_tarsal_distal_phalanx_5",  ("r_tarsal_middle_phalanx_5",  ( 0.000, 0.013, 0.000))),

    # ── SPINE ─────────────────────────────────────────────────────────────
    ("vl5",                       ("sacroiliac",                ( 0.000, -0.015,  0.090))),
    ("vl4",                       ("vl5",                       ( 0.000, -0.010,  0.075))),
    ("vl3",                       ("vl4",                       ( 0.000, -0.008,  0.075))),
    ("vl2",                       ("vl3",                       ( 0.000, -0.005,  0.075))),
    ("vl1",                       ("vl2",                       ( 0.000, -0.003,  0.075))),
    ("vt12",                      ("vl1",                       ( 0.000,  0.000,  0.065))),
    ("vt11",                      ("vt12",                      ( 0.000,  0.003,  0.065))),
    ("vt10",                      ("vt11",                      ( 0.000,  0.005,  0.065))),
    ("vt9",                       ("vt10",                      ( 0.000,  0.005,  0.065))),
    ("vt8",                       ("vt9",                       ( 0.000,  0.005,  0.065))),
    ("vt7",                       ("vt8",                       ( 0.000,  0.005,  0.065))),
    ("vt6",                       ("vt7",                       ( 0.000,  0.005,  0.060))),
    ("vt5",                       ("vt6",                       ( 0.000,  0.005,  0.060))),
    ("vt4",                       ("vt5",                       ( 0.000,  0.005,  0.060))),
    ("vt3",                       ("vt4",                       ( 0.000,  0.005,  0.060))),
    ("vt2",                       ("vt3",                       ( 0.000,  0.005,  0.055))),
    ("vt1",                       ("vt2",                       ( 0.000,  0.005,  0.055))),
    ("vc7",                       ("vt1",                       ( 0.000,  0.005,  0.055))),
    ("vc6",                       ("vc7",                       ( 0.000,  0.004,  0.045))),
    ("vc5",                       ("vc6",                       ( 0.000,  0.003,  0.040))),
    ("vc4",                       ("vc5",                       ( 0.000,  0.002,  0.038))),
    ("vc3",                       ("vc4",                       ( 0.000,  0.001,  0.035))),
    ("vc2",                       ("vc3",                       ( 0.000,  0.001,  0.033))),
    ("vc1",                       ("vc2",                       ( 0.000,  0.001,  0.030))),
    ("skullbase",                 ("vc1",                       ( 0.000,  0.005,  0.050))),
    ("skull",                     ("skullbase",                 ( 0.000, -0.010,  0.080))),

    # ── FACE ──────────────────────────────────────────────────────────────
    ("l_eyeball_joint",           ("skull",                     (-0.033,  0.075,  0.022))),
    ("r_eyeball_joint",           ("skull",                     ( 0.033,  0.075,  0.022))),
    ("l_eyelid_joint",            ("skull",                     (-0.033,  0.077,  0.030))),
    ("r_eyelid_joint",            ("skull",                     ( 0.033,  0.077,  0.030))),
    ("l_temporomandibular",       ("skull",                     (-0.040,  0.018, -0.012))),
    ("r_temporomandibular",       ("skull",                     ( 0.040,  0.018, -0.012))),

    # ── LEFT ARM ──────────────────────────────────────────────────────────
    ("l_sternoclavicular",        ("vt1",                       (-0.080,  0.020,  0.040))),
    ("l_acromioclavicular",       ("l_sternoclavicular",        (-0.075,  0.000,  0.015))),
    ("l_shoulder",                ("l_acromioclavicular",       (-0.025, -0.012, -0.010))),
    ("l_elbow",                   ("l_shoulder",                ( 0.000,  0.000, -0.285))),
    ("l_radiocarpal",             ("l_elbow",                   ( 0.000,  0.000, -0.265))),
    # Left hand carpals
    ("l_midcarpal_1",             ("l_radiocarpal",             (-0.030,  0.018, -0.055))),
    ("l_carpometacarpal_1",       ("l_midcarpal_1",             (-0.010,  0.010, -0.028))),
    ("l_metacarpophalangeal_1",   ("l_carpometacarpal_1",       (-0.025,  0.022, -0.022))),
    ("l_carpal_interphalangeal_1",("l_metacarpophalangeal_1",   (-0.018,  0.018, -0.016))),
    ("l_midcarpal_2",             ("l_radiocarpal",             (-0.010,  0.012, -0.055))),
    ("l_carpometacarpal_2",       ("l_midcarpal_2",             (-0.005,  0.010, -0.028))),
    ("l_metacarpophalangeal_2",   ("l_carpometacarpal_2",       ( 0.000,  0.015, -0.032))),
    ("l_carpal_proximal_interphalangeal_2",("l_metacarpophalangeal_2",( 0.000, 0.000,-0.027))),
    ("l_carpal_distal_interphalangeal_2",  ("l_carpal_proximal_interphalangeal_2",(0.000,0.000,-0.020))),
    ("l_midcarpal_3",             ("l_radiocarpal",             ( 0.007,  0.012, -0.055))),
    ("l_carpometacarpal_3",       ("l_midcarpal_3",             ( 0.000,  0.010, -0.028))),
    ("l_metacarpophalangeal_3",   ("l_carpometacarpal_3",       ( 0.000,  0.015, -0.032))),
    ("l_carpal_proximal_interphalangeal_3",("l_metacarpophalangeal_3",( 0.000, 0.000,-0.027))),
    ("l_carpal_distal_interphalangeal_3",  ("l_carpal_proximal_interphalangeal_3",(0.000,0.000,-0.020))),
    ("l_midcarpal_4_5",           ("l_radiocarpal",             ( 0.020,  0.012, -0.055))),
    ("l_carpometacarpal_4",       ("l_midcarpal_4_5",           ( 0.000,  0.010, -0.028))),
    ("l_metacarpophalangeal_4",   ("l_carpometacarpal_4",       ( 0.000,  0.015, -0.030))),
    ("l_carpal_proximal_interphalangeal_4",("l_metacarpophalangeal_4",( 0.000, 0.000,-0.025))),
    ("l_carpal_distal_interphalangeal_4",  ("l_carpal_proximal_interphalangeal_4",(0.000,0.000,-0.018))),
    ("l_carpometacarpal_5",       ("l_midcarpal_4_5",           ( 0.018,  0.010, -0.028))),
    ("l_metacarpophalangeal_5",   ("l_carpometacarpal_5",       ( 0.000,  0.014, -0.028))),
    ("l_carpal_proximal_interphalangeal_5",("l_metacarpophalangeal_5",( 0.000, 0.000,-0.022))),
    ("l_carpal_distal_interphalangeal_5",  ("l_carpal_proximal_interphalangeal_5",(0.000,0.000,-0.015))),

    # ── RIGHT ARM (mirrored X) ─────────────────────────────────────────────
    ("r_sternoclavicular",        ("vt1",                       ( 0.080,  0.020,  0.040))),
    ("r_acromioclavicular",       ("r_sternoclavicular",        ( 0.075,  0.000,  0.015))),
    ("r_shoulder",                ("r_acromioclavicular",       ( 0.025, -0.012, -0.010))),
    ("r_elbow",                   ("r_shoulder",                ( 0.000,  0.000, -0.285))),
    ("r_radiocarpal",             ("r_elbow",                   ( 0.000,  0.000, -0.265))),
    ("r_midcarpal_1",             ("r_radiocarpal",             ( 0.030,  0.018, -0.055))),
    ("r_carpometacarpal_1",       ("r_midcarpal_1",             ( 0.010,  0.010, -0.028))),
    ("r_metacarpophalangeal_1",   ("r_carpometacarpal_1",       ( 0.025,  0.022, -0.022))),
    ("r_carpal_interphalangeal_1",("r_metacarpophalangeal_1",   ( 0.018,  0.018, -0.016))),
    ("r_midcarpal_2",             ("r_radiocarpal",             ( 0.010,  0.012, -0.055))),
    ("r_carpometacarpal_2",       ("r_midcarpal_2",             ( 0.005,  0.010, -0.028))),
    ("r_metacarpophalangeal_2",   ("r_carpometacarpal_2",       ( 0.000,  0.015, -0.032))),
    ("r_carpal_proximal_interphalangeal_2",("r_metacarpophalangeal_2",( 0.000, 0.000,-0.027))),
    ("r_carpal_distal_interphalangeal_2",  ("r_carpal_proximal_interphalangeal_2",(0.000,0.000,-0.020))),
    ("r_midcarpal_3",             ("r_radiocarpal",             (-0.007,  0.012, -0.055))),
    ("r_carpometacarpal_3",       ("r_midcarpal_3",             ( 0.000,  0.010, -0.028))),
    ("r_metacarpophalangeal_3",   ("r_carpometacarpal_3",       ( 0.000,  0.015, -0.032))),
    ("r_carpal_proximal_interphalangeal_3",("r_metacarpophalangeal_3",( 0.000, 0.000,-0.027))),
    ("r_carpal_distal_interphalangeal_3",  ("r_carpal_proximal_interphalangeal_3",(0.000,0.000,-0.020))),
    ("r_midcarpal_4_5",           ("r_radiocarpal",             (-0.020,  0.012, -0.055))),
    ("r_carpometacarpal_4",       ("r_midcarpal_4_5",           ( 0.000,  0.010, -0.028))),
    ("r_metacarpophalangeal_4",   ("r_carpometacarpal_4",       ( 0.000,  0.015, -0.030))),
    ("r_carpal_proximal_interphalangeal_4",("r_metacarpophalangeal_4",( 0.000, 0.000,-0.025))),
    ("r_carpal_distal_interphalangeal_4",  ("r_carpal_proximal_interphalangeal_4",(0.000,0.000,-0.018))),
    ("r_carpometacarpal_5",       ("r_midcarpal_4_5",           (-0.018,  0.010, -0.028))),
    ("r_metacarpophalangeal_5",   ("r_carpometacarpal_5",       ( 0.000,  0.014, -0.028))),
    ("r_carpal_proximal_interphalangeal_5",("r_metacarpophalangeal_5",( 0.000, 0.000,-0.022))),
    ("r_carpal_distal_interphalangeal_5",  ("r_carpal_proximal_interphalangeal_5",(0.000,0.000,-0.015))),
])

print(f"[HAnim] Joint count: {len(JOINTS_DEF)}")

# ============================================================
# 3.  BUILD ARMATURE FROM JOINT DEFINITIONS
# ============================================================
def build_armature():
    """Create Blender armature matching the HAnim LOA4 joint hierarchy."""
    bpy.ops.object.armature_add(enter_editmode=False, location=(0, 0, 0))
    arm_obj = bpy.context.active_object
    arm_obj.name = "HAnimArmature"
    arm_data = arm_obj.data
    arm_data.name = "HAnimSkeleton"

    # Compute world positions for each joint
    world_pos = {}
    def get_world(name):
        if name in world_pos:
            return world_pos[name]
        parent_name, offset = JOINTS_DEF[name]
        if parent_name is None:
            wp = Vector(offset)
        else:
            wp = get_world(parent_name) + Vector(offset)
        world_pos[name] = wp
        return wp

    for name in JOINTS_DEF:
        get_world(name)

    # Enter edit mode to create bones
    bpy.ops.object.mode_set(mode='EDIT')
    # Remove default bone
    for b in list(arm_data.edit_bones):
        arm_data.edit_bones.remove(b)

    created = {}
    for name, (parent_name, _) in JOINTS_DEF.items():
        bone = arm_data.edit_bones.new(name)
        head = world_pos[name]
        # tail: offset toward first child, or small offset upward
        children = [c for c, (p, _) in JOINTS_DEF.items() if p == name]
        if children:
            tail = world_pos[children[0]]
        else:
            tail = head + Vector((0, 0, 0.03))
        bone.head = head
        bone.tail = tail
        bone.use_connect = False
        created[name] = bone

    # Parent bones
    for name, (parent_name, _) in JOINTS_DEF.items():
        if parent_name and parent_name in created:
            created[name].parent = created[parent_name]

    bpy.ops.object.mode_set(mode='OBJECT')
    return arm_obj


# ============================================================
# 4.  BODY MESH (procedural female silhouette)
# ============================================================
def lerp(a, b, t):
    return a + (b - a) * t

def body_profile(z_norm):
    """
    Returns (radius, y_offset) for a cross-section at normalised height z_norm ∈ [0,1].
    Models a feminine hourglass shape.
    z_norm=0 → feet, z_norm=1 → top of skull
    """
    # Key profile points  (z_norm, radius, y_shift)
    profile = [
        (0.00, 0.04,   0.00),   # foot sole
        (0.03, 0.045,  0.00),   # ankle
        (0.15, 0.07,   0.00),   # mid calf
        (0.22, 0.09,  -0.01),   # knee
        (0.30, 0.085,  0.00),   # mid thigh
        (0.40, 0.12,   0.02),   # upper thigh / glute
        (0.44, 0.14,   0.025),  # hip (max width)
        (0.48, 0.105,  0.01),   # waist lower
        (0.52, 0.085, -0.01),   # waist (narrowest)
        (0.57, 0.10,  -0.015),  # ribcage lower
        (0.63, 0.115,  0.005),  # bust
        (0.66, 0.105,  0.01),   # upper chest
        (0.70, 0.09,   0.005),  # shoulders inner
        (0.73, 0.075,  0.00),   # neck
        (0.77, 0.068,  0.00),   # throat
        (0.80, 0.09,  -0.02),   # jaw / chin
        (0.85, 0.10,   0.00),   # mid skull
        (0.90, 0.10,   0.01),   # upper skull
        (1.00, 0.07,   0.00),   # crown
    ]
    for i in range(len(profile) - 1):
        z0, r0, y0 = profile[i]
        z1, r1, y1 = profile[i + 1]
        if z0 <= z_norm <= z1:
            t = (z_norm - z0) / (z1 - z0)
            return lerp(r0, r1, t), lerp(y0, y1, t)
    return 0.05, 0.0


def build_body_mesh(arm_obj):
    """Procedural female body mesh using bmesh revolution."""
    total_height = 1.75
    segments_v   = 64   # vertical slices
    segments_u   = 32   # radial subdivisions

    me  = bpy.data.meshes.new("SkinMesh")
    obj = bpy.data.objects.new("Skin", me)
    bpy.context.collection.objects.link(obj)

    bm = bmesh.new()
    vert_grid = []

    for vi in range(segments_v + 1):
        z_norm = vi / segments_v
        z = z_norm * total_height
        r, y_off = body_profile(z_norm)

        ring = []
        for ui in range(segments_u):
            angle = 2 * math.pi * ui / segments_u
            x = r * math.cos(angle)
            y = r * math.sin(angle) + y_off
            ring.append(bm.verts.new((x, y, z)))
        vert_grid.append(ring)

    bm.verts.ensure_lookup_table()

    # Create faces
    for vi in range(segments_v):
        for ui in range(segments_u):
            ui_next = (ui + 1) % segments_u
            v0 = vert_grid[vi][ui]
            v1 = vert_grid[vi][ui_next]
            v2 = vert_grid[vi + 1][ui_next]
            v3 = vert_grid[vi + 1][ui]
            bm.faces.new([v0, v1, v2, v3])

    # Cap bottom
    bot_verts = vert_grid[0]
    bot_center = bm.verts.new((0, 0, 0))
    for ui in range(segments_u):
        ui_next = (ui + 1) % segments_u
        bm.faces.new([bot_center, bot_verts[ui_next], bot_verts[ui]])

    # Cap top
    top_verts = vert_grid[-1]
    top_center = bm.verts.new((0, 0, total_height))
    for ui in range(segments_u):
        ui_next = (ui + 1) % segments_u
        bm.faces.new([top_center, top_verts[ui], top_verts[ui_next]])

    bm.to_mesh(me)
    bm.free()
    me.update()

    # Smooth shade
    for poly in me.polygons:
        poly.use_smooth = True

    # Skin material  (nodes are always enabled in Blender 5.0+)
    mat = bpy.data.materials.new("SkinMat")
    nodes = mat.node_tree.nodes
    bsdf = nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.80, 0.65, 0.55, 1.0)
        bsdf.inputs["Subsurface Weight"].default_value = 0.3
    obj.data.materials.append(mat)

    # Bind to armature
    mod = obj.modifiers.new("Armature", "ARMATURE")
    mod.object = arm_obj
    obj.parent = arm_obj

    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    arm_obj.select_set(True)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.parent_set(type='ARMATURE_AUTO')
    bpy.context.view_layer.objects.active = obj

    return obj


# ============================================================
# 5.  FACE FEATURES
# ============================================================
def make_material(name, color):
    # nodes are always enabled in Blender 5.0+; node_tree already exists
    mat = bpy.data.materials.new(name)
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    return mat

def parent_to_bone(obj, arm_obj, bone_name):
    """
    Parent *obj* to *bone_name* on *arm_obj* while preserving its current
    world-space position.  Works without requiring an active bone or any
    operator context — uses direct property assignment + matrix restore.
    """
    # Snapshot current world matrix before reparenting
    mw = obj.matrix_world.copy()
    obj.parent      = arm_obj
    obj.parent_type = "BONE"
    obj.parent_bone = bone_name
    # Force the dependency graph to recalculate parent transforms
    bpy.context.view_layer.update()
    # Restore world position so the object doesn't jump
    obj.matrix_world = mw


def build_face(arm_obj, world_pos):
    skull_pos = world_pos["skull"]

    # ── Eyes ──────────────────────────────────────────────────
    eye_mat   = make_material("EyeWhite",  (0.95, 0.95, 0.95))
    pupil_mat = make_material("Pupil",     (0.05, 0.03, 0.02))
    iris_mat  = make_material("Iris",      (0.25, 0.40, 0.65))

    face_objects = []
    for side, sx in (("L", -0.033), ("R", 0.033)):
        # Eyeball
        bpy.ops.mesh.primitive_uv_sphere_add(
            radius=0.013, location=skull_pos + Vector((sx, 0.075, 0.022)),
            segments=16, ring_count=10)
        eyeball = bpy.context.active_object
        eyeball.name = f"Eye_{side}"
        eyeball.data.materials.append(eye_mat)

        # Iris disc
        bpy.ops.mesh.primitive_cylinder_add(
            radius=0.009, depth=0.002,
            location=skull_pos + Vector((sx, 0.087, 0.022)))
        iris = bpy.context.active_object
        iris.name = f"Iris_{side}"
        iris.data.materials.append(iris_mat)
        iris.rotation_euler = (math.pi/2, 0, 0)

        # Pupil disc
        bpy.ops.mesh.primitive_cylinder_add(
            radius=0.004, depth=0.003,
            location=skull_pos + Vector((sx, 0.088, 0.022)))
        pupil = bpy.context.active_object
        pupil.name = f"Pupil_{side}"
        pupil.data.materials.append(pupil_mat)
        pupil.rotation_euler = (math.pi/2, 0, 0)

        face_objects += [eyeball, iris, pupil]

    # ── Nose ──────────────────────────────────────────────────
    bpy.ops.mesh.primitive_cone_add(
        vertices=8, radius1=0.012, radius2=0.004, depth=0.025,
        location=skull_pos + Vector((0, 0.085, -0.008)))
    nose = bpy.context.active_object
    nose.name = "Nose"
    nose.rotation_euler = (math.pi/2, 0, 0)
    nose.data.materials.append(make_material("NoseMat", (0.78, 0.62, 0.52)))
    face_objects.append(nose)

    # ── Lips ──────────────────────────────────────────────────
    lip_mat = make_material("LipMat", (0.72, 0.30, 0.25))
    for dz, name_sfx in ((0.006, "Upper"), (-0.006, "Lower")):
        bpy.ops.mesh.primitive_uv_sphere_add(
            radius=0.008, segments=12, ring_count=6,
            location=skull_pos + Vector((0, 0.083, -0.032 + dz)))
        lip = bpy.context.active_object
        lip.name = f"Lip_{name_sfx}"
        lip.scale = (2.2, 0.6, 0.5)
        lip.data.materials.append(lip_mat)
        face_objects.append(lip)

    # Parent all face objects to skull bone (no operator — direct assignment)
    for fo in face_objects:
        parent_to_bone(fo, arm_obj, "skull")
    bpy.ops.object.select_all(action='DESELECT')

    return face_objects


# ============================================================
# 6.  HAIR
# ============================================================
def build_hair(arm_obj, world_pos):
    skull_pos = world_pos["skull"]

    # ── Main hair volume ──────────────────────────────────────
    # Create a sculpted-like hair cap that wraps skull and flows down
    bm = bmesh.new()

    # Hair cap (hemisphere)
    bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=16, radius=0.105)

    # Scale slightly to fit skull + volume
    bm.verts.ensure_lookup_table()
    for v in bm.verts:
        if v.co.z < 0:
            # Pull lower hemisphere downward to form long hair
            v.co.z *= 4.5          # stretch downward
            v.co.x *= 1.05
            v.co.y *= 0.95
        else:
            v.co.z *= 1.0

    # Translate so it sits atop skull
    offset = skull_pos + Vector((0, -0.01, 0.04))
    for v in bm.verts:
        v.co += offset

    hair_me = bpy.data.meshes.new("HairMesh")
    bm.to_mesh(hair_me)
    bm.free()

    hair_obj = bpy.data.objects.new("Hair", hair_me)
    bpy.context.collection.objects.link(hair_obj)

    hair_mat = make_material("HairMat", (0.06, 0.04, 0.03))
    hair_obj.data.materials.append(hair_mat)

    # ── Side bangs (left & right flat planes shaped into bang strips) ──
    bang_objs = []
    for sx in (-1, 1):
        bm2 = bmesh.new()
        # A rectangular strip that curves around the face
        rows, cols = 12, 6
        verts = []
        for ri in range(rows):
            row_verts = []
            t = ri / (rows - 1)
            # Arc: sweeps from temple forward and down
            angle = math.radians(30 + t * 70) * sx   # side angle
            ry    = math.cos(t * math.pi * 0.5) * 0.08
            rz    = -t * 0.18 + 0.03
            for ci in range(cols):
                u = ci / (cols - 1)
                # width from crown to chin-level
                x = sx * (0.065 + u * 0.015 + t * 0.01)
                y = ry - u * 0.01
                z = rz - u * 0.005
                vp = skull_pos + Vector((x, y, z))
                row_verts.append(bm2.verts.new(vp))
            verts.append(row_verts)
        bm2.verts.ensure_lookup_table()
        for ri in range(rows - 1):
            for ci in range(cols - 1):
                bm2.faces.new([verts[ri][ci], verts[ri][ci+1],
                                verts[ri+1][ci+1], verts[ri+1][ci]])
        bang_me = bpy.data.meshes.new(f"SideBang_{'L' if sx<0 else 'R'}")
        bm2.to_mesh(bang_me)
        bm2.free()
        bo = bpy.data.objects.new(f"SideBang_{'L' if sx<0 else 'R'}", bang_me)
        bpy.context.collection.objects.link(bo)
        bo.data.materials.append(hair_mat)
        bang_objs.append(bo)

    # ── Front bangs ─────────────────────────────────────────
    bm3 = bmesh.new()
    rows, cols = 8, 14
    bang_verts = []
    for ri in range(rows):
        t = ri / (rows - 1)
        rv = []
        for ci in range(cols):
            u = (ci / (cols - 1)) - 0.5   # -0.5 to 0.5
            x = u * 0.085
            y = 0.095 - t * 0.02
            z = skull_pos.z + 0.04 - t * 0.07 + abs(u) * 0.015
            rv.append(bm3.verts.new((skull_pos.x + x, skull_pos.y + y, z)))
        bang_verts.append(rv)
    bm3.verts.ensure_lookup_table()
    for ri in range(rows - 1):
        for ci in range(cols - 1):
            bm3.faces.new([bang_verts[ri][ci], bang_verts[ri][ci+1],
                            bang_verts[ri+1][ci+1], bang_verts[ri+1][ci]])
    front_bang_me = bpy.data.meshes.new("FrontBang")
    bm3.to_mesh(front_bang_me)
    bm3.free()
    fbo = bpy.data.objects.new("FrontBang", front_bang_me)
    bpy.context.collection.objects.link(fbo)
    fbo.data.materials.append(hair_mat)

    all_hair = [hair_obj] + bang_objs + [fbo]
    for ho in all_hair:
        # Solidify for thickness
        ho.modifiers.new("Solidify", "SOLIDIFY").thickness = 0.008
        # Parent to skull bone, preserving world position
        parent_to_bone(ho, arm_obj, "skull")

    return all_hair


# ============================================================
# 7.  EARS
# ============================================================
def build_ears(arm_obj, world_pos):
    skull_pos = world_pos["skull"]
    ear_mat   = make_material("EarMat", (0.79, 0.63, 0.53))
    ear_objs  = []

    for side, sx in (("L", -1), ("R", 1)):
        bm = bmesh.new()
        # Ear = flattened torus / loop shape
        bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=0.022)
        bm.verts.ensure_lookup_table()
        # Flatten Y (ear is flat against head)
        for v in bm.verts:
            v.co.y *= 0.35
        # Position
        ear_pos = skull_pos + Vector((sx * 0.105, -0.015, 0.005))
        for v in bm.verts:
            v.co += ear_pos
        ear_me = bpy.data.meshes.new(f"Ear_{side}")
        bm.to_mesh(ear_me)
        bm.free()
        ear_obj = bpy.data.objects.new(f"Ear_{side}", ear_me)
        bpy.context.collection.objects.link(ear_obj)
        ear_obj.data.materials.append(ear_mat)
        parent_to_bone(ear_obj, arm_obj, "skull")
        ear_objs.append(ear_obj)

    return ear_objs


# ============================================================
# 8.  CLOTHING: Blouse, Leggings, High-heel Shoes
# ============================================================
def duplicate_skin_trimmed(skin_obj, name, z_min, z_max, inflate):
    """Duplicate the skin mesh, keep only verts in [z_min, z_max], inflate."""
    bpy.ops.object.select_all(action='DESELECT')
    skin_obj.select_set(True)
    bpy.context.view_layer.objects.active = skin_obj
    bpy.ops.object.duplicate()
    dup = bpy.context.active_object
    dup.name = name

    # Remove armature modifier from duplicate (we'll re-parent later)
    for mod in list(dup.modifiers):
        if mod.type == "ARMATURE":
            dup.modifiers.remove(mod)
        elif mod.type != "SUBSURF":
            pass

    # Go into edit mode, delete verts outside range
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(dup.data)
    bm.verts.ensure_lookup_table()
    del_verts = [v for v in bm.verts if v.co.z < z_min or v.co.z > z_max]
    bmesh.ops.delete(bm, geom=del_verts, context='VERTS')
    bmesh.update_edit_mesh(dup.data)
    bpy.ops.object.mode_set(mode='OBJECT')

    # Shrink-fatten (inflate outward)
    sf_mod = dup.modifiers.new("Inflate", "SHRINKWRAP")
    sf_mod.target = skin_obj
    sf_mod.offset = inflate
    sf_mod.wrap_mode = "OUTSIDE"

    # Re-attach armature
    arm_mod = dup.modifiers.new("Armature", "ARMATURE")
    arm_mod.object = bpy.data.objects.get("HAnimArmature")

    return dup


def build_clothing(skin_obj, arm_obj, world_pos):
    # ── Blouse  (torso, z 0.82–1.25 m) ────────────────────────────────
    blouse = duplicate_skin_trimmed(skin_obj, "Blouse", 0.82, 1.25, 0.008)
    blouse_mat = make_material("BlouseMat", (0.85, 0.75, 0.90))
    blouse.data.materials.clear()
    blouse.data.materials.append(blouse_mat)

    # ── Leggings (legs, z 0.02–0.92 m) ────────────────────────────────
    leggings = duplicate_skin_trimmed(skin_obj, "Leggings", 0.02, 0.92, 0.005)
    leg_mat = make_material("LeggingsMat", (0.15, 0.12, 0.18))
    leggings.data.materials.clear()
    leggings.data.materials.append(leg_mat)

    # ── High-heel shoes (per foot) ──────────────────────────────────────
    shoe_mat  = make_material("ShoeMat",  (0.08, 0.06, 0.06))
    heel_mat  = make_material("HeelMat",  (0.06, 0.05, 0.05))
    shoe_objs = []
    for side, sx, jname in (("L", -1, "l_ankle"), ("R", 1, "r_ankle")):
        ankle_pos = world_pos[jname]
        # Toe box
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        bm.verts.ensure_lookup_table()
        for v in bm.verts:
            v.co.x *= 0.055
            v.co.y *= 0.120
            v.co.z *= 0.045
        shoe_pos = ankle_pos + Vector((sx * 0.0, 0.03, -0.06))
        for v in bm.verts:
            v.co += shoe_pos
        shoe_me = bpy.data.meshes.new(f"Shoe_{side}")
        bm.to_mesh(shoe_me)
        bm.free()
        shoe_obj = bpy.data.objects.new(f"Shoe_{side}", shoe_me)
        bpy.context.collection.objects.link(shoe_obj)
        shoe_obj.data.materials.append(shoe_mat)
        parent_to_bone(shoe_obj, arm_obj, f"{'l' if sx<0 else 'r'}_ankle")
        shoe_objs.append(shoe_obj)

        # Heel spike
        bm2 = bmesh.new()
        bmesh.ops.create_cone(bm2, segments=8, radius1=0.012, radius2=0.004, depth=0.08)
        bm2.verts.ensure_lookup_table()
        heel_pos = ankle_pos + Vector((sx * 0.0, -0.055, -0.075))
        for v in bm2.verts:
            v.co += heel_pos
        heel_me = bpy.data.meshes.new(f"Heel_{side}")
        bm2.to_mesh(heel_me)
        bm2.free()
        heel_obj = bpy.data.objects.new(f"Heel_{side}", heel_me)
        bpy.context.collection.objects.link(heel_obj)
        heel_obj.data.materials.append(heel_mat)
        parent_to_bone(heel_obj, arm_obj, f"{'l' if sx<0 else 'r'}_ankle")
        shoe_objs.append(heel_obj)

    return blouse, leggings, shoe_objs


# ============================================================
# 9.  PONCHO (cloth simulation)
# ============================================================
def build_poncho(world_pos):
    skull_z = world_pos["skull"].z

    # High-res plane
    bpy.ops.mesh.primitive_plane_add(size=1.5, location=(0, 0, skull_z + 0.60))
    poncho = bpy.context.active_object
    poncho.name = "Poncho"

    # Subdivide for cloth resolution
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.subdivide(number_cuts=25)
    bpy.ops.object.mode_set(mode='OBJECT')

    # Circular neck hole (delete central verts)
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(poncho.data)
    bm.verts.ensure_lookup_table()
    neck_r = 0.085
    neck_verts = [v for v in bm.verts if math.sqrt(v.co.x**2 + v.co.y**2) < neck_r]
    bmesh.ops.delete(bm, geom=neck_verts, context='VERTS')
    bmesh.update_edit_mesh(poncho.data)
    bpy.ops.object.mode_set(mode='OBJECT')

    # Solidify modifier
    sol = poncho.modifiers.new("Solidify", "SOLIDIFY")
    sol.thickness = 0.005

    # Cloth modifier
    cloth = poncho.modifiers.new("Cloth", "CLOTH")
    cs = cloth.settings
    # Silk/Velvet feel
    cs.quality         = 15
    cs.mass            = 0.3
    cs.tension_stiffness  = 5.0
    cs.compression_stiffness = 5.0
    cs.shear_stiffness    = 3.0
    cs.bending_stiffness  = 0.5
    cs.bending_damping    = 0.5
    cs.air_damping        = 2.0
    cs.use_dynamic_mesh   = False
    # Collision settings
    coll = cloth.collision_settings
    coll.use_collision    = True
    coll.distance_min     = 0.010
    coll.use_self_collision = True
    coll.self_distance_min  = 0.007

    poncho_mat = make_material("PonchoMat", (0.55, 0.25, 0.15))
    poncho.data.materials.append(poncho_mat)

    return poncho


# ============================================================
# 10.  COLLISION ON SKIN / BLOUSE / LEGGINGS
# ============================================================
def add_collision(obj, thickness=0.045):
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.modifier_add(type='COLLISION')
    obj.collision.thickness_outer = thickness
    obj.collision.thickness_inner = 0.005
    obj.collision.damping         = 0.5
    obj.collision.friction_factor = 0.3


# ============================================================
# 11.  ANIMATION (T-pose settle → bend-to-toes)
# ============================================================
def set_bone_rotation(arm_obj, bone_name, frame, euler_xyz, mode='XYZ'):
    """Insert rotation keyframe on a pose bone."""
    if bone_name not in arm_obj.pose.bones:
        return
    pb = arm_obj.pose.bones[bone_name]
    pb.rotation_mode = mode
    pb.rotation_euler = Euler(euler_xyz, mode)
    pb.keyframe_insert("rotation_euler", frame=frame)


def animate_humanoid(arm_obj):
    scene = bpy.context.scene
    scene.frame_set(1)

    # ── Frames 1-60: T-pose (default) ────────────────────────────────────
    bpy.ops.object.select_all(action='DESELECT')
    arm_obj.select_set(True)
    bpy.context.view_layer.objects.active = arm_obj

    # Insert T-pose keys on main bones at frame 1
    bpy.ops.object.mode_set(mode='POSE')
    t_pose_bones = [
        "HumanoidRoot","sacroiliac","vl5","vl4","vl3","vl2","vl1",
        "vt12","vt11","vt10","vt9","vt8","vt7","vt6","vt5","vt4","vt3","vt2","vt1",
        "vc7","vc6","vc5","vc4","vc3","vc2","vc1","skullbase","skull",
        "l_hip","l_knee","l_ankle","r_hip","r_knee","r_ankle",
        "l_shoulder","l_elbow","r_shoulder","r_elbow",
    ]
    for bname in t_pose_bones:
        if bname in arm_obj.pose.bones:
            pb = arm_obj.pose.bones[bname]
            pb.rotation_mode = 'XYZ'
            pb.rotation_euler = Euler((0, 0, 0), 'XYZ')
            pb.keyframe_insert("rotation_euler", frame=1)
            pb.keyframe_insert("rotation_euler", frame=60)

    # Also keep root in place
    if "HumanoidRoot" in arm_obj.pose.bones:
        pb = arm_obj.pose.bones["HumanoidRoot"]
        pb.rotation_mode = 'XYZ'
        pb.rotation_euler = Euler((0, 0, 0))
        pb.location = Vector((0, 0, 0))
        pb.keyframe_insert("location",       frame=1)
        pb.keyframe_insert("rotation_euler", frame=1)
        pb.keyframe_insert("location",       frame=60)
        pb.keyframe_insert("rotation_euler", frame=60)

    # ── Frames 61-120: Bend to toes ──────────────────────────────────────
    # Strategy:
    #   - Curl lumbar/thoracic spine (progressive forward flexion)
    #   - Tilt pelvis (sacroiliac forward)
    #   - Counter-rotate hips/thighs to keep legs vertical
    #   - Shift HumanoidRoot slightly backward for CoM balance
    #   - Ankles compensate (slight plantarflexion) to keep shoes on ground

    BEND_FRAME = 120
    deg = math.radians

    # Lumbar spine – distribute ~80° forward flex across 5 segments
    lumbar_segs = ["vl5","vl4","vl3","vl2","vl1"]
    lumbar_each = deg(16)  # 5 × 16° = 80° total
    for bn in lumbar_segs:
        set_bone_rotation(arm_obj, bn, BEND_FRAME, (lumbar_each, 0, 0))

    # Thoracic spine – additional ~40° spread across 12 segments
    thoracic_segs = ["vt12","vt11","vt10","vt9","vt8","vt7","vt6","vt5","vt4","vt3","vt2","vt1"]
    thoracic_each = deg(3.5)
    for bn in thoracic_segs:
        set_bone_rotation(arm_obj, bn, BEND_FRAME, (thoracic_each, 0, 0))

    # Cervical – keep head upward (slight extension to look ahead)
    cervical_segs = ["vc7","vc6","vc5","vc4","vc3","vc2","vc1"]
    for bn in cervical_segs:
        set_bone_rotation(arm_obj, bn, BEND_FRAME, (deg(-5), 0, 0))

    # Sacroiliac / pelvis tilt
    set_bone_rotation(arm_obj, "sacroiliac", BEND_FRAME, (deg(25), 0, 0))

    # Hip counter-rotate to keep thighs/legs vertical
    set_bone_rotation(arm_obj, "l_hip", BEND_FRAME, (deg(-25), 0, 0))
    set_bone_rotation(arm_obj, "r_hip", BEND_FRAME, (deg(-25), 0, 0))

    # Knee stays straight (toe-touch) – no rotation
    set_bone_rotation(arm_obj, "l_knee", BEND_FRAME, (0, 0, 0))
    set_bone_rotation(arm_obj, "r_knee", BEND_FRAME, (0, 0, 0))

    # Ankle – slight plantarflexion to keep shoes flat
    set_bone_rotation(arm_obj, "l_ankle", BEND_FRAME, (deg(5), 0, 0))
    set_bone_rotation(arm_obj, "r_ankle", BEND_FRAME, (deg(5), 0, 0))

    # Arms hang down (gravity during bend)
    set_bone_rotation(arm_obj, "l_shoulder", BEND_FRAME, (deg(5), 0, deg(-5)))
    set_bone_rotation(arm_obj, "r_shoulder", BEND_FRAME, (deg(5), 0, deg(5)))

    # Root shifts backward to balance CoM
    if "HumanoidRoot" in arm_obj.pose.bones:
        pb = arm_obj.pose.bones["HumanoidRoot"]
        pb.location = Vector((0, -0.05, 0))
        pb.keyframe_insert("location", frame=BEND_FRAME)
        pb.rotation_euler = Euler((0, 0, 0))
        pb.keyframe_insert("rotation_euler", frame=BEND_FRAME)

    bpy.ops.object.mode_set(mode='OBJECT')


# ============================================================
# 12.  BAKE CLOTH PHYSICS
# ============================================================
def bake_cloth(poncho):
    bpy.context.view_layer.objects.active = poncho
    poncho.select_set(True)
    # Point cache
    for mod in poncho.modifiers:
        if mod.type == "CLOTH":
            mod.point_cache.frame_start = 1
            mod.point_cache.frame_end   = TOTAL_FRAMES
            break
    bpy.ops.ptcache.bake_all(bake=True)

# ============================================================
# 13.  CUSTOM X3D / HAnim EXPORTER
# ============================================================

def quat_to_axis_angle(q):
    """Convert mathutils.Quaternion to (ax, ay, az, angle) for X3D."""
    q = q.normalized()
    angle = 2 * math.acos(max(-1.0, min(1.0, q.w)))
    s = math.sin(angle / 2)
    if s < 1e-6:
        return (1.0, 0.0, 0.0, 0.0)
    return (q.x / s, q.y / s, q.z / s, angle)


def collect_bone_animation(arm_obj):
    """
    Walk every frame, collect pose-bone quaternions.
    Returns: { bone_name: [(frame, ax, ay, az, angle), ...] }
    """
    scene   = bpy.context.scene
    bpy.context.view_layer.objects.active = arm_obj
    data    = {name: [] for name in JOINTS_DEF}

    for f in range(scene.frame_start, scene.frame_end + 1):
        scene.frame_set(f)
        for name in JOINTS_DEF:
            if name not in arm_obj.pose.bones:
                data[name].append((f, 1, 0, 0, 0))
                continue
            pb = arm_obj.pose.bones[name]
            q  = pb.rotation_quaternion if pb.rotation_mode == 'QUATERNION' \
                 else pb.rotation_euler.to_quaternion()
            ax, ay, az, ang = quat_to_axis_angle(q)
            data[name].append((f, ax, ay, az, ang))

    return data


def collect_poncho_animation(poncho_obj):
    """
    Capture per-vertex positions of poncho for each frame.
    Returns: {frame: [Vector, ...]}
    """
    scene   = bpy.context.scene
    result  = {}
    for f in range(scene.frame_start, scene.frame_end + 1):
        scene.frame_set(f)
        depsgraph = bpy.context.evaluated_depsgraph_get()
        eval_obj  = poncho_obj.evaluated_get(depsgraph)
        mesh      = eval_obj.to_mesh()
        positions = [poncho_obj.matrix_world @ v.co for v in mesh.vertices]
        result[f] = positions
        eval_obj.to_mesh_clear()
    return result


def collect_skin_data(skin_obj):
    """
    Extract vertices, faces, and vertex-group weights for skinCoord export.
    Returns: (verts_list, faces_list, weights_dict)
      weights_dict = {group_name: [(vert_idx, weight), ...]}
    """
    depsgraph = bpy.context.evaluated_depsgraph_get()
    eval_obj  = skin_obj.evaluated_get(depsgraph)
    mesh      = eval_obj.to_mesh()

    verts = [skin_obj.matrix_world @ v.co for v in mesh.vertices]
    faces = [list(p.vertices) for p in mesh.polygons]

    group_names = {g.index: g.name for g in skin_obj.vertex_groups}
    weights = {name: [] for name in group_names.values()}
    for v in mesh.vertices:
        for ge in v.groups:
            gname = group_names.get(ge.group)
            if gname and ge.weight > 0.001:
                weights[gname].append((v.index, ge.weight))

    eval_obj.to_mesh_clear()
    return verts, faces, weights


def vec3_str(v, precision=6):
    return f"{v[0]:.{precision}f} {v[1]:.{precision}f} {v[2]:.{precision}f}"


def build_x3d_tree(arm_obj, skin_obj, poncho_obj, world_pos, bone_anim, poncho_anim):
    """
    Build the full X3D XML tree and return the root Element.
    Strict HAnim 2.0 compliance.
    """
    scene = bpy.context.scene
    fps   = scene.render.fps
    frame_start = scene.frame_start
    frame_end   = scene.frame_end

    root = ET.Element("X3D", {
        "profile":   "Full",
        "version":   "4.0",
        "xmlns:xsd": "http://www.w3.org/2001/XMLSchema-instance",
        "xsd:noNamespaceSchemaLocation": "https://www.web3d.org/specifications/x3d-4.0.xsd"
    })

    ET.SubElement(root, "head").append(
        ET.Comment("Generated by Blender HAnim Exporter")
    )

    scene_el = ET.SubElement(root, "Scene")

    # ── Background ────────────────────────────────────────────────────────
    ET.SubElement(scene_el, "Background", {"skyColor": "0.2 0.3 0.4"})

    # ── Viewpoint ─────────────────────────────────────────────────────────
    ET.SubElement(scene_el, "Viewpoint", {
        "description":   "Full body view",
        "position":      "0 3.5 3.0",
        "orientation":   "1 0 0 -0.4",
        "fieldOfView":   "0.7"
    })

    # ── NavigationInfo ────────────────────────────────────────────────────
    ET.SubElement(scene_el, "NavigationInfo", {"type": '"EXAMINE" "ANY"'})

    # ── HAnimHumanoid ─────────────────────────────────────────────────────
    humanoid = ET.SubElement(scene_el, "HAnimHumanoid", {
        "DEF":        "Humanoid",
        "name":       "HAnimFemale",
        "version":    "2.0",
        "info":       '"authorName=BlenderExporter" "authorEmail=none"',
        "translation": "0 0 0",
        "rotation":    "0 0 1 0",
        "scale":       "1 1 1",
    })

    # ── Build joint DEF elements (skeleton field) ─────────────────────────
    joint_elements = {}  # name → ET.Element

    def make_joint_el(name, container_field):
        _, offset = JOINTS_DEF[name]
        wp = world_pos[name]
        el = ET.Element("HAnimJoint", {
            "DEF":            f"hanim_{name}",
            "name":           name,
            "containerField": container_field,
            "translation":    vec3_str(wp),
            "rotation":       "0 0 1 0",
            "scale":          "1 1 1",
            "center":         vec3_str(wp),
            "scaleOrientation":"0 0 1 0",
        })
        return el

    def build_skeleton_recursive(name, parent_el, container_field):
        el = make_joint_el(name, container_field)
        joint_elements[name] = el
        parent_el.append(el)
        # Add children
        children = [c for c, (p, _) in JOINTS_DEF.items() if p == name]
        for child_name in children:
            build_skeleton_recursive(child_name, el, "children")
        return el

    # Skeleton group
    skeleton_group = ET.SubElement(humanoid, "Group", {"containerField": "skeleton"})
    build_skeleton_recursive("HumanoidRoot", skeleton_group, "skeleton")

    # ── USE copies (joints field) ─────────────────────────────────────────
    for name in JOINTS_DEF:
        ET.SubElement(humanoid, "HAnimJoint", {
            "USE":            f"hanim_{name}",
            "containerField": "joints",
        })

    # ── Skin geometry (viewpoint field) ──────────────────────────────────
    skin_verts, skin_faces, skin_weights = collect_skin_data(skin_obj)

    coord_str  = " ".join(vec3_str(v) for v in skin_verts)
    idx_str    = " ".join(
        " ".join(str(vi) for vi in face) + " -1" for face in skin_faces
    )

    # Build skinCoordIndex and skinCoordWeight arrays
    # Format: parallel arrays indexed by bone name
    coord_index_lines = []
    coord_weight_lines = []
    for jname in JOINTS_DEF:
        if jname in skin_weights and skin_weights[jname]:
            pairs = skin_weights[jname]
            idxs  = " ".join(str(p[0]) for p in pairs)
            wgts  = " ".join(f"{p[1]:.4f}" for p in pairs)
            coord_index_lines.append(f"{jname}: {idxs}")
            coord_weight_lines.append(f"{jname}: {wgts}")

    shape_el = ET.SubElement(humanoid, "Shape", {"containerField": "skin"})
    app_el   = ET.SubElement(shape_el, "Appearance")
    mat_el   = ET.SubElement(app_el, "Material", {
        "diffuseColor":    "0.80 0.65 0.55",
        "specularColor":   "0.3 0.2 0.1",
        "shininess":       "0.3",
    })
    geo_el = ET.SubElement(shape_el, "IndexedFaceSet", {
        "coordIndex":   idx_str,
        "solid":        "true",
        "creaseAngle":  "1.57",
    })
    ET.SubElement(geo_el, "Coordinate", {
        "DEF":   "SkinCoord",
        "point": coord_str,
    })

    # skinCoord / skinCoordIndex / skinCoordWeight on HAnimHumanoid
    humanoid.set("skinCoord", "SkinCoord")

    # Flatten skinCoordIndex: list of joint-index per vertex (simplified)
    # Build vertex→dominant joint mapping
    vert_joint = {}
    for jname, pairs in skin_weights.items():
        if jname not in JOINTS_DEF:
            continue
        jidx = list(JOINTS_DEF.keys()).index(jname)
        for vi, w in pairs:
            if vi not in vert_joint or w > vert_joint[vi][1]:
                vert_joint[vi] = (jidx, w)
    skinCoordIndex = [str(vert_joint.get(i, (0, 0))[0])
                      for i in range(len(skin_verts))]
    humanoid.set("skinCoordIndex", " ".join(skinCoordIndex))

    # ── OrientationInterpolators for each bone ────────────────────────────
    frame_count = frame_end - frame_start + 1
    keys_str    = " ".join(f"{(f - frame_start) / max(frame_count - 1, 1):.4f}"
                           for f in range(frame_start, frame_end + 1))

    interp_group = ET.SubElement(scene_el, "Group", {"DEF": "BoneAnimGroup"})

    timer = ET.SubElement(interp_group, "TimeSensor", {
        "DEF":      "AnimTimer",
        "cycleInterval": f"{frame_count / fps:.4f}",
        "loop":     "true",
    })

    for name, frames in bone_anim.items():
        values_str = " ".join(
            f"{ax:.4f} {ay:.4f} {az:.4f} {ang:.4f}"
            for (_, ax, ay, az, ang) in frames
        )
        interp_el = ET.SubElement(interp_group, "OrientationInterpolator", {
            "DEF":       f"OI_{name}",
            "key":       keys_str,
            "keyValue":  values_str,
        })
        # Route timer → interpolator
        ET.SubElement(interp_group, "ROUTE", {
            "fromNode":  "AnimTimer",
            "fromField": "fraction_changed",
            "toNode":    f"OI_{name}",
            "toField":   "set_fraction",
        })
        # Route interpolator → joint
        ET.SubElement(interp_group, "ROUTE", {
            "fromNode":  f"OI_{name}",
            "fromField": "value_changed",
            "toNode":    f"hanim_{name}",
            "toField":   "rotation",
        })

    # ── Poncho vertex animation (CoordinateInterpolator) ─────────────────
    poncho_frames = sorted(poncho_anim.keys())
    p_frame_count = len(poncho_frames)
    if p_frame_count > 0:
        p_keys   = " ".join(f"{(f - frame_start) / max(frame_count - 1, 1):.4f}"
                            for f in poncho_frames)
        # Build keyValue: all vertices for each frame concatenated
        kv_parts = []
        for f in poncho_frames:
            for v in poncho_anim[f]:
                kv_parts.append(f"{v.x:.5f} {v.y:.5f} {v.z:.5f}")
        p_kv_str = " ".join(kv_parts)

        poncho_group = ET.SubElement(scene_el, "Group", {"DEF": "PonchoAnim"})

        # Poncho shape
        num_p_verts = len(poncho_anim[poncho_frames[0]]) if poncho_frames else 0
        p_coord_str = " ".join(
            f"{v.x:.5f} {v.y:.5f} {v.z:.5f}"
            for v in poncho_anim[poncho_frames[0]]
        )

        # Poncho faces: regenerate from mesh at rest
        bpy.context.scene.frame_set(1)
        depsgraph   = bpy.context.evaluated_depsgraph_get()
        eval_poncho = poncho_obj.evaluated_get(depsgraph)
        pmesh       = eval_poncho.to_mesh()
        p_idx_str   = " ".join(
            " ".join(str(vi) for vi in p.vertices) + " -1"
            for p in pmesh.polygons
        )
        eval_poncho.to_mesh_clear()

        p_shape = ET.SubElement(poncho_group, "Shape")
        p_app   = ET.SubElement(p_shape, "Appearance")
        ET.SubElement(p_app, "Material", {
            "diffuseColor":    "0.55 0.25 0.15",
            "transparency":    "0.0",
        })
        p_ifs = ET.SubElement(p_shape, "IndexedFaceSet", {
            "coordIndex":  p_idx_str,
            "solid":       "false",
            "creaseAngle": "0.8",
        })
        ET.SubElement(p_ifs, "Coordinate", {
            "DEF":   "PonchoCoord",
            "point": p_coord_str,
        })

        # CoordinateInterpolator
        ci = ET.SubElement(poncho_group, "CoordinateInterpolator", {
            "DEF":      "PonchoCI",
            "key":      p_keys,
            "keyValue": p_kv_str,
        })

        # Shared timer
        ET.SubElement(poncho_group, "ROUTE", {
            "fromNode":  "AnimTimer",
            "fromField": "fraction_changed",
            "toNode":    "PonchoCI",
            "toField":   "set_fraction",
        })
        ET.SubElement(poncho_group, "ROUTE", {
            "fromNode":  "PonchoCI",
            "fromField": "value_changed",
            "toNode":    "PonchoCoord",
            "toField":   "point",
        })

    return root


def write_x3d(tree, filepath):
    """Pretty-print the XML tree to a file with correct X3D doctype."""
    rough = ET.tostring(tree, encoding="unicode", xml_declaration=False)
    parsed = minidom.parseString(rough)
    pretty = parsed.toprettyxml(indent="  ", encoding=None)
    # Replace minidom's XML declaration with proper X3D header
    lines = pretty.splitlines()
    # Remove minidom's ?xml line
    lines = [l for l in lines if not l.startswith("<?xml")]
    header = ('<?xml version="1.0" encoding="UTF-8"?>\n'
              '<!DOCTYPE X3D PUBLIC "ISO//Web3D//DTD X3D 4.0//EN"\n'
              '  "https://www.web3d.org/specifications/x3d-4.0.dtd">')
    output = header + "\n" + "\n".join(lines)
    with open(filepath, "w", encoding="utf-8") as fh:
        fh.write(output)
    print(f"[X3D] Saved: {filepath}")


# ============================================================
# 14.  MAIN ORCHESTRATOR
# ============================================================
def main():
    print("=" * 60)
    print(" HAnim LOA4 Female Humanoid — Starting build …")
    print("=" * 60)

    # 1. Clean slate
    clean_scene()
    print("[1] Scene cleaned.")

    # 2. Build armature
    arm_obj = build_armature()
    print(f"[2] Armature built: {len(arm_obj.data.bones)} bones.")

    # Compute world positions for reference
    world_pos_cache = {}
    def get_world(name):
        if name in world_pos_cache:
            return world_pos_cache[name]
        parent_name, offset = JOINTS_DEF[name]
        wp = get_world(parent_name) + Vector(offset) if parent_name else Vector(offset)
        world_pos_cache[name] = wp
        return wp
    for name in JOINTS_DEF:
        get_world(name)

    # 3. Body mesh
    bpy.ops.object.select_all(action='DESELECT')
    skin_obj = build_body_mesh(arm_obj)
    print("[3] Body mesh built and bound.")

    # 4. Face
    bpy.ops.object.select_all(action='DESELECT')
    face_objs = build_face(arm_obj, world_pos_cache)
    print(f"[4] Face features: {len(face_objs)} objects.")

    # 5. Hair
    bpy.ops.object.select_all(action='DESELECT')
    hair_objs = build_hair(arm_obj, world_pos_cache)
    print(f"[5] Hair: {len(hair_objs)} objects.")

    # 6. Ears
    bpy.ops.object.select_all(action='DESELECT')
    ear_objs = build_ears(arm_obj, world_pos_cache)
    print(f"[6] Ears: {len(ear_objs)} objects.")

    # 7. Clothing
    bpy.ops.object.select_all(action='DESELECT')
    blouse, leggings, shoe_objs = build_clothing(skin_obj, arm_obj, world_pos_cache)
    print(f"[7] Clothing built (blouse + leggings + {len(shoe_objs)} shoe parts).")

    # 8. Poncho
    bpy.ops.object.select_all(action='DESELECT')
    poncho = build_poncho(world_pos_cache)
    print("[8] Poncho created with cloth modifier.")

    # 9. Collision bodies
    add_collision(skin_obj,  thickness=0.045)
    add_collision(blouse,    thickness=0.040)
    add_collision(leggings,  thickness=0.040)
    print("[9] Collision modifiers added.")

    # 10. Animation
    bpy.ops.object.select_all(action='DESELECT')
    animate_humanoid(arm_obj)
    print("[10] Animation keyframes inserted.")

    # 11. Bake cloth
    print("[11] Baking cloth physics (this may take a while) …")
    try:
        bake_cloth(poncho)
        print("[11] Cloth bake complete.")
    except Exception as e:
        print(f"[11] Cloth bake warning: {e}")

    # 12. Collect animation data
    print("[12] Collecting bone animation data …")
    bone_anim = collect_bone_animation(arm_obj)

    print("[12] Collecting poncho vertex animation …")
    poncho_anim = collect_poncho_animation(poncho)

    # 13. Build and write X3D
    print("[13] Building X3D tree …")
    x3d_tree = build_x3d_tree(
        arm_obj, skin_obj, poncho,
        world_pos_cache, bone_anim, poncho_anim
    )

    print(f"[13] Writing X3D to: {OUTPUT_PATH}")
    write_x3d(x3d_tree, OUTPUT_PATH)

    # Restore final frame
    bpy.context.scene.frame_set(1)
    print("=" * 60)
    print(" Build complete!")
    print(f" X3D file: {OUTPUT_PATH}")
    print("=" * 60)


# ── Entry point ─────────────────────────────────────────────
if __name__ == "__main__":
    main()
