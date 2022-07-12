from anytree import Node, RenderTree
from pickpack import pickpack

title = 'Select:'
children = [Node('foo.bar%s.baz'%x, index=x) for x in range(1, 71)]
root = Node("All", children=children)

options = RenderTree(root)
option, index = pickpack(options, title, indicator='=>', default_index=2)
print(option, index)
