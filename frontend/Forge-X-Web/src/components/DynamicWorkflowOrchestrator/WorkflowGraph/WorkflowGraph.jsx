import React, { useMemo } from "react";
import { ReactFlow, Controls, Background, MiniMap, useNodesState, useEdgesState } from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { AgentNode } from "./AgentNode";

const nodeTypes = {
  agentNode: AgentNode,
};

export function WorkflowGraph({ graphData, onSelectNode }) {
  const nodes = useMemo(() => graphData?.nodes || [], [graphData]);
  const edges = useMemo(() => graphData?.edges || [], [graphData]);

  const handleNodeClick = (event, node) => {
    if (onSelectNode) {
      onSelectNode(node.id);
    }
  };

  return (
    <div
      className="glass-panel"
      style={{
        width: "100%",
        height: "520px",
        borderRadius: "16px",
        overflow: "hidden",
        position: "relative",
        marginBottom: "20px",
      }}
    >
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        onNodeClick={handleNodeClick}
        fitView
        attributionPosition="bottom-right"
      >
        <Background color="#334155" gap={20} size={1} />
        <Controls />
        <MiniMap
          nodeStrokeColor="#6366f1"
          nodeColor="#1e293b"
          maskColor="rgba(10, 13, 20, 0.7)"
          style={{
            background: "rgba(17, 24, 39, 0.8)",
            border: "1px solid var(--border-color)",
            borderRadius: "8px",
          }}
        />
      </ReactFlow>
    </div>
  );
}
