"""

"""

from ... import react
from . import Widget, Layout


class GridPanel(Layout):
    """ A panel which lays out its children in a grid. 
    
    For each column and each row, the flex factor is determined by
    taking the average of all child widgets in that column/row. If all
    flex factors are zero, all columns/rows become of equal size.
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
        
        @react.connect('children.*.pos', 'children.*.flex')
        def __update_positions(self):
            # Set position of all children and get how large our grid is
            max_row, max_col = 0, 0
            for child in self.children():
                x, y = child.pos()
                phosphor.gridpanel.GridPanel.setColumn(child.p, x)
                phosphor.gridpanel.GridPanel.setRow(child.p, y)
                max_col = max(max_col, x)
                max_row = max(max_row, y)
            
            # Collect specs from all children
            # todo: also collect min-size, max-size and pref-size
            colSpecs = [{'stretch': 0, 'count': 0} for i in range(max_col+1)]
            rowSpecs = [{'stretch': 0, 'count': 0} for i in range(max_row+1)]
            for child in self.children():
                x, y = child.pos()
                fx, fy = child.flex()
                colSpecs[x].stretch += fx
                colSpecs[x].count += 1
                rowSpecs[y].stretch += fy
                rowSpecs[y].count += 1
            
            # Averaging
            for i in range(len(colSpecs)):
                if colSpecs[i].count:
                    colSpecs[i].stretch /= colSpecs[i].count
                del colSpecs[i].count
            for i in range(len(rowSpecs)):
                if rowSpecs[i].count:
                    rowSpecs[i].stretch /= rowSpecs[i].count
                del rowSpecs[i].count
            
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
