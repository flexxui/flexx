----------------------
Widgets and components
----------------------

The app module implements the connection between Python and JavaScript.
It runs a web server and websocket server based on Tornado, provides
an asset (and data) management system, and provides the
:class:`PyComponent <flexx.app.PyComponent>` and
:class:`JsComponent <flexx.app.JsComponent>` classes, which form the
basis for e.g. Widgets.

PyComponent and JsComponent
---------------------------

A Flexx application consists of components that exist in either Python or
JavaScript, and which can communicate with each-other in a variety of ways.

The :class:`PyComponent <flexx.app.PyComponent>` and
:class:`JsComponent <flexx.app.JsComponent>` classes derive from the
:class:`Component <flexx.event.Component>` class (so learn about that one first!).
What sets ``PyComponent`` and ``JsComponent`` apart is this:

* They are associated with a :class:`Session <flexx.app.Session>`.
* They have an ``id`` attribute that is unique within their session,
  and a ``uid`` attribute that is globally unique.
* They live (i.e. their methods run) in Python and JavaScript, respectively.
* A ``PyComponent`` can only be instantiated in Python, a ``JsComponent`` can
  be instantiated in both Python and JavaScript.
* A ``PyComponent`` always has a corresponding proxy object in JavaScript.
* A ``JsComponent`` *may* have a proxy object in Python; these proxy objects
  are created automatically when Python references the component.


Proxy components
----------------

The proxy components allow the "other side" to inspect properties, invoke
actions and connect to events. The real component is aware of what events
the proxy reacts to, and will only communicate these events.


An example:

.. code-block:: py

    from flexx import app, event

    class Person(app.JsComponent):  # Lives in Js
        name = event.StringProp(settable=True)
        age = event.IntProp(settable=True)

        @event.action
        def increase_age(self):
            self._mutate_age(self.age + 1)

    class PersonDatabase(app.PyComponent):  # Lives in Python
        persons = event.ListProp()

        @event.action
        def add_person(self, name, age):
            p = Person(name=name, age=age)
            self._mutate_persons([p], 'insert', 99999)

        @event.action
        def new_year(self):
            for p in self.persons:
                p.increase_age()


In the above code, the ``Person`` objects live in JavaScript, while a
database object that keeps a list of them lives in Python. In practice,
the ``Person`` components will e.g. have a visual representation in the
browser. The database could also have been a ``JsComponent``, but let's
assume that we need it in Python because it synchronizes to a mysql
database or something.

We can observe that the ``add_person`` action (which executes in Python)
instantiates new ``Person`` objects. Actually, it instantiates proxy objects that
automatically get corresponding (real) ``Person`` objects in JavaScript.
The ``new_year`` action executes in Python, which in turn invokes the ``increase_age``
action of each person, which execute in JavaScript.

It is also possible for JavaScript to invoke actions of ``PyComponents``. For
the example above, we would have to get the
database object into a JsComponent. For example:


.. code-block:: py

    class Person(app.JsComponent):
        ...
        def init(self, db):
            self.db = db
            # now we can call self.db.add_person() from JavaScript!

    ...

    # To instantiate ...
    Person(database, name=name, age=age)

Another useful feature is that each component has a ``root`` attribute that
holds a reference to the component representing the root of the application.
E.g. if the root is a ``PersonDatabase``, all ``JsComponent`` objects have a
reference to (a proxy of) this database.

Note that ``PyComponents`` can instantiate ``JsComponents``, but not the other
way around.


Local properties
----------------

Regular methods of a ``JsComponent`` are only available in JavaScript. On the
other hand, all properties are available on the proxy object as well. This may
not always be useful. It is possible to create properties that are local
to JavaScript (or to Python in a ``PyComponent``) using ``app.LocalProp``.
An alternative may be to use ``event.Attribute``; these are also local
to JavaScript/Python.
