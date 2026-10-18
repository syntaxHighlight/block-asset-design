#!/usr/bin/env python3
"""Review views for interactive Blender. Does not create cameras, edit objects, or save."""
import math

DIRECTIONS = {'front': (0,-1,0), 'back': (0,1,0), 'left': (-1,0,0), 'right': (1,0,0),
              'top': (0,0,1), 'front-right': (1,-1,.6), 'back-left': (-1,1,.6)}


def plan(objects):
    from mathutils import Vector
    points = [o.matrix_world @ Vector(c) for o in objects for c in o.bound_box]
    if not points: raise ValueError('select objects with bounds')
    low = Vector(tuple(min(p[k] for p in points) for k in range(3)))
    high = Vector(tuple(max(p[k] for p in points) for k in range(3)))
    return {'center': list((low+high)/2), 'distance': max((high-low).length*1.2,.1),
            'directions': DIRECTIONS, 'note': 'Source object bounds; inspect evaluated instances separately.'}


def apply_view(objects, direction='front-right', perspective='ORTHO'):
    import bpy
    from mathutils import Vector
    if direction not in DIRECTIONS or perspective not in ('ORTHO','PERSP'): raise ValueError('invalid view')
    if not bpy.context.screen: raise RuntimeError('interactive screen required')
    areas = [a for a in bpy.context.screen.areas if a.type=='VIEW_3D']
    if not areas: raise RuntimeError('open a 3D Viewport first')
    config=plan(objects); saved=[]
    for area in areas:
        region=area.spaces.active.region_3d
        saved.append((region, region.view_location.copy(), region.view_rotation.copy(), region.view_distance, region.view_perspective))
        region.view_location=Vector(config['center'])
        region.view_rotation=(-Vector(DIRECTIONS[direction])).to_track_quat('-Z','Y')
        region.view_distance=config['distance']; region.view_perspective=perspective
        area.tag_redraw()
    return saved


def restore(saved):
    for region, location, rotation, distance, perspective in saved:
        region.view_location=location; region.view_rotation=rotation
        region.view_distance=distance; region.view_perspective=perspective
