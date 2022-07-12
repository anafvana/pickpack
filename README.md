# pickpack

[![ci](https://github.com/anafvana/pickpack/actions/workflows/ci.yml/badge.svg)](https://github.com/anafvana/pickpack/actions/workflows/ci.yml)

**pickpack** is a small python library based on [wong2's pick](https://github.com/wong2/pick) which allows you to create a curses-based interactive selection tree in the terminal.

![Demo](https://github.com/anafvana/pick/raw/master/example/basic.gif)

It was made with installation processes in mind, so that a user can select a parent node and get all children elements included. Different configurations allow for different outputs.

## Installation

    $ pip install pickpack

## Options

- `options`: a RenderTree (anytree) or a list of options (if using list, `options_map_func` MUST be included)
- `title`: (optional) a title displayed above the options list
- `root_name`: (optional) name of root ("select all") node; defaults to root-node's value
- `multiselect`: (optional) if true, it is possible to select multiple values by hitting SPACE; defaults to `False`
- `singleselect_output_include_children`: (optional) if true, output in singleselect will include all children of the selected node, as well as the node itself; defaults to `False`
- `output_leaves_only`: (optional) if true, only leaf (childless) nodes will be returned; **for singleselect mode, `singleselect_output_include_children` MUST be True**; defaults to `False`
- `output_format`: (optional) allows for customising output format. 'nodeindex' = `[(Node('name'), index)]`; 'nameindex' = `[('name', index)]`; 'nodeonly' = `[Node('name')]`; 'nameonly' = `['name']`; default is 'nodeindex'
- `indicator`: (optional) custom the selection indicator
- `indicator_parentheses`: (optional) include/remove parentheses around selection indicator; defaults to `True`
- `default_index`: (optional) defines at which line the indicator will be placed when the program is started; default is `0` (first line)
- `options_map_func`: (optional for multiselect) a mapping function to pass each option through before displaying. Must return `Node`

## Usage

**pickpack** can be used by creating a tree and passing it into pickpack:

    from anytree import Node, RenderTree
    from pickpack import pickpack

    title = 'Please choose one: '

    c1 = Node('child1')
    c2 = Node('child2')
    p1 = Node('parent', children=[c1,c2])

    options = RenderTree(p1)
    option, index = pickpack(options, title)
    print(option, index)

**outputs**:

    Node('/parent/child1', index=1)
    1

**pickpack** multiselect example returning node-name and index:

    from anytree import Node, RenderTree
    from pickpack import pickpack

    title = 'Please choose one: '

    c1 = Node('child1')
    c2 = Node('child2')
    p1 = Node('parent', children=[c1,c2])

    options = RenderTree(p1)
    option, index = pickpack(options, title, multiselect=True, min_selection_count=1, output_format='nameindex')
    print(option, index)

**outputs**::

    [('child1', 1), ('child2', 2)]

### Register custom handlers

To register custom handlers for specific keyboard keypresses, you can use the `register_custom_handler` property:

    from anytree import Node, RenderTree
    from pickpack import PickPacker

    title = 'Please choose one: '
    c1 = Node('child1')
    c2 = Node('child2')
    p1 = Node('parent', children=[c1,c2])
    options = RenderTree(p1)

    picker = PickPacker(options, title)
    def go_back(picker):
         return None, -1
    picker.register_custom_handler(ord('h'),  go_back)
    option, index = picker.start()

- the custom handler will be called with the `picker` instance as its parameter.
- the custom handler should either return a two-element `tuple` or `None`.
- if `None` is returned, the picker would continue to run; otherwise the picker will stop and return the tuple.

### Options Map Function

If your options are not a `RenderTree`, you can pass in a mapping function through which each option will be run. [^1]

[^1]: It MAY be also possible to use the `options_map_function` to customise how each option is displayed (as was the case with the original `options_map_function` from [wong2's pick](https://github.com/wong2/pick)). However, this behaviour has not been thoroughly tested. Feel free to submit an issue if you try it out.

The function must take in elements of the type you passed into the options (`Node` if you passed a `RenderTree`, `T` if you passed a `list[T]`) and return a `Node`.

You may also store any additional information as a custom property within the node.

**pickpack** options map function example:

    from anytree import Node, RenderTree
    from pickpack import pickpack

    title = 'Please choose an option: '
    options = [
        {'label': 'option1', 'abbreviation': 'op1'},
        {'label': 'option2', 'abbreviation': 'op2'},
        {'label': 'option3', 'abbreviation': 'op3'}
    ]

    def get_node(option):
        return Node(option.get('label'), abbreviation=option.get('abbreviation'))

    picker = PickPacker(options, title, indicator='*', options_map_func=get_node, output_format='nameindex')

**displays**:

    Please choose an option:

    (*) Select all
    ( )    └── option1
    ( )    └── option2
    ( )    └── option3

**outputs**:

    >>> ({ 'label': 'option1' }, 0)

#### Map function for nested lists

**pickpack** options map function example for lists with **nesting**:

    from anytree import Node, RenderTree
    from pickpack import pickpack

    title = 'Please choose an option: '
    options = [
        {'label': 'option1', 'abbreviation': 'op1', 'children':
            [{'label': 'option1.1', 'abbreviation': 'op1.1',}]
        },
        {'label': 'option2', 'abbreviation': 'op2'},
        {'label': 'option3', 'abbreviation': 'op3'}
    ]

    def get_node(option):
        children = option.get('children')
        if children is not None:
            children_list: list[Node] = []
            for child in children:
                children_list.append(get_nodes(child))
            return Node(option.get('label'), children=children_list, abbreviation=option.get('abbreviation'))
        else:
            return Node(option.get('label'), children=None, abbreviation=option.get('abbreviation'))

    picker = PickPacker(options, title, indicator='*', options_map_func=get_node, output_format='nameindex')

**displays**:

    Please choose an option:

    (*) Select all
    ( )    └── option1
    ( )           └── option1.1
    ( )    └── option2
    ( )    └── option3
