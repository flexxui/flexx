"""
Provides the base ``Widget`` and ``PyWidget`` classes.

When subclassing a Widget to create a compound widget (i.e. a widget
that contains other widgets), initialize the child widgets inside the
``init()`` method. That method is called while the widget is the
*current widget*; any widgets instantiated inside it will automatically
become children.

.. UIExample:: 100

    from flexx import flx

    class Example(flx.Widget):
        def init(self):
            super().init()
            
            flx.Button(text='foo')
            flx.Button(text='bar')


One can also use a widget as a context manager (i.e. using the ``with``
statement) to create child widgets. This is particularly useful for
layout widgets (like ``HBox``).

.. UIExample:: 100

    from flexx import flx

    class Example(flx.Widget):
        def init(self):
            super().init()
            
            with flx.HBox():
                flx.Button(flex=1, text='foo')
                flx.Button(flex=2, text='bar')

In the above two examples, the newly created classes subclass from
``Widget`` and are thus a ``JsComponent`` (i.e. operate in JS). This
may be what you want if you are aiming for a UI that can be exported
for the web. If, however, you are developing a desktop application,
consider subclassing from ``PyWidget`` instead, which will make your
widget operate in Python.

It is also possible to create custom low-level widgets by implementing
``_render_dom()``, resulting in a declarative "react-like" (but less
Pythonic) approach. It returns a virtual DOM that is used to update/replace
the real browser DOM.

.. UIExample:: 100

    from flexx import flx
    
    class Example(flx.Widget):
        
        count = flx.IntProp()
        
        def _render_dom(self):
            # This method automatically gets called when any of the used
            # properties (only count, in this case) changes.
            return flx.create_element('div', {}, 
                flx.create_element('button',
                                   {'onclick': self.increase_count},
                                   '+'),
                flx.create_element('span',
                                   {'style.background': '#afa'},
                                   str(self.count)),
                )
        
        @flx.action
        def increase_count(self):
            self._mutate_count(self.count + 1)

"""

from pscript import undefined, window, RawJS

from ..event import loop
from .. import event, app

from . import logger  # noqa


def create_element(type, props=None, *children):
    """ Convenience function to create a dictionary to represent
    a virtual DOM node. Intended for use inside ``Widget._render_dom()``.

    The content of the widget may be given as a series/list of child nodes
    (virtual or real), and strings. Strings are converted to text nodes. To
    insert raw HTML, use the ``innerHTML`` prop, but be careful not to
    include user-defined text, as this may introduce openings for XSS attacks.

    The returned dictionary has three fields: type, props, children.
    """
    if len(children) == 0:
        children = None  # i.e. don't touch children
    elif len(children) == 1 and isinstance(children[0], list):
        children = children[0]

    return dict(type=type,
                props=props or {},
                children=children,
                )


class Widget(app.JsComponent):
    """ Base widget class (a :class:`Component <flexx.event.Component>` in JS wrapping
    an `HTML element <https://developer.mozilla.org/docs/Web/HTML/Element>`_).
    
    When subclassing a Widget, it is recommended to not implement the
    ``__init__()`` method, but instead implement ``init()`` for compound
    (higher-level) widgets, and ``_create_dom()`` for low-level widgets.
    
    Widgets can be styled using `CSS <https://developer.mozilla.org/docs/Web/CSS>`_
    by implementing a string class attribute named ``CSS``.
    A widget's node has a CSS-class-name corresponding to its Python class
    (and its base classes), following the scheme ``flx-WidgetClassName``.
    
    All widgets have a ``node`` and ``outernode`` attribute (only accessible
    in JavaScript), representing the 
    `DOM element(s) <https://developer.mozilla.org/docs/Web/HTML/Element>`_
    that represent the widget. For most types of widgets, ``node`` is
    equal to ``outernode``. For the ``Widget`` class, this is simply a
    `<div> <https://developer.mozilla.org/docs/Web/HTML/Element/div>`_
    element. If you don't understand what this is about, don't worry;
    you won't need it unless you are creating your own low-level widgets.
    See ``_create_dom()`` for details.
    
    When implementing your own widget class, the class attribute
    ``DEFAULT_MIN_SIZE`` can be set to specify a sensible minimum size.
    
    """

    DEFAULT_MIN_SIZE = 0, 0

    CSS = """

    .flx-Widget {
        box-sizing: border-box;
        overflow: hidden;
        position: relative;  /* helps with absolute positioning of content */
    }

    /* Main widget to fill the whole page */
    .flx-main-widget {
       position: absolute;
       left: 0;
       right: 0;
       width: 100%;
       top: 0;
       bottom: 0;
       height: 100%;
    }

    /* to position children absolute */
    .flx-abs-children > .flx-Widget {
        position: absolute;
    }

    /* Fix issue flexbox > Widget > layout on Chrome */
    .flx-Widget:not(.flx-Layout) > .flx-Layout {
        position: absolute;
    }
    """

    ## Properties

    container = event.StringProp('', settable=True, doc="""
        The id of the DOM element that contains this widget if
        parent is None. Use 'body' to make this widget the root.
        """)

    parent = event.ComponentProp(None, doc="""
        The parent widget, or None if it has no parent. Setting
        this property will update the "children" property of the
        old and new parent.
        """)

    children = app.LocalProperty((), doc="""
        The child widgets of this widget. This property is not settable and
        only present in JavaScript.
        """)

    title = event.StringProp('', settable=True, doc="""
        The string title of this widget. This is used to mark
        the widget in e.g. a tab layout or form layout, and is used
        as the app's title if this is the main widget.
        """)

    icon = app.LocalProperty('', settable=False, doc="""
        The icon for this widget. This is used is some widgets classes,
        and is used as the app's icon if this is the main widget.
        It is settable from Python, but only present in JavaScript.
        """)

    css_class = event.StringProp('', settable=True, doc="""
        The extra CSS class name to asign to the DOM element.
        Spaces can be used to delimit multiple names. Note that the
        DOM element already has a css class-name corresponding to
        its class (e.g. 'flx-Widget) and all its superclasses.
        """)

    flex = event.FloatPairProp((0, 0), settable=True, doc="""
        How much space this widget takes (relative to the other
        widgets) when contained in a flexible layout such as HBox,
        HFix, HSplit or FormLayout. A flex of 0 means to take
        the minimum size. Flex is a two-element tuple, but both values
        can be specified at once by specifying a scalar.
        """)

    size = event.FloatPairProp((0, 0), settable=False, doc="""
        The actual size of the widget (readonly). Flexx tries to keep
        this value up-to-date, but in e.g. a box layout, a change in a
        Button's text can change the size of sibling widgets.
        """)

    minsize = event.FloatPairProp((0, 0), settable=True, doc="""
        The user-defined minimum size (width, height) of this widget in pixels.
        The default value differs per widget (``Widget.DEFAULT_MIN_SIZE``).
        Note that using "min-width" or "min-height" in ``apply_style()``.
        (and in the ``style`` kwarg) also set this property. Minimum sizes set
        in CSS are ignored.
        """)

    minsize_from_children = event.BoolProp(True, settable=True, doc="""
        Whether the children are taken into account to calculate this
        widget's size constraints. Default True: both the ``minsize``
        of this widget and the size constraints of its children (plus
        spacing and padding for layout widgets) are used to calculate
        the size constraints for this widget.

        Set to False to prevent the content in this widget to affect
        the parent's layout, e.g. to allow fully collapsing this widget
        when the parent is a splitter. If this widget has a lot of
        content, you may want to combine with ``style='overflow-y: auto'``.
        """)

    maxsize = event.FloatPairProp((1e9, 1e9), settable=True, doc="""
        The user-defined maximum size (width, height) of this widget in pixels.
        Note that using "max-width" or "max-height" in ``apply_style()``.
        (and in the ``style`` kwarg) also set this property. Maximum sizes set
        in CSS are ignored.
        """)

    _size_limits = event.TupleProp((0, 1e9, 0, 1e9), settable=True, doc="""
        A 4-element tuple (minWidth, maxWidth, minHeight, maxHeight) in pixels,
        based on ``minsize``, ``maxsize`` (and for some layouts the size limits
        of the children). Private prop for internal use.
        """)

    tabindex = event.IntProp(-2, settable=True, doc="""
        The index used to determine widget order when the user
        iterates through the widgets using tab. This also determines
        whether a widget is able to receive key events. Flexx automatically
        sets this property when it should emit key events.
        Effect of possible values on underlying DOM element:

        * -2: element cannot have focus unless its a special element like
            a link or form control (default).
        * -1: element can have focus, but is not reachable via tab.
        * 0: element can have focus, and is reachable via tab in the order
            at which the element is defined.
        * 1 and up: element can have focus, and the tab-order is determined
            by the value of tabindex.
        """)

    capture_mouse = event.IntProp(1, settable=True, doc="""
        To what extend the mouse is "captured".

        * If 0, the mouse is not captured, and move events are only emitted
          when the mouse is pressed down (not recommended).
        * If 1 (default) the mouse is captured when pressed down, so move
          and up events are received also when the mouse is outside the widget.
        * If 2, move events are also emitted when the mouse is not pressed down
          and inside the widget.
        """)

    @event.action
    def set_icon(self, val):
        """ Set the icon for this widget. This is used is some widgets classes,
        and is used as the app's icon if this is the main widget.
        It is settable from Python, but the property is not available in Python.

        Can be a url, a relative url to a shared asset, or a base64
        encoded image. In the future this may also support names in
        icon packs like FontAwesome.
        """
        if not isinstance(val, str):
            raise TypeError('Icon must be a string')
        self._mutate_icon(val)

    ## Methods

    def __init__(self, *init_args, **kwargs):

        # Handle parent
        try:
            given_parent = parent = kwargs.pop('parent')
            parent_given = True
        except KeyError:
            given_parent = parent = None
            parent_given = False
        
        if parent is None:
            active_components = loop.get_active_components()
            for active_component in reversed(active_components):
                if isinstance(active_component, Widget):
                    parent = active_component
                    break
        # -> we apply via set_parent below

        # Use parent session unless session was given
        if parent is not None and not kwargs.get('flx_session', None):
            kwargs['flx_session'] = parent.session

        # Allow initial styling via property-like mechanism
        style = kwargs.pop('style', '')

        # Whether this was the component that represents the app.
        # We use window.flexx.need_main_widget for a similar purpose,
        # but we might use it in the future.
        is_app = kwargs.get('flx_is_app', False)  # noqa

        # Init this component (e.g. create properties and actions)
        super().__init__(*init_args, **kwargs)

        # Some further initialization ...
        # Note that the _comp_init_property_values() will get called first.

        # Attach this widget in the widget hierarchy, if we can
        if parent_given is True:
            self.set_parent(given_parent)
        elif parent is not None:
            self.set_parent(parent)
        elif self.container == '':
            # Determine whether this should be the main widget. If the browser
            # seems to need one, and this is the first "orphan" widget to be
            # instantiated, this widget will take on this role.
            if window.flexx.need_main_widget:
                window.flexx.need_main_widget = False
                self.set_container('body')

        # Apply widget-specific default minsize if minsize is not given
        if kwargs.get('minsize', None) is None:
            self.set_minsize(self.DEFAULT_MIN_SIZE)

        # Apply style if given (can override minsize)
        if style:
            self.apply_style(style)

    def _comp_init_property_values(self, property_values):
        # This is a good time to do further initialization. The JsComponent
        # does its init here, property values have been set at this point,
        # but init() has not yet been called.

        super()._comp_init_property_values(property_values)

        # Create DOM nodes
        # outernode is the root node
        # node is an inner (representative) node, often the same, but not always
        nodes = self._create_dom()
        assert nodes is not None
        if not isinstance(nodes, list):
            nodes = [nodes]
        assert len(nodes) == 1 or len(nodes) == 2
        if len(nodes) == 1:
            self.outernode = self.node = self.__render_resolve(nodes[0])
        else:
            self.outernode = self.__render_resolve(nodes[0])
            self.node = self.__render_resolve(nodes[1])

        # Derive css class name from class hierarchy (needs self.outernode)
        cls = self.__class__
        for i in range(32):  # i.e. a safe while-loop
            self.outernode.classList.add('flx-' + cls.__name__)
            if cls is Widget.prototype:
                break
            cls = cls._base_class
        else:
            raise RuntimeError('Error determining class names for %s' % self.id)

        # Setup JS events to enter Flexx' event system (needs self.node)
        self._init_events()

    def init(self):
        """ Overload this to initialize a custom widget. It's preferred
        to use this instead of ``__init__()``, because it gets called
        at a better moment in the instantiation of the widget.
        
        This method receives any positional arguments that were passed
        to the constructor.  When called, this widget is the current parent.
        """
        # The Component class already implement a stub, but we may like a more
        # specific docstring here.
        pass

    def _create_dom(self):
        """ Create DOM node(s) for this widget.

        This method must return two (real or virtual) DOM nodes which
        will be available as ``self.outernode`` and ``self.node``
        respectively. If a single node is given, it is used for both
        values. These attributes must remain unchanged throughout the
        lifetime of a widget. This method can be overloaded in
        subclasses.

        Most widgets have the same value for ``node`` and ``outernode``.
        However, in some cases it helps to distinguish between the
        semantic "actual node" and a wrapper. E.g. Flexx uses it to
        properly layout the ``CanvasWidget`` and ``TreeItem``.
        Internally, Flexx uses the ``node`` attribute for tab-index, and
        binding to mouse/touch/scroll/key events. If your ``outernode``
        already semantically represents your widget, you should probably
        just use that.
        """
        return create_element('div')

    def _render_dom(self):
        """ Update the content of the DOM for this widget.

        This method must return a DOM structure consisting of (a mix of)
        virtual nodes, real nodes and strings. The widget will use this
        structure to update the real DOM in a relatively efficient
        manner (new nodes are only (re)created if needed). The root
        element must match the type of this widget's outernode. This
        method may also return a list to apply as the root node's children.

        Note that this method is called from an implicit reaction: it will
        auto-connect to any properties that are accessed. Combined with the
        above, this allows for a very declarative way to write widgets.

        Virtual nodes are represented as dicts with fields "type", "props"
        and "children". Children is a list consisting of real dom nodes,
        virtual nodes, and strings. Strings are converted to TextNode (XSS safe).
        The ``create_element()`` function makes it easy to create virtual nodes.

        The default ``_render_dom()`` method simply places the outer node of
        the child widgets as the content of this DOM node, while preserving
        nodes that do not represent a widget. Overload as needed.
        """
        nodes = []
        for i in range(len(self.outernode.childNodes)):
            node = self.outernode.childNodes[i]
            if not (node.classList and node.classList.contains('flx-Widget')):
                nodes.push(node)  # push is JS' append
        for widget in self.children:
            nodes.push(widget.outernode)
        return nodes

    @event.reaction
    def __render(self):
        # Call render method
        vnode = self._render_dom()
        # Validate output, allow it to return content instead of a vnode
        if vnode is None or vnode is self.outernode:
            return
        elif isinstance(vnode, list):
            vnode = dict(type=self.outernode.nodeName, props={}, children=vnode)
        elif isinstance(vnode, dict):
            if vnode.type.toLowerCase() != self.outernode.nodeName.toLowerCase():
                raise ValueError('Widget._render_dom() must return root node with '
                                 'same element type as outernode.')
        else:
            raise TypeError('Widget._render_dom() '
                            'must return None, list or dict.')
        # Resolve
        node = self.__render_resolve(vnode, self.outernode)
        assert node is self.outernode

    def __render_resolve(self, vnode, node=None):
        """ Given a DOM node and its virtual representation,
        update or create a new DOM node as necessary.
        """

        # Check vnode (we check vnode.children further down)
        if vnode and vnode.nodeName:  # is DOM node
            return vnode
        elif isinstance(vnode, str):
            return window.document.createTextNode(vnode)
        elif not isinstance(vnode, dict):
            raise TypeError('Widget._render_dom() needs virtual nodes '
                            'to be dicts, not ' + vnode)
        if not isinstance(vnode.type, str):
            raise TypeError('Widget._render_dom() needs virtual node '
                            'type to be str, not ' + vnode.type)
        if not isinstance(vnode.props, dict):
            raise TypeError('Widget._render_dom() needs virtual node '
                            'props as dict, not ' + vnode.props)

        # Resolve the node itself
        if node is None or node.nodeName.toLowerCase() != vnode.type.toLowerCase():
            node = window.document.createElement(vnode.type)

        # Resolve props (i.e. attributes)
        map = {'css_class': 'className', 'class': 'className'}
        for key, val in vnode.props.items():
            ob = node
            parts = key.replace('__', '.').split('.')
            for i in range(len(parts)-1):
                ob = ob[parts[i]]
            key = parts[len(parts)-1]
            ob[map.get(key, key)] = val

        # Resolve content
        if vnode.children is None:
            pass  # dont touch it
        elif isinstance(vnode.children, list):
            # Truncate children
            while len(node.childNodes) > len(vnode.children):
                node.removeChild(node.childNodes[len(node.childNodes)-1])
            # Resolve children
            i1 = -1
            for i2 in range(len(vnode.children)):
                i1 += 1
                vsubnode = vnode.children[i2]
                subnode = None
                if i1 < len(node.childNodes):
                    subnode = node.childNodes[i1]
                    if subnode.nodeName == "#text" and isinstance(vsubnode, str):
                        if subnode.data != vsubnode:
                            subnode.data = vsubnode
                        continue  # early exit for text nodes
                new_subnode = self.__render_resolve(vsubnode, subnode)
                if subnode is None:
                    node.appendChild(new_subnode)
                elif subnode is not new_subnode:
                    node.insertBefore(new_subnode, subnode)
                    node.removeChild(subnode)
        else:
            window.flexx_vnode = vnode
            raise TypeError('Widget._render_dom() '
                            'needs virtual node children to be None or list, not %s' %
                            vnode.children)

        return node

    # Note that this method is only present at the Python side
    # (because the JsComponent meta class makes it so).
    def _repr_html_(self):
        """ This is to get the widget shown inline in the notebook.
        """
        if self.container:
            return "<i>Th widget %s is already shown in this notebook</i>" % self.id

        container_id = self.id + '_container'
        self.set_container(container_id)
        return "<div class='flx-container' id='%s' />" % container_id

    def dispose(self):
        """ Overloaded version of dispose() that disposes any child widgets.
        """
        # Dispose children? Yes, each widget can have exactly one parent and
        # when that parent is disposed, it makes sense to assume that the
        # child ought to be disposed as well. It avoids memory leaks. If a
        # child is not supposed to be disposed, the developer should orphan the
        # child widget.
        children = self.children
        # First dispose children (so they wont send messages back), then clear
        # the children and dispose ourselves.
        for child in children:
            child.dispose()
        super().dispose()
        self.set_parent(None)
        self._children_value = ()

    ## Actions


    @event.action
    def apply_style(self, style):
        """ Apply CSS style to this widget object. e.g.
        ``"background: #f00; color: #0f0;"``. If the given value is a
        dict, its key-value pairs are converted to a CSS style string.

        Initial styling can also be given in a property-like fashion:
        ``MyWidget(style='background:red;')``

        For static styling it is often better to define a CSS class attribute
        and/or use ``css_class``.
        """
        if isinstance(style, dict):
            style = ['%s: %s' % (k, v) for k, v in style.items()]
            style = '; '.join(style)

        # self.node.style = style  # forbidden in strict mode,
        # plus it clears all previously set style

        # Note that styling is applied to the outer node, just like
        # the styling defined via the CSS attribute. In most cases
        # the inner and outer node are the same, but not always
        # (e.g. CanvasWidget).

        # Set style elements, keep track in a dict
        d = {}
        if style:
            for part in style.split(';'):
                if ':' in part:
                    key, val = part.split(':')
                    key, val = key.trim(), val.trim()
                    self.outernode.style[key] = val
                    d[key] = val

        # Did we change style related to sizing?
        w1, h1 = self.minsize
        w2, h2 = self.maxsize
        mima = w1, w2, h1, h2
        size_limits_keys = 'min-width', 'max-width', 'min-height', 'max-height'
        size_limits_changed = False
        for i in range(4):
            key = size_limits_keys[i]
            if key in d:
                val = d[key]
                if val == '0':
                    mima[i] = 0
                    size_limits_changed = True
                elif val.endswith('px'):
                    mima[i] = float(val[:-2])
                    size_limits_changed = True

        if size_limits_changed:
            self.set_minsize((mima[0], mima[2]))
            self.set_maxsize((mima[1], mima[3]))

    ## Reactions

    @event.reaction('css_class')
    def __css_class_changed(self, *events):
        if len(events):
            # Reset / apply explicitly given class name (via the prop)
            for cn in events[0].old_value.split(' '):
                if cn:
                    self.outernode.classList.remove(cn)
            for cn in events[-1].new_value.split(' '):
                if cn:
                    self.outernode.classList.add(cn)

    @event.reaction('title')
    def __title_changed(self, *events):
        if self.parent is None and self.container == 'body':
            window.document.title = self.title or 'Flexx app'

    @event.reaction('icon')
    def __icon_changed(self, *events):
        if self.parent is None and self.container == 'body':
            window.document.title = self.title or 'Flexx app'

            link = window.document.createElement('link')
            oldLink = window.document.getElementById('flexx-favicon')
            link.id = 'flexx-favicon'
            link.rel = 'shortcut icon'
            link.href = events[-1].new_value
            if oldLink:
                window.document.head.removeChild(oldLink)
            window.document.head.appendChild(link)

    @event.reaction
    def __update_tabindex(self, *events):
        # Note that this also makes the widget able to get focus, and thus
        # able to do key events.
        ti = self.tabindex
        if ti < -1:
            self.node.removeAttribute('tabIndex')
        else:
            self.node.tabIndex = ti

    # Now solved with CSS, which seems to work, but leaving this code for now ...
    # @event.reaction('children', '!children*.mode', '!children*.orientation')
    # def __make_singleton_container_widgets_work(self, *events):
    #     classNames = self.outernode.classList
    #     if not classNames.contains('flx-Layout'):
    #         # classNames.remove('flx-box')
    #         # classNames.remove('flx-horizontal')
    #         # classNames.remove('flx-vertical')
    #         classNames.remove('flx-abs-children')
    #         children = self.children
    #         if len(children) == 1:
    #             subClassNames = children[0].outernode.classList
    #             if subClassNames.contains('flx-Layout'):
    #                 classNames.add('flx-abs-children')
    #             # This seems to be enough, though previously we did:
    #             # if subClassNames.contains('flx-box'):
    #             #     # classNames.add('flx-box')
    #             #     vert = subClassNames.contains('flx-vertical')
    #             #     classNames.add('flx-horizontal' if vert else 'flx-horizontal')
    #             # else:
    #             #     # If child is a layout that uses absolute position, make
    #             #     # out children absolute.
    #             #     for name in ('split', 'StackPanel', 'TabPanel', 'DockPanel'):
    #             #         if subClassNames.contains('flx-' + name):
    #             #             classNames.add('flx-abs-children')
    #             #             break

    ## Sizing

    @event.reaction
    def _update_minmaxsize(self):
        """ Update the internal _size_limits.
        Note that this is an implicit reaction.
        """
        # Get new limits
        w1, w2, h1, h2 = self._query_min_max_size()
        w1 = max(0, w1)
        h1 = max(0, h1)
        # Update the property, so that our parent may react
        self._set_size_limits((w1, w2, h1, h2))
        # Update the style, so that flexbox works
        s = self.outernode.style
        s['min-width'] = w1 + 'px'
        s['max-width'] = w2 + 'px'
        s['min-height'] = h1 + 'px'
        s['max-height'] = h2 + 'px'

    def _query_min_max_size(self):
        """Can be overloaded in subclasses to include the minsize and maxsize of
        children. Note that this is called from an implicit reaction.
        """
        w1, h1 = self.minsize
        w2, h2 = self.maxsize

        # Widgets that are custom classes containing a single layout propagate
        # that layout's limits
        if self.outernode.classList.contains('flx-Layout') is False:
            if self.minsize_from_children is True and len(self.children) == 1:
                child = self.children[0]
                if child.outernode.classList.contains('flx-Layout') is True:
                    w3, w4, h3, h4 = child._query_min_max_size()
                    w1, w2 = max(w1, w3), min(w2, w4)
                    h1, h2 = max(h1, h3), min(h2, h4)

        return w1, w2, h1, h2

    @event.action
    def check_real_size(self):
        """ Check whether the current size has changed. It should usually not
        be necessary to invoke this action, since a widget does so by itself,
        but it some situations the widget may not be aware of possible size
        changes.
        """
        n = self.outernode
        cursize = self.size
        if cursize[0] != n.clientWidth or cursize[1] != n.clientHeight:
            self._mutate_size([n.clientWidth, n.clientHeight])

    @event.reaction('container', 'parent.size', 'children')
    def __size_may_have_changed(self, *events):
        # Invoke actions, i.e. check size in *next* event loop iter to
        # give the DOM a chance to settle.
        self.check_real_size()

    def _set_size(self, prefix, w, h):
        """ Method to allow setting size (via style). Used by some layouts.
        """
        size = w, h
        for i in range(2):
            if size[i] <= 0 or size is None or size is undefined:
                size[i] = ''  # Use size defined by CSS
            elif size[i] > 1:
                size[i] = size[i] + 'px'
            else:
                size[i] = size[i] * 100 + '%'
        self.outernode.style[prefix + 'width'] = size[0]
        self.outernode.style[prefix + 'height'] = size[1]

    ## Parenting

    @event.action
    def set_parent(self, parent, pos=None):
        """ Set the parent widget (can be None). This action also mutates the
        childen of the old and new parent.
        """
        old_parent = self.parent  # or None
        new_parent = parent

        # Early exit
        if new_parent is old_parent and pos is None:
            return
        if not (new_parent is None or isinstance(new_parent, Widget)):
            raise ValueError('%s.parent must be a Widget or None' % self.id)

        # Apply parent
        self._mutate_parent(new_parent)

        # Remove ourselves
        if old_parent is not None:
            children = []
            for i in range(len(old_parent.children)):
                child = old_parent.children[i]
                if child is not self:
                    children.push(child)
            if old_parent is not new_parent:
                old_parent._mutate_children(children)

        # Insert ourselves
        if new_parent is not None:
            if old_parent is not new_parent:
                children = []
                for i in range(len(new_parent.children)):
                    child = new_parent.children[i]
                    if child is not self:
                        children.push(child)
            if pos is None:
                children.push(self)
            elif pos >= 0:
                children.insert(pos, self)
            elif pos < 0:
                children.append(None)
                children.insert(pos, self)
                children.pop(-1)
            else:  # maybe pos is nan for some reason
                children.push(self)
            new_parent._mutate_children(children)

    @event.reaction('container')
    def __container_changed(self, *events):
        id = self.container
        self.outernode.classList.remove('flx-main-widget')
        if self.parent:
            return

        # Let session keep us up to date about size changes
        # (or make it stop if we dont have a container anymore)
        self._session.keep_checking_size_of(self, bool(id))

        if id:
            if id == 'body':
                el = window.document.body
                self.outernode.classList.add('flx-main-widget')
                window.document.title = self.title or 'Flexx app'
            else:
                el = window.document.getElementById(id)
                if el is None:  # Try again later
                    window.setTimeout(self.__container_changed, 100)
                    return
            el.appendChild(self.outernode)

    def _release_child(self, widget):
        """ Overload to restore a child widget, e.g. to its normal style.
        """
        pass

    ## Events

    # todo: events: focus, enter, leave ... ?

    def _registered_reactions_hook(self):
        event_types = super()._registered_reactions_hook()
        if self.tabindex < -1:
            for event_type in event_types:
                if event_type in ('key_down', 'key_up', 'key_press'):
                    self.set_tabindex(-1)
        return event_types

    def _init_events(self):
        # TODO: we listen to a lot of events which is unncessary in a lot of cases.
        # Maybe make it possible (with a class attribute?) to configure this
        # Connect some standard events
        self._addEventListener(self.node, 'wheel', self.pointer_wheel, 0)
        self._addEventListener(self.node, 'keydown', self.key_down, 0)
        self._addEventListener(self.node, 'keyup', self.key_up, 0)
        self._addEventListener(self.node, 'keypress', self.key_press, 0)
        # Mouse events, for move and up we implement some heuristics below
        self._addEventListener(self.node, 'mousedown', self.pointer_down, 0)
        self._addEventListener(self.node, 'click', self.pointer_click, 0)
        self._addEventListener(self.node, 'dblclick', self.pointer_double_click, 0)
        # Touch events
        self._addEventListener(self.node, 'touchstart', self.pointer_down, 0)
        self._addEventListener(self.node, 'touchmove', self.pointer_move, 0)
        self._addEventListener(self.node, 'touchend', self.pointer_up, 0)
        self._addEventListener(self.node, 'touchcancel', self.pointer_cancel, 0)

        # Implement mouse capturing. When a mouse is pressed down on
        # a widget, it "captures" the mouse, and will continue to receive
        # move and up events, even if the mouse is not over the widget.

        self._capture_flag = 0
        # 0: mouse not down, 1: mouse down (no capture), 2: captured, -1: capture end

        def mdown(e):
            # Start emitting move events, maybe follow the mouse outside widget bounds
            if self.capture_mouse == 0:
                self._capture_flag = 1
            else:
                self._capture_flag = 2
                window.document.addEventListener("mousemove", mmove_outside, True)
                window.document.addEventListener("mouseup", mup_outside, True)
                # Explicit caputuring is not necessary, and even causes problems on IE
                #if self.node.setCapture:
                #    self.node.setCapture()

        def mmove_inside(e):
            # maybe emit move event
            if self._capture_flag == -1:
                self._capture_flag = 0
            elif self._capture_flag == 1:
                self.pointer_move(e)
            elif self._capture_flag == 0 and self.capture_mouse > 1:
                self.pointer_move(e)

        def mup_inside(e):
            if self._capture_flag == 1:
                self.pointer_up(e)
            self._capture_flag = 0

        def mmove_outside(e):
            # emit move event
            if self._capture_flag == 2:  # can hardly be anything else, but be safe
                e = window.event if window.event else e
                self.pointer_move(e)

        def mup_outside(e):
            # emit mouse up event, and stop capturing
            if self._capture_flag == 2:
                e = window.event if window.event else e
                stopcapture()
                self.pointer_up(e)

        def stopcapture():
            # Stop capturing
            if self._capture_flag == 2:
                self._capture_flag = -1
                window.document.removeEventListener("mousemove", mmove_outside, True)
                window.document.removeEventListener("mouseup", mup_outside, True)

        def losecapture(e):
            # We lost the capture. The losecapture event seems to be IE only.
            # The pointer_cancel seems poort supported too. So pointer_cancel
            # only really works with touch events ...
            stopcapture()
            self.pointer_cancel(e)

        # Setup capturing and releasing
        self._addEventListener(self.node, 'mousedown', mdown, True)
        self._addEventListener(self.node, "losecapture", losecapture)
        # Subscribe to normal mouse events
        self._addEventListener(self.node, "mousemove", mmove_inside, False)
        self._addEventListener(self.node, "mouseup", mup_inside, False)

    @event.emitter
    def pointer_down(self, e):
        """ Event emitted when mouse-button/touchpad/screen is pressed.

        All pointer events have the following attributes:

        * pos: the pointer position, in pixels, relative to this widget
        * page_pos: the pointer position relative to the page
        * button: what mouse button the event is about, 1, 2, 3 are left, right,
            middle, respectively. 0 indicates no button.
        * buttons: what buttons were pressed at the time of the event.
        * modifiers: list of strings "Alt", "Shift", "Ctrl", "Meta" for
            modifier keys pressed down at the time of the event.
        * touches: a dictionary that maps touch_id's to (x, y, force) tuples.
            For mouse events touch_id is -1 and force is 1.

        A note about the relation with JavaScript events: although the name
        might suggest that this makes use of JS pointer events, this is not
        the case; Flexx captures both mouse events and touch events and exposes
        both as its own "pointer event". In effect, it works better on mobile
        devices, and has multi-touch support.
        """
        return self._create_pointer_event(e)

    @event.emitter
    def pointer_up(self, e):
        """ Event emitted when mouse-button/touchpad/screen is released.

        See pointer_down() for a description of the event object.
        """
        return self._create_pointer_event(e)

    @event.emitter
    def pointer_cancel(self, e):
        """ Event emitted when the mouse/touch is lost, e.g. the window becomes
        inactive during a drag. This only seem to work well for touch events
        in most browsers.

        See pointer_down() for a description of the event object.
        """
        return self._create_pointer_event(e)

    @event.emitter
    def pointer_click(self, e):
        """ Event emitted when mouse-button/touchpad/screen is clicked.

        See pointer_down() for a description of the event object.
        """
        return self._create_pointer_event(e)

    @event.emitter
    def pointer_double_click(self, e):
        """ Event emitted when mouse-button/touchpad/screen is double-clicked.

        See pointer_down() for a description of the event object.
        """
        return self._create_pointer_event(e)

    @event.emitter
    def pointer_move(self, e):
        """ Event fired when the mouse or a touch is moved.

        See pointer_down for details.
        """

        ev = self._create_pointer_event(e)
        ev.button = 0
        return ev

    @event.emitter
    def pointer_wheel(self, e):
        """ Event emitted when the mouse wheel is used.

        See pointer_down() for a description of the event object.
        Additional event attributes:

        * hscroll: amount of scrolling in horizontal direction
        * vscroll: amount of scrolling in vertical direction
        """
        # Note: wheel event gets generated also for parent widgets
        # I think this makes sense, but there might be cases
        # where we want to prevent propagation.
        ev = self._create_pointer_event(e)
        ev.button = 0
        ev.hscroll = e.deltaX * [1, 16, 600][e.deltaMode]
        ev.vscroll = e.deltaY * [1, 16, 600][e.deltaMode]
        return ev

    def _create_pointer_event(self, e):
        # Get offset to fix positions
        rect = self.node.getBoundingClientRect()
        offset = rect.left, rect.top

        if e.type.startswith('touch'):
            # Touch event - select one touch to represent the main position
            t = e.changedTouches[0]
            pos = float(t.clientX - offset[0]), float(t.clientY - offset[1])
            page_pos = t.pageX, t.pageY
            button = 0
            buttons = []
            # Include basic support for multi-touch
            touches = {}
            for i in range(e.changedTouches.length):
                t = e.changedTouches[i]
                if t.target is not e.target:
                    continue
                touches[t.identifier] = (float(t.clientX - offset[0]),
                                         float(t.clientY - offset[1]),
                                         t.force)
        else:
            # Mouse event
            pos = float(e.clientX - offset[0]), float(e.clientY - offset[1])
            page_pos = e.pageX, e.pageY
            # Fix buttons
            if e.buttons:
                buttons_mask = RawJS(
                    "e.buttons.toString(2).split('').reverse().join('')"
                )
            else:
                # libjavascriptcoregtk-3.0-0  version 2.4.11-1 does not define
                # e.buttons
                buttons_mask = [e.button.toString(2)]
            buttons = [i+1 for i in range(5) if buttons_mask[i] == '1']
            button = {0: 1, 1: 3, 2: 2, 3: 4, 4: 5}[e.button]
            touches = {-1: (pos[0], pos[1], 1)}  # key must not clash with real touches

        # note: our button has a value as in JS "which"
        modifiers = [n for n in ('Alt', 'Shift', 'Ctrl', 'Meta')
                        if e[n.toLowerCase() + 'Key']]
        # Create event dict
        return dict(pos=pos, page_pos=page_pos, touches=touches,
                    button=button, buttons=buttons,
                    modifiers=modifiers,
                    )

    @event.emitter
    def key_down(self, e):
        """ Event emitted when a key is pressed down while this
        widget has focus. A key event has the following attributes:

        * key: the character corresponding to the key being pressed, or
            a key name like "Escape", "Alt", "Enter".
        * modifiers: list of strings "Alt", "Shift", "Ctrl", "Meta" for
            modifier keys pressed down at the time of the event.

        A browser may associate certain actions with certain key presses.
        If this browser action is unwanted, it can be disabled by
        overloading this emitter:

        .. code-block:: py

            @event.emitter
            def key_down(self, e):
                # Prevent browser's default reaction to function keys
                ev = super().key_press(e)
                if ev.key.startswith('F'):
                    e.preventDefault()
                return ev
        """
        return self._create_key_event(e)

    @event.emitter
    def key_up(self, e):
        """ Event emitted when a key is released while
        this widget has focus. See key_down for details.
        """
        return self._create_key_event(e)

    @event.emitter
    def key_press(self, e):
        """ Event emitted when a key is released after pressing down, in theory.
        In contast to key_down, this event does not fire for the
        pressing of modifier keys, and some browsers will also not fire
        for the arrow keys, backspace, etc. See key_down for details.
        """
        # Is there actually a reason for ever using this instead of key_down?
        return self._create_key_event(e)

    def _create_key_event(self, e):
        # https://developer.mozilla.org/en-US/docs/Web/API/KeyboardEvent
        # key: chrome 51, ff 23, ie 9
        # code: chrome ok, ff 32, ie no
        modifiers = [n for n in ('Alt', 'Shift', 'Ctrl', 'Meta')
                        if e[n.toLowerCase() + 'Key']]
        key = e.key
        if not key and e.code:  # Chrome < v51
            key = e.code
            if key.startswith('Key'):
                key = key[3:]
                if 'Shift' not in modifiers:
                    key = key.toLowerCase()
            elif key.startswith('Digit'):
                key = key[5:]
        # todo: handle Safari and older browsers via keyCode
        key = {'Esc': 'Escape', 'Del': 'Delete'}.get(key, key)  # IE
        return dict(key=key, modifiers=modifiers)


class PyWidget(app.PyComponent):
    """ A base class that can be used to create compound widgets that
    operate in Python. This enables an approach for building GUI's in
    a Pythonic way: by only *using* JS components (actual widgets) all
    code that you *write* can be Python code.

    Internally, objects of this class create a sub-widget (a
    ``flx.Widget`` instance). When the object is used as a context
    manager, the sub-widget will also become active. Further, this class
    gets attributes for all the sub-widget's properties, actions, and
    emitters. In effect, this class can be used like a normal
    ``flx.Widget`` (but in Python).
    """

    _WidgetCls = Widget

    def __init__(self, *args, **kwargs):
        self._jswidget = None
        super().__init__(*args, **kwargs)

    def _comp_init_property_values(self, property_values):
        # This is a good place to hook up our sub-widget. It gets called
        # when this is the active component, and after the original
        # version of this has been called, everything related to session
        # etc. will work fine.

        # First extract the kwargs
        kwargs_for_real_widget = {}
        for name in list(property_values.keys()):
            if name not in self.__properties__:
                if name in self._WidgetCls.__properties__:
                    kwargs_for_real_widget[name] = property_values.pop(name)
        # Call original version, sets _session, amongst other things
        super()._comp_init_property_values(property_values)
        # Create widget and activate it
        w = self._WidgetCls(**kwargs_for_real_widget)
        self.__exit__(None, None, None)
        self._jswidget = w
        self.__enter__()
        # Copy all properties, actions and emitters
        for x in w.__properties__ + w.__actions__ + w.__emitters__:
            if not hasattr(self, x):
                setattr(self, x, getattr(w, x))
        # Handle implicit actions from settable properties
        for x in w.__properties__:
            x = "set_" + x
            if hasattr(w, x) and not hasattr(self, x):
                setattr(self, x, getattr(w, x))

    def __enter__(self):
        res = super().__enter__()
        if self._jswidget is not None:
            self._jswidget.__enter__()
        return res

    def __exit__(self, *args, **kwargs):
        if self._jswidget is not None:
            self._jswidget.__exit__(None, None, None)
        return super().__exit__(*args, **kwargs)
