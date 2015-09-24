"""
The splitter layout classes provide a mechanism to horizontally
or vertically stack child widgets, where the available space can be
manually specified by the user.

Example:

.. UIExample:: 200
    
    from flexx import ui
    
    class Example(ui.Widget):
        def init(self):
            with ui.Splitter(orientation='h'):
                ui.Button(text='Left A')
                with ui.Splitter(orientation='v'):
                    ui.Button(text='Right B')
                    ui.Button(text='Right C')
                    ui.Button(text='Right D')
"""

from .. import react
from . import Widget, Layout


class Splitter(Layout):
    """ Layout to split space for widgets horizontally or vertically.
    
    The Splitter layout divides the available space among its child
    widgets in a similar way that Box does, except that the
    user can divide the space by dragging the divider in between the
    widgets.
    """
    
    _DEFAULT_ORIENTATION = 'h'
    
    @react.input
    def orientation(self, v=None):
        """ The orientation of the child widgets. 'h' or 'v'. Default
        horizontal.
        """
        if v is None:
            v = self._DEFAULT_ORIENTATION
        if isinstance(v, str):
            v = v.lower()
        v = {'horizontal': 'h', 'vertical': 'v', 0: 'h', 1: 'v'}.get(v, v)
        if v not in ('h', 'v'):
            raise ValueError('Unknown value for splitter orientation %r' % v)
        return v
    
    class JS:
        
        def _create_node(self):
            self.p = phosphor.splitpanel.SplitPanel()
        
        @react.connect('orientation')
        def __orientation_changed(self, orientation):
            if orientation == 0 or orientation == 'h':
                self.p.orientation = phosphor.splitpanel.SplitPanel.Horizontal
            elif orientation == 1 or orientation == 'v':
                self.p.orientation = phosphor.splitpanel.SplitPanel.Vertical
            else:
                raise ValueError('Invalid splitter orientation: ' + orientation)


# note: I don' think we need to expose these ...
class HSplitter(Splitter):
    """ Horizontal splitter.
    """
    
    _DEFAULT_ORIENTATION = 'h'


class VSplitter(Splitter):
    """ Vertical splitter.
    """
    
    _DEFAULT_ORIENTATION = 'v'


class DockLayout(Layout):
    """
    """
    
    CSS = """
        .flx-docklayout > .ppppp-Widget {
            height: 100%;
        }
        
        
        .p-DockTabPanel {
        padding-right: 2px;
        padding-bottom: 2px;
        }
        
        
        .p-DockTabPanel > .p-StackedPanel {
        padding: 10px;
        background: white;
        border: 1px solid #C0C0C0;
        border-top: none;
        box-shadow: 1px 1px 2px rgba(0, 0, 0, 0.2);
        }
        
        
        .p-DockTabPanel-overlay {
        background: rgba(255, 255, 255, 0.6);
        border: 1px solid rgba(0, 0, 0, 0.6);
        }
        
        
        .p-TabBar {
        min-height: 24px;
        }
        
        
        .p-TabBar-content {
        bottom: 1px;
        align-items: flex-end;
        }
        
        
        .p-TabBar-content > .p-Tab {
        flex-basis: 125px;
        max-height: 21px;
        min-width: 35px;
        margin-left: -1px;
        border: 1px solid #C0C0C0;
        border-bottom: none;
        padding: 0px 10px;
        background: #E5E5E5;
        font: 12px Helvetica, Arial, sans-serif;
        }
        
        
        .p-TabBar-content > .p-Tab.p-mod-first {
        margin-left: 0;
        }
        
        
        .p-TabBar-content > .p-Tab.p-mod-selected {
        min-height: 24px;
        background: white;
        transform: translateY(1px);
        }
        
        
        .p-TabBar-content > .p-Tab:hover:not(.p-mod-selected) {
        background: #F0F0F0;
        }
        
        
        .p-TabBar-content > .p-Tab > span {
        line-height: 21px;
        }
        
        
        .p-TabBar-footer {
        display: block;
        height: 1px;
        background: #C0C0C0;
        }
        
        
        .p-Tab.p-mod-closable > .p-Tab-close-icon {
        margin-left: 4px;
        }
        
        
        .p-Tab.p-mod-closable > .p-Tab-close-icon:before {
        content: '\f00d';
        font-family: FontAwesome;
        }
        
        
        .p-Tab.p-mod-docking {
        font: 12px Helvetica, Arial, sans-serif;
        height: 24px;
        width: 125px;
        padding: 0px 10px;
        background: white;
        box-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);
        transform: translateX(-50px) translateY(-14px);
        }
        
        
        .p-Tab.p-mod-docking > span {
        line-height: 21px;
        }
    
    """
    
    class JS:
        
        def _create_node(self):
            self.p = phosphor.dockpanel.DockPanel()
            # if False:
            #     self.node = self._p.node
            #     phosphor.messaging.sendMessage(self._p, phosphor.widget.MSG_AFTER_ATTACH)  # simulate attachWidget()
            #     that = this
            #     window.onresize = lambda x=None: that._p.update()
            # else:
            #     # Need placeholder that scales along with parent
            #     # todo: when we stack phosphor elements, I don't want empty divs in between
            #     this.node = document.createElement('div')
            #     self.node.appendChild(self._p.node)
            #     phosphor.messaging.sendMessage(self._p, phosphor.widget.MSG_AFTER_ATTACH)
            #     # body.appendChild(this.node)
            #     # phosphor.widget.attachWidget(self._p, this.node)
            #     # body.removeChild(this.node)
            # #self._css_class_name(self._css_class_name() + ' ' + self._p.node.className)
        
        def _add_child(self, widget):
            
            if not widget.p:
                pwidget = phosphor.widget.Widget()
                pwidget.node.appendChild(widget.node)
                widget._pindex = self.p.childCount
            else:
                pwidget = widget.p
            
            tab = phosphor.tabs.Tab('xxxx')
            phosphor.dockpanel.DockPanel.setTab(pwidget, tab)
            #self.p.tabProperty.set(pwidget, tab)
            
            self.p.addWidget(pwidget)
        
        # @react.connect('actual_size')
        # def __size_changed(self, size):
        #     #phosphor.messaging.sendMessage(self._p, phosphor.widget.ResizeMessage(size[0], size[1]))
        #     self._p.setOffsetGeometry(0, 0, *size)
        #     #print('setting size', size)
        #     #self._p.update()
        #     
        # def _remove_child(self, widget):
        #     self._p.removeChildAt(widget._pindex)
