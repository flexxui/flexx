---------
Debugging
---------

Debugging can be hard. Especially if your app runs partly in Python and partly
in JavaScript. Here are some tips that may help.


Be clear about where the offending code is running
--------------------------------------------------

This may sound obvious, but it's important to do this before moving on.
Sometimes the bug presents itself due to the interaction between Python
and JavaScript. The same rules apply, but you'd have to dig into both ends.


Digging in the Python side
--------------------------

All the normal Python debugging tips apply here. GUI applications run in
an event loop, which makes debugging harder. E.g. using breakpoints is not
always possible. A strategically placed ``print()`` can sometimes help a lot.

It can be worthwhile to run the app in an IDE that can integrate the
event loop, so that you can use a Python REPL to inspect an application
while it is running. E.g. with `Pyzo <http://pyzo.org>`_ with asyncio GUI integration.


Digging in the JavaScript side
------------------------------

People unfamiliar with web technology might be hesitant to try and debug
using the browser, but you'll be amazed by how awesome the debugging tools
of Firefox and Chrome are!

Firstly, hit the  F12 key to pop up the developer console. From here, there
are a few things that you can do:
    
You can run JavaScript commands to inspect and control your app. There
is a global ``flexx`` object, and you can get access to all components
using ``flexx.s1.instances.xxx``. Use autocompletion to select the
component you need. You can inspect the component's properties and
invoke its actions.

If the problem is related to appearance, you can activate the element selector
and then click on the element on the page to select it. This will allow you
to inspect the HTML DOM structure and inspect the CSS of all elements.


End
---

This concluses the Flexx guide. Have fun!
