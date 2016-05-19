"""
This example demonstrates a parent-children relationship for nodes,
that gets synced between Python and JS. This is basically a
stripped-down version of what is used in the Widget class.

The idea is to implement the "parent" and "children" properties using
the "both" flag, so that the same implementation is used in Python and
JavaScript. Then we disable syncing of parent, so that the syncing
happens via the children property only, otherwiser we end up with
infinite loops.
"""

from flexx import event, app


class Node(app.Model):
    
    @event.prop(both=True, sync=False)
    def parent(self, new_parent=None):
        old_parent = self.parent
        
        if old_parent is not None:
            children = list(old_parent.children if old_parent.children else [])
            while self in children:
                children.remove(self)
            old_parent.children = children
        if new_parent is not None:
            children = list(new_parent.children if new_parent.children else [])
            children.append(self)
            new_parent.children = children
        
        return new_parent
    
    @event.prop(both=True)
    def children(self, new_children=()):
        old_children = self.children
        if not old_children:  # Can be None during initialization
            old_children = []
        
        for child in old_children:
            if child not in new_children:
                child.parent = None
        for child in new_children:
            if child not in old_children:
                child.parent = self
        
        return tuple(new_children)
    
    def on_parent(self, *events):
        parent = events[-1].new_value
        parent_id = 'None' if parent is None else parent._id
        print('parent of %s changed to %s in Py' % (self._id, parent_id))
    
    
    class JS:
        
        def on_parent(self, *events):
            parent = events[-1].new_value
            parent_id = 'None' if parent is None else parent._id
            print('parent of %s changed to %s in JS' % (self._id, parent_id))


n1 = app.launch(Node, 'xul')

# Create other nodes in context of n1, so they share the same session
with n1:
    n2 = Node()
    n3 = Node()

# This is intended to be run interactively (e.g. in Pyzo), so that you
# change the parent-children relationships dynamically.
