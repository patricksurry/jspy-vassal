Experimental python tools for extracting [Vassal](http://www.vassalengine.org/)
module definitions and save files into more descriptive and hackable json formats,
with the goal of promoting further exploration and innovation that builds
on the amazing work of the Vassal community.
Perhaps it also provides some insight for understanding how the current codebase
works, and/or ideas for future evolution.

The information here is purely based on reverse-engineering
Vassal's serialization formats by inspecting the
[vassal engine source code](https://sourceforge.net/p/vassalengine/svn/HEAD/tree/VASSAL-src/trunk/).
None of the source code incorporated directly.

My initial goal is to mock up a very limited web-based map explorer for hex-based games.

Vassal module structure
===

A typical vassal module `foo.vmod` is a zipped archive,
containing some standard files and a bunch of module-specific data.

The `moduledata` (and similar `savedata`) file is an XML file with basic info about the module itself, e.g.:

    <?xml version="1.0" encoding="UTF-8"?>
    <data version="1">
      <version>1.3b06</version>
      <VassalVersion>3.2.17</VassalVersion>
      <dateSaved>1536337512302</dateSaved>
      <description>Minor Fixes</description>
      <name>TRC4</name>
    </data>

The `buildFile` is a more interesting XML file that specifies the module contents,
with pointers to the documentation, definitions for the game pices and map,
as well as module-specific plugins.   Images with a variety of formats (png, gif) and
sometimes lacking proper file extensions are commonly found in the `images/` folder.
(The [imagemagick identify](https://imagemagick.org/script/identify.php) command is
useful for inspecting these.)
Other subdirectories mainly seem to contain module-specific plugin code
(java classes without source).

The `info` file looks like some older version of the obfuscated save format,
but is not quite the same, with a different header and which doesn't obviously decode the same way.
A couple of examples are shown below, which share a common prefix but different trailing bytes:

    !VCSS162400110100010020BA6DB55D00208FA8FB010010D6A50010DE5900109E5F6057DF8373ECC6763F93A7A219F645835F482E5318C7BC70B206CC07A54156C753970F8B8F3382E5A1BF858E3E16763828BC8BB07E267B54354D299E61936588AD73288E74A26456429E6E52

    !VCSS162400110100010020BA6DB55D00208FA8FB010010D6A50010DE5900109E5F87BF0681138FD98B51AFEF6E54E90C2C9EE7899F3871CE6A7A5756E2A0F86D2253970F8B9D504C52A009559C594F694D619F156B80834F92560E86421762B2E77DAA688709F55AD07E267B54354D299E61936588AD73288E74A264565DD3542E

Documentation is normally stored in `*.htm` or `*.html` files.

Saved games are single-file zip archives containing a `savedGame` file.
Although there's no standard name for the archive file itself,
things like `*.sav`, `*.vsav`, `*.scen` seem common.
The game file within the archive is written in an obfuscated format (see `decoder.py`)
but is still not trivially decipherable after the obfuscation is removed :-)

The core principle in the save file is that objects are saved as serialized utf-8 data
fields separated by a delimiter character.
Apperances of the delimiter within the data are escaped with a backslash (`\`) character,
which makes it possible to serialize nested objects,
although the choice of delimiter also varies throughout the code base.
Commonly used delimiters are escape (`0x1b`), semicolon and comma.
The save file is not self-describing: we need the java source code to understand how to
interpret the serialized objects.
Backwards compatibility is supported by allowing most (all?) object fields to
be optional with default values, with new fields always appended to the serialized form.
My initial goal is to extract those objects to a more self-contained form,
by pulling out field name and type descriptions for the common objects found in the save files.



