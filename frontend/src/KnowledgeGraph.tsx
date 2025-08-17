import { useEffect, useState } from "react";
import ForceGraph2D from "react-force-graph-2d";
import axios from "axios";

interface Node {
  id: string;
}
interface Edge {
  source: string;
  target: string;
  type: string;
}

export default function KnowledgeGraph() {
  const [graphData, setGraphData] = useState<{ nodes: Node[]; links: Edge[] }>({
    nodes: [],
    links: [],
  });

  useEffect(() => {
    const fetchGraph = async () => {
      const res = await axios.get("http://localhost:8000/knowledge_graph");
      setGraphData(res.data);
    };
    fetchGraph();
    const interval = setInterval(fetchGraph, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div style={{ width: "100%", height: "600px" }}>
      <ForceGraph2D
        graphData={graphData}
        nodeLabel="id"
        nodeAutoColorBy="id"
        linkDirectionalArrowLength={4}
        linkDirectionalArrowRelPos={1}
      />
    </div>
  );
}
