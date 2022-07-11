from __future__ import annotations
import curses
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional
from anytree import Node, RenderTree, find
from anytree_utils import add_indices, find_by_index, count_leaves, count_nodes, get_descendants, get_leaves_only

__all__ = ['TreePicker', 'tree_pick']


KEYS_ENTER = (curses.KEY_ENTER, ord('\n'), ord('\r'))
KEYS_UP = (curses.KEY_UP, ord('k'))
KEYS_DOWN = (curses.KEY_DOWN, ord('j'))
KEYS_SELECT = (curses.KEY_RIGHT, ord(' '))


@dataclass
class TreePicker:
    """The :class:`TreePicker <TreePicker>` object

    :param options: a RenderTree (anytree) or a list of options to choose from
    :param title: (optional) a title above options list
    :param root_name: (optional) name of root ("select all") node; defaults to root node's value
    :param multiselect: (optional) if true its possible to select multiple values by hitting SPACE; defaults to False
    :param singleselect_output_include_children: (optional) if true, output will include all children of the selected node, as well as the node itself; defaults to False
    :param output_leaves_only: (optional) if true, only leaf nodes will be returned; for singleselect mode, singleselect_output_include_children MUST be True; defaults to False
    :param indicator: (optional) custom the selection indicator
    :param indicator_parentheses: (optional) include/remove parentheses around selection indicator; defaults to True
    :param default_index: (optional) set this if the default selected option is not the first one
    :param options_map_func: (optional) a mapping function to pass each option through before displaying
    """

    options: RenderTree|list
    title: Optional[str] = None
    root_name: Optional[str] = None
    indicator: str = "*"
    indicator_parentheses: bool = True
    default_index: int = 0
    multiselect: bool = False
    min_selection_count: int = 0
    singleselect_output_include_children: bool = False
    output_leaves_only: bool = False
    options_map_func: Optional[Callable[[Dict], Node]] = None
    all_selected: List[str] = field(init=False, default_factory=list)
    custom_handlers: Dict[str, Callable[["TreePicker"], str]] = field(
        init=False, default_factory=dict
    )
    index: int = field(init=False, default=0)
    scroll_top: int = field(init=False, default=0)

    def __post_init__(self):
        if (type(self.options) == RenderTree and count_nodes(self.options.node) == 0) or (type(self.options) == list and len(self.options) == 0):
            raise ValueError('options should not be an empty list')

        if not self.multiselect and not self.singleselect_output_include_children and self.output_leaves_only:
            raise ValueError('To output only leaves on singleselect mode, singleselect_output_include_children MUST be True')

        optnr = (lambda : count_leaves(self.options.node) if type(self.options) == RenderTree else len(self.options))()

        if self.default_index >= optnr:
            raise ValueError('default_index should be less than the length of options')

        if self.multiselect and self.min_selection_count > optnr:
            raise ValueError('min_selection_count is bigger than the available options, you will not be able to make any selection')

        if self.options_map_func is not None and not callable(self.options_map_func):
            raise ValueError('options_map_func must be a callable function')
        elif self.options_map_func is not None and callable(self.options_map_func) and type(self.options) == list:
            opts = [self.options_map_func(opt) for opt in self.options]
            if len(opts) > 1:
                root = Node("Select all", children=opts)
            else:
                root = opts[0]
            self.options = RenderTree(root)
        add_indices(self.options)
        
        if type(self.options) == RenderTree and self.root_name is not None:
            self.options.node.name = self.root_name

        self.index = self.default_index

    def register_custom_handler(self, key, func):
        self.custom_handlers[key] = func

    def move_up(self):
        self.index -= 1
        if self.index < 0:
            self.index = count_nodes(self.options.node) - 1

    def move_down(self):
        self.index += 1
        if self.index >= count_nodes(self.options.node):
            self.index = 0

    def check_children(self, node:Node):
        for child in node.children:
            if child.index not in self.all_selected:
                self.all_selected.append(child.index)
            if child.children:
                self.check_children(child)
    
    def check_ancestors(self, node:Node):
        while (node is not None and node.parent):
            all_checked = 1
            for child in node.parent.children:
                all_checked = all_checked * (child.index in self.all_selected)
            if all_checked > 0:
                self.all_selected.append(node.parent.index)
                node = node.parent
            else:
                node = None

    def uncheck_children(self, node:Node):
        for child in node.children:
            if child.index in self.all_selected:
                self.all_selected.remove(child.index)
            if child.children:
                self.uncheck_children(child)

    def uncheck_ancestors(self, node:Node):
        while (node is not None and node.parent):
            try:
                self.all_selected.remove(node.parent.index)
                node = node.parent
            except:
                node = None

    def add_relatives_index(self):
        node = find_by_index(self.options.node, self.index)
        self.check_children(node)
        self.check_ancestors(node)

    def remove_relatives_index(self):
        node = find_by_index(self.options.node, self.index)
        self.uncheck_children(node)
        self.uncheck_ancestors(node)

    def mark_index(self):
        if self.multiselect:
            if self.index in self.all_selected:
                self.all_selected.remove(self.index)
                self.remove_relatives_index()
            else:
                self.all_selected.append(self.index)
                self.add_relatives_index()

    def get_selected(self):
        """return the current selected option as a tuple: (option, index)
           or as a list of tuples (in case multiselect==True)
        """
        if self.multiselect:
            return_tuples = []
            if self.output_leaves_only:
                for selected in self.all_selected:
                    node = find_by_index(self.options.node, selected)
                    return_tuples.extend([leaf for leaf in get_leaves_only(node) if leaf not in return_tuples])
            else: 
                for selected in self.all_selected:
                    return_tuples.append((find_by_index(self.options.node, selected), selected))
            return return_tuples
        else:
            node = find_by_index(self.options.node, self.index)
            if self.singleselect_output_include_children:
                if self.output_leaves_only:
                    return get_leaves_only(node)
                return get_descendants(node)
            else:
                return node, self.index

    def get_title_lines(self):
        if self.title:
            return self.title.split('\n') + ['']
        return []

    def get_option_lines(self):
        lines = []
        for index, option in enumerate(self.options):
            if index == self.index:
                prefix = (self.indicator_parentheses * "(") + self.indicator + (self.indicator_parentheses * ")")  + (option.node.depth * '    ') + ((option.node.depth > 0) * '└──')
            else:
                prefix = (self.indicator_parentheses * "(") + (len(self.indicator) * ' ') + (self.indicator_parentheses * ")") + (option.node.depth * '    ') + ((option.node.depth > 0) * '└──')

            if self.multiselect and index in self.all_selected:
                format = curses.color_pair(1)
                line = ('{0} {1}'.format(prefix, option.node.name), format)
            else:
                line = '{0} {1}'.format(prefix, option.node.name)
            lines.append(line)

        return lines

    def get_lines(self):
        title_lines = self.get_title_lines()
        option_lines = self.get_option_lines()
        lines = title_lines + option_lines
        current_line = self.index + len(title_lines) + 1
        return lines, current_line

    def draw(self, screen):
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

        lines_to_draw = lines[self.scroll_top:self.scroll_top+max_rows]

        for line in lines_to_draw:
            if type(line) is tuple:
                screen.addnstr(y, x, line[0], max_x-2, line[1])
            else:
                screen.addnstr(y, x, line, max_x-2)
            y += 1

        screen.refresh()

    def run_loop(self, screen):
        while True:
            self.draw(screen)
            c = screen.getch()
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
                ret = self.custom_handlers[c](self)
                if ret:
                    return ret

    def config_curses(self):
        try:
            # use the default colors of the terminal
            curses.use_default_colors()
            # hide the cursor
            curses.curs_set(0)
            # add some color for multi_select
            # @todo make colors configurable
            curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_WHITE)
        except:
            # Curses failed to initialize color support, eg. when TERM=vt100
            curses.initscr()

    def _start(self, screen):
        self.config_curses()
        return self.run_loop(screen)

    def start(self):
        return curses.wrapper(self._start)

def tree_pick(*args, **kwargs):
    """Construct and start a :class:`Picker <Picker>`.

    Usage::

      >>> from pick import pick
      >>> title = 'Please choose an option: '
      >>> options = ['option1', 'option2', 'option3']
      >>> option, index = pick(options, title)
    """
    picker = TreePicker(*args, **kwargs)
    return picker.start()
