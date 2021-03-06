import pytest
from anytree import Node, RenderTree
from pickpack import PickPacker


def test_move_up_down():
    title = "Please choose an option: "
    c1 = Node("child1")
    c2 = Node("child2")
    p1 = Node("parent", children=[c1,c2])
    options = RenderTree(p1)
    picker = PickPacker(options, title, output_format="nameindex")
    picker.move_up()
    assert picker.get_selected() == ("child2", 2)
    picker.move_down()
    picker.move_down()
    assert picker.get_selected() == ("child1", 1)

def test_default_index():
    title = "Please choose an option: "
    c1 = Node("child1")
    c2 = Node("child2")
    p1 = Node("parent", children=[c1,c2])
    options = RenderTree(p1)
    picker = PickPacker(options, title, output_format="nameindex", default_index=1)
    assert picker.get_selected() == ("child1", 1)

def test_get_lines():
    title = "Please choose an option: "
    c1 = Node("child1")
    c2 = Node("child2")
    p1 = Node("parent", children=[c1,c2])
    options = RenderTree(p1)    
    picker = PickPacker(options, title, indicator="*", indicator_parentheses=False)
    lines, current_line = picker.get_lines()
    assert lines == [title, "", "* parent", "     └── child1", "     └── child2"]
    assert current_line == 3

def test_parenthesis():
    title = "Please choose an option: "
    c1 = Node("child1")
    c2 = Node("child2")
    p1 = Node("parent", children=[c1,c2])
    options = RenderTree(p1)    
    picker = PickPacker(options, title, indicator="*")
    lines, current_line = picker.get_lines()
    assert lines == [title, "", "(*) parent", "( )    └── child1", "( )    └── child2"]
    assert current_line == 3

def test_no_title():
    title = "Please choose an option: "
    c1 = Node("child1")
    c2 = Node("child2")
    p1 = Node("parent", children=[c1,c2])
    options = RenderTree(p1)  
    picker = PickPacker(options)
    lines, current_line = picker.get_lines()
    assert current_line == 1

def test_multi_select():
    title = "Please choose one or more options: "
    c1 = Node("child1")
    c2 = Node("child2")
    p1 = Node("parent", children=[c1,c2])
    options = RenderTree(p1)  
    picker = PickPacker(options, title, multiselect=True, min_selection_count=1, output_format="nameindex")
    assert picker.get_selected() == []
    picker.mark_index()
    assert picker.get_selected() == [("parent", 0), ("child1", 1), ("child2", 2)]
    picker.move_down()
    picker.mark_index()
    assert picker.get_selected() == [("child2", 2)]

def test_options_map_func():
    title = "Please choose an option: "
    options = [{"label": "option1"}, {"label": "option2"}, {"label": "option3"}]

    def get_node(option):
        return Node(option.get("label"))

    picker = PickPacker(options, title, indicator="*", options_map_func=get_node, output_format="nameindex")
    lines, current_line = picker.get_lines()
    assert lines == [title, "", "(*) Select all", "( )    └── option1", "( )    └── option2", "( )    └── option3"]
    assert picker.get_selected() == ("Select all", 0)

def test_list_no_func():
    title = "Please choose an option: "
    options = [{"label": "option1"}, {"label": "option2"}, {"label": "option3"}]

    with pytest.raises(Exception): picker = PickPacker(options, title, indicator="*")
    with pytest.raises(TypeError): picker = PickPacker(options, title, indicator="*", options_map_func="hello")

def test_output_format():
    title = "Please choose one or more options: "
    c1 = Node("child1")
    c2 = Node("child2")
    p1 = Node("parent", children=[c1,c2])
    options = RenderTree(p1)  

    # Default (nodeindex)
    picker = PickPacker(options, title, multiselect=True, min_selection_count=1)
    assert picker.get_selected() == []
    picker.move_down()
    picker.mark_index()
    assert picker.get_selected() == [(c1, 1)]

    # nodeindex
    picker = PickPacker(options, title, multiselect=True, min_selection_count=1, output_format="nodeindex")
    assert picker.get_selected() == []
    picker.move_down()
    picker.mark_index()
    assert picker.get_selected() == [(c1, 1)]

    # nameindex
    picker = PickPacker(options, title, multiselect=True, min_selection_count=1, output_format="nameindex")
    assert picker.get_selected() == []
    picker.move_down()
    picker.mark_index()
    assert picker.get_selected() == [("child1", 1)]

    # nodeonly
    picker = PickPacker(options, title, multiselect=True, min_selection_count=1, output_format="nodeonly")
    assert picker.get_selected() == []
    picker.move_down()
    picker.mark_index()
    assert picker.get_selected() == [c1]

    # nameonly
    picker = PickPacker(options, title, multiselect=True, min_selection_count=1, output_format="nameonly")
    assert picker.get_selected() == []
    picker.move_down()
    picker.mark_index()
    assert picker.get_selected() == ["child1"]

    with pytest.raises(ValueError):
        picker = PickPacker(options, title, multiselect=True, min_selection_count=1, output_format="invalid")

    with pytest.raises(TypeError):
        picker = PickPacker(options, title, multiselect=True, min_selection_count=1, output_format=1)

def test_root_name():
    title = "Please choose an option: "
    options = [{"label": "option1"}, {"label": "option2"}, {"label": "option3"}]

    def get_node(option):
        return Node(option.get("label"))

    picker = PickPacker(options, title, indicator="*", options_map_func=get_node, output_format="nameindex", root_name="EVERYTHING")
    lines, current_line = picker.get_lines()
    assert lines == [title, "", "(*) EVERYTHING", "( )    └── option1", "( )    └── option2", "( )    └── option3"]
    assert picker.get_selected() == ("EVERYTHING", 0)

def test_leaves_only():
    title = "Please choose an option: "
    options = [{"label": "option1"}, {"label": "option2"}, {"label": "option3"}]

    def get_node(option):
        return Node(option.get("label"))

    # Multiselect
    picker = PickPacker(options, title, multiselect=True, options_map_func=get_node, output_format="nameindex", output_leaves_only=True)
    assert picker.get_selected() == []
    picker.mark_index()
    assert picker.get_selected() == [("option1", 1), ("option2", 2), ("option3", 3)]

    # Singleselect
    with pytest.raises(ValueError):
        picker = PickPacker(options, title, options_map_func=get_node, output_format="nameindex", output_leaves_only=True)
    
    picker = PickPacker(options, title, options_map_func=get_node, output_format="nameindex", output_leaves_only=True, singleselect_output_include_children=True)
    assert picker.get_selected() == [("option1", 1), ("option2", 2), ("option3", 3)]

def test_include_children():
    title = "Please choose an option: "
    options = [{"label": "option1"}, {"label": "option2"}, {"label": "option3"}]

    def get_node(option):
        return Node(option.get("label"))

    picker = PickPacker(options, title, options_map_func=get_node, output_format="nameindex",  singleselect_output_include_children=True)
    assert picker.get_selected() == [("Select all", 0), ("option1", 1), ("option2", 2), ("option3", 3)]

if __name__ == "__main__":
    test_move_up_down()
    test_default_index()
    test_get_lines()
    test_parenthesis()
    test_no_title()
    test_multi_select()
    test_options_map_func()
    test_list_no_func()
    test_output_format()
    test_root_name()
    test_leaves_only()
    test_include_children()
    print("Tests concluded")
