from decoder import disdict, disconcat, boolish, keyStroke, rgbColor
import json

def _proto(**kwargs):
    return disdict(kwargs, ';')

# from build.module.gamepieceimage.XxxItem.java
pieceLayoutProtos = dict(
    Box=_proto(width=int, height=int, shape=str, bevel=int),  # aka Shape
    Image=_proto(imageName=str, imageSource=str),
    Symbol=_proto(width=int, height=int, lineWidght=float),
    Text=_proto(
        fontStyleName=str, textSource=str, text=str,
        changeCmd=str, changeKey=keyStroke, lockCmd=str, lockKey=keyStroke,
        lockable=boolish
    ),
    TextBox=_proto(width=int, height=int, isHTML=boolish),

    # base layout proto shared by all derived layouts
    Item=_proto(name=str, location=str, xoffset=int, yoffset=int, rotation=int, antialias=boolish)
)

# from build.module.gamepieceimage.XxxItemInstace.java
pieceImageProtos = dict(
    Box=_proto(name=str, location=str, fgColor=rgbColor, borderColor=rgbColor),
    Image=_proto(name=str, location=str, imageName=str),
    Symbol=_proto(
        name=str, location=str, fgColor=rgbColor, bgColor=rgbColor, size=str,
        symbol1=str, symbol2=str, sizeColor=rgbColor
    ),
    Text=_proto(
        name=str, location=str, fgColor=rgbColor, bgColor=rgbColor,
        value=str, outlineCoolor=rgbColor
    ),
    TextBox=_proto(name=str, location=str, fgColor=rgbColor, bgColor=rgbColor, value=str)
)


def parsePieceLayout(s):
    items = []
    for spec in disconcat(s, ','):
        deriv, base = disconcat(spec, '|')
        typ, val = disconcat(deriv, ';', 1)
        item = dict(kind=typ)
        if typ not in pieceLayoutProtos:
            item['spec'] = spec
        else:
            item.update(pieceLayoutProtos['Item'](base))
            item.update(pieceLayoutProtos[typ](val))
        items.append(item)
    return items


def parsePieceImage(s):
    items = []
    for spec in disconcat(s, ','):
        typ, val = disconcat(spec, ';', 1)
        item = dict(kind=typ)
        if typ not in pieceImageProtos:
            item['spec'] = spec
        else:
            item.update(pieceImageProtos[typ](val))
        items.append(item)
    return items


testLayouts = [
    r"Symbol;27;21;1.0|Symbol;Center;0;-2;0;true,Text;Stats;center;Command;;67\,130;76\,520;76\,130;false|Stats;Bottom;0;0;0;true,Text;Id;center;Command;;67\,130;76\,520;76\,130;false|Id;Bottom;0;0;270;true,Text;Loc;left;Command;;67\,130;76\,520;76\,130;false|Loc;Top Left;4;0;0;true",
    r"Symbol;27;21;1.0|Symbol0;Center;0;-4;0;true,Text;Stats;center;Fixed;1-7;;;;false|Stats;Bottom;0;-3;0;true,Text;IdPlain;center;Fixed;STAVKA;;;76\,130;false|Id;Bottom;0;0;270;true,Text;Loc;left;Fixed;C;;;;false|Loc;Top Left;-10;0;0;true,Text;Loc;center;Fixed;HQ;;;;false|HQ;Center;0;-4;0;true",
    r"Box;27;21;Rectangle;5|Shape4;Center;0;-4;0;true,Text;Stats;center;Fixed;1-0;;;;false|Stats;Bottom;0;-4;0;true,Text;IdPlain;center;Variable;;;;;false|Id;Bottom;0;0;270;true,Image;;Variable|Image3;Center;0;-3;0;true",
]

testPieces = [
    r"Symbol;Symbol0;Center;BLACK;CLEAR;Army Group;None;None;BLACK,Text;Stats;Bottom;BLACK;CLEAR;1-7;,Text;Id;Bottom;BLACK;CLEAR;STAVKA;,Text;Loc;Top Left;BLUE;CLEAR;C;,Text;HQ;Center;BLACK;CLEAR;HQ;",
    r"Box;Shape4;Center;CLEAR;BLACK,Text;Stats;Bottom;BLACK;CLEAR;St;,Text;Id;Bottom;BLACK;CLEAR;STALIN;,Image;Image3;Center;hammer.png",
]


print("** test layouts **")
for layout in testLayouts:
    print(json.dumps(parsePieceLayout(layout), indent=4))

print("** test pieces **")
for piece in testPieces:
    print(json.dumps(parsePieceImage(piece), indent=4))

"""
VASSAL.build.module.gamepieceimage.GamePieceImage @props
Symbol;Symbol;Center;ru-fg;CLEAR;Corps;Infantry;Airborne;ru-fg,Text;Stats;Bottom;ru-fg;CLEAR;1-2;,Text;Id;Bottom;ru-fg;CLEAR;4;,Text;Loc;Top Left;BLACK;CLEAR;3;

VASSAL.build.module.gamepieceimage.GamePieceLayout @layout
VASSAL.build.module.gamepieceimage.GamePieceImage
Symbol;27;21;1.0|Symbol;Center;0;-2;0;true,Text;Stats;center;Command;;67\,130;76\,520;76\,130;false|Stats;Bottom;0;0;0;true,Text;Id;center;Command;;67\,130;76\,520;76\,130;false|Id;Bottom;0;0;270;true,Text;Loc;left;Command;;67\,130;76\,520;76\,130;false|Loc;Top Left;4;0;0;true

VASSAL.build.module.gamepieceimage.Item

SymbolItem width:int;height:int;lineWidth:float|
TextBoxItem width:int;height:int;isHTML:bool, <= bug?
TextItem fontStyleName:str;textSource:str;text:str;changeCmd:str;changeKey:keyStroke;
            lockCmd:str;lockKey:keyStroke;lockable:boolean|
ImageItem imageName:str;imageSource:str|
ShapeItem width:int;height:int;shape:str;bevel:int  # aka Box

    Item name:str;location:str;xoffset:int;yoffset:int;rotation:int;antialias:bool


ImageItemInstance: type:str;name:str;location:str;imageName:str
TextItemInstance: type:str;name:str;location:str;fgColor:rgbColor;bgColor:rgbColor;value:str;outlineCoolor:rgbColor
TextBoxItemInstance: type:str;name:str;location:str;fgColor:rgbColor;bgColor:rgbColor;value:str
ShapeItemInstance: type:str;name:str;location:str;fgColor:rgbColor;borderColor:rgbColor
SymbolItemInstance: type:str;name:str;location:str;fgColor:rgbColor;bgColor:rgbColor;size:str;symbol1:str;symbol2:str;sizeColor:rgbColor

GamePieceLayout  @layout
    Box;27;21;Rectangle;5|Shape4;Center;0;-4;0;true,
    Text;Stats;center;Fixed;1-0;;;;false|Stats;Bottom;0;-4;0;true,
    Text;IdPlain;center;Variable;;;;;false|Id;Bottom;0;0;270;true,
    Image;;Variable|Image3;Center;0;-3;0;true

GamePieceImage bgColor="ge-bg" borderColor="BLACK" name="Hitler" @props
    Box;Shape4;Center;CLEAR;BLACK,
    Text;Stats;Bottom;BLACK;CLEAR;1-0;,
    Text;Id;Bottom;BLACK;CLEAR;HITLER;,
    Image;Image3;Center;swastika.png
"""
