"""low level modules to deal with tools.SequenceEncoder and tools.io.ObfuscatingOutputStream output"""

import re


MAGIC_HEADER = '!VCSK'
UNUSED_SIGIL = '\x01'
COMMAND_SEPARATOR = '\x1b'


def deobfuscate(s):
    """
    Deobufuscate an input stream, to get an almost equally obfuscated sequence encoding :-)

    tools/io/ObfuscatingOutputStream.java
    tools/io/DeobfuscatingInputStream.java
    """
    if not s.startswith(MAGIC_HEADER):
        return s
    bytes = bytearray.fromhex(s[len(MAGIC_HEADER):])
    key = bytes[0]
    return bytearray(b ^ key for b in bytes[1:]).decode('utf-8')


def dequote(s):
    if len(s) >= 2 and s[0] == "'" and s[-1] == "'":
        s = s[1:-1]
    return s


def disconcat(s, delim, maxsplit=-1):
    """parse output of tools.SequenceEncoder, which concats a sequence of strings using a delimiter"""
    if s is None:  # as opposed to '' => ['']
        return []

    assert UNUSED_SIGIL not in s, "Found marker string in source"

    # preserve escaped delimiters using an unused character
    s = re.sub(r'\\' + re.escape(delim), UNUSED_SIGIL, s)
    # then split on delimiter and replace previously escaped delims
    # also remove single-quoted strings, which is used to protect trailing backslashes or quotes
    ds = [dequote(d.replace(UNUSED_SIGIL, delim)) for d in s.split(delim, maxsplit)]
    return ds


def seqdict(proto, vs, use_defaults=True, ignore_excess=True):
    """convert a sequence of strings to a dictionary via a prototype of field names and types"""
    if isinstance(proto, dict):
        # proto is a dict of {fieldName => constructor}
        ks = list(proto.keys())
        fs = list(proto.values())
        if use_defaults:
            fs = [maybe(f) if not hasattr(f, 'varargs') else f for f in fs]
    else:
        # proto is just a list of fieldName, so use identity constructor
        ks = proto
        fs = [identity for _ in ks]

    nk = len(ks)
    nv = len(vs)
    varargs = fs and hasattr(fs[-1], 'varargs')
    if nk > nv and use_defaults:
        dv = (nk - nv - (1 if varargs else 0))
        vs += [None] * dv
        nv += dv
    if nk < nv and not varargs and ignore_excess:
        vs = vs[:nk]
        nv = nk
    assert nk == nv or (varargs and nk-1 <= nv),\
        "seqdict: Mismatched key / value length: {!s} vs {!s}".format(ks, vs)

    if varargs:
        # the last item becomes the tail of the list
        vs = vs[:nk-1] + [vs[nk-1:]]
    vs = [f(v) for (f, v) in zip(fs, vs)]
    return dict(zip(ks, vs))



# compound type constructors that wrap other constructors
def maybe(typ):
    if typ == str:
        return lambda s: None if s == 'null' else s
    else:
        return lambda s: None if not s else typ(s)


def listOf(typ, delim):
    return lambda s: list(map(typ, disconcat(s, delim)))


def varargs(typ):
    """
    Special case allowed as last argrument of seqdict to capture all remaining items
    as a list; note difference from capturing a separately delimited list via strList
    """
    f = lambda ds: list(map(typ, ds))
    f.varargs = True
    return f


# basic constructors that take a str => type

def identity(s):
    return s


def formatted(s, newline='|'):
    return re.sub(re.escape(newline), '\n', s)


def boolish(s):
    if type(s) is bool:
        return s
    if not s:
        return False
    if type(s) is str:
        return s.lower()[0] not in "nf0"
    return bool(s)


def disdict(proto, delim):
    """parse a sequence of delimited values to a dictionary"""
    return lambda s: seqdict(proto, disconcat(s, delim))


def pdict(listsep=',', kvsep='='):
    return lambda s: dict(disconcat(kv, kvsep) for kv in disconcat(s, listsep))


def rgbColor(s):
    return 'rgb({:s})'.format(s) if s else None


_halign = dict(l='left', r='right', c='center')
_valign = dict(t='top', b='bottom', c='center')
halign = _halign.get
valign = _valign.get

#https://docs.oracle.com/javase/7/docs/api/constant-values.html#java.awt.event.InputEvent.ALT_DOWN_MASK
_keyMods = [
    (1 << i, v) for (i,v) in enumerate([
        'SHIFT', 'CTRL', 'META', 'ALT', 'BUTTON1', 'ALT_GRAPH',
        'SHIFT_DOWN', 'CTRL_DOWN', 'META_DOWN', 'ALT_DOWN', 'BUTTON1_DOWN',
        'BUTTON2_DOWN', 'BUTTON3_DOWN', 'ALT_GRAPH_DOWN'
    ])
]
def keyStroke(s):
    if not s:
        return None
    code, mask = [int(v) for v in s.split(',')]
    mods = [v for (i,v) in _keyMods if i & mask]
    return dict(code=code, key=chr(code), mask=mask, mods=mods)
