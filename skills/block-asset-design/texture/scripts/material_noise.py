#!/usr/bin/env python3
"""Original neutral palettes and coordinate-stable procedural materials. No external assets."""
import math

PRESETS = {
 'plate': {'palette': [[v,v+1,v+2] for v in (78,84,90,96,102)], 'scales': [(1,1,.75),(5,5,.25)]},
 'structure': {'palette': [[v,v+2,v+1] for v in (43,48,53,58,63)], 'scales': [(2,3,.75),(1,1,.20),(7,6,.05)]},
 'machined': {'palette': [[v,v+2,v+3] for v in (112,117,122,127,132)], 'scales': [(9,1,.85),(3,1,.12),(1,1,.03)]},
 'painted': {'palette': [[v,v+8,v-2] for v in (40,44,48,52,56)], 'scales': [(4,3,.85),(1,1,.10),(9,7,.05)]},
}


def recipe(raw):
    allowed={'preset','seed','palette','palette_weights','direction','algorithm','noise_strength'}
    if not isinstance(raw,dict) or set(raw)-allowed: raise ValueError('unknown procedural fields')
    name=raw.get('preset')
    if name not in PRESETS: raise ValueError('unknown material preset')
    if raw.get('algorithm','jittered-clusters-v1')!='jittered-clusters-v1': raise ValueError('unsupported algorithm; external calibrated recipes require their own resources')
    seed=raw.get('seed',0)
    if type(seed) is not int or not 0<=seed<=0xffffffff: raise ValueError('seed must be uint32')
    direction=raw.get('direction','x')
    if direction not in ('x','y'): raise ValueError('direction must be x or y')
    palette=raw.get('palette',PRESETS[name]['palette'])
    if not isinstance(palette,list) or not 3<=len(palette)<=256 or any(not isinstance(c,list) or len(c)!=3 or any(type(v) is not int or not 0<=v<=255 for v in c) for c in palette): raise ValueError('expected 3..256 RGB colors')
    luma=[sum(v*w for v,w in zip(c,(.2126,.7152,.0722))) for c in palette]
    if any(b<=a for a,b in zip(luma,luma[1:])): raise ValueError('palette must increase in luminance')
    weights=raw.get('palette_weights',[1]*len(palette))
    if not isinstance(weights,list) or len(weights)!=len(palette) or any(type(v) not in (int,float) or not math.isfinite(v) or v<=0 for v in weights) or not math.isfinite(sum(weights)): raise ValueError('invalid palette weights')
    strength=raw.get('noise_strength',.75)
    if type(strength) not in (int,float) or not math.isfinite(strength) or not 0<=strength<=1: raise ValueError('noise_strength must be 0..1')
    return dict(preset=name,seed=seed,direction=direction,palette=palette,palette_weights=weights,algorithm='jittered-clusters-v1',noise_strength=strength)


def hashed(x, y, seed):
    n = (x*0x1f123bb5 ^ y*0x5f356495 ^ seed) & 0xffffffff
    n = ((n ^ (n >> 16))*0x7feb352d) & 0xffffffff
    n = ((n ^ (n >> 15))*0x846ca68b) & 0xffffffff
    return ((n ^ (n >> 16)) & 0xffffffff)/0xffffffff


def field(x, y, sx, sy, seed):
    """Piecewise-constant jittered cells, without interpolated brightness ramps.

    One site per lattice cell, bounded jitter; a 3x3 neighborhood suffices.
    Nearest-site ownership breaks regular tile outlines without blurring colors.
    """
    x, y = x/sx, y/sy
    ix, iy = math.floor(x), math.floor(y)
    best, value = float('inf'), 0
    for cy in range(iy-1, iy+2):
        for cx in range(ix-1, ix+2):
            px = cx+.25+.5*hashed(cx, cy, seed ^ 0xa511e9b3)
            py = cy+.25+.5*hashed(cx, cy, seed ^ 0x63d83595)
            distance = (x-px)**2+(y-py)**2
            if distance < best:
                best = distance
                value = hashed(cx, cy, seed)
    return value


def sample(config,x,y,density=16):
    if not math.isfinite(density) or density<=0: raise ValueError('positive density required')
    x,y=x*16/density,y*16/density
    if config['direction']=='y': x,y=y,x
    value=sum(field(x,y,sx,sy,config['seed']^(i*0x9e3779b9))*w for i,(sx,sy,w) in enumerate(PRESETS[config['preset']]['scales']))
    value=max(0,min(1,.5+(value-.5)*1.1*config.get('noise_strength',1)))
    target=value*sum(config['palette_weights']); total=0
    for color,weight in zip(config['palette'],config['palette_weights']):
        total+=weight
        if target<total: return tuple(color)+(255,)
    return tuple(config['palette'][-1])+(255,)
