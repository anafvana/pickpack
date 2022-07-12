''' anytree_utils.py '''

from typing import Optional

from anytree import Node, RenderTree, find


# Add index property to tree nodes
def add_indices(tree:RenderTree):
    for index, row in enumerate(tree):
        row.node.index = index

# Count all leaf (childless) nodes under specified node
def count_leaves(node:Node, acc: int = 0) -> int:
    if node.children:
        for child in node.children:
            acc += count_leaves(child)
    else:
        acc += 1
    return acc

# Count all nodes in tree under specified node
def count_nodes(node:Node, acc: int = 0) -> int:
    if node.children:
        for child in node.children:
            acc += count_nodes(child)
    return acc + 1

# Find node using self-defined index property
def find_by_index(n: Node, index: int) -> Optional[Node]:
        return find(n, filter_= lambda n : n.index == index)

# Create list of node and all of its descendents (INCLUDES NODE ITSELF at list[0])
def get_descendants(node:Node, leaves: list[Node] = None) -> list[Node]:
    if leaves is None:
        leaves = []
    
    leaves.append(node)

    if node.children:
        for child in node.children:
            leaves = get_descendants(child, leaves)

    return leaves

# Create list of only leaf (childless) nodes under specified node
def get_leaves_only(node:Node, leaves: list[Node] = None) -> list[Node]:
    if leaves is None:
        leaves = []
    
    if node.children:
        for child in node.children:
            leaves = get_leaves_only(child, leaves)
    else:
        if node not in leaves:
            leaves.append(node)
    return leaves
