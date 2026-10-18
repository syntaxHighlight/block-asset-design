#!/usr/bin/env python3
"""Render planar polygon regions with tiled or coordinate-generated materials. Requires Pillow.

python fill_regions.py --input regions.json --output preview-directory
Coordinates: model units, X right, Y down. Raster coverage uses pixel centers.
"""
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re

from PIL import Image, ImageDraw

_noise_spec = importlib.util.spec_from_file_location('material_noise', Path(__file__).with_name('material_noise.py'))
noise = importlib.util.module_from_spec(_noise_spec)
_noise_spec.loader.exec_module(noise)

EPS = 1e-8
MODES = {'none', 'outer', 'seam'}


def number(value, label, low=None, high=None):
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value):
        raise ValueError(f'{label}: expected a finite number')
    if (low is not None and value < low) or (high is not None and value > high):
        raise ValueError(f'{label}: outside allowed range {low}..{high}')
    return value


def integer(value, label, low, high):
    number(value, label, low, high)
    if int(value) != value:
        raise ValueError(f'{label}: expected an integer')
    return int(value)


def keys(obj, allowed, label):
    if not isinstance(obj, dict):
        raise ValueError(f'{label}: expected an object')
    extra = set(obj) - set(allowed)
    if extra:
        raise ValueError(f'{label}: unknown fields {sorted(extra)}')


def cross(a, b, c):
    return (b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0])


def on_segment(p, a, b):
    return abs(cross(a, b, p)) < EPS and all(min(a[i], b[i])-EPS <= p[i] <= max(a[i], b[i])+EPS for i in (0, 1))


def intersect(a, b, c, d):
    x, y, z, w = cross(a, b, c), cross(a, b, d), cross(c, d, a), cross(c, d, b)
    return ((x > EPS and y < -EPS or x < -EPS and y > EPS) and
            (z > EPS and w < -EPS or z < -EPS and w > EPS)) or any(
        on_segment(p, u, v) for p, u, v in ((a, c, d), (b, c, d), (c, a, b), (d, a, b)))


def segments(points):
    return list(zip(points, points[1:]+points[:1]))


def area(points):
    return sum(a[0]*b[1]-b[0]*a[1] for a, b in segments(points))/2


def inside(p, points):
    """Even/odd interior; boundary included, holes later subtract their boundary."""
    result = False
    for a, b in segments(points):
        if on_segment(p, a, b):
            return True
        if (a[1] > p[1]) != (b[1] > p[1]):
            at_x = a[0] + (p[1]-a[1])*(b[0]-a[0])/(b[1]-a[1])
            if p[0] < at_x:
                result = not result
    return result


def distance(p, a, b):
    dx, dy = b[0]-a[0], b[1]-a[1]
    t = max(0, min(1, ((p[0]-a[0])*dx+(p[1]-a[1])*dy)/(dx*dx+dy*dy)))
    return math.hypot(p[0]-a[0]-t*dx, p[1]-a[1]-t*dy)


def parse_ring(raw, density, label):
    keys(raw, ('points', 'edges', 'rivets'), label)
    values = raw.get('points')
    if not isinstance(values, list) or not 3 <= len(values) <= 256:
        raise ValueError(f'{label}: expected 3..256 points without repeated closing point')
    points = []
    for value in values:
        if not isinstance(value, list) or len(value) != 2:
            raise ValueError(f'{label}: each point must be [x, y]')
        points.append(tuple(number(v, label, -1e6, 1e6)*density for v in value))
    modes = raw.get('edges', ['outer']*len(points))
    if not isinstance(modes, list) or len(modes) != len(points) or any(not isinstance(m, str) or m not in MODES for m in modes):
        raise ValueError(f'{label}: edges must match points, using none/outer/seam')
    if abs(area(points)) < EPS:
        raise ValueError(f'{label}: zero area')
    seg = segments(points)
    for i, (a, b) in enumerate(seg):
        if math.dist(a, b) < EPS:
            raise ValueError(f'{label}: zero-length edge')
        prev = points[i-1]
        if abs(cross(prev, a, b)) < EPS and sum((prev[k]-a[k])*(b[k]-a[k]) for k in (0, 1)) > EPS:
            raise ValueError(f'{label}: overlapping adjacent edges')
        for j in range(i+1, len(seg)):
            if j == i+1 or (i == 0 and j == len(seg)-1):
                continue
            if intersect(a, b, *seg[j]):
                raise ValueError(f'{label}: self-intersection or repeated vertex')
    ring_rivets(raw, len(points))
    return points, modes


def validate_holes(rings):
    outer = rings[0][0]
    for index, (hole, _) in enumerate(rings[1:], 1):
        if not all(inside(p, outer) for p in hole):
            raise ValueError('hole must be strictly inside outer contour')
        for other, _ in rings[:index]:
            if any(intersect(a, b, c, d) for a, b in segments(hole) for c, d in segments(other)):
                raise ValueError('contours must not touch or intersect')
        for other, _ in rings[1:index]:
            if inside(hole[0], other) or inside(other[0], hole):
                raise ValueError('holes must not overlap or nest')


def color(value, name):
    if not isinstance(value, list) or len(value) not in (3, 4):
        raise ValueError(f'{name}: expected RGB or RGBA')
    result = tuple(integer(c, name, 0, 255) for c in value)
    return result if len(result) == 4 else result+(255,)


def material(raw, root):
    keys(raw, ('tile', 'procedural', 'phase_px', 'border_px', 'seam_px', 'edge_color', 'bevel_color', 'edge_profile', 'rivets'), 'material')
    if ('tile' in raw) == ('procedural' in raw):
        raise ValueError('material: provide exactly one of tile or procedural')
    procedural = noise.recipe(raw['procedural']) if 'procedural' in raw else None
    tile, tile_hash = None, None
    if procedural is None:
        path = raw['tile']
        if not isinstance(path, str):
            raise ValueError('material.tile: required image path relative to input JSON')
        path = root/path
        with Image.open(path) as source:
            if not 1 <= source.width <= 2048 or not 1 <= source.height <= 2048:
                raise ValueError('tile dimensions must be 1..2048')
            tile = source.convert('RGBA')
        if tile.getextrema()[3] != (255, 255):
            raise ValueError('material tile must be opaque; the contour supplies transparency')
        tile_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    phase = raw.get('phase_px', [0, 0])
    if not isinstance(phase, list) or len(phase) != 2:
        raise ValueError('phase_px: expected [x, y]')
    phase = tuple(integer(v, 'phase_px', -1000000, 1000000) for v in phase)
    profile = raw.get('edge_profile')
    if profile is not None:
        keys(profile, ('bands', 'light_direction', 'texture_strength'), 'edge_profile')
        bands = profile.get('bands')
        if not isinstance(bands, list) or not 1 <= len(bands) <= 8:
            raise ValueError('edge_profile.bands: expected 1..8 one-pixel bands')
        parsed = []
        for band in bands:
            keys(band, ('light', 'shade'), 'edge_profile band')
            parsed.append((color(band.get('light'), 'band.light'), color(band.get('shade'), 'band.shade')))
        light = profile.get('light_direction', [-1, -1])
        if not isinstance(light, list) or len(light) != 2:
            raise ValueError('edge_profile.light_direction: expected [x, y]')
        light = tuple(number(v, 'light_direction', -1e6, 1e6) for v in light)
        length = math.hypot(*light)
        if length < EPS:
            raise ValueError('edge_profile.light_direction must be nonzero')
        texture_strength=number(profile.get('texture_strength',0),'edge_profile.texture_strength',0,4)
        if procedural:
            weights=procedural['palette_weights'];total=sum(weights)
            center=tuple(sum(c[i]*w for c,w in zip(procedural['palette'],weights))/total for i in range(3))
        else:
            from PIL import ImageStat
            center=tuple(ImageStat.Stat(tile).mean[:3])
        profile = dict(bands=parsed, light=tuple(v/length for v in light), texture_strength=texture_strength, center=center)
        if 'border_px' in raw and integer(raw['border_px'], 'border_px', 0, 32) != len(parsed):
            raise ValueError('border_px must match edge_profile band count')
    rivets = raw.get('rivets', {})
    keys(rivets, ('enabled', 'spacing_px', 'inset_px', 'gap_px', 'colors', 'sprite', 'border_gap_px'), 'rivets')
    enabled = rivets.get('enabled', True)
    if not isinstance(enabled, bool):
        raise ValueError('rivets.enabled must be boolean')
    colors = rivets.get('colors', [[135, 135, 135], [105, 105, 105], [63, 63, 63]])
    if not isinstance(colors, list) or len(colors) != 3:
        raise ValueError('rivets.colors: highlight, body, shadow')
    sprite = rivets.get('sprite')
    if sprite is not None:
        if not isinstance(sprite, list) or not 1 <= len(sprite) <= 9 or any(not isinstance(row, list) or len(row) != len(sprite) for row in sprite):
            raise ValueError('rivets.sprite: expected a square 1..9 pixel matrix')
        sprite = tuple(tuple(None if px is None else color(px, 'sprite pixel') for px in row) for row in sprite)
        if all(px is None for row in sprite for px in row):
            raise ValueError('rivets.sprite must contain visible pixels')
    return dict(tile=tile, procedural=procedural, phase=phase,
                border=len(profile['bands']) if profile else integer(raw.get('border_px', 2), 'border_px', 0, 32),
                profile=profile,
                seam=integer(raw.get('seam_px', 2), 'seam_px', 0, 32),
                edge=color(raw.get('edge_color', [60, 60, 60]), 'edge_color'),
                bevel=color(raw.get('bevel_color', [100, 100, 100]), 'bevel_color'),
                sprite=sprite, border_gap=number(rivets.get('border_gap_px', 1), 'border_gap_px', 0, 32),
                rivets=enabled, spacing=number(rivets.get('spacing_px', 16), 'spacing_px', 4, 1024),
                inset=number(rivets.get('inset_px', 5), 'inset_px', 2, 64),
                gap=integer(rivets.get('gap_px', 2), 'gap_px', 0, 64),
                rivet_colors=[color(c, 'rivet color') for c in colors],
                tile_sha256=tile_hash)


def edge_records(rings, mat):
    records = []
    for index, (points, modes) in enumerate(rings):
        sign = (1 if area(points) > 0 else -1) * (1 if index == 0 else -1)
        for (a, b), mode in zip(segments(points), modes):
            length = math.dist(a, b)
            normal = (sign*(a[1]-b[1])/length, sign*(b[0]-a[0])/length)
            # Opposing material-side normals get complementary halves, even for odd widths.
            positive = normal[0] > EPS or (abs(normal[0]) <= EPS and normal[1] > 0)
            width = mat['border'] if mode == 'outer' else ((mat['seam']+int(positive))//2 if mode == 'seam' else 0)
            records.append((a, b, mode, width, normal, length))
    return records


def ring_rivets(raw, count):
    config = raw.get('rivets', {})
    keys(config, ('placement', 'alignment', 'edges'), 'contour.rivets')
    placement = config.get('placement', 'edges')
    alignment = config.get('alignment', 'edge')
    if placement not in ('edges', 'corners') or alignment not in ('edge', 'bounds'):
        raise ValueError('contour.rivets: placement edges/corners, alignment edge/bounds')
    enabled = config.get('edges', [True]*count)
    if not isinstance(enabled, list) or len(enabled) != count or any(type(v) is not bool for v in enabled):
        raise ValueError('contour.rivets.edges: one boolean per edge')
    return placement, alignment, enabled


def spaced(low, high, mat):
    span = high-low-2*mat['inset']
    if span < 0:
        return []
    if span < EPS:
        return [(low+high)/2]
    # Endpoints belong to both adjacent edges; deduplicate them after snapping.
    # A short edge uses its two endpoints, not an additional midpoint.
    count = max(2, math.floor(span/mat['spacing'])+1)
    return [low+mat['inset']+i*span/(count-1) for i in range(count)]


def rivet_positions(rings, raw_rings, mat):
    """Choose layout independently from border appearance; validate clearance later."""
    positions = []
    all_records = edge_records(rings, mat)
    offset = 0
    for (points, _), raw in zip(rings, raw_rings):
        records = all_records[offset:offset+len(points)]
        offset += len(points)
        placement, alignment, enabled = ring_rivets(raw, len(points))
        enabled = [flag and record[2] == 'outer' for flag, record in zip(enabled, records)]
        if placement == 'corners':
            for i, vertex in enumerate(points):
                if not (enabled[i-1] and enabled[i]):
                    continue
                n1, n2 = records[i-1][4], records[i][4]
                denominator = 1+n1[0]*n2[0]+n1[1]*n2[1]
                if denominator < EPS or abs(cross(records[i-1][0], vertex, records[i][1])) < EPS:
                    continue
                delta = tuple(mat['inset']*(n1[k]+n2[k])/denominator for k in (0, 1))
                if math.hypot(*delta) <= 4*mat['inset']:
                    positions.append(tuple(vertex[k]+delta[k] for k in (0, 1)))
            continue
        for use, (a, b, _, _, normal, length) in zip(enabled, records):
            if not use:
                continue
            if alignment == 'bounds' and (abs(a[0]-b[0]) < EPS or abs(a[1]-b[1]) < EPS):
                axis = 0 if abs(a[1]-b[1]) < EPS else 1
                for value in spaced(min(p[axis] for p in points), max(p[axis] for p in points), mat):
                    if min(a[axis], b[axis])+mat['inset']-EPS <= value <= max(a[axis], b[axis])-mat['inset']+EPS:
                        point = [a[k]+normal[k]*mat['inset'] for k in (0, 1)]
                        point[axis] = value
                        positions.append(tuple(point))
            else:
                for along in spaced(0, length, mat):
                    positions.append(tuple(a[k]+(b[k]-a[k])*along/length+normal[k]*mat['inset'] for k in (0, 1)))
    return positions


def snap_rivet(point, records, inset, size=3):
    """Snap to pixel centers; exact ties move into material, including shared corners."""
    indices = []
    phase = .5 if size % 2 == 0 else 0
    for axis, value in enumerate(point):
        shifted = value+phase
        index = math.floor(shifted)
        if abs(shifted-round(shifted)) < EPS:
            signs = set()
            for a, b, _, _, normal, _ in records:
                if abs(abs(normal[axis])-1) < EPS:
                    signed_distance = sum((point[k]-a[k])*normal[k] for k in (0, 1))
                    if abs(signed_distance-inset) < EPS:
                        signs.add(1 if normal[axis] > 0 else -1)
            if len(signs) > 1:
                return None
            if signs == {-1}:
                index = round(shifted)-1
        indices.append(index)
    return tuple(indices)


def render(shape, mat, density, padding):
    keys(shape, ('id', 'material', 'outer', 'holes'), 'shape')
    name = shape.get('id')
    if not isinstance(name, str) or not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}', name):
        raise ValueError('shape.id: use 1..64 letters, digits, underscores or hyphens')
    holes = shape.get('holes', [])
    if not isinstance(holes, list) or len(holes) > 32:
        raise ValueError('holes: expected up to 32 contours')
    rings = [parse_ring(shape.get('outer'), density, name)] + [parse_ring(h, density, f'{name}.hole') for h in holes]
    validate_holes(rings)
    points = rings[0][0]
    x0 = math.floor(min(p[0] for p in points))-padding
    y0 = math.floor(min(p[1] for p in points))-padding
    width = math.ceil(max(p[0] for p in points))+padding-x0
    height = math.ceil(max(p[1] for p in points))+padding-y0
    if not 1 <= width <= 1024 or not 1 <= height <= 1024:
        raise ValueError(f'{name}: output dimensions must be 1..1024 pixels')
    if width*height*sum(len(p) for p, _ in rings) > 50_000_000:
        raise ValueError(f'{name}: contour rasterization budget exceeded; reduce size or vertices')
    records = edge_records(rings, mat)
    image = Image.new('RGBA', (width, height))
    pixels = image.load()
    mask = set()
    for y in range(height):
        for x in range(width):
            p = (x+x0+.5, y+y0+.5)
            if not inside(p, points) or any(inside(p, h) for h, _ in rings[1:]):
                continue
            mask.add((x, y))
            if mat['procedural'] is not None:
                px = noise.sample(mat['procedural'], p[0]+mat['phase'][0], p[1]+mat['phase'][1], density)
            else:
                px = mat['tile'].getpixel(((x+x0+mat['phase'][0]) % mat['tile'].width,
                                           (y+y0+mat['phase'][1]) % mat['tile'].height))
            affected = [(distance(p, a, b), mode, normal) for a, b, mode, w, normal, _ in records if w and distance(p, a, b) < w]
            if affected:
                # Geometry-based tie break keeps corners independent of contour winding.
                dist, mode, normal = min(affected, key=lambda v:(round(v[0],12), v[1], v[2]))
                if mode == 'outer' and mat['profile']:
                    profile = mat['profile']
                    light, shade = profile['bands'][min(int(dist), len(profile['bands'])-1)]
                    strength = max(0, min(1, .5-.5*sum(normal[i]*profile['light'][i] for i in (0,1))))
                    base=px
                    px = tuple(max(0,min(255,round(a*strength+b*(1-strength)+
                        (profile['texture_strength']*(base[i]-profile['center'][i]) if i<3 else 0))))
                        for i,(a,b) in enumerate(zip(light,shade)))
                else:
                    px = mat['edge'] if mode == 'seam' or dist < 1 else mat['bevel']
            pixels[x, y] = px
    if not mask:
        raise ValueError(f'{name}: contour covers no pixel centers; increase pixel density')
    centers = []
    if mat['rivets']:
        light, body, dark = mat['rivet_colors']
        sprite = mat['sprite'] or ((None, light, None), (light, body, dark), (None, dark, None))
        size = len(sprite)
        occupied = [(sx-size//2, sy-size//2) for sy,row in enumerate(sprite) for sx,px in enumerate(row) if px is not None]
        positions = rivet_positions(rings, [shape['outer']]+holes, mat)
        snapped = [snap_rivet(point, records, mat['inset'], size) for point in positions]
        candidates = {(point[0]-x0, point[1]-y0) for point in snapped if point is not None}
        for cx, cy in sorted(candidates, key=lambda p: (p[1], p[0])):
            footprint = [(cx+dx, cy+dy) for dx,dy in occupied]
            if any(p not in mask for p in footprint):
                continue
            if any(distance((x+x0+.5, y+y0+.5), a, b) < w+mat['border_gap'] for x, y in footprint for a, b, _, w, _, _ in records):
                continue
            if any(max(abs(cx-x), abs(cy-y)) < size+mat['gap'] for x, y in centers):
                continue
            centers.append((cx, cy))
        for cx, cy in centers:
            for sy, row in enumerate(sprite):
                for sx, px in enumerate(row):
                    if px is not None:
                        pixels[cx+sx-size//2, cy+sy-size//2] = px
    return image, dict(id=name, size_px=[width, height], origin_px=[x0, y0], rivet_centers_px=centers,
                       coverage_pixels=len(mask), tile_sha256=mat['tile_sha256'],
                       procedural=mat['procedural'],
                       rivet_center_offset_px=(0 if mat['sprite'] and len(mat['sprite']) % 2 == 0 else .5))


def generate(config, root):
    keys(config, ('version', 'pixels_per_unit', 'padding_px', 'materials', 'shapes'), 'input')
    if type(config.get('version')) is not int or config['version'] != 1:
        raise ValueError('input version must be 1')
    density = number(config.get('pixels_per_unit', 16), 'pixels_per_unit', .01, 4096)
    padding = integer(config.get('padding_px', 2), 'padding_px', 0, 32)
    raw_materials = config.get('materials')
    if not isinstance(raw_materials, dict) or not raw_materials:
        raise ValueError('materials: expected a nonempty object')
    mats = {name: material(raw, root) for name, raw in raw_materials.items()}
    shapes = config.get('shapes')
    if not isinstance(shapes, list) or not 1 <= len(shapes) <= 32:
        raise ValueError('shapes: expected 1..32 shapes')
    outputs, names, total = [], set(), 0
    for shape in shapes:
        if not isinstance(shape, dict) or not isinstance(shape.get('material'), str) or shape['material'] not in mats:
            raise ValueError('shape requires a known material')
        image, info = render(shape, mats[shape['material']], density, padding)
        if info['id'].casefold() in names:
            raise ValueError('shape IDs must be unique (case insensitive)')
        names.add(info['id'].casefold())
        total += image.width*image.height
        if total > 4_000_000:
            raise ValueError('total output pixel budget exceeded')
        outputs.append((image, info))
    return outputs



def preview(outputs):
    """Bounded contact sheet, native scale above a 4x nearest-neighbor view."""
    if len(outputs) > 8 or any(im.width > 128 or im.height > 128 for im, _ in outputs):
        raise ValueError('--preview supports up to 8 regions, each at most 128x128; render larger images separately')
    cell_w = max(im.width for im, _ in outputs)*4+18
    native_h = max(im.height for im, _ in outputs)
    enlarged_y = 70+native_h
    canvas = Image.new('RGB', (16+cell_w*len(outputs), enlarged_y+native_h*4+16), (28, 30, 33))
    draw = ImageDraw.Draw(canvas)
    draw.text((16, 10), 'REGION FILL / top: 1x / bottom: 4x nearest-neighbor', fill=(210, 210, 210))
    for index, (im, info) in enumerate(outputs):
        x = 16+index*cell_w
        draw.text((x, 34), info['id'], fill=(205, 205, 205))
        for scale, y in ((1, 54), (4, enlarged_y)):
            w, h = im.width*scale, im.height*scale
            for yy in range(0, h, 8):
                for xx in range(0, w, 8):
                    shade = (42, 44, 47) if (xx//8+yy//8) % 2 else (49, 51, 54)
                    draw.rectangle((x+xx, y+yy, x+min(xx+7, w-1), y+min(yy+7, h-1)), fill=shade)
            enlarged = im.resize((w, h), Image.Resampling.NEAREST)
            canvas.paste(enlarged, (x, y), enlarged)
    return canvas


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--preview', action='store_true', help='also create specimens.png with native and 4x views')
    parser.add_argument('--force', action='store_true', help='replace only same-named generated files')
    args = parser.parse_args()
    try:
        config = json.loads(args.input.read_text())
        outputs = generate(config, args.input.resolve().parent)
        sheet = preview(outputs) if args.preview else None
        targets = [args.output/(info['id']+'.png') for _, info in outputs] + [args.output/'manifest.json']
        if sheet is not None:
            if any(info['id'].casefold() == 'specimens' for _, info in outputs):
                raise ValueError('shape ID specimens is reserved when --preview is used')
            targets.append(args.output/'specimens.png')
        if any(p.resolve() == args.input.resolve() for p in targets):
            raise ValueError('output would overwrite input JSON')
        tile_paths = {(args.input.resolve().parent/m['tile']).resolve() for m in config['materials'].values() if 'tile' in m}
        if any(p.resolve() in tile_paths for p in targets):
            raise ValueError('output would overwrite a source tile')
        if not args.force and any(p.exists() for p in targets):
            raise ValueError('output already exists; choose another directory or pass --force')
        args.output.mkdir(parents=True, exist_ok=True)
        for image, info in outputs:
            image.save(args.output/(info['id']+'.png'))
        if sheet is not None:
            sheet.save(args.output/'specimens.png')
        manifest = dict(version=1, generator_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                        noise_sha256=hashlib.sha256(Path(noise.__file__).read_bytes()).hexdigest(),
                        pixels_per_unit=config.get('pixels_per_unit', 16),
                        input_sha256=hashlib.sha256(args.input.read_bytes()).hexdigest(),
                        shapes=[info for _, info in outputs])
        (args.output/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
        print(f'Generated {len(outputs)} regions in {args.output}')
    except (ValueError, OSError, Image.DecompressionBombError) as error:
        parser.exit(2, f'error: {error}\n')


if __name__ == '__main__':
    main()
