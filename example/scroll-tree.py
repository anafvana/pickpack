from anytree import Node, RenderTree
from tree_pick import tree_pick

title = 'Select:'
children = [Node('foo.bar%s.baz'%x, index=x) for x in range(1, 71)]
root = Node("All", children=children)

options = RenderTree(root)
option, index = tree_pick(options, title, indicator='=>', default_index=2)
print(option, index)
