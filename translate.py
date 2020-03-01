"""module to translate vassal module saveFile and buildFile to more explicitly typed and
    self-descriptive json representation"""

from zipfile import ZipFile
import json
from os import path
import xml.etree.ElementTree as ET

from decoder import maybe, disconcat, deobfuscate, seqdict, COMMAND_SEPARATOR
from counters import decodePiece
from component import decodeComponent


_cmds = {'+': 'add', '-': 'remove', 'D': 'change', 'M': 'move'}
def decodeCommand(s):
    """
    module/BasicCommandEncoder.java:

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


def decodeBuild(fname):
    data = ET.parse(fname)
    defs = data.findall('.//VASSAL.build.module.PrototypeDefinition')
    protos = []
    for d in defs:
        p = dict(type='prototype', name=d.attrib['name'])
        p.update(decodeCommand(d.text))
        protos.append(p)

    result = dict(prototypes=protos)
    base = path.splitext(fname)[0]
    with open(base + '.json', 'w') as f:
        json.dump(result, f, indent=4)


if __name__ == '__main__':
    from counters import _missingPieceDecoders
#    decodeSave('Campaign-180907.vsav')
#    decodeSave('New-180907.vsav')
    decodeSave('A3R_1939_Scenario_Template_Rev1702_AWAW')
    decodeBuild('buildFile')
    print("missing decoders: {!s}".format(_missingPieceDecoders))


r"""

VASSAL.build.module.PrototypeDefinition
+/null/macro;Remove All Markers;;88,520;;;65\,520,83\,520,70\,520,69\,520   emb2;;2;;AutoVictory;2;A;;0;;;65,520;1;false;0;0;transparent.gif,av_force_layer.gif;,+ (AV attack);true;AV;;;false;;1\  label;76,130;Change Label;14;0,0,0;255,255,255;t;0;c;0;b;c;$pieceName$ ($label$);Dialog;0;0;TextLabel\\ piece;;;;/  1;\ \\  null;0;0;


VASSAL.build.widget.PieceSlot
+/null/prototype;Basic prototype;German\   piece;;;ge-art-7;ge-art-7/  \   null;0;0;0


"""

"""

the module is a zip archive
the save game *.sav, *.vsav, *.scen? is a zip archive

buildFile is an XML file with a bunch of spec info

moduledata is a XML file with some module version info


./module/GameState.java:
   return GameModule.getGameModule().encode(getRestoreCommand());


./launch/BasicModule.java:  private static char COMMAND_SEPARATOR = (char) KeyEvent.VK_ESCAPE;




GameState::getRestoreCommand
    Command c = new SetupCommand(false);
    c.append(checkVersionCommand());
    c.append(getRestorePiecesCommand());
    for (GameComponent gc : gameComponents) {
      c.append(gc.getRestoreCommand());
    }
    c.append(new SetupCommand(true));
    return c;


tools/SequenceEncoder

concats items with delimiter, first escaping delimiter
single-quoted strings 'a' or strings ending with bkslsh are single-quoted, ''a'', 'some\'


saveFile, ESC-separated
nested with backslash escaping, e.g. \esc
begin_save
<versionCmd>
<piecesCmd>
[<restoreComponent>]
end_save

piece id's are generally epoch time millis creation date

module/GameComponent.java
module/NotesWindow.java  - NOTE / PNOTE
/build/module/Map.java - BoardPicker
module/turn/TurnTracker.java - TURN

 info looks like 107 bytes of hex with almost the obfuscated header, but isn't quite?
less info
!VCSS162400110100010020BA6DB55D00208FA8FB010010D6A50010DE5900109E5F6057DF8373ECC6763F93A7A219F645835F482E5318C7BC70B206CC07A54156C753970F8B8F3382E5A1BF858E3E16763828BC8BB07E267B54354D299E61936588AD73288E74A26456429E6E52

"""
