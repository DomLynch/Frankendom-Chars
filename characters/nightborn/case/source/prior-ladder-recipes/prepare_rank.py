"""Prepare a rank-specific build from the accepted pilot recipe; does not submit work."""
from pathlib import Path
import sys,json
R=Path(__file__).resolve().parents[1]
rank=int(sys.argv[1]);assert rank in range(2,11)
s=(R/'source/build_pilot_v8.py').read_text()
s=s.replace('L8',f'L{rank}').replace('pilot-v8/',f'ladder/L{rank}/')
s=s.replace("zmin=min((donor.matrix_world@v.co).z for v in donor.data.vertices)","""world_points=[donor.matrix_world@v.co for v in donor.data.vertices]
zmin=min(p.z for p in world_points)
import statistics
armheight=statistics.median(p.z for p in world_points if .28<abs(p.x)<.38)-zmin
scale=1.90*.7818291/armheight
assert 1.6<scale<2.3, ('unexpected reference proportions',scale)
print('CALIBRATED SCALE',scale,flush=True)""")
s=s.replace('p*=1.90;p.z-=zmin*1.90','p*=scale;p.z-=zmin*scale').replace("'donor_scale':1.90","'donor_scale':scale")
colours={2:((.12,.045,.018),0,.67),3:((.43,.32,.19),0,.65),4:((.42,.14,.055),.8,.4),5:((.35,.22,.067),.8,.42),6:((.12,.13,.14),.75,.46),7:((.32,.35,.38),.9,.32),8:((.024,.020,.023),.65,.42),9:((.018,.115,.05),.75,.34),10:((.57,.32,.065),.85,.30)}
c,metal,rough=colours[rank]
s=s.replace("material('Aged blackened steel',(.024,.020,.023),.65,.42)",f"material('L{rank} crown metal',{c!r},{metal},{rough})")
if rank==9:s=s.replace("(.19,.006,.014),.22,.20","(.003,.12,.025),.22,.20")
if rank==10:s=s.replace("(.018,.004,.006),0,.65","(.57,.32,.065),.85,.30")
if rank<=3:
 s=s.replace("for m in donor.data.materials:","for mat in donor.data.materials:\n shader=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')\n for link in list(shader.inputs['Metallic'].links):mat.node_tree.links.remove(link)\n shader.inputs['Metallic'].default_value=0\nfor m in donor.data.materials:")
# Crown silhouettes are authored against the unchanged original head.
a=s.index('for side in [-1,1]:');b=s.index('for x,z,size in ',a)
if rank!=8:
 count={2:0,3:2,4:3,5:5,6:3,7:4,9:5,10:7}[rank]
 crown=f'''# Rank {rank}: distinct open crown geometry, no face cover.
for i in range({count}):
 a=math.pi+(i+1)*math.pi/({count}+1)
 x=.120*math.cos(a);y=-.05+.132*math.sin(a)
 height={.035 if rank<6 else .05 if rank<8 else .095 if rank==9 else .13}*(.65+.35*(1-abs(x)/.12))
 width={.011 if rank<6 else .015 if rank<9 else .021}
 verts=[(x-width,y-.008,1.808),(x+width,y-.008,1.808),(x+width,y+.006,1.812),(x-width,y+.006,1.812),(x*{1.35 if rank==9 else 1.10},y+{.02 if rank==9 else 0},1.812+height)]
 me=bpy.data.meshes.new('Crown leaf');me.from_pydata(verts,[],[(0,1,4),(1,2,4),(2,3,4),(3,0,4),(0,3,2,1)]);o=bpy.data.objects.new('L{rank}_CrownLeaf',me);bpy.context.collection.objects.link(o);o.data.materials.append(steel);bind(o,'Head')
'''
 s=s[:a]+crown+s[b:]
if rank<8:
 a=s.index('for x,z,size in ');b=s.index('for m in donor.data.materials:',a)
 # retain material adjustment for leather/bone inserted immediately before this section
 patch=''
 if rank<=3:patch="for mat in donor.data.materials:\n shader=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')\n for link in list(shader.inputs['Metallic'].links):mat.node_tree.links.remove(link)\n shader.inputs['Metallic'].default_value=0\n"
 s=s[:a]+patch+s[b:]
path=R/f'source/build-L{rank}.py';compile(s,str(path),'exec');path.write_text(s);print(path)
