"""Geometry and UV math shared by diagnostics and atlas export."""
import math

def sub(a, b): return tuple(x-y for x, y in zip(a, b))
def dot(a, b): return sum(x*y for x, y in zip(a, b))
def cross(a, b): return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
def norm(a): return math.sqrt(dot(a, a))
def cross2(a, b): return a[0]*b[1]-a[1]*b[0]
def area(poly): return abs(sum(cross2(a, b) for a, b in zip(poly, poly[1:]+poly[:1])))/2 if len(poly) >= 3 else 0.


def intersection_area(a, b):
    """Convex polygon clipping; boundary contact has zero area."""
    sign = 1 if sum(cross2(x, y) for x, y in zip(b, b[1:]+b[:1])) >= 0 else -1
    out = list(a)
    for p, q in zip(b, b[1:]+b[:1]):
        result = []
        if not out: return 0.
        for x, y in zip(out, out[1:]+out[:1]):
            dx = sign*cross2(sub(q, p), sub(x, p))
            dy = sign*cross2(sub(q, p), sub(y, p))
            if dx >= 0: result.append(x)
            if (dx < 0 < dy) or (dy < 0 < dx):
                t = dx/(dx-dy)
                result.append(tuple(x[k]+t*(y[k]-x[k]) for k in (0, 1)))
        out = result
    return area(out)


def singular_values(xyz, uv):
    a, b = sub(xyz[1], xyz[0]), sub(xyz[2], xyz[0])
    length = norm(a)
    if length <= 1e-15: return None
    bx = dot(a, b)/length
    by = norm(cross(a, b))/length
    if by <= 1e-15: return None
    u, v = sub(uv[1], uv[0]), sub(uv[2], uv[0])
    c0 = (u[0]/length, u[1]/length)
    c1 = ((v[0]-c0[0]*bx)/by, (v[1]-c0[1]*bx)/by)
    aa, bb, cc = dot(c0, c0), dot(c1, c1), dot(c0, c1)
    disc = math.sqrt(max(0., (aa-bb)**2+4*cc*cc))
    return math.sqrt(max(0., (aa+bb-disc)/2)), math.sqrt(max(0., (aa+bb+disc)/2))
