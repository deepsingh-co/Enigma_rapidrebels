import React, { useState } from "react";
import { Share2, Info, Building, Factory, Sparkles, Layers } from "lucide-react";

export default function SymbiosisNetworkGraph({ data }) {
  const [selectedNode, setSelectedNode] = useState(null);

  if (!data || !data.nodes || data.nodes.length === 0) {
    return (
      <div className="bg-secondary/40 border border-gray-800 rounded-xl p-8 text-center text-textmuted">
        No graph data available. Run analysis to render industrial symbiosis network.
      </div>
    );
  }

  const { nodes, links } = data;

  // Layout positions in 4 columns:
  // Col 0: Producer
  // Col 1: Waste Stream
  // Col 2: Transformed Resources
  // Col 3: Discovered Partner Industries
  const producerNodes = nodes.filter((n) => n.type === "producer");
  const wasteNodes = nodes.filter((n) => n.type === "waste");
  const resourceNodes = nodes.filter((n) => n.type === "resource");
  const partnerNodes = nodes.filter((n) => n.type === "partner");

  const width = 860;
  const height = 460;

  // Calculate coordinates
  const nodeCoords = {};

  // Producer (Col 0)
  producerNodes.forEach((node, idx) => {
    const y = height / 2 + (idx - (producerNodes.length - 1) / 2) * 80;
    nodeCoords[node.id] = { x: 90, y, ...node };
  });

  // Waste (Col 1)
  wasteNodes.forEach((node, idx) => {
    const y = height / 2 + (idx - (wasteNodes.length - 1) / 2) * 90;
    nodeCoords[node.id] = { x: 280, y, ...node };
  });

  // Resources (Col 2)
  resourceNodes.forEach((node, idx) => {
    const spacing = Math.min(75, (height - 80) / Math.max(1, resourceNodes.length));
    const y = 60 + idx * spacing + (height - 80 - (resourceNodes.length - 1) * spacing) / 2;
    nodeCoords[node.id] = { x: 500, y, ...node };
  });

  // Partners (Col 3)
  partnerNodes.forEach((node, idx) => {
    const spacing = Math.min(85, (height - 80) / Math.max(1, partnerNodes.length));
    const y = 60 + idx * spacing + (height - 80 - (partnerNodes.length - 1) * spacing) / 2;
    nodeCoords[node.id] = { x: 730, y, ...node };
  });

  const getNodeColor = (type) => {
    switch (type) {
      case "producer":
        return "#3B82F6"; // Blue
      case "waste":
        return "#F59E0B"; // Amber
      case "resource":
        return "#10B981"; // Emerald
      case "partner":
        return "#A855F7"; // Purple
      default:
        return "#6B7280";
    }
  };

  return (
    <div className="bg-secondary/60 border border-gray-800 rounded-2xl p-5 relative overflow-hidden backdrop-blur-sm">
      <div className="flex flex-wrap items-center justify-between gap-4 mb-4 pb-4 border-b border-gray-800">
        <div>
          <div className="flex items-center gap-2">
            <Share2 className="w-5 h-5 text-accent" />
            <h3 className="text-lg font-bold text-white">W2RKG Knowledge Graph Pathways</h3>
          </div>
          <p className="text-xs text-textmuted mt-0.5">
            Interactive multi-hop symbiosis network: Producer → Waste → Process → Resource → Partner
          </p>
        </div>

        {/* Legend */}
        <div className="flex flex-wrap items-center gap-3 text-xs">
          <span className="flex items-center gap-1.5 text-blue-400">
            <span className="w-2.5 h-2.5 rounded-full bg-blue-500"></span> Producer
          </span>
          <span className="flex items-center gap-1.5 text-amber-400">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500"></span> Waste Stream
          </span>
          <span className="flex items-center gap-1.5 text-emerald-400">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span> Transformed Resource
          </span>
          <span className="flex items-center gap-1.5 text-purple-400">
            <span className="w-2.5 h-2.5 rounded-full bg-purple-500"></span> Discovered Partner
          </span>
        </div>
      </div>

      {/* SVG Canvas */}
      <div className="w-full overflow-x-auto">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          className="w-full h-auto min-w-[700px] select-none"
          style={{ maxHeight: "480px" }}
        >
          <defs>
            <linearGradient id="grad-producer-waste" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#3B82F6" stopOpacity="0.8" />
              <stop offset="100%" stopColor="#F59E0B" stopOpacity="0.8" />
            </linearGradient>
            <linearGradient id="grad-waste-res" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#F59E0B" stopOpacity="0.8" />
              <stop offset="100%" stopColor="#10B981" stopOpacity="0.8" />
            </linearGradient>
            <linearGradient id="grad-res-partner" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#10B981" stopOpacity="0.8" />
              <stop offset="100%" stopColor="#A855F7" stopOpacity="0.8" />
            </linearGradient>
            <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="3" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
          </defs>

          {/* Render Links */}
          {links.map((link, idx) => {
            const src = nodeCoords[link.source];
            const tgt = nodeCoords[link.target];
            if (!src || !tgt) return null;

            // Curved cubic bezier
            const dx = tgt.x - src.x;
            const cpx1 = src.x + dx * 0.45;
            const cpx2 = src.x + dx * 0.55;
            const pathD = `M ${src.x} ${src.y} C ${cpx1} ${src.y}, ${cpx2} ${tgt.y}, ${tgt.x} ${tgt.y}`;

            let strokeColor = "url(#grad-waste-res)";
            if (src.type === "producer" || tgt.type === "producer") strokeColor = "url(#grad-producer-waste)";
            if (tgt.type === "partner" || src.type === "partner") strokeColor = "url(#grad-res-partner)";

            const isHighlighted =
              selectedNode && (selectedNode.id === link.source || selectedNode.id === link.target);

            return (
              <g key={idx} className="transition-opacity duration-300">
                <path
                  d={pathD}
                  fill="none"
                  stroke={strokeColor}
                  strokeWidth={isHighlighted ? 3.5 : 2}
                  strokeDasharray={link.process ? "4,4" : "none"}
                  opacity={selectedNode ? (isHighlighted ? 1 : 0.2) : 0.65}
                />
              </g>
            );
          })}

          {/* Render Nodes */}
          {Object.values(nodeCoords).map((node) => {
            const isSelected = selectedNode && selectedNode.id === node.id;
            const color = getNodeColor(node.type);

            return (
              <g
                key={node.id}
                transform={`translate(${node.x}, ${node.y})`}
                onClick={() => setSelectedNode(isSelected ? null : node)}
                className="cursor-pointer group"
              >
                {/* Glow ring */}
                {isSelected && (
                  <circle r="26" fill="none" stroke={color} strokeWidth="3" opacity="0.6" filter="url(#glow)" />
                )}

                {/* Main Circle */}
                <circle
                  r={node.type === "waste" ? 22 : 18}
                  fill="#1E1E1E"
                  stroke={color}
                  strokeWidth={isSelected ? 3 : 2}
                  className="transition-all duration-200 group-hover:scale-110"
                />

                {/* Inner Icon / Letter */}
                <text
                  textAnchor="middle"
                  dy="4"
                  fill="#FFFFFF"
                  fontSize={node.type === "waste" ? "11" : "10"}
                  fontWeight="bold"
                  className="pointer-events-none font-mono"
                >
                  {node.type === "producer" ? "P" : node.type === "waste" ? "W" : node.type === "resource" ? "R" : "I"}
                </text>

                {/* Node Label Text */}
                <text
                  textAnchor={node.x > width / 2 ? "start" : "end"}
                  dx={node.x > width / 2 ? 26 : -26}
                  dy="4"
                  fill="#E5E7EB"
                  fontSize="11"
                  fontWeight="500"
                  className="pointer-events-none drop-shadow-md"
                >
                  {node.name.length > 24 ? node.name.slice(0, 22) + "..." : node.name}
                </text>

                {/* Subtitle / category */}
                <text
                  textAnchor={node.x > width / 2 ? "start" : "end"}
                  dx={node.x > width / 2 ? 26 : -26}
                  dy="16"
                  fill={color}
                  fontSize="9"
                  className="pointer-events-none opacity-85 font-mono uppercase"
                >
                  {node.matchScore ? `${node.matchScore}% Match` : node.category}
                </text>
              </g>
            );
          })}
        </svg>
      </div>

      {/* Selected Node Inspector Drawer */}
      {selectedNode && (
        <div className="mt-4 p-4 rounded-xl bg-primary/90 border border-accent/40 animate-fade-in flex flex-col md:flex-row justify-between items-start md:items-center gap-3">
          <div className="flex items-center gap-3">
            <div
              className="w-10 h-10 rounded-lg flex items-center justify-center font-bold text-white"
              style={{ backgroundColor: getNodeColor(selectedNode.type) }}
            >
              {selectedNode.type === "producer" ? "P" : selectedNode.type === "waste" ? "W" : selectedNode.type === "resource" ? "R" : "I"}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h4 className="font-semibold text-white text-sm">{selectedNode.name}</h4>
                <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-gray-800 text-accent">
                  {selectedNode.category}
                </span>
              </div>
              <p className="text-xs text-textmuted mt-0.5">{selectedNode.details || "Active node in industrial symbiosis path."}</p>
            </div>
          </div>
          <button
            onClick={() => setSelectedNode(null)}
            className="text-xs text-textmuted hover:text-white px-3 py-1 rounded bg-secondary border border-gray-700"
          >
            Clear Selection
          </button>
        </div>
      )}
    </div>
  );
}
