import { useEffect, useState } from "react";
import axios from "axios";
import { PieChart, Pie, Cell, Legend } from "recharts";

export default function MemoryMetrics() {
  const [memoryCount, setMemoryCount] = useState(0);

  useEffect(() => {
    const interval = setInterval(async () => {
      const res = await axios.get("http://localhost:8000/memory_metrics");
      setMemoryCount(res.data.memory_count);
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  const data = [
    { name: "Stored Knowledge", value: memoryCount },
    { name: "Remaining Capacity", value: 1000 - memoryCount },
  ];

  const COLORS = ["#0088FE", "#FFBB28"];

  return (
    <PieChart width={300} height={300}>
      <Pie
        data={data}
        dataKey="value"
        nameKey="name"
        cx="50%"
        cy="50%"
        outerRadius={80}
        label
      >
        {data.map((entry, index) => (
          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
        ))}
      </Pie>
      <Legend />
    </PieChart>
  );
}
