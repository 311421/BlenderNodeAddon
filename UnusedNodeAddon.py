import bpy
from bpy.props import FloatProperty

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
    
    frame_x_pos: FloatProperty(
        name="Frame X Position",
        description="X-координата для расположения Frame",
        default=1000.0
    )
    frame_y_pos: FloatProperty(
        name="Frame Y Position",
        description="Y-координата для расположения Frame",
        default=100.0
    )
    
    def find_unused_nodes(self, node_tree: bpy.types.NodeTree) -> list[bpy.types.Node]:
        output_node = next((n for n in node_tree.nodes if n.type == 'OUTPUT_MATERIAL'), None)
        
        if not output_node:
            self.report({'INFO'}, f"В нодовом дереве '{node_tree.name}' не найдена нода 'Material Output'.")
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

    def execute(self, context):
        all_unused_nodes = []
        
        for mat in bpy.data.materials:
            if not mat.node_tree:
                continue
            node_tree = mat.node_tree
            unused_nodes_in_mat = self.find_unused_nodes(node_tree)
            if not unused_nodes_in_mat:
                self.report({'INFO'}, f"--- Материал: {mat.name} ---")
                self.report({'INFO'}, "  > Неиспользуемых нод не найдено.")
                continue
            self.report({'INFO'}, f"--- Материал: {mat.name} ({len(unused_nodes_in_mat)} неиспользуемых нод) ---")
            
            frame_node = node_tree.nodes.new(type='NodeFrame')
            frame_node.label = "UNUSED NODES"
            
            min_x, max_x = float('inf'), float('-inf')
            min_y, max_y = float('inf'), float('-inf')

            cur_height = 0
            
            # Обработка нод
            for node in unused_nodes_in_mat:
                self.report({'INFO'}, f"Неиспользуемая нода: {node.name}, Тип: {node.type}")
                # Обработка групп
                if node.type == 'GROUP' and node.node_tree:
                    group_users = []
                    for mat in bpy.data.materials:
                        if mat.use_nodes and mat.node_tree:
                            for cur_node in mat.node_tree.nodes:
                                if cur_node.type == 'GROUP' and cur_node.node_tree == node.node_tree:
                                    group_users.append(mat.name)
                                    break 
                    self.report({'INFO'}, f"Нода-группа '{node.name}' используется в материалах: {', '.join(group_users) if group_users else 'Только здесь'}")

                node.location = (0, 0 - cur_height)

                min_x = min(min_x, node.location.x)
                max_x = max(max_x, node.location.x + node.width)
                min_y = min(min_y, node.location.y - node.height)
                max_y = max(max_y, node.location.y)
                
                node.parent = frame_node

                first_input = next((s for s in node.inputs), None)
                
                # Позиция аттрибутов
                if first_input:
                    attr_node = node_tree.nodes.new(type='ShaderNodeAttribute')
                    attr_node.label = "Attribute"
                    attr_node.location = (self.frame_x_pos - 500, self.frame_y_pos - cur_height)
                    node_tree.links.new(attr_node.outputs['Color'], first_input)
                
                cur_height += node.dimensions.y
                all_unused_nodes.append(node.name)
            
            # Позиция фрейма
            if unused_nodes_in_mat:
                frame_node.location = (self.frame_x_pos, self.frame_y_pos)
                frame_node.width = max_x - min_x + 200
                frame_node.height = max_y - min_y + 100
        
        if not all_unused_nodes:
            self.report({'INFO'}, "Неиспользуемые ноды материалов не найдены во всей сцене.")
            return {'FINISHED'}

        self.report({'INFO'}, f"Обработано {len(all_unused_nodes)} неиспользуемых нод и сгруппировано во Frame.")
        return {'FINISHED'}

class NODE_TOOLS_PT_unused_nodes_panel(bpy.types.Panel):
    bl_label = "Node Cleaner Tools"
    bl_idname = "NODE_PT_unused_nodes_panel"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Node Tools"

    def draw(self, context):
        layout = self.layout
        wm = context.window_manager
        
        box = layout.box()
        box.label(text="Frame Position Settings", icon='ORIENTATION_LOCAL')
        
        box.prop(wm, "node_cleaner_frame_x", text="Frame X Position")
        box.prop(wm, "node_cleaner_frame_y", text="Frame Y Position")
        
        op_apply = box.operator(UNUSED_NODE_OT_process_material_nodes.bl_idname, text="Найти и объединить неиспользованные ноды")
        op_apply.frame_x_pos = wm.node_cleaner_frame_x
        op_apply.frame_y_pos = wm.node_cleaner_frame_y

classes = (
    UNUSED_NODE_OT_process_material_nodes,
    NODE_TOOLS_PT_unused_nodes_panel,
)

def register():
    bpy.types.WindowManager.node_cleaner_frame_x = FloatProperty(
        name="Frame X Pos",
        default=1000.0,
        description="X-координата для расположения Frame'а с неиспользуемыми нодами"
    )
    bpy.types.WindowManager.node_cleaner_frame_y = FloatProperty(
        name="Frame Y Pos",
        default=100.0,
        description="Y-координата для расположения Frame'а с неиспользуемыми нодами"
    )

    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    del bpy.types.WindowManager.node_cleaner_frame_x
    del bpy.types.WindowManager.node_cleaner_frame_y

if __name__ == "__main__":
    register()