Motivation
----------

The primary motivation for Flexx is the undeniable fact that the web
(i.e. browser technology) has become an increasingly popular method for
delivering applications to users, also for (interactive) scientific
content.

The purpose of Flexx is to provide a single application framework to
create desktop applications and web apps. By making use of browser
technology, the library itself can be relatively small and pure Python,
making it widely and easily available.

By making use of PScript (Python to JavaScript translation), the entire
library is written without (hardly) a line of JavaScript. This makes it easier
to develop than if we would have a corresponding "flexx.js" to maintain.
Further, it allows users to easily define callback methods that are
executed in JavaScript, allowing for higher performance when needed.

Libraries written for Python, but not *in* Python have a much harder
time to survive, because users don't easily become contributors. This
is one of the reasons of the success of e.g. scikit-image, while e.g. Mayavi
has a much harder time attracting developers. Since Flexx is written
in a combination of Python and PScript, its user community is more
likely to take an active role in its development.
