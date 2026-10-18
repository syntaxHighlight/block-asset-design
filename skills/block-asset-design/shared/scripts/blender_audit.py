#!/usr/bin/env python3
"""Blender adapter: read-only inventory and geometry/UV snapshot diagnostics."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import mesh_checks


from blender_objects import choose_objects


def inventory(bpy, objects):
    entries = []
    for obj in objects:
        drivers = []
        for owner in (obj, obj.data):
            animation = getattr(owner, 'animation_data', None)
            for curve in animation.drivers if animation else []:
                drivers.append({'path': curve.data_path, 'valid': curve.driver.is_valid,
                                'missing_targets': [v.name for v in curve.driver.variables for t in v.targets if t.id is None and v.type != 'CONTEXT_PROP']})
        constraints = [{'name': c.name, 'type': c.type, 'muted': c.mute, 'missing_target': hasattr(c, 'target') and c.target is None} for c in obj.constraints]
        images = []
        for slot in obj.material_slots:
            mat = slot.material
            if mat and mat.use_nodes:
                for node in mat.node_tree.nodes:
                    if node.type == 'TEX_IMAGE':
                        im = node.image
                        images.append({'node': node.name, 'image': im.name if im else None,
                                       'packed': bool(im.packed_file) if im else False,
                                       'path': im.filepath if im else None,
                                       'available': (bool(im.packed_file) or im.source in ('GENERATED','VIEWER') or Path(bpy.path.abspath(im.filepath)).is_file()) if im and im.source not in ('TILED','SEQUENCE') else None})
        entries.append({'name': obj.name, 'type': obj.type, 'parent': obj.parent.name if obj.parent else None,
                        'hidden_render': obj.hide_render, 'hidden_viewport': obj.hide_get(),
                        'uv_layers': [{'name': uv.name, 'active_render': uv.active_render} for uv in obj.data.uv_layers] if obj.type == 'MESH' else [],
                        'modifiers': [{'name': m.name, 'type': m.type, 'viewport': m.show_viewport, 'render': m.show_render} for m in obj.modifiers],
                        'constraints': constraints, 'drivers': drivers, 'images': images})
    return {'version': 1, 'status': 'inventory', 'blend': bpy.data.filepath, 'frame': bpy.context.scene.frame_current,
            'blender_version': bpy.app.version_string, 'objects': entries,
            'limitations': ['Does not execute embedded scripts, inspect arbitrary script references, or interpret all shader node groups.']}


def snapshot(bpy, objects, uv_layer=None, evaluated=False, instances=False):
    if instances and not evaluated: raise ValueError('instances require --evaluated')
    if bpy.context.mode != 'OBJECT': raise ValueError('switch to Object Mode so mesh data is synchronized')
    depsgraph = bpy.context.evaluated_depsgraph_get()
    records, skipped = [], []
    selected = {o.name for o in objects}
    source = []
    if instances:
        for item in depsgraph.object_instances:
            original = item.object.original
            parent = item.parent.original if item.parent else None
            if original.name in selected or (parent and parent.name in selected):
                source.append((item.object, item.matrix_world.copy(), f'{original.name}@{len(source)}', original))
    else:
        source = [(o.evaluated_get(depsgraph) if evaluated else o, o.matrix_world.copy(), o.name, o) for o in objects]
    for obj, matrix, name, original in source:
        if obj.type != 'MESH':
            skipped.append({'object': name, 'reason': 'not a mesh; convert explicitly if relevant'})
            continue
        temporary = False
        try:
            if evaluated:
                mesh = obj.to_mesh(preserve_all_data_layers=True, depsgraph=depsgraph); temporary = True
            else: mesh = obj.data
            mesh.calc_loop_triangles()
            layer = mesh.uv_layers.get(uv_layer) if uv_layer else None
            verts = [list(matrix @ v.co) for v in mesh.vertices]
            faces = [{'vertices': list(p.vertices)} for p in mesh.polygons]
            triangles = []
            for t in mesh.loop_triangles:
                tri = {'vertices': list(t.vertices), 'face': t.polygon_index}
                if layer: tri['uv'] = [list(layer.data[li].uv) for li in t.loops]
                triangles.append(tri)
            record = {'id': name, 'vertices': verts, 'faces': faces, 'triangles': triangles}
            if 'md_grid_step' in original: record['grid_step'] = float(original['md_grid_step'])
            records.append(record)
        except Exception as error:
            skipped.append({'object': name, 'reason': str(error)})
        finally:
            if temporary: obj.to_mesh_clear()
    data = {'meshes': records, 'skipped': skipped,
            'scope': {'blend': bpy.data.filepath, 'frame': bpy.context.scene.frame_current,
                      'blender_version': bpy.app.version_string, 'objects': sorted(selected), 'evaluated': evaluated,
                      'instances': instances, 'uv_layer': uv_layer, 'coordinates': 'world', 'uv_domain': 'explicit selected common atlas'}}
    data['scope']['snapshot_sha256'] = hashlib.sha256(json.dumps(records, sort_keys=True).encode()).hexdigest()
    return data


def main():
    import bpy
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--mode', choices=['inventory', 'geometry', 'uv', 'all'], required=True)
    p.add_argument('--objects', nargs='+'); p.add_argument('--collection'); p.add_argument('--uv-layer')
    p.add_argument('--evaluated', action='store_true'); p.add_argument('--instances', action='store_true')
    p.add_argument('--frame', type=int); p.add_argument('--grid', type=float)
    p.add_argument('--origin', type=float, nargs=3, default=(0,0,0)); p.add_argument('--size', type=int, nargs=2, default=(1024,1024))
    p.add_argument('--density', type=float); p.add_argument('--epsilon', type=float, default=1e-6)
    p.add_argument('--stretch', type=float, default=1.05); p.add_argument('--density-tolerance', type=float, default=.05)
    p.add_argument('--pixel-tolerance', type=float, default=.01); p.add_argument('--max-pairs', type=int, default=200000)
    p.add_argument('--output', type=Path, required=True); p.add_argument('--snapshot-output', type=Path)
    args = p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    if args.mode in ('uv', 'all') and not args.uv_layer: p.error('--uv-layer is required for UV checks')
    for path in (args.output, args.snapshot_output):
        if path and path.exists(): p.error('output exists: '+str(path))
    if args.snapshot_output and args.snapshot_output.resolve() == args.output.resolve(): p.error('outputs must differ')
    objects = choose_objects(bpy, args.objects, args.collection)
    frame, subframe = bpy.context.scene.frame_current, bpy.context.scene.frame_subframe
    try:
        if args.frame is not None: bpy.context.scene.frame_set(args.frame)
        if args.mode == 'inventory': report = inventory(bpy, objects)
        else:
            data = snapshot(bpy, objects, args.uv_layer, args.evaluated, args.instances)
            if not data['meshes']: raise ValueError('no readable meshes in selected scope')
            report = mesh_checks.audit(data, mode=args.mode, epsilon=args.epsilon, grid=args.grid, origin=args.origin,
                                       size=args.size, density=args.density, density_tolerance=args.density_tolerance,
                                       stretch=args.stretch, pixel_tolerance=args.pixel_tolerance, max_pairs=args.max_pairs)
            if args.snapshot_output:
                args.snapshot_output.parent.mkdir(parents=True, exist_ok=True)
                args.snapshot_output.write_text(json.dumps(data, allow_nan=False)+'\n')
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
        print('AUDIT', report['status'], args.output)
    finally:
        if args.frame is not None: bpy.context.scene.frame_set(frame, subframe=subframe)


if __name__ == '__main__': main()
