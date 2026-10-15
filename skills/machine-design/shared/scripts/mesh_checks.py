#!/usr/bin/env python3
"""Read-only geometry/UV diagnostics on Blender snapshots; Python stdlib only."""
import argparse
import json
import math
from collections import defaultdict
from pathlib import Path
from mesh_math import sub, dot, cross, norm, area, intersection_area, singular_values



class Findings:
    def __init__(self, limit):
        self.limit = limit
        self.items = {}

    def touch(self, key):
        return self.items.setdefault(key, {'status': 'checked', 'count': 0, 'samples': []})

    def add(self, key, item):
        entry = self.touch(key)
        entry['count'] += 1
        entry['status'] = 'candidates'
        if len(entry['samples']) < self.limit: entry['samples'].append(item)

    def incomplete(self, key, reason):
        entry = self.touch(key)
        entry['status'] = 'incomplete'
        entry['reason'] = reason


def candidate_pairs(items, dimensions, tolerance, budget, stats):
    """Sweep AABBs, including all tested active pairs in the budget."""
    bounds = [(tuple(min(p[k] for p in item['p']) for k in range(dimensions)),
               tuple(max(p[k] for p in item['p']) for k in range(dimensions)), i)
              for i, item in enumerate(items)]
    active = []
    for low, high, idx in sorted(bounds):
        active = [v for v in active if v[1][0]+tolerance >= low[0]]
        for other_low, other_high, other_idx in active:
            if stats['pairs_examined'] >= budget:
                stats['complete'] = False
                return
            stats['pairs_examined'] += 1
            if all(other_high[k]+tolerance >= low[k] and high[k]+tolerance >= other_low[k]
                   for k in range(dimensions)):
                yield other_idx, idx
        active.append((low, high, idx))



def audit(snapshot, mode='all', epsilon=1e-6, grid=None, origin=(0, 0, 0),
          size=(1024, 1024), density=None, density_tolerance=.05,
          stretch=1.05, pixel_tolerance=.01, max_pairs=200000, max_samples=100):
    if mode not in ('all', 'geometry', 'uv'): raise ValueError('invalid mode')
    if epsilon <= 0 or not math.isfinite(epsilon): raise ValueError('epsilon must be positive')
    if grid is not None and (grid <= 0 or not math.isfinite(grid)): raise ValueError('grid must be positive')
    if len(size) != 2 or min(size) <= 0: raise ValueError('positive image dimensions required')
    if density is not None and (density <= 0 or not math.isfinite(density)): raise ValueError('density must be positive')
    if max_pairs < 1 or max_samples < 1 or stretch < 1 or min(density_tolerance, pixel_tolerance) < 0:
        raise ValueError('invalid tolerance or budget')
    found = Findings(max_samples)
    geom = mode in ('all', 'geometry')
    uvs = mode in ('all', 'uv')
    geom_tris, uv_tris, density_values = [], [], []
    for key in (['degenerate_faces', 'nonplanar_faces', 'boundary_edges', 'nonmanifold_edges',
                 'winding_conflicts', 'coplanar_overlap'] if geom else []): found.touch(key)
    if geom and grid: found.touch('off_grid_vertices')
    for key in (['missing_uv', 'uv_out_of_bounds', 'uv_off_pixel', 'uv_degenerate', 'uv_overlap', 'uv_stretch'] if uvs else []): found.touch(key)
    if uvs and density: found.touch('uv_density')
    for mesh in snapshot['meshes']:
        verts = mesh['vertices']
        if any(len(p) != 3 or not all(math.isfinite(x) for x in p) for p in verts):
            raise ValueError('nonfinite or invalid vertex')
        name = mesh['id']
        if geom:
            step = mesh.get('grid_step', grid)
            if step is not None:
                if step <= 0 or not math.isfinite(step): raise ValueError('invalid object grid step')
                found.touch('off_grid_vertices')
                for vi, v in enumerate(verts):
                    residual = max(abs((v[k]-origin[k])-round((v[k]-origin[k])/step)*step) for k in range(3))
                    if residual > epsilon: found.add('off_grid_vertices', {'mesh': name, 'vertex': vi, 'distance': residual, 'step': step})
            edges = defaultdict(list)
            for fi, face in enumerate(mesh['faces']):
                idx = face['vertices']; points = [verts[v] for v in idx]
                for a, b in zip(idx, idx[1:]+idx[:1]): edges[tuple(sorted((a, b)))].append((fi, a < b))
                n = (0., 0., 0.)
                if len(points) >= 3:
                    vectors = [cross(sub(points[i], points[0]), sub(points[i+1], points[0])) for i in range(1, len(points)-1)]
                    n = tuple(sum(v[k] for v in vectors) for k in range(3))
                if norm(n) <= epsilon**2:
                    found.add('degenerate_faces', {'mesh': name, 'face': fi})
                else:
                    distance = max(abs(dot(sub(p, points[0]), n))/norm(n) for p in points)
                    if distance > epsilon: found.add('nonplanar_faces', {'mesh': name, 'face': fi, 'distance': distance})
            for edge, uses in edges.items():
                info = {'mesh': name, 'edge': edge, 'faces': [x[0] for x in uses]}
                if len(uses) == 1: found.add('boundary_edges', info)
                elif len(uses) > 2: found.add('nonmanifold_edges', info)
                elif uses[0][1] == uses[1][1]: found.add('winding_conflicts', info)
        for ti, tri in enumerate(mesh['triangles']):
            p = [verts[i] for i in tri['vertices']]
            identity = {'mesh': name, 'face': tri['face'], 'triangle': ti}
            if geom and norm(cross(sub(p[1], p[0]), sub(p[2], p[0]))) > epsilon**2:
                geom_tris.append(dict(identity, p=p))
            if not uvs: continue
            uv = tri.get('uv')
            if uv is None:
                found.add('missing_uv', identity)
                continue
            if any(len(q) != 2 or not all(math.isfinite(x) for x in q) for q in uv): raise ValueError('invalid UV')
            pixel = [[q[k]*size[k] for k in range(2)] for q in uv]
            if any(v < -epsilon or v > 1+epsilon for q in uv for v in q): found.add('uv_out_of_bounds', identity)
            if any(abs(v-round(v)) > pixel_tolerance for q in pixel for v in q): found.add('uv_off_pixel', identity)
            if area(pixel) <= 1e-12: found.add('uv_degenerate', identity)
            else: uv_tris.append(dict(identity, p=pixel, domain=tri.get('uv_domain', mesh.get('uv_domain', 'selected-atlas'))))
            sv = singular_values(p, pixel)
            if sv is not None:
                lo, hi = sv
                density_values.extend(sv)
                if lo <= 1e-12 or hi/lo > stretch:
                    found.add('uv_stretch', dict(identity, min_density=lo, max_density=hi, ratio=hi/lo if lo > 1e-12 else None))
                if density and max(abs(lo/density-1), abs(hi/density-1)) > density_tolerance:
                    found.add('uv_density', dict(identity, min_density=lo, max_density=hi, target=density))
    budgets = {}
    if geom:
        stats = {'pairs_examined': 0, 'complete': True}
        for i, j in candidate_pairs(geom_tris, 3, epsilon, max_pairs, stats):
            a, b = geom_tris[i], geom_tris[j]
            if a['mesh'] == b['mesh'] and a['face'] == b['face']: continue
            pa, pb = a['p'], b['p']
            na = cross(sub(pa[1], pa[0]), sub(pa[2], pa[0])); nb = cross(sub(pb[1], pb[0]), sub(pb[2], pb[0]))
            cosine = dot(na, nb)/(norm(na)*norm(nb))
            if abs(cosine) < 1-1e-8: continue
            if max(abs(dot(sub(p, pa[0]), na))/norm(na) for p in pb) > epsilon: continue
            axis = max(range(3), key=lambda k: abs(na[k])); keep = [k for k in range(3) if k != axis]
            overlap = intersection_area([tuple(p[k] for k in keep) for p in pa], [tuple(p[k] for k in keep) for p in pb])
            if overlap > epsilon**2:
                found.add('coplanar_overlap', {'a': {k: a[k] for k in ('mesh', 'face', 'triangle')}, 'b': {k: b[k] for k in ('mesh', 'face', 'triangle')}, 'orientation': 'same' if cosine > 0 else 'opposite', 'projected_area': overlap})
        if not stats['complete']: found.incomplete('coplanar_overlap', 'pair budget exhausted')
        budgets['geometry'] = stats
    if uvs:
        stats = {'pairs_examined': 0, 'complete': True}
        for i, j in candidate_pairs(uv_tris, 2, 0., max_pairs, stats):
            a, b = uv_tris[i], uv_tris[j]
            if a['domain'] != b['domain']: continue
            overlap = intersection_area(a['p'], b['p'])
            if overlap > 1e-8:
                found.add('uv_overlap', {'a': {k: a[k] for k in ('mesh', 'face', 'triangle')}, 'b': {k: b[k] for k in ('mesh', 'face', 'triangle')}, 'area_pixels': overlap})
        if not stats['complete']: found.incomplete('uv_overlap', 'pair budget exhausted')
        budgets['uv'] = stats
    skipped = snapshot.get('skipped', [])
    complete = not skipped and all(s['complete'] for s in budgets.values()) and not found.items.get('missing_uv', {}).get('count', 0)
    return {'version': 1, 'status': 'incomplete' if not complete else ('candidates' if any(x['count'] for x in found.items.values()) else 'checked'),
            'scope': snapshot.get('scope', {}), 'skipped': skipped, 'budgets': budgets,
            'settings': dict(mode=mode, epsilon=epsilon, grid=grid, origin=origin, image_size=size, density=density, stretch=stretch, density_tolerance=density_tolerance, pixel_tolerance=pixel_tolerance),
            'checks': found.items, 'density_range': [min(density_values), max(density_values)] if density_values else None,
            'limitations': ['Candidates require semantic/visual review.', 'No volumetric collision, noncoplanar intersection or continuous sweep checks.', 'UV checks use the explicitly selected raw layer and atlas domain, not shader transformations.', 'Diagnostic indices belong to this snapshot; evaluated indices may not map to source geometry.']}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
    p.add_argument('--mode', choices=['geometry', 'uv', 'all'], default='all')
    p.add_argument('--grid', type=float); p.add_argument('--origin', type=float, nargs=3, default=(0,0,0))
    p.add_argument('--size', type=int, nargs=2, default=(1024,1024)); p.add_argument('--density', type=float)
    p.add_argument('--epsilon', type=float, default=1e-6); p.add_argument('--max-pairs', type=int, default=200000)
    a = p.parse_args()
    if a.output.exists(): p.error('output exists; use a new report path')
    report = audit(json.loads(a.input.read_text()), mode=a.mode, grid=a.grid, origin=a.origin, size=a.size, density=a.density, epsilon=a.epsilon, max_pairs=a.max_pairs)
    a.output.parent.mkdir(parents=True, exist_ok=True); a.output.write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    print(report['status'])


if __name__ == '__main__': main()
