import bpy
import bmesh
import os
import math

# Try to import the x3d package
try:
    import x3d
except ImportError:
    print("ERROR: The 'x3d' python package is not installed.")
    print("Please install it in Blender's python environment via: pip install x3d")
    raise

# ==============================================================================
# 1. SCENE SETUP & PHYSICS GENERATION (Unchanged)
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
    
    # 4. Join components
    head.select_set(True)
    arms.select_set(True)
    torso.select_set(True)
    bpy.context.view_layer.objects.active = torso
    bpy.ops.object.join()
    
    # 5. Add Collision Modifier
    bpy.ops.object.modifier_add(type='COLLISION')
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
    
    # 2. Collision Properties
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
        print("Forcing cache update by stepping frames...")
        for f in range(start_frame, end_frame + 1):
            scene.frame_set(f)
            
    print("Baking complete.")

# ==============================================================================
# 2. X3D EXPORT LOGIC (USING X3D PACKAGE)
# ==============================================================================

def blender_to_x3d_coords(vector):
    """Converts Blender Z-up (x, y, z) to X3D Y-up (x, z, -y)."""
    return [vector.x, vector.z, -vector.y]

def get_mesh_data(obj):
    """Extracts points and indices from a Blender mesh object."""
    mesh = obj.data
    matrix = obj.matrix_world
    
    points = []
    for v in mesh.vertices:
        # Transform vertex to world space then convert to X3D coords
        co = matrix @ v.co
        points.extend(blender_to_x3d_coords(co))
        
    indices = []
    for poly in mesh.polygons:
        for loop_index in poly.loop_indices:
            indices.append(mesh.loops[loop_index].vertex_index)
        indices.append(-1)
        
    return points, indices

def create_static_mesh_node(obj):
    """Creates an X3D Transform containing a static Shape."""
    points, indices = get_mesh_data(obj)
    
    # Material Color
    color = [0.8, 0.8, 0.8]
    if obj.active_material:
        c = obj.active_material.diffuse_color
        color = [c[0], c[1], c[2]]

    # X3D Node Construction
    shape = x3d.Shape(
        appearance=x3d.Appearance(
            material=x3d.Material(diffuseColor=color)
        ),
        geometry=x3d.IndexedFaceSet(
            creaseAngle=3.14,
            coordIndex=indices,
            coord=x3d.Coordinate(point=points)
        )
    )
    
    transform = x3d.Transform(
        DEF=f"{obj.name}_Trans",
        children=[shape]
    )
    
    return transform

def create_animated_mesh_nodes(obj, start_frame, end_frame):
    """Creates Transform, TimeSensor, Interpolator, and Routes for animation."""
    scene = bpy.context.scene
    depsgraph = bpy.context.evaluated_depsgraph_get()
    obj_name = obj.name
    
    # 1. Get Base Geometry (Topology)
    scene.frame_set(start_frame)
    # We grab indices from the base mesh, assuming topology doesn't change
    _, indices = get_mesh_data(obj)
    
    # Material Color
    color = [0.2, 0.2, 0.8]
    if obj.active_material:
        c = obj.active_material.diffuse_color
        color = [c[0], c[1], c[2]]

    # 2. Prepare Animation Data
    keys = []
    key_values = [] # Large flattened list of all vertices for all frames
    total_frames = end_frame - start_frame
    
    print(f"Sampling vertex animation for {obj_name}...")
    
    matrix = obj.matrix_world
    
    for frame in range(start_frame, end_frame + 1):
        scene.frame_set(frame)
        
        # Get evaluated mesh (cloth sim applied)
        eval_obj = obj.evaluated_get(depsgraph)
        temp_mesh = eval_obj.to_mesh()
        
        # Calculate key (0.0 to 1.0)
        fraction = (frame - start_frame) / total_frames if total_frames > 0 else 0.0
        keys.append(fraction)
        
        # Collect vertex positions for this frame
        for v in temp_mesh.vertices:
            co = matrix @ v.co
            key_values.extend(blender_to_x3d_coords(co))
            
        eval_obj.to_mesh_clear()

    # 3. Construct X3D Nodes
    
    # Definition Names
    coord_def = f"{obj_name}_Coord"
    interp_def = f"{obj_name}_Interp"
    timer_def = "AnimationClock" # Generic name, or unique if multiple anims
    
    # Shape with empty Coordinate node (populated by Route)
    shape = x3d.Shape(
        appearance=x3d.Appearance(
            material=x3d.Material(diffuseColor=color)
        ),
        geometry=x3d.IndexedFaceSet(
            creaseAngle=3.14,
            coordIndex=indices,
            coord=x3d.Coordinate(DEF=coord_def, point=[]) # Start empty or with frame 1
        )
    )
    
    transform = x3d.Transform(
        DEF=f"{obj_name}_Trans",
        children=[shape]
    )
    
    # TimeSensor
    fps = scene.render.fps
    duration = total_frames / fps
    time_sensor = x3d.TimeSensor(
        DEF=timer_def,
        cycleInterval=duration,
        loop=True
    )
    
    # CoordinateInterpolator
    interpolator = x3d.CoordinateInterpolator(
        DEF=interp_def,
        key=keys,
        keyValue=key_values
    )
    
    # Routes
    r1 = x3d.ROUTE(fromNode=timer_def, fromField="fraction_changed", 
                   toNode=interp_def, toField="set_fraction")
    r2 = x3d.ROUTE(fromNode=interp_def, fromField="value_changed", 
                   toNode=coord_def, toField="point")
    
    return [transform, time_sensor, interpolator, r1, r2]

def export_scene_to_x3d(filepath, start_frame, end_frame):
    print(f"Exporting to {filepath} using x3d package...")
    
    # 1. Create Head
    head_node = x3d.head(
        children=[
            x3d.component(name="HAnim", level=3),
            x3d.meta(name="generator", content="Blender Python with x3d package")
        ]
    )

    # 2. Create Scene children
    scene_children = []
    
    # Add Navigation and Viewpoint
    scene_children.append(x3d.NavigationInfo(type=['EXAMINE', 'ANY']))
    scene_children.append(x3d.Viewpoint(description="Front View", position=[0, 2, 6], orientation=[1, 0, 0, -0.2]))
    
    # 3. Add Objects
    humanoid = bpy.data.objects.get("Humanoid")
    poncho = bpy.data.objects.get("Poncho")
    
    if humanoid:
        scene_children.append(create_static_mesh_node(humanoid))
        
    if poncho:
        anim_nodes = create_animated_mesh_nodes(poncho, start_frame, end_frame)
        scene_children.extend(anim_nodes)

    # 4. Construct Root
    x3d_root = x3d.X3D(
        profile="Full",
        version="3.3",
        head=head_node,
        Scene=x3d.Scene(children=scene_children)
    )
    
    # 5. Write to file
    xml_string = x3d_root.XML()
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(xml_string)
        
    print(f"Export finished: {filepath}")

if __name__ == "__main__":
    clean_scene()
    humanoid = create_humanoid()
    poncho = create_poncho()
    
    start_frame = 1
    end_frame = 60
    bake_simulation(start_frame, end_frame)
    
    output_filename = "poncho_drop_animation.X3DPSAIL.x3d"
    output_path = os.path.join(os.path.expanduser("~"), output_filename)
    
    export_scene_to_x3d(output_path, start_frame, end_frame)
