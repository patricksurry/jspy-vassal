# Decode game components listed in save file, which implement module/GameComponent.java

from decoder import varargs, disdict, disconcat, seqdict, formatted, boolish, COMMAND_SEPARATOR

def _tabDecoder(proto):
    return disdict(proto, '\t')

_noteTypes=dict(
    NOTES=dict(type='scenario', proto=dict(text=formatted)),
    PNOTES=dict(type='public', proto=dict(text=formatted)),
    PNOTE=dict(type='private', proto=dict(owner=str, text=formatted)),
    SNOTE=dict(type='secret', proto=dict(name=str, owner=str, hidden=boolish, text=formatted)),
)

def noteDecoder(s):
    notes = {}
    cmds = disconcat(s, COMMAND_SEPARATOR)
    for cmd in cmds:
        typ, *vs = disconcat(cmd, '\t')
        d = _noteTypes.get(typ)
        assert d, "Uncrecognized note type {:s} in {:s}".format(typ, s)
        note = dict(type=d['type'])
        if vs and vs[0]:
            note.update(seqdict(d['proto'], vs))
        notes[typ] = note
    return notes

_componentDecoders = dict(
    # module/map/BoardPicker
    BoardPicker=_tabDecoder(dict(id=str, name=str, x=int, y=int)), #TODO name can be optional name/rev
    # module/turn/TurnTracker.java
    #TODO parse level state
    TurnTracker=_tabDecoder(dict(id=str, levels=varargs(disdict(dict(turn=int, state=str), '|')))),
    NOTE=noteDecoder
)

"""
"NOTES\t\u001bPNOTES\t\u001bPNOTE\trommel8\tGermsn-Bill Thomson|Russian-Peter Stein|Bid 24 RP; 1 extra a turn"
"PNOTE\trommel8\tGermsn-Bill Thomson|Russian-Peter Stein|Bid 24 RP; 1 extra a turn"
"""

def decodeComponent(state):
    cmd = disconcat(state, COMMAND_SEPARATOR)[0]
    id = disconcat(cmd, '\t')[0]
    result = dict(state=state)
    for kind, decoder in _componentDecoders.items():
        if kind in id:
            result = dict(kind=kind)
            try:
                result.update(decoder(state))
            except:
                print('Failed to parse state for {!s}: {:s}'.format(result, state))
                result['state'] = state
            break
    return result


#module/NotesWindow.java  - NOTE / PNOTE


"""
"FlugplatzBoardPicker\tFlugplatz\t0\t0"


        "TURNTurnTracker0\t0|1941;0;false;-1;1\\;0\\;0\\;true,true,true,true,true,true\\;0\\\\;0\\\\;0\\\\;true,true,true,true\\\\;0\\\\\\;0\\\\\\;0\\\\\\;true"

TURN

    final SequenceEncoder se = new SequenceEncoder('|');
    se.append(currentLevel);
    final Iterator<TurnLevel> i = getTurnLevels();
    while (i.hasNext()) {
      final TurnLevel level = i.next();
      se.append(level.getState());
    }
    return se.getValue();

    return new SetTurn(getState(), this);


      SequenceEncoder se = new SequenceEncoder('\t');
      se.append(COMMAND_PREFIX + com.getTurn().getId());
      se.append(com.newState);


currentLevel(int)|turnlevel

"""


