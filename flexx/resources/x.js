(function e(t,n,r){function s(o,u){if(!n[o]){if(!t[o]){var a=typeof require=="function"&&require;if(!u&&a)return a(o,!0);if(i)return i(o,!0);var f=new Error("Cannot find module '"+o+"'");throw f.code="MODULE_NOT_FOUND",f}var l=n[o]={exports:{}};t[o][0].call(l.exports,function(e){var n=t[o][1][e];return s(n?n:e)},l,l.exports,e,t,n,r)}return n[o].exports}var i=typeof require=="function"&&require;for(var o=0;o<r.length;o++)s(r[o]);return s})({1:[function(require,module,exports){
window.phosphor = {};
window.phosphor.disposable = require("phosphor-disposable");
window.phosphor.messaging = require("phosphor-messaging");
window.phosphor.properties = require("phosphor-properties");
window.phosphor.signaling = require("phosphor-signaling");
window.phosphor.boxengine = require("phosphor-boxengine");
window.phosphor.domutil = require("phosphor-domutil");
window.phosphor.nodewrapper = require("phosphor-nodewrapper");
window.phosphor.widget = require("phosphor-widget");
window.phosphor.menus = require("phosphor-menus");
window.phosphor.boxpanel = require("phosphor-boxpanel");
window.phosphor.gridpanel = require("phosphor-gridpanel");
window.phosphor.splitpanel = require("phosphor-splitpanel");
window.phosphor.stackedpanel = require("phosphor-stackedpanel");
window.phosphor.tabs = require("phosphor-tabs");
window.phosphor.dockpanel = require("phosphor-dockpanel");
window.phosphor.createWidget = function (name) {
	var ori = phosphor.widget.Widget.createNode;
	phosphor.widget.Widget.createNode = function() {return document.createElement(name);};
	var w = new phosphor.widget.Widget();
	phosphor.widget.Widget.createNode = ori;
	return w;
};
},{"phosphor-boxengine":3,"phosphor-boxpanel":5,"phosphor-disposable":10,"phosphor-dockpanel":12,"phosphor-domutil":22,"phosphor-gridpanel":24,"phosphor-menus":29,"phosphor-messaging":40,"phosphor-nodewrapper":42,"phosphor-properties":43,"phosphor-signaling":44,"phosphor-splitpanel":46,"phosphor-stackedpanel":55,"phosphor-tabs":59,"phosphor-widget":72}],2:[function(require,module,exports){
'use strict';
module.exports = {
	createLink: function(href, attributes) {
		var head = document.head || document.getElementsByTagName('head')[0];
		var link = document.createElement('link');
		link.href = href;
		link.rel = 'stylesheet';
		for (var key in attributes) {
			if ( ! attributes.hasOwnProperty(key)) {
				continue;
			}
			var value = attributes[key];
			link.setAttribute('data-' + key, value);
		}
		head.appendChild(link);
	},
	createStyle: function(cssText, attributes) {
		var head = document.head || document.getElementsByTagName('head')[0],
			style = document.createElement('style');
		style.type = 'text/css';
		for (var key in attributes) {
			if ( ! attributes.hasOwnProperty(key)) {
				continue;
			}
			var value = attributes[key];
			style.setAttribute('data-' + key, value);
		}
		if (style.sheet) {
			style.innerHTML = cssText;
			style.sheet.cssText = cssText;
			head.appendChild(style);
		} else if (style.styleSheet) {
			head.appendChild(style);
			style.styleSheet.cssText = cssText;
		} else {
			style.appendChild(document.createTextNode(cssText));
			head.appendChild(style);
		}
	}
};
},{}],3:[function(require,module,exports){

'use strict';

var BoxSizer = (function () {
	function BoxSizer() {

		this.sizeHint = 0;

		this.minSize = 0;

		this.maxSize = Infinity;

		this.stretch = 1;

		this.size = 0;

		this.done = false;
	}
	return BoxSizer;
})();
exports.BoxSizer = BoxSizer;

function boxCalc(sizers, space) {
	var count = sizers.length;
	if (count === 0) {
		return;
	}
	var totalMin = 0;
	var totalMax = 0;
	var totalSize = 0;
	var totalStretch = 0;
	var stretchCount = 0;
	for (var i = 0; i < count; ++i) {
		var sizer = sizers[i];
		initSizer(sizer);
		totalSize += sizer.size;
		totalMin += sizer.minSize;
		totalMax += sizer.maxSize;
		if (sizer.stretch > 0) {
			totalStretch += sizer.stretch;
			stretchCount++;
		}
	}
	if (space === totalSize) {
		return;
	}
	if (space <= totalMin) {
		for (var i = 0; i < count; ++i) {
			var sizer = sizers[i];
			sizer.size = sizer.minSize;
		}
		return;
	}
	if (space >= totalMax) {
		for (var i = 0; i < count; ++i) {
			var sizer = sizers[i];
			sizer.size = sizer.maxSize;
		}
		return;
	}
	var nearZero = 0.01;
	var notDoneCount = count;
	if (space < totalSize) {
		var freeSpace = totalSize - space;
		while (stretchCount > 0 && freeSpace > nearZero) {
			var distSpace = freeSpace;
			var distStretch = totalStretch;
			for (var i = 0; i < count; ++i) {
				var sizer = sizers[i];
				if (sizer.done || sizer.stretch === 0) {
					continue;
				}
				var amt = sizer.stretch * distSpace / distStretch;
				if (sizer.size - amt <= sizer.minSize) {
					freeSpace -= sizer.size - sizer.minSize;
					totalStretch -= sizer.stretch;
					sizer.size = sizer.minSize;
					sizer.done = true;
					notDoneCount--;
					stretchCount--;
				}
				else {
					freeSpace -= amt;
					sizer.size -= amt;
				}
			}
		}
		while (notDoneCount > 0 && freeSpace > nearZero) {
			var amt = freeSpace / notDoneCount;
			for (var i = 0; i < count; ++i) {
				var sizer = sizers[i];
				if (sizer.done) {
					continue;
				}
				if (sizer.size - amt <= sizer.minSize) {
					freeSpace -= sizer.size - sizer.minSize;
					sizer.size = sizer.minSize;
					sizer.done = true;
					notDoneCount--;
				}
				else {
					freeSpace -= amt;
					sizer.size -= amt;
				}
			}
		}
	}
	else {
		var freeSpace = space - totalSize;
		while (stretchCount > 0 && freeSpace > nearZero) {
			var distSpace = freeSpace;
			var distStretch = totalStretch;
			for (var i = 0; i < count; ++i) {
				var sizer = sizers[i];
				if (sizer.done || sizer.stretch === 0) {
					continue;
				}
				var amt = sizer.stretch * distSpace / distStretch;
				if (sizer.size + amt >= sizer.maxSize) {
					freeSpace -= sizer.maxSize - sizer.size;
					totalStretch -= sizer.stretch;
					sizer.size = sizer.maxSize;
					sizer.done = true;
					notDoneCount--;
					stretchCount--;
				}
				else {
					freeSpace -= amt;
					sizer.size += amt;
				}
			}
		}
		while (notDoneCount > 0 && freeSpace > nearZero) {
			var amt = freeSpace / notDoneCount;
			for (var i = 0; i < count; ++i) {
				var sizer = sizers[i];
				if (sizer.done) {
					continue;
				}
				if (sizer.size + amt >= sizer.maxSize) {
					freeSpace -= sizer.maxSize - sizer.size;
					sizer.size = sizer.maxSize;
					sizer.done = true;
					notDoneCount--;
				}
				else {
					freeSpace -= amt;
					sizer.size += amt;
				}
			}
		}
	}
}
exports.boxCalc = boxCalc;

function initSizer(sizer) {
	sizer.size = Math.max(sizer.minSize, Math.min(sizer.sizeHint, sizer.maxSize));
	sizer.done = false;
}
},{}],4:[function(require,module,exports){
var css = ".p-BoxPanel{position:relative}.p-BoxPanel>.p-Widget{position:absolute}"; (require("browserify-css").createStyle(css, { "href": "node_modules/phosphor-boxpanel/lib/index.css"})); module.exports = css;
},{"browserify-css":2}],5:[function(require,module,exports){

'use strict';
var __extends = (this && this.__extends) || function (d, b) {
	for (var p in b) if (b.hasOwnProperty(p)) d[p] = b[p];
	function __() { this.constructor = d; }
	d.prototype = b === null ? Object.create(b) : (__.prototype = b.prototype, new __());
};
var arrays = require('phosphor-arrays');
var phosphor_boxengine_1 = require('phosphor-boxengine');
var phosphor_messaging_1 = require('phosphor-messaging');
var phosphor_properties_1 = require('phosphor-properties');
var phosphor_widget_1 = require('phosphor-widget');
require('./index.css');

exports.BOX_PANEL_CLASS = 'p-BoxPanel';

exports.LTR_CLASS = 'p-mod-left-to-right';

exports.RTL_CLASS = 'p-mod-right-to-left';

exports.TTB_CLASS = 'p-mod-top-to-bottom';

exports.BTT_CLASS = 'p-mod-bottom-to-top';

(function (Direction) {

	Direction[Direction["LeftToRight"] = 0] = "LeftToRight";

	Direction[Direction["RightToLeft"] = 1] = "RightToLeft";

	Direction[Direction["TopToBottom"] = 2] = "TopToBottom";

	Direction[Direction["BottomToTop"] = 3] = "BottomToTop";
})(exports.Direction || (exports.Direction = {}));
var Direction = exports.Direction;

var BoxPanel = (function (_super) {
	__extends(BoxPanel, _super);

	function BoxPanel() {
		_super.call(this);
		this._fixedSpace = 0;
		this._sizers = [];
		this.addClass(exports.BOX_PANEL_CLASS);
		this.addClass(exports.TTB_CLASS);
	}

	BoxPanel.getStretch = function (widget) {
		return BoxPanel.stretchProperty.get(widget);
	};

	BoxPanel.setStretch = function (widget, value) {
		BoxPanel.stretchProperty.set(widget, value);
	};

	BoxPanel.getSizeBasis = function (widget) {
		return BoxPanel.sizeBasisProperty.get(widget);
	};

	BoxPanel.setSizeBasis = function (widget, value) {
		BoxPanel.sizeBasisProperty.set(widget, value);
	};

	BoxPanel.prototype.dispose = function () {
		this._sizers.length = 0;
		_super.prototype.dispose.call(this);
	};
	Object.defineProperty(BoxPanel.prototype, "direction", {

		get: function () {
			return BoxPanel.directionProperty.get(this);
		},

		set: function (value) {
			BoxPanel.directionProperty.set(this, value);
		},
		enumerable: true,
		configurable: true
	});
	Object.defineProperty(BoxPanel.prototype, "spacing", {

		get: function () {
			return BoxPanel.spacingProperty.get(this);
		},

		set: function (value) {
			BoxPanel.spacingProperty.set(this, value);
		},
		enumerable: true,
		configurable: true
	});

	BoxPanel.prototype.onChildAdded = function (msg) {
		arrays.insert(this._sizers, msg.currentIndex, new phosphor_boxengine_1.BoxSizer());
		this.node.appendChild(msg.child.node);
		if (this.isAttached)
			phosphor_messaging_1.sendMessage(msg.child, phosphor_widget_1.MSG_AFTER_ATTACH);
		phosphor_messaging_1.postMessage(this, phosphor_widget_1.MSG_LAYOUT_REQUEST);
	};

	BoxPanel.prototype.onChildRemoved = function (msg) {
		arrays.removeAt(this._sizers, msg.previousIndex);
		if (this.isAttached)
			phosphor_messaging_1.sendMessage(msg.child, phosphor_widget_1.MSG_BEFORE_DETACH);
		this.node.removeChild(msg.child.node);
		phosphor_messaging_1.postMessage(this, phosphor_widget_1.MSG_LAYOUT_REQUEST);
		msg.child.clearOffsetGeometry();
	};

	BoxPanel.prototype.onChildMoved = function (msg) {
		arrays.move(this._sizers, msg.previousIndex, msg.currentIndex);
		this.update();
	};

	BoxPanel.prototype.onAfterShow = function (msg) {
		this.update(true);
	};

	BoxPanel.prototype.onAfterAttach = function (msg) {
		phosphor_messaging_1.postMessage(this, phosphor_widget_1.MSG_LAYOUT_REQUEST);
	};

	BoxPanel.prototype.onChildShown = function (msg) {
		phosphor_messaging_1.postMessage(this, phosphor_widget_1.MSG_LAYOUT_REQUEST);
	};

	BoxPanel.prototype.onChildHidden = function (msg) {
		phosphor_messaging_1.postMessage(this, phosphor_widget_1.MSG_LAYOUT_REQUEST);
	};

	BoxPanel.prototype.onResize = function (msg) {
		if (this.isVisible) {
			if (msg.width < 0 || msg.height < 0) {
				var rect = this.offsetRect;
				this._layoutChildren(rect.width, rect.height);
			}
			else {
				this._layoutChildren(msg.width, msg.height);
			}
		}
	};

	BoxPanel.prototype.onUpdateRequest = function (msg) {
		if (this.isVisible) {
			var rect = this.offsetRect;
			this._layoutChildren(rect.width, rect.height);
		}
	};

	BoxPanel.prototype.onLayoutRequest = function (msg) {
		if (this.isAttached) {
			this._setupGeometry();
		}
	};

	BoxPanel.prototype._setupGeometry = function () {
		var visibleCount = 0;
		for (var i = 0, n = this.childCount; i < n; ++i) {
			if (!this.childAt(i).hidden)
				visibleCount++;
		}
		this._fixedSpace = this.spacing * Math.max(0, visibleCount - 1);
		var minW = 0;
		var minH = 0;
		var maxW = Infinity;
		var maxH = Infinity;
		var dir = this.direction;
		if (dir === Direction.LeftToRight || dir === Direction.RightToLeft) {
			minW = this._fixedSpace;
			maxW = visibleCount > 0 ? minW : maxW;
			for (var i = 0, n = this.childCount; i < n; ++i) {
				var widget = this.childAt(i);
				var sizer = this._sizers[i];
				if (widget.hidden) {
					sizer.minSize = 0;
					sizer.maxSize = 0;
					continue;
				}
				var limits = widget.sizeLimits;
				sizer.sizeHint = BoxPanel.getSizeBasis(widget);
				sizer.stretch = BoxPanel.getStretch(widget);
				sizer.minSize = limits.minWidth;
				sizer.maxSize = limits.maxWidth;
				minW += limits.minWidth;
				maxW += limits.maxWidth;
				minH = Math.max(minH, limits.minHeight);
				maxH = Math.min(maxH, limits.maxHeight);
			}
		}
		else {
			minH = this._fixedSpace;
			maxH = visibleCount > 0 ? minH : maxH;
			for (var i = 0, n = this.childCount; i < n; ++i) {
				var widget = this.childAt(i);
				var sizer = this._sizers[i];
				if (widget.hidden) {
					sizer.minSize = 0;
					sizer.maxSize = 0;
					continue;
				}
				var limits = widget.sizeLimits;
				sizer.sizeHint = BoxPanel.getSizeBasis(widget);
				sizer.stretch = BoxPanel.getStretch(widget);
				sizer.minSize = limits.minHeight;
				sizer.maxSize = limits.maxHeight;
				minH += limits.minHeight;
				maxH += limits.maxHeight;
				minW = Math.max(minW, limits.minWidth);
				maxW = Math.min(maxW, limits.maxWidth);
			}
		}
		var box = this.boxSizing;
		minW += box.horizontalSum;
		minH += box.verticalSum;
		maxW += box.horizontalSum;
		maxH += box.verticalSum;
		this.setSizeLimits(minW, minH, maxW, maxH);
		if (this.parent)
			phosphor_messaging_1.sendMessage(this.parent, phosphor_widget_1.MSG_LAYOUT_REQUEST);
		this.update(true);
	};

	BoxPanel.prototype._layoutChildren = function (offsetWidth, offsetHeight) {
		if (this.childCount === 0) {
			return;
		}
		var box = this.boxSizing;
		var top = box.paddingTop;
		var left = box.paddingLeft;
		var width = offsetWidth - box.horizontalSum;
		var height = offsetHeight - box.verticalSum;
		var dir = this.direction;
		var spacing = this.spacing;
		if (dir === Direction.LeftToRight) {
			phosphor_boxengine_1.boxCalc(this._sizers, Math.max(0, width - this._fixedSpace));
			for (var i = 0, n = this.childCount; i < n; ++i) {
				var widget = this.childAt(i);
				if (widget.hidden) {
					continue;
				}
				var size = this._sizers[i].size;
				widget.setOffsetGeometry(left, top, size, height);
				left += size + spacing;
			}
		}
		else if (dir === Direction.TopToBottom) {
			phosphor_boxengine_1.boxCalc(this._sizers, Math.max(0, height - this._fixedSpace));
			for (var i = 0, n = this.childCount; i < n; ++i) {
				var widget = this.childAt(i);
				if (widget.hidden) {
					continue;
				}
				var size = this._sizers[i].size;
				widget.setOffsetGeometry(left, top, width, size);
				top += size + spacing;
			}
		}
		else if (dir === Direction.RightToLeft) {
			left += width;
			phosphor_boxengine_1.boxCalc(this._sizers, Math.max(0, width - this._fixedSpace));
			for (var i = 0, n = this.childCount; i < n; ++i) {
				var widget = this.childAt(i);
				if (widget.hidden) {
					continue;
				}
				var size = this._sizers[i].size;
				widget.setOffsetGeometry(left - size, top, size, height);
				left -= size + spacing;
			}
		}
		else {
			top += height;
			phosphor_boxengine_1.boxCalc(this._sizers, Math.max(0, height - this._fixedSpace));
			for (var i = 0, n = this.childCount; i < n; ++i) {
				var widget = this.childAt(i);
				if (widget.hidden) {
					continue;
				}
				var size = this._sizers[i].size;
				widget.setOffsetGeometry(left, top - size, width, size);
				top -= size + spacing;
			}
		}
	};

	BoxPanel.prototype._onDirectionChanged = function (old, value) {
		this.toggleClass(exports.LTR_CLASS, value === Direction.LeftToRight);
		this.toggleClass(exports.RTL_CLASS, value === Direction.RightToLeft);
		this.toggleClass(exports.TTB_CLASS, value === Direction.TopToBottom);
		this.toggleClass(exports.BTT_CLASS, value === Direction.BottomToTop);
		phosphor_messaging_1.postMessage(this, phosphor_widget_1.MSG_LAYOUT_REQUEST);
	};

	BoxPanel.LeftToRight = Direction.LeftToRight;

	BoxPanel.RightToLeft = Direction.RightToLeft;

	BoxPanel.TopToBottom = Direction.TopToBottom;

	BoxPanel.BottomToTop = Direction.BottomToTop;

	BoxPanel.directionProperty = new phosphor_properties_1.Property({
		value: Direction.TopToBottom,
		changed: function (owner, old, value) { return owner._onDirectionChanged(old, value); },
	});

	BoxPanel.spacingProperty = new phosphor_properties_1.Property({
		value: 8,
		coerce: function (owner, value) { return Math.max(0, value | 0); },
		changed: function (owner) { return phosphor_messaging_1.postMessage(owner, phosphor_widget_1.MSG_LAYOUT_REQUEST); },
	});

	BoxPanel.stretchProperty = new phosphor_properties_1.Property({
		value: 0,
		coerce: function (owner, value) { return Math.max(0, value | 0); },
		changed: onChildPropertyChanged,
	});

	BoxPanel.sizeBasisProperty = new phosphor_properties_1.Property({
		value: 0,
		coerce: function (owner, value) { return Math.max(0, value | 0); },
		changed: onChildPropertyChanged,
	});
	return BoxPanel;
})(phosphor_widget_1.Widget);
exports.BoxPanel = BoxPanel;

function onChildPropertyChanged(child) {
	if (child.parent instanceof BoxPanel) {
		phosphor_messaging_1.postMessage(child.parent, phosphor_widget_1.MSG_LAYOUT_REQUEST);
	}
}
},{"./index.css":4,"phosphor-arrays":6,"phosphor-boxengine":7,"phosphor-messaging":40,"phosphor-properties":8,"phosphor-widget":72}],6:[function(require,module,exports){

'use strict';

function forEach(array, callback, fromIndex, wrap) {
	if (fromIndex === void 0) { fromIndex = 0; }
	if (wrap === void 0) { wrap = false; }
	var start = fromIndex | 0;
	if (start < 0 || start >= array.length) {
		return void 0;
	}
	if (wrap) {
		for (var i = 0, n = array.length; i < n; ++i) {
			var j = (start + i) % n;
			var result = callback(array[j], j);
			if (result !== void 0)
				return result;
		}
	}
	else {
		for (var i = start, n = array.length; i < n; ++i) {
			var result = callback(array[i], i);
			if (result !== void 0)
				return result;
		}
	}
	return void 0;
}
exports.forEach = forEach;

function rforEach(array, callback, fromIndex, wrap) {
	if (fromIndex === void 0) { fromIndex = array.length - 1; }
	if (wrap === void 0) { wrap = false; }
	var start = fromIndex | 0;
	if (start < 0 || start >= array.length) {
		return void 0;
	}
	if (wrap) {
		for (var i = 0, n = array.length; i < n; ++i) {
			var j = (start - i + n) % n;
			var result = callback(array[j], j);
			if (result !== void 0)
				return result;
		}
	}
	else {
		for (var i = start; i >= 0; --i) {
			var result = callback(array[i], i);
			if (result !== void 0)
				return result;
		}
	}
	return void 0;
}
exports.rforEach = rforEach;

function findIndex(array, pred, fromIndex, wrap) {
	if (fromIndex === void 0) { fromIndex = 0; }
	if (wrap === void 0) { wrap = false; }
	var start = fromIndex | 0;
	if (start < 0 || start >= array.length) {
		return -1;
	}
	if (wrap) {
		for (var i = 0, n = array.length; i < n; ++i) {
			var j = (start + i) % n;
			if (pred(array[j], j))
				return j;
		}
	}
	else {
		for (var i = start, n = array.length; i < n; ++i) {
			if (pred(array[i], i))
				return i;
		}
	}
	return -1;
}
exports.findIndex = findIndex;

function rfindIndex(array, pred, fromIndex, wrap) {
	if (fromIndex === void 0) { fromIndex = array.length - 1; }
	if (wrap === void 0) { wrap = false; }
	var start = fromIndex | 0;
	if (start < 0 || start >= array.length) {
		return -1;
	}
	if (wrap) {
		for (var i = 0, n = array.length; i < n; ++i) {
			var j = (start - i + n) % n;
			if (pred(array[j], j))
				return j;
		}
	}
	else {
		for (var i = start; i >= 0; --i) {
			if (pred(array[i], i))
				return i;
		}
	}
	return -1;
}
exports.rfindIndex = rfindIndex;

function find(array, pred, fromIndex, wrap) {
	var i = findIndex(array, pred, fromIndex, wrap);
	return i !== -1 ? array[i] : void 0;
}
exports.find = find;

function rfind(array, pred, fromIndex, wrap) {
	var i = rfindIndex(array, pred, fromIndex, wrap);
	return i !== -1 ? array[i] : void 0;
}
exports.rfind = rfind;

function insert(array, index, value) {
	var j = Math.max(0, Math.min(index | 0, array.length));
	for (var i = array.length; i > j; --i) {
		array[i] = array[i - 1];
	}
	array[j] = value;
	return j;
}
exports.insert = insert;

function move(array, fromIndex, toIndex) {
	var j = fromIndex | 0;
	if (j < 0 || j >= array.length) {
		return false;
	}
	var k = toIndex | 0;
	if (k < 0 || k >= array.length) {
		return false;
	}
	var value = array[j];
	if (j > k) {
		for (var i = j; i > k; --i) {
			array[i] = array[i - 1];
		}
	}
	else if (j < k) {
		for (var i = j; i < k; ++i) {
			array[i] = array[i + 1];
		}
	}
	array[k] = value;
	return true;
}
exports.move = move;

function removeAt(array, index) {
	var j = index | 0;
	if (j < 0 || j >= array.length) {
		return void 0;
	}
	var value = array[j];
	for (var i = j + 1, n = array.length; i < n; ++i) {
		array[i - 1] = array[i];
	}
	array.length -= 1;
	return value;
}
exports.removeAt = removeAt;

function remove(array, value) {
	var j = -1;
	for (var i = 0, n = array.length; i < n; ++i) {
		if (array[i] === value) {
			j = i;
			break;
		}
	}
	if (j === -1) {
		return -1;
	}
	for (var i = j + 1, n = array.length; i < n; ++i) {
		array[i - 1] = array[i];
	}
	array.length -= 1;
	return j;
}
exports.remove = remove;

function reverse(array, fromIndex, toIndex) {
	if (fromIndex === void 0) { fromIndex = 0; }
	if (toIndex === void 0) { toIndex = array.length; }
	var i = Math.max(0, Math.min(fromIndex | 0, array.length - 1));
	var j = Math.max(0, Math.min(toIndex | 0, array.length - 1));
	if (j < i)
		i = j + (j = i, 0);
	while (i < j) {
		var tmpval = array[i];
		array[i++] = array[j];
		array[j--] = tmpval;
	}
	return array;
}
exports.reverse = reverse;

function rotate(array, delta) {
	var n = array.length;
	if (n <= 1) {
		return array;
	}
	var d = delta | 0;
	if (d > 0) {
		d = d % n;
	}
	else if (d < 0) {
		d = ((d % n) + n) % n;
	}
	if (d === 0) {
		return array;
	}
	reverse(array, 0, d - 1);
	reverse(array, d, n - 1);
	reverse(array, 0, n - 1);
	return array;
}
exports.rotate = rotate;

function lowerBound(array, value, cmp) {
	var begin = 0;
	var half;
	var middle;
	var n = array.length;
	while (n > 0) {
		half = n >> 1;
		middle = begin + half;
		if (cmp(array[middle], value)) {
			begin = middle + 1;
			n -= half + 1;
		}
		else {
			n = half;
		}
	}
	return begin;
}
exports.lowerBound = lowerBound;

function upperBound(array, value, cmp) {
	var begin = 0;
	var half;
	var middle;
	var n = array.length;
	while (n > 0) {
		half = n >> 1;
		middle = begin + half;
		if (cmp(value, array[middle])) {
			n = half;
		}
		else {
			begin = middle + 1;
			n -= half + 1;
		}
	}
	return begin;
}
exports.upperBound = upperBound;
},{}],7:[function(require,module,exports){
arguments[4][3][0].apply(exports,arguments)
},{"dup":3}],8:[function(require,module,exports){

'use strict';
var phosphor_signaling_1 = require('phosphor-signaling');

var Property = (function () {

	function Property(options) {
		if (options === void 0) { options = {}; }
		this._pid = nextPID();
		this._value = options.value;
		this._create = options.create;
		this._coerce = options.coerce;
		this._compare = options.compare;
		this._changed = options.changed;
	}

	Property.getChanged = function (owner) {
		return Property.changedSignal.bind(owner);
	};

	Property.prototype.get = function (owner) {
		var value;
		var hash = lookupHash(owner);
		if (this._pid in hash) {
			value = hash[this._pid];
		}
		else {
			value = hash[this._pid] = this._createValue(owner);
		}
		return value;
	};

	Property.prototype.set = function (owner, value) {
		var oldValue;
		var hash = lookupHash(owner);
		if (this._pid in hash) {
			oldValue = hash[this._pid];
		}
		else {
			oldValue = hash[this._pid] = this._createValue(owner);
		}
		var newValue = this._coerceValue(owner, value);
		this._maybeNotify(owner, oldValue, hash[this._pid] = newValue);
	};

	Property.prototype.coerce = function (owner) {
		var oldValue;
		var hash = lookupHash(owner);
		if (this._pid in hash) {
			oldValue = hash[this._pid];
		}
		else {
			oldValue = hash[this._pid] = this._createValue(owner);
		}
		var newValue = this._coerceValue(owner, oldValue);
		this._maybeNotify(owner, oldValue, hash[this._pid] = newValue);
	};

	Property.prototype._createValue = function (owner) {
		var create = this._create;
		return create ? create(owner) : this._value;
	};

	Property.prototype._coerceValue = function (owner, value) {
		var coerce = this._coerce;
		return coerce ? coerce(owner, value) : value;
	};

	Property.prototype._compareValue = function (oldValue, newValue) {
		var compare = this._compare;
		return compare ? compare(oldValue, newValue) : oldValue === newValue;
	};

	Property.prototype._maybeNotify = function (owner, oldValue, newValue) {
		if (!this._compareValue(oldValue, newValue)) {
			var changed = this._changed;
			if (changed)
				changed(owner, oldValue, newValue);
			Property.getChanged(owner).emit(changedArgs(this, oldValue, newValue));
		}
	};

	Property.changedSignal = new phosphor_signaling_1.Signal();
	return Property;
})();
exports.Property = Property;

function clearPropertyData(owner) {
	ownerData.delete(owner);
}
exports.clearPropertyData = clearPropertyData;

var ownerData = new WeakMap();

var nextPID = (function () { var id = 0; return function () { return 'pid-' + id++; }; })();

function changedArgs(property, oldValue, newValue) {
	return { property: property, oldValue: oldValue, newValue: newValue };
}

function lookupHash(owner) {
	var hash = ownerData.get(owner);
	if (hash !== void 0)
		return hash;
	hash = Object.create(null);
	ownerData.set(owner, hash);
	return hash;
}
},{"phosphor-signaling":9}],9:[function(require,module,exports){

'use strict';

var Signal = (function () {
	function Signal() {
	}

	Signal.prototype.bind = function (sender) {
		return new BoundSignal(this, sender);
	};
	return Signal;
})();
exports.Signal = Signal;

function disconnectSender(sender) {
	var list = senderMap.get(sender);
	if (!list) {
		return;
	}
	var conn = list.first;
	while (conn !== null) {
		removeFromSendersList(conn);
		conn.callback = null;
		conn.thisArg = null;
		conn = conn.nextReceiver;
	}
	senderMap.delete(sender);
}
exports.disconnectSender = disconnectSender;

function disconnectReceiver(receiver) {
	var conn = receiverMap.get(receiver);
	if (!conn) {
		return;
	}
	while (conn !== null) {
		var next = conn.nextSender;
		conn.callback = null;
		conn.thisArg = null;
		conn.prevSender = null;
		conn.nextSender = null;
		conn = next;
	}
	receiverMap.delete(receiver);
}
exports.disconnectReceiver = disconnectReceiver;

function clearSignalData(obj) {
	disconnectSender(obj);
	disconnectReceiver(obj);
}
exports.clearSignalData = clearSignalData;

var BoundSignal = (function () {

	function BoundSignal(signal, sender) {
		this._signal = signal;
		this._sender = sender;
	}

	BoundSignal.prototype.connect = function (callback, thisArg) {
		return connect(this._sender, this._signal, callback, thisArg);
	};

	BoundSignal.prototype.disconnect = function (callback, thisArg) {
		return disconnect(this._sender, this._signal, callback, thisArg);
	};

	BoundSignal.prototype.emit = function (args) {
		emit(this._sender, this._signal, args);
	};
	return BoundSignal;
})();

var Connection = (function () {
	function Connection() {

		this.signal = null;

		this.callback = null;

		this.thisArg = null;

		this.nextReceiver = null;

		this.nextSender = null;

		this.prevSender = null;
	}
	return Connection;
})();

var ConnectionList = (function () {
	function ConnectionList() {

		this.refs = 0;

		this.first = null;

		this.last = null;
	}
	return ConnectionList;
})();

var senderMap = new WeakMap();

var receiverMap = new WeakMap();

function connect(sender, signal, callback, thisArg) {
	thisArg = thisArg || void 0;
	var list = senderMap.get(sender);
	if (list && findConnection(list, signal, callback, thisArg)) {
		return false;
	}
	var conn = new Connection();
	conn.signal = signal;
	conn.callback = callback;
	conn.thisArg = thisArg;
	if (!list) {
		list = new ConnectionList();
		list.first = conn;
		list.last = conn;
		senderMap.set(sender, list);
	}
	else if (list.last === null) {
		list.first = conn;
		list.last = conn;
	}
	else {
		list.last.nextReceiver = conn;
		list.last = conn;
	}
	var receiver = thisArg || callback;
	var head = receiverMap.get(receiver);
	if (head) {
		head.prevSender = conn;
		conn.nextSender = head;
	}
	receiverMap.set(receiver, conn);
	return true;
}

function disconnect(sender, signal, callback, thisArg) {
	thisArg = thisArg || void 0;
	var list = senderMap.get(sender);
	if (!list) {
		return false;
	}
	var conn = findConnection(list, signal, callback, thisArg);
	if (!conn) {
		return false;
	}
	removeFromSendersList(conn);
	conn.callback = null;
	conn.thisArg = null;
	return true;
}

function emit(sender, signal, args) {
	var list = senderMap.get(sender);
	if (!list) {
		return;
	}
	list.refs++;
	try {
		var dirty = invokeList(list, sender, signal, args);
	}
	finally {
		list.refs--;
	}
	if (dirty && list.refs === 0) {
		cleanList(list);
	}
}

function findConnection(list, signal, callback, thisArg) {
	var conn = list.first;
	while (conn !== null) {
		if (conn.signal === signal &&
			conn.callback === callback &&
			conn.thisArg === thisArg) {
			return conn;
		}
		conn = conn.nextReceiver;
	}
	return null;
}

function invokeList(list, sender, signal, args) {
	var dirty = false;
	var last = list.last;
	var conn = list.first;
	while (conn !== null) {
		if (!conn.callback) {
			dirty = true;
		}
		else if (conn.signal === signal) {
			conn.callback.call(conn.thisArg, sender, args);
		}
		if (conn === last) {
			break;
		}
		conn = conn.nextReceiver;
	}
	return dirty;
}

function cleanList(list) {
	var prev;
	var conn = list.first;
	while (conn !== null) {
		var next = conn.nextReceiver;
		if (!conn.callback) {
			conn.nextReceiver = null;
		}
		else if (!prev) {
			list.first = conn;
			prev = conn;
		}
		else {
			prev.nextReceiver = conn;
			prev = conn;
		}
		conn = next;
	}
	if (!prev) {
		list.first = null;
		list.last = null;
	}
	else {
		prev.nextReceiver = null;
		list.last = prev;
	}
}

function removeFromSendersList(conn) {
	var receiver = conn.thisArg || conn.callback;
	var prev = conn.prevSender;
	var next = conn.nextSender;
	if (prev === null && next === null) {
		receiverMap.delete(receiver);
	}
	else if (prev === null) {
		receiverMap.set(receiver, next);
		next.prevSender = null;
	}
	else if (next === null) {
		prev.nextSender = null;
	}
	else {
		prev.nextSender = next;
		next.prevSender = prev;
	}
	conn.prevSender = null;
	conn.nextSender = null;
}
},{}],10:[function(require,module,exports){

'use strict';

var DisposableDelegate = (function () {

	function DisposableDelegate(callback) {
		this._callback = callback;
	}
	Object.defineProperty(DisposableDelegate.prototype, "isDisposed", {

		get: function () {
			return !this._callback;
		},
		enumerable: true,
		configurable: true
	});

	DisposableDelegate.prototype.dispose = function () {
		var callback = this._callback;
		this._callback = null;
		if (callback)
			callback();
	};
	return DisposableDelegate;
})();
exports.DisposableDelegate = DisposableDelegate;

var DisposableSet = (function () {

	function DisposableSet(items) {
		var _this = this;
		this._set = new Set();
		if (items)
			items.forEach(function (item) { return _this._set.add(item); });
	}
	Object.defineProperty(DisposableSet.prototype, "isDisposed", {

		get: function () {
			return !this._set;
		},
		enumerable: true,
		configurable: true
	});

	DisposableSet.prototype.dispose = function () {
		var set = this._set;
		this._set = null;
		if (set)
			set.forEach(function (item) { return item.dispose(); });
	};

	DisposableSet.prototype.add = function (item) {
		if (!this._set) {
			throw new Error('object is disposed');
		}
		this._set.add(item);
	};

	DisposableSet.prototype.remove = function (item) {
		if (!this._set) {
			throw new Error('object is disposed');
		}
		this._set.delete(item);
	};

	DisposableSet.prototype.clear = function () {
		if (!this._set) {
			throw new Error('object is disposed');
		}
		this._set.clear();
	};
	return DisposableSet;
})();
exports.DisposableSet = DisposableSet;
},{}],11:[function(require,module,exports){
var css = ".p-DockTabPanel-overlay{box-sizing:border-box;position:absolute;top:0;left:0;right:0;bottom:0;z-index:2;transition:all 150ms ease}.p-Tab.p-mod-docking{position:absolute}"; (require("browserify-css").createStyle(css, { "href": "node_modules/phosphor-dockpanel/lib/index.css"})); module.exports = css;
},{"browserify-css":2}],12:[function(require,module,exports){

'use strict';
var __extends = (this && this.__extends) || function (d, b) {
	for (var p in b) if (b.hasOwnProperty(p)) d[p] = b[p];
	function __() { this.constructor = d; }
	d.prototype = b === null ? Object.create(b) : (__.prototype = b.prototype, new __());
};
var arrays = require('phosphor-arrays');
var phosphor_boxpanel_1 = require('phosphor-boxpanel');
var phosphor_domutil_1 = require('phosphor-domutil');
var phosphor_properties_1 = require('phosphor-properties');
var phosphor_splitpanel_1 = require('phosphor-splitpanel');
var phosphor_stackedpanel_1 = require('phosphor-stackedpanel');
var phosphor_tabs_1 = require('phosphor-tabs');
require('./index.css');

var DOCK_PANEL_CLASS = 'p-DockPanel';

var DOCK_SPLIT_PANEL_CLASS = 'p-DockSplitPanel';

var DOCK_TAB_PANEL_CLASS = 'p-DockTabPanel';

var OVERLAY_CLASS = 'p-DockTabPanel-overlay';

var DOCKING_CLASS = 'p-mod-docking';

(function (DockMode) {

	DockMode[DockMode["SplitTop"] = 0] = "SplitTop";

	DockMode[DockMode["SplitLeft"] = 1] = "SplitLeft";

	DockMode[DockMode["SplitRight"] = 2] = "SplitRight";

	DockMode[DockMode["SplitBottom"] = 3] = "SplitBottom";

	DockMode[DockMode["TabBefore"] = 4] = "TabBefore";

	DockMode[DockMode["TabAfter"] = 5] = "TabAfter";
})(exports.DockMode || (exports.DockMode = {}));
var DockMode = exports.DockMode;

var DockPanel = (function (_super) {
	__extends(DockPanel, _super);

	function DockPanel() {
		_super.call(this);
		this._ignoreRemoved = false;
		this._items = [];
		this._dragData = null;
		this.addClass(DOCK_PANEL_CLASS);
		this._root = this._createSplitPanel(phosphor_splitpanel_1.Orientation.Horizontal);
		this.addChild(this._root);
	}

	DockPanel.getTab = function (widget) {
		return DockPanel.tabProperty.get(widget);
	};

	DockPanel.setTab = function (widget, tab) {
		DockPanel.tabProperty.set(widget, tab);
	};

	DockPanel.prototype.dispose = function () {
		this._abortDrag();
		this._root = null;
		this._items.length = 0;
		_super.prototype.dispose.call(this);
	};
	Object.defineProperty(DockPanel.prototype, "handleSize", {

		get: function () {
			return DockPanel.handleSizeProperty.get(this);
		},

		set: function (value) {
			DockPanel.handleSizeProperty.set(this, value);
		},
		enumerable: true,
		configurable: true
	});

	DockPanel.prototype.addWidget = function (widget, mode, ref) {
		if (widget === ref) {
			throw new Error('invalid ref widget');
		}
		if (!DockPanel.getTab(widget)) {
			throw new Error('`DockPanel.tab` property not set');
		}
		switch (mode) {
			case DockMode.SplitTop:
				this._splitWidget(widget, ref, phosphor_splitpanel_1.Orientation.Vertical, false);
				break;
			case DockMode.SplitLeft:
				this._splitWidget(widget, ref, phosphor_splitpanel_1.Orientation.Horizontal, false);
				break;
			case DockMode.SplitRight:
				this._splitWidget(widget, ref, phosphor_splitpanel_1.Orientation.Horizontal, true);
				break;
			case DockMode.SplitBottom:
				this._splitWidget(widget, ref, phosphor_splitpanel_1.Orientation.Vertical, true);
				break;
			case DockMode.TabBefore:
				this._tabifyWidget(widget, ref, false);
				break;
			case DockMode.TabAfter:
				this._tabifyWidget(widget, ref, true);
				break;
			default:
				this._addPanel(widget, phosphor_splitpanel_1.Orientation.Horizontal, false);
				break;
		}
	};

	DockPanel.prototype.handleEvent = function (event) {
		switch (event.type) {
			case 'mousemove':
				this._evtMouseMove(event);
				break;
			case 'mouseup':
				this._evtMouseUp(event);
				break;
			case 'contextmenu':
				event.preventDefault();
				event.stopPropagation();
				break;
		}
	};

	DockPanel.prototype._splitWidget = function (widget, ref, orientation, after) {
		var item = ref ? this._findItemByWidget(ref) : void 0;
		if (item) {
			this._splitPanel(item.panel, widget, orientation, after);
		}
		else {
			this._addPanel(widget, orientation, after);
		}
	};

	DockPanel.prototype._tabifyWidget = function (widget, ref, after) {
		var item = ref ? this._findItemByWidget(ref) : void 0;
		if (item) {
			this._tabifyPanel(item, widget, after);
		}
		else {
			this._addPanel(widget, phosphor_splitpanel_1.Orientation.Horizontal, after);
		}
	};

	DockPanel.prototype._addPanel = function (widget, orientation, after) {
		widget.parent = null;
		var panel = this._createTabPanel();
		var tab = DockPanel.getTab(widget);
		this._items.push({ tab: tab, widget: widget, panel: panel });
		panel.stack.addChild(widget);
		panel.tabs.addTab(tab);
		this._ensureRoot(orientation);
		this._root.insertChild(after ? this._root.childCount : 0, panel);
	};

	DockPanel.prototype._splitPanel = function (target, widget, orientation, after) {
		widget.parent = null;
		var panel = this._createTabPanel();
		var tab = DockPanel.getTab(widget);
		this._items.push({ tab: tab, widget: widget, panel: panel });
		panel.stack.addChild(widget);
		panel.tabs.addTab(tab);
		var splitPanel = target.parent;
		if (splitPanel.orientation !== orientation) {
			if (splitPanel.childCount <= 1) {
				splitPanel.orientation = orientation;
				splitPanel.insertChild(+after, panel);
				splitPanel.setSizes([1, 1]);
			}
			else {
				var sizes = splitPanel.sizes();
				var i = splitPanel.childIndex(target);
				var childSplit = this._createSplitPanel(orientation);
				childSplit.addChild(target);
				childSplit.insertChild(+after, panel);
				splitPanel.insertChild(i, childSplit);
				splitPanel.setSizes(sizes);
				childSplit.setSizes([1, 1]);
			}
		}
		else {
			var i = splitPanel.childIndex(target);
			var sizes = splitPanel.sizes();
			var size = sizes[i] = sizes[i] / 2;
			splitPanel.insertChild(i + (+after), panel);
			arrays.insert(sizes, i + (+after), size);
			splitPanel.setSizes(sizes);
		}
	};

	DockPanel.prototype._tabifyPanel = function (item, widget, after) {
		widget.parent = null;
		var tab = DockPanel.getTab(widget);
		this._items.push({ tab: tab, widget: widget, panel: item.panel });
		var i = item.panel.stack.childIndex(item.widget);
		item.panel.stack.addChild(widget);
		item.panel.tabs.insertTab(i + (+after), tab);
	};

	DockPanel.prototype._evtMouseMove = function (event) {
		event.preventDefault();
		event.stopPropagation();
		var dragData = this._dragData;
		if (!dragData) {
			return;
		}
		var clientX = event.clientX;
		var clientY = event.clientY;
		var hitPanel = iterTabPanels(this._root, function (panel) {
			return phosphor_domutil_1.hitTest(panel.node, clientX, clientY) ? panel : void 0;
		});
		if (dragData.lastHitPanel && dragData.lastHitPanel !== hitPanel) {
			dragData.lastHitPanel.hideOverlay();
		}
		dragData.lastHitPanel = null;
		var item = dragData.item;
		var tabStyle = item.tab.node.style;
		if (!hitPanel) {
			tabStyle.left = clientX + 'px';
			tabStyle.top = clientY + 'px';
			return;
		}
		if (!phosphor_domutil_1.hitTest(hitPanel.tabs.node, clientX, clientY)) {
			dragData.lastHitPanel = hitPanel;
			if (hitPanel !== item.panel || hitPanel.tabs.tabCount > 0) {
				hitPanel.showOverlay(clientX, clientY);
			}
			tabStyle.left = clientX + 'px';
			tabStyle.top = clientY + 'px';
			return;
		}
		hitPanel.hideOverlay();
		if (hitPanel !== item.panel) {
			dragData.tempPanel = hitPanel;
			dragData.tempTab = hitPanel.tabs.selectedTab;
		}
		item.tab.removeClass(DOCKING_CLASS);
		tabStyle.top = '';
		tabStyle.left = '';
		hitPanel.tabs.attachTab(item.tab, clientX);
		document.removeEventListener('mousemove', this, true);
	};

	DockPanel.prototype._evtMouseUp = function (event) {
		if (event.button !== 0) {
			return;
		}
		event.preventDefault();
		event.stopPropagation();
		document.removeEventListener('mouseup', this, true);
		document.removeEventListener('mousemove', this, true);
		document.removeEventListener('contextmenu', this, true);
		var dragData = this._dragData;
		if (!dragData) {
			return;
		}
		this._dragData = null;
		dragData.cursorGrab.dispose();
		if (dragData.lastHitPanel) {
			dragData.lastHitPanel.hideOverlay();
		}
		var item = dragData.item;
		var ownPanel = item.panel;
		var ownBar = ownPanel.tabs;
		var ownCount = ownBar.tabCount;
		var itemTab = item.tab;
		if (dragData.tempPanel) {
			this._ignoreRemoved = true;
			item.panel = dragData.tempPanel;
			item.panel.stack.addChild(item.widget);
			item.panel.stack.currentWidget = item.widget;
			this._ignoreRemoved = false;
			if (ownPanel.stack.childCount === 0) {
				this._removePanel(ownPanel);
			}
			else {
				var i = ownBar.tabIndex(dragData.prevTab);
				if (i === -1)
					i = Math.min(dragData.index, ownCount - 1);
				ownBar.selectedTab = ownBar.tabAt(i);
			}
			return;
		}
		var mode = SplitMode.Invalid;
		var hitPanel = dragData.lastHitPanel;
		if (hitPanel && (hitPanel !== ownPanel || ownCount !== 0)) {
			mode = hitPanel.splitModeAt(event.clientX, event.clientY);
		}
		var tabStyle = itemTab.node.style;
		if (mode === SplitMode.Invalid) {
			if (ownBar.selectedTab !== itemTab) {
				itemTab.removeClass(DOCKING_CLASS);
				tabStyle.top = '';
				tabStyle.left = '';
				ownBar.insertTab(dragData.index, itemTab);
			}
			return;
		}
		document.body.removeChild(itemTab.node);
		itemTab.removeClass(DOCKING_CLASS);
		tabStyle.top = '';
		tabStyle.left = '';
		var after = mode === SplitMode.Right || mode === SplitMode.Bottom;
		var horiz = mode === SplitMode.Left || mode === SplitMode.Right;
		var orientation = horiz ? phosphor_splitpanel_1.Orientation.Horizontal : phosphor_splitpanel_1.Orientation.Vertical;
		this._splitPanel(hitPanel, item.widget, orientation, after);
		var i = ownBar.tabIndex(dragData.prevTab);
		if (i === -1)
			i = Math.min(dragData.index, ownCount - 1);
		ownBar.selectedTab = ownBar.tabAt(i);
	};

	DockPanel.prototype._ensureRoot = function (orientation) {
		if (this._root.orientation === orientation) {
			return;
		}
		if (this._root.childCount <= 1) {
			this._root.orientation = orientation;
			return;
		}
		var panel = this._createSplitPanel(orientation);
		panel.addChild(this._root);
		this._root = panel;
		this.addChild(panel);
	};

	DockPanel.prototype._createTabPanel = function () {
		var panel = new DockTabPanel();
		panel.tabs.tabSelected.connect(this._onTabSelected, this);
		panel.tabs.tabCloseRequested.connect(this._onTabCloseRequested, this);
		panel.tabs.tabDetachRequested.connect(this._onTabDetachRequested, this);
		panel.stack.widgetRemoved.connect(this._onWidgetRemoved, this);
		return panel;
	};

	DockPanel.prototype._createSplitPanel = function (orientation) {
		var panel = new DockSplitPanel();
		panel.orientation = orientation;
		panel.handleSize = this.handleSize;
		return panel;
	};

	DockPanel.prototype._removePanel = function (panel) {
		var splitPanel = panel.parent;
		panel.dispose();
		if (splitPanel.childCount > 1) {
			return;
		}
		if (splitPanel === this._root) {
			if (splitPanel.childCount === 1) {
				var child = splitPanel.childAt(0);
				if (child instanceof DockSplitPanel) {
					var sizes = child.sizes();
					splitPanel.parent = null;
					this._root = child;
					this.addChild(child);
					child.setSizes(sizes);
					splitPanel.dispose();
				}
			}
			return;
		}
		var gParent = splitPanel.parent;
		var gSizes = gParent.sizes();
		var gChild = splitPanel.childAt(0);
		var index = gParent.childIndex(splitPanel);
		splitPanel.parent = null;
		if (gChild instanceof DockTabPanel) {
			gParent.insertChild(index, gChild);
		}
		else {
			var gcsp = gChild;
			var gcspSizes = gcsp.sizes();
			var sizeShare = arrays.removeAt(gSizes, index);
			for (var i = 0; gcsp.childCount !== 0; ++i) {
				gParent.insertChild(index + i, gcsp.childAt(0));
				arrays.insert(gSizes, index + i, sizeShare * gcspSizes[i]);
			}
		}
		gParent.setSizes(gSizes);
		splitPanel.dispose();
	};

	DockPanel.prototype._abortDrag = function () {
		var dragData = this._dragData;
		if (!dragData) {
			return;
		}
		this._dragData = null;
		document.removeEventListener('mouseup', this, true);
		document.removeEventListener('mousemove', this, true);
		document.removeEventListener('contextmenu', this, true);
		dragData.cursorGrab.dispose();
		if (dragData.lastHitPanel) {
			dragData.lastHitPanel.hideOverlay();
		}
		if (dragData.tempPanel) {
			var tabs = dragData.tempPanel.tabs;
			tabs.removeTab(tabs.selectedTab);
			tabs.selectedTab = dragData.tempTab;
		}
		var item = dragData.item;
		var ownBar = item.panel.tabs;
		if (ownBar.selectedTab !== item.tab) {
			var tabStyle = item.tab.node.style;
			item.tab.removeClass(DOCKING_CLASS);
			tabStyle.top = '';
			tabStyle.left = '';
			ownBar.insertTab(dragData.index, item.tab);
		}
	};

	DockPanel.prototype._findItemByTab = function (tab) {
		return arrays.find(this._items, function (item) { return item.tab === tab; });
	};

	DockPanel.prototype._findItemByWidget = function (widget) {
		return arrays.find(this._items, function (item) { return item.widget === widget; });
	};

	DockPanel.prototype._onHandleSizeChanged = function (old, value) {
		iterSplitPanels(this._root, function (panel) { panel.handleSize = value; });
	};

	DockPanel.prototype._onTabSelected = function (sender, args) {
		var item = this._findItemByTab(args.tab);
		if (item && item.panel.tabs === sender) {
			item.panel.stack.currentWidget = item.widget;
		}
	};

	DockPanel.prototype._onTabCloseRequested = function (sender, args) {
		var item = this._findItemByTab(args.tab);
		if (item)
			item.widget.close();
	};

	DockPanel.prototype._onTabDetachRequested = function (sender, args) {
		var item = this._findItemByTab(args.tab);
		if (!item) {
			return;
		}
		if (!this._dragData) {
			this._dragData = {
				item: item,
				index: args.index,
				prevTab: sender.previousTab,
				lastHitPanel: null,
				cursorGrab: null,
				tempPanel: null,
				tempTab: null,
			};
		}
		var dragData = this._dragData;
		dragData.cursorGrab = phosphor_domutil_1.overrideCursor('default');
		if (item.panel.tabs === sender) {
			sender.selectedTab = null;
			sender.removeTabAt(args.index);
		}
		else {
			sender.removeTabAt(args.index);
			sender.selectedTab = dragData.tempTab;
		}
		dragData.tempPanel = null;
		dragData.tempTab = null;
		var style = args.tab.node.style;
		style.zIndex = '';
		style.top = args.clientY + 'px';
		style.left = args.clientX + 'px';
		args.tab.addClass(DOCKING_CLASS);
		document.body.appendChild(args.tab.node);
		document.addEventListener('mouseup', this, true);
		document.addEventListener('mousemove', this, true);
		document.addEventListener('contextmenu', this, true);
	};

	DockPanel.prototype._onWidgetRemoved = function (sender, args) {
		if (this._ignoreRemoved) {
			return;
		}
		var item = this._findItemByWidget(args.widget);
		if (!item) {
			return;
		}
		this._abortDrag();
		arrays.remove(this._items, item);
		item.panel.tabs.removeTab(item.tab);
		if (item.panel.stack.childCount === 0) {
			this._removePanel(item.panel);
		}
	};

	DockPanel.SplitTop = DockMode.SplitTop;

	DockPanel.SplitLeft = DockMode.SplitLeft;

	DockPanel.SplitRight = DockMode.SplitRight;

	DockPanel.SplitBottom = DockMode.SplitBottom;

	DockPanel.TabBefore = DockMode.TabBefore;

	DockPanel.TabAfter = DockMode.TabAfter;

	DockPanel.tabProperty = new phosphor_properties_1.Property({
		value: null,
		coerce: function (owner, value) { return value || null; },
	});

	DockPanel.handleSizeProperty = new phosphor_properties_1.Property({
		value: 3,
		coerce: function (owner, value) { return Math.max(0, value | 0); },
		changed: function (owner, old, value) { return owner._onHandleSizeChanged(old, value); },
	});
	return DockPanel;
})(phosphor_boxpanel_1.BoxPanel);
exports.DockPanel = DockPanel;

function iterTabPanels(root, cb) {
	for (var i = 0, n = root.childCount; i < n; ++i) {
		var result = void 0;
		var panel = root.childAt(i);
		if (panel instanceof DockTabPanel) {
			result = cb(panel);
		}
		else if (panel instanceof DockSplitPanel) {
			result = iterTabPanels(panel, cb);
		}
		if (result !== void 0) {
			return result;
		}
	}
	return void 0;
}

function iterSplitPanels(root, cb) {
	var result = cb(root);
	if (result !== void 0) {
		return result;
	}
	for (var i = 0, n = root.childCount; i < n; ++i) {
		var panel = root.childAt(i);
		if (panel instanceof DockSplitPanel) {
			result = iterSplitPanels(panel, cb);
			if (result !== void 0) {
				return result;
			}
		}
	}
	return void 0;
}

function createOverlay() {
	var overlay = document.createElement('div');
	overlay.className = OVERLAY_CLASS;
	overlay.style.display = 'none';
	return overlay;
}

var SplitMode;
(function (SplitMode) {
	SplitMode[SplitMode["Top"] = 0] = "Top";
	SplitMode[SplitMode["Left"] = 1] = "Left";
	SplitMode[SplitMode["Right"] = 2] = "Right";
	SplitMode[SplitMode["Bottom"] = 3] = "Bottom";
	SplitMode[SplitMode["Invalid"] = 4] = "Invalid";
})(SplitMode || (SplitMode = {}));

var DockTabPanel = (function (_super) {
	__extends(DockTabPanel, _super);

	function DockTabPanel() {
		_super.call(this);
		this._overlayTimer = 0;
		this._overlayHidden = true;
		this._tabs = new phosphor_tabs_1.TabBar();
		this._stack = new phosphor_stackedpanel_1.StackedPanel();
		this.addClass(DOCK_TAB_PANEL_CLASS);
		this.direction = phosphor_boxpanel_1.BoxPanel.TopToBottom;
		this.spacing = 0;
		phosphor_boxpanel_1.BoxPanel.setStretch(this._tabs, 0);
		phosphor_boxpanel_1.BoxPanel.setStretch(this._stack, 1);
		this.addChild(this._tabs);
		this.addChild(this._stack);
		this._overlay = createOverlay();
		this.node.appendChild(this._overlay);
	}

	DockTabPanel.prototype.dispose = function () {
		this._clearOverlayTimer();
		this._tabs = null;
		this._stack = null;
		this._overlay = null;
		_super.prototype.dispose.call(this);
	};
	Object.defineProperty(DockTabPanel.prototype, "tabs", {

		get: function () {
			return this._tabs;
		},
		enumerable: true,
		configurable: true
	});
	Object.defineProperty(DockTabPanel.prototype, "stack", {

		get: function () {
			return this._stack;
		},
		enumerable: true,
		configurable: true
	});

	DockTabPanel.prototype.splitModeAt = function (clientX, clientY) {
		var rect = this.stack.node.getBoundingClientRect();
		var fracX = (clientX - rect.left) / rect.width;
		var fracY = (clientY - rect.top) / rect.height;
		if (fracX < 0.0 || fracX > 1.0 || fracY < 0.0 || fracY > 1.0) {
			return SplitMode.Invalid;
		}
		var mode;
		var normX = fracX > 0.5 ? 1 - fracX : fracX;
		var normY = fracY > 0.5 ? 1 - fracY : fracY;
		if (normX < normY) {
			mode = fracX <= 0.5 ? SplitMode.Left : SplitMode.Right;
		}
		else {
			mode = fracY <= 0.5 ? SplitMode.Top : SplitMode.Bottom;
		}
		return mode;
	};

	DockTabPanel.prototype.showOverlay = function (clientX, clientY) {
		this._clearOverlayTimer();
		var rect = this.node.getBoundingClientRect();
		var box = this.boxSizing;
		var top = box.paddingTop;
		var left = box.paddingLeft;
		var right = box.paddingRight;
		var bottom = box.paddingBottom;
		switch (this.splitModeAt(clientX, clientY)) {
			case SplitMode.Left:
				right = rect.width / 2;
				break;
			case SplitMode.Right:
				left = rect.width / 2;
				break;
			case SplitMode.Top:
				bottom = rect.height / 2;
				break;
			case SplitMode.Bottom:
				top = rect.height / 2;
				break;
		}
		var style = this._overlay.style;
		if (this._overlayHidden) {
			this._overlayHidden = false;
			style.top = clientY - rect.top + 'px';
			style.left = clientX - rect.left + 'px';
			style.right = rect.right - clientX + 'px';
			style.bottom = rect.bottom - clientY + 'px';
			style.display = '';
			this._overlay.offsetWidth;
		}
		style.opacity = '1';
		style.top = top + 'px';
		style.left = left + 'px';
		style.right = right + 'px';
		style.bottom = bottom + 'px';
	};

	DockTabPanel.prototype.hideOverlay = function () {
		var _this = this;
		if (this._overlayHidden) {
			return;
		}
		this._clearOverlayTimer();
		this._overlayHidden = true;
		this._overlay.style.opacity = '0';
		this._overlayTimer = setTimeout(function () {
			_this._overlayTimer = 0;
			_this._overlay.style.display = 'none';
		}, 150);
	};

	DockTabPanel.prototype._clearOverlayTimer = function () {
		if (this._overlayTimer) {
			clearTimeout(this._overlayTimer);
			this._overlayTimer = 0;
		}
	};
	return DockTabPanel;
})(phosphor_boxpanel_1.BoxPanel);

var DockSplitPanel = (function (_super) {
	__extends(DockSplitPanel, _super);

	function DockSplitPanel() {
		_super.call(this);
		this.addClass(DOCK_SPLIT_PANEL_CLASS);
	}
	return DockSplitPanel;
})(phosphor_splitpanel_1.SplitPanel);
},{"./index.css":11,"phosphor-arrays":13,"phosphor-boxpanel":5,"phosphor-domutil":16,"phosphor-properties":17,"phosphor-splitpanel":46,"phosphor-stackedpanel":20,"phosphor-tabs":59}],13:[function(require,module,exports){
arguments[4][6][0].apply(exports,arguments)
},{"dup":6}],14:[function(require,module,exports){
arguments[4][10][0].apply(exports,arguments)
},{"dup":10}],15:[function(require,module,exports){
var css = "body.p-mod-override-cursor *{cursor:inherit!important}"; (require("browserify-css").createStyle(css, { "href": "node_modules/phosphor-dockpanel/node_modules/phosphor-domutil/lib/index.css"})); module.exports = css;
},{"browserify-css":2}],16:[function(require,module,exports){

'use strict';
var phosphor_disposable_1 = require('phosphor-disposable');
require('./index.css');

exports.OVERRIDE_CURSOR_CLASS = 'p-mod-override-cursor';

var overrideID = 0;

function overrideCursor(cursor) {
	var id = ++overrideID;
	var body = document.body;
	body.style.cursor = cursor;
	body.classList.add(exports.OVERRIDE_CURSOR_CLASS);
	return new phosphor_disposable_1.DisposableDelegate(function () {
		if (id === overrideID) {
			body.style.cursor = '';
			body.classList.remove(exports.OVERRIDE_CURSOR_CLASS);
		}
	});
}
exports.overrideCursor = overrideCursor;

function hitTest(node, clientX, clientY) {
	var rect = node.getBoundingClientRect();
	return (clientX >= rect.left &&
		clientX < rect.right &&
		clientY >= rect.top &&
		clientY < rect.bottom);
}
exports.hitTest = hitTest;

function boxSizing(node) {
	var cstyle = window.getComputedStyle(node);
	var bt = parseInt(cstyle.borderTopWidth, 10) || 0;
	var bl = parseInt(cstyle.borderLeftWidth, 10) || 0;
	var br = parseInt(cstyle.borderRightWidth, 10) || 0;
	var bb = parseInt(cstyle.borderBottomWidth, 10) || 0;
	var pt = parseInt(cstyle.paddingTop, 10) || 0;
	var pl = parseInt(cstyle.paddingLeft, 10) || 0;
	var pr = parseInt(cstyle.paddingRight, 10) || 0;
	var pb = parseInt(cstyle.paddingBottom, 10) || 0;
	var hs = bl + pl + pr + br;
	var vs = bt + pt + pb + bb;
	return {
		borderTop: bt,
		borderLeft: bl,
		borderRight: br,
		borderBottom: bb,
		paddingTop: pt,
		paddingLeft: pl,
		paddingRight: pr,
		paddingBottom: pb,
		horizontalSum: hs,
		verticalSum: vs,
	};
}
exports.boxSizing = boxSizing;

function sizeLimits(node) {
	var cstyle = window.getComputedStyle(node);
	return {
		minWidth: parseInt(cstyle.minWidth, 10) || 0,
		minHeight: parseInt(cstyle.minHeight, 10) || 0,
		maxWidth: parseInt(cstyle.maxWidth, 10) || Infinity,
		maxHeight: parseInt(cstyle.maxHeight, 10) || Infinity,
	};
}
exports.sizeLimits = sizeLimits;
},{"./index.css":15,"phosphor-disposable":14}],17:[function(require,module,exports){
arguments[4][8][0].apply(exports,arguments)
},{"dup":8,"phosphor-signaling":18}],18:[function(require,module,exports){
arguments[4][9][0].apply(exports,arguments)
},{"dup":9}],19:[function(require,module,exports){
var css = ".p-StackedPanel{position:relative}.p-StackedPanel>.p-Widget{position:absolute}"; (require("browserify-css").createStyle(css, { "href": "node_modules/phosphor-dockpanel/node_modules/phosphor-stackedpanel/lib/index.css"})); module.exports = css;
},{"browserify-css":2}],20:[function(require,module,exports){

'use strict';
var __extends = (this && this.__extends) || function (d, b) {
	for (var p in b) if (b.hasOwnProperty(p)) d[p] = b[p];
	function __() { this.constructor = d; }
	d.prototype = b === null ? Object.create(b) : (__.prototype = b.prototype, new __());
};
var phosphor_messaging_1 = require('phosphor-messaging');
var phosphor_properties_1 = require('phosphor-properties');
var phosphor_signaling_1 = require('phosphor-signaling');
var phosphor_widget_1 = require('phosphor-widget');
require('./index.css');

exports.STACKED_PANEL_CLASS = 'p-StackedPanel';

var StackedPanel = (function (_super) {
	__extends(StackedPanel, _super);

	function StackedPanel() {
		_super.call(this);
		this.addClass(exports.STACKED_PANEL_CLASS);
	}
	Object.defineProperty(StackedPanel.prototype, "currentChanged", {

		get: function () {
			return StackedPanel.currentChangedSignal.bind(this);
		},
		enumerable: true,
		configurable: true
	});
	Object.defineProperty(StackedPanel.prototype, "widgetRemoved", {

		get: function () {
			return StackedPanel.widgetRemovedSignal.bind(this);
		},
		enumerable: true,
		configurable: true
	});
	Object.defineProperty(StackedPanel.prototype, "currentWidget", {

		get: function () {
			return StackedPanel.currentWidgetProperty.get(this);
		},

		set: function (widget) {
			StackedPanel.currentWidgetProperty.set(this, widget);
		},
		enumerable: true,
		configurable: true
	});

	StackedPanel.prototype.onChildAdded = function (msg) {
		msg.child.hidden = true;
		this.node.appendChild(msg.child.node);
		if (this.isAttached)
			phosphor_messaging_1.sendMessage(msg.child, phosphor_widget_1.MSG_AFTER_ATTACH);
	};

	StackedPanel.prototype.onChildRemoved = function (msg) {
		if (msg.child === this.currentWidget)
			this.currentWidget = null;
		if (this.isAttached)
			phosphor_messaging_1.sendMessage(msg.child, phosphor_widget_1.MSG_BEFORE_DETACH);
		this.node.removeChild(msg.child.node);
		msg.child.clearOffsetGeometry();
		this.widgetRemoved.emit({ index: msg.previousIndex, widget: msg.child });
	};

	StackedPanel.prototype.onChildMoved = function (msg) { };

	StackedPanel.prototype.onAfterShow = function (msg) {
		this.update(true);
	};

	StackedPanel.prototype.onAfterAttach = function (msg) {
		phosphor_messaging_1.postMessage(this, phosphor_widget_1.MSG_LAYOUT_REQUEST);
	};

	StackedPanel.prototype.onResize = function (msg) {
		if (this.isVisible) {
			if (msg.width < 0 || msg.height < 0) {
				var rect = this.offsetRect;
				this._layoutChildren(rect.width, rect.height);
			}
			else {
				this._layoutChildren(msg.width, msg.height);
			}
		}
	};

	StackedPanel.prototype.onUpdateRequest = function (msg) {
		if (this.isVisible) {
			var rect = this.offsetRect;
			this._layoutChildren(rect.width, rect.height);
		}
	};

	StackedPanel.prototype.onLayoutRequest = function (msg) {
		if (this.isAttached) {
			this._setupGeometry();
		}
	};

	StackedPanel.prototype._setupGeometry = function () {
		var minW = 0;
		var minH = 0;
		var maxW = Infinity;
		var maxH = Infinity;
		var widget = this.currentWidget;
		if (widget) {
			var limits = widget.sizeLimits;
			minW = limits.minWidth;
			minH = limits.minHeight;
			maxW = limits.maxWidth;
			maxH = limits.maxHeight;
		}
		var box = this.boxSizing;
		minW += box.horizontalSum;
		minH += box.verticalSum;
		maxW += box.horizontalSum;
		maxH += box.verticalSum;
		this.setSizeLimits(minW, minH, maxW, maxH);
		if (this.parent)
			phosphor_messaging_1.sendMessage(this.parent, phosphor_widget_1.MSG_LAYOUT_REQUEST);
		this.update(true);
	};

	StackedPanel.prototype._layoutChildren = function (offsetWidth, offsetHeight) {
		var widget = this.currentWidget;
		if (!widget) {
			return;
		}
		var box = this.boxSizing;
		var top = box.paddingTop;
		var left = box.paddingLeft;
		var width = offsetWidth - box.horizontalSum;
		var height = offsetHeight - box.verticalSum;
		widget.setOffsetGeometry(left, top, width, height);
	};

	StackedPanel.prototype._onCurrentWidgetChanged = function (old, val) {
		if (old)
			old.hidden = true;
		if (val)
			val.hidden = false;
		phosphor_messaging_1.sendMessage(this, phosphor_widget_1.MSG_LAYOUT_REQUEST);
		this.currentChanged.emit({ index: this.childIndex(val), widget: val });
	};

	StackedPanel.currentChangedSignal = new phosphor_signaling_1.Signal();

	StackedPanel.widgetRemovedSignal = new phosphor_signaling_1.Signal();

	StackedPanel.currentWidgetProperty = new phosphor_properties_1.Property({
		value: null,
		coerce: function (owner, val) { return (val && val.parent === owner) ? val : null; },
		changed: function (owner, old, val) { return owner._onCurrentWidgetChanged(old, val); },
	});
	return StackedPanel;
})(phosphor_widget_1.Widget);
exports.StackedPanel = StackedPanel;
},{"./index.css":19,"phosphor-messaging":40,"phosphor-properties":17,"phosphor-signaling":18,"phosphor-widget":72}],21:[function(require,module,exports){
var css = "body.p-mod-override-cursor *{cursor:inherit!important}"; (require("browserify-css").createStyle(css, { "href": "node_modules/phosphor-domutil/lib/index.css"})); module.exports = css;
},{"browserify-css":2}],22:[function(require,module,exports){
arguments[4][16][0].apply(exports,arguments)
},{"./index.css":21,"dup":16,"phosphor-disposable":10}],23:[function(require,module,exports){
var css = ".p-GridPanel{position:relative}.p-GridPanel>.p-Widget{position:absolute}"; (require("browserify-css").createStyle(css, { "href": "node_modules/phosphor-gridpanel/lib/index.css"})); module.exports = css;
},{"browserify-css":2}],24:[function(require,module,exports){

'use strict';
var __extends = (this && this.__extends) || function (d, b) {
	for (var p in b) if (b.hasOwnProperty(p)) d[p] = b[p];
	function __() { this.constructor = d; }
	d.prototype = b === null ? Object.create(b) : (__.prototype = b.prototype, new __());
};
var phosphor_boxengine_1 = require('phosphor-boxengine');
var phosphor_messaging_1 = require('phosphor-messaging');
var phosphor_properties_1 = require('phosphor-properties');
var phosphor_widget_1 = require('phosphor-widget');
require('./index.css');

exports.GRID_PANEL_CLASS = 'p-GridPanel';

var GridPanel = (function (_super) {
	__extends(GridPanel, _super);

	function GridPanel() {
		_super.call(this);
		this._rowStarts = [];
		this._colStarts = [];
		this._rowSizers = [];
		this._colSizers = [];
		this.addClass(exports.GRID_PANEL_CLASS);
	}

	GridPanel.getRow = function (widget) {
		return GridPanel.rowProperty.get(widget);
	};

	GridPanel.setRow = function (widget, value) {
		GridPanel.rowProperty.set(widget, value);
	};

	GridPanel.getColumn = function (widget) {
		return GridPanel.columnProperty.get(widget);
	};

	GridPanel.setColumn = function (widget, value) {
		GridPanel.columnProperty.set(widget, value);
	};

	GridPanel.getRowSpan = function (widget) {
		return GridPanel.rowSpanProperty.get(widget);
	};

	GridPanel.setRowSpan = function (widget, value) {
		GridPanel.rowSpanProperty.set(widget, value);
	};

	GridPanel.getColumnSpan = function (widget) {
		return GridPanel.columnSpanProperty.get(widget);
	};

	GridPanel.setColumnSpan = function (widget, value) {
		GridPanel.columnSpanProperty.set(widget, value);
	};

	GridPanel.prototype.dispose = function () {
		this._rowStarts.length = 0;
		this._colStarts.length = 0;
		this._rowSizers.length = 0;
		this._colSizers.length = 0;
		_super.prototype.dispose.call(this);
	};
	Object.defineProperty(GridPanel.prototype, "rowSpecs", {

		get: function () {
			return GridPanel.rowSpecsProperty.get(this);
		},

		set: function (value) {
			GridPanel.rowSpecsProperty.set(this, value);
		},
		enumerable: true,
		configurable: true
	});
	Object.defineProperty(GridPanel.prototype, "columnSpecs", {

		get: function () {
			return GridPanel.columnSpecsProperty.get(this);
		},

		set: function (value) {
			GridPanel.columnSpecsProperty.set(this, value);
		},
		enumerable: true,
		configurable: true
	});
	Object.defineProperty(GridPanel.prototype, "rowSpacing", {

		get: function () {
			return GridPanel.rowSpacingProperty.get(this);
		},

		set: function (value) {
			GridPanel.rowSpacingProperty.set(this, value);
		},
		enumerable: true,
		configurable: true
	});
	Object.defineProperty(GridPanel.prototype, "columnSpacing", {

		get: function () {
			return GridPanel.columnSpacingProperty.get(this);
		},

		set: function (value) {
			GridPanel.columnSpacingProperty.set(this, value);
		},
		enumerable: true,
		configurable: true
	});

	GridPanel.prototype.onChildAdded = function (msg) {
		this.node.appendChild(msg.child.node);
		if (this.isAttached)
			phosphor_messaging_1.sendMessage(msg.child, phosphor_widget_1.MSG_AFTER_ATTACH);
		this.update();
	};

	GridPanel.prototype.onChildRemoved = function (msg) {
		if (this.isAttached)
			phosphor_messaging_1.sendMessage(msg.child, phosphor_widget_1.MSG_BEFORE_DETACH);
		this.node.removeChild(msg.child.node);
		msg.child.clearOffsetGeometry();
	};

	GridPanel.prototype.onChildMoved = function (msg) { };

	GridPanel.prototype.onAfterShow = function (msg) {
		this.update(true);
	};

	GridPanel.prototype.onAfterAttach = function (msg) {
		phosphor_messaging_1.postMessage(this, phosphor_widget_1.MSG_LAYOUT_REQUEST);
	};

	GridPanel.prototype.onChildShown = function (msg) {
		this.update();
	};

	GridPanel.prototype.onResize = function (msg) {
		if (this.isVisible) {
			if (msg.width < 0 || msg.height < 0) {
				var rect = this.offsetRect;
				this._layoutChildren(rect.width, rect.height);
			}
			else {
				this._layoutChildren(msg.width, msg.height);
			}
		}
	};

	GridPanel.prototype.onUpdateRequest = function (msg) {
		if (this.isVisible) {
			var rect = this.offsetRect;
			this._layoutChildren(rect.width, rect.height);
		}
	};

	GridPanel.prototype.onLayoutRequest = function (msg) {
		if (this.isAttached) {
			this._setupGeometry();
		}
	};

	GridPanel.prototype._setupGeometry = function () {
		var minW = 0;
		var minH = 0;
		var maxW = Infinity;
		var maxH = Infinity;
		var rowSpecs = this.rowSpecs;
		if (rowSpecs.length > 0) {
			var fixed = this.rowSpacing * (rowSpecs.length - 1);
			minH = rowSpecs.reduce(function (s, spec) { return s + spec.minSize; }, 0) + fixed;
			maxH = rowSpecs.reduce(function (s, spec) { return s + spec.maxSize; }, 0) + fixed;
		}
		var colSpecs = this.columnSpecs;
		if (colSpecs.length > 0) {
			var fixed = this.columnSpacing * (colSpecs.length - 1);
			minW = colSpecs.reduce(function (s, spec) { return s + spec.minSize; }, 0) + fixed;
			maxW = colSpecs.reduce(function (s, spec) { return s + spec.maxSize; }, 0) + fixed;
		}
		this._rowStarts = zeros(rowSpecs.length);
		this._colStarts = zeros(colSpecs.length);
		this._rowSizers = rowSpecs.map(makeSizer);
		this._colSizers = colSpecs.map(makeSizer);
		var box = this.boxSizing;
		minW += box.horizontalSum;
		minH += box.verticalSum;
		maxW += box.horizontalSum;
		maxH += box.verticalSum;
		this.setSizeLimits(minW, minH, maxW, maxH);
		if (this.parent)
			phosphor_messaging_1.sendMessage(this.parent, phosphor_widget_1.MSG_LAYOUT_REQUEST);
		this.update(true);
	};

	GridPanel.prototype._layoutChildren = function (offsetWidth, offsetHeight) {
		if (this.childCount === 0) {
			return;
		}
		var box = this.boxSizing;
		var top = box.paddingTop;
		var left = box.paddingLeft;
		var width = offsetWidth - box.horizontalSum;
		var height = offsetHeight - box.verticalSum;
		if (this._rowSizers.length === 0 || this._colSizers.length === 0) {
			for (var i = 0, n = this.childCount; i < n; ++i) {
				var widget = this.childAt(i);
				var limits = widget.sizeLimits;
				var w = Math.max(limits.minWidth, Math.min(width, limits.maxWidth));
				var h = Math.max(limits.minHeight, Math.min(height, limits.maxHeight));
				widget.setOffsetGeometry(left, top, w, h);
			}
			return;
		}
		var rowPos = top;
		var rowStarts = this._rowStarts;
		var rowSizers = this._rowSizers;
		var rowSpacing = this.rowSpacing;
		phosphor_boxengine_1.boxCalc(rowSizers, height - rowSpacing * (rowSizers.length - 1));
		for (var i = 0, n = rowSizers.length; i < n; ++i) {
			rowStarts[i] = rowPos;
			rowPos += rowSizers[i].size + rowSpacing;
		}
		var colPos = left;
		var colStarts = this._colStarts;
		var colSizers = this._colSizers;
		var colSpacing = this.columnSpacing;
		phosphor_boxengine_1.boxCalc(colSizers, width - colSpacing * (colSizers.length - 1));
		for (var i = 0, n = colSizers.length; i < n; ++i) {
			colStarts[i] = colPos;
			colPos += colSizers[i].size + colSpacing;
		}
		var maxRow = rowSizers.length - 1;
		var maxCol = colSizers.length - 1;
		for (var i = 0, n = this.childCount; i < n; ++i) {
			var widget = this.childAt(i);
			var r1 = Math.max(0, Math.min(GridPanel.getRow(widget), maxRow));
			var r2 = Math.min(r1 + GridPanel.getRowSpan(widget) - 1, maxRow);
			var y = rowStarts[r1];
			var h = rowStarts[r2] + rowSizers[r2].size - y;
			var c1 = Math.max(0, Math.min(GridPanel.getColumn(widget), maxCol));
			var c2 = Math.min(c1 + GridPanel.getColumnSpan(widget) - 1, maxCol);
			var x = colStarts[c1];
			var w = colStarts[c2] + colSizers[c2].size - x;
			var limits = widget.sizeLimits;
			w = Math.max(limits.minWidth, Math.min(w, limits.maxWidth));
			h = Math.max(limits.minHeight, Math.min(h, limits.maxHeight));
			widget.setOffsetGeometry(x, y, w, h);
		}
	};

	GridPanel.prototype._onGridSpecsChanged = function (old, value) {
		for (var i = 0, n = old.length; i < n; ++i) {
			phosphor_properties_1.Property.getChanged(old[i]).disconnect(this._onSpecChanged, this);
		}
		for (var i = 0, n = value.length; i < n; ++i) {
			phosphor_properties_1.Property.getChanged(value[i]).connect(this._onSpecChanged, this);
		}
		phosphor_messaging_1.postMessage(this, phosphor_widget_1.MSG_LAYOUT_REQUEST);
	};

	GridPanel.prototype._onSpecChanged = function (sender, args) {
		phosphor_messaging_1.postMessage(this, phosphor_widget_1.MSG_LAYOUT_REQUEST);
	};

	GridPanel.rowSpecsProperty = new phosphor_properties_1.Property({
		value: Object.freeze([]),
		coerce: function (owner, value) { return Object.freeze(value ? value.slice() : []); },
		changed: function (owner, old, value) { return owner._onGridSpecsChanged(old, value); },
	});

	GridPanel.columnSpecsProperty = new phosphor_properties_1.Property({
		value: Object.freeze([]),
		coerce: function (owner, value) { return Object.freeze(value ? value.slice() : []); },
		changed: function (owner, old, value) { return owner._onGridSpecsChanged(old, value); },
	});

	GridPanel.rowSpacingProperty = new phosphor_properties_1.Property({
		value: 8,
		coerce: function (owner, value) { return Math.max(0, value | 0); },
		changed: function (owner) { return phosphor_messaging_1.postMessage(owner, phosphor_widget_1.MSG_LAYOUT_REQUEST); },
	});

	GridPanel.columnSpacingProperty = new phosphor_properties_1.Property({
		value: 8,
		coerce: function (owner, value) { return Math.max(0, value | 0); },
		changed: function (owner) { return phosphor_messaging_1.postMessage(owner, phosphor_widget_1.MSG_LAYOUT_REQUEST); },
	});

	GridPanel.rowProperty = new phosphor_properties_1.Property({
		value: 0,
		coerce: function (owner, value) { return Math.max(0, value | 0); },
		changed: onWidgetChanged,
	});

	GridPanel.columnProperty = new phosphor_properties_1.Property({
		value: 0,
		coerce: function (owner, value) { return Math.max(0, value | 0); },
		changed: onWidgetChanged,
	});

	GridPanel.rowSpanProperty = new phosphor_properties_1.Property({
		value: 1,
		coerce: function (owner, value) { return Math.max(1, value | 0); },
		changed: onWidgetChanged,
	});

	GridPanel.columnSpanProperty = new phosphor_properties_1.Property({
		value: 1,
		coerce: function (owner, value) { return Math.max(1, value | 0); },
		changed: onWidgetChanged,
	});
	return GridPanel;
})(phosphor_widget_1.Widget);
exports.GridPanel = GridPanel;

var Spec = (function () {

	function Spec(options) {
		if (options === void 0) { options = {}; }
		if (options.sizeBasis !== void 0) {
			this.sizeBasis = options.sizeBasis;
		}
		if (options.minSize !== void 0) {
			this.minSize = options.minSize;
		}
		if (options.maxSize !== void 0) {
			this.maxSize = options.maxSize;
		}
		if (options.stretch !== void 0) {
			this.stretch = options.stretch;
		}
	}
	Object.defineProperty(Spec.prototype, "sizeBasis", {

		get: function () {
			return Spec.sizeBasisProperty.get(this);
		},

		set: function (value) {
			Spec.sizeBasisProperty.set(this, value);
		},
		enumerable: true,
		configurable: true
	});
	Object.defineProperty(Spec.prototype, "minSize", {

		get: function () {
			return Spec.minSizeProperty.get(this);
		},

		set: function (value) {
			Spec.minSizeProperty.set(this, value);
		},
		enumerable: true,
		configurable: true
	});
	Object.defineProperty(Spec.prototype, "maxSize", {

		get: function () {
			return Spec.maxSizeProperty.get(this);
		},

		set: function (value) {
			Spec.maxSizeProperty.set(this, value);
		},
		enumerable: true,
		configurable: true
	});
	Object.defineProperty(Spec.prototype, "stretch", {

		get: function () {
			return Spec.stretchProperty.get(this);
		},

		set: function (value) {
			Spec.stretchProperty.set(this, value);
		},
		enumerable: true,
		configurable: true
	});

	Spec.sizeBasisProperty = new phosphor_properties_1.Property({
		value: 0,
	});

	Spec.minSizeProperty = new phosphor_properties_1.Property({
		value: 0,
		coerce: function (owner, value) { return Math.max(0, value); },
	});

	Spec.maxSizeProperty = new phosphor_properties_1.Property({
		value: Infinity,
		coerce: function (owner, value) { return Math.max(0, value); },
	});

	Spec.stretchProperty = new phosphor_properties_1.Property({
		value: 1,
		coerce: function (owner, value) { return Math.max(0, value | 0); },
	});
	return Spec;
})();
exports.Spec = Spec;

function onWidgetChanged(owner) {
	if (owner.parent instanceof GridPanel) {
		owner.parent.update();
	}
}

function zeros(n) {
	var arr = new Array(n);
	for (var i = 0; i < n; ++i)
		arr[i] = 0;
	return arr;
}

function makeSizer(spec) {
	var sizer = new phosphor_boxengine_1.BoxSizer();
	sizer.sizeHint = spec.sizeBasis;
	sizer.minSize = spec.minSize;
	sizer.maxSize = spec.maxSize;
	sizer.stretch = spec.stretch;
	sizer.maxSize = Math.max(sizer.minSize, sizer.maxSize);
	return sizer;
}
},{"./index.css":23,"phosphor-boxengine":25,"phosphor-messaging":40,"phosphor-properties":26,"phosphor-widget":72}],25:[function(require,module,exports){
arguments[4][3][0].apply(exports,arguments)
},{"dup":3}],26:[function(require,module,exports){
arguments[4][8][0].apply(exports,arguments)
},{"dup":8,"phosphor-signaling":27}],27:[function(require,module,exports){
arguments[4][9][0].apply(exports,arguments)
},{"dup":9}],28:[function(require,module,exports){
var css = ".p-Menu{position:absolute;top:0;left:0;margin:0;padding:3px 0;white-space:nowrap;overflow-x:hidden;overflow-y:auto;z-index:100000}.p-Menu-content{display:table;width:100%;margin:0;padding:0;border-spacing:0}.p-Menu-item{display:table-row}.p-Menu-item.p-mod-force-hidden,.p-Menu-item.p-mod-hidden{display:none}.p-Menu-item>span{display:table-cell;padding-top:4px;padding-bottom:4px}.p-Menu-item-icon{width:21px;padding-left:2px;padding-right:2px;text-align:center}.p-Menu-item-text{padding-left:2px;padding-right:35px}.p-Menu-item-shortcut{text-align:right}.p-Menu-item-submenu-icon{width:16px;text-align:center}.p-Menu-item.p-mod-separator-type>span{padding:0;height:9px;line-height:0;text-indent:100%;overflow:hidden;whitespace:nowrap;vertical-align:top}.p-Menu-item.p-mod-separator-type>span::after{content:'';display:block;position:relative;top:4px}.p-MenuBar-content{display:flex;flex-direction:row}.p-MenuBar-item{box-sizing:border-box}.p-MenuBar-item.p-mod-force-hidden,.p-MenuBar-item.p-mod-hidden{display:none}"; (require("browserify-css").createStyle(css, { "href": "node_modules/phosphor-menus/lib/index.css"})); module.exports = css;
},{"browserify-css":2}],29:[function(require,module,exports){

'use strict';
function __export(m) {
	for (var p in m) if (!exports.hasOwnProperty(p)) exports[p] = m[p];
}
__export(require('./menu'));
__export(require('./menubar'));
__export(require('./menubase'));
__export(require('./menuitem'));
require('./index.css');
},{"./index.css":28,"./menu":30,"./menubar":31,"./menubase":32,"./menuitem":33}],30:[function(require,module,exports){

'use strict';
var __extends = (this && this.__extends) || function (d, b) {
	for (var p in b) if (b.hasOwnProperty(p)) d[p] = b[p];
	function __() { this.constructor = d; }
	d.prototype = b === null ? Object.create(b) : (__.prototype = b.prototype, new __());
};
var phosphor_domutil_1 = require('phosphor-domutil');
var phosphor_signaling_1 = require('phosphor-signaling');
var phosphor_widget_1 = require('phosphor-widget');
var menubase_1 = require('./menubase');
var menuitem_1 = require('./menuitem');

exports.MENU_CLASS = 'p-Menu';

exports.CONTENT_CLASS = 'p-Menu-content';

exports.MENU_ITEM_CLASS = 'p-Menu-item';

exports.ICON_CLASS = 'p-Menu-item-icon';

exports.TEXT_CLASS = 'p-Menu-item-text';

exports.SHORTCUT_CLASS = 'p-Menu-item-shortcut';

exports.SUBMENU_ICON_CLASS = 'p-Menu-item-submenu-icon';

exports.CHECK_TYPE_CLASS = 'p-mod-check-type';

exports.SEPARATOR_TYPE_CLASS = 'p-mod-separator-type';

exports.ACTIVE_CLASS = 'p-mod-active';

exports.DISABLED_CLASS = 'p-mod-disabled';

exports.HIDDEN_CLASS = 'p-mod-hidden';

exports.FORCE_HIDDEN_CLASS = 'p-mod-force-hidden';

exports.CHECKED_CLASS = 'p-mod-checked';

exports.HAS_SUBMENU_CLASS = 'p-mod-has-submenu';

var OPEN_DELAY = 300;

var CLOSE_DELAY = 300;

var SUBMENU_OVERLAP = 3;

var Menu = (function (_super) {
	__extends(Menu, _super);

	function Menu() {
		_super.call(this);
		this._openTimerId = 0;
		this._closeTimerId = 0;
		this._parentMenu = null;
		this._childMenu = null;
		this._childItem = null;
		this.addClass(exports.MENU_CLASS);
	}

	Menu.createNode = function () {
		var node = document.createElement('div');
		var content = document.createElement('div');
		content.className = exports.CONTENT_CLASS;
		node.appendChild(content);
		return node;
	};

	Menu.fromTemplate = function (array) {
		var menu = new Menu();
		menu.items = array.map(createMenuItem);
		return menu;
	};

	Menu.prototype.dispose = function () {
		this.close(true);
		_super.prototype.dispose.call(this);
	};
	Object.defineProperty(Menu.prototype, "closed", {

		get: function () {
			return Menu.closedSignal.bind(this);
		},
		enumerable: true,
		configurable: true
	});
	Object.defineProperty(Menu.prototype, "parentMenu", {

		get: function () {
			return this._parentMenu;
		},
		enumerable: true,
		configurable: true
	});
	Object.defineProperty(Menu.prototype, "childMenu", {

		get: function () {
			return this._childMenu;
		},
		enumerable: true,
		configurable: true
	});
	Object.defineProperty(Menu.prototype, "rootMenu", {

		get: function () {
			var menu = this;
			while (menu._parentMenu) {
				menu = menu._parentMenu;
			}
			return menu;
		},
		enumerable: true,
		configurable: true
	});
	Object.defineProperty(Menu.prototype, "leafMenu", {

		get: function () {
			var menu = this;
			while (menu._childMenu) {
				menu = menu._childMenu;
			}
			return menu;
		},
		enumerable: true,
		configurable: true
	});

	Menu.prototype.popup = function (x, y, forceX, forceY) {
		if (forceX === void 0) { forceX = false; }
		if (forceY === void 0) { forceY = false; }
		if (!this.isAttached) {
			this.update(true);
			document.addEventListener('keydown', this, true);
			document.addEventListener('keypress', this, true);
			document.addEventListener('mousedown', this, true);
			openRootMenu(this, x, y, forceX, forceY);
		}
	};

	Menu.prototype.open = function (x, y, forceX, forceY) {
		if (forceX === void 0) { forceX = false; }
		if (forceY === void 0) { forceY = false; }
		if (!this.isAttached) {
			this.update(true);
			openRootMenu(this, x, y, forceX, forceY);
		}
	};

	Menu.prototype.handleEvent = function (event) {
		switch (event.type) {
			case 'mouseenter':
				this._evtMouseEnter(event);
				break;
			case 'mouseleave':
				this._evtMouseLeave(event);
				break;
			case 'mousedown':
				this._evtMouseDown(event);
				break;
			case 'mouseup':
				this._evtMouseUp(event);
				break;
			case 'contextmenu':
				this._evtContextMenu(event);
				break;
			case 'keydown':
				this._evtKeyDown(event);
				break;
			case 'keypress':
				this._evtKeyPress(event);
				break;
		}
	};

	Menu.prototype.onItemsChanged = function (old, items) {
		this.close(true);
	};

	Menu.prototype.onActiveIndexChanged = function (old, index) {
		var oldNode = this._itemNodeAt(old);
		var newNode = this._itemNodeAt(index);
		if (oldNode)
			oldNode.classList.remove(exports.ACTIVE_CLASS);
		if (newNode)
			newNode.classList.add(exports.ACTIVE_CLASS);
	};

	Menu.prototype.onOpenItem = function (index, item) {
		var node = this._itemNodeAt(index) || this.node;
		this._openChildMenu(item, node, false);
		this._childMenu.activateNextItem();
	};

	Menu.prototype.onTriggerItem = function (index, item) {
		this.rootMenu.close();
		var handler = item.handler;
		if (handler)
			handler(item);
	};

	Menu.prototype.onAfterAttach = function (msg) {
		this.node.addEventListener('mouseup', this);
		this.node.addEventListener('mouseleave', this);
		this.node.addEventListener('contextmenu', this);
	};

	Menu.prototype.onBeforeDetach = function (msg) {
		this.node.removeEventListener('mouseup', this);
		this.node.removeEventListener('mouseleave', this);
		this.node.removeEventListener('contextmenu', this);
		document.removeEventListener('keydown', this, true);
		document.removeEventListener('keypress', this, true);
		document.removeEventListener('mousedown', this, true);
	};

	Menu.prototype.onUpdateRequest = function (msg) {
		var items = this.items;
		var count = items.length;
		var nodes = new Array(count);
		for (var i = 0; i < count; ++i) {
			var node = createItemNode(items[i]);
			node.addEventListener('mouseenter', this);
			nodes[i] = node;
		}
		for (var k1 = 0; k1 < count; ++k1) {
			if (items[k1].hidden) {
				continue;
			}
			if (!items[k1].isSeparatorType) {
				break;
			}
			nodes[k1].classList.add(exports.FORCE_HIDDEN_CLASS);
		}
		for (var k2 = count - 1; k2 >= 0; --k2) {
			if (items[k2].hidden) {
				continue;
			}
			if (!items[k2].isSeparatorType) {
				break;
			}
			nodes[k2].classList.add(exports.FORCE_HIDDEN_CLASS);
		}
		var hide = false;
		while (++k1 < k2) {
			if (items[k1].hidden) {
				continue;
			}
			if (hide && items[k1].isSeparatorType) {
				nodes[k1].classList.add(exports.FORCE_HIDDEN_CLASS);
			}
			else {
				hide = items[k1].isSeparatorType;
			}
		}
		var content = this.node.firstChild;
		content.textContent = '';
		for (var i = 0; i < count; ++i) {
			content.appendChild(nodes[i]);
		}
	};

	Menu.prototype.onCloseRequest = function (msg) {
		this._cancelPendingOpen();
		this._cancelPendingClose();
		this.activeIndex = -1;
		var childMenu = this._childMenu;
		if (childMenu) {
			this._childMenu = null;
			this._childItem = null;
			childMenu.close(true);
		}
		var parentMenu = this._parentMenu;
		if (parentMenu) {
			this._parentMenu = null;
			parentMenu._cancelPendingOpen();
			parentMenu._cancelPendingClose();
			parentMenu._childMenu = null;
			parentMenu._childItem = null;
		}
		if (this.parent) {
			this.parent = null;
			this.closed.emit(void 0);
		}
		else if (this.isAttached) {
			phosphor_widget_1.detachWidget(this);
			this.closed.emit(void 0);
		}
		this.node.firstChild.textContent = '';
	};

	Menu.prototype._evtMouseEnter = function (event) {
		this._syncAncestors();
		this._closeChildMenu();
		this._cancelPendingOpen();
		var node = event.currentTarget;
		this.activeIndex = this._itemNodeIndex(node);
		var item = this.items[this.activeIndex];
		if (item && item.submenu) {
			if (item === this._childItem) {
				this._cancelPendingClose();
			}
			else {
				this._openChildMenu(item, node, true);
			}
		}
	};

	Menu.prototype._evtMouseLeave = function (event) {
		this._cancelPendingOpen();
		var child = this._childMenu;
		if (!child || !phosphor_domutil_1.hitTest(child.node, event.clientX, event.clientY)) {
			this.activeIndex = -1;
			this._closeChildMenu();
		}
	};

	Menu.prototype._evtMouseUp = function (event) {
		event.preventDefault();
		event.stopPropagation();
		if (event.button !== 0) {
			return;
		}
		var node = this._itemNodeAt(this.activeIndex);
		if (node && node.contains(event.target)) {
			this.triggerActiveItem();
		}
	};

	Menu.prototype._evtContextMenu = function (event) {
		event.preventDefault();
		event.stopPropagation();
	};

	Menu.prototype._evtMouseDown = function (event) {
		var menu = this;
		var hit = false;
		var x = event.clientX;
		var y = event.clientY;
		while (!hit && menu) {
			hit = phosphor_domutil_1.hitTest(menu.node, x, y);
			menu = menu._childMenu;
		}
		if (!hit)
			this.close(true);
	};

	Menu.prototype._evtKeyDown = function (event) {
		event.stopPropagation();
		var leaf = this.leafMenu;
		switch (event.keyCode) {
			case 13:
				event.preventDefault();
				leaf.triggerActiveItem();
				break;
			case 27:
				event.preventDefault();
				leaf.close(true);
				break;
			case 37:
				event.preventDefault();
				if (leaf !== this)
					leaf.close(true);
				break;
			case 38:
				event.preventDefault();
				leaf.activatePreviousItem();
				break;
			case 39:
				event.preventDefault();
				leaf.openActiveItem();
				break;
			case 40:
				event.preventDefault();
				leaf.activateNextItem();
				break;
		}
	};

	Menu.prototype._evtKeyPress = function (event) {
		event.preventDefault();
		event.stopPropagation();
		this.leafMenu.activateMnemonicItem(String.fromCharCode(event.charCode));
	};

	Menu.prototype._syncAncestors = function () {
		var menu = this._parentMenu;
		while (menu) {
			menu._syncChildItem();
			menu = menu._parentMenu;
		}
	};

	Menu.prototype._syncChildItem = function () {
		this._cancelPendingOpen();
		this._cancelPendingClose();
		this.activeIndex = this.items.indexOf(this._childItem);
	};

	Menu.prototype._openChildMenu = function (item, node, delayed) {
		var _this = this;
		if (item === this._childItem) {
			return;
		}
		this._cancelPendingOpen();
		if (delayed) {
			this._openTimerId = setTimeout(function () {
				var menu = item.submenu;
				_this._openTimerId = 0;
				_this._childItem = item;
				_this._childMenu = menu;
				menu._parentMenu = _this;
				menu.update(true);
				openSubmenu(menu, node);
			}, OPEN_DELAY);
		}
		else {
			var menu = item.submenu;
			this._childItem = item;
			this._childMenu = menu;
			menu._parentMenu = this;
			menu.update(true);
			openSubmenu(menu, node);
		}
	};

	Menu.prototype._closeChildMenu = function () {
		var _this = this;
		if (this._closeTimerId || !this._childMenu) {
			return;
		}
		this._closeTimerId = setTimeout(function () {
			_this._closeTimerId = 0;
			if (_this._childMenu) {
				_this._childMenu.close(true);
				_this._childMenu = null;
				_this._childItem = null;
			}
		}, CLOSE_DELAY);
	};

	Menu.prototype._cancelPendingOpen = function () {
		if (this._openTimerId) {
			clearTimeout(this._openTimerId);
			this._openTimerId = 0;
		}
	};

	Menu.prototype._cancelPendingClose = function () {
		if (this._closeTimerId) {
			clearTimeout(this._closeTimerId);
			this._closeTimerId = 0;
		}
	};

	Menu.prototype._itemNodeAt = function (index) {
		var content = this.node.firstChild;
		return content.children[index];
	};

	Menu.prototype._itemNodeIndex = function (node) {
		var content = this.node.firstChild;
		return Array.prototype.indexOf.call(content.children, node);
	};

	Menu.closedSignal = new phosphor_signaling_1.Signal();
	return Menu;
})(menubase_1.MenuBase);
exports.Menu = Menu;

function createMenuItem(template) {
	return menuitem_1.MenuItem.fromTemplate(template);
}

function createItemClassName(item) {
	var parts = [exports.MENU_ITEM_CLASS];
	if (item.isCheckType) {
		parts.push(exports.CHECK_TYPE_CLASS);
	}
	else if (item.isSeparatorType) {
		parts.push(exports.SEPARATOR_TYPE_CLASS);
	}
	if (item.checked) {
		parts.push(exports.CHECKED_CLASS);
	}
	if (item.disabled) {
		parts.push(exports.DISABLED_CLASS);
	}
	if (item.hidden) {
		parts.push(exports.HIDDEN_CLASS);
	}
	if (item.submenu) {
		parts.push(exports.HAS_SUBMENU_CLASS);
	}
	if (item.className) {
		parts.push(item.className);
	}
	return parts.join(' ');
}

function createItemNode(item) {
	var node = document.createElement('div');
	var icon = document.createElement('span');
	var text = document.createElement('span');
	var shortcut = document.createElement('span');
	var submenu = document.createElement('span');
	node.className = createItemClassName(item);
	icon.className = exports.ICON_CLASS;
	text.className = exports.TEXT_CLASS;
	shortcut.className = exports.SHORTCUT_CLASS;
	submenu.className = exports.SUBMENU_ICON_CLASS;
	if (!item.isSeparatorType) {
		text.textContent = item.text.replace(/&/g, '');
		shortcut.textContent = item.shortcut;
	}
	node.appendChild(icon);
	node.appendChild(text);
	node.appendChild(shortcut);
	node.appendChild(submenu);
	return node;
}

function clientViewportRect() {
	var elem = document.documentElement;
	var x = window.pageXOffset;
	var y = window.pageYOffset;
	var width = elem.clientWidth;
	var height = elem.clientHeight;
	return { x: x, y: y, width: width, height: height };
}

function mountAndMeasure(menu, maxHeight) {
	var node = menu.node;
	var style = node.style;
	style.top = '';
	style.left = '';
	style.width = '';
	style.height = '';
	style.visibility = 'hidden';
	style.maxHeight = maxHeight + 'px';
	phosphor_widget_1.attachWidget(menu, document.body);
	if (node.scrollHeight > maxHeight) {
		style.width = 2 * node.offsetWidth - node.clientWidth + 'px';
	}
	var rect = node.getBoundingClientRect();
	return { width: rect.width, height: rect.height };
}

function showMenu(menu, x, y) {
	var style = menu.node.style;
	style.top = Math.max(0, y) + 'px';
	style.left = Math.max(0, x) + 'px';
	style.visibility = '';
}

function openRootMenu(menu, x, y, forceX, forceY) {
	var rect = clientViewportRect();
	var size = mountAndMeasure(menu, rect.height - (forceY ? y : 0));
	if (!forceX && (x + size.width > rect.x + rect.width)) {
		x = rect.x + rect.width - size.width;
	}
	if (!forceY && (y + size.height > rect.y + rect.height)) {
		if (y > rect.y + rect.height) {
			y = rect.y + rect.height - size.height;
		}
		else {
			y = y - size.height;
		}
	}
	showMenu(menu, x, y);
}

function openSubmenu(menu, item) {
	var rect = clientViewportRect();
	var size = mountAndMeasure(menu, rect.height);
	var box = phosphor_domutil_1.boxSizing(menu.node);
	var itemRect = item.getBoundingClientRect();
	var x = itemRect.right - SUBMENU_OVERLAP;
	var y = itemRect.top - box.borderTop - box.paddingTop;
	if (x + size.width > rect.x + rect.width) {
		x = itemRect.left + SUBMENU_OVERLAP - size.width;
	}
	if (y + size.height > rect.y + rect.height) {
		y = itemRect.bottom + box.borderBottom + box.paddingBottom - size.height;
	}
	showMenu(menu, x, y);
}
},{"./menubase":32,"./menuitem":33,"phosphor-domutil":36,"phosphor-signaling":39,"phosphor-widget":72}],31:[function(require,module,exports){

'use strict';
var __extends = (this && this.__extends) || function (d, b) {
	for (var p in b) if (b.hasOwnProperty(p)) d[p] = b[p];
	function __() { this.constructor = d; }
	d.prototype = b === null ? Object.create(b) : (__.prototype = b.prototype, new __());
};
var phosphor_domutil_1 = require('phosphor-domutil');
var phosphor_properties_1 = require('phosphor-properties');
var menubase_1 = require('./menubase');
var menuitem_1 = require('./menuitem');

exports.MENU_BAR_CLASS = 'p-MenuBar';

exports.CONTENT_CLASS = 'p-MenuBar-content';

exports.MENU_CLASS = 'p-MenuBar-menu';

exports.MENU_ITEM_CLASS = 'p-MenuBar-item';

exports.ICON_CLASS = 'p-MenuBar-item-icon';

exports.TEXT_CLASS = 'p-MenuBar-item-text';

exports.SEPARATOR_TYPE_CLASS = 'p-mod-separator-type';

exports.ACTIVE_CLASS = 'p-mod-active';

exports.DISABLED_CLASS = 'p-mod-disabled';

exports.HIDDEN_CLASS = 'p-mod-hidden';

exports.FORCE_HIDDEN_CLASS = 'p-mod-force-hidden';

var MenuBar = (function (_super) {
	__extends(MenuBar, _super);

	function MenuBar() {
		_super.call(this);
		this._active = false;
		this._childMenu = null;
		this.addClass(exports.MENU_BAR_CLASS);
	}

	MenuBar.createNode = function () {
		var node = document.createElement('div');
		var content = document.createElement('div');
		content.className = exports.CONTENT_CLASS;
		node.appendChild(content);
		return node;
	};

	MenuBar.fromTemplate = function (array) {
		var bar = new MenuBar();
		bar.items = array.map(createMenuItem);
		return bar;
	};

	MenuBar.prototype.dispose = function () {
		this._reset();
		_super.prototype.dispose.call(this);
	};
	Object.defineProperty(MenuBar.prototype, "childMenu", {

		get: function () {
			return this._childMenu;
		},
		enumerable: true,
		configurable: true
	});

	MenuBar.prototype.handleEvent = function (event) {
		switch (event.type) {
			case 'mousedown':
				this._evtMouseDown(event);
				break;
			case 'mousemove':
				this._evtMouseMove(event);
				break;
			case 'mouseleave':
				this._evtMouseLeave(event);
				break;
			case 'contextmenu':
				this._evtContextMenu(event);
				break;
			case 'keydown':
				this._evtKeyDown(event);
				break;
			case 'keypress':
				this._evtKeyPress(event);
				break;
		}
	};

	MenuBar.prototype.onItemsChanged = function (old, items) {
		for (var i = 0, n = old.length; i < n; ++i) {
			phosphor_properties_1.Property.getChanged(old[i]).disconnect(this._onItemChanged, this);
		}
		for (var i = 0, n = items.length; i < n; ++i) {
			phosphor_properties_1.Property.getChanged(items[i]).connect(this._onItemChanged, this);
		}
		this.update(true);
	};

	MenuBar.prototype.onActiveIndexChanged = function (old, index) {
		var oldNode = this._itemNodeAt(old);
		var newNode = this._itemNodeAt(index);
		if (oldNode)
			oldNode.classList.remove(exports.ACTIVE_CLASS);
		if (newNode)
			newNode.classList.add(exports.ACTIVE_CLASS);
	};

	MenuBar.prototype.onOpenItem = function (index, item) {
		var node = this._itemNodeAt(index) || this.node;
		this._activate();
		this._closeChildMenu();
		this._openChildMenu(item.submenu, node);
	};

	MenuBar.prototype.onAfterAttach = function (msg) {
		this.node.addEventListener('mousedown', this);
		this.node.addEventListener('mousemove', this);
		this.node.addEventListener('mouseleave', this);
		this.node.addEventListener('contextmenu', this);
	};

	MenuBar.prototype.onBeforeDetach = function (msg) {
		this.node.removeEventListener('mousedown', this);
		this.node.removeEventListener('mousemove', this);
		this.node.removeEventListener('mouseleave', this);
		this.node.removeEventListener('contextmenu', this);
	};

	MenuBar.prototype.onUpdateRequest = function (msg) {
		this._reset();
		var items = this.items;
		var count = items.length;
		var nodes = new Array(count);
		for (var i = 0; i < count; ++i) {
			nodes[i] = createItemNode(items[i]);
		}
		for (var k1 = 0; k1 < count; ++k1) {
			if (items[k1].hidden) {
				continue;
			}
			if (!items[k1].isSeparatorType) {
				break;
			}
			nodes[k1].classList.add(exports.FORCE_HIDDEN_CLASS);
		}
		for (var k2 = count - 1; k2 >= 0; --k2) {
			if (items[k2].hidden) {
				continue;
			}
			if (!items[k2].isSeparatorType) {
				break;
			}
			nodes[k2].classList.add(exports.FORCE_HIDDEN_CLASS);
		}
		var hide = false;
		while (++k1 < k2) {
			if (items[k1].hidden) {
				continue;
			}
			if (hide && items[k1].isSeparatorType) {
				nodes[k1].classList.add(exports.FORCE_HIDDEN_CLASS);
			}
			else {
				hide = items[k1].isSeparatorType;
			}
		}
		var content = this.node.firstChild;
		content.textContent = '';
		for (var i = 0; i < count; ++i) {
			content.appendChild(nodes[i]);
		}
	};

	MenuBar.prototype.onCloseRequest = function (msg) {
		this._reset();
		_super.prototype.onCloseRequest.call(this, msg);
	};

	MenuBar.prototype._evtMouseDown = function (event) {
		var x = event.clientX;
		var y = event.clientY;
		if (this._active && hitTestMenus(this._childMenu, x, y)) {
			return;
		}
		var i = this._hitTestItemNodes(x, y);
		if (this._active) {
			this._deactivate();
			this._closeChildMenu();
			this.activeIndex = i;
			return;
		}
		if (i === -1) {
			this.activeIndex = -1;
			return;
		}
		this._activate();
		this.activeIndex = i;
		this.openActiveItem();
	};

	MenuBar.prototype._evtMouseMove = function (event) {
		var x = event.clientX;
		var y = event.clientY;
		var i = this._hitTestItemNodes(x, y);
		if (i === this.activeIndex) {
			return;
		}
		if (i === -1 && this._active) {
			return;
		}
		this.activeIndex = i;
		if (!this._active) {
			return;
		}
		this._closeChildMenu();
		this.openActiveItem();
	};

	MenuBar.prototype._evtMouseLeave = function (event) {
		if (!this._active)
			this.activeIndex = -1;
	};

	MenuBar.prototype._evtContextMenu = function (event) {
		event.preventDefault();
		event.stopPropagation();
	};

	MenuBar.prototype._evtKeyDown = function (event) {
		event.stopPropagation();
		var menu = this._childMenu;
		var leaf = menu && menu.leafMenu;
		switch (event.keyCode) {
			case 13:
				event.preventDefault();
				if (leaf)
					leaf.triggerActiveItem();
				break;
			case 27:
				event.preventDefault();
				if (leaf)
					leaf.close(true);
				break;
			case 37:
				event.preventDefault();
				if (leaf && leaf !== menu) {
					leaf.close(true);
				}
				else {
					this._closeChildMenu();
					this.activatePreviousItem();
					this.openActiveItem();
				}
				break;
			case 38:
				event.preventDefault();
				if (leaf)
					leaf.activatePreviousItem();
				break;
			case 39:
				event.preventDefault();
				if (leaf && activeHasMenu(leaf)) {
					leaf.openActiveItem();
				}
				else {
					this._closeChildMenu();
					this.activateNextItem();
					this.openActiveItem();
				}
				break;
			case 40:
				event.preventDefault();
				if (leaf)
					leaf.activateNextItem();
				break;
		}
	};

	MenuBar.prototype._evtKeyPress = function (event) {
		event.preventDefault();
		event.stopPropagation();
		var str = String.fromCharCode(event.charCode);
		(this._childMenu || this).activateMnemonicItem(str);
	};

	MenuBar.prototype._openChildMenu = function (menu, node) {
		var rect = node.getBoundingClientRect();
		this._childMenu = menu;
		menu.addClass(exports.MENU_CLASS);
		menu.open(rect.left, rect.bottom, false, true);
		menu.closed.connect(this._onMenuClosed, this);
	};

	MenuBar.prototype._closeChildMenu = function () {
		var menu = this._childMenu;
		if (menu) {
			this._childMenu = null;
			menu.closed.disconnect(this._onMenuClosed, this);
			menu.removeClass(exports.MENU_CLASS);
			menu.close(true);
		}
	};

	MenuBar.prototype._activate = function () {
		var _this = this;
		if (this._active) {
			return;
		}
		this._active = true;
		this.addClass(exports.ACTIVE_CLASS);
		setTimeout(function () {
			_this.node.removeEventListener('mousedown', _this);
			document.addEventListener('mousedown', _this, true);
			document.addEventListener('keydown', _this, true);
			document.addEventListener('keypress', _this, true);
		}, 0);
	};

	MenuBar.prototype._deactivate = function () {
		var _this = this;
		if (!this._active) {
			return;
		}
		this._active = false;
		this.removeClass(exports.ACTIVE_CLASS);
		setTimeout(function () {
			_this.node.addEventListener('mousedown', _this);
			document.removeEventListener('mousedown', _this, true);
			document.removeEventListener('keydown', _this, true);
			document.removeEventListener('keypress', _this, true);
		}, 0);
	};

	MenuBar.prototype._reset = function () {
		this._deactivate();
		this._closeChildMenu();
		this.activeIndex = -1;
	};

	MenuBar.prototype._itemNodeAt = function (index) {
		var content = this.node.firstChild;
		return content.children[index];
	};

	MenuBar.prototype._hitTestItemNodes = function (x, y) {
		var nodes = this.node.firstChild.children;
		for (var i = 0, n = nodes.length; i < n; ++i) {
			if (phosphor_domutil_1.hitTest(nodes[i], x, y))
				return i;
		}
		return -1;
	};

	MenuBar.prototype._onMenuClosed = function (sender) {
		sender.closed.disconnect(this._onMenuClosed, this);
		sender.removeClass(exports.MENU_CLASS);
		this._childMenu = null;
		this._reset();
	};

	MenuBar.prototype._onItemChanged = function (sender) {
		this.update();
	};
	return MenuBar;
})(menubase_1.MenuBase);
exports.MenuBar = MenuBar;

function createMenuItem(template) {
	return menuitem_1.MenuItem.fromTemplate(template);
}

function createItemClassName(item) {
	var parts = [exports.MENU_ITEM_CLASS];
	if (item.isSeparatorType) {
		parts.push(exports.SEPARATOR_TYPE_CLASS);
	}
	if (item.disabled) {
		parts.push(exports.DISABLED_CLASS);
	}
	if (item.hidden) {
		parts.push(exports.HIDDEN_CLASS);
	}
	if (item.className) {
		parts.push(item.className);
	}
	return parts.join(' ');
}

function createItemNode(item) {
	var node = document.createElement('div');
	var icon = document.createElement('span');
	var text = document.createElement('span');
	node.className = createItemClassName(item);
	icon.className = exports.ICON_CLASS;
	text.className = exports.TEXT_CLASS;
	if (!item.isSeparatorType) {
		text.textContent = item.text.replace(/&/g, '');
	}
	node.appendChild(icon);
	node.appendChild(text);
	return node;
}

function activeHasMenu(menu) {
	var item = menu.items[menu.activeIndex];
	return !!(item && item.submenu);
}

function hitTestMenus(menu, x, y) {
	while (menu) {
		if (phosphor_domutil_1.hitTest(menu.node, x, y)) {
			return true;
		}
		menu = menu.childMenu;
	}
	return false;
}
},{"./menubase":32,"./menuitem":33,"phosphor-domutil":36,"phosphor-properties":38}],32:[function(require,module,exports){

'use strict';
var __extends = (this && this.__extends) || function (d, b) {
	for (var p in b) if (b.hasOwnProperty(p)) d[p] = b[p];
	function __() { this.constructor = d; }
	d.prototype = b === null ? Object.create(b) : (__.prototype = b.prototype, new __());
};
var arrays = require('phosphor-arrays');
var phosphor_properties_1 = require('phosphor-properties');
var phosphor_widget_1 = require('phosphor-widget');

var MenuBase = (function (_super) {
	__extends(MenuBase, _super);
	function MenuBase() {
		_super.apply(this, arguments);
	}
	Object.defineProperty(MenuBase.prototype, "items", {

		get: function () {
			return MenuBase.itemsProperty.get(this);
		},

		set: function (value) {
			MenuBase.itemsProperty.set(this, value);
		},
		enumerable: true,
		configurable: true
	});
	Object.defineProperty(MenuBase.prototype, "activeIndex", {

		get: function () {
			return MenuBase.activeIndexProperty.get(this);
		},

		set: function (value) {
			MenuBase.activeIndexProperty.set(this, value);
		},
		enumerable: true,
		configurable: true
	});

	MenuBase.prototype.activateNextItem = function () {
		var k = this.activeIndex + 1;
		var i = k >= this.items.length ? 0 : k;
		this.activeIndex = arrays.findIndex(this.items, isSelectable, i, true);
	};

	MenuBase.prototype.activatePreviousItem = function () {
		var k = this.activeIndex;
		var i = k <= 0 ? this.items.length - 1 : k - 1;
		this.activeIndex = arrays.rfindIndex(this.items, isSelectable, i, true);
	};

	MenuBase.prototype.activateMnemonicItem = function (char) {
		var c = char.toUpperCase();
		var k = this.activeIndex + 1;
		var i = k >= this.items.length ? 0 : k;
		this.activeIndex = arrays.findIndex(this.items, function (item) {
			if (!isSelectable(item)) {
				return false;
			}
			var match = item.text.match(/&\w/);
			if (!match) {
				return false;
			}
			return match[0][1].toUpperCase() === c;
		}, i, true);
	};

	MenuBase.prototype.openActiveItem = function () {
		var i = this.activeIndex;
		var item = this.items[i];
		if (item && item.submenu) {
			this.onOpenItem(i, item);
		}
	};

	MenuBase.prototype.triggerActiveItem = function () {
		var i = this.activeIndex;
		var item = this.items[i];
		if (item && item.submenu) {
			this.onOpenItem(i, item);
		}
		else if (item) {
			this.onTriggerItem(i, item);
		}
	};

	MenuBase.prototype.coerceActiveIndex = function (index) {
		var i = index | 0;
		var item = this.items[i];
		return (item && isSelectable(item)) ? i : -1;
	};

	MenuBase.prototype.onItemsChanged = function (old, items) { };

	MenuBase.prototype.onActiveIndexChanged = function (old, index) { };

	MenuBase.prototype.onOpenItem = function (index, item) { };

	MenuBase.prototype.onTriggerItem = function (index, item) { };

	MenuBase.itemsProperty = new phosphor_properties_1.Property({
		value: Object.freeze([]),
		coerce: function (owner, value) { return Object.freeze(value ? value.slice() : []); },
		changed: function (owner, old, value) { return owner.onItemsChanged(old, value); },
	});

	MenuBase.activeIndexProperty = new phosphor_properties_1.Property({
		value: -1,
		coerce: function (owner, index) { return owner.coerceActiveIndex(index); },
		changed: function (owner, old, index) { return owner.onActiveIndexChanged(old, index); },
	});
	return MenuBase;
})(phosphor_widget_1.Widget);
exports.MenuBase = MenuBase;

function isSelectable(item) {
	return !item.hidden && !item.disabled && !item.isSeparatorType;
}
},{"phosphor-arrays":34,"phosphor-properties":38,"phosphor-widget":72}],33:[function(require,module,exports){

'use strict';
var phosphor_properties_1 = require('phosphor-properties');
var menu_1 = require('./menu');

var MenuItem = (function () {

	function MenuItem(options) {
		if (options)
			initFromOptions(this, options);
	}

	MenuItem.fromTemplate = function (template) {
		var item = new MenuItem();
		initFromTemplate(item, template);
		return item;
	};
	Object.defineProperty(MenuItem.prototype, "type", {

		get: function () {
			return MenuItem.typeProperty.get(this);
		},

		set: function (value) {
			MenuItem.typeProperty.set(this, value);
		},
		enumerable: true,
		configurable: true
	});
	Object.defineProperty(MenuItem.prototype, "text", {

		get: function () {
			return MenuItem.textProperty.get(this);
		},

		set: function (value) {
			MenuItem.textProperty.set(this, value);
		},
		enumerable: true,
		configurable: true
	});
	Object.defineProperty(MenuItem.prototype, "shortcut", {

		get: function () {
			return MenuItem.shortcutProperty.get(this);
		},

		set: function (value) {
			MenuItem.shortcutProperty.set(this, value);
		},
		enumerable: true,
		configurable: true
	});
	Object.defineProperty(MenuItem.prototype, "disabled", {

		get: function () {
			return MenuItem.disabledProperty.get(this);
		},

		set: function (value) {
			MenuItem.disabledProperty.set(this, value);
		},
		enumerable: true,
		configurable: true
	});
	Object.defineProperty(MenuItem.prototype, "hidden", {

		get: function () {
			return MenuItem.hiddenProperty.get(this);
		},

		set: function (value) {
			MenuItem.hiddenProperty.set(this, value);
		},
		enumerable: true,
		configurable: true
	});
	Object.defineProperty(MenuItem.prototype, "checked", {

		get: function () {
			return MenuItem.checkedProperty.get(this);
		},

		set: function (value) {
			MenuItem.checkedProperty.set(this, value);
		},
		enumerable: true,
		configurable: true
	});
	Object.defineProperty(MenuItem.prototype, "className", {

		get: function () {
			return MenuItem.classNameProperty.get(this);
		},

		set: function (value) {
			MenuItem.classNameProperty.set(this, value);
		},
		enumerable: true,
		configurable: true
	});
	Object.defineProperty(MenuItem.prototype, "handler", {

		get: function () {
			return MenuItem.handlerProperty.get(this);
		},

		set: function (value) {
			MenuItem.handlerProperty.set(this, value);
		},
		enumerable: true,
		configurable: true
	});
	Object.defineProperty(MenuItem.prototype, "submenu", {

		get: function () {
			return MenuItem.submenuProperty.get(this);
		},

		set: function (value) {
			MenuItem.submenuProperty.set(this, value);
		},
		enumerable: true,
		configurable: true
	});
	Object.defineProperty(MenuItem.prototype, "isNormalType", {

		get: function () {
			return this.type === 'normal';
		},
		enumerable: true,
		configurable: true
	});
	Object.defineProperty(MenuItem.prototype, "isCheckType", {

		get: function () {
			return this.type === 'check';
		},
		enumerable: true,
		configurable: true
	});
	Object.defineProperty(MenuItem.prototype, "isSeparatorType", {

		get: function () {
			return this.type === 'separator';
		},
		enumerable: true,
		configurable: true
	});

	MenuItem.typeProperty = new phosphor_properties_1.Property({
		value: 'normal',
		coerce: coerceMenuItemType,
		changed: function (owner) { return MenuItem.checkedProperty.coerce(owner); },
	});

	MenuItem.textProperty = new phosphor_properties_1.Property({
		value: '',
	});

	MenuItem.shortcutProperty = new phosphor_properties_1.Property({
		value: '',
	});

	MenuItem.disabledProperty = new phosphor_properties_1.Property({
		value: false,
	});

	MenuItem.hiddenProperty = new phosphor_properties_1.Property({
		value: false,
	});

	MenuItem.checkedProperty = new phosphor_properties_1.Property({
		value: false,
		coerce: function (owner, val) { return owner.type === 'check' ? val : false; },
	});

	MenuItem.classNameProperty = new phosphor_properties_1.Property({
		value: '',
	});

	MenuItem.handlerProperty = new phosphor_properties_1.Property({
		value: null,
		coerce: function (owner, value) { return value || null; },
	});

	MenuItem.submenuProperty = new phosphor_properties_1.Property({
		value: null,
		coerce: function (owner, value) { return value || null; },
	});
	return MenuItem;
})();
exports.MenuItem = MenuItem;

function initFromCommon(item, common) {
	if (common.type !== void 0) {
		item.type = common.type;
	}
	if (common.text !== void 0) {
		item.text = common.text;
	}
	if (common.shortcut !== void 0) {
		item.shortcut = common.shortcut;
	}
	if (common.disabled !== void 0) {
		item.disabled = common.disabled;
	}
	if (common.hidden !== void 0) {
		item.hidden = common.hidden;
	}
	if (common.checked !== void 0) {
		item.checked = common.checked;
	}
	if (common.className !== void 0) {
		item.className = common.className;
	}
	if (common.handler !== void 0) {
		item.handler = common.handler;
	}
}

function initFromTemplate(item, template) {
	initFromCommon(item, template);
	if (template.submenu !== void 0) {
		item.submenu = menu_1.Menu.fromTemplate(template.submenu);
	}
}

function initFromOptions(item, options) {
	initFromCommon(item, options);
	if (options.submenu !== void 0) {
		item.submenu = options.submenu;
	}
}

function coerceMenuItemType(item, value) {
	if (value === 'normal' || value === 'check' || value === 'separator') {
		return value;
	}
	console.warn('invalid menu item type:', value);
	return 'normal';
}
},{"./menu":30,"phosphor-properties":38}],34:[function(require,module,exports){
arguments[4][6][0].apply(exports,arguments)
},{"dup":6}],35:[function(require,module,exports){
var css = "body.p-mod-override-cursor *{cursor:inherit!important}"; (require("browserify-css").createStyle(css, { "href": "node_modules/phosphor-menus/node_modules/phosphor-domutil/lib/index.css"})); module.exports = css;
},{"browserify-css":2}],36:[function(require,module,exports){
arguments[4][16][0].apply(exports,arguments)
},{"./index.css":35,"dup":16,"phosphor-disposable":37}],37:[function(require,module,exports){
arguments[4][10][0].apply(exports,arguments)
},{"dup":10}],38:[function(require,module,exports){
arguments[4][8][0].apply(exports,arguments)
},{"dup":8,"phosphor-signaling":39}],39:[function(require,module,exports){
arguments[4][9][0].apply(exports,arguments)
},{"dup":9}],40:[function(require,module,exports){

'use strict';
var phosphor_queue_1 = require('phosphor-queue');

var Message = (function () {

	function Message(type) {
		this._type = type;
	}
	Object.defineProperty(Message.prototype, "type", {

		get: function () {
			return this._type;
		},
		enumerable: true,
		configurable: true
	});
	return Message;
})();
exports.Message = Message;

function sendMessage(handler, msg) {
	getDispatcher(handler).sendMessage(handler, msg);
}
exports.sendMessage = sendMessage;

function postMessage(handler, msg) {
	getDispatcher(handler).postMessage(handler, msg);
}
exports.postMessage = postMessage;

function hasPendingMessages(handler) {
	return getDispatcher(handler).hasPendingMessages();
}
exports.hasPendingMessages = hasPendingMessages;

function sendPendingMessage(handler) {
	getDispatcher(handler).sendPendingMessage(handler);
}
exports.sendPendingMessage = sendPendingMessage;

function installMessageFilter(handler, filter) {
	getDispatcher(handler).installMessageFilter(filter);
}
exports.installMessageFilter = installMessageFilter;

function removeMessageFilter(handler, filter) {
	getDispatcher(handler).removeMessageFilter(filter);
}
exports.removeMessageFilter = removeMessageFilter;

function clearMessageData(handler) {
	var dispatcher = dispatcherMap.get(handler);
	if (dispatcher)
		dispatcher.clear();
	dispatchQueue.removeAll(handler);
}
exports.clearMessageData = clearMessageData;

var dispatcherMap = new WeakMap();

var dispatchQueue = new phosphor_queue_1.Queue();

var frameId = void 0;

var raf;
if (typeof requestAnimationFrame === 'function') {
	raf = requestAnimationFrame;
}
else {
	raf = setImmediate;
}

function getDispatcher(handler) {
	var dispatcher = dispatcherMap.get(handler);
	if (dispatcher)
		return dispatcher;
	dispatcher = new MessageDispatcher();
	dispatcherMap.set(handler, dispatcher);
	return dispatcher;
}

function wakeUpMessageLoop() {
	if (frameId === void 0 && !dispatchQueue.empty) {
		frameId = raf(runMessageLoop);
	}
}

function runMessageLoop() {
	frameId = void 0;
	if (dispatchQueue.empty) {
		return;
	}
	if (dispatchQueue.back !== null) {
		dispatchQueue.push(null);
	}
	while (!dispatchQueue.empty) {
		var handler = dispatchQueue.pop();
		if (handler === null) {
			wakeUpMessageLoop();
			return;
		}
		dispatchMessage(dispatcherMap.get(handler), handler);
	}
}

function dispatchMessage(dispatcher, handler) {
	try {
		dispatcher.sendPendingMessage(handler);
	}
	catch (ex) {
		wakeUpMessageLoop();
		throw ex;
	}
}

var MessageDispatcher = (function () {
	function MessageDispatcher() {
		this._filters = null;
		this._messages = null;
	}

	MessageDispatcher.prototype.sendMessage = function (handler, msg) {
		if (!this._filterMessage(handler, msg)) {
			handler.processMessage(msg);
		}
	};

	MessageDispatcher.prototype.postMessage = function (handler, msg) {
		if (!this._compressMessage(handler, msg)) {
			this._enqueueMessage(handler, msg);
		}
	};

	MessageDispatcher.prototype.hasPendingMessages = function () {
		return !!(this._messages && !this._messages.empty);
	};

	MessageDispatcher.prototype.sendPendingMessage = function (handler) {
		if (this._messages && !this._messages.empty) {
			this.sendMessage(handler, this._messages.pop());
		}
	};

	MessageDispatcher.prototype.installMessageFilter = function (filter) {
		this._filters = { next: this._filters, filter: filter };
	};

	MessageDispatcher.prototype.removeMessageFilter = function (filter) {
		var link = this._filters;
		var prev = null;
		while (link !== null) {
			if (link.filter === filter) {
				link.filter = null;
			}
			else if (prev === null) {
				this._filters = link;
				prev = link;
			}
			else {
				prev.next = link;
				prev = link;
			}
			link = link.next;
		}
		if (!prev) {
			this._filters = null;
		}
		else {
			prev.next = null;
		}
	};

	MessageDispatcher.prototype.clear = function () {
		if (this._messages) {
			this._messages.clear();
		}
		for (var link = this._filters; link !== null; link = link.next) {
			link.filter = null;
		}
		this._filters = null;
	};

	MessageDispatcher.prototype._filterMessage = function (handler, msg) {
		for (var link = this._filters; link !== null; link = link.next) {
			if (link.filter && link.filter.filterMessage(handler, msg)) {
				return true;
			}
		}
		return false;
	};

	MessageDispatcher.prototype._compressMessage = function (handler, msg) {
		if (!handler.compressMessage) {
			return false;
		}
		if (!this._messages || this._messages.empty) {
			return false;
		}
		return handler.compressMessage(msg, this._messages);
	};

	MessageDispatcher.prototype._enqueueMessage = function (handler, msg) {
		(this._messages || (this._messages = new phosphor_queue_1.Queue())).push(msg);
		dispatchQueue.push(handler);
		wakeUpMessageLoop();
	};
	return MessageDispatcher;
})();
},{"phosphor-queue":41}],41:[function(require,module,exports){

'use strict';

var Queue = (function () {

	function Queue(items) {
		var _this = this;
		this._size = 0;
		this._front = null;
		this._back = null;
		if (items)
			items.forEach(function (item) { return _this.push(item); });
	}
	Object.defineProperty(Queue.prototype, "size", {

		get: function () {
			return this._size;
		},
		enumerable: true,
		configurable: true
	});
	Object.defineProperty(Queue.prototype, "empty", {

		get: function () {
			return this._size === 0;
		},
		enumerable: true,
		configurable: true
	});
	Object.defineProperty(Queue.prototype, "front", {

		get: function () {
			return this._front !== null ? this._front.value : void 0;
		},
		enumerable: true,
		configurable: true
	});
	Object.defineProperty(Queue.prototype, "back", {

		get: function () {
			return this._back !== null ? this._back.value : void 0;
		},
		enumerable: true,
		configurable: true
	});

	Queue.prototype.push = function (value) {
		var link = { next: null, value: value };
		if (this._back === null) {
			this._front = link;
			this._back = link;
		}
		else {
			this._back.next = link;
			this._back = link;
		}
		this._size++;
	};

	Queue.prototype.pop = function () {
		var link = this._front;
		if (link === null) {
			return void 0;
		}
		if (link.next === null) {
			this._front = null;
			this._back = null;
		}
		else {
			this._front = link.next;
		}
		this._size--;
		return link.value;
	};

	Queue.prototype.remove = function (value) {
		var link = this._front;
		var prev = null;
		while (link !== null) {
			if (link.value === value) {
				if (prev === null) {
					this._front = link.next;
				}
				else {
					prev.next = link.next;
				}
				if (link.next === null) {
					this._back = prev;
				}
				this._size--;
				return true;
			}
			prev = link;
			link = link.next;
		}
		return false;
	};

	Queue.prototype.removeAll = function (value) {
		var count = 0;
		var link = this._front;
		var prev = null;
		while (link !== null) {
			if (link.value === value) {
				count++;
				this._size--;
			}
			else if (prev === null) {
				this._front = link;
				prev = link;
			}
			else {
				prev.next = link;
				prev = link;
			}
			link = link.next;
		}
		if (!prev) {
			this._front = null;
			this._back = null;
		}
		else {
			prev.next = null;
			this._back = prev;
		}
		return count;
	};

	Queue.prototype.clear = function () {
		this._size = 0;
		this._front = null;
		this._back = null;
	};

	Queue.prototype.toArray = function () {
		var result = new Array(this._size);
		for (var i = 0, link = this._front; link !== null; link = link.next, ++i) {
			result[i] = link.value;
		}
		return result;
	};

	Queue.prototype.some = function (pred) {
		for (var i = 0, link = this._front; link !== null; link = link.next, ++i) {
			if (pred(link.value, i))
				return true;
		}
		return false;
	};

	Queue.prototype.every = function (pred) {
		for (var i = 0, link = this._front; link !== null; link = link.next, ++i) {
			if (!pred(link.value, i))
				return false;
		}
		return true;
	};

	Queue.prototype.filter = function (pred) {
		var result = [];
		for (var i = 0, link = this._front; link !== null; link = link.next, ++i) {
			if (pred(link.value, i))
				result.push(link.value);
		}
		return result;
	};

	Queue.prototype.map = function (callback) {
		var result = new Array(this._size);
		for (var i = 0, link = this._front; link !== null; link = link.next, ++i) {
			result[i] = callback(link.value, i);
		}
		return result;
	};

	Queue.prototype.forEach = function (callback) {
		for (var i = 0, link = this._front; link !== null; link = link.next, ++i) {
			var result = callback(link.value, i);
			if (result !== void 0)
				return result;
		}
		return void 0;
	};
	return Queue;
})();
exports.Queue = Queue;
},{}],42:[function(require,module,exports){

'use strict';

var NodeWrapper = (function () {
	function NodeWrapper() {
		this._node = this.constructor.createNode();
	}

	NodeWrapper.createNode = function () {
		return document.createElement('div');
	};
	Object.defineProperty(NodeWrapper.prototype, "node", {

		get: function () {
			return this._node;
		},
		enumerable: true,
		configurable: true
	});
	Object.defineProperty(NodeWrapper.prototype, "id", {

		get: function () {
			return this._node.id;
		},

		set: function (value) {
			this._node.id = value;
		},
		enumerable: true,
		configurable: true
	});

	NodeWrapper.prototype.hasClass = function (name) {
		return this._node.classList.contains(name);
	};

	NodeWrapper.prototype.addClass = function (name) {
		this._node.classList.add(name);
	};

	NodeWrapper.prototype.removeClass = function (name) {
		this._node.classList.remove(name);
	};

	NodeWrapper.prototype.toggleClass = function (name, force) {
		var present;
		if (force === true) {
			this.addClass(name);
			present = true;
		}
		else if (force === false) {
			this.removeClass(name);
			present = false;
		}
		else if (this.hasClass(name)) {
			this.removeClass(name);
			present = false;
		}
		else {
			this.addClass(name);
			present = true;
		}
		return present;
	};
	return NodeWrapper;
})();
exports.NodeWrapper = NodeWrapper;
},{}],43:[function(require,module,exports){
arguments[4][8][0].apply(exports,arguments)
},{"dup":8,"phosphor-signaling":44}],44:[function(require,module,exports){
arguments[4][9][0].apply(exports,arguments)
},{"dup":9}],45:[function(require,module,exports){
var css = ".p-SplitPanel{position:relative}.p-SplitPanel>.p-Widget{position:absolute;z-index:0}.p-SplitHandle{box-sizing:border-box;position:absolute;z-index:1}.p-SplitHandle.p-mod-hidden{display:none}.p-SplitHandle.p-mod-horizontal{cursor:ew-resize}.p-SplitHandle.p-mod-vertical{cursor:ns-resize}.p-SplitHandle-overlay{box-sizing:border-box;position:absolute;top:0;left:0;width:100%;height:100%}.p-SplitHandle.p-mod-horizontal>.p-SplitHandle-overlay{min-width:7px;left:50%;transform:translateX(-50%)}.p-SplitHandle.p-mod-vertical>.p-SplitHandle-overlay{min-height:7px;top:50%;transform:translateY(-50%)}"; (require("browserify-css").createStyle(css, { "href": "node_modules/phosphor-splitpanel/lib/index.css"})); module.exports = css;
},{"browserify-css":2}],46:[function(require,module,exports){

'use strict';
var __extends = (this && this.__extends) || function (d, b) {
	for (var p in b) if (b.hasOwnProperty(p)) d[p] = b[p];
	function __() { this.constructor = d; }
	d.prototype = b === null ? Object.create(b) : (__.prototype = b.prototype, new __());
};
var arrays = require('phosphor-arrays');
var phosphor_boxengine_1 = require('phosphor-boxengine');
var phosphor_domutil_1 = require('phosphor-domutil');
var phosphor_messaging_1 = require('phosphor-messaging');
var phosphor_nodewrapper_1 = require('phosphor-nodewrapper');
var phosphor_properties_1 = require('phosphor-properties');
var phosphor_widget_1 = require('phosphor-widget');
require('./index.css');

exports.SPLIT_PANEL_CLASS = 'p-SplitPanel';

exports.SPLIT_HANDLE_CLASS = 'p-SplitHandle';

exports.OVERLAY_CLASS = 'p-SplitHandle-overlay';

exports.HORIZONTAL_CLASS = 'p-mod-horizontal';

exports.VERTICAL_CLASS = 'p-mod-vertical';

exports.HIDDEN_CLASS = 'p-mod-hidden';

(function (Orientation) {

	Orientation[Orientation["Horizontal"] = 0] = "Horizontal";

	Orientation[Orientation["Vertical"] = 1] = "Vertical";
})(exports.Orientation || (exports.Orientation = {}));
var Orientation = exports.Orientation;

var SplitPanel = (function (_super) {
	__extends(SplitPanel, _super);

	function SplitPanel() {
		_super.call(this);
		this._fixedSpace = 0;
		this._pendingSizes = false;
		this._sizers = [];
		this._pressData = null;
		this.addClass(exports.SPLIT_PANEL_CLASS);
		this.addClass(exports.HORIZONTAL_CLASS);
	}

	SplitPanel.getStretch = function (widget) {
		return SplitPanel.stretchProperty.get(widget);
	};

	SplitPanel.setStretch = function (widget, value) {
		SplitPanel.stretchProperty.set(widget, value);
	};

	SplitPanel.prototype.dispose = function () {
		this._releaseMouse();
		this._sizers.length = 0;
		_super.prototype.dispose.call(this);
	};
	Object.defineProperty(SplitPanel.prototype, "orientation", {

		get: function () {
			return SplitPanel.orientationProperty.get(this);
		},

		set: function (value) {
			SplitPanel.orientationProperty.set(this, value);
		},
		enumerable: true,
		configurable: true
	});
	Object.defineProperty(SplitPanel.prototype, "handleSize", {

		get: function () {
			return SplitPanel.handleSizeProperty.get(this);
		},

		set: function (size) {
			SplitPanel.handleSizeProperty.set(this, size);
		},
		enumerable: true,
		configurable: true
	});

	SplitPanel.prototype.sizes = function () {
		return normalize(this._sizers.map(function (sizer) { return sizer.size; }));
	};

	SplitPanel.prototype.setSizes = function (sizes) {
		var normed = normalize(sizes);
		for (var i = 0, n = this._sizers.length; i < n; ++i) {
			var hint = Math.max(0, normed[i] || 0);
			var sizer = this._sizers[i];
			sizer.sizeHint = hint;
			sizer.size = hint;
		}
		this._pendingSizes = true;
		this.update();
	};

	SplitPanel.prototype.handleEvent = function (event) {
		switch (event.type) {
			case 'mousedown':
				this._evtMouseDown(event);
				break;
			case 'mouseup':
				this._evtMouseUp(event);
				break;
			case 'mousemove':
				this._evtMouseMove(event);
				break;
		}
	};

	SplitPanel.prototype.onChildAdded = function (msg) {
		var sizer = createSizer(averageSize(this._sizers));
		arrays.insert(this._sizers, msg.currentIndex, sizer);
		this.node.appendChild(msg.child.node);
		this.node.appendChild(getHandle(msg.child).node);
		if (this.isAttached)
			phosphor_messaging_1.sendMessage(msg.child, phosphor_widget_1.MSG_AFTER_ATTACH);
		phosphor_messaging_1.postMessage(this, phosphor_widget_1.MSG_LAYOUT_REQUEST);
	};

	SplitPanel.prototype.onChildRemoved = function (msg) {
		arrays.removeAt(this._sizers, msg.previousIndex);
		if (this.isAttached)
			phosphor_messaging_1.sendMessage(msg.child, phosphor_widget_1.MSG_BEFORE_DETACH);
		this.node.removeChild(msg.child.node);
		this.node.removeChild(getHandle(msg.child).node);
		phosphor_messaging_1.postMessage(this, phosphor_widget_1.MSG_LAYOUT_REQUEST);
		msg.child.clearOffsetGeometry();
	};

	SplitPanel.prototype.onChildMoved = function (msg) {
		arrays.move(this._sizers, msg.previousIndex, msg.currentIndex);
		phosphor_messaging_1.postMessage(this, phosphor_widget_1.MSG_LAYOUT_REQUEST);
	};

	SplitPanel.prototype.onAfterShow = function (msg) {
		this.update(true);
	};

	SplitPanel.prototype.onAfterAttach = function (msg) {
		this.node.addEventListener('mousedown', this);
		phosphor_messaging_1.postMessage(this, phosphor_widget_1.MSG_LAYOUT_REQUEST);
	};

	SplitPanel.prototype.onBeforeDetach = function (msg) {
		this.node.removeEventListener('mousedown', this);
	};

	SplitPanel.prototype.onChildShown = function (msg) {
		phosphor_messaging_1.postMessage(this, phosphor_widget_1.MSG_LAYOUT_REQUEST);
	};

	SplitPanel.prototype.onChildHidden = function (msg) {
		phosphor_messaging_1.postMessage(this, phosphor_widget_1.MSG_LAYOUT_REQUEST);
	};

	SplitPanel.prototype.onResize = function (msg) {
		if (this.isVisible) {
			if (msg.width < 0 || msg.height < 0) {
				var rect = this.offsetRect;
				this._layoutChildren(rect.width, rect.height);
			}
			else {
				this._layoutChildren(msg.width, msg.height);
			}
		}
	};

	SplitPanel.prototype.onUpdateRequest = function (msg) {
		if (this.isVisible) {
			var rect = this.offsetRect;
			this._layoutChildren(rect.width, rect.height);
		}
	};

	SplitPanel.prototype.onLayoutRequest = function (msg) {
		if (this.isAttached) {
			this._setupGeometry();
		}
	};

	SplitPanel.prototype._setupGeometry = function () {
		var visibleCount = 0;
		var orientation = this.orientation;
		var lastVisibleHandle = null;
		for (var i = 0, n = this.childCount; i < n; ++i) {
			var widget = this.childAt(i);
			var handle = getHandle(widget);
			handle.hidden = widget.hidden;
			handle.orientation = orientation;
			if (!handle.hidden) {
				lastVisibleHandle = handle;
				visibleCount++;
			}
		}
		if (lastVisibleHandle)
			lastVisibleHandle.hidden = true;
		this._fixedSpace = this.handleSize * Math.max(0, visibleCount - 1);
		var minW = 0;
		var minH = 0;
		var maxW = Infinity;
		var maxH = Infinity;
		if (orientation === Orientation.Horizontal) {
			minW = this._fixedSpace;
			maxW = visibleCount > 0 ? minW : maxW;
			for (var i = 0, n = this.childCount; i < n; ++i) {
				var widget = this.childAt(i);
				var sizer = this._sizers[i];
				if (sizer.size > 0) {
					sizer.sizeHint = sizer.size;
				}
				if (widget.hidden) {
					sizer.minSize = 0;
					sizer.maxSize = 0;
					continue;
				}
				var limits = widget.sizeLimits;
				sizer.stretch = SplitPanel.getStretch(widget);
				sizer.minSize = limits.minWidth;
				sizer.maxSize = limits.maxWidth;
				minW += limits.minWidth;
				maxW += limits.maxWidth;
				minH = Math.max(minH, limits.minHeight);
				maxH = Math.min(maxH, limits.maxHeight);
			}
		}
		else {
			minH = this._fixedSpace;
			maxH = visibleCount > 0 ? minH : maxH;
			for (var i = 0, n = this.childCount; i < n; ++i) {
				var widget = this.childAt(i);
				var sizer = this._sizers[i];
				if (sizer.size > 0) {
					sizer.sizeHint = sizer.size;
				}
				if (widget.hidden) {
					sizer.minSize = 0;
					sizer.maxSize = 0;
					continue;
				}
				var limits = widget.sizeLimits;
				sizer.stretch = SplitPanel.getStretch(widget);
				sizer.minSize = limits.minHeight;
				sizer.maxSize = limits.maxHeight;
				minH += limits.minHeight;
				maxH += limits.maxHeight;
				minW = Math.max(minW, limits.minWidth);
				maxW = Math.min(maxW, limits.maxWidth);
			}
		}
		var box = this.boxSizing;
		minW += box.horizontalSum;
		minH += box.verticalSum;
		maxW += box.horizontalSum;
		maxH += box.verticalSum;
		this.setSizeLimits(minW, minH, maxW, maxH);
		if (this.parent)
			phosphor_messaging_1.sendMessage(this.parent, phosphor_widget_1.MSG_LAYOUT_REQUEST);
		this.update(true);
	};

	SplitPanel.prototype._layoutChildren = function (offsetWidth, offsetHeight) {
		if (this.childCount === 0) {
			return;
		}
		var box = this.boxSizing;
		var top = box.paddingTop;
		var left = box.paddingLeft;
		var width = offsetWidth - box.horizontalSum;
		var height = offsetHeight - box.verticalSum;
		var horizontal = this.orientation === Orientation.Horizontal;
		if (this._pendingSizes) {
			var space = horizontal ? width : height;
			var adjusted = Math.max(0, space - this._fixedSpace);
			for (var i = 0, n = this._sizers.length; i < n; ++i) {
				this._sizers[i].sizeHint *= adjusted;
			}
			this._pendingSizes = false;
		}
		var handleSize = this.handleSize;
		if (horizontal) {
			phosphor_boxengine_1.boxCalc(this._sizers, Math.max(0, width - this._fixedSpace));
			for (var i = 0, n = this.childCount; i < n; ++i) {
				var widget = this.childAt(i);
				if (widget.hidden) {
					continue;
				}
				var size = this._sizers[i].size;
				var hStyle = getHandle(widget).node.style;
				widget.setOffsetGeometry(left, top, size, height);
				hStyle.top = top + 'px';
				hStyle.left = left + size + 'px';
				hStyle.width = handleSize + 'px';
				hStyle.height = height + 'px';
				left += size + handleSize;
			}
		}
		else {
			phosphor_boxengine_1.boxCalc(this._sizers, Math.max(0, height - this._fixedSpace));
			for (var i = 0, n = this.childCount; i < n; ++i) {
				var widget = this.childAt(i);
				if (widget.hidden) {
					continue;
				}
				var size = this._sizers[i].size;
				var hStyle = getHandle(widget).node.style;
				widget.setOffsetGeometry(left, top, width, size);
				hStyle.top = top + size + 'px';
				hStyle.left = left + 'px';
				hStyle.width = width + 'px';
				hStyle.height = handleSize + 'px';
				top += size + handleSize;
			}
		}
	};

	SplitPanel.prototype._evtMouseDown = function (event) {
		if (event.button !== 0) {
			return;
		}
		var index = this._findHandleIndex(event.target);
		if (index === -1) {
			return;
		}
		event.preventDefault();
		event.stopPropagation();
		document.addEventListener('mouseup', this, true);
		document.addEventListener('mousemove', this, true);
		var delta;
		var node = getHandle(this.childAt(index)).node;
		if (this.orientation === Orientation.Horizontal) {
			delta = event.clientX - node.getBoundingClientRect().left;
		}
		else {
			delta = event.clientY - node.getBoundingClientRect().top;
		}
		var override = phosphor_domutil_1.overrideCursor(window.getComputedStyle(node).cursor);
		this._pressData = { index: index, delta: delta, override: override };
	};

	SplitPanel.prototype._evtMouseUp = function (event) {
		if (event.button !== 0) {
			return;
		}
		event.preventDefault();
		event.stopPropagation();
		this._releaseMouse();
	};

	SplitPanel.prototype._evtMouseMove = function (event) {
		event.preventDefault();
		event.stopPropagation();
		var pos;
		var data = this._pressData;
		var rect = this.node.getBoundingClientRect();
		if (this.orientation === Orientation.Horizontal) {
			pos = event.clientX - data.delta - rect.left;
		}
		else {
			pos = event.clientY - data.delta - rect.top;
		}
		this._moveHandle(data.index, pos);
	};

	SplitPanel.prototype._releaseMouse = function () {
		if (!this._pressData) {
			return;
		}
		this._pressData.override.dispose();
		this._pressData = null;
		document.removeEventListener('mouseup', this, true);
		document.removeEventListener('mousemove', this, true);
	};

	SplitPanel.prototype._moveHandle = function (index, pos) {
		var widget = this.childAt(index);
		if (!widget) {
			return;
		}
		var handle = getHandle(widget);
		if (handle.hidden) {
			return;
		}
		var delta;
		if (this.orientation === Orientation.Horizontal) {
			delta = pos - handle.node.offsetLeft;
		}
		else {
			delta = pos - handle.node.offsetTop;
		}
		if (delta === 0) {
			return;
		}
		for (var i = 0, n = this._sizers.length; i < n; ++i) {
			var sizer = this._sizers[i];
			if (sizer.size > 0)
				sizer.sizeHint = sizer.size;
		}
		if (delta > 0) {
			growSizer(this._sizers, index, delta);
		}
		else {
			shrinkSizer(this._sizers, index, -delta);
		}
		this.update();
	};

	SplitPanel.prototype._findHandleIndex = function (target) {
		for (var i = 0, n = this.childCount; i < n; ++i) {
			var handle = getHandle(this.childAt(i));
			if (handle.node.contains(target))
				return i;
		}
		return -1;
	};

	SplitPanel.prototype._onOrientationChanged = function (old, value) {
		this.toggleClass(exports.HORIZONTAL_CLASS, value === Orientation.Horizontal);
		this.toggleClass(exports.VERTICAL_CLASS, value === Orientation.Vertical);
		phosphor_messaging_1.postMessage(this, phosphor_widget_1.MSG_LAYOUT_REQUEST);
	};

	SplitPanel.Horizontal = Orientation.Horizontal;

	SplitPanel.Vertical = Orientation.Vertical;

	SplitPanel.orientationProperty = new phosphor_properties_1.Property({
		value: Orientation.Horizontal,
		changed: function (owner, old, value) { return owner._onOrientationChanged(old, value); },
	});

	SplitPanel.handleSizeProperty = new phosphor_properties_1.Property({
		value: 3,
		coerce: function (owner, value) { return Math.max(0, value | 0); },
		changed: function (owner) { return phosphor_messaging_1.postMessage(owner, phosphor_widget_1.MSG_LAYOUT_REQUEST); },
	});

	SplitPanel.stretchProperty = new phosphor_properties_1.Property({
		value: 0,
		coerce: function (owner, value) { return Math.max(0, value | 0); },
		changed: onStretchChanged,
	});
	return SplitPanel;
})(phosphor_widget_1.Widget);
exports.SplitPanel = SplitPanel;

var SplitHandle = (function (_super) {
	__extends(SplitHandle, _super);

	function SplitHandle() {
		_super.call(this);
		this._hidden = false;
		this._orientation = Orientation.Horizontal;
		this.addClass(exports.SPLIT_HANDLE_CLASS);
		this.addClass(exports.HORIZONTAL_CLASS);
	}

	SplitHandle.createNode = function () {
		var node = document.createElement('div');
		var overlay = document.createElement('div');
		overlay.className = exports.OVERLAY_CLASS;
		node.appendChild(overlay);
		return node;
	};
	Object.defineProperty(SplitHandle.prototype, "hidden", {

		get: function () {
			return this._hidden;
		},

		set: function (hidden) {
			if (hidden === this._hidden) {
				return;
			}
			this._hidden = hidden;
			this.toggleClass(exports.HIDDEN_CLASS, hidden);
		},
		enumerable: true,
		configurable: true
	});
	Object.defineProperty(SplitHandle.prototype, "orientation", {

		get: function () {
			return this._orientation;
		},

		set: function (value) {
			if (value === this._orientation) {
				return;
			}
			this._orientation = value;
			this.toggleClass(exports.HORIZONTAL_CLASS, value === Orientation.Horizontal);
			this.toggleClass(exports.VERTICAL_CLASS, value === Orientation.Vertical);
		},
		enumerable: true,
		configurable: true
	});
	return SplitHandle;
})(phosphor_nodewrapper_1.NodeWrapper);

var splitHandleProperty = new phosphor_properties_1.Property({
	create: function (owner) { return new SplitHandle(); },
});

function getHandle(widget) {
	return splitHandleProperty.get(widget);
}

function onStretchChanged(child, old, value) {
	if (child.parent instanceof SplitPanel) {
		phosphor_messaging_1.postMessage(child.parent, phosphor_widget_1.MSG_LAYOUT_REQUEST);
	}
}

function createSizer(size) {
	var sizer = new phosphor_boxengine_1.BoxSizer();
	sizer.sizeHint = size | 0;
	return sizer;
}

function averageSize(sizers) {
	var sum = sizers.reduce(function (v, s) { return v + s.size; }, 0);
	return sum > 0 ? sum / sizers.length : 0;
}

function growSizer(sizers, index, delta) {
	var growLimit = 0;
	for (var i = 0; i <= index; ++i) {
		var sizer = sizers[i];
		growLimit += sizer.maxSize - sizer.size;
	}
	var shrinkLimit = 0;
	for (var i = index + 1, n = sizers.length; i < n; ++i) {
		var sizer = sizers[i];
		shrinkLimit += sizer.size - sizer.minSize;
	}
	delta = Math.min(delta, growLimit, shrinkLimit);
	var grow = delta;
	for (var i = index; i >= 0 && grow > 0; --i) {
		var sizer = sizers[i];
		var limit = sizer.maxSize - sizer.size;
		if (limit >= grow) {
			sizer.sizeHint = sizer.size + grow;
			grow = 0;
		}
		else {
			sizer.sizeHint = sizer.size + limit;
			grow -= limit;
		}
	}
	var shrink = delta;
	for (var i = index + 1, n = sizers.length; i < n && shrink > 0; ++i) {
		var sizer = sizers[i];
		var limit = sizer.size - sizer.minSize;
		if (limit >= shrink) {
			sizer.sizeHint = sizer.size - shrink;
			shrink = 0;
		}
		else {
			sizer.sizeHint = sizer.size - limit;
			shrink -= limit;
		}
	}
}

function shrinkSizer(sizers, index, delta) {
	var growLimit = 0;
	for (var i = index + 1, n = sizers.length; i < n; ++i) {
		var sizer = sizers[i];
		growLimit += sizer.maxSize - sizer.size;
	}
	var shrinkLimit = 0;
	for (var i = 0; i <= index; ++i) {
		var sizer = sizers[i];
		shrinkLimit += sizer.size - sizer.minSize;
	}
	delta = Math.min(delta, growLimit, shrinkLimit);
	var grow = delta;
	for (var i = index + 1, n = sizers.length; i < n && grow > 0; ++i) {
		var sizer = sizers[i];
		var limit = sizer.maxSize - sizer.size;
		if (limit >= grow) {
			sizer.sizeHint = sizer.size + grow;
			grow = 0;
		}
		else {
			sizer.sizeHint = sizer.size + limit;
			grow -= limit;
		}
	}
	var shrink = delta;
	for (var i = index; i >= 0 && shrink > 0; --i) {
		var sizer = sizers[i];
		var limit = sizer.size - sizer.minSize;
		if (limit >= shrink) {
			sizer.sizeHint = sizer.size - shrink;
			shrink = 0;
		}
		else {
			sizer.sizeHint = sizer.size - limit;
			shrink -= limit;
		}
	}
}

function normalize(values) {
	var n = values.length;
	if (n === 0) {
		return [];
	}
	var sum = 0;
	for (var i = 0; i < n; ++i) {
		sum += values[i];
	}
	var result = new Array(n);
	if (sum === 0) {
		for (var i = 0; i < n; ++i) {
			result[i] = 1 / n;
		}
	}
	else {
		for (var i = 0; i < n; ++i) {
			result[i] = values[i] / sum;
		}
	}
	return result;
}
},{"./index.css":45,"phosphor-arrays":47,"phosphor-boxengine":48,"phosphor-domutil":51,"phosphor-messaging":40,"phosphor-nodewrapper":42,"phosphor-properties":52,"phosphor-widget":72}],47:[function(require,module,exports){
arguments[4][6][0].apply(exports,arguments)
},{"dup":6}],48:[function(require,module,exports){
arguments[4][3][0].apply(exports,arguments)
},{"dup":3}],49:[function(require,module,exports){
arguments[4][10][0].apply(exports,arguments)
},{"dup":10}],50:[function(require,module,exports){
var css = "body.p-mod-override-cursor *{cursor:inherit!important}"; (require("browserify-css").createStyle(css, { "href": "node_modules/phosphor-splitpanel/node_modules/phosphor-domutil/lib/index.css"})); module.exports = css;
},{"browserify-css":2}],51:[function(require,module,exports){
arguments[4][16][0].apply(exports,arguments)
},{"./index.css":50,"dup":16,"phosphor-disposable":49}],52:[function(require,module,exports){
arguments[4][8][0].apply(exports,arguments)
},{"dup":8,"phosphor-signaling":53}],53:[function(require,module,exports){
arguments[4][9][0].apply(exports,arguments)
},{"dup":9}],54:[function(require,module,exports){
var css = ".p-StackedPanel{position:relative}.p-StackedPanel>.p-Widget{position:absolute}"; (require("browserify-css").createStyle(css, { "href": "node_modules/phosphor-stackedpanel/lib/index.css"})); module.exports = css;
},{"browserify-css":2}],55:[function(require,module,exports){
arguments[4][20][0].apply(exports,arguments)
},{"./index.css":54,"dup":20,"phosphor-messaging":40,"phosphor-properties":56,"phosphor-signaling":57,"phosphor-widget":72}],56:[function(require,module,exports){
arguments[4][8][0].apply(exports,arguments)
},{"dup":8,"phosphor-signaling":57}],57:[function(require,module,exports){
arguments[4][9][0].apply(exports,arguments)
},{"dup":9}],58:[function(require,module,exports){
var css = ".p-TabBar{position:relative}.p-TabBar-header{display:none;position:absolute;top:0;left:0;right:0;z-index:0}.p-TabBar-content{position:absolute;top:0;left:0;right:0;bottom:0;z-index:2;display:flex;flex-direction:row}.p-TabBar-footer{display:none;position:absolute;left:0;right:0;bottom:0;z-index:1}.p-Tab{display:flex;flex-direction:row;box-sizing:border-box;overflow:hidden}.p-Tab-close-icon,.p-Tab-icon{flex:0 0 auto}.p-Tab-text{flex:1 1 auto;overflow:hidden;white-space:nowrap}.p-TabBar.p-mod-dragging>.p-TabBar-content>.p-Tab{position:relative;left:0;transition:left 150ms ease}.p-TabBar.p-mod-dragging>.p-TabBar-content>.p-Tab.p-mod-active{transition:none}"; (require("browserify-css").createStyle(css, { "href": "node_modules/phosphor-tabs/lib/index.css"})); module.exports = css;
},{"browserify-css":2}],59:[function(require,module,exports){

'use strict';
function __export(m) {
	for (var p in m) if (!exports.hasOwnProperty(p)) exports[p] = m[p];
}
__export(require('./tab'));
__export(require('./tabbar'));
__export(require('./tabpanel'));
require('./index.css');
},{"./index.css":58,"./tab":60,"./tabbar":61,"./tabpanel":62}],60:[function(require,module,exports){

'use strict';
var __extends = (this && this.__extends) || function (d, b) {
	for (var p in b) if (b.hasOwnProperty(p)) d[p] = b[p];
	function __() { this.constructor = d; }
	d.prototype = b === null ? Object.create(b) : (__.prototype = b.prototype, new __());
};
var phosphor_nodewrapper_1 = require('phosphor-nodewrapper');

exports.TAB_CLASS = 'p-Tab';

exports.TEXT_CLASS = 'p-Tab-text';

exports.ICON_CLASS = 'p-Tab-icon';

exports.CLOSE_ICON_CLASS = 'p-Tab-close-icon';

exports.SELECTED_CLASS = 'p-mod-selected';

exports.CLOSABLE_CLASS = 'p-mod-closable';

var Tab = (function (_super) {
	__extends(Tab, _super);

	function Tab(text) {
		_super.call(this);
		this.addClass(exports.TAB_CLASS);
		if (text)
			this.text = text;
	}

	Tab.createNode = function () {
		var node = document.createElement('div');
		var icon = document.createElement('span');
		var text = document.createElement('span');
		var closeIcon = document.createElement('span');
		icon.className = exports.ICON_CLASS;
		text.className = exports.TEXT_CLASS;
		closeIcon.className = exports.CLOSE_ICON_CLASS;
		node.appendChild(icon);
		node.appendChild(text);
		node.appendChild(closeIcon);
		return node;
	};
	Object.defineProperty(Tab.prototype, "text", {

		get: function () {
			return this.node.children[1].textContent;
		},

		set: function (text) {
			this.node.children[1].textContent = text;
		},
		enumerable: true,
		configurable: true
	});
	Object.defineProperty(Tab.prototype, "selected", {

		get: function () {
			return this.hasClass(exports.SELECTED_CLASS);
		},

		set: function (selected) {
			this.toggleClass(exports.SELECTED_CLASS, selected);
		},
		enumerable: true,
		configurable: true
	});
	Object.defineProperty(Tab.prototype, "closable", {

		get: function () {
			return this.hasClass(exports.CLOSABLE_CLASS);
		},

		set: function (closable) {
			this.toggleClass(exports.CLOSABLE_CLASS, closable);
		},
		enumerable: true,
		configurable: true
	});
	Object.defineProperty(Tab.prototype, "closeIconNode", {

		get: function () {
			return this.node.lastChild;
		},
		enumerable: true,
		configurable: true
	});
	return Tab;
})(phosphor_nodewrapper_1.NodeWrapper);
exports.Tab = Tab;
},{"phosphor-nodewrapper":42}],61:[function(require,module,exports){

'use strict';
var __extends = (this && this.__extends) || function (d, b) {
	for (var p in b) if (b.hasOwnProperty(p)) d[p] = b[p];
	function __() { this.constructor = d; }
	d.prototype = b === null ? Object.create(b) : (__.prototype = b.prototype, new __());
};
var arrays = require('phosphor-arrays');
var phosphor_domutil_1 = require('phosphor-domutil');
var phosphor_properties_1 = require('phosphor-properties');
var phosphor_signaling_1 = require('phosphor-signaling');
var phosphor_widget_1 = require('phosphor-widget');

exports.TAB_BAR_CLASS = 'p-TabBar';

exports.HEADER_CLASS = 'p-TabBar-header';

exports.CONTENT_CLASS = 'p-TabBar-content';

exports.FOOTER_CLASS = 'p-TabBar-footer';

exports.DRAGGING_CLASS = 'p-mod-dragging';

exports.ACTIVE_CLASS = 'p-mod-active';

exports.FIRST_CLASS = 'p-mod-first';

exports.LAST_CLASS = 'p-mod-last';

var DRAG_THRESHOLD = 5;

var DETACH_THRESHOLD = 20;

var TRANSITION_DURATION = 150;

var TabBar = (function (_super) {
	__extends(TabBar, _super);

	function TabBar() {
		_super.call(this);
		this._tabs = [];
		this._previousTab = null;
		this._dragData = null;
		this.addClass(exports.TAB_BAR_CLASS);
	}

	TabBar.createNode = function () {
		var node = document.createElement('div');
		var header = document.createElement('div');
		var content = document.createElement('div');
		var footer = document.createElement('div');
		header.className = exports.HEADER_CLASS;
		content.className = exports.CONTENT_CLASS;
		footer.className = exports.FOOTER_CLASS;
		node.appendChild(header);
		node.appendChild(content);
		node.appendChild(footer);
		return node;
	};

	TabBar.prototype.dispose = function () {
		this._releaseMouse();
		this._previousTab = null;
		this._tabs.length = 0;
		_super.prototype.dispose.call(this);
	};
	Object.defineProperty(TabBar.prototype, "tabMoved", {

		get: function () {
			return TabBar.tabMovedSignal.bind(this);
		},
		enumerable: true,
		configurable: true
	});
	Object.defineProperty(TabBar.prototype, "tabSelected", {

		get: function () {
			return TabBar.tabSelectedSignal.bind(this);
		},
		enumerable: true,
		configurable: true
	});
	Object.defineProperty(TabBar.prototype, "tabCloseRequested", {

		get: function () {
			return TabBar.tabCloseRequestedSignal.bind(this);
		},
		enumerable: true,
		configurable: true
	});
	Object.defineProperty(TabBar.prototype, "tabDetachRequested", {

		get: function () {
			return TabBar.tabDetachRequestedSignal.bind(this);
		},
		enumerable: true,
		configurable: true
	});
	Object.defineProperty(TabBar.prototype, "previousTab", {

		get: function () {
			return this._previousTab;
		},
		enumerable: true,
		configurable: true
	});
	Object.defineProperty(TabBar.prototype, "selectedTab", {

		get: function () {
			return TabBar.selectedTabProperty.get(this);
		},

		set: function (value) {
			TabBar.selectedTabProperty.set(this, value);
		},
		enumerable: true,
		configurable: true
	});
	Object.defineProperty(TabBar.prototype, "tabsMovable", {

		get: function () {
			return TabBar.tabsMovableProperty.get(this);
		},

		set: function (value) {
			TabBar.tabsMovableProperty.set(this, value);
		},
		enumerable: true,
		configurable: true
	});
	Object.defineProperty(TabBar.prototype, "tabs", {

		get: function () {
			return this._tabs.slice();
		},

		set: function (tabs) {
			var _this = this;
			this.clearTabs();
			tabs.forEach(function (tab) { return _this.addTab(tab); });
		},
		enumerable: true,
		configurable: true
	});
	Object.defineProperty(TabBar.prototype, "tabCount", {

		get: function () {
			return this._tabs.length;
		},
		enumerable: true,
		configurable: true
	});

	TabBar.prototype.tabAt = function (index) {
		return this._tabs[index | 0];
	};

	TabBar.prototype.tabIndex = function (tab) {
		return this._tabs.indexOf(tab);
	};

	TabBar.prototype.addTab = function (tab) {
		return this.insertTab(this._tabs.length, tab);
	};

	TabBar.prototype.insertTab = function (index, tab) {
		this.removeTab(tab);
		return this._insertTab(index, tab);
	};

	TabBar.prototype.moveTab = function (fromIndex, toIndex) {
		this._releaseMouse();
		return this._moveTab(fromIndex, toIndex);
	};

	TabBar.prototype.removeTabAt = function (index) {
		this._releaseMouse();
		return this._removeTab(index);
	};

	TabBar.prototype.removeTab = function (tab) {
		this._releaseMouse();
		var i = this._tabs.indexOf(tab);
		if (i !== -1)
			this._removeTab(i);
		return i;
	};

	TabBar.prototype.clearTabs = function () {
		while (this._tabs.length > 0) {
			this.removeTabAt(this._tabs.length - 1);
		}
	};

	TabBar.prototype.attachTab = function (tab, clientX) {
		if (this._dragData || !this.tabsMovable) {
			return false;
		}
		if (this._tabs.indexOf(tab) !== -1) {
			return false;
		}
		var index = this._tabs.length;
		this._insertTab(index, tab);
		this.selectedTab = tab;
		var content = this.node.firstChild.nextSibling;
		var tabRect = tab.node.getBoundingClientRect();
		var data = this._dragData = new DragData();
		data.tab = tab;
		data.tabIndex = index;
		data.tabLeft = tab.node.offsetLeft;
		data.tabWidth = tabRect.width;
		data.pressX = tabRect.left + Math.floor(0.4 * tabRect.width);
		data.pressY = tabRect.top + (tabRect.height >> 1);
		data.tabPressX = Math.floor(0.4 * tabRect.width);
		data.tabLayout = snapTabLayout(this._tabs);
		data.contentRect = content.getBoundingClientRect();
		data.cursorGrab = phosphor_domutil_1.overrideCursor('default');
		data.dragActive = true;
		document.addEventListener('mouseup', this, true);
		document.addEventListener('mousemove', this, true);
		tab.addClass(exports.ACTIVE_CLASS);
		this.addClass(exports.DRAGGING_CLASS);
		this._updateDragPosition(clientX);
		return true;
	};

	TabBar.prototype.handleEvent = function (event) {
		switch (event.type) {
			case 'click':
				this._evtClick(event);
				break;
			case 'mousedown':
				this._evtMouseDown(event);
				break;
			case 'mousemove':
				this._evtMouseMove(event);
				break;
			case 'mouseup':
				this._evtMouseUp(event);
				break;
		}
	};

	TabBar.prototype.onAfterAttach = function (msg) {
		this.node.addEventListener('mousedown', this);
		this.node.addEventListener('click', this);
	};

	TabBar.prototype.onBeforeDetach = function (msg) {
		this.node.removeEventListener('mousedown', this);
		this.node.removeEventListener('click', this);
	};

	TabBar.prototype._evtClick = function (event) {
		if (event.button !== 0) {
			return;
		}
		var index = hitTestTabs(this._tabs, event.clientX, event.clientY);
		if (index < 0) {
			return;
		}
		event.preventDefault();
		event.stopPropagation();
		var tab = this._tabs[index];
		var target = event.target;
		if (tab.closable && tab.closeIconNode.contains(target)) {
			this.tabCloseRequested.emit({ index: index, tab: tab });
		}
	};

	TabBar.prototype._evtMouseDown = function (event) {
		if (event.button !== 0) {
			return;
		}
		if (this._dragData) {
			return;
		}
		var index = hitTestTabs(this._tabs, event.clientX, event.clientY);
		if (index < 0) {
			return;
		}
		event.preventDefault();
		event.stopPropagation();
		var tab = this._tabs[index];
		if (tab.closeIconNode.contains(event.target)) {
			return;
		}
		if (this.tabsMovable) {
			var tabRect = tab.node.getBoundingClientRect();
			var data = this._dragData = new DragData();
			data.tab = tab;
			data.tabIndex = index;
			data.tabLeft = tab.node.offsetLeft;
			data.tabWidth = tabRect.width;
			data.pressX = event.clientX;
			data.pressY = event.clientY;
			data.tabPressX = event.clientX - tabRect.left;
			document.addEventListener('mouseup', this, true);
			document.addEventListener('mousemove', this, true);
		}
		this.selectedTab = tab;
	};

	TabBar.prototype._evtMouseMove = function (event) {
		event.preventDefault();
		event.stopPropagation();
		if (!this._dragData) {
			return;
		}
		var data = this._dragData;
		if (!data.dragActive) {
			var dx = Math.abs(event.clientX - data.pressX);
			var dy = Math.abs(event.clientY - data.pressY);
			if (dx < DRAG_THRESHOLD && dy < DRAG_THRESHOLD) {
				return;
			}
			var content = this.node.firstChild.nextSibling;
			data.tabLayout = snapTabLayout(this._tabs);
			data.contentRect = content.getBoundingClientRect();
			data.cursorGrab = phosphor_domutil_1.overrideCursor('default');
			data.dragActive = true;
			data.tab.addClass(exports.ACTIVE_CLASS);
			this.addClass(exports.DRAGGING_CLASS);
		}
		if (!data.detachRequested && shouldDetach(data.contentRect, event)) {
			data.detachRequested = true;
			this.tabDetachRequested.emit({
				tab: data.tab,
				index: data.tabIndex,
				clientX: event.clientX,
				clientY: event.clientY,
			});
			if (!this._dragData) {
				return;
			}
		}
		this._updateDragPosition(event.clientX);
	};

	TabBar.prototype._evtMouseUp = function (event) {
		var _this = this;
		if (event.button !== 0) {
			return;
		}
		event.preventDefault();
		event.stopPropagation();
		if (!this._dragData) {
			return;
		}
		document.removeEventListener('mouseup', this, true);
		document.removeEventListener('mousemove', this, true);
		var data = this._dragData;
		if (!data.dragActive) {
			this._dragData = null;
			return;
		}
		var idealLeft;
		if (data.tabTargetIndex === data.tabIndex) {
			idealLeft = 0;
		}
		else if (data.tabTargetIndex > data.tabIndex) {
			var tl = data.tabLayout[data.tabTargetIndex];
			idealLeft = tl.left + tl.width - data.tabWidth - data.tabLeft;
		}
		else {
			var tl = data.tabLayout[data.tabTargetIndex];
			idealLeft = tl.left - data.tabLeft;
		}
		var maxLeft = data.contentRect.width - (data.tabLeft + data.tabWidth);
		var adjustedLeft = Math.max(-data.tabLeft, Math.min(idealLeft, maxLeft));
		data.tab.node.style.left = adjustedLeft + 'px';
		data.tab.removeClass(exports.ACTIVE_CLASS);
		setTimeout(function () {
			if (_this._dragData !== data) {
				return;
			}
			_this._dragData = null;
			for (var i = 0, n = _this._tabs.length; i < n; ++i) {
				_this._tabs[i].node.style.left = '';
			}
			data.cursorGrab.dispose();
			data.tab.removeClass(exports.ACTIVE_CLASS);
			_this.removeClass(exports.DRAGGING_CLASS);
			if (data.tabTargetIndex !== -1) {
				_this._moveTab(data.tabIndex, data.tabTargetIndex);
			}
		}, TRANSITION_DURATION);
	};

	TabBar.prototype._updateDragPosition = function (clientX) {
		var data = this._dragData;
		if (!data || !data.dragActive) {
			return;
		}
		var offsetLeft = clientX - data.contentRect.left;
		var targetLeft = offsetLeft - data.tabPressX;
		var targetRight = targetLeft + data.tabWidth;
		data.tabTargetIndex = data.tabIndex;
		for (var i = 0, n = this._tabs.length; i < n; ++i) {
			var style = this._tabs[i].node.style;
			var layout = data.tabLayout[i];
			var threshold = layout.left + (layout.width >> 1);
			if (i < data.tabIndex && targetLeft < threshold) {
				style.left = data.tabWidth + data.tabLayout[i + 1].margin + 'px';
				data.tabTargetIndex = Math.min(data.tabTargetIndex, i);
			}
			else if (i > data.tabIndex && targetRight > threshold) {
				style.left = -data.tabWidth - layout.margin + 'px';
				data.tabTargetIndex = i;
			}
			else if (i !== data.tabIndex) {
				style.left = '';
			}
		}
		var idealLeft = clientX - data.pressX;
		var maxLeft = data.contentRect.width - (data.tabLeft + data.tabWidth);
		var adjustedLeft = Math.max(-data.tabLeft, Math.min(idealLeft, maxLeft));
		data.tab.node.style.left = adjustedLeft + 'px';
	};

	TabBar.prototype._releaseMouse = function () {
		if (!this._dragData) {
			return;
		}
		document.removeEventListener('mouseup', this, true);
		document.removeEventListener('mousemove', this, true);
		var data = this._dragData;
		this._dragData = null;
		if (!data.dragActive) {
			return;
		}
		for (var i = 0, n = this._tabs.length; i < n; ++i) {
			this._tabs[i].node.style.left = '';
		}
		data.cursorGrab.dispose();
		data.tab.removeClass(exports.ACTIVE_CLASS);
		this.removeClass(exports.DRAGGING_CLASS);
	};

	TabBar.prototype._insertTab = function (index, tab) {
		tab.selected = false;
		var i = arrays.insert(this._tabs, index, tab);
		var content = this.node.firstChild.nextSibling;
		content.appendChild(tab.node);
		if (!this.selectedTab) {
			this.selectedTab = tab;
		}
		else {
			this._updateTabOrdering();
		}
		return i;
	};

	TabBar.prototype._moveTab = function (fromIndex, toIndex) {
		var i = fromIndex | 0;
		var j = toIndex | 0;
		if (!arrays.move(this._tabs, i, j)) {
			return false;
		}
		if (i === j) {
			return true;
		}
		this._updateTabOrdering();
		this.tabMoved.emit({ fromIndex: i, toIndex: j });
		return true;
	};

	TabBar.prototype._removeTab = function (index) {
		var i = index | 0;
		var tab = arrays.removeAt(this._tabs, i);
		if (!tab) {
			return void 0;
		}
		var content = this.node.firstChild.nextSibling;
		content.removeChild(tab.node);
		tab.selected = false;
		tab.node.style.left = '';
		tab.node.style.zIndex = '';
		tab.removeClass(exports.ACTIVE_CLASS);
		tab.removeClass(exports.FIRST_CLASS);
		tab.removeClass(exports.LAST_CLASS);
		if (tab === this.selectedTab) {
			var next = this._previousTab || this._tabs[i] || this._tabs[i - 1];
			this.selectedTab = next;
			this._previousTab = null;
		}
		else if (tab === this._previousTab) {
			this._previousTab = null;
			this._updateTabOrdering();
		}
		else {
			this._updateTabOrdering();
		}
		return tab;
	};

	TabBar.prototype._updateTabOrdering = function () {
		if (this._tabs.length === 0) {
			return;
		}
		var selectedTab = this.selectedTab;
		for (var i = 0, n = this._tabs.length, k = n - 1; i < n; ++i) {
			var tab = this._tabs[i];
			var style = tab.node.style;
			tab.removeClass(exports.FIRST_CLASS);
			tab.removeClass(exports.LAST_CLASS);
			style.order = i + '';
			if (tab === selectedTab) {
				style.zIndex = n + '';
			}
			else {
				style.zIndex = k-- + '';
			}
		}
		this._tabs[0].addClass(exports.FIRST_CLASS);
		this._tabs[n - 1].addClass(exports.LAST_CLASS);
	};

	TabBar.prototype._onSelectedTabChanged = function (old, tab) {
		if (old)
			old.selected = false;
		if (tab)
			tab.selected = true;
		this._previousTab = old;
		this._updateTabOrdering();
		this.tabSelected.emit({ index: this.tabIndex(tab), tab: tab });
	};

	TabBar.tabMovedSignal = new phosphor_signaling_1.Signal();

	TabBar.tabSelectedSignal = new phosphor_signaling_1.Signal();

	TabBar.tabCloseRequestedSignal = new phosphor_signaling_1.Signal();

	TabBar.tabDetachRequestedSignal = new phosphor_signaling_1.Signal();

	TabBar.selectedTabProperty = new phosphor_properties_1.Property({
		value: null,
		coerce: function (owner, val) { return (val && owner.tabIndex(val) !== -1) ? val : null; },
		changed: function (owner, old, val) { return owner._onSelectedTabChanged(old, val); },
	});

	TabBar.tabsMovableProperty = new phosphor_properties_1.Property({
		value: true,
	});
	return TabBar;
})(phosphor_widget_1.Widget);
exports.TabBar = TabBar;

var DragData = (function () {
	function DragData() {

		this.tab = null;

		this.tabLeft = -1;

		this.tabWidth = -1;

		this.tabIndex = -1;

		this.tabPressX = -1;

		this.tabTargetIndex = -1;

		this.tabLayout = null;

		this.pressX = -1;

		this.pressY = -1;

		this.contentRect = null;

		this.cursorGrab = null;

		this.dragActive = false;

		this.detachRequested = false;
	}
	return DragData;
})();

function shouldDetach(rect, event) {
	return ((event.clientX < rect.left - DETACH_THRESHOLD) ||
		(event.clientX >= rect.right + DETACH_THRESHOLD) ||
		(event.clientY < rect.top - DETACH_THRESHOLD) ||
		(event.clientY >= rect.bottom + DETACH_THRESHOLD));
}

function hitTestTabs(tabs, clientX, clientY) {
	for (var i = 0, n = tabs.length; i < n; ++i) {
		if (phosphor_domutil_1.hitTest(tabs[i].node, clientX, clientY)) {
			return i;
		}
	}
	return -1;
}

function snapTabLayout(tabs) {
	var layout = new Array(tabs.length);
	for (var i = 0, n = tabs.length; i < n; ++i) {
		var node = tabs[i].node;
		var left = node.offsetLeft;
		var width = node.offsetWidth;
		var cstyle = window.getComputedStyle(tabs[i].node);
		var margin = parseInt(cstyle.marginLeft, 10) || 0;
		layout[i] = { margin: margin, left: left, width: width };
	}
	return layout;
}
},{"phosphor-arrays":63,"phosphor-domutil":66,"phosphor-properties":67,"phosphor-signaling":68,"phosphor-widget":72}],62:[function(require,module,exports){

'use strict';
var __extends = (this && this.__extends) || function (d, b) {
	for (var p in b) if (b.hasOwnProperty(p)) d[p] = b[p];
	function __() { this.constructor = d; }
	d.prototype = b === null ? Object.create(b) : (__.prototype = b.prototype, new __());
};
var phosphor_boxpanel_1 = require('phosphor-boxpanel');
var phosphor_properties_1 = require('phosphor-properties');
var phosphor_signaling_1 = require('phosphor-signaling');
var phosphor_stackedpanel_1 = require('phosphor-stackedpanel');
var tabbar_1 = require('./tabbar');

exports.TAB_PANEL_CLASS = 'p-TabPanel';

var TabPanel = (function (_super) {
	__extends(TabPanel, _super);

	function TabPanel() {
		_super.call(this);
		this.addClass(exports.TAB_PANEL_CLASS);
		var tabs = new tabbar_1.TabBar();
		tabs.tabMoved.connect(this._onTabMoved, this);
		tabs.tabSelected.connect(this._onTabSelected, this);
		tabs.tabCloseRequested.connect(this._onTabCloseRequested, this);
		var stack = new phosphor_stackedpanel_1.StackedPanel();
		stack.currentChanged.connect(this._onCurrentChanged, this);
		stack.widgetRemoved.connect(this._onWidgetRemoved, this);
		phosphor_boxpanel_1.BoxPanel.setStretch(tabs, 0);
		phosphor_boxpanel_1.BoxPanel.setStretch(stack, 1);
		this.direction = phosphor_boxpanel_1.BoxPanel.TopToBottom;
		this.spacing = 0;
		this._tabs = tabs;
		this._stack = stack;
		this.addChild(tabs);
		this.addChild(stack);
	}

	TabPanel.getTab = function (widget) {
		return TabPanel.tabProperty.get(widget);
	};

	TabPanel.setTab = function (widget, tab) {
		TabPanel.tabProperty.set(widget, tab);
	};

	TabPanel.prototype.dispose = function () {
		this._tabs = null;
		this._stack = null;
		_super.prototype.dispose.call(this);
	};
	Object.defineProperty(TabPanel.prototype, "currentChanged", {

		get: function () {
			return TabPanel.currentChangedSignal.bind(this);
		},
		enumerable: true,
		configurable: true
	});
	Object.defineProperty(TabPanel.prototype, "currentWidget", {

		get: function () {
			return this._stack.currentWidget;
		},

		set: function (widget) {
			var i = this._stack.childIndex(widget);
			this._tabs.selectedTab = this._tabs.tabAt(i);
		},
		enumerable: true,
		configurable: true
	});
	Object.defineProperty(TabPanel.prototype, "tabsMovable", {

		get: function () {
			return this._tabs.tabsMovable;
		},

		set: function (movable) {
			this._tabs.tabsMovable = movable;
		},
		enumerable: true,
		configurable: true
	});
	Object.defineProperty(TabPanel.prototype, "widgets", {

		get: function () {
			return this._stack.children;
		},

		set: function (widgets) {
			var _this = this;
			this.clearWidgets();
			widgets.forEach(function (widget) { return _this.addWidget(widget); });
		},
		enumerable: true,
		configurable: true
	});
	Object.defineProperty(TabPanel.prototype, "widgetCount", {

		get: function () {
			return this._stack.childCount;
		},
		enumerable: true,
		configurable: true
	});

	TabPanel.prototype.widgetAt = function (index) {
		return this._stack.childAt(index);
	};

	TabPanel.prototype.widgetIndex = function (widget) {
		return this._stack.childIndex(widget);
	};

	TabPanel.prototype.addWidget = function (widget) {
		return this.insertWidget(this.widgetCount, widget);
	};

	TabPanel.prototype.insertWidget = function (index, widget) {
		var tab = TabPanel.getTab(widget);
		if (!tab)
			throw new Error('`TabPanel.tab` property not set');
		var i = this._stack.insertChild(index, widget);
		return this._tabs.insertTab(i, tab);
	};

	TabPanel.prototype.moveWidget = function (fromIndex, toIndex) {
		return this._tabs.moveTab(fromIndex, toIndex);
	};

	TabPanel.prototype.removeWidgetAt = function (index) {
		return this._stack.removeChildAt(index);
	};

	TabPanel.prototype.removeWidget = function (widget) {
		return this._stack.removeChild(widget);
	};

	TabPanel.prototype.clearWidgets = function () {
		this._stack.clearChildren();
	};

	TabPanel.prototype._onTabMoved = function (sender, args) {
		this._stack.moveChild(args.fromIndex, args.toIndex);
	};

	TabPanel.prototype._onTabSelected = function (sender, args) {
		this._stack.currentWidget = this._stack.childAt(args.index);
	};

	TabPanel.prototype._onTabCloseRequested = function (sender, args) {
		this._stack.childAt(args.index).close();
	};

	TabPanel.prototype._onCurrentChanged = function (sender, args) {
		this.currentChanged.emit(args);
	};

	TabPanel.prototype._onWidgetRemoved = function (sender, args) {
		this._tabs.removeTabAt(args.index);
	};

	TabPanel.currentChangedSignal = new phosphor_signaling_1.Signal();

	TabPanel.tabProperty = new phosphor_properties_1.Property({
		value: null,
		coerce: function (owner, value) { return value || null; },
	});
	return TabPanel;
})(phosphor_boxpanel_1.BoxPanel);
exports.TabPanel = TabPanel;
},{"./tabbar":61,"phosphor-boxpanel":5,"phosphor-properties":67,"phosphor-signaling":68,"phosphor-stackedpanel":70}],63:[function(require,module,exports){
arguments[4][6][0].apply(exports,arguments)
},{"dup":6}],64:[function(require,module,exports){
arguments[4][10][0].apply(exports,arguments)
},{"dup":10}],65:[function(require,module,exports){
var css = "body.p-mod-override-cursor *{cursor:inherit!important}"; (require("browserify-css").createStyle(css, { "href": "node_modules/phosphor-tabs/node_modules/phosphor-domutil/lib/index.css"})); module.exports = css;
},{"browserify-css":2}],66:[function(require,module,exports){
arguments[4][16][0].apply(exports,arguments)
},{"./index.css":65,"dup":16,"phosphor-disposable":64}],67:[function(require,module,exports){
arguments[4][8][0].apply(exports,arguments)
},{"dup":8,"phosphor-signaling":68}],68:[function(require,module,exports){
arguments[4][9][0].apply(exports,arguments)
},{"dup":9}],69:[function(require,module,exports){
var css = ".p-StackedPanel{position:relative}.p-StackedPanel>.p-Widget{position:absolute}"; (require("browserify-css").createStyle(css, { "href": "node_modules/phosphor-tabs/node_modules/phosphor-stackedpanel/lib/index.css"})); module.exports = css;
},{"browserify-css":2}],70:[function(require,module,exports){
arguments[4][20][0].apply(exports,arguments)
},{"./index.css":69,"dup":20,"phosphor-messaging":40,"phosphor-properties":67,"phosphor-signaling":68,"phosphor-widget":72}],71:[function(require,module,exports){
var css = ".p-Widget{box-sizing:border-box;-webkit-user-select:none;-moz-user-select:none;-ms-user-select:none;user-select:none;overflow:hidden;cursor:default}.p-Widget.p-mod-hidden{display:none}"; (require("browserify-css").createStyle(css, { "href": "node_modules/phosphor-widget/lib/index.css"})); module.exports = css;
},{"browserify-css":2}],72:[function(require,module,exports){

'use strict';
var __extends = (this && this.__extends) || function (d, b) {
	for (var p in b) if (b.hasOwnProperty(p)) d[p] = b[p];
	function __() { this.constructor = d; }
	d.prototype = b === null ? Object.create(b) : (__.prototype = b.prototype, new __());
};
var arrays = require('phosphor-arrays');
var phosphor_domutil_1 = require('phosphor-domutil');
var phosphor_messaging_1 = require('phosphor-messaging');
var phosphor_nodewrapper_1 = require('phosphor-nodewrapper');
var phosphor_properties_1 = require('phosphor-properties');
var phosphor_signaling_1 = require('phosphor-signaling');
require('./index.css');

exports.WIDGET_CLASS = 'p-Widget';

exports.HIDDEN_CLASS = 'p-mod-hidden';

exports.MSG_UPDATE_REQUEST = new phosphor_messaging_1.Message('update-request');

exports.MSG_LAYOUT_REQUEST = new phosphor_messaging_1.Message('layout-request');

exports.MSG_CLOSE_REQUEST = new phosphor_messaging_1.Message('close-request');

exports.MSG_AFTER_SHOW = new phosphor_messaging_1.Message('after-show');

exports.MSG_BEFORE_HIDE = new phosphor_messaging_1.Message('before-hide');

exports.MSG_AFTER_ATTACH = new phosphor_messaging_1.Message('after-attach');

exports.MSG_BEFORE_DETACH = new phosphor_messaging_1.Message('before-detach');

var Widget = (function (_super) {
	__extends(Widget, _super);

	function Widget() {
		_super.call(this);
		this._flags = 0;
		this._parent = null;
		this._children = [];
		this._box = null;
		this._rect = null;
		this._limits = null;
		this.addClass(exports.WIDGET_CLASS);
	}

	Widget.prototype.dispose = function () {
		if (this.isDisposed) {
			return;
		}
		this._flags |= WidgetFlag.IsDisposed;
		this.disposed.emit(void 0);
		if (this._parent) {
			this._parent.removeChild(this);
		}
		else if (this.isAttached) {
			detachWidget(this);
		}
		while (this._children.length > 0) {
			var child = this._children.pop();
			child._parent = null;
			child.dispose();
		}
		phosphor_signaling_1.clearSignalData(this);
		phosphor_messaging_1.clearMessageData(this);
		phosphor_properties_1.clearPropertyData(this);
	};
	Object.defineProperty(Widget.prototype, "disposed", {

		get: function () {
			return Widget.disposedSignal.bind(this);
		},
		enumerable: true,
		configurable: true
	});
	Object.defineProperty(Widget.prototype, "isAttached", {

		get: function () {
			return (this._flags & WidgetFlag.IsAttached) !== 0;
		},
		enumerable: true,
		configurable: true
	});
	Object.defineProperty(Widget.prototype, "isDisposed", {

		get: function () {
			return (this._flags & WidgetFlag.IsDisposed) !== 0;
		},
		enumerable: true,
		configurable: true
	});
	Object.defineProperty(Widget.prototype, "isVisible", {

		get: function () {
			return (this._flags & WidgetFlag.IsVisible) !== 0;
		},
		enumerable: true,
		configurable: true
	});
	Object.defineProperty(Widget.prototype, "hidden", {

		get: function () {
			return Widget.hiddenProperty.get(this);
		},

		set: function (value) {
			Widget.hiddenProperty.set(this, value);
		},
		enumerable: true,
		configurable: true
	});
	Object.defineProperty(Widget.prototype, "boxSizing", {

		get: function () {
			if (this._box)
				return this._box;
			return this._box = Object.freeze(phosphor_domutil_1.boxSizing(this.node));
		},
		enumerable: true,
		configurable: true
	});
	Object.defineProperty(Widget.prototype, "sizeLimits", {

		get: function () {
			if (this._limits)
				return this._limits;
			return this._limits = Object.freeze(phosphor_domutil_1.sizeLimits(this.node));
		},
		enumerable: true,
		configurable: true
	});
	Object.defineProperty(Widget.prototype, "offsetRect", {

		get: function () {
			if (this._rect)
				return cloneOffsetRect(this._rect);
			return getOffsetRect(this.node);
		},
		enumerable: true,
		configurable: true
	});
	Object.defineProperty(Widget.prototype, "parent", {

		get: function () {
			return this._parent;
		},

		set: function (parent) {
			if (parent && parent !== this._parent) {
				parent.addChild(this);
			}
			else if (!parent && this._parent) {
				this._parent.removeChild(this);
			}
		},
		enumerable: true,
		configurable: true
	});
	Object.defineProperty(Widget.prototype, "children", {

		get: function () {
			return this._children.slice();
		},

		set: function (children) {
			var _this = this;
			this.clearChildren();
			children.forEach(function (child) { return _this.addChild(child); });
		},
		enumerable: true,
		configurable: true
	});
	Object.defineProperty(Widget.prototype, "childCount", {

		get: function () {
			return this._children.length;
		},
		enumerable: true,
		configurable: true
	});

	Widget.prototype.childAt = function (index) {
		return this._children[index | 0];
	};

	Widget.prototype.childIndex = function (child) {
		return this._children.indexOf(child);
	};

	Widget.prototype.addChild = function (child) {
		return this.insertChild(this._children.length, child);
	};

	Widget.prototype.insertChild = function (index, child) {
		if (child === this) {
			throw new Error('invalid child widget');
		}
		if (child._parent) {
			child._parent.removeChild(child);
		}
		else if (child.isAttached) {
			detachWidget(child);
		}
		child._parent = this;
		var i = arrays.insert(this._children, index, child);
		phosphor_messaging_1.sendMessage(this, new ChildMessage('child-added', child, -1, i));
		return i;
	};

	Widget.prototype.moveChild = function (fromIndex, toIndex) {
		var i = fromIndex | 0;
		var j = toIndex | 0;
		if (!arrays.move(this._children, i, j)) {
			return false;
		}
		if (i !== j) {
			var child = this._children[j];
			phosphor_messaging_1.sendMessage(this, new ChildMessage('child-moved', child, i, j));
		}
		return true;
	};

	Widget.prototype.removeChildAt = function (index) {
		var i = index | 0;
		var child = arrays.removeAt(this._children, i);
		if (child) {
			child._parent = null;
			phosphor_messaging_1.sendMessage(this, new ChildMessage('child-removed', child, i, -1));
		}
		return child;
	};

	Widget.prototype.removeChild = function (child) {
		var i = this.childIndex(child);
		if (i !== -1)
			this.removeChildAt(i);
		return i;
	};

	Widget.prototype.clearChildren = function () {
		while (this.childCount > 0) {
			this.removeChildAt(this.childCount - 1);
		}
	};

	Widget.prototype.update = function (immediate) {
		if (immediate === void 0) { immediate = false; }
		if (immediate) {
			phosphor_messaging_1.sendMessage(this, exports.MSG_UPDATE_REQUEST);
		}
		else {
			phosphor_messaging_1.postMessage(this, exports.MSG_UPDATE_REQUEST);
		}
	};

	Widget.prototype.close = function (immediate) {
		if (immediate === void 0) { immediate = false; }
		if (immediate) {
			phosphor_messaging_1.sendMessage(this, exports.MSG_CLOSE_REQUEST);
		}
		else {
			phosphor_messaging_1.postMessage(this, exports.MSG_CLOSE_REQUEST);
		}
	};

	Widget.prototype.clearBoxSizing = function () {
		this._box = null;
	};

	Widget.prototype.setSizeLimits = function (minWidth, minHeight, maxWidth, maxHeight) {
		var minW = Math.max(0, minWidth);
		var minH = Math.max(0, minHeight);
		var maxW = Math.max(0, maxWidth);
		var maxH = Math.max(0, maxHeight);
		this._limits = Object.freeze({
			minWidth: minW,
			minHeight: minH,
			maxWidth: maxW,
			maxHeight: maxH,
		});
		var style = this.node.style;
		style.minWidth = minW + 'px';
		style.minHeight = minH + 'px';
		style.maxWidth = (maxW === Infinity) ? '' : maxW + 'px';
		style.maxHeight = (maxH === Infinity) ? '' : maxH + 'px';
	};

	Widget.prototype.clearSizeLimits = function () {
		this._limits = null;
		var style = this.node.style;
		style.minWidth = '';
		style.maxWidth = '';
		style.minHeight = '';
		style.maxHeight = '';
	};

	Widget.prototype.setOffsetGeometry = function (left, top, width, height) {
		var rect = this._rect || (this._rect = makeOffsetRect());
		var style = this.node.style;
		var resized = false;
		if (top !== rect.top) {
			rect.top = top;
			style.top = top + 'px';
		}
		if (left !== rect.left) {
			rect.left = left;
			style.left = left + 'px';
		}
		if (width !== rect.width) {
			resized = true;
			rect.width = width;
			style.width = width + 'px';
		}
		if (height !== rect.height) {
			resized = true;
			rect.height = height;
			style.height = height + 'px';
		}
		if (resized)
			phosphor_messaging_1.sendMessage(this, new ResizeMessage(width, height));
	};

	Widget.prototype.clearOffsetGeometry = function () {
		if (!this._rect) {
			return;
		}
		this._rect = null;
		var style = this.node.style;
		style.top = '';
		style.left = '';
		style.width = '';
		style.height = '';
	};

	Widget.prototype.processMessage = function (msg) {
		switch (msg.type) {
			case 'resize':
				this.onResize(msg);
				break;
			case 'update-request':
				this.onUpdateRequest(msg);
				break;
			case 'layout-request':
				this.onLayoutRequest(msg);
				break;
			case 'child-added':
				this.onChildAdded(msg);
				break;
			case 'child-removed':
				this.onChildRemoved(msg);
				break;
			case 'child-moved':
				this.onChildMoved(msg);
				break;
			case 'after-show':
				this._flags |= WidgetFlag.IsVisible;
				this.onAfterShow(msg);
				sendToShown(this._children, msg);
				break;
			case 'before-hide':
				this.onBeforeHide(msg);
				sendToShown(this._children, msg);
				this._flags &= ~WidgetFlag.IsVisible;
				break;
			case 'after-attach':
				var visible = !this.hidden && (!this._parent || this._parent.isVisible);
				if (visible)
					this._flags |= WidgetFlag.IsVisible;
				this._flags |= WidgetFlag.IsAttached;
				this.onAfterAttach(msg);
				sendToAll(this._children, msg);
				break;
			case 'before-detach':
				this.onBeforeDetach(msg);
				sendToAll(this._children, msg);
				this._flags &= ~WidgetFlag.IsVisible;
				this._flags &= ~WidgetFlag.IsAttached;
				break;
			case 'child-shown':
				this.onChildShown(msg);
				break;
			case 'child-hidden':
				this.onChildHidden(msg);
				break;
			case 'close-request':
				this.onCloseRequest(msg);
				break;
		}
	};

	Widget.prototype.compressMessage = function (msg, pending) {
		switch (msg.type) {
			case 'update-request':
			case 'layout-request':
			case 'close-request':
				return pending.some(function (other) { return other.type === msg.type; });
		}
		return false;
	};

	Widget.prototype.onChildAdded = function (msg) {
		var next = this.childAt(msg.currentIndex + 1);
		this.node.insertBefore(msg.child.node, next && next.node);
		if (this.isAttached)
			phosphor_messaging_1.sendMessage(msg.child, exports.MSG_AFTER_ATTACH);
	};

	Widget.prototype.onChildRemoved = function (msg) {
		if (this.isAttached)
			phosphor_messaging_1.sendMessage(msg.child, exports.MSG_BEFORE_DETACH);
		this.node.removeChild(msg.child.node);
	};

	Widget.prototype.onChildMoved = function (msg) {
		if (this.isAttached)
			phosphor_messaging_1.sendMessage(msg.child, exports.MSG_BEFORE_DETACH);
		var next = this.childAt(msg.currentIndex + 1);
		this.node.insertBefore(msg.child.node, next && next.node);
		if (this.isAttached)
			phosphor_messaging_1.sendMessage(msg.child, exports.MSG_AFTER_ATTACH);
	};

	Widget.prototype.onResize = function (msg) {
		sendToAll(this._children, ResizeMessage.UnknownSize);
	};

	Widget.prototype.onUpdateRequest = function (msg) {
		sendToAll(this._children, ResizeMessage.UnknownSize);
	};

	Widget.prototype.onCloseRequest = function (msg) {
		if (this._parent) {
			this._parent.removeChild(this);
		}
		else if (this.isAttached) {
			detachWidget(this);
		}
	};

	Widget.prototype.onLayoutRequest = function (msg) { };

	Widget.prototype.onAfterShow = function (msg) { };

	Widget.prototype.onBeforeHide = function (msg) { };

	Widget.prototype.onAfterAttach = function (msg) { };

	Widget.prototype.onBeforeDetach = function (msg) { };

	Widget.prototype.onChildShown = function (msg) { };

	Widget.prototype.onChildHidden = function (msg) { };

	Widget.disposedSignal = new phosphor_signaling_1.Signal();

	Widget.hiddenProperty = new phosphor_properties_1.Property({
		value: false,
		changed: onHiddenChanged,
	});
	return Widget;
})(phosphor_nodewrapper_1.NodeWrapper);
exports.Widget = Widget;

function attachWidget(widget, host) {
	if (widget.parent) {
		throw new Error('only a root widget can be attached to the DOM');
	}
	if (widget.isAttached || document.body.contains(widget.node)) {
		throw new Error('widget is already attached to the DOM');
	}
	if (!document.body.contains(host)) {
		throw new Error('host is not attached to the DOM');
	}
	host.appendChild(widget.node);
	phosphor_messaging_1.sendMessage(widget, exports.MSG_AFTER_ATTACH);
}
exports.attachWidget = attachWidget;

function detachWidget(widget) {
	if (widget.parent) {
		throw new Error('only a root widget can be detached from the DOM');
	}
	if (!widget.isAttached || !document.body.contains(widget.node)) {
		throw new Error('widget is not attached to the DOM');
	}
	phosphor_messaging_1.sendMessage(widget, exports.MSG_BEFORE_DETACH);
	widget.node.parentNode.removeChild(widget.node);
}
exports.detachWidget = detachWidget;

var ChildMessage = (function (_super) {
	__extends(ChildMessage, _super);

	function ChildMessage(type, child, previousIndex, currentIndex) {
		if (previousIndex === void 0) { previousIndex = -1; }
		if (currentIndex === void 0) { currentIndex = -1; }
		_super.call(this, type);
		this._child = child;
		this._currentIndex = currentIndex;
		this._previousIndex = previousIndex;
	}
	Object.defineProperty(ChildMessage.prototype, "child", {

		get: function () {
			return this._child;
		},
		enumerable: true,
		configurable: true
	});
	Object.defineProperty(ChildMessage.prototype, "currentIndex", {

		get: function () {
			return this._currentIndex;
		},
		enumerable: true,
		configurable: true
	});
	Object.defineProperty(ChildMessage.prototype, "previousIndex", {

		get: function () {
			return this._previousIndex;
		},
		enumerable: true,
		configurable: true
	});
	return ChildMessage;
})(phosphor_messaging_1.Message);
exports.ChildMessage = ChildMessage;

var ResizeMessage = (function (_super) {
	__extends(ResizeMessage, _super);

	function ResizeMessage(width, height) {
		_super.call(this, 'resize');
		this._width = width;
		this._height = height;
	}
	Object.defineProperty(ResizeMessage.prototype, "width", {

		get: function () {
			return this._width;
		},
		enumerable: true,
		configurable: true
	});
	Object.defineProperty(ResizeMessage.prototype, "height", {

		get: function () {
			return this._height;
		},
		enumerable: true,
		configurable: true
	});

	ResizeMessage.UnknownSize = new ResizeMessage(-1, -1);
	return ResizeMessage;
})(phosphor_messaging_1.Message);
exports.ResizeMessage = ResizeMessage;

var WidgetFlag;
(function (WidgetFlag) {

	WidgetFlag[WidgetFlag["IsAttached"] = 1] = "IsAttached";

	WidgetFlag[WidgetFlag["IsVisible"] = 2] = "IsVisible";

	WidgetFlag[WidgetFlag["IsDisposed"] = 4] = "IsDisposed";
})(WidgetFlag || (WidgetFlag = {}));

function makeOffsetRect() {
	return { top: NaN, left: NaN, width: NaN, height: NaN };
}

function cloneOffsetRect(rect) {
	return {
		top: rect.top,
		left: rect.left,
		width: rect.width,
		height: rect.height
	};
}

function getOffsetRect(node) {
	return {
		top: node.offsetTop,
		left: node.offsetLeft,
		width: node.offsetWidth,
		height: node.offsetHeight,
	};
}

function onHiddenChanged(owner, old, hidden) {
	if (hidden) {
		if (owner.isAttached && (!owner.parent || owner.parent.isVisible)) {
			phosphor_messaging_1.sendMessage(owner, exports.MSG_BEFORE_HIDE);
		}
		owner.addClass(exports.HIDDEN_CLASS);
		if (owner.parent) {
			phosphor_messaging_1.sendMessage(owner.parent, new ChildMessage('child-hidden', owner));
		}
	}
	else {
		owner.removeClass(exports.HIDDEN_CLASS);
		if (owner.isAttached && (!owner.parent || owner.parent.isVisible)) {
			phosphor_messaging_1.sendMessage(owner, exports.MSG_AFTER_SHOW);
		}
		if (owner.parent) {
			phosphor_messaging_1.sendMessage(owner.parent, new ChildMessage('child-shown', owner));
		}
	}
}

function sendToAll(array, msg) {
	for (var i = 0; i < array.length; ++i) {
		phosphor_messaging_1.sendMessage(array[i], msg);
	}
}

function sendToShown(array, msg) {
	for (var i = 0; i < array.length; ++i) {
		if (!array[i].hidden)
			phosphor_messaging_1.sendMessage(array[i], msg);
	}
}
},{"./index.css":71,"phosphor-arrays":73,"phosphor-domutil":76,"phosphor-messaging":40,"phosphor-nodewrapper":77,"phosphor-properties":78,"phosphor-signaling":79}],73:[function(require,module,exports){
arguments[4][6][0].apply(exports,arguments)
},{"dup":6}],74:[function(require,module,exports){
arguments[4][10][0].apply(exports,arguments)
},{"dup":10}],75:[function(require,module,exports){
var css = "body.p-mod-override-cursor *{cursor:inherit!important}"; (require("browserify-css").createStyle(css, { "href": "node_modules/phosphor-widget/node_modules/phosphor-domutil/lib/index.css"})); module.exports = css;
},{"browserify-css":2}],76:[function(require,module,exports){
arguments[4][16][0].apply(exports,arguments)
},{"./index.css":75,"dup":16,"phosphor-disposable":74}],77:[function(require,module,exports){
arguments[4][42][0].apply(exports,arguments)
},{"dup":42}],78:[function(require,module,exports){
arguments[4][8][0].apply(exports,arguments)
},{"dup":8,"phosphor-signaling":79}],79:[function(require,module,exports){
arguments[4][9][0].apply(exports,arguments)
},{"dup":9}]},{},[1]);