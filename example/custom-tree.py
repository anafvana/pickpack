import curses
from tree_pick import TreePicker
from anytree import Node, RenderTree

def go_back(picker):
    return (None, -1)

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

picker = TreePicker(options, title)
picker.register_custom_handler(curses.KEY_LEFT, go_back)
option, index = picker.start()
print(option, index)
