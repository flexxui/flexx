# -*- coding: utf-8 -*-
# Copyright (C) 2014, Almar Klein

""" IPC in about 250 lines

This modules implements inter process communication via a memory mapped
file. The protocol is designed to be simple, so it can be implemented
in other (dynamic) languages with ease. Nevertheless, communication is
very fast and there are no restrictions on message size.
"""

""" Developer notes

This protocol uses a memory mapped file for communication between two
processes. The file is divided in blocks; there is at least one pair
of a read and a write block (a read block on one end is a write block
on the other end), but there can be multiple pairs (i.e. "channels").

This protocol provides a means to communicate packages of binary data.
Each package consists of a head (a 64bit unsigned integer that specifies
the package length) and the data (bytes).

The Writer first processes the package head and then the data. If possible,
both are written in once piece, but this is not always possible. One
reason is that the package (or its head) needs to wrap around the block
boundary. Further, the Writer cannot write to parts of the block that
have not been read yet (this may occur when the reader is slow, or when
the packages are very large. In the latter case, the Writer will write
what it can. Consequently, packages can be (much) larger than the block
size.

The Reader first reads the message head and then it reads the message.
The message (but also the head, in cases near the block boundary) can
be split in pieces.

The Reader and Writer class both use a queue (called ``_pending``). The
Writer uses the queue to store head and data before trying to actually
write it to the file. The reader uses the queue to store head and data
(which may be incomplete) before reconstructing the package and passing
it to the user.

"""

import sys
import os
import time
import struct
import mmap
import tempfile
import ctypes

if sys.version_info[0] >= 3:
    bytezero = bytes([0])
    uint8 = lambda x: x
    toint = lambda x: x
else:
    bytezero = chr(0)
    uint8 = chr
    toint = ord


version_info = (0, 1)  # Only two numbers
__verion__ = '.'.join([str(i) for i in version_info])

# todo: increase to reserve bytes for future
HEAD_SIZE = 32  # For global header and for header of each block
BLOCK_SIZE = 2**10  #2**10  # must be >> HEAD_SIZE

# todo: make work on Python 2.4? (need to get rid of Mmap class) -> __del__ in socket
# todo: heartbeat
# todo: expose as a queue for which both sides know the length
# todo: employ max length
# todo: one blockpair per mmap
# todo: combine two blocks in one "socket"
# todo: maybe implement close-handshake and zero-out the file?


class Mmap(mmap.mmap):
    """ Mmap(filename=None, size=0)
    
    Create a memory map that can be shared between processes. If
    filename is None, a unique filename is used. If size is given, the
    file is created and filled with zeros. The filename in use is set
    as an attribute on this object.
    """
    
    def __new__(cls, filename=None, size=0):
        # Deal with filename
        if filename is None:
            if size <= 0:
                raise ValueError('Mmap needs size if no filename is given.')
            filename = tempfile.mktemp(prefix='yoton2_')
        elif not os.path.split(filename)[0]:
            filename = os.path.join(tempfile.gettempdir(), filename)
        else:
            pass  # filename is considered absolute
        # If necessary, create the file with size zero bytes
        if size > 0:
            f = open(filename, 'wb')
            f.write(bytezero * size)
            f.close()
        elif not os.path.isfile(filename):
            raise ValueError('Mmap file does not exist, give size to create.')
        # Open the file in append read/write mode
        f = open(filename, 'a+b')
        # Create the memory map on the file
        m = mmap.mmap.__new__(cls, f.fileno(), 0)
        f.close()  # File can safely be closed
        # Mark file for deletion. On Unix, the file is in /tmp/ and will be
        # removed automatically. On Windows we need to explicitly mark it.
        # todo: is this correct for Windows? I tried and it did not seem to work
        if ctypes and sys.platform.startswith('win'):
            ctypes.windll.kernel32.MoveFileExA(filename, None, 4)
        # For deleting
        m._unlink = os.unlink  # Need unlink even if Python is shutting down
        m.filename = filename
        return m
    
    def close(self):
        # Try to close the mmap and then remove the file. On Unix, the
        # file is "unlinked" from the directory, and will be deleted
        # when the last file handle is closed. In Windows, removing the
        # file will fail if the other end has it open, and the file
        # will be deleted when the mmap at the other end is closed.
        try:
            mmap.mmap.close(self)
        except Exception:
            pass
        try:
            self._unlink(self.filename)
        except Exception:
            pass
    
    def __del__(self):
        self.close()


def bind(filename=None, blockpairs=1):
    """ Open a connection. If filename is not given or None, a filename
    is chosen automatically. This function returns blockpairs number
    of Writer, Reader pairs.
    """
    # Open memory mapped file, deduced file size from number of blocks
    size = HEAD_SIZE + blockpairs * 2 * BLOCK_SIZE
    m = Mmap(filename, size=size)
    # Write header
    m[0:5] = 'yoton'.encode('ascii')
    m[5] = uint8(version_info[0])
    m[6] = uint8(version_info[1])
    # Create blocks
    blocks = []
    for i in range(blockpairs):
        b1 = Writer(m, (2 * i + 0) * BLOCK_SIZE + HEAD_SIZE)
        b2 = Reader(m, (2 * i + 1) * BLOCK_SIZE + HEAD_SIZE)
        blocks.extend([b1, b2])
    return tuple(blocks)


def connect(filename):
    """ Connect to an open connection.
    """
    # Open memory mapped file and deduce the number of block pairs
    m = Mmap(filename)
    blockpairs = m.size() // (BLOCK_SIZE*2)  # integer divide
    # Check yoton and version (minor version number is allowed to be different)
    assert m[0:5] == 'yoton'.encode('ascii')
    assert uint8(version_info[0]) == m[5]  #struct.unpack('<B', m[5])[0]
    # Create blocks
    blocks = []
    for i in range(blockpairs):
        b1 = Writer(m, (2 * i + 1) * BLOCK_SIZE + HEAD_SIZE)
        b2 = Reader(m, (2 * i + 0) * BLOCK_SIZE + HEAD_SIZE)
        blocks.extend([b1, b2])
    return tuple(blocks)


class Block(object):
    """ Base class for the Reader and Writer class

    Each block consists of a number of meta bytes and then the data.
    The meta bytes consists of a write and a read counter, and each
    comes with a control byte that indicates whether the counter has
    changed.

    [cwwwwwwwwcrrrrrrrr---------- data --------------]
    """

    def __init__(self, m, offset):
        self._m = m
        self._o = offset
        self._read_cache = 0
        self._read_control = 0
        self._counter = 0  # mirror of the counter that we set
        self._pending = []

    def _set_counter(self, i):
        # If we write to this block, we must set the write counter
        pos = self._o + [9, 0][isinstance(self, Writer)]
        self._m[pos+1:pos+9] = struct.pack('<Q', i)  # counter
        self._m[pos] = uint8((toint(self._m[pos]) + 1) % 255)  # control byte

    def _get_counter(self):
        # If we write to this block, we must set get the read counter
        pos = self._o + [0, 9][isinstance(self, Writer)]
        control = toint(self._m[pos])  # control byte
        if control != self._read_control:
            self._read_control = control
            self._read_cache = struct.unpack('<Q', self._m[pos+1:pos+9])[0]
        return self._read_cache


class Reader(Block):
    """ Reader object for yoton2, returned by bind() and connect()
    """

    def read(self, block=False):
        """ Read one package of data. If block is False (default) this
        function returns None when no new package is available. If block
        is True, this functions waits until a package is available.
        """
        # Read until we cannot, or until we have a complete piece of data
        result = 1
        if block:
            while result != 2:  # 2 means a complete piece of data
                time.sleep(0.00001)
                result = self._read_something()
        else:
            while result == 1:
                result = self._read_something()
        # Return data if it was complete
        if result == 2:
            if len(self._pending) == 2:
                data = self._pending[1]
            else:
                data = bytes().join(self._pending[1:])
            self._pending = []
            return data.decode('utf-8')

    def _read_something(self):
        """ Read a piece of data and put it in our queue. Returns 0 if
        no data was available for reading. Returns 1 if we read some
        data. Returns 2 if we read data and now have a complete package.
        """
        # Prepare counters
        read_counter = self._counter
        write_counter = self._get_counter()
        blocksize = BLOCK_SIZE - HEAD_SIZE
        # Calculate bytes left
        rounds, pos = read_counter // blocksize, read_counter % blocksize
        bytesleft_to_read = write_counter - read_counter
        bytesleft_to_edge = blocksize - pos
        bytesleft = min(bytesleft_to_read, bytesleft_to_edge)
        # How many bytes do we need (for head or data) to complete?
        self._pending = self._pending or [-8]  # -8 means look for head
        allready_read = sum([len(x) for x in self._pending[1:]])
        nbytes = abs(self._pending[0]) - allready_read
        max
        # Read what we can
        p = self._o + HEAD_SIZE + pos
        if not bytesleft:
            return 0  # We could not read anything
        elif bytesleft >= nbytes:
            data = self._m[p:p+nbytes]
            pos += nbytes
        else:
            data = self._m[p:p+bytesleft]
            pos += bytesleft
        # Update counter
        self._counter = rounds * blocksize + pos
        self._set_counter(self._counter)
        # Process
        if self._pending[0] < 0:
            # Process head
            if len(self._pending) == 2:
                data = self._pending.pop(1) + data
            assert len(data) <= 8
            if len(data) == 8:
                datasize = struct.unpack('<Q', data)[0]
                self._pending = [datasize]  # Now search for data
            else:
                self._pending.append(data)  # We need more for the head
        else:
            # Data itself
            self._pending.append(data)
            if len(data) >= nbytes:
                return 2
        return 1  # We read something (but not a whole message)


class Writer(Block):
    """ Writer object for yoton2, returned by bind() and connect()
    """

    def write(self, msg, block=False):
        """ Write one package of data. If block is False (default) the
        package is queued if it cannot be written right away. If block is
        True this function waits until the queue is empty.
        """
        # Add head and data to queue
        data = msg.encode('utf8')
        head = struct.pack('<Q', len(data))
        self._pending.append(head)
        self._pending.append(data)
        # Write to file
        if block:
            while self._pending:
                time.sleep(0.00001)
                self.poll()
        else:
            self.poll()

    def poll(self):
        """ Write pending data until the queue is empty or no more
        data could be written. When using write() in non-blocking mode,
        it is recommended to periodically call this function.
        """
        wrote_something = True
        while self._pending and wrote_something:
            wrote_something = self._write_something()

    def _write_something(self):
        """ Write a piece of data from our queue. Returns 0 if we could
        not write anything. Returns 1 if we did write something.
        """
        # Prepare counters
        write_counter = self._counter
        read_counter = self._get_counter()
        blocksize = BLOCK_SIZE - HEAD_SIZE
        # Calculate bytes left
        rounds, pos = write_counter // blocksize, write_counter % blocksize
        bytesleft_to_write = (read_counter + blocksize) - write_counter
        bytesleft_to_edge = blocksize - pos
        bytesleft = min(bytesleft_to_write, bytesleft_to_edge)
        if bytesleft_to_write <= 8:  # todo: this could higher
            return 0
        # Write the lot, or a part
        bb = self._pending.pop(0)
        nbytes = len(bb)
        p = self._o + HEAD_SIZE + pos
        if bytesleft >= nbytes:
            self._m[p:p+nbytes] = bb
            pos += nbytes
        else:
            bb, remainder = bb[:bytesleft], bb[bytesleft:]
            self._m[p:p+bytesleft] = bb  # write what we can
            self._pending.insert(0, remainder)  # remainder back in queue
            pos += bytesleft
        # Update counter
        self._counter = rounds * blocksize + pos
        self._set_counter(self._counter)
        return 1
