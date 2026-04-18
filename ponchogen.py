import bpy
import bmesh
import os

# ==============================================================================
# 1. SCENE SETUP & PHYSICS GENERATION
# ==============================================================================

def clean_scene():
    """Clears the scene to ensure a fresh start."""
    if bpy.context.active_object and bpy.context.active_object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
        
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    
    for collection in [bpy.data.meshes, bpy.data.materials, bpy.data.images]:
        for block in collection:
            collection.remove(block)

def create_humanoid():
    """Creates a dummy humanoid with Collision physics."""
    bpy.ops.object.select_all(action='DESELECT')
    
    # 1. Create Torso
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 1.2))
    torso = bpy.context.active_object
    torso.name = "Humanoid"
    torso.scale = (0.5, 0.3, 0.9)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    # 2. Create Head
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.25, location=(0, 0, 1.85))
    head = bpy.context.active_object
    
    # 3. Create Arms
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 1.5))
    arms = bpy.context.active_object
    arms.scale = (1.8, 0.25, 0.25)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    
    # 4. Join components (Blender 4.x compatible)
    head.select_set(True)
    arms.select_set(True)
    torso.select_set(True)
    bpy.context.view_layer.objects.active = torso
    bpy.ops.object.join()
    
    # 5. Add Collision Modifier
    bpy.ops.object.modifier_add(type='COLLISION')
    # Collision settings for the collider object
    torso.modifiers["Collision"].settings.thickness_outer = 0.02
    
    mat = bpy.data.materials.new(name="SkinMat")
    mat.diffuse_color = (0.8, 0.6, 0.5, 1)
    if torso.data.materials:
        torso.data.materials[0] = mat
    else:
        torso.data.materials.append(mat)
    
    return torso

def create_poncho():
    """Creates the cloth object."""
    bpy.ops.object.select_all(action='DESELECT')
    
    bpy.ops.mesh.primitive_plane_add(size=2.2, location=(0, 0, 2.3))
    poncho = bpy.context.active_object
    poncho.name = "Poncho"
    
    # Geometry: Subdivide and create hole
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.subdivide(number_cuts=25) 
    
    bm = bmesh.from_edit_mesh(poncho.data)
    bm.faces.ensure_lookup_table()
    to_delete = [f for f in bm.faces if abs(f.calc_center_median().x) < 0.15 and abs(f.calc_center_median().y) < 0.15]
    bmesh.ops.delete(bm, geom=to_delete, context='FACES')
    bmesh.update_edit_mesh(poncho.data)
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # Physics: Add Cloth Modifier
    bpy.ops.object.modifier_add(type='CLOTH')
    cloth_modifier = poncho.modifiers["Cloth"]
    
    # 1. Physical Properties
    cset = cloth_modifier.settings
    cset.quality = 5
    cset.mass = 0.3
    cset.bending_model = 'LINEAR'
    cset.tension_stiffness = 5
    cset.compression_stiffness = 5
    cset.shear_stiffness = 5
    cset.bending_stiffness = 0.1
    
    # 2. Collision Properties (FIXED FOR BLENDER 4.x)
    # Collision settings are stored in 'collision_settings', not 'settings'
    col_settings = cloth_modifier.collision_settings
    col_settings.use_self_collision = True
    col_settings.self_distance_min = 0.02
    col_settings.distance_min = 0.02
    
    # Visuals
    for p in poncho.data.polygons:
        p.use_smooth = True
        
    mat = bpy.data.materials.new(name="ClothMat")
    mat.diffuse_color = (0.8, 0.1, 0.1, 1)
    if poncho.data.materials:
        poncho.data.materials[0] = mat
    else:
        poncho.data.materials.append(mat)
        
    return poncho

def bake_simulation(start_frame, end_frame):
    """Sets timeline and bakes physics."""
    scene = bpy.context.scene
    scene.frame_start = start_frame
    scene.frame_end = end_frame
    
    print(f"Baking simulation from frame {start_frame} to {end_frame}...")
    
    bpy.ops.object.select_all(action='SELECT')
        
    if bpy.ops.ptcache.bake_all.poll():
        bpy.ops.ptcache.bake_all(bake=True)
    else:
        # Fallback if bake_all isn't pollable (rare but possible in script contexts)
        print("Forcing cache update by stepping frames...")
        for f in range(start_frame, end_frame + 1):
            scene.frame_set(f)
            
    print("Baking complete.")

# ==============================================================================
# 2. X3D XML EXPORT LOGIC
# ==============================================================================

def write_x3d_header(f):
    f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    f.write('<!DOCTYPE X3D PUBLIC "ISO//Web3D//DTD X3D 3.3//EN" "https://www.web3d.org/specifications/x3d-3.3.dtd">\n')
    f.write('<X3D profile="Full" version="3.3" xmlns:xsd="http://www.w3.org/2001/XMLSchema-instance" xsd:noNamespaceSchemaLocation="https://www.web3d.org/specifications/x3d-3.3.xsd">\n')
    f.write('  <head>\n')
    f.write('    <component name="HAnim" level="3"/><meta name="generator" content="Blender Python Script"/>\n')
    f.write('  </head>\n')
    f.write('  <Scene>\n')
    f.write('    <NavigationInfo type=\'"EXAMINE" "ANY"\'/>\n')
    f.write('    <Viewpoint description="Front View" position="0 2 6" orientation="1 0 0 -0.2"/>\n')

def export_static_mesh(f, obj, indent="    "):
    """Exports a static mesh."""
    mesh = obj.data
    color_str = "0.8 0.8 0.8"
    if obj.active_material:
        c = obj.active_material.diffuse_color
        color_str = f"{c[0]:.3f} {c[1]:.3f} {c[2]:.3f}"
        
    f.write(f'{indent}<Transform DEF="{obj.name}_Trans">\n')
    f.write(f'{indent}  <Shape>\n')
    f.write(f'{indent}    <Appearance>\n')
    f.write(f'{indent}      <Material diffuseColor="{color_str}"/>\n')
    f.write(f'{indent}    </Appearance>\n')
    
    coord_indices = []
    for poly in mesh.polygons:
        for loop_index in poly.loop_indices:
            coord_indices.append(str(mesh.loops[loop_index].vertex_index))
        coord_indices.append("-1")
    index_str = " ".join(coord_indices)
    
    points = []
    matrix = obj.matrix_world
    for v in mesh.vertices:
        co = matrix @ v.co
        # Blender Z-up to X3D Y-up convention: (x, z, -y)
        points.append(f"{co.x:.4f} {co.z:.4f} {-co.y:.4f}")
    
    point_str = " ".join(points)
    
    f.write(f'{indent}    <IndexedFaceSet creaseAngle="3.14" coordIndex="{index_str}">\n')
    f.write(f'{indent}      <Coordinate point="{point_str}"/>\n')
    f.write(f'{indent}    </IndexedFaceSet>\n')
    f.write(f'{indent}  </Shape>\n')
    f.write(f'{indent}</Transform>\n')

def export_animated_mesh(f, obj, start_frame, end_frame, indent="    "):
    """Exports a mesh with CoordinateInterpolator."""
    scene = bpy.context.scene
    depsgraph = bpy.context.evaluated_depsgraph_get()
    
    mesh_data = obj.data
    obj_name = obj.name
    
    scene.frame_set(start_frame)
    
    coord_indices = []
    for poly in mesh_data.polygons:
        for loop_index in poly.loop_indices:
            coord_indices.append(str(mesh_data.loops[loop_index].vertex_index))
        coord_indices.append("-1")
    index_str = " ".join(coord_indices)
    
    color_str = "0.2 0.2 0.8"
    if obj.active_material:
        c = obj.active_material.diffuse_color
        color_str = f"{c[0]:.3f} {c[1]:.3f} {c[2]:.3f}"

    f.write(f'{indent}<Transform DEF="{obj_name}_Trans">\n')
    f.write(f'{indent}  <Shape>\n')
    f.write(f'{indent}    <Appearance>\n')
    f.write(f'{indent}      <Material diffuseColor="{color_str}"/>\n')
    f.write(f'{indent}    </Appearance>\n')
    f.write(f'{indent}    <IndexedFaceSet creaseAngle="3.14" coordIndex="{index_str}">\n')
    f.write(f'{indent}      <Coordinate DEF="{obj_name}_Coord" point=""/>\n') 
    f.write(f'{indent}    </IndexedFaceSet>\n')
    f.write(f'{indent}  </Shape>\n')
    f.write(f'{indent}</Transform>\n')

    keys = []
    key_values = []
    total_frames = end_frame - start_frame
    
    print(f"Sampling vertex animation for {obj_name}...")
    
    for frame in range(start_frame, end_frame + 1):
        scene.frame_set(frame)
        
        # Get evaluated mesh (cloth sim applied)
        eval_obj = obj.evaluated_get(depsgraph)
        temp_mesh = eval_obj.to_mesh()
        
        fraction = (frame - start_frame) / total_frames if total_frames > 0 else 0.0
        keys.append(f"{fraction:.4f}")
        
        frame_coords = []
        matrix = obj.matrix_world
        
        for v in temp_mesh.vertices:
            co = matrix @ v.co
            frame_coords.append(f"{co.x:.4f} {co.z:.4f} {-co.y:.4f}")
            
        key_values.append(" ".join(frame_coords))
        eval_obj.to_mesh_clear()

    keys_str = " ".join(keys)
    key_values_str = " ".join(key_values)

    fps = scene.render.fps
    duration = total_frames / fps
    f.write(f'{indent}<TimeSensor DEF="AnimationClock" cycleInterval="{duration:.2f}" loop="true"/>\n')
    f.write(f'{indent}<CoordinateInterpolator DEF="{obj_name}_Interp" key="{keys_str}" keyValue="{key_values_str}"/>\n')
    f.write(f'{indent}<ROUTE fromNode="AnimationClock" fromField="fraction_changed" toNode="{obj_name}_Interp" toField="set_fraction"/>\n')
    f.write(f'{indent}<ROUTE fromNode="{obj_name}_Interp" fromField="value_changed" toNode="{obj_name}_Coord" toField="point"/>\n')

def export_scene_to_x3d(filepath, start_frame, end_frame):
    print(f"Exporting to {filepath}...")
    
    with open(filepath, 'w', encoding='utf-8') as f:
        write_x3d_header(f)
        
        humanoid = bpy.data.objects.get("Humanoid")
        poncho = bpy.data.objects.get("Poncho")
        
        if humanoid:
            export_static_mesh(f, humanoid)
            
        if poncho:
            export_animated_mesh(f, poncho, start_frame, end_frame)
            
        f.write('  </Scene>\n')
        f.write('</X3D>\n')
        
    print(f"Export finished: {filepath}")

if __name__ == "__main__":
    clean_scene()
    humanoid = create_humanoid()
    poncho = create_poncho()
    
    start_frame = 1
    end_frame = 60
    bake_simulation(start_frame, end_frame)
    
    output_filename = "poncho_drop_animation.x3d"
    output_path = os.path.join(os.path.expanduser("~"), output_filename)
    
    export_scene_to_x3d(output_path, start_frame, end_frame)
