# Docs for new Model class - now called Component

This document is intended to give a complete understanding of how the Flexx
``Component`` classes are used. You might also need the API docs to
learn how to write things down exactly, though all relevant concepts
should be covered here.

This is not a particularly short text, but it does (should) cover
everything. We try to be gentle by starting with an introduction and
an example that cover the most important bits.


## Introduction

To understand how components work, there are four main concepts to understand:
1) a component is either a ``PyComponent`` or a ``JSComponent``, i.e. defining
behavior for server or client; 2) a component has state in the form of
(read-only) properties, which are synchronised to JS/Python;
3) a component can have "actions" to mutate the state; 4) a component can have
"reactions" to keep the application up-to-date with the current state
and react to (user) events.

```
                                                    Events
                                                      \
Actions                     -->  State         -->  Reactions
(do work and mutate state)       (properties)       (make app reflect the state)
```

The ``Component`` classes promote a certain information flow: it starts with an
action, which generally modifies properties. The combination of state
mutations caused by one action should be seen as a single transition
to a new state. These mutations lead to reactions that e.g. change the
(visual) representation. All reactions to the state-change caused by
the initiating action are handled *before* the system starts handling
the next action. During this time, the state cannot change. This applies
to all parts of your application, from the level of widgets to high
level application state.

If this seems complicated or confusing at first, don't worry, in most cases it
Just Works, and you don't have to think too much about it. Actions and
reactions are nothing more than methods of a component class.


## A simple example


```py
class DrawingWidget(flexx.JSComponent):
    
    points = prop([], doc='The drawn points')
    color = prop('red', doc='Color of new points')
    
    def init(self):
        self.label = ui.Label()
        self.canvas = ui.Canvas()
        ...
    
    @action
    def add_point(self, x, y, color):
        """An action to mutate the points property by appending a point."""
        point = x, y, color
        self._set_prop('points', points + [point])  # this is a mutation
    
    @reaction
    def _update_label(self):
        """A reaction to keep the label up-to-date."""
        self.label.set_text('Drawing in ' + self.color)
    
    @reaction
    def _draw_points(self):
        """An action to react to changes in state by (re)drawing the points,
        using fictive _clear() and _draw_point() methods."""
        self._clear()
        clr = self.color
        for p in self.points:
            self._draw_point(*p)
```

In the above example, the three aspects of action, state and reaction
are all used. Note that an action *can* be called from a reaction, which will
cause the action to be invoked asynchronously. Its mostly that you cannot call
``_set_prop()`` and other mutator methods inside a reaction. More on that later.


## Python or JavaScript

The component classes that you use and write inherit (directly or
indirectly) either from ``PyComponent`` or ``JSComponent``, which define where
the app "operates".

A py-component is always instantiated in Python, and can be
associated with a session (more than one, actually, as we'll see later),
where it will have a representation; from JS its properties can be observed,
and its actions invoked (which will then run in Python).

A js-component can be instantiated in JS, in which case the object only
lives in JS, and can thus only be used from JS. When it is instantiated
in Python, the object has a representation in both JS and Python; from
both sided its state can be observed and actions invoked (which will then
run in JS).

While we're on the subject of instantiation, any component class can have
an ``init()`` method, which should generally be used as an alternative to
`__init__`, since the former is called at a better moment in the component's
initialisation procedure.


## State / properties

State is represented as properties. These are readonly and can only be
changed using private mutation functions (see below). This might seem
restrictive, but this keeps the flow of information unidirectional,
which leads to more predictability and less bugs.

```py
class MyModel(flexx.PyComponent):
    
    foo = prop('', doc='An example prop')
    bar = prop(42, doc='Another example prop')
```


### Array and dict properties

Normal properties can have any value (as long as it can be serialized). For
properties that represent large data, performance can become an issue though.
Therefore, Flexx provides a variety of properties:

* `prop(initial, doc)`: a generic property that can take on any value
* `array_prop(initial, type, doc)`:  an array, optionally typed, can efficiently be updated and synchronized.
* `dict_prop(initial, doc)`: a dictionary that can be updated in-place.

The ``array_prop``, for instance, can be mutated by adding/inserting/removing one or more
items. Reaction functions can listen for these specific mutations and thereby act in a more
efficient way.

### Mutations

Properties can (and in the case of `array_prop` and `dict_prop` *should*) only
be changed via the mutator functions:
    
* `_set_prop(name, value)` can be used to update a property as a whole.
* For the `dict_prop` one can also use `_merge_prop(name, a_dict)`.
* For the `array_prop` one can use `_push_prop(name, start, data)`, `_remove_prop(name, start, count)`,
  `_update_prop(name, start, data)`, where `data` is a list/array of data.

As mentioned earlier, these mutation functions should/can only be called from actions.

For efficiently applying changes with large data from Python, it is
possible to register a "pending mutation". E.g. a `set_data()` method
in Python would register a pending mutation together with invoking an
action that updates the data at the JS side. The action (plus data) is transported
to JavaScript, where the mutation takes place. If the registered
mutation is valid (not outdated), JS sends back a small acknowledge
message instead of syncing the whole data.

TODO: the above assumes that we can define methods on the Python side of a
`JSComponent` class. Not sure yet how to do this, but it might make sense for special
cases.


## Actions

Actions are special methods that can be invoked by calling them. 
Normally, the actual function is not called right away but in a future
iteration of the event loop, i.e. asynchronous, and therefore
thread-safe. Actions that are called from other actions *are* invoked
directly unless the implementation is on the other side (Python/JS).

Actions are implemented on either the Python and JS side (depending on whether
ist a py-component or js-component), though can be invoked from both
the Python and JS side, as long as the arguments are serializable.

Actions are defined by decorating a method with `@action`:

```py
class DrawinApp(ui.Widget):
    
    points = prop([], doc='The drawn points')
    color = prop('red', doc='Color of new points')
    
    @action
    def add_point(self, x, y, color):
        point = x, y, color
        self._set_prop('points', points + [point])
```

### Setter actions

In a lot of cases, it makes sense for property `foo` to have a
corresponding action `set_foo` action. Therefore, as a convenience
feature, one can define a property as "settable" to let Flexx create
the action:

```py
    color = prop('red', settable=str, doc='Color of new points')
```

The value of ``settable`` can be a type/function that is used to normalize/validate the given value.

Nevertheless, sometimes it makes sense to write actions explicitly, for instance to
do more validation of the input value, or to provide additional means
to mutate a property (e.g. ``set_priority()`` and ``increase_priority()``):

```py
    @action
    set_color(self, value):
        if value not in ('red', 'green', 'blue'):
            raise ValueError('Only primary color allowed.')
        self._set_prop('color', value)
        # ... or maybe simply like this?
        self.color = value
```

Note that since actions are asynchronous, calling `set_foo()` from a
reaction will only have effect in a next iteration of the event loop.
This is deliberate; it keeps the flow of information clear. It is also
the reason why properties can not be set via `ob.foo = 'hello'`.


## Reactions

You should think of your app as always being in a certain state, when
that state changes, certain parts of your apps should react to reflect
the new state. Ideally, it should be possible to apply a certain state to an app,
and always have the same predictable outcome.

Reactions are defined by decorating a method with `@reaction`:

``` py
class DrawinApp(ui.Widget):

    points = prop([], doc='The drawn points')
    color = prop('red', doc='Color of new points')

    @reaction
    def _update_label(self):
        self.label.set_text('Drawing in ' + self.color)
    
    @reaction
    def _draw_points(self):
        """Draw the points, using fictive _clear() and _draw_point() methods."""
        self._clear()
        for p in self.points:
            self._draw_point(*p)
```

Reaction functions are automatically called when any of the properties that are
used during the function call is updated. 
The way that this works is that the property getters keep track of their use,
so that after each call, we know what properties the function depends on.
The dependencies of the function are dynamically tracked, so in the
following example, the function would update its dependencies when
`self.children` changes:

``` py
   @react
   def xx(self):
        text = ', '.join([x.text for x in self.children])
        self.set_summary(text)
```

### Explicit form actions

Your app must usually act on events such as user interaction. This
is done by reactions too, but written in "explicit form":

```py
@reaction('button.mouse_click')
def _update_stuff(self, ev):
    if ev.button == 1:
        ...
```

The explicit form can also be used to react to mutations, in which case
they can be handled individually. This can be convenient to target
certain mutations precisely, e.g. keeping track of changing
properties of multiple components without having to iterate over them.
Or for effectively keeping track of `array_prop` and `dict_prop` by
"replicating" the mutations instead of resetting the data as a whole:

```py
@reaction('points')
def _draw_points(self, *events):
    for ev in events:
        if ev.method == 'push':
            for point in ev.data:
                self._draw_point(*point)
        elif ev.method == 'set':
            ...
```

The mutation objects have a ``type`` attribute that matches the property
name, a ``method`` attribute that matches the kind of mutation, and
have attributes matching with each ot the parameters of the
corresponding mutation function.


### In-line reactions

Reactions can be written in just one line of code while initializing a
component. This helps keeping your code compact and declarative. The color
label example above could thus also be written as:

```py
        ui.Label(text=lambda:'Drawing in ' + self.color)
```

To be precise, the lambda is a reaction and its return value is fed to the
``set_text()`` action.

Similarly, reactions can be associated with an event in a one-liner:

```
        ui.Button(text='Submit', on_mouse_click=lambda ev: self.submit())
```

To be precise, the lambda is a reaction that invokes the ``submit()`` action.


### Computed properties

As an extension of reaction functions, one can also define computed properties.
These are properties that do not directly correspond to state, but are derived
from it:

``` py
    @computed
    def full_name(self):
        return self.first_name + ' ' + self.last_name
```



## Event emitters

Above, we've covered how to react to events such as mouse clicks. These
events are generated from event emitters. Typically, these only need to be implemented
on widgets that allow a form of user interaction. Emitters are implemented by decorating
a function with ``@emitter``:
    
```py
class Button(Widget):
    
    class JS:
        
        @emitter
        def mouse_click(self, native_event):
            return {...}
```

Emitters behave like functions, and can have input arguments. It should return a
dictionary object to represent the event, and the event object should be described
in the docstring. In this case the emitter converts the native JS mouse event to
a (simpler) Flexx event.


## Sharing a PyComponent

The ``PyComponent`` class can be instantiated at any time; and is associated
with a session when it is set as an attribute on another py-component.
In this way it is possible to associate it with *multiple*
sessions, which offers some interesting mechanics, such as providing
a shared state between clients, e.g. for a chat application.


## Tips

When writing a higher level widget with subwidgets, consider what the
"application state" of your component is, and represent that with
properties; avoid using properties of subcomponents to manage such
state.

In deciding whether a function should be an action or a reaction, consider whether
what you're writing represents a certain "action" that ought to cause a mutation in
state, or whether it is something to make your app reflect (i.e. react to) the current state.


## Simple example, more complete

The example below is an extended version of the example at the start of this document:

* It adds a ``DrawingApp`` class, which inherits from ``PyComponent``, which
  represents the app and operates in Python.
* This new class has actions to save and restore the points.
* It makes use of ``array_prop`` to represent the points, so that when a point
  is added, the mutation to sync to the server is just a small message.
* Also, the above allows more efficient drawing when points are only added.
* It demonstrates explicit form reactions.
* It makes use of in-line reactions.


```py

class DrawingApp(flexx.PyComponent):
    
    def init(self):
        self.view = DrawingWidget()
    
    @action
    def save(self):
        """Save the currently drawn points at the server."""
        s = json.dumps(self.view.points)
        with open('~/points.json', 'wt') as f:
            f.write(s)
    
    @action
    def load(self):
        """Load the currently drawn points from the latest save point."""
        s = open('~/points.json', 'rt').read()
        self.view.set_points(json.loads(s))  # invoke action set_points


class DrawingWidget(ui.Widget):
    
    points = array_prop(settable=True, doc='The drawn points')
    color = prop('red', doc='Color of new points')

    def init(self):
        ui.Label(text=lambda:'Drawing in ' + self.color)
        self.canvas = ui.Canvas(on_mouse_click=lambda ev: self.add_point(ev.x, ev.y, self.color))
        ...
    
    @action
    def add_point(self, x, y, color):
        point = x, y, color
        self._push_prop('points', None, [point])
    
    # Instead of the inline acion above, this would also work:
    #@reaction('canvas.mouse_click')
    #def _add_point_from_click(self, ev):
    #    self.add_point(ev.x, ev.y, self.color)
    
    @reaction('points')
    def _draw_points(self, *events):
        """Draw the points, using fictive _clear() and _draw_point() methods."""
        for ev in events:
            if ev.method == 'push':
                assert ev.start is None  # only appends, not insert
                for point in ev.data:
                    self._draw_point(*point)
            elif ev.method == 'set':
                self._clear()
                for point in self.points:
                    self._draw_point(*point)
            else:
                    raise RuntimeError('was only expecting set and push mutations.')
```



## Programming patterns

This section describes how you can keep your app easy to maintain as
it grows by providing three examples. The exact way depends on the
use-case, but the main point is to separate "drawing code" from
application logic, and to implement high-level application logic in a
central place. Web apps tend to have more js-components, whereas desktop
apps might have more py-components.

### A silly app component

In the first example, we write a component of an app that displays the
username. It also implements an action to perform a login (the details
of the login process are not interesting for this example). On sucess,
a label text is updated to display the username.

```py
class SomeWidget(ui.Widget):
    
    def init(self):
        self.username_label = ui.Label()
    
    @action
    def login(self, username):
        success = self.try_login(username)
        if success:
            self.username_label.set_text(username)
...

This could work, but becomes annoying when the username is used in other places,
or when the login action is implemented on another component; other parts of your
app must then be aware of the `username_label`, and that makes things hard to maintain.
Actually, its good practice to use private attribute names for sub components.


### A better app component

The above can be improved by defining a property to hold the username. That way,
the username is more clearly seen as "application state" rather than local state related
to the view.


```py
class SomeWidget(ui.Widget):
    
    username = prop('', settable=str)
        
    def init(self):
        ui.Label(text=lambda: self.username)
    
    @action
    def login(self, username):
        success = self.try_login(username)
        if success:
            self.set_username(username)
...

A nice side effect is that all code related to the label is constrained to a
single line and we don't even have to give the label a name. The login action
is also easier to read because ``set_username()`` has semantic meaning. As your
app grows, however, the login procedure might be implemented in a different place,
or there might be more ways to set the username, and in all places you'd need
a reference to this component in order to store the username.


### The Elm architecture

In the Elm architecture, you keep track of (most) state in a central place.
Flexx provides a means to implement this pattern via the ``root`` component,
which represents the main/central component of the application.

```py

class MyApp(ui.Widget):
    
    username = prop('', settable=str)
    
    def init(self):
        
        # Somewhere, maybe here, but maybe as a subwidget of a subwidget:
        SomeWidget()

class SomeWidget(ui.Widget):
    
    class JS:
        
        def init(self):
            ui.Label(text=lambda: self.root.username)

class SomeOtherWidget(ui.Widget):
    
    @action
    def login(self, username):
        success = self.try_login(username)
        if success:
            self.root.set_username(username)
...

Now, this does not mean that all state should be put at the root
application component, but things that apply to the whole app are certainly
easier to manage when they are stored in a central place.

A hybrid form is also possible, where a component keep a reference to another
component which acts as a model to store state:

```py
class SomeWidget(ui.Widget):
    
    def init(self, given_model):
        self.given_model = given_model
    
    def init(self):
        ui.Label(text=lambda: self.given_model.username) 
```
