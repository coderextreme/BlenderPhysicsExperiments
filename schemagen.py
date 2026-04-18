from lxml import etree

# --- Configuration and Namespaces ---
NS_MAP = {
    None: "http://www.w3.org/2001/XMLSchema",
    'xs': "http://www.w3.org/2001/XMLSchema"
}

def create_xsd_element(tag, attrib={}, nsmap=NS_MAP):
    """Helper to create an XML element within the XSD namespace."""
    return etree.Element(f"{{{nsmap['xs']}}}{tag}", attrib, nsmap=nsmap)

# --- Attribute Definitions Mapped from Input Documentation ---

# --- 1. option types ---
OPTION_FLAG_ATTRIBUTES = {
    'constraint': {'type': 'xs:string', 'use': 'optional'}, 'equality': {'type': 'xs:string', 'use': 'optional'},
    'frictionloss': {'type': 'xs:string', 'use': 'optional'}, 'limit': {'type': 'xs:string', 'use': 'optional'},
    'contact': {'type': 'xs:string', 'use': 'optional'}, 'spring': {'type': 'xs:string', 'use': 'optional'},
    'damper': {'type': 'xs:string', 'use': 'optional'}, 'gravity': {'type': 'xs:string', 'use': 'optional'},
    'clampctrl': {'type': 'xs:string', 'use': 'optional'}, 'warmstart': {'type': 'xs:string', 'use': 'optional'},
    'filterparent': {'type': 'xs:string', 'use': 'optional'}, 'actuation': {'type': 'xs:string', 'use': 'optional'},
    'refsafe': {'type': 'xs:string', 'use': 'optional'}, 'sensor': {'type': 'xs:string', 'use': 'optional'},
    'midphase': {'type': 'xs:string', 'use': 'optional'}, 'eulerdamp': {'type': 'xs:string', 'use': 'optional'},
    'autoreset': {'type': 'xs:string', 'use': 'optional'}, 'nativeccd': {'type': 'xs:string', 'use': 'optional'},
    'island': {'type': 'xs:string', 'use': 'optional'}, 'override': {'type': 'xs:string', 'use': 'optional'},
    'energy': {'type': 'xs:string', 'use': 'optional'}, 'fwdinv': {'type': 'xs:string', 'use': 'optional'},
    'invdiscrete': {'type': 'xs:string', 'use': 'optional'}, 'multiccd': {'type': 'xs:string', 'use': 'optional'},
    'sleep': {'type': 'xs:string', 'use': 'optional'},
}

OPTION_ATTRIBUTES = {
    "timestep": {'type': 'xs:double', 'use': 'optional'}, "impratio": {'type': 'xs:double', 'use': 'optional'},
    "tolerance": {'type': 'xs:double', 'use': 'optional'}, "ls_tolerance": {'type': 'xs:double', 'use': 'optional'},
    "noslip_tolerance": {'type': 'xs:double', 'use': 'optional'}, "ccd_tolerance": {'type': 'xs:double', 'use': 'optional'},
    "sleep_tolerance": {'type': 'xs:double', 'use': 'optional'}, "gravity": {'type': 'xs:string', 'use': 'optional'},
    "wind": {'type': 'xs:string', 'use': 'optional'}, "magnetic": {'type': 'xs:string', 'use': 'optional'},
    "density": {'type': 'xs:double', 'use': 'optional'}, "viscosity": {'type': 'xs:double', 'use': 'optional'},
    "o_margin": {'type': 'xs:double', 'use': 'optional'}, "o_solref": {'type': 'xs:string', 'use': 'optional'},
    "o_solimp": {'type': 'xs:string', 'use': 'optional'}, "o_friction": {'type': 'xs:double', 'use': 'optional'},
    "integrator": {'type': 'xs:string', 'use': 'optional'}, "cone": {'type': 'xs:string', 'use': 'optional'},
    "jacobian": {'type': 'xs:string', 'use': 'optional'}, "solver": {'type': 'xs:string', 'use': 'optional'},
    "iterations": {'type': 'xs:integer', 'use': 'optional'}, "ls_iterations": {'type': 'xs:integer', 'use': 'optional'},
    "noslip_iterations": {'type': 'xs:integer', 'use': 'optional'}, "ccd_iterations": {'type': 'xs:integer', 'use': 'optional'},
    "sdf_iterations": {'type': 'xs:integer', 'use': 'optional'}, "sdf_initpoints": {'type': 'xs:integer', 'use': 'optional'},
    "actuatorgroupdisable": {'type': 'xs:string', 'use': 'optional'},
}

# --- 2. compiler types ---
compiler_attrs = {
    "autolimits": {'type': 'xs:string', 'use': 'optional'},
    "boundmass": {'type': 'xs:double', 'use': 'optional'},
    "boundinertia": {'type': 'xs:double', 'use': 'optional'},
    "settotalmass": {'type': 'xs:double', 'use': 'optional'},
    "balanceinertia": {'type': 'xs:string', 'use': 'optional'},
    "strippath": {'type': 'xs:string', 'use': 'optional'},
    "coordinate": {'type': 'xs:string', 'use': 'optional'},
    "angle": {'type': 'xs:string', 'use': 'optional'},
    "fitaabb": {'type': 'xs:string', 'use': 'optional'},
    "eulerseq": {'type': 'xs:string', 'use': 'optional'},
    "meshdir": {'type': 'xs:string', 'use': 'optional'},
    "texturedir": {'type': 'xs:string', 'use': 'optional'},
    "discardvisual": {'type': 'xs:string', 'use': 'optional'},
    "usethread": {'type': 'xs:string', 'use': 'optional'},
    "fusestatic": {'type': 'xs:string', 'use': 'optional'},
    "inertiafromgeom": {'type': 'xs:string', 'use': 'optional'},
    "inertiagrouprange": {'type': 'xs:string', 'use': 'optional'},
    "saveinertial": {'type': 'xs:string', 'use': 'optional'},
    "assetdir": {'type': 'xs:string', 'use': 'optional'},
    "alignfree": {'type': 'xs:string', 'use': 'optional'},
}

# --- 3. body/geom/joint (Structural elements) ---
joint_attrs = {
    "type": {'type': 'xs:string', 'use': 'required'},
    "stiffness": {'type': 'xs:double', 'use': 'optional'},
    "damping": {'type': 'xs:double', 'use': 'optional'},
    "range": {'type': 'xs:string', 'use': 'optional'},
    "margin": {'type': 'xs:double', 'use': 'optional'},
    "armature": {'type': 'xs:double', 'use': 'optional'},
    "frictionloss": {'type': 'xs:double', 'use': 'optional'},
}

geom_attrs = {
    "type": {'type': 'xs:string', 'use': 'required'},
    "size": {'type': 'xs:string', 'use': 'optional'},
    "material": {'type': 'xs:string', 'use': 'optional'},
    "friction": {'type': 'xs:double', 'use': 'optional'},
    "mass": {'type': 'xs:double', 'use': 'optional'},
    "density": {'type': 'xs:double', 'use': 'optional'},
    "margin": {'type': 'xs:double', 'use': 'optional'},
    "rgba": {'type': 'xs:string', 'use': 'optional'},
}

site_attrs = {
    "type": {'type': 'xs:string', 'use': 'optional'},
    "size": {'type': 'xs:double', 'use': 'optional'},
    "rgba": {'type': 'xs:string', 'use': 'optional'},
}

# --- List of Elements/Choices ---
ASSET_CHILDREN = [
    "mesh", "hfield", "skin", "texture", "material", "model"
]
TOP_LEVEL_ELEMENTS = [
    "compiler", "option", "asset", "visual", "custom", "extension",
    "actuator", "sensor", "equality", "tendon", "contact", "keyframe", "worldbody"
]
ACTUATOR_CHILDREN = [
    "general", "motor", "position", "velocity", "intvelocity", "damper",
    "cylinder", "muscle", "adhesion", "plugin"
]
SENSOR_CHILDREN = [
    "touch", "accelerometer", "velocimeter", "gyro", "force", "torque", "magnetometer",
    "camprojection", "rangefinder", "jointpos", "jointvel", "tendonpos", "tendonvel",
    "actuatorpos", "actuatorvel", "actuatorfrc", "jointactuatorfrc", "tendonactuatorfrc",
    "ballquat", "ballangvel", "jointlimitpos", "jointlimitvel", "jointlimitfrc",
    "tendonlimitpos", "tendonlimitvel", "tendonlimitfrc", "framepos", "framequat",
    "framexaxis", "frameyaxis", "framezaxis", "framelinvel", "frameangvel",
    "framelinacc", "frameangacc", "subtreecom", "subtreelinvel", "subtreeangmom",
    "insidesite", "distance", "normal", "fromto", "contact", "e_potential", "e_kinetic",
    "clock", "user", "tactile", "plugin", "flex", "deformable_skin"
]
EQUALITY_CHILDREN = [
    "connect", "weld", "joint", "tendon", "flex"
]
TENDON_CHILDREN = [
    "spatial", "fixed"
]
CONTACT_CHILDREN = [
    "pair", "exclude"
]
DEFAULT_CHILDREN = [
    "mesh", "material", "joint", "geom", "site", "camera", "light", "pair",
    "equality", "tendon", "general", "motor", "position", "velocity",
    "intvelocity", "damper", "cylinder", "muscle", "adhesion"
]
VISUAL_CHILDREN = [
    "global", "quality", "headlight", "map", "scale", "rgba"
]
CUSTOM_CHILDREN = [
    "numeric", "text", "tuple"
]


# --- HELPER DEFINITIONS FOR RECURRING TYPES ---

def create_minimal_ct(schema_element, name, attrs_dict=None, children_list=None):
    """Creates a complexType definition for an element, passing the schema root element."""
    ct = create_xsd_element("complexType", {"name": f"{name}_type"})
    seq = create_xsd_element("sequence", {"minOccurs":"0"})

    has_children = False
    if children_list:
        for child in children_list:
            # Skip elements whose types aren't defined or are self-referential within this simplified structure
            if child in ["plugin", "composite", "flexcomp", "key", "config", "element", "layer"]:
                continue

            child_type = f"{child}_type"
            el = create_xsd_element("element", {"name": child, "type": child_type, "minOccurs": "0", "maxOccurs": "unbounded"})
            seq.append(el)
            has_children = True

    if has_children:
        ct.append(seq)

    if attrs_dict:
        for attr_name, props in attrs_dict.items():
            ct.append(create_xsd_element("attribute", attrib={"name": attr_name, "type": props['type'], "use": props['use']}))

    schema_element.append(ct)
    return ct

# --- XSD Construction Function ---

def build_xsd_structure():
    schema = create_xsd_element("schema", attrib={"targetNamespace": "", "elementFormDefault": "qualified"})

    # --- 1. Define CTs for Asset Children (Stubs) ---
    for el_name in ASSET_CHILDREN:
        create_minimal_ct(schema, f"asset_{el_name}")

    # --- 2. Define CTs for Structural Elements & Containers ---

    # CT: joint_type
    ct_joint = create_xsd_element("complexType", {"name": "joint_type"})
    for attr_name, props in joint_attrs.items():
        ct_joint.append(create_xsd_element("attribute", attrib={"name": attr_name, "type": props['type'], "use": props['use']}))
    schema.append(ct_joint)

    # CT: geom_type
    ct_geom = create_xsd_element("complexType", {"name": "geom_type"})
    for attr_name, props in geom_attrs.items():
        ct_geom.append(create_xsd_element("attribute", attrib={"name": attr_name, "type": props['type'], "use": props['use']}))
    schema.append(ct_geom)

    # CT: site_type
    ct_site = create_xsd_element("complexType", {"name": "site_type"})
    for attr_name, props in site_attrs.items():
        ct_site.append(create_xsd_element("attribute", attrib={"name": attr_name, "type": props['type'], "use": props['use']}))
    schema.append(ct_site)

    # CT: body_type (Recursive)
    ct_body = create_xsd_element("complexType", {"name": "body_type", "mixed": "true"})
    seq = create_xsd_element("sequence")

    seq.append(create_xsd_element("element", {"name": "inertial", "type": "body_inertial_type", "minOccurs": "0"}))
    seq.append(create_xsd_element("element", {"name": "joint", "type": "joint_type", "minOccurs": "0", "maxOccurs": "unbounded"}))
    seq.append(create_xsd_element("element", {"name": "geom", "type": "geom_type", "minOccurs": "0", "maxOccurs": "unbounded"}))
    seq.append(create_xsd_element("element", {"name": "site", "type": "site_type", "minOccurs": "0", "maxOccurs": "unbounded"}))
    # Self-reference for body recursion
    seq.append(create_xsd_element("element", {"name": "body", "type": "body_type", "maxOccurs": "unbounded", "minOccurs": "0"}))
    # Placeholder for other complex body children (plugin, composite, camera, light)
    seq.append(create_xsd_element("any", {"namespace": "##other", "processContents": "lax", "minOccurs": "0", "maxOccurs": "unbounded"}))

    ct_body.append(seq)
    ct_body.append(create_xsd_element("attribute", {"name": "name", "type": "xs:string", "use": "optional"}))
    ct_body.append(create_xsd_element("attribute", {"name": "pos", "type": "xs:string", "use": "optional"}))
    ct_body.append(create_xsd_element("attribute", {"name": "quat", "type": "xs:string", "use": "optional"}))
    schema.append(ct_body)

    # CT: worldbody_type
    ct_worldbody = create_xsd_element("complexType", {"name": "worldbody_type"})
    seq_wb = create_xsd_element("sequence")
    seq_wb.append(create_xsd_element("element", {"name": "body", "type": "body_type", "minOccurs": "1", "maxOccurs": "unbounded"}))
    ct_worldbody.append(seq_wb)
    schema.append(ct_worldbody)

    # CT: asset_type (Choice)
    ct_asset = create_xsd_element("complexType", {"name": "asset_type"})
    choice_el = create_xsd_element("choice", {"minOccurs":"0", "maxOccurs":"unbounded"})
    for el in ASSET_CHILDREN:
        choice_el.append(create_xsd_element("element", {"name": el, "type": f"asset_{el}_type"}))
    ct_asset.append(choice_el)
    schema.append(ct_asset)

    # CT: option_flag_type
    ct_flag = create_xsd_element("complexType", {"name": "option_flag_type"})
    for attr_name, props in OPTION_FLAG_ATTRIBUTES.items():
        ct_flag.append(create_xsd_element("attribute", attrib={"name": attr_name, "type": props['type'], "use": props['use']}))
    schema.append(ct_flag)

    # CT: option_type
    ct_option = create_xsd_element("complexType", {"name": "option_type"})
    ct_option.append(create_xsd_element("element", {"name": "flag", "type": "option_flag_type", "minOccurs": "0"}))
    for attr_name, props in OPTION_ATTRIBUTES.items():
        ct_option.append(create_xsd_element("attribute", attrib={"name": attr_name, "type": props['type'], "use": props['use']}))
    schema.append(ct_option)

    # CT: compiler_type
    ct_compiler = create_xsd_element("complexType", {"name": "compiler_type"})
    ct_compiler.append(create_xsd_element("element", {"name": "lengthrange", "type": "compiler_lengthrange_type", "minOccurs": "0"}))
    for attr_name, props in compiler_attrs.items():
        ct_compiler.append(create_xsd_element("attribute", attrib={"name": attr_name, "type": props['type'], "use": props['use']}))
    schema.append(ct_compiler)

    # --- Define Types for Default Sections (Using helper function) ---

    default_attrs_map = {
        "mesh": {'scale': {'type': 'xs:double', 'use': 'optional'}},
        "material": {'rgba': {'type': 'xs:string', 'use': 'optional'}},
        "joint": {'type': {'type': 'xs:string', 'use': 'optional'}, 'stiffness': {'type': 'xs:double', 'use': 'optional'}},
        "geom": {'type': {'type': 'xs:string', 'use': 'optional'}, 'rgba': {'type': 'xs:string', 'use': 'optional'}},
        "site": {'type': {'type': 'xs:string', 'use': 'optional'}, 'size': {'type': 'xs:double', 'use': 'optional'}},
        "camera": {'fovy': {'type': 'xs:double', 'use': 'optional'}},
        "light": {'pos': {'type': 'xs:string', 'use': 'optional'}},
        "pair": {'friction': {'type': 'xs:double', 'use': 'optional'}},
        "equality": {'active': {'type': 'xs:string', 'use': 'optional'}},
        "tendon": {'width': {'type': 'xs:double', 'use': 'optional'}},
        "general": {'ctrlrange': {'type': 'xs:string', 'use': 'optional'}},
        "motor": {'ctrlrange': {'type': 'xs:string', 'use': 'optional'}},
        "position": {'kp': {'type': 'xs:double', 'use': 'optional'}},
        "velocity": {'kv': {'type': 'xs:double', 'use': 'optional'}},
        "intvelocity": {'kp': {'type': 'xs:double', 'use': 'optional'}},
        "damper": {'kv': {'type': 'xs:double', 'use': 'optional'}},
        "cylinder": {'area': {'type': 'xs:double', 'use': 'optional'}},
        "muscle": {'timeconst': {'type': 'xs:double', 'use': 'optional'}},
        "adhesion": {'gain': {'type': 'xs:double', 'use': 'optional'}},
    }

    for name, attrs in default_attrs_map.items():
        create_minimal_ct(schema, f"default-{name}", attrs)

    create_minimal_ct(schema, "default", children_list=DEFAULT_CHILDREN)
    create_minimal_ct(schema, "visual", children_list=VISUAL_CHILDREN)
    create_minimal_ct(schema, "custom", children_list=CUSTOM_CHILDREN)
    create_minimal_ct(schema, "extension", children_list=["plugin"])
    create_minimal_ct(schema, "actuator", children_list=ACTUATOR_CHILDREN)
    create_minimal_ct(schema, "sensor", children_list=SENSOR_CHILDREN)
    create_minimal_ct(schema, "equality", children_list=EQUALITY_CHILDREN)
    create_minimal_ct(schema, "tendon", children_list=TENDON_CHILDREN)
    create_minimal_ct(schema, "contact", children_list=CONTACT_CHILDREN)
    create_minimal_ct(schema, "keyframe", children_list=["key"])
    create_minimal_ct(schema, "plugin_config")
    create_minimal_ct(schema, "plugin_instance")

    # Placeholder for other internal structures referenced
    create_minimal_ct(schema, "body_inertial_type")
    create_minimal_ct(schema, "compiler_lengthrange_type")

    # --- 4. Root Element Definition ---
    ct_mujoco = create_xsd_element("complexType", {"name": "mujoco_type"})
    seq_mujoco = create_xsd_element("sequence")

    for el_name in TOP_LEVEL_ELEMENTS:
        type_name = "worldbody_type" if el_name == "worldbody" else f"{el_name}_type"
        seq_mujoco.append(create_xsd_element("element", {"name": el_name, "type": type_name, "minOccurs": "0"}))

    ct_mujoco.append(seq_mujoco)
    schema.append(ct_mujoco)

    root_element = create_xsd_element("element", {"name": "mujoco", "type": "mujoco_type"})
    schema.append(root_element)

    return schema

# --- Execution ---
xml_schema_tree = build_xsd_structure()
xsd_output = etree.tostring(xml_schema_tree, pretty_print=True, xml_declaration=True, encoding="UTF-8").decode()

# Save to file
FILE_NAME = "mujoco_inferred_structure_full.xsd"
with open(FILE_NAME, "w", encoding="utf-8") as f:
    f.write(xsd_output)

print(f"Successfully generated a structural XSD skeleton: {FILE_NAME}")
print("\n--- Start of XSD Content (Partial View) ---")
print(xsd_output[:2000] + "\n...\n" + xsd_output[-2000:])
