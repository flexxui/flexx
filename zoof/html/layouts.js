
zoof.widgets = {};

zoof.get = function (id) {
    if (id === 'body') {
        return document.body;
    } else {
        return zoof.widgets[id]
    }
};


zoof.createWidgetElement = function (type, D) {
    /* Used by all createX functions to create the HTML element, assign
       id and class name, and insert the element in the DOM.
    */
    var e = document.createElement(type);
    var par;  // semantic parent
    
    e.id = D.id;
    zoof.widgets[D.id] = e;

    e.className = D.className;
    e.zfInfo = D;  // store info used to create the widget
    
    par = zoof.get(D.parent);
    if (typeof par.appendWidget == 'function') {
        par.appendWidget(e);
    } else {
        par.appendChild(e);
    }
    return e;
};


zoof.setProps = function (id) {
    e = zoof.get(id);
    for (var i=1; i<arguments.length; i+=2) {
        e[arguments[i]] = arguments[i+1];
    }
};

zoof.setStyle = function (id) {
    e = zoof.get(id);
    for (var i=1; i<arguments.length; i+=2) {
        e.style[arguments[i]] = arguments[i+1];
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
    var e = zoof.createWidgetElement('table', D);
    var row = document.createElement("tr")
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
};


zoof.createVBox = function (D) {
    var e = zoof.createWidgetElement('table', D);
    
    e.appendWidget = function (child) {
        var tr = document.createElement("tr");
        var td = document.createElement("td");
        this.appendChild(tr);
        tr.appendChild(td);
        td.appendChild(child);
    };
};


zoof.createForm = function (D) {
    var e = zoof.createWidgetElement('table', D);
    e.appendChild(document.createElement("tr"));
    
    e.appendWidget = function (child) {
        var row = e.children[e.children.length-1];
        var itemsinrow = row.children.length;
        if (itemsinrow >= 2) {
            row = document.createElement("tr");
            e.appendChild(row);
        }
        var td = document.createElement("td");
        row.appendChild(td);
        td.appendChild(child);
    };
};


zoof.HBox_layout = function (id) {

    var T = zoof.get(id);
    var ncols;
    var j;
    var flexes = [];
    var nflex;
    var cell;
    var row = T.children[0];
    
    var ncols = row.children.length;
    for (j=0; j<ncols; j++) {
        cell = row.children[j];
        flexes[j] = cell.children[0].flex || 0;
    }
    
    nflex = flexes.reduce(function(pv, cv) { return pv + cv; }, 0);
    
    // If no flexes are given; assign each an equal flex
    if (nflex === 0) {
        flexes.fill(1);
        nflex = flexes.length;
    }
    
    // Assign width and classnames to cells, so that together with the
    // css, the table layout engine will behave as we want.
    for (j=0; j<ncols; j++) {
        cell = row.children[j];
        cell.style.height = '100%';
        if (flexes[j] === 0) {
            cell.className = 'hcell';
            cell.style.width = 'auto';
        } else {
            cell.className = 'hcell hcell-flex';  // via css we set button width to 100%
            cell.style.width = flexes[j] * 100/nflex + '%';
        }
    }
};


zoof.VBox_layout = function (id) {
    // Get table
    var T = zoof.get(id);
    var nrows = T.children.length;
    if (nrows === 0) {
        return
    }
    var ncols = T.children[0].children.length
    
    var i, j;
    var flexes = [];
    var nflex;
    var cell;
    var row;
    
    for (i=0; i<nrows; i++) {
        row = T.children[i];
        cell = row.children[0];
        flexes[i] = cell.children[0].flex || 0;
    }
    
    nflex = flexes.reduce(function(pv, cv) { return pv + cv; }, 0);
    
    // If no flexes are given; assign each an equal flex
    if (nflex === 0) {
        flexes.fill(1);
        nflex = flexes.length;
    }
    
    // Assign width and classnames to cells, so that together with the
    // css, the table layout engine will behave as we want.
    for (i=0; i<nrows; i++) {
        row = T.children[i]
        cell = row.children[0];
        if (flexes[i] === 0) {
            cell.className = 'vcell';
            row.style.height = 'auto';
        } else {
            cell.className = 'vcell vcell-flex';  // via css we set button width to 100%
            row.style.height = flexes[i] * 100/nflex + '%';
        }
    }
};


zoof.Form_layout = function (id) {
    // Get table
    var T = zoof.get(id);
    var nrows = T.children.length;
    if (nrows === 0) {
        return
    }
    var ncols = T.children[0].children.length
    
    var i, j;
    var flexes = [];
    var nflex;
    var cell;
    var row;
    
    flexes.fill(1);
    nflex = flexes.length;
    
    // Assign width and classnames to cells, so that together with the
    // css, the table layout engine will behave as we want.
    for (i=0; i<nrows; i++) {
        row = T.children[i]
        cell1 = row.children[0];
        cell2 = row.children[1];
        
        cell1.className = 'vcell vcell-flex hcell';
        cell2.className = 'vcell vcell-flex hcell hcell-flex';
        
        // Vertical
        row.style.height = flexes[i] * 100/nflex + '%';
        //row.style.height = 'auto';
        
        // Horizontal
        cell1.style.width = 'auto';
        cell2.style.width = '100%';
        
    }
};