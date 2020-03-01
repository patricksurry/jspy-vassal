"""module to translate vassal module saveFile and buildFile to more explicitly typed and
    self-descriptive json representation"""

from zipfile import ZipFile
import json
from os import path
import xml.etree.ElementTree as ET
from xmljson import yahoo as x2j
import logging

from decoder import maybe, disconcat, deobfuscate, seqdict, COMMAND_SEPARATOR
from counters import decodePiece
from component import decodeComponent
from gamepiece import  decodePieceLayout, decodePieceImage


_cmds = {'+': 'add', '-': 'remove', 'D': 'change', 'M': 'move'}
def decodeCommand(s):
    """
    module/BasicCommandEncoder.java

    encodes commands like below, though so far I only see + (add)
    id's are generally epoch time millis based on the object creation date

    +/id/type/state
    -/id
    D/id/state[/oldstate]
    M/id/mapid/x/y/underid/oldmapid/oldx/oldy/oldunderid/playerid
    """
    (c, id, *elts) = disconcat(s, '/')
    id = maybe(str)(id)
    assert c in _cmds, 'Unknown command {:s}'.format(c)
    cmd = _cmds[c]
    data = dict(id=id)
    if cmd == 'add':
        d = seqdict(['type', 'state'], elts)
        data['piece'] = decodePiece(**d)
    elif cmd == 'remove':
        assert len(elts) == 0, "Got {:d} args for remove, expected 0".format(len(elts))
    elif cmd == 'change':
        fields = ['state', 'oldstate']
        assert 1 <= len(elts) <= len(fields), "Got {:d} args for change, expected 1-2".format(len(elts))
        data.update(dict(zip(fields, elts)))
    elif cmd == 'move':
        proto = dict(
            newMapId=str, newX=int, newY=int, newUnderId=str,
            oldMapId=str, oldX=int, oldY=int, oldUnderId=str,
            playerId=str
        )
        data.update(seqdict(proto, elts))
    return {cmd: data}


def decodeSave(fname):
    """
    Decode a savedGame which is ESC-separated with backlashed nested separators

    See ./module/GameState.java: getRestoreCommand()

    begin_save
    <versionCmd>  <= not clear if this is serialized?
    <piecesCmd>
    [<restoreComponent>]
    end_save
    """
    with ZipFile(fname).open('savedGame') as f:
        saved = f.read().decode('utf-8')
    content = deobfuscate(saved)
    base = path.splitext(fname)[0]
    with open(base + '.raw', 'w') as f:
        f.write(content)
    begin, *cmds, end = disconcat(content, COMMAND_SEPARATOR)
    assert begin == 'begin_save' and end == 'end_save', "Expected start/end markers in savedGame"
    while cmds:
        # skip empty cmds, not sure that checkVersion even gets serialized?
        if cmds[0]:
            break
        cmds.pop(0)
    assert cmds, "Expected some non-empty commands?!"
    pcs, *comps = cmds
    assert pcs[0] == COMMAND_SEPARATOR, 'expected leading separator for restorePieces in {!s}'.format(pcs)
    result = dict(
        restorePieces=[decodeCommand(cmd) for cmd in disconcat(pcs, COMMAND_SEPARATOR)[1:]],
        components=[decodeComponent(c) for c in comps],
    )
    with open(base + '.json', 'w') as f:
        json.dump(result, f, indent=4)


def getCoercedList(d, k):
    """returns d[k], first coercing the value in-place as a list if required"""
    v = d.get(k, [])
    if not isinstance(v, list):
        v = [v]
        d[k] = v
    return v


def decodeByKey(d, key, decoder):
    """decodes and removes the specified key in dict d using the given decoder, updating in place"""
    v = decoder(d[key])
    del d[key]
    d.update(v)


def decodeBuild(fname):
    data = x2j.data(ET.parse(fname).getroot())
    keyref = {}
    data = simplifykeys(data['VASSAL.launch.BasicModule'], keyref)
    data['classRefs'] = {k: list(v) if len(v) > 1 else v.pop() for (k,v) in keyref.items()}

    # parse prototype commands in elements like VASSAL.build.module.PrototypeDefinition
    # e.g.
    #   +/null/macro;Remove All Markers;;88,520;;;65\,520,83\,520,70\,520,69\,520   emb2;;2;;AutoVictory;2;A;;0;;;65,520;1;false;0;0;transparent.gif,av_force_layer.gif;,+ (AV attack);true;AV;;;false;;1\  label;76,130;Change Label;14;0,0,0;255,255,255;t;0;c;0;b;c;$pieceName$ ($label$);Dialog;0;0;TextLabel\\ piece;;;;/  1;\ \\  null;0;0;
    defs = data.get('PrototypesContainer', {}).get('PrototypeDefinition', [])
    for d in defs:
        decodeByKey(d, 'content', decodeCommand)

    ds = getCoercedList(data, 'PieceWindow')

    #parse commands in elements like VASSAL.build.widget.PieceSlot
    # e.g.
    #   +/null/prototype;Basic prototype;German\   piece;;;ge-art-7;ge-art-7/  \   null;0;0;0
    def decodePieceSlots(v):
        if isinstance(v, dict):
            for (k, vv) in v.items():
                if k == 'PieceSlot':
                    for p in getCoercedList(v, 'PieceSlot'):
                        decodeByKey(p, 'content', decodeCommand)
                else:
                    decodePieceSlots(vv)
        elif isinstance(v, list):
            for vv in v:
                decodePieceSlots(vv)
        else:
            pass

    decodePieceSlots(ds)

    # parse piecelayout and image defs like
    #
    #   <VASSAL.build.module.gamepieceimage.GamePieceLayout border="Fancy" height="57" layout="Symbol;27;21;1.0|Symbol;Center;0;-2;0;true,Text;Stats;center;Command;;67\,130;76\,520;76\,130;false|Stats;Bottom;0;0;0;true,Text;Id;center;Command;;67\,130;76\,520;76\,130;false|Id;Bottom;0;0;270;true,Text;Loc;left;Command;;67\,130;76\,520;76\,130;false|Loc;Top Left;4;0;0;true" name="Ground" width="57">
    #       <VASSAL.build.module.gamepieceimage.GamePieceImage bgColor="ru-bg" borderColor="ru-fg" name="ru-abn-4" props="Symbol;Symbol;Center;ru-fg;CLEAR;Corps;Infantry;Airborne;ru-fg,Text;Stats;Bottom;ru-fg;CLEAR;1-2;,Text;Id;Bottom;ru-fg;CLEAR;4;,Text;Loc;Top Left;BLACK;CLEAR;3;"/>
    defs = (
        data.get('GamePieceImageDefinitions', {})
        .get('GamePieceLayoutsContainer', {})
        .get('GamePieceLayout', [])
    )
    for d in defs:
        d['layout'] = decodePieceLayout(d['layout'])
        for pi in getCoercedList(d, 'GamePieceImage'):
            pi['props'] = decodePieceImage(pi['props'])

    base = path.splitext(fname)[0]
    with open(base + '.json', 'w') as f:
        json.dump(data, f, indent=4)


def simplifykeys(d, keyref):
    """
    Simplify element (key) names in the imported XML by
    taking the last item in a dotted sequence, while maintaining a
    cross-reference that lists the long version(s) of any short key.
    In practice there don't seem to be dupes,
    and we could probably infer detailed type by context away.
    """

    if isinstance(d, dict):
        return {_simplekey(k, keyref): simplifykeys(v, keyref) for (k,v) in d.items()}
    elif isinstance(d, list):
        return [simplifykeys(x, keyref) for x in d]
    else:
        return d


def _simplekey(k, keyref):
    if '.' not in k:
        return k
    sk = k.split('.')[-1]
    keyref.setdefault(sk, set()).add(k)
    return sk


if __name__ == '__main__':
    from counters import _missingPieceDecoders
    from glob import glob
    import logging

    logging.basicConfig(level=logging.INFO)

    fs = glob('test/*.vsav')
    logging.info('Decoding save files {!s}'.format(fs))
    for f in fs:
        decodeSave(f)
    fs = glob('test/buildFile*.yml')
    logging.info('Decoding build files {!s}'.format(fs))
    for f in fs:
        decodeBuild(f)
    if _missingPieceDecoders:
        logging.warn("missing decoders: {!s}".format(_missingPieceDecoders))
