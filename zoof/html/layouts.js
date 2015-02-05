
zoof.createWidget = function (parent, id, type, className) {
    var e = document.createElement(type);
    var par;  // semantic parent
    
    e.id = id;
    e.className = className + ' zf-widget';
    
    par = document.getElementById(parent);
    if (typeof par.appendWidget == 'function') {
        par.appendWidget(e);
    } else {
        par.appendChild(e);
    }
    return e;
};


zoof.setProps = function (id) {
    e = document.getElementById(id);
    for (var i=1; i<arguments.length; i+=2) {
        e[arguments[i]] = arguments[i+1];
    }
};

zoof.createButton = function (parent, id, text) {
    //console.warn('creating button');
    var e = zoof.createWidget(parent, id, 'button', 'zf-button');
    e.innerHTML = text;
};


zoof.createHBox = function (parent, id) {
    //console.warn('creating hbox');
    var e = zoof.createWidget(parent, id, 'table', 'zf-hbox');
    e.appendChild(document.createElement("tr"));
    
    e.appendWidget = function (child) {
        var td = document.createElement("td");
        this.children[0].appendChild(td);
        td.appendChild(child);
    };
};



zoof.createVBox = function (parent, id) {
    var e = zoof.createWidget(parent, id, 'table', 'zf-vbox');
    
    e.appendWidget = function (child) {
        var tr = document.createElement("tr");
        var td = document.createElement("td");
        this.appendChild(tr);
        tr.appendChild(td);
        td.appendChild(child);
    };
};


zoof.HBox_layout = function (id) {

    var T = document.getElementById(id);
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
    var T = document.getElementById(id);
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
    if (nflex > 0) {
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
    }
};