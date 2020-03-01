from decoder import disconcat, disdict, keyStroke, boolish, listOf, varargs, rgbColor, halign, valign, pdict


def _protoDecoder(specProto, stateProto):
    nil = lambda s: {}
    f = disdict(specProto, ';') if specProto else nil
    g = disdict(stateProto, ';') if stateProto else nil
    return lambda spec, state: {**f(spec), **g(state)}


_pieceDecoders = dict(
    # counters.BasicPiece
    piece=_protoDecoder(
        ('cloneKey', 'deleteKey', 'imageName', 'commonName'),
        dict(mapId=str, x=int, y=int, gpId=str)
    ),
    # counters.Stack
    stack=_protoDecoder(
        None,
        dict(mapId=str, x=int, y=int, ids=varargs(str)),
    ),
    # counters.Hideable
    hide=_protoDecoder(
        dict(
            hideKey=keyStroke, command=str, bgColor=rgbColor,
            access=str, #TODO configure.pieceAccessConfigurer
            transparency=float
        ),
        dict(hiddenBy=str)
    ),
    # counters.Clone
    clone=_protoDecoder(
        dict(commandName=str, key=keyStroke),
        None
    ),
    # counters.Marker - note spec has the labels, state has the values, we represent as a dict
    mark=lambda spec, state: dict(marks=dict(zip(listOf(str, ',')(spec), listOf(str, ',')(state)))),
    # counters.MovementMarkable
    markmoved=_protoDecoder(
        dict(
            movedIcon=str,
            xOffset=int, yOffset=int,
            command=str, key=keyStroke,
        ),
        dict(hasMoved=boolish)
    ),
    # counters.SendToLocation
    sendto=_protoDecoder(
        dict(
            commandName=str, key=keyStroke,
            mapId=str, boardName=str, x=int, y=int,
            backCommandName=str, backKey=keyStroke,
            xIndex=int, yIndex=int, xOffset=int, yOffset=int,
            description=str, destination=str, # st.nextToken(DEST_LOCATION.substring(0,1));
            zone=str, region=str, propertyFilter=str, gridLocation=str
        ),
        dict(backMapId=str, backMapX=int, backMapY=int)
    ),
    # counters.Embellishment
    emb2=_protoDecoder(
        dict(
            activateCommand=str, activateModifiers=int, activateKey=str,
            upCommand=str, upModifiers=int, upKey=str,
            downCommand=str, downModifiers=int, downKey=str,
            resetCommand=str, resetKey=keyStroke, resetLevel=str,
            drawUnderneathWhenSelected=boolish, xOff=int, yOff=int,
            imageName=listOf(str, ','), commonName=listOf(str, ','),
            loopLevels=boolish, name=str,
            rndKey=keyStroke, rndText=str,
            followProperty=boolish, propertyName=str, firstLevelValue=int,
            version=int, alwaysActive=boolish,
            activateKeyStroke=keyStroke, increaseKeyStroke=keyStroke, decreaseKeyStroke=keyStroke,
        ),
        dict(value=int)
    ),
    # counters.Footprint
    footprint=_protoDecoder(
        dict(
            trailKey=keyStroke, menuCommand=str, initiallyVisible=boolish, globallyVisible=boolish,
            circleRadius=int, fillColor=rgbColor, lineColor=rgbColor,
            selectedTransparency=int, unSelectedTransparency=int,
            edgePointBuffer=int, edgeDisplayBuffer=int, lineWidth=float
        ),
        dict(
           globalVisibility=boolish, startMapId=str, numPoints=int,
           points=varargs(disdict(dict(x=int, y=int), ','))
        )
    ),
    # counters.Labeler
    label=_protoDecoder(
        dict(
            labelKey=keyStroke,
            menuCommand=str,
            fontSize=int,
            textBg=rgbColor,
            textFg=rgbColor,
            verticalPos=valign, verticalOffset=int,
            horizontalPos=halign, horizontalOffset=int,
            verticalJust=valign, horizontalJust=halign,
            nameFormat=str,
            fontFamily=str, fontStyle=str,
            rotateDegrees=int,
            propertyName=str,
            description=str,
        ),
        dict(label=str)
    ),
    # counters.TriggerAction
    macro=_protoDecoder(
        dict(
            name=str, command=str, key=keyStroke, propertyMatch=str,
            watchKeys=listOf(keyStroke, ','), actionKeys=listOf(keyStroke, ','),
            loopConfig=str, preLoopKeyConfig=str, postLoopKeyConfig=str,
            loopTypeConfig=str, whileExpressionConfig=str, untilExpressionConfig=str,
            loopCountConfig=str, indexConfig=str, indexPropertyConfig=str,
            indexStartConfig=str, indexStepConfig=str,
        ),
        None
    ),
    # counters.ReportState
    report=_protoDecoder(
        dict(
            keys=listOf(keyStroke, ','), reportFormat=str,
            cycleDownKeys=listOf(keyStroke, ','), cycleReportFormat=listOf(str, ','),
            description=str
        ),
        dict(cycleIndex=int)
    ),
    # counters.SubMenu
    submenu=_protoDecoder(
        dict(subMenu=str, commands=listOf(str, ',')),
        None
    ),
    # counters.Immobilized
    immob=_protoDecoder(
        dict(selectionOptions=str, movementOptions=str),  #TODO could parse these letter selectors
        None
    ),
    # counters.Delete
    delete=_protoDecoder(
        dict(nameInput=str, keyInput=keyStroke),
        None
    ),
    # counters.UsePrototype
    prototype=_protoDecoder(
        dict(name=str, properties=pdict(',', '=')),
        None
    ),
    # counters.FreeRotator
    # "type": "rotate;6;93,130;91,130;Rotate CW;Rotate CCW;;;",
    # "state": "0"
    rotate=_protoDecoder(
        dict(
            validAngles=int,
            #TODO - next items areconditional on validAngles==1
            # in that case we want:
            #   setAngleKey=keyStroke, setAngleText=str,
            # but assume always != 1 case for now
            rotateCWKey=keyStroke, rotateCCWKey=keyStroke,
            rotateCWText=str, rotateCCWText=str,
            rotateRNDKey=keyStroke, rotateRNDText=str, name=str
        ),
        dict(angleIndex=int)
    )
)

_missingPieceDecoders = {}

def decodePiece(type, state):
    # nested decorator structure gets represented as pairs of tab-separated types & states
    # we'll return as a list instead
    types = disconcat(type, '\t')
    states = disconcat(state, '\t')
    if len(types) != len(states) or len(types) > 2:
        raise SyntaxError("Mismatched nested piece definition")

    t, s = types[0], states[0]
    kind, *maybeSpec = disconcat(t, ';', 1)
    spec = maybeSpec[0] if maybeSpec else None
    piece = dict(kind=kind)
    if kind in _pieceDecoders:
        try:
            piece.update(_pieceDecoders[kind](spec,s))
        except:
            print("Failed to decode {:s} with spec='{!s}', state='{!s}'".format(kind, spec, s))
            raise
    else:
        _missingPieceDecoders[kind] = _missingPieceDecoders.setdefault(kind, 0) + 1
        piece.update(dict(type=t, state=s))

    result = [piece]
    if len(types) == 2:
        result = decodePiece(types[1], states[1]) + result
    return result

