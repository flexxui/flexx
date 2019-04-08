----------------------
Widgets are components
----------------------

Widgets are what we call "components", which are a central
part of the event system. They are what allows widgets to have properties
and react to things happening in other parts of the application. But
let's not get ahead of ourselves; the event system is dicsussed in the
next chapter.

For the moment, it's enough to know that the :class:`Widget <flexx.ui.Widget>`
class is kind of :class:`JsComponent <flexx.app.JsComponent>`.
This means that these widgets live in JavaScript. But the cool
thing is that you can use widget objects in Python, by setting their properties,
invoking their actions, and reacting to their state. This is possible because
of so-called proxy objects.

We mentioned earlier that the :class:`PyWidget <flexx.ui.PyWidget>` can be used to
create widgets that live in Python: these are a kind of :class:`PyComponent <flexx.app.PyComponent>`.
It's good to understand the difference between these kinds of classes.


PyComponent and JsComponent
---------------------------

A Flexx application consists of components that exist in either Python or
JavaScript, and which can communicate with each-other in a variety of ways.

The :class:`PyComponent <flexx.app.PyComponent>` and
:class:`JsComponent <flexx.app.JsComponent>` classes derive from the
:class:`Component <flexx.event.Component>` class (which is a topic of the next chapter).
The most important things to know about ``PyComponent`` and ``JsComponent``:

* They are both associated with a :class:`Session <flexx.app.Session>`.
* They have an ``id`` attribute that is unique within their session,
  and a ``uid`` attribute that is globally unique.
* They live (i.e. their methods run) in Python and JavaScript, respectively.
* A ``PyComponent`` can only be instantiated in Python, a ``JsComponent`` can
  be instantiated in both Python and JavaScript.
* A ``PyComponent`` always has a corresponding proxy object in JavaScript.
* A ``JsComponent`` *may* have a proxy object in Python; these proxy objects
  are created automatically when Python references the component.

In practice, you'll use ``PyComponents`` to implement Python-side behavior,
and ``JsComponents`` (e.g. Widgets) for the behavior in JavaScript. Flexx
allows a variety of ways by which you can tie Python and JS together, but
this can be a pitfall. It's important to think well about what parts of your
app operate in JavaScript and what in Python. Patterns which help you do this
are discussed later in the guide.


Proxy components
----------------

The proxy components allow the "other side" to inspect properties, invoke
actions and connect to events. The real component is aware of what events
the proxy reacts to, and will only communicate these events.

The example below may be a bit much to digest. Don't worry about that.
In most cases things should just work.

.. code-block:: py

    from flexx import flx

    class Person(flx.JsComponent):  # Lives in Js
        name = flx.StringProp(settable=True)
        age = flx.IntProp(settable=True)

        @flx.action
        def increase_age(self):
            self._mutate_age(self.age + 1)

    class PersonDatabase(flx.PyComponent):  # Lives in Python
        persons = flx.ListProp()

        @flx.action
        def add_person(self, name, age):
            p = Person(name=name, age=age)
            self._mutate_persons([p], 'insert', 99999)

        @flx.action
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

    class Person(flx.JsComponent):
        ...
        def init(self, db):
            self.db = db
            # now we can call self.db.add_person() from JavaScript!

    ...

    # To instantiate ...
    Person(database, name=name, age=age)




The root component
------------------

Another useful feature is that each component has a ``root`` attribute that
holds a reference to the component representing the root of the application.
E.g. if the root is a ``PersonDatabase``, all ``JsComponent`` objects have a
reference to (a proxy of) this database.


Next
----

Next up: :doc:`The event system <event_system>`.
