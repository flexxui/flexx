/* JavaScript implementation of the Binary Structured Data Format (BSDF)
 *
 * BSDF is a binary format for serializing structured (scientific) data.
 * See http://bsdf.io for more information.
 *
 * var bsdf = require('bsdf.js');
 * bsdf.encode(data) -> ArrayBuffer
 * bsdf.decode(bytes) -> data (bytes can be ArrayBuffer, DataView or Uint8Array)
 *
 * The data is any data structure supported by BSDF and available extensions.
 * ArrayBuffer and DataView are consumed as bytes, and Uint8Array as a typed array.
 * Bytes are decoded as DataView objects, which can be mapped to arrays with e.g.
 * `a = new Uint8Array(bytes.buffer, bytes.byteOffset, bytes.byteLength)`, if needed
 * make a copy with `a = new Uint8Array(a)`.
 *
 * This code is distributed under the terms of the 2-clause BSD license.
 * Copyright (C) 2017 Almar Klein
 */

/* Developer notes:
 *
 * To represent bytes we need to chose between Uint8Array, DataView and ArrayBuffer.
 * The ArrayBuffer most closely resembles abstract byte blobs, but it cannot be a view.
 * The Uint8Array can be a view, but it can represent an array of numbers.
 * The DataView provides an abstract view on a buffer, so it seems to give us both.
 *
 * - The encoder accepts either of these three (and also Nodejs Buffer objects).
 * - The decoder returns ArrayBuffer.
 * - The encoder consumes DataView and ArrayBuffer as bytes.
 * - The decoder produces DataView objects for bytes, allowing mapping to typed arrays
 *   without copying.
 *
 */

(function (root, factory) {
    if (typeof define === 'function' && define.amd) {
        // AMD. Register as an anonymous module.
        define("bsdf", [], factory);
    } else if (typeof exports !== 'undefined') {
        // Node or CommonJS
        module.exports = factory();
        if (typeof window === 'undefined') {
            root.bsdf = module.exports;  // also create global module in Node
        }
    } else {
        // Browser globals (root is window)
        root.bsdf = factory();
    }
}(this, function () {
/* above is the UMD module prefix */

"use strict";

var VERSION;
VERSION = [2, 2, 2];

// http://github.com/msgpack/msgpack-javascript/blob/master/msgpack.js#L181-L192
function utf8encode(mix) {
    // Mix is assumed to be a string. returns an Array of ints.
    var iz = mix.length;
    var rv = [];
    for (var i = 0; i < iz; ++i) {
        var c = mix.charCodeAt(i);
        if (c < 0x80) { // ASCII(0x00 ~ 0x7f)
            rv.push(c & 0x7f);
        } else if (c < 0x0800) {
            rv.push(((c >>>  6) & 0x1f) | 0xc0, (c & 0x3f) | 0x80);
        } else if (c < 0x10000) {
            rv.push(((c >>> 12) & 0x0f) | 0xe0,
                    ((c >>>  6) & 0x3f) | 0x80, (c & 0x3f) | 0x80);
        }
    }
    return rv;
}

// http://github.com/msgpack/msgpack-javascript/blob/master/msgpack.js#L365-L375
function utf8decode(buf) {
    // The buf is assumed to be an Array or Uint8Array. Returns a string.
    var iz = buf.length - 1;
    var ary = [];
    for (var i = -1; i < iz; ) {
        var c = buf[++i]; // lead byte
        ary.push(c < 0x80 ? c : // ASCII(0x00 ~ 0x7f)
                 c < 0xe0 ? ((c & 0x1f) <<  6 | (buf[++i] & 0x3f)) :
                            ((c & 0x0f) << 12 | (buf[++i] & 0x3f) << 6
                                              | (buf[++i] & 0x3f)));
    }
    // First line can cause Maximum call stack size exceeded"
    // return String.fromCharCode.apply(null, ary);
    return ary.map(function(i) {return String.fromCharCode(i)}).join("");
}


// ================== API

function bsdf_encode(d, extensions) {
    var s = new BsdfSerializer(extensions);
    return s.encode(d);
}

function bsdf_decode(buf, extensions) {
    var s = new BsdfSerializer(extensions);
    return s.decode(buf);
}

function BsdfSerializer(extensions) {
    /* A placeholder for a BSDF serializer with associated extensions.
     * Other formats also use it to associate options, but we don't have any.
     */
    this.extensions = [];
    if (extensions === undefined) { extensions = standard_extensions; }
    if (!Array.isArray(extensions)) { throw new TypeError("Extensions must be an array."); }
    for (var i=0; i<extensions.length; i++) {
        this.add_extension(extensions[i]);
    }
}

BsdfSerializer.prototype.add_extension = function (e) {
    // We use an array also as a dict for quick lookup
    if (this.extensions[e.name] !== undefined) {
        // Overwrite existing
        for (var i=0; i<this.extensions.length; i++) {
            if (this.extensions[i].name == e.name) { this.extensions[i] = e; break; }
        }
    } else {
        // Append
        this.extensions.push(e);
        this.extensions[e.name] = e;
    }
};

BsdfSerializer.prototype.remove_extension = function (e) {
    delete this.extensions[e.name];
    for (var i=0; i<this.extensions.length; i++) {
        if (this.extensions[i].name == name) { this.extensions.splice(i, 1); break; }
    }
};

BsdfSerializer.prototype.encode = function (d) {
    // Write head and version
    var f = ByteBuilder();
    f.push_char('B'); f.push_char('S'); f.push_char('D'); f.push_char('F');
    f.push_uint8(VERSION[0]); f.push_uint8(VERSION[1]);
    // Encode and return result
    this.encode_object(f, d);
    return f.get_result();
};

BsdfSerializer.prototype.decode = function (buf, extensions) {
    // Read and check head
    var f = BytesReader(buf);
    var head = f.get_char() + f.get_char() + f.get_char() + f.get_char();
    if (head != 'BSDF') {
        throw new Error("This does not look like BSDF encoded data: " + head);
    }
    // Read and check version
    var major_version = f.get_uint8();
    var minor_version = f.get_uint8();
    if (major_version != VERSION[0]) {
        throw new Error('Reading file with different major version ' + major_version + ' from the implementation ' + VERSION[0]);
    } else if (minor_version > VERSION[1]){
        console.warn('BSDF warning: reading file with higher minor version ' + minor_version + ' than the implementation ' + VERSION[1]);
    }
    // Decode
    return this.decode_object(f);
};


//---- encoder

function ByteBuilder() {
    // We use an arraybuffer for efficiency, but we don't know its final size.
    // Therefore we create a new one with increasing size when needed.
    var buffers = [];
    var min_buf_size = 1024;

    var buf8 = new Uint8Array(min_buf_size);
    var bufdv = new DataView(buf8.buffer);

    var pos = 0;
    var pos_offset = 0;
    var pos_max = buf8.byteLength;  // max valid value of pos

    // Create text encoder / decoder
    var text_encode, text_decode;
    if (typeof TextEncoder !== 'undefined') {
        var x = new TextEncoder('utf-8');
        text_encode = x.encode.bind(x);
    } else {
        // test this
        text_encode = utf8encode;
    }

    function get_result() {
        // Combine all sub buffers into one contiguous buffer
        var total = new Uint8Array(pos_offset + pos);
        var i = 0, j;
        for (var index=0; index<buffers.length; index+=2) {
            var sub = buffers[index];
            var n = buffers[index + 1];
            var offset = i;
            for(j=0; j<n; j++, i++){ total[i] = sub[j]; }
        }
        for(j=0; j<pos; j++, i++){ total[i] = buf8[j]; }  // also current buffer
        return total.buffer; // total is an exact fit on its buffer
    }
    function new_buffer(n) {
        // Establish size
        var new_size = Math.max(n + 64 , min_buf_size);
        // Store current buffer
        buffers.push(buf8);
        buffers.push(pos);
        // Create new
        buf8 = new Uint8Array(new_size);
        bufdv = new DataView(buf8.buffer);
        // Set positions
        pos_offset += pos;
        pos_max = buf8.byteLength;
        pos = 0;
    }
    function tell() {
        return pos_offset + pos;
    }
    function push_bytes(s) {  // we use Uint8Array internally for this
        var n = s.byteLength;
        if (pos + n > pos_max) { new_buffer(n); }
        for (var i=0; i<n; i++) { buf8[pos+i] = s[i]; }
        pos += n;
    }
    function push_char(s) {
        if (pos + 1 > pos_max) { new_buffer(1); }
        buf8[pos] = s.charCodeAt();
        pos += 1;
    }
    function push_str(s) {
        var bb = text_encode(s);
        push_size(bb.length);
        if (pos + bb.length > pos_max) { new_buffer(bb.length); }
        for (var i=0; i<bb.length; i++) { buf8[pos + i] = bb[i]; }
        pos += bb.length;
    }
    function push_size(s, big) {
        if (s <= 250 && typeof big == 'undefined') {
            if (pos + 1 > pos_max) { new_buffer(1); }
            buf8[pos] = s;
            pos += 1;
        } else {
            if (pos + 9 > pos_max) { new_buffer(9); }
            buf8[pos] = 253;
            bufdv.setUint32(pos+1, (s % 4294967296), true); // uint64
            bufdv.setUint32(pos+5, (s / 4294967296) & 4294967295, true);
            pos += 9;
        }
    }
    function push_uint8(s) {
        if (pos + 1 > pos_max) { new_buffer(1); }
        buf8[pos] = s;
        pos += 1;
    }
    function push_int16(s) {
        if (pos + 2 > pos_max) { new_buffer(2); }
        bufdv.setInt16(pos, s, true);
        pos += 2;
    }
    function push_int64(s) {
        if (pos + 8 > pos_max) { new_buffer(8); }
        var j, a;
        if (s < 0) { // perform two's complement encoding
            for (j=0, a=s+1; j<8; j++, a/=256) { buf8[pos+j] = ((-(a % 256 )) & 255) ^ 255; }
        } else {
            for (j=0, a=s; j<8; j++, a/=256) { buf8[pos+j] = ((a % 256 ) & 255); }
        }
        pos += 8;
    }
    function push_float64(s) {
        // todo: we could push 32bit floats via "f"
        if (pos + 8 > pos_max) { new_buffer(8); }
        bufdv.setFloat64(pos, s, true);
        pos += 8;
    }
    return {get_result: get_result, tell: tell, push_bytes: push_bytes,
            push_char: push_char, push_str: push_str, push_size: push_size,
            push_uint8: push_uint8, push_int16: push_int16, push_int64: push_int64,
            push_float64: push_float64};
}

function encode_type_id(f, c, extension_id) {
    if (typeof extension_id == 'undefined') {
        f.push_char(c);
    } else {
        f.push_char(c.toUpperCase());
        f.push_str(extension_id);
    }
}

BsdfSerializer.prototype.encode_object = function (f, value, extension_id) {
    var iext, ext;

    // We prefer to fail on undefined, instead of silently converting to null like JSON
    // if (typeof value == 'undefined') { encode_type_id(f, 'v', extension_id); }
    if (typeof value == 'undefined') { throw new TypeError("BSDF cannot encode undefined, use null instead."); }
    else if (value === null) { encode_type_id(f, 'v', extension_id); }
    else if (value === false) { encode_type_id(f, 'n', extension_id); }
    else if (value === true) { encode_type_id(f, 'y', extension_id); }
    else if (typeof value == 'number') {
        if ((value ^ 0) == value) { // no Number.isInteger on IE
            if (value >= -32768 && value <= 32767) {
                encode_type_id(f, 'h', extension_id);
                f.push_int16(value);
            } else {
                encode_type_id(f, 'i', extension_id);
                f.push_int64(value);
            }
        } else {
            encode_type_id(f, 'd', extension_id);
            f.push_float64(value);
        }
    } else if (typeof value == 'string') {
        encode_type_id(f, 's', extension_id);
        f.push_str(value);
    } else if (typeof value == 'object') {
        if (Array.isArray(value)) {  // heterogeneous list
            encode_type_id(f, 'l', extension_id);
            var n = value.length;
            f.push_size(n);
            for (var i=0; i<n; i++) {
                this.encode_object(f, value[i]);
            }
        } else if (value.constructor === Object) {  // mapping / dict
            encode_type_id(f, 'm', extension_id);
            var nm = Object.keys(value).length;
            f.push_size(nm);
            for (var key in value) {
                f.push_str(key);
                this.encode_object(f, value[key]);
            }
        } else if (value instanceof ArrayBuffer || value instanceof DataView) {  // bytes
            if (value instanceof ArrayBuffer) { value = new DataView(value); }
            encode_type_id(f, 'b', extension_id);
            var compression = 0;
            var compressed = new Uint8Array(value.buffer, value.byteOffset, value.byteLength);  // map to uint8
            var data_size = value.byteLength;
            var used_size = data_size;
            var extra_size = 0;
            var allocated_size = used_size + extra_size;
            // Write sizes - write at least in a size that allows resizing
            if (allocated_size > 250) {  // && compression == 0
                f.push_size(allocated_size, true);
                f.push_size(used_size, true);
                f.push_size(data_size, true);
            } else {
                f.push_size(allocated_size);
                f.push_size(used_size);
                f.push_size(data_size);
            }
            // Compression and checksum
            f.push_uint8(0);
            f.push_uint8(0);  // no checksum
            // Byte alignment
            if (compression == 0) {
                var alignment = 8 - (f.tell() + 1) % 8;  // +1 for the byte to write
                f.push_uint8(alignment);
                for (var j=0; j<alignment; j++) { f.push_uint8(0); }
            } else {
                f.push_uint8(0);  // zero alignment
            }
            // The actual data and extra space
            f.push_bytes(compressed);
            f.push_bytes(new Uint8Array(allocated_size - used_size));
        } else {
            // Try extensions (for objects)
            for (iext=0; iext<this.extensions.length; iext++) {
                ext = this.extensions[iext];
                if (ext.match(this, value)) {
                    this.encode_object(f, ext.encode(this, value), ext.name);
                    return;
                }
            }
            var cls = Object.getPrototypeOf(value);
            var cname = cls.__name__ || cls.constructor.name;  // __name__ is a PyScript thing
            throw new TypeError("cannot encode object of type " + cname);
        }
    } else {
        if (typeof extension_id != 'undefined') {
            throw new Error('Extension ' + extension_id + ' wronfully encodes object to another ' +
                        'extension object (though it may encode to a list/dict ' +
                        'that contains other extension objects).');
        }
        // Try extensions (for other types)
        for (iext=0; iext<this.extensions.length; iext++) {
            ext = this.extensions[iext];
            if (ext.match(this, value)) {
                this.encode_object(f, ext.encode(this, value), ext.name);
                return;
            }
        }
        throw new Error("cannot encode type " + typeof(value));
    }
};

//---- decoder

function BytesReader(buf) {

    // Buffer can be ArrayBuffer, DataView or Uint8Array, or Nodejs Buffer, we map to DataView
    var bufdv;

    if (typeof buf.byteLength == 'undefined') {
        throw new Error("BSDF decorer needs something that looks like bytes");
    }
    if (typeof buf.byteOffset == 'undefined') {
        bufdv = new DataView(buf);  // buf was probably an ArrayBuffer
    } else {
        bufdv = new DataView(buf.buffer, buf.byteOffset, buf.byteLength);  // remap to something we know
    }

    var startpos = bufdv.byteOffset;
    var pos = 0;
    var buf8 = new Uint8Array(bufdv.buffer, bufdv.byteOffset, bufdv.byteLength);

    // Create text encoder / decoder
    var text_encode, text_decode;
    if (typeof TextDecoder !== 'undefined') {
        var x = new TextDecoder('utf-8');
        text_decode = x.decode.bind(x);
    } else {
        // test this
        text_decode = utf8decode;
    }

    function tell() {
        return pos;
    }
    function get_char() {
        return String.fromCharCode(buf8[pos++]);
    }
    function get_size() {
        var s = buf8[pos++];
        if (s >= 253) {
            if (s == 253) {
                s = bufdv.getUint32(pos, true) + bufdv.getUint32(pos+4, true) * 4294967296;
            } else if (s == 254) { // closed stream
                s = bufdv.getUint32(pos, true) + bufdv.getUint32(pos+4, true) * 4294967296;
            } else if (s == 255) {  // unclosed stream
                s = -1;
            } else {
                throw new Error("Invalid size");
            }
            pos += 8;
        }
        return s;
    }
    function get_bytes(n) {  // we use Uint8Array internally for this
        var s = new Uint8Array(buf8.buffer, buf8.byteOffset + pos, n);
        pos += n;
        return s;
    }
    function get_str() {
        var n = get_size();
        var bb = new Uint8Array(buf8.buffer, buf8.byteOffset + pos, n);
        pos += n;
        return text_decode(bb);
    }
    function get_uint8() {
        return buf8[pos++];
    }
    function get_int16() {
        var s = bufdv.getInt16(pos, true);
        pos += 2;
        return s;
    }
    function get_int64() {
        var isneg = (buf8[pos+7] & 0x80) > 0;
        var s, j, m;
        if (isneg) {
            s = -1;
            for (j=0, m=1; j<8; j++, m*=256) { s -= (buf8[pos+j] ^ 0xff) * m; }
        } else {
            s = 0;
            for (j=0, m=1; j<8; j++, m*=256) { s += buf8[pos+j] * m; }
        }
        pos += 8;
        return s;
    }
    function get_float32() {
        var s = bufdv.getFloat32(pos, true);
        pos += 4;
        return s;
    } function get_float64() {
        var s = bufdv.getFloat64(pos, true);
        pos += 8;
        return s;
    }

    return {tell: tell, get_size:get_size, get_bytes: get_bytes,
            get_uint8: get_uint8, get_int16: get_int16, get_int64: get_int64,
            get_float32: get_float32, get_float64: get_float64, get_char: get_char, get_str: get_str};

}

BsdfSerializer.prototype.decode_object = function (f) {

    var char = f.get_char();
    var c = char.toLowerCase();
    var value;
    var extension_id = null;

    if (char == '\x00') {  // because String.fromCharCode(undefined) produces ASCII 0.
        throw new EOFError('End of BSDF data reached.');
    }

    // Conversion (uppercase value identifiers signify converted values)
    if (char != c) {
        extension_id = f.get_str();
    }

    if (c == 'v') {
        value = null;
    } else if (c == 'n') {
        value = false;
    } else if (c == 'y') {
        value = true;
    } else if (c == 'h') {
        value = f.get_int16();
    } else if (c == 'i') {
        value = f.get_int64();
    } else if (c == 'f') {
        value = f.get_float32();
    } else if (c == 'd') {
        value = f.get_float64();
    } else if (c == 's') {
        value = f.get_str();
    } else if (c == 'l') {
        var n = f.get_size();
        if (n < 0) {
            // Streaming
            value = [];
            try {
                while (true) { value.push(this.decode_object(f)); }
            } catch(err) {
                if (err instanceof EOFError) { /* ok */ } else { throw err; }
            }
        } else {
            // Normal
            value = new Array(n);
            for (var i=0; i<n; i++) {
                value[i] = this.decode_object(f);
            }
        }
    } else if (c == 'm') {
        var nm = f.get_size();
        value = {};
        for (var j=0; j<nm; j++) {
            var key = f.get_str();
            value[key] = this.decode_object(f);
        }
    } else if (c == 'b') {
        // Get sizes
        var allocated_size = f.get_size();
        var used_size = f.get_size();
        var data_size = f.get_size();
        // Compression and checksum
        var compression = f.get_uint8();
        var has_checksum = f.get_uint8();
        if (has_checksum) {
            var checksum = f.get_bytes(16);
        }
        // Skip alignment
        var alignment = f.get_uint8();
        f.get_bytes(alignment);
        // Get data (as ArrayBuffer)
        var compressed = f.get_bytes(used_size);  // uint8
        f.get_bytes(allocated_size - used_size);  // skip extra space
        if (compression == 0) {
            value = new DataView(compressed.buffer, compressed.byteOffset, compressed.byteLength);
        } else {
            throw new Error("JS implementation of BSDF does not support compression (" + compression + ')');
        }
    } else {
        throw new Error("Invalid value specifier at pos " + f.tell() + ": " + JSON.stringify(char));
    }

    // Convert using an extension?
    if (extension_id !== null) {
        var ext = this.extensions[extension_id];
        if (ext) {
            value = ext.decode(this, value);
        } else {
            console.warn('BSDF warning: no known extension for "' + extension_id + '", value passes in raw form.');
        }
    }
    return value;
};


// To be able to support complex numbers
function Complex(real, imag) {
    this.real = real;
    this.imag = imag;
}

function EOFError(msg) {
    this.name = 'EOF';
    this.message = msg;
}


// ================== Standard extensions

var rootns;
if (typeof window == 'undefined') { rootns = global; } else { rootns = window; }

var complex_extension = {
    name: 'c',
    match: function(s, v) { return v instanceof Complex; },
    encode: function(s, v) { return [v.real, v.imag]; },
    decode: function(s, v) { return new Complex(v[0], v[1]); }
};

var ndarray_extension = {
    name: 'ndarray',
    match: function(s, v) {
        return v.BYTES_PER_ELEMENT !== undefined && v.constructor.name.slice(-5) == 'Array';
    },
    encode: function(s, v) {
        return {shape: v.shape || [v.length],
                dtype: v.constructor.name.slice(0, -5).toLowerCase(),
                data: new DataView(v.buffer, v.byteOffset, v.byteLength)};
    },
    decode: function(s, v) {
        var cls = rootns[v.dtype[0].toUpperCase() + v.dtype.slice(1) + 'Array'];
        if (typeof cls == 'undefined') {
            throw new TypeError("Cannot create typed array with dtype: " + v.dtype);
        }
        var value = new cls(v.data.buffer, v.data.byteOffset, v.data.byteLength / cls.BYTES_PER_ELEMENT);
        value.shape = v.shape;
        return value;
    }
};

var standard_extensions = [complex_extension, ndarray_extension];

// ================== the UMD module suffix
return {encode: bsdf_encode, decode: bsdf_decode, BsdfSerializer: BsdfSerializer, standard_extensions: standard_extensions};
}));
