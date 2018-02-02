/* Efficient JavaScript implementation of Base64 encoding/decoding of bytes (Uint8Array).
 * This code is distributed under the terms of the 2-clause BSD license.
 * Copyright (C) 2018 Almar Klein
 */

(function (root, factory) {
    if (typeof define === 'function' && define.amd) {
        // AMD. Register as an anonymous module.
        define("bb64", [], factory);
    } else if (typeof exports !== 'undefined') {
        // Node or CommonJS
        module.exports = factory();
        if (typeof window === 'undefined') {
            root.bb64 = module.exports;  // also create global module in Node
        }
    } else {
        // Browser globals (root is window)
        root.bb64 = factory();
    }
}(this, function () {

"use strict";

function base64encode(b, last_two) {
    "use strict";
    console.assert(b.BYTES_PER_ELEMENT == 1);
    // Most Base64 encoders use +/ for the last two characters, but not all
    if (last_two === undefined) last_two = '+/';
    // Init charcodes array
    var chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789" + last_two;
    var charcodes = new Uint8Array(64);
    for (var k=0; k<64; k++) charcodes[k] = chars.charCodeAt(k);
    // Init result string, as a typed array of ASCII values
    var s = new Uint8Array(Math.ceil(b.length / 3) * 4);
    // Init
    var b1, b2, b3;
    var i = 0;  // The byte index
    var j = 0;  // The string index
    // Iterate over bytes
    while (i < b.length) {
        // Sample bytes, out of bounds are mapped to zero
        b1 = b[i+0] || 0; b2 = b[i+1] || 0; b3 = b[i+2] || 0;
        i += 3;
        // Encode and assign
        s[j+0] = charcodes[( b1 >> 2 ) & 0x3F];
        s[j+1] = charcodes[( ( b1 & 0x3 ) << 4 ) | ( ( b2 >> 4 ) & 0xF )];
        s[j+2] = charcodes[( ( b2 & 0xF ) << 2 ) | ( ( b3 >> 6 ) & 0x3 )];
        s[j+3] = charcodes[b3 & 0x3F];
        j += 4;
    }
    // Replace stub bytes with the padding char
    for (var k=0; k<(i-b.length); k++) s[s.length-k-1] = '61';
    // Convert to string
    return String.fromCharCode.apply(null, s);
}

function base64decode(s, last_two) {
    "use strict";
    // Most Base64 encoders use +/ for the last two characters, but not all
    if (last_two === undefined) last_two = '+/';
    var charcode62 = last_two.charCodeAt(0), charcode63 = last_two.charCodeAt(1);
    // Allocate byte array, with a length as large as it can possibly become
    var b = new Uint8Array(Math.floor((s.length / 4) * 3));
    // Init
    var i = 0; // The number of bytes (and byte index)
    var j = 0; // The index into the string
    var c, cc = new Array(4);  // to store character codes (ints)
    // Iterate while there are chars left
    while (j < s.length) {
        // Collect 4 (or less) characters
        var charcount = 0;
        while (charcount < 4 && j < s.length) {
            c = s.charCodeAt(j++);
            if (c >= 65 && c <=90) c -= 65;  // A-Z: 0-25
            else if (c >=97 && c<=122) c -= 71;  // a-z: 26-51
            else if (c >=48 && c<=57) c += 4;  // 0-9: 52-61
            else if (c == charcode62) c = 62;
            else if (c == charcode63) c = 63;
            else continue;  // skip other chars, like newline, padding, or other
            cc[charcount] = c;
            charcount += 1;
        }
        // At the end, we may not have enough chars, zero these values
        if (charcount != 4) for (var k=charcount; k<4; k++) cc[k] = 0;
        // Calculate the 3 byte values
        b[i+0] = (cc[0] << 2) | (cc[1] >> 4);
        b[i+1] = ((cc[1] & 15) << 4) | (cc[2] >> 2);
        b[i+2] = ((cc[2] & 3) << 6) | cc[3];
        // Next i (4 chars -> 3 bytes, 3 chars -> 2 bytes, 2 chars -> 1 byte)
        i += charcount - 1;
    }
    // Return view that has the correct length, but on same data buffer.
    // The unused memory should be marginal, so making a copy not worth it.
    return new Uint8Array(b.buffer, 0, i);
}

return {encode: base64encode, decode: base64decode};
}));
