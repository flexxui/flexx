/*  Script for handling widgets and layout.

*/

/* JSLint config */
/*global zoof */
/*jslint node: true, continue:true */
"use strict";

zoof.widgets = {};
zoof.AUTOFLEX = 729;  // magic number unlikely to occut in practice


zoof.get = function (id) {
    if (id === 'body') {
        return document.body;
    } else {
        return zoof.widgets[id];
    }
};


zoof.createWidgetElement = function (type, D) {
    /* Used by all createX functions to create the HTML element, assign
       id and class name, and insert the element in the DOM.
    */
    var e = document.createElement(type),
        par;  // semantic parent
    
    e.id = D.id;
    zoof.widgets[D.id] = e;
    
    e.className = D.className;
    e.hflex = D.hflex;
    e.vflex = D.vflex;
    e.zfInfo = D;  // store info used to create the widget
    
    // Set position. Ignored unless position is absolute or relative
    e.style.left = (D.pos[0] > 1 ? D.pos[0] + "px" : D.pos[0] * 100 + "%");
    e.style.top = (D.pos[1] > 1 ? D.pos[1] + "px" : D.pos[1] * 100 + "%");
    
    // Add to parent
    par = zoof.get(D.parent);
    if (typeof par.appendWidget === 'function') {
        par.appendWidget(e);
    } else {
        par.appendChild(e);
    }
    
    // Add callback for resizing    
    e.checkResize = function () {
        /* This needs to be called if there is a chance that the widget has
           changed size. If will check the real size the next tick and emit
           a resize event if necessary.
        */
        setTimeout(e.checkResizeNow, 0);
    };
    e.storedSize = [0, 0];
    e.checkResizeNow = function () {
        var i, func, event;
        event = new window.CustomEvent("resize");
        event.widthChanged = (e.storedSize[0] !== e.clientWidth);
        event.heightChanged = (e.storedSize[1] !== e.clientHeight);
        if (event.widthChanged || event.heightChanged) {
            e.storedSize = [e.clientWidth, e.clientHeight];
            e.dispatchEvent(event);
        }
    };
        
    // Always invoke a resize after all initialization is done
    e.checkResize();
    // Keep up to date from parent size changes    
    if (par === document.body) {
        window.addEventListener('resize', e.checkResize, false);
    } else {
        par.addEventListener('resize', e.checkResize, false);
    }
            
    return e;
};


zoof.setProps = function (id) {
    var i,
        e = zoof.get(id);
    for (i = 0; i < arguments.length; i += 2) {
        e[arguments[i]] = arguments[i + 1];
    }
};

zoof.setStyle = function (id) {
    var i,
        e = zoof.get(id);
    for (i = 1; i < arguments.length; i += 2) {
        e.style[arguments[i]] = arguments[i + 1];
    }
};


zoof.createWidget = function (D) {
    var e = zoof.createWidgetElement('div', D);
};


zoof.createLabel = function (D) {
    var e = zoof.createWidgetElement('div', D);
    e.innerHTML = D.text;
};


zoof.createButton = function (D) {
    var e = zoof.createWidgetElement('button', D);
    e.innerHTML = D.text;
};


zoof.createHBox = function (D) {
    var e, row;
    
    e = zoof.createWidgetElement('table', D);
    row = document.createElement("tr");
    e.appendChild(row);
        
    // layout margin is implemented by table padding
    e.style.padding = D.margin;
    
    e.appendWidget = function (child) {
        var td = document.createElement("td");
        row.appendChild(td);
        td.appendChild(child);
        if (row.children.length > 1) {
            td.style['padding-left'] = D.spacing;
        }
    };
    
    e.applyLayout = function () {zoof.applyTableLayout(this); };
    
    e.applyCellLayout = function (row, col, vflex, hflex, cum_vflex, cum_hflex) {
        col.style.height = '100%';
        if (hflex === 0) {
            col.className = '';
            col.style.width = 'auto';
        } else {
            col.className = 'hflex';
            col.style.width = hflex * 100 / cum_hflex + '%';
        }
    };
    
    // no need to adjust the row-height when resizing
};


zoof.createVBox = function (D) {
    var e = zoof.createWidgetElement('table', D);
    
    e.appendWidget = function (child) {
        var tr = document.createElement("tr"),
            td = document.createElement("td");
        this.appendChild(tr);
        tr.appendChild(td);
        td.appendChild(child);
    };
    
    e.applyLayout = function () {zoof.applyTableLayout(this); };
    
    e.applyCellLayout = function (row, col, vflex, hflex, cum_vflex, cum_hflex) {
        
        row.vflex = vflex;
        if (vflex === 0) {
            col.className = 'hflex';
            row.style.height = 'auto';
        } else {
            col.className = 'vflex hflex';
            row.style.height = vflex * 100 / cum_vflex + '%';
        }
    };
    
    // We need to adjust height-percent when there is a vertical resize
    e.addEventListener('resize', zoof.adaptLayoutToSizeChange, false);
};


zoof.createForm = function (D) {
    var e = zoof.createWidgetElement('table', D);
    e.appendChild(document.createElement("tr"));
    
    e.appendWidget = function (child) {
        var row, td, itemsinrow;
        row = e.children[e.children.length - 1];
        itemsinrow = row.children.length;
        if (itemsinrow >= 2) {
            row = document.createElement("tr");
            e.appendChild(row);
        }
        td = document.createElement("td");
        row.appendChild(td);
        td.appendChild(child);
        // Do some auto-flexing
        child.hflex = (row.children.length === 1 ? 0 : 1);
    };
    
    e.applyLayout = function () {zoof.applyTableLayout(this); };
    
    e.applyCellLayout = function (row, col, vflex, hflex, cum_vflex, cum_hflex) {
        var className = '';
        if ((vflex === zoof.AUTOFLEX) || (vflex === 0)) {
            row.style.height = 'auto';
            className += '';
        } else {
            row.style.height = vflex * 100 / cum_vflex + '%';
            className += 'vflex';
        }
        className += ' ';
        if (hflex === 0) {
            col.style.width = 'auto';
            className += '';
        } else {
            col.style.width = '100%';
            className += 'hflex';
        }
        col.className = className;
    };
    
    // We need to adjust height-percent when there is a vertical resize
    e.addEventListener('resize', zoof.adaptLayoutToSizeChange, false);
};


zoof.createGrid = function (D) {
    var e = zoof.createWidgetElement('table', D);
    e.appendChild(document.createElement("tr"));
    
    e.appendWidget = function (child) {
        var i, j, row, cell;
        i = child.zfInfo.pos[1];
        j = child.zfInfo.pos[0];
        // Ensure enough rows
        while (i >= e.children.length) {
            e.appendChild(document.createElement("tr"));
        }
        row = e.children[i];
        // Ensure enough coloums
        while (j >= row.children.length) {
            row.appendChild(document.createElement("td"));
        }
        cell = row.children[j];
        // Append
        cell.appendChild(child);
    };
    
    e.applyLayout = function () {zoof.applyTableLayout(this); };
    
    e.applyCellLayout = function (row, col, vflex, hflex, cum_vflex, cum_hflex) {
        var className = '';
        if (vflex === 0) {
            row.style.height = 'auto';
            className += '';
        } else {
            row.style.height = vflex * 100 / cum_vflex + '%';
            className += 'vflex';
        }
        className += ' ';
        if (hflex === 0) {
            col.style.width = 'auto';
            className += '';
        } else {
            col.style.width = hflex * 100 / cum_hflex + '%';
            className += ' hflex';
        }
        col.className = className;
    };
    
    // We need to adjust height-percent when there is a vertical resize
    e.addEventListener('resize', zoof.adaptLayoutToSizeChange, false);

};


zoof.createPinBoard = function (D) {
    var e = zoof.createWidgetElement('div', D);
    e.applyLayout = function () {}; // dummy    
};


zoof.applyTableLayout = function (table) {
    /* To be called with a layout id when a child is added or stretch factor
       changes. Calculates the flexes and (via a layout-dependent function)
       sets the class of the td element and the width of the td element.
       The heights of tr elements is set on resize, since it behaves slightly 
       different.
    */
    var row, col,
        i, j, nrows, ncols,
        vflexes, hflexes, cum_vflex, cum_hflex;
        
    // Get table dimensions    
    nrows = table.children.length;
    ncols = 0;
    for (i = 0; i < nrows; i += 1) {
        row = table.children[i];
        ncols = Math.max(ncols, row.children.length);
    }
    if (nrows === 0 || ncols === 0) {
        return;
    }
    
    // Collect flexes
    vflexes = [];
    hflexes = [];
    for (i = 0; i < nrows; i += 1) {
        row = table.children[i];
        for (j = 0; j < ncols; j += 1) {
            col = row.children[j];
            if ((col === undefined) || (col.children.length === 0)) {
                continue;
            }
            vflexes[i] = Math.max(vflexes[i] || 0, col.children[0].vflex || 0);
            hflexes[j] = Math.max(hflexes[j] || 0, col.children[0].hflex || 0);
        }
    }
    
    // What is the cumulative "flex-value"?
    cum_vflex = vflexes.reduce(function (pv, cv) { return pv + cv; }, 0);
    cum_hflex = hflexes.reduce(function (pv, cv) { return pv + cv; }, 0);
    
    // If no flexes are given; assign each equal
    if (cum_vflex === 0) {
        vflexes.fill(zoof.AUTOFLEX);
        cum_vflex = vflexes.length * zoof.AUTOFLEX;
    }
    if (cum_hflex === 0) {
        hflexes.fill(zoof.AUTOFLEX);
        cum_hflex = hflexes.length * zoof.AUTOFLEX;
    }
    
    // Assign css class and height/weight to cells
    for (i = 0; i < nrows; i += 1) {
        row = table.children[i];
        row.vflex = vflexes[i] || 0;  // Store for use during resizing
        for (j = 0; j < ncols; j += 1) {
            col = row.children[j];
            if ((col === undefined) || (col.children.length === 0)) {
                continue;
            }
            table.applyCellLayout(row, col, vflexes[i], hflexes[j], cum_vflex, cum_hflex);
        }
    }
};


zoof.adaptLayoutToSizeChange = function (event) {
    /* This function adapts the height (in percent) of the flexible rows
    of a layout. This is needed because the percent-height applies to the
    total height of the table. This function is called whenever the
    table resizes, and adjusts the percent-height, taking the available 
    remaining table height into account. This is not necesary for the
    width, since percent-width in colums *does* apply to available width.
    */
    
    var table, row, col, i, j,
        cum_vflex, remainingHeight, remainingPercentage, maxHeight;
    
    table = event.target;
    
    if (event.heightChanged) {
        
        // Set one flex row to max, so that non-flex rows have their minimum size
        // The table can already have been stretched a bit, causing the total row-height
        // in % to not be sufficient from keeping the non-flex rows from growing.
        for (i = 0; i < table.children.length; i += 1) {
            row = table.children[i];
            if (row.vflex > 0) {
                row.style.height = '100%';
                break;
            }
        }
        
        // Get remaining height: subtract height of each non-flex row
        remainingHeight = table.clientHeight;
        cum_vflex = 0;
        for (i = 0; i < table.children.length; i += 1) {
            row = table.children[i];
            cum_vflex += row.vflex;
            if ((row.vflex === 0) && (row.children.length > 0)) {
                remainingHeight -= row.children[0].clientHeight;
            }
        }
        
        // Apply height % for each flex row
        remainingPercentage = 100 * remainingHeight / table.clientHeight;
        for (i = 0; i < table.children.length; i += 1) {
            row = table.children[i];
            if (row.vflex > 0) {
                row.style.height = Math.round(row.vflex / cum_vflex * remainingPercentage) + 1 + '%';
            }
        }
    }
};
