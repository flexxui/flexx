"""
Example:

.. UIExample:: 200
    
    from flexx import ui
    
    class Example(ui.Widget):
        def init(self):
            with ui.FormLayout():
                self.b1 = ui.LineEdit(title='Name:')
                self.b2 = ui.LineEdit(title="Age:")
                self.b3 = ui.LineEdit(title="Favorite color:")
                ui.Widget(flex=1)
"""

from ... import event
from ...pyscript import window, undefined
from . import Layout


class BaseTableLayout(Layout):
    """ Abstract base class for layouts that use an HTML table.
    
    Layouts that use this approach don't have good performance when
    resizing. This is not so much a problem when it is used as a leaf
    layout, but we don't recommend embedding such layouts in each-other.
    """
    
    CSS = """
    
    /* Clear any styling on this table (rendered_html is an IPython thing) */
    .flx-BaseTableLayout, .flx-BaseTableLayout td, .flx-BaseTableLayout tr,
    .rendered_html .flx-BaseTableLayout {
        border: 0px;
        padding: initial;
        margin: initial;
        background: initial;
    }
    
    /* Behave well inside hbox/vbox, 
       we assume no layouts to be nested inside a table layout */
    .flx-hbox > .flx-BaseTableLayout {
        width: auto;
    }
    .flx-vbox > .flx-BaseTableLayout {
        height: auto;
    }
    
    td.flx-vflex, td.flx-hflex {
        padding: 1px;
    }
    
    /* In flexed cells, occupy the full space */
    td.flx-vflex > .flx-Widget {
        height: 100%;
    }
    td.flx-hflex > .flx-Widget {
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
                    col = row.children[j]
                    if (col is undefined) or (col.children.length is 0):
                        continue
                    self._apply_cell_layout(row, col, vflexes[i], hflexes[j],
                                            cum_vflex, cum_hflex)
        
        @event.connect('size')
        def _adapt_to_size_change(self, *events):
            """ This function adapts the height (in percent) of the flexible rows
            of a layout. This is needed because the percent-height applies to the
            total height of the table. This function is called whenever the
            table resizes, and adjusts the percent-height, taking the available 
            remaining table height into account. This is not necesary for the
            width, since percent-width in colums *does* apply to available width.
            """
            table = self.node  # or event.target
            #print('heigh changed', event.heightChanged, event.owner.__id)
            
            if events[-1].new_value[1] != events[0].old_value[1]:
                
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
                        row.style.height = round(row.vflex /cum_vflex *
                                                 remainingPercentage) + 1 + '%'
        
        def _apply_cell_layout(self, row, col, vflex, hflex, cum_vflex, cum_hflex):
            raise NotImplementedError()



class FormLayout(BaseTableLayout):
    """ A form layout vertically alligns its child widgets.
    
    A label is placed to the left of each widget (based on the widget's
    title).
    """
    
    CSS = """
    .flx-FormLayout .flx-title {
        text-align: right;
        padding-right: 5px;
    }
    """
    
    class JS:
        
        def _init_phosphor_and_node(self):
            self.phosphor = self._create_phosphor_widget('table')
            self.node = self.phosphor.node
        
        def _apply_cell_layout(self, row, col, vflex, hflex, cum_vflex, cum_hflex):
            AUTOFLEX = 729
            className = ''
            if (vflex == AUTOFLEX) or (vflex == 0):
                row.style.height = 'auto'
                className += ''
            else:
                row.style.height = vflex * 100 / cum_vflex + '%'
                className += 'flx-vflex'
            className += ' '
            if (hflex == 0):
                col.style.width = 'auto'
                className += ''
            else:
                col.style.width = '100%'
                className += 'flx-hflex'
            col.className = className
        
        def _add_child(self, widget):
            # Create row
            row = window.document.createElement('tr')
            self.node.appendChild(row)
            # Create element for label
            td = window.document.createElement("td")
            td.classList.add('flx-title')
            row.appendChild(td)
            widget._title_elem = td
            td.innerHTML = widget.title
            # Create element for widget
            td = window.document.createElement("td")
            row.appendChild(td)
            td.appendChild(widget.outernode)
            #
            widget.outernode.hflex = 1
            widget.outernode.vflex = widget.flex[1]
            self._apply_table_layout()
        
        def _remove_child(self, widget):
            row = widget.outernode.parentNode.parentNode
            self.node.removeChild(row)
            if widget._title_elem:
                del widget._title_elem
        
        @event.connect('children', 'children*.flex')
        def __update_flexes(self, *events):
            for widget in self.children:
                widget.outernode.vflex = widget.flex[1]
            self._apply_table_layout()
        
        @event.connect('children', 'children*.title')
        def __update_titles(self, *events):
            for widget in self.children:
                if hasattr(widget, '_title_elem'):
                    widget._title_elem.innerHTML = widget.title
