from collections import defaultdict

vector_db = {"documents": []}
knowledge_graph = defaultdict(list)
node_metadata = {}

def add_to_memory(text, metadata=None):
    vector_db["documents"].append({"text": text, "metadata": metadata})

def retrieve_from_memory(query, k=5):
    # simplistic: return last k docs
    return [doc["text"] for doc in vector_db["documents"][-k:]]

def add_node(node_id: str, node_type="task", label=None):
    node_metadata[node_id] = {"type": node_type, "label": label or node_id}

def add_relationship(source_id: str, target_id: str, relation_type="related"):
    knowledge_graph[source_id].append({"target": target_id, "type": relation_type})
    if source_id not in node_metadata:
        add_node(source_id)
    if target_id not in node_metadata:
        add_node(target_id)

def get_knowledge_graph():
    nodes = [{"id": k, "type": node_metadata[k]["type"], "label": node_metadata[k]["label"]} for k in knowledge_graph.keys()]
    edges = []
    for src, targets in knowledge_graph.items():
        for t in targets:
            edges.append({"source": src, "target": t["target"], "type": t["type"]})
    return {"nodes": nodes, "links": edges}