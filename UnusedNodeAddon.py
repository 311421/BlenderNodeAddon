import bpy

bl_info = {
    "name": "Material Node addon",
    "blender": (4, 5, 3),
    "description": "Поиск неиспользуемых нод",
    "category": "Node",
}

class UNUSED_NODE_OT_process_material_nodes(bpy.types.Operator):
    """Находит неиспользуемые ноды, добавляет к ним Attribute ноду и группирует их во Frame."""
    bl_idname = "unused_node.process_material_nodes"
    bl_label = "Process Unused Nodes"
    bl_options = {'REGISTER', 'UNDO'}

    def find_unused_nodes(self, node_tree):
        output_node = next((n for n in node_tree.nodes if n.type == 'OUTPUT_MATERIAL'), None)
        
        if not output_node:
            print(f"В дереве '{node_tree.name}' не найдена нода 'Material Output'.")
            return []

        used_nodes = {output_node}
        
        def traverse_inputs(node):
            for input in node.inputs:
                for link in input.links:
                    if link.from_node not in used_nodes:
                        used_nodes.add(link.from_node)
                        traverse_inputs(link.from_node)

        traverse_inputs(output_node)
        
        unused_nodes = [
            node for node in node_tree.nodes if node not in used_nodes
        ]
        
        return unused_nodes

class UNUSED_NODES_PT_nodes_panel(bpy.types.Panel):
    """Отрисовывает панель Node Tools в Node editor"""
    bl_label = "Unused Nodes Tools"
    bl_idname = "UNUSED_NODES_PT_nodes_panel"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Node Tools"

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.label(text="Unused Material Nodes", icon='NODE')

        op = box.operator(UNUSED_NODE_OT_process_material_nodes.bl_idname, text="Find, Connect & Frame Unused")

classes = [UNUSED_NODES_PT_nodes_panel]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()