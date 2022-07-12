from anytree import Node, RenderTree
from pickpack import pickpack

title = 'Please choose your favorite programming language: '
java = Node("Java")
js = Node("JavaScript")
py = Node("Python")
php = Node("PHP")
c = Node("C")
cpp = Node("C++")
go = Node("Go")
erl = Node("Erlang")
hs = Node("Haskell")
fun = Node("Functional", children=[erl, hs])
imp = Node("Imperative", children=[c, go])
oop = Node("Object-Oriented", children=[java, cpp])
mul = Node("Multiparadigm", children=[js, py, php])
root = Node("Select all", children=[fun, imp, oop, mul])

options = RenderTree(root)
option, index = pickpack(options, title, indicator='=>', default_index=2)
print(option, index)
