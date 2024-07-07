""" pickpack.py """

from __future__ import annotations

import curses
import enum
from _curses import window
from dataclasses import dataclass, field
from typing import Any, Callable, TypeAlias, TypeVar

from anytree import Node, RenderTree

from pickpack.anytree_utils import add_indices, count_nodes, find_by_index, get_descendants, get_leaves_only

__all__ = ['PickPacker', 'pickpack']


KEYS_ENTER = (curses.KEY_ENTER, ord('\n'), ord('\r'))
KEYS_UP = (curses.KEY_UP, ord('k'))
KEYS_DOWN = (curses.KEY_DOWN, ord('j'))
KEYS_SELECT = (curses.KEY_RIGHT, ord(' '))

NodeWithIndex: TypeAlias = tuple[str | Node, int] | list[tuple[str | Node, int]]
NodeNameOnly: TypeAlias = str | Node | list[Node | str]
AnyNode: TypeAlias = NodeNameOnly | NodeWithIndex

_T = TypeVar("_T")


class OutputMode(enum.IntEnum):
    """Changes how the selected entry is returned"""
    nodeindex = 0
    """Returns the selected node and it's index: [(Node('name'), index)]"""
    nameindex = 1
    """Returns the name of the selected node and it's index: [('name', index)]"""
    nodeonly = 2
    """Returns only the selected node: [Node('name')]"""
    nameonly = 3
    """Returns only the name of the selected node: ['name']"""


@dataclass
class PickPacker:
    """The :class:`PickPacker <PickPacker>` object

    :param options: a RenderTree (anytree) or a list of options to choose from
    :param title: (optional) a title above options list
    :param root_name: (optional) name of root ("select all") node; defaults to root node's value
    :param multiselect: (optional) if true its possible to select multiple values by hitting SPACE; defaults to False
    :param singleselect_output_include_children: (optional) if true, output will include all children of the selected node, as well as the node itself; defaults to False
    :param output_leaves_only: (optional) if true, only leaf nodes will be returned; for singleselect mode, singleselect_output_include_children MUST be True; defaults to False
    :param output_format: (optional) allows for customising output format.
    :param indicator: (optional) custom the selection indicator
    :param indicator_parentheses: (optional) include/remove parentheses around selection indicator; defaults to True
    :param indicator_parentheses_design: (optional) the design of the parentheses for the indicator; defaults to '("(", ")")'
    :param default_index: (optional) set this if the default selected option is not the first one
    :param options_map_func: (optional) a mapping function to pass each option through before displaying
    """

    # list type is only for users, internally options is always RenderTree (converted in post_init)
    options: RenderTree | list[_T]
    title: str | None = None
    root_name: str | None = None
    indicator: str = "*"
    indicator_parentheses: bool = True
    indicator_parentheses_design: tuple[str, str] = ("(", ")")
    default_index: int = 0
    multiselect: bool = False
    min_selection_count: int = 0
    singleselect_output_include_children: bool = False
    output_leaves_only: bool = False
    # str type should only be for users
    output_format: OutputMode | str = OutputMode.nodeindex
    # the default is not perfect, but good enough for most cases
    options_map_func: Callable[[_T], Node] | None = lambda o: Node(str(o))
    foreground: int = curses.COLOR_WHITE
    background: int = curses.COLOR_GREEN
    # internal fields
    all_selected: list[int] = field(init=False, default_factory=list)
    custom_handlers: dict[int, Callable[[PickPacker], Any]] = field(init=False, default_factory=dict)
    index: int = field(init=False, default=0)
    scroll_top: int = field(init=False, default=0)

    def __post_init__(self):
        # Check for correct number of elements
        if (isinstance(self.options, RenderTree) and count_nodes(self.options.node) == 0) or (isinstance(self.options, list) and len(self.options) == 0):
            raise ValueError('options should not be an empty list')

        if not self.multiselect and not self.singleselect_output_include_children and self.output_leaves_only:
            raise ValueError('To output only leaves on singleselect mode, singleselect_output_include_children MUST be True')

        optnr = (lambda: count_nodes(self.options.node) if isinstance(self.options, RenderTree) else len(self.options))()

        if (isinstance(self.options, list) and (optnr == 1 and self.default_index >= 1) or (self.default_index > optnr)) or (self.default_index >= optnr and isinstance(self.options, RenderTree)):
            raise ValueError('default_index should be less than the length of options')

        if self.multiselect and self.min_selection_count > optnr:
            raise ValueError('min_selection_count is bigger than the available options, you will not be able to make any selection')

        # Check for correct options_map_func and build tree
        if self.options_map_func is None and isinstance(self.options, list):
            raise ValueError('options_map_func that maps list items to Node objects is required when passing options of type list')
        elif self.options_map_func is not None and not callable(self.options_map_func):
            raise TypeError('options_map_func must be a callable function')
        elif self.options_map_func is not None and callable(self.options_map_func) and isinstance(self.options, list):
            opts = [self.options_map_func(opt) for opt in self.options]
            if len(opts) > 1:
                root = Node("Select all", children=opts)
            else:
                root = opts[0]
            self.options = RenderTree(root)
        add_indices(self.options)
        
        # Rename root node
        if isinstance(self.options, RenderTree) and self.root_name is not None:
            self.options.node.name = self.root_name

        if isinstance(self.output_format, str):
            try:
                self.output_format = OutputMode[self.output_format]
            except KeyError:
                raise ValueError('Invalid output_format property. If it is a str, it must be either "nodeindex", "nameindex", "nodeonly", or "nameonly"')
        if not isinstance(self.output_format, OutputMode):
            raise TypeError('Invalid output_format property type. Must be OutputMode or str (nodeindex, nameindex, nodeonly, or nameonly)')
        
        if not isinstance(self.indicator_parentheses_design, tuple) or len(self.indicator_parentheses_design) != 2 or not isinstance(self.indicator_parentheses_design[0], str) or not isinstance(self.indicator_parentheses_design[1], str):
            raise TypeError('Invalid indicator_parentheses_design type: must be tuple[str, str]')

        self.index = self.default_index

    def register_custom_handler(self, key: int, func: Callable[[PickPacker], Any]) -> None:
        self.custom_handlers[key] = func
    
    def move_up(self) -> None:
        self.index -= 1
        if self.index < 0:
            self.index = count_nodes(self.options.node) - 1

    def move_down(self) -> None:
        self.index += 1
        if self.index >= count_nodes(self.options.node):
            self.index = 0

    def check_children(self, node: Node) -> None:
        for child in node.children:
            if child.index not in self.all_selected:
                self.all_selected.append(child.index)
            if child.children:
                self.check_children(child)
    
    def check_ancestors(self, node: Node) -> None:
        while node is not None and node.parent:
            all_checked = 1
            for child in node.parent.children:
                all_checked = all_checked * (child.index in self.all_selected)
            if all_checked > 0:
                self.all_selected.append(node.parent.index)
                node = node.parent
            else:
                node = None

    def uncheck_children(self, node: Node) -> None:
        for child in node.children:
            if child.index in self.all_selected:
                self.all_selected.remove(child.index)
            if child.children:
                self.uncheck_children(child)

    def uncheck_ancestors(self, node: Node) -> None:
        while node is not None and node.parent:
            try:
                self.all_selected.remove(node.parent.index)
                node = node.parent
            except ValueError:
                node = None

    def add_relatives_index(self) -> None:
        node = find_by_index(self.options.node, self.index)
        self.check_children(node)
        self.check_ancestors(node)

    def remove_relatives_index(self) -> None:
        node = find_by_index(self.options.node, self.index)
        self.uncheck_children(node)
        self.uncheck_ancestors(node)

    def mark_index(self) -> None:
        if self.multiselect:
            if self.index in self.all_selected:
                self.all_selected.remove(self.index)
                self.remove_relatives_index()
            else:
                self.all_selected.append(self.index)
                self.add_relatives_index()

    def get_selected_noindex(self) -> NodeNameOnly:
        nameonly = self.output_format == OutputMode.nameonly
        if self.multiselect:
            return_tuples: list[Node] = []
            if self.output_leaves_only:
                for selected in self.all_selected:
                    node = find_by_index(self.options.node, selected)
                    return_tuples.extend([leaf for leaf in get_leaves_only(node) if leaf not in return_tuples])
            else:
                for selected in self.all_selected:
                    if nameonly:
                        return_tuples.append(find_by_index(self.options.node, selected).name)
                    else:
                        return_tuples.append(find_by_index(self.options.node, selected))
            return return_tuples
        else:
            node = find_by_index(self.options.node, self.index)
            if self.output_leaves_only:
                if nameonly:
                    return [leaf.name for leaf in get_leaves_only(node)]
                else:
                    return get_leaves_only(node)
            else:
                if self.singleselect_output_include_children:
                    descendants = get_descendants(node)
                    if nameonly:
                        return [node.name for node in descendants]
                    else:
                        return descendants
                else:
                    if nameonly:
                        return node.name
                    else:
                        return node
    
    def get_selected_withindex(self) -> NodeWithIndex:
        """return the current selected option as a tuple: (option, index)
           or as a list of tuples (in case multiselect==True)
        """
        nameonly = bool(self.output_format)

        if self.multiselect:
            return_tuples: list[tuple[str | Node, int]] = []    
            if self.output_leaves_only:
                for selected in self.all_selected:
                    node = find_by_index(self.options.node, selected)
                    if nameonly:
                        return_tuples.extend([(leaf.name, leaf.index) for leaf in get_leaves_only(node) if (leaf.name, leaf.index) not in return_tuples])
                    else:
                        return_tuples.extend([(leaf, leaf.index) for leaf in get_leaves_only(node) if (leaf, leaf.index) not in return_tuples])

            else:
                if nameonly:
                    for selected in self.all_selected:
                        return_tuples.append((find_by_index(self.options.node, selected).name, selected))
                else:
                    for selected in self.all_selected:
                        return_tuples.append((find_by_index(self.options.node, selected), selected))
            return return_tuples
        else:
            node = find_by_index(self.options.node, self.index)
            if self.singleselect_output_include_children:
                if self.output_leaves_only:
                    if nameonly:
                        return [(leaf.name, leaf.index) for leaf in get_leaves_only(node)]
                    else:
                        return [(leaf, leaf.index) for leaf in get_leaves_only(node)]
                else:
                    descendants = get_descendants(node)
                    if nameonly:
                        return [(node.name, node.index) for node in descendants]
                    else:
                        return [(node, node.index) for node in descendants]
            else:
                if nameonly:
                    return node.name, self.index
                else:
                    return node, self.index

    def get_selected(self) -> AnyNode:
        """return the current selected option as a tuple: (option, index)
           or as a list of tuples (in case multiselect is True)
        """
        if self.output_format == OutputMode.nodeindex or self.output_format == OutputMode.nameindex:
            return self.get_selected_withindex()
        elif self.output_format == OutputMode.nameonly or self.output_format == OutputMode.nodeonly:
            return self.get_selected_noindex()

    def get_title_lines(self) -> list[str]:
        if self.title:
            return self.title.split('\n') + ['']
        return []

    def get_option_lines(self) -> list[str | tuple[str, int]]:
        lines: list[str | tuple[str, int]] = []
        for index, option in enumerate(self.options):
            prefix = self.indicator_parentheses * self.indicator_parentheses_design[0]
            
            if index == self.index:
                prefix += self.indicator
            else:
                prefix += (len(self.indicator) * ' ')
            
            prefix += self.indicator_parentheses * self.indicator_parentheses_design[1] + " " + option.pre

            if self.multiselect and index in self.all_selected:
                format_ = curses.color_pair(1)
                line = ('{0} {1}'.format(prefix, option.node.name), format_)
            else:
                line = '{0} {1}'.format(prefix, option.node.name)
            lines.append(line)

        return lines

    def get_lines(self) -> tuple[list[str], int]:
        """Get the displayed lines and the current line (NOT the index)
        
        :returns: a tuple containing the lines and the current line number"""
        title_lines = self.get_title_lines()
        option_lines = self.get_option_lines()
        lines = title_lines + option_lines
        current_line = self.index + len(title_lines) + 1
        return lines, current_line

    def draw(self, screen) -> None:
        """draw the curses ui on the screen, handle scroll if needed"""
        screen.clear()

        x, y = 1, 1  # start point
        max_y, max_x = screen.getmaxyx()
        max_rows = max_y - y  # the max rows we can draw

        lines, current_line = self.get_lines()

        # calculate how many lines we should scroll, relative to the top
        if current_line <= self.scroll_top:
            self.scroll_top = 0
        elif current_line - self.scroll_top > max_rows:
            self.scroll_top = current_line - max_rows

        lines_to_draw = lines[self.scroll_top:self.scroll_top + max_rows]

        for line in lines_to_draw:
            if type(line) is tuple:
                screen.addnstr(y, x, line[0], max_x - 2, line[1])
            else:
                screen.addnstr(y, x, line, max_x - 2)
            y += 1

        screen.refresh()

    def run_loop(self, screen: window) -> AnyNode:
        while True:
            self.draw(screen)
            c: int = screen.getch()
            if c in KEYS_UP:
                self.move_up()
            elif c in KEYS_DOWN:
                self.move_down()
            elif c in KEYS_ENTER:
                if self.multiselect and len(self.all_selected) < self.min_selection_count:
                    continue
                return self.get_selected()
            elif c in KEYS_SELECT and self.multiselect:
                self.mark_index()
            elif c in self.custom_handlers:
                if ret := self.custom_handlers[c](self):
                    return ret

    def config_curses(self) -> None:
        try:
            # use the default colors of the terminal
            curses.use_default_colors()
            # hide the cursor
            curses.curs_set(0)
            # add some color for multi_select
            curses.init_pair(1, self.foreground, self.background)
        except curses.error:
            # Curses failed to initialize color support, eg. when TERM=vt100
            curses.initscr()

    def _start(self, screen: window) -> AnyNode:
        PickPacker.config_curses()
        return self.run_loop(screen)

    def start(self) -> AnyNode:
        """Starts the interaction with the user"""
        return curses.wrapper(self._start)


def pickpack(*args, **kwargs) -> AnyNode:
    """Construct and start a :class:`PickPacker <PickPacker>`.

    Usage::

      >>> from pickpack import pickpack
      >>> from anytree import Node, RenderTree
      
      >>> child = Node("Child")
      >>> root = Node("Root", children=[child])
      >>> options = RenderTree(root)
      >>> title = 'Please choose an option: '
      
      >>> option, index = pickpack(options, title)
    """
    picker = PickPacker(*args, **kwargs)
    return picker.start()
