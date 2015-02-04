
zoof.createWidget = function (parent, id, type, className) {
    var e = document.createElement(type);
    var par;  // semantic parent
    
    e.id = id;
    e.className = className + ' zf-widget';
    
    par = document.getElementById(parent);
    if (par.className.search('zf-hbox') > -1) {
        // todo: generalize this triage with some sort of table?
        zoof.addToHBox(par, e);
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
    var row = document.createElement("tr");
    e.appendChild(row);
};


zoof.addToHBox = function (layout, child) {
    var td = document.createElement("td");
    layout.children[0].appendChild(td);
    td.appendChild(child);
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
        flexes[j] = cell.children[0].flex | 0;
    }
    
    nflex = flexes.reduce(function(pv, cv) { return pv + cv; }, 0);
    console.warn(flexes);
    if (nflex > 0) {
        for (j=0; j<ncols; j++) {
            cell = row.children[j];
            if (flexes[j] === 0) {
                cell.className = '';
                cell.style.width = 'auto';
            } else {
                cell.className = 'flex';  // via css we set button width to 100%
                cell.style.width = flexes[j] * 100/nflex + '%';
            }
        }
    }
};
