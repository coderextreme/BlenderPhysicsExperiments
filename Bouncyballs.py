import bpy
import math

class BouncyBall:
    """Class to create and manage bouncy ball objects with rigid body physics"""
    
    def __init__(self, name, location, color, radius=1.0, mass=1.0, restitution=0.95):
        """
        Initialize a bouncy ball
        
        Args:
            name: Name of the ball object
            location: Tuple (x, y, z) for ball position
            color: Tuple (r, g, b, a) for ball color
            radius: Radius of the sphere
            mass: Mass of the ball
            restitution: Bounciness factor (0-1, higher = bouncier)
        """
        self.name = name
        self.location = location
        self.color = color
        self.radius = radius
        self.mass = mass
        self.restitution = restitution
        self.obj = None
        
    def create(self):
        """Create the ball mesh and set up physics"""
        # Create sphere mesh
        bpy.ops.mesh.primitive_uv_sphere_add(
            radius=self.radius, 
            location=self.location, 
            segments=32, 
            ring_count=16
        )
        self.obj = bpy.context.active_object
        self.obj.name = self.name
        
        # Add material
        self._add_material()
        
        # Add rigid body physics
        self._add_physics()
        
        print(f"{self.name} created at: {self.location}")
        
        return self.obj
    
    def _add_material(self):
        """Add colored material to the ball"""
        mat = bpy.data.materials.new(name=f"{self.name}_Material")
        mat.diffuse_color = self.color
        self.obj.data.materials.append(mat)
    
    def _add_physics(self):
        """Add rigid body physics to the ball"""
        bpy.ops.rigidbody.object_add()
        self.obj.rigid_body.type = 'ACTIVE'
        self.obj.rigid_body.collision_shape = 'SPHERE'
        self.obj.rigid_body.restitution = self.restitution
        self.obj.rigid_body.friction = 0.1
        self.obj.rigid_body.mass = self.mass
        self.obj.rigid_body.linear_damping = 0.0
        self.obj.rigid_body.angular_damping = 0.0
    
    def set_restitution(self, value):
        """Set the bounciness of the ball (0-1)"""
        if self.obj and self.obj.rigid_body:
            self.obj.rigid_body.restitution = value
    
    def set_mass(self, value):
        """Set the mass of the ball"""
        if self.obj and self.obj.rigid_body:
            self.obj.rigid_body.mass = value


class Ground:
    """Class to create and manage ground plane with collision"""
    
    def __init__(self, size=20, location=(0, 0, 0), restitution=0.95):
        """
        Initialize ground plane
        
        Args:
            size: Size of the ground plane
            location: Tuple (x, y, z) for ground position
            restitution: Bounciness of the ground surface
        """
        self.size = size
        self.location = location
        self.restitution = restitution
        self.obj = None
    
    def create(self):
        """Create the ground plane and set up collision"""
        bpy.ops.mesh.primitive_plane_add(size=self.size, location=self.location)
        self.obj = bpy.context.active_object
        self.obj.name = "Ground"
        
        # Add rigid body physics (passive)
        bpy.ops.rigidbody.object_add()
        self.obj.rigid_body.type = 'PASSIVE'
        self.obj.rigid_body.collision_shape = 'MESH'
        self.obj.rigid_body.restitution = self.restitution
        self.obj.rigid_body.friction = 0.1
        
        # Add material
        mat = bpy.data.materials.new(name="Ground_Material")
        mat.diffuse_color = (0.3, 0.3, 0.3, 1.0)
        self.obj.data.materials.append(mat)
        
        print(f"Ground created at: {self.location}")
        
        return self.obj


def clear_scene():
    """Clear all objects and materials from the scene"""
    for obj in bpy.data.objects:
        bpy.data.objects.remove(obj, do_unlink=True)
    
    for mat in bpy.data.materials:
        bpy.data.materials.remove(mat)


def setup_scene(frame_start=1, frame_end=250):
    """Configure scene settings for animation"""
    bpy.context.scene.frame_start = frame_start
    bpy.context.scene.frame_end = frame_end
    bpy.context.scene.gravity = (0, 0, -9.81)
    
    # Configure rigid body world
    if bpy.context.scene.rigidbody_world:
        bpy.context.scene.rigidbody_world.enabled = True
        bpy.context.scene.rigidbody_world.point_cache.frame_start = frame_start
        bpy.context.scene.rigidbody_world.point_cache.frame_end = frame_end
    
    # Make sure we're at frame 1
    bpy.context.scene.frame_set(frame_start)
    
    # Set viewport shading
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    space.shading.type = 'SOLID'


def main():
    """Main function to set up the bouncy ball simulation"""
    # Clear existing scene
    clear_scene()
    
    # Create ground
    ground = Ground(size=20, location=(0, 0, 0), restitution=0.95)
    ground.create()
    
    # Create bouncy balls
    ball1 = BouncyBall(
        name="RedBall",
        location=(-2, 0, 5),
        color=(1.0, 0.0, 0.0, 1.0),  # Red
        radius=1.0,
        mass=1.0,
        restitution=0.95
    )
    ball1.create()
    
    ball2 = BouncyBall(
        name="BlueBall",
        location=(2, 0, 8),
        color=(0.0, 0.3, 1.0, 1.0),  # Blue
        radius=1.0,
        mass=1.0,
        restitution=0.95
    )
    ball2.create()
    
    # Setup scene
    setup_scene(frame_start=1, frame_end=250)
    
    # Select balls for visibility
    bpy.ops.object.select_all(action='DESELECT')
    ball1.obj.select_set(True)
    ball2.obj.select_set(True)
    bpy.context.view_layer.objects.active = ball1.obj
    
    # Force viewport update
    bpy.context.view_layer.update()
    
    print("=" * 60)
    print("BOUNCY BALL SIMULATION - OBJECT-ORIENTED VERSION")
    print("=" * 60)
    print(f"Total objects in scene: {len(bpy.data.objects)}")
    print("=" * 60)
    print("Press SPACEBAR to play animation and watch them bounce!")
    print("=" * 60)


# Run the main function
if __name__ == "__main__":
    main()
