from haversine import haversine


def haversine_length(nodes, all_nodes):
    length = 0
    for j in range(0, len(nodes) - 1):
        length += haversine(all_nodes[nodes[j]], all_nodes[nodes[j + 1]])
    return length * 1000
