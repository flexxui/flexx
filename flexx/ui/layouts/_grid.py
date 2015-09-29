"""

"""

from ... import react
from . import Widget, Layout


class GridPanel(Layout):
    """ A panel which lays out its children in a grid. 
    
    For each column and each row, it looks at its children and selects
    the maximum flex, min_size and base_size, and the minimum max_size.
    
    If all flex factors are zero, all columns/rows become of equal size
    (subject to min_size and max_size).
    """
    
    @react.input
    def spacing(v=5):
        """ The space between two child elements. """
        return float(v)
    
    # todo: allow specifying flex, minSize etc. using an array of dicts?
    # @react.input
    # def col_specs(v=None):
    #     """ The specification for the columns. If None, uses the 
    #     """
    #     return v
    
    class JS:
        
        def _create_node(self):
            self.p = phosphor.gridpanel.GridPanel()
        
        # NOTE: if min/max size were signals
        # @react.connect('children.*.pos', 'children.*.flex', 'children.*.min_size', 'children.*.max_size', 'children.*.base_size')
        # def __update_positions(self):
        #     # Set position of all children and get how large our grid is
        #     max_row, max_col = 0, 0
        #     for child in self.children():
        #         x, y = child.pos()
        #         phosphor.gridpanel.GridPanel.setColumn(child.p, x)
        #         phosphor.gridpanel.GridPanel.setRow(child.p, y)
        #         max_col = max(max_col, x)
        #         max_row = max(max_row, y)
        #     
        #     # Collect specs from all children
        #     colSpecs = [{'stretch': 0, 'minSize': 0, 'maxSize': Infinity, 'sizeBasis': 0} for i in range(max_col+1)]
        #     rowSpecs = [{'stretch': 0, 'minSize': 0, 'maxSize': Infinity, 'sizeBasis': 0} for i in range(max_row+1)]
        #     for child in self.children():
        #         x, y = child.pos()
        #         minx, miny = child.min_size()
        #         maxx, maxy = child.max_size()
        #         maxx, maxy = maxx if maxx > 0 else Infinity, maxy if maxy > 0 else Infinity
        #         colSpecs[x].minSize = max(colSpecs[x].minSize, minx)
        #         colSpecs[x].maxSize = min(colSpecs[x].maxSize, maxx)
        #         colSpecs[x].sizeBasis = max(colSpecs[x].sizeBasis, child.base_size()[0])
        #         colSpecs[x].stretch = max(colSpecs[x].stretch, child.flex()[0])
        #         
        #         rowSpecs[y].minSize = max(rowSpecs[y].minSize, miny)
        #         rowSpecs[y].maxSize = min(rowSpecs[y].maxSize, maxy)
        #         rowSpecs[y].sizeBasis = max(rowSpecs[y].sizeBasis, child.base_size()[1])
        #         rowSpecs[y].stretch = max(rowSpecs[y].stretch, child.flex()[1])
        #     
        #     # Assign
        #     self.p._columnSpecs = colSpecs
        #     self.p._rowSpecs = rowSpecs
        #     Spec = phosphor.gridpanel.Spec
        #     self.p.columnSpecs = [Spec(i) for i in colSpecs]
        #     self.p.rowSpecs = [Spec(i) for i in rowSpecs]
        
        @react.connect('children.*.pos', 'children.*.flex', 'children.*.base_size')
        def __update_positions(self):
            self._child_limits_changed()
        
        # todo: the fact that we need this special hook method might be an indication that min/max size should be signals
        # todo: on the other hand, min/max size ARE style things, and are rarely set other than on the constructor.
        def _child_limits_changed(self):
            
            # Set position of all children and get how large our grid is
            max_row, max_col = 0, 0
            for child in self.children():
                x, y = child.pos()
                phosphor.gridpanel.GridPanel.setColumn(child.p, x)
                phosphor.gridpanel.GridPanel.setRow(child.p, y)
                max_col = max(max_col, x)
                max_row = max(max_row, y)
            
            # Collect specs from all children
            colSpecs = [{'stretch': 0, 'minSize': 0, 'maxSize': Infinity, 'sizeBasis': 0} for i in range(max_col+1)]
            rowSpecs = [{'stretch': 0, 'minSize': 0, 'maxSize': Infinity, 'sizeBasis': 0} for i in range(max_row+1)]
            for child in self.children():
                x, y = child.pos()
                limits = child.p.sizeLimits
                colSpecs[x].minSize = max(colSpecs[x].minSize, limits.minWidth)
                colSpecs[x].maxSize = min(colSpecs[x].maxSize, limits.maxWidth)
                colSpecs[x].sizeBasis = max(colSpecs[x].sizeBasis, child.base_size()[0])
                colSpecs[x].stretch = max(colSpecs[x].stretch, child.flex()[0])
                
                rowSpecs[y].minSize = max(rowSpecs[y].minSize, limits.minHeight)
                rowSpecs[y].maxSize = min(rowSpecs[y].maxSize, limits.maxHeight)
                rowSpecs[y].sizeBasis = max(rowSpecs[y].sizeBasis, child.base_size()[1])
                rowSpecs[y].stretch = max(rowSpecs[y].stretch, child.flex()[1])
            
            # Assign
            self.p._columnSpecs = colSpecs
            self.p._rowSpecs = rowSpecs
            Spec = phosphor.gridpanel.Spec
            self.p.columnSpecs = [Spec(i) for i in colSpecs]
            self.p.rowSpecs = [Spec(i) for i in rowSpecs]
        
        def _remove_child(self, widget):
            pass

        
        @react.connect('spacing')
        def __spacing_changed(self, spacing):
            self.p.rowSpacing = spacing
            self.p.columnSpacing = spacing
