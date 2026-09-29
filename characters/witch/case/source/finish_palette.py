"""Keep L8 visibly blackened under the shared neutral studio lighting."""

import sys
from pack_preserved import read, write

source, dest = sys.argv[1:3]
g, b = read(source)
node = next(n for n in g["nodes"] if n.get("name") == "Witch_L8_Armour")
for prim in g["meshes"][node["mesh"]]["primitives"]:
    material = g["materials"][prim["material"]]
    material["pbrMetallicRoughness"]["baseColorFactor"] = [0.42, 0.42, 0.42, 1]
    material["emissiveFactor"] = [0, 0, 0]
write(dest, g, b)
