from models.workflow import WorkflowState, WorkflowNode, WorkflowEdge
from models.graph import WorkflowGraphModel, XYFlowNode, XYFlowEdge, GraphNodeData, GraphNodePosition


class WorkflowGraphBuilder:
    """Builds and lays out XYFlow compatible graph structures from WorkflowState."""

    @staticmethod
    def build_xyflow_graph(state: WorkflowState) -> WorkflowGraphModel:
        xy_nodes: list[XYFlowNode] = []
        xy_edges: list[XYFlowEdge] = []

        # Simple hierarchical layout
        level_map: dict[str, int] = {}
        for node in state.nodes:
            if not node.depends_on:
                level_map[node.id] = 0
            else:
                max_dep_lvl = max([level_map.get(dep, 0) for dep in node.depends_on], default=0)
                level_map[node.id] = max_dep_lvl + 1

        level_counts: dict[int, int] = {}
        for node in state.nodes:
            lvl = level_map.get(node.id, 0)
            idx_in_lvl = level_counts.get(lvl, 0)
            level_counts[lvl] = idx_in_lvl + 1

            pos_x = node.position_x if node.position_x != 0.0 else (lvl * 280.0) + 50.0
            pos_y = node.position_y if node.position_y != 0.0 else (idx_in_lvl * 140.0) + 80.0

            artifact_id = node.artifact_refs[0] if node.artifact_refs else None

            xy_nodes.append(
                XYFlowNode(
                    id=node.id,
                    type="agentNode",
                    position=GraphNodePosition(x=pos_x, y=pos_y),
                    data=GraphNodeData(
                        label=node.display_name,
                        agent_id=node.agent_id,
                        display_name=node.display_name,
                        task_type=node.task_type,
                        status=node.status,
                        plan_version=node.plan_version,
                        artifact_id=artifact_id,
                        error_message=node.error_message,
                        hitl_required=node.hitl_required,
                        metadata={"invocation_count": node.invocation_count}
                    )
                )
            )

        for edge in state.edges:
            xy_edges.append(
                XYFlowEdge(
                    id=edge.id,
                    source=edge.source,
                    target=edge.target,
                    animated=True,
                    label=f"v{edge.plan_version}" if edge.plan_version > 1 else None
                )
            )

        return WorkflowGraphModel(nodes=xy_nodes, edges=xy_edges)
