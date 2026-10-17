#!/usr/bin/env python3
"""Export authored UV charts; apply verified atlas UVs into an explicitly named layer."""
import argparse
import hashlib
import json
import math
import statistics
import sys
from pathlib import Path
# Release packages keep the checks beside texture; source checkouts retain skills/.
_script_dir = Path(__file__).resolve().parent
_checks_dir = _script_dir.parent / 'checks'
if not _checks_dir.is_dir():
    _checks_dir = _script_dir.parents[1] / 'machine-design/shared/scripts'
sys.path.insert(0, str(_checks_dir))
from blender_objects import choose_objects
from mesh_math import sub, cross, norm, singular_values


def fingerprint(obj, layer_name):
    mesh=obj.data; layer=mesh.uv_layers.get(layer_name)
    if not layer: raise ValueError('source UV layer missing: '+obj.name)
    data={'vertices':[list(v.co) for v in mesh.vertices], 'polygons':[list(p.vertices) for p in mesh.polygons],
          'uv':[list(v.uv) for v in layer.data], 'matrix':[list(row) for row in obj.matrix_world],
          'materials':[p.material_index for p in mesh.polygons],
          'attributes':{name:[getattr(d,'value',None) for d in mesh.attributes[name].data]
                        for name in ('md_edge_role','md_material_role') if name in mesh.attributes},
          'roles':obj.get('md_role_names',None)}
    return hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest()


def export(bpy, objects, layer_name, density, source_size, padding, default_role=None, tolerance=.05):
    if bpy.context.mode!='OBJECT': raise ValueError('Object Mode required')
    if not objects or density<=0 or not math.isfinite(density) or min(source_size)<=0 or padding<2: raise ValueError('invalid scope/density/size/padding')
    meshes={}; charts=[]; bindings={}; seen=set()
    for obj in objects:
        if obj.type!='MESH': raise ValueError('export only explicit mesh objects: '+obj.name)
        mesh=obj.data
        if mesh.as_pointer() in seen: raise ValueError('linked mesh instances need an explicit shared layout or single-user source')
        seen.add(mesh.as_pointer())
        if any(m.show_viewport for m in obj.modifiers): raise ValueError('export uses source topology; resolve active modifiers into a deliberate editable/export source first: '+obj.name)
        uv=mesh.uv_layers.get(layer_name)
        if not uv: raise ValueError('source UV missing: '+obj.name)
        edge_role=mesh.attributes.get('md_edge_role'); face_role=mesh.attributes.get('md_material_role')
        if edge_role and (edge_role.domain!='EDGE' or edge_role.data_type!='INT'): raise ValueError('md_edge_role must be EDGE INT')
        if face_role and (face_role.domain!='FACE' or face_role.data_type!='INT'): raise ValueError('md_material_role must be FACE INT')
        role_names=json.loads(obj.get('md_role_names','{}'))
        if not face_role and not default_role: raise ValueError('provide face roles or --default-role explicitly')
        mesh.calc_loop_triangles()
        by_face={p.index:[] for p in mesh.polygons}
        scales=[]
        for tri in mesh.loop_triangles:
            by_face[tri.polygon_index].append(list(tri.loops))
            xyz=[list(obj.matrix_world @ mesh.vertices[v].co) for v in tri.vertices]
            coords=[[uv.data[li].uv[k]*source_size[k] for k in (0,1)] for li in tri.loops]
            sv=singular_values(xyz,coords)
            if sv is None or min(sv)<=1e-12: raise ValueError('degenerate geometry or UV')
            scales.extend(sv)
        if not scales: raise ValueError('mesh has no surface')
        source_density=statistics.median(scales)
        if max(abs(x/source_density-1) for x in scales)>tolerance: raise ValueError('source UV density/stretch exceeds tolerance; inspect before export: '+obj.name)
        factor=density/source_density
        points={li:[uv.data[li].uv[0]*source_size[0]*factor,-uv.data[li].uv[1]*source_size[1]*factor] for li in range(len(mesh.loops))}
        parent=list(range(len(mesh.polygons)))
        def find(x):
            while parent[x]!=x:
                parent[x]=parent[parent[x]]; x=parent[x]
            return x
        edge_uses={}
        for p in mesh.polygons:
            loops=list(p.loop_indices)
            for li,lj in zip(loops,loops[1:]+loops[:1]):
                edge_uses.setdefault(mesh.loops[li].edge_index,[]).append((p.index,{mesh.loops[li].vertex_index:li,mesh.loops[lj].vertex_index:lj}))
        for uses in edge_uses.values():
            if len(uses)!=2: continue
            (a,la),(b,lb)=uses
            if la.keys()==lb.keys() and all((uv.data[la[v]].uv-uv.data[lb[v]].uv).length<1e-7 for v in la): parent[find(a)]=find(b)
        groups={}
        for p in mesh.polygons: groups.setdefault(find(p.index),[]).append(p)
        meshes[obj.name]={'loops':len(mesh.loops)}
        bindings[obj.name]={'fingerprint':fingerprint(obj,layer_name),'source_uv':layer_name}
        for group in groups.values():
            all_loops=[li for p in group for li in p.loop_indices]
            offset=[min(points[li][k] for li in all_loops) for k in (0,1)]
            local={li:[points[li][k]-offset[k] for k in (0,1)] for li in all_loops}
            faces=[]; edges=[]
            for p in group:
                loops=list(p.loop_indices); xyz=[list(obj.matrix_world @ mesh.vertices[mesh.loops[li].vertex_index].co) for li in loops]
                tri=by_face[p.index][0]; xyz_tri=[list(obj.matrix_world @ mesh.vertices[mesh.loops[li].vertex_index].co) for li in tri]
                n=cross(sub(xyz_tri[1],xyz_tri[0]),sub(xyz_tri[2],xyz_tri[0])); n=[v/norm(n) for v in n]
                role=role_names.get(str(face_role.data[p.index].value)) if face_role else default_role
                if not role: raise ValueError('unmapped material role')
                if role in ('artwork','glass'): raise ValueError('preserve artwork/glass separately; the generic exporter cannot reconstruct their source material')
                faces.append({'id':p.index,'loops':loops,'xy':[local[li] for li in loops], 'xyz':xyz,'normal':n,'role':role,
                              'triangles':[[loops.index(li) for li in t] for t in by_face[p.index]]})
                for li,lj in zip(loops,loops[1:]+loops[:1]):
                    ei=mesh.loops[li].edge_index; value=edge_role.data[ei].value if edge_role else 0
                    if value not in (0,1,2): raise ValueError('edge role must be 0,1,2')
                    if not value: continue
                    uses=edge_uses[ei]
                    if len(uses)==2 and p.index!=min(u[0] for u in uses): continue
                    length=math.dist(local[li],local[lj])
                    # Conservative width estimate; narrow faces may intentionally suppress a stroke.
                    world_by_loop=dict(zip(loops,xyz))
                    world_area=0.
                    for t in by_face[p.index]:
                        x,y,z=(world_by_loop[k] for k in t)
                        world_area+=norm(cross(sub(y,x),sub(z,x)))/2
                    width=2*world_area*density*density/max(length,1e-9)
                    edges.append({'id':ei,'face':p.index,'role':value,'xy':[local[li],local[lj]],'length_px':length,'surface_width_px':width})
            charts.append({'id':obj.name+':'+str(group[0].index),'mesh':obj.name,'object':obj.name,'faces':faces,'edges':edges})
    return {'version':1,'pixels_per_unit':density,'padding_px':padding,'meshes':meshes,'charts':charts,
            'bindings':bindings,'source_uv':layer_name,'source_size':source_size}


def apply(bpy, spec, layout, target_layer, output, replace_target=False):
    if bpy.context.mode!='OBJECT': raise ValueError('Object Mode required')
    if not target_layer: raise ValueError('target layer required')
    output=Path(output)
    if output.suffix.lower()!='.blend' or output.exists() or (bpy.data.filepath and output.resolve()==Path(bpy.data.filepath).resolve()):
        raise ValueError('save to a NEW .blend path; source is never overwritten')
    if layout.get('input_sha256')!=hashlib.sha256(json.dumps(spec,sort_keys=True).encode()).hexdigest(): raise ValueError('layout does not belong to this input')
    pending=[]
    if set(layout['mesh_uv'])!=set(spec['bindings']): raise ValueError('layout object set mismatch')
    for name, binding in spec['bindings'].items():
        obj=bpy.context.scene.objects.get(name)
        if obj is None or obj.type!='MESH' or fingerprint(obj,binding['source_uv'])!=binding['fingerprint']:
            raise ValueError('source changed; re-export: '+name)
        if target_layer==binding['source_uv']: raise ValueError('target must differ from source UV')
        existing=obj.data.uv_layers.get(target_layer)
        if existing and not replace_target: raise ValueError('target exists; explicit --replace-target required')
        values=layout['mesh_uv'][name]
        if len(values)!=len(obj.data.loops) or any(len(p)!=2 or any(not math.isfinite(v) or not 0<=v<=1 for v in p) for p in values): raise ValueError('invalid UV output')
        pending.append((obj,existing,values))
    backups=[]
    try:
        for obj,existing,values in pending:
            old=[list(d.uv) for d in existing.data] if existing else None
            layer=existing if existing else obj.data.uv_layers.new(name=target_layer)
            backups.append((obj,layer,old))
            for datum, value in zip(layer.data,values): datum.uv=value
        output.parent.mkdir(parents=True,exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=str(output.resolve()),copy=True)
    except Exception:
        for obj,layer,old in reversed(backups):
            if old is None: obj.data.uv_layers.remove(layer)
            else:
                for datum,value in zip(layer.data,old): datum.uv=value
        raise
    print('Saved production UV layer to',output,'; explicitly connect this layer in the intended material before visual acceptance.')


def main():
    import bpy
    p=argparse.ArgumentParser(description=__doc__); subp=p.add_subparsers(dest='command',required=True)
    e=subp.add_parser('export'); e.add_argument('--objects',nargs='+'); e.add_argument('--collection')
    e.add_argument('--uv-layer',required=True); e.add_argument('--density',type=float,required=True)
    e.add_argument('--source-size',type=int,nargs=2,required=True); e.add_argument('--padding',type=int,default=3)
    e.add_argument('--default-role'); e.add_argument('--density-tolerance',type=float,default=.05); e.add_argument('--output',type=Path,required=True)
    a=subp.add_parser('apply'); a.add_argument('--input',type=Path,required=True); a.add_argument('--layout',type=Path,required=True)
    a.add_argument('--target-layer',required=True); a.add_argument('--output',type=Path,required=True); a.add_argument('--replace-target',action='store_true')
    args=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    if args.command=='export':
        if args.output.exists(): p.error('output exists')
        spec=export(bpy,choose_objects(bpy,args.objects,args.collection),args.uv_layer,args.density,args.source_size,args.padding,args.default_role,args.density_tolerance)
        args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps(spec,allow_nan=False)+'\n')
        print('Exported',len(spec['charts']),'charts')
    else: apply(bpy,json.loads(args.input.read_text()),json.loads(args.layout.read_text()),args.target_layer,args.output,args.replace_target)


if __name__=='__main__': main()
