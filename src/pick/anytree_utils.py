from anytree import Node, RenderTree, find
from typing import Optional

def add_indices(tree:RenderTree):
    for index, row in enumerate(tree):
        row.node.index = index

def count_leaves(node:Node, acc: int = 0) -> int:
    if node.children:
        for child in node.children:
            acc += count_leaves(child)
    else:
        acc += 1
    return acc

def count_nodes(node:Node, acc: int = 0) -> int:
    if node.children:
        for child in node.children:
            acc += count_nodes(child)
    return acc + 1

def find_by_index(n: Node, index: int) -> Optional[Node]:
        return find(n, filter_= lambda n : n.index == index)

