import { useEffect, useState } from "react";

interface Task {
  id: number;
  description: string;
  status: string;
  priority?: number;
}

export default function TaskMonitor() {
  const [tasks, setTasks] = useState<Task[]>([]);

  useEffect(() => {
    const eventSource = new EventSource("http://localhost:8000/tasks_stream");
    eventSource.onmessage = (e) => {
      const data: Task[] = JSON.parse(e.data);
      setTasks(data);
    };
    return () => eventSource.close();
  }, []);

  return (
    <div>
      <h2>Pending Tasks</h2>
      <ul>
        {tasks.map((task) => (
          <li key={task.id}>
            {task.description} - <strong>{task.status}</strong> (Priority:{" "}
            {task.priority})
          </li>
        ))}
      </ul>
    </div>
  );
}
