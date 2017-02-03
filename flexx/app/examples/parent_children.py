"""
This example demonstrates a parent-children relationship for nodes,
that gets synced between Python and JS. This is basically a
stripped-down version of what is used in the Widget class.

The idea is to make the "parent" and "children" properties available
in both Python and JS. However, if they were both synced, we would get
an infinite loop. Therefore the parent property is added as a "local"
property to both Py and JS, using a common validator function.
"""

from flexx import event, app


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


class Node(app.Model):
    
    parent = event.prop(parent)
    
    @event.connect('parent')
    def on_parent(self, *events):
        parent = events[-1].new_value
        parent_id = 'None' if parent is None else parent._id
        print('parent of %s changed to %s in Py' % (self._id, parent_id))
    
    class Both:
        
        # cannot define parent prop here; it would result in an infinite loop
        
        @event.prop
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
    
    class JS:
        
        parent = event.prop(parent)
        
        @event.connect('parent')
        def on_parent(self, *events):
            parent = events[-1].new_value
            parent_id = 'None' if parent is None else parent._id
            print('parent of %s changed to %s in JS' % (self._id, parent_id))


n1 = app.launch(Node, 'app')

# Create other nodes in context of n1, so they share the same session
with n1:
    n2 = Node()
    n3 = Node()

# This is intended to be run interactively (e.g. in Pyzo), so that you
# change the parent-children relationships dynamically.
