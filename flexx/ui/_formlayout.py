"""
Example:

.. UIExample:: 200
    
    from flexx import ui
    
    class Example(ui.Widget):
        def init(self):
            with ui.FormLayout():
                ui.Label(text='Pet name:')
                self.b1 = ui.Button(text='...')
                ui.Label(text='Pet Age:')
                self.b2 = ui.Button(text='...')
                ui.Label(text="Pet's Favorite color:")
                self.b3 = ui.Button(text='...')
                ui.Widget(flex=1)
"""

from .. import react
from . import Widget, Layout


class BaseTableLayout(Layout):
    """ Abstract base class for layouts that use an HTML table.
    
    Layouts that use this approach are rather bad in performance when
    resizing. This is not so much a problem when it is a leaf layout,
    but we don't recommend embedding such layouts in each-other.
    """
    
    CSS = """
    
    /* Clear any styling on this table (rendered_html is an IPython thing) */
    .flx-basetablelayout, .flx-basetablelayout td, .flx-basetablelayout tr,
    .rendered_html .flx-basetablelayout {
        border: 0px;
        padding: initial;
        margin: initial;
        background: initial;
    }
    
    /* Behave well inside hbox/vbox, 
       we assume no layouts to be nested inside a table layout */
    .flx-hbox > .flx-basetablelayout {
        width: auto;
    }
    .flx-vbox > .flx-basetablelayout {
        height: auto;
    }

    /* In flexed cells, occupy the full space */
    td.vflex > .flx-widget {
        height: 100%;
    }
    td.hflex > .flx-widget {
        width: 100%;
    }
    """
    
    class JS:
        
        def _apply_table_layout(self):
            table = self.node
            AUTOFLEX = 729  # magic number unlikely to occur in practice
            
            # Get table dimensions
            nrows = len(table.children)
            ncols = 0
            for i in range(len(table.children)):
                row = table.children[i]
                ncols = max(ncols, len(row.children))
            if ncols == 0 and nrows == 0:
                return
            
            # Collect flexes
            vflexes = []
            hflexes = []
            for i in range(nrows):
                row = table.children[i]
                for j in range(ncols):
                    col = row.children[j]
                    if (col is undefined) or (len(col.children) == 0):
                        continue
                    vflexes[i] = max(vflexes[i] or 0, col.children[0].vflex or 0)
                    hflexes[j] = max(hflexes[j] or 0, col.children[0].hflex or 0)
            
            # What is the cumulative "flex-value"?
            cum_vflex = vflexes.reduce(lambda pv, cv: pv + cv, 0)
            cum_hflex = hflexes.reduce(lambda pv, cv: pv + cv, 0)
            
            # If no flexes are given; assign each equal
            if (cum_vflex == 0):
                for i in range(len(vflexes)):
                    vflexes[i] = AUTOFLEX
                cum_vflex = len(vflexes) * AUTOFLEX
            if (cum_hflex == 0):
                for i in range(len(hflexes)):
                    hflexes[i] = AUTOFLEX
                cum_hflex = len(hflexes) * AUTOFLEX
            
            # Assign css class and height/weight to cells
            for i in range(nrows):
                row = table.children[i]
                row.vflex = vflexes[i] or 0  # Store for use during resizing
                for j in range(ncols):
                    col = row.children[j];
                    if (col is undefined) or (col.children.length is 0):
                        continue
                    self._apply_cell_layout(row, col, vflexes[i], hflexes[j], cum_vflex, cum_hflex)
        
        @react.connect('real_size')
        def _adapt_to_size_change(self, size):
            """ This function adapts the height (in percent) of the flexible rows
            of a layout. This is needed because the percent-height applies to the
            total height of the table. This function is called whenever the
            table resizes, and adjusts the percent-height, taking the available 
            remaining table height into account. This is not necesary for the
            width, since percent-width in colums *does* apply to available width.
            """
            table = self.node  # or event.target
            #print('heigh changed', event.heightChanged, event.owner.__id)
            
            if not self.real_size.last_value or (self.real_size.value[1] !=
                                                 self.real_size.last_value[1]):
                
                # Set one flex row to max, so that non-flex rows have their
                # minimum size. The table can already have been stretched
                # a bit, causing the total row-height in % to not be
                # sufficient from keeping the non-flex rows from growing.
                for i in range(len(table.children)):
                    row = table.children[i]
                    if (row.vflex > 0):
                        row.style.height = '100%'
                        break
                
                # Get remaining height: subtract height of each non-flex row
                remainingHeight = table.clientHeight
                cum_vflex = 0
                for i in range(len(table.children)):
                    row = table.children[i]
                    cum_vflex += row.vflex
                    if (row.vflex == 0) and (row.children.length > 0):
                        remainingHeight -= row.children[0].clientHeight
                
                # Apply height % for each flex row
                remainingPercentage = 100 * remainingHeight / table.clientHeight
                for i in range(len(table.children)):
                    row = table.children[i]
                    if row.vflex > 0:
                        row.style.height = round(row.vflex / cum_vflex * remainingPercentage) + 1 + '%'
        
        def _apply_cell_layout(self, row, col, vflex, hflex, cum_vflex, cum_hflex):
            raise NotImplementedError()



class FormLayout(BaseTableLayout):
    """ A form layout organizes pairs of widgets vertically.
    
    Note: the API may change. maybe the label can be derived from the
    widgets' ``title`` property?
    """
    
    CSS = """
    .flx-formlayout > tr > td > .flx-label {
        text-align: right;
    }
    """
    
    class JS:
        
        def _create_node(self):
            this.node = document.createElement('table')
            this.node.appendChild(document.createElement('tr'))
        
        def _add_child(self, widget):
            # Get row, create if necessary
            row = this.node.children[-1]
            itemsInRow = row.children.length
            if itemsInRow >= 2:
                row = document.createElement('tr')
                self.node.appendChild(row)
            # Create td and add widget to it
            td = document.createElement("td")
            row.appendChild(td)
            td.appendChild(widget.node)
            #
            self._update_layout()
            self._apply_table_layout()
            # do not call super!
        
        def _update_layout(self):
            """ Set hflex and vflex on node.
            """
            i = 0
            for widget in self.children():
                i += 1
                widget.node.hflex = 0 if (i % 2) else 1
                widget.node.vflex = widget.flex()
            self._apply_table_layout()
        
        def _remove_child(self, widget):
            pass
            # do not call super!
        
        def _apply_cell_layout(self, row, col, vflex, hflex, cum_vflex, cum_hflex):
            AUTOFLEX = 729
            className = ''
            if (vflex == AUTOFLEX) or (vflex == 0):
                row.style.height = 'auto'
                className += ''
            else:
                row.style.height = vflex * 100 / cum_vflex + '%'
                className += 'vflex'
            className += ' '
            if (hflex == 0):
                col.style.width = 'auto'
                className += ''
            else:
                col.style.width = '100%'
                className += 'hflex'
            col.className = className


class GridLayout(BaseTableLayout):
    """ Not implemented.
    
    Do we even need it? If we do implement it, we need a way to specify
    the vertical flex value.
    """
