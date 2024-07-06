""" anytree_utils.py """

from anytree import Node, RenderTree, find


def add_indices(tree: RenderTree) -> None:
    """Add index property to tree nodes"""
    for index, row in enumerate(tree):
        row.node.index = index


def count_leaves(node: Node, acc: int = 0) -> int:
    """Count all leaf (childless) nodes under specified node"""
    if node.children:
        for child in node.children:
            acc += count_leaves(child)
    else:
        acc += 1
    return acc


def count_nodes(node: Node, acc: int = 0) -> int:
    """Count all nodes in tree under specified node"""
    if node.children:
        for child in node.children:
            acc += count_nodes(child)
    return acc + 1


def find_by_index(node: Node, index: int) -> Node | None:
    """Find node using self-defined index property"""
    return find(node, filter_=lambda n: n.index == index)


def get_descendants(node: Node, leaves: list[Node] = None) -> list[Node]:
    """Create list of node and all of its descendants (INCLUDES NODE ITSELF at index 0)"""
    if leaves is None:
        leaves = []
    
    leaves.append(node)
    
    if node.children:
        for child in node.children:
            leaves = get_descendants(child, leaves)
    
    return leaves


def get_leaves_only(node: Node, leaves: list[Node] = None) -> list[Node]:
    """Create list of only leaf (childless) nodes under specified node"""
    if leaves is None:
        leaves = []
    
    if node.children:
        for child in node.children:
            leaves = get_leaves_only(child, leaves)
    else:
        if node not in leaves:
            leaves.append(node)
    return leaves
