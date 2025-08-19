import TaskMonitor from "./TaskMonitor.tsx";
import MemoryMetrics from "./MemoryMetrics.tsx";
import KnowledgeGraph from "./KnowledgeGraph.tsx";

export default function Dashboard() {
  return (
    <div
      style={{
        display: "flex",
        justifyContent: "space-around",
        padding: "2rem",
      }}
    >
      <TaskMonitor />
      <MemoryMetrics />
      <KnowledgeGraph />
    </div>
  );
}