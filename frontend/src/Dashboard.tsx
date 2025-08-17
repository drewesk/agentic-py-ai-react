import TaskMonitor from "./TaskMonitor";
import MemoryMetrics from "./MemoryMetrics";

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
    </div>
  );
}
