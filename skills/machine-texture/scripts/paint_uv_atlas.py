"""Paint pre-unwrapped pixel charts using authored surface and edge semantics.

Consumes pixel coordinates, mesh-space positions and explicit edge roles; never
infers painted lines from UV discontinuities or triangle boundaries. PIL only.
Packing moves whole charts by integer pixels. Source geometry is not modified.
"""
import argparse,copy,hashlib,json,math,sys,zlib
from pathlib import Path
from collections import deque,Counter
from PIL import Image
import material_noise as noise


def cross(a,b):return a[0]*b[1]-a[1]*b[0]

def subtract(a,b):return a[0]-b[0],a[1]-b[1]

def barycentric(p,a,b,c):
    ab=subtract(b,a);ac=subtract(c,a);ap=subtract(p,a);d=cross(ab,ac)
    if abs(d)<1e-12:return None
    v=cross(ap,ac)/d;w=cross(ab,ap)/d;u=1-v-w
    return (u,v,w) if min(u,v,w)>=-1e-8 else None

def clipped_pixel(tri,x,y):
    """Exact conservative coverage for subpixel sides, without enlarging UVs."""
    poly=list(tri)
    for axis,edge,sign in ((0,x,1),(0,x+1,-1),(1,y,1),(1,y+1,-1)):
        out=[]
        if not poly:return None
        for p,q in zip(poly,poly[1:]+poly[:1]):
            a=(p[axis]-edge)*sign;b=(q[axis]-edge)*sign
            if a>=0:out.append(p)
            if (a<0<b) or (b<0<a):
                t=a/(a-b);out.append([p[k]+t*(q[k]-p[k]) for k in (0,1)])
        poly=out
    if len(poly)<3:return None
    area=abs(sum(cross(subtract(poly[i],poly[0]),subtract(poly[(i+1)%len(poly)],poly[0])) for i in range(1,len(poly)-1)))*.5
    if area<1e-12:return None
    return area,[sum(p[k] for p in poly)/len(poly) for k in (0,1)]


def distance(p,a,b):
    dx,dy=b[0]-a[0],b[1]-a[1];ll=dx*dx+dy*dy
    t=max(0,min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/ll)) if ll else 0
    return math.hypot(p[0]-a[0]-t*dx,p[1]-a[1]-t*dy)


def pack(rects,width,height):
    free=[(0,0,width,height)];result={}
    for key,w,h in sorted(rects,key=lambda x:(-max(x[1:]),-x[1]*x[2],x[0])):
        matches=[(min(fw-w,fh-h),max(fw-w,fh-h),y,x,i) for i,(x,y,fw,fh) in enumerate(free) if w<=fw and h<=fh]
        if not matches:return None
        _,_,y,x,_=min(matches);result[key]=(x,y);new=[]
        for fx,fy,fw,fh in free:
            if x>=fx+fw or x+w<=fx or y>=fy+fh or y+h<=fy:new.append((fx,fy,fw,fh));continue
            if x>fx:new.append((fx,fy,x-fx,fh))
            if x+w<fx+fw:new.append((x+w,fy,fx+fw-x-w,fh))
            if y>fy:new.append((fx,fy,fw,y-fy))
            if y+h<fy+fh:new.append((fx,y+h,fw,fy+fh-y-h))
        free=[r for i,r in enumerate(new) if not any(i!=j and s[0]<=r[0] and s[1]<=r[1] and s[0]+s[2]>=r[0]+r[2] and s[1]+s[3]>=r[1]+r[3] and (s!=r or j<i) for j,s in enumerate(new))]
    return result


def surface_color(recipe,xyz,normal,density):
    # Model-space triplanar sampling makes the result independent of chart
    # placement, chart rotation, atlas size and a UV cut's arbitrary location.
    weights=[abs(v)**4 for v in normal];total=sum(weights)
    planes=((xyz[1],xyz[2]),(xyz[0],xyz[2]),(xyz[0],xyz[1]))
    rgb=[0.,0.,0.]
    for weight,point in zip(weights,planes):
        if weight<1e-5:continue
        sample=noise.sample(recipe,point[0]*density,point[1]*density,density)
        for k in range(3):rgb[k]+=sample[k]*weight/total
    color=min(recipe['palette'],key=lambda p:sum((p[k]-rgb[k])**2 for k in range(3)))
    return tuple(color)+(255,)


def stamp_sample(stamp,xyz,normal,density):
    if sum(a*b for a,b in zip(normal,stamp['normal']))<.999:return None
    delta=[xyz[k]-stamp['center'][k] for k in range(3)]
    if abs(sum(a*b for a,b in zip(delta,stamp['normal'])))>1e-5:return None
    im=stamp['image'];u=sum(a*b for a,b in zip(delta,stamp['right']))*density+im.width/2
    v=im.height/2-sum(a*b for a,b in zip(delta,stamp['up']))*density
    # Remove only floating-point residue at exact source-pixel boundaries.
    x=math.floor(u+1e-5);y=math.floor(v+1e-5)
    return (x,y) if 0<=x<im.width and 0<=y<im.height else None


def render_chart(chart,materials,density,padding,style=None,stamps=(),borders=()):
    style=style or {}
    extent=[max(p[i] for f in chart['faces'] for p in f['xy']) for i in (0,1)]
    w,h=[max(1,math.ceil(v-1e-6))+2*padding for v in extent]
    image=Image.new('RGBA',(w,h));pixels=image.load();owners={};positions={};center_owned=set();fallback_area={};lookup={f['id']:f for f in chart['faces']}
    recipes={};seed=zlib.crc32(chart['mesh'].encode())
    for name,raw in materials.items():
        conf=copy.deepcopy(raw['procedural']);conf['seed']=conf.get('seed',0)^seed;recipes[name]=noise.recipe(conf)
    def paint(q,f,xyz):
        role=f['role']
        color=(77,82,84,255) if role=='glass' else (85,85,85,255) if role=='artwork' else surface_color(recipes[role],xyz,f['normal'],density)
        pixels[q]=color;owners[q]=f['id'];positions[q]=xyz
    for f in chart['faces']:
        xy=f['xy']
        for ids in f['triangles']:
            tri=[xy[i] for i in ids]
            low=[max(0,math.floor(min(p[k] for p in tri))) for k in (0,1)];high=[min((w if k==0 else h)-2*padding,math.ceil(max(p[k] for p in tri))) for k in (0,1)]
            for y in range(low[1],high[1]):
                for x in range(low[0],high[0]):
                    bc=barycentric((x+.5,y+.5),*tri)
                    q=(x+padding,y+padding)
                    if bc is None:
                        if q in center_owned:continue
                        clipped=clipped_pixel(tri,x,y)
                        if clipped is None or clipped[0]<=fallback_area.get(q,0):continue
                        bc=barycentric(clipped[1],*tri)
                        if bc is None:continue
                        fallback_area[q]=clipped[0]
                    else:center_owned.add(q)
                    xyz=[sum(b*f['xyz'][i][k] for b,i in zip(bc,ids)) for k in range(3)]
                    paint(q,f,xyz)
    # Record subpixel faces; do not enlarge them or overwrite neighboring faces.
    covered=set(owners.values());missing=[f['id'] for f in chart['faces'] if f['id'] not in covered]
    if not owners:
        f=max(chart['faces'],key=lambda f:len(f['xy']));paint((padding,padding),f,f['xyz'][0])
    by_face={}
    for e in chart['edges']:
        if e['role'] not in (0,1,2):raise ValueError('Unknown structural edge role')
        if e['role']==0:continue
        if e['length_px']<1.5 or e['surface_width_px']<2:continue
        if lookup[e['face']]['role'] in ('artwork','glass'):continue
        by_face.setdefault(e['face'],[]).append(e)
    colored=Counter()
    for q,fi in owners.items():
        point=(q[0]-padding+.5,q[1]-padding+.5);f=lookup[fi];edges=by_face.get(fi,[])
        hits=[(distance(point,*e['xy']),e) for e in edges];hits=[(d,e) for d,e in hits if d<style.get('joint_width_px' if e['role']==2 else 'form_width_px',1.)]
        if not hits:continue
        # One band per pixel; never compound multiple borders at corners.
        d,e=min(hits,key=lambda hit:(-hit[1]['role'],hit[0],hit[1]['id']))
        base=pixels[q];delta=style.get('joint_delta',-17) if e['role']==2 else (style.get('convex_delta',9) if e.get('convex',True) else style.get('concave_delta',-10))
        pixels[q]=tuple(max(0,min(255,v+delta)) for v in base[:3])+(255,);colored[e['role']]+=1
    # Explicit physical panel perimeter. UV island bounds never supply borders.
    border_hits=Counter()
    for border in borders:
        if border.get('object') and border['object']!=chart.get('object'):continue
        for q,fi in owners.items():
            f=lookup[fi]
            if f['role'] not in border['roles']:continue
            if sum(a*b for a,b in zip(f['normal'],border['normal']))<.999:continue
            rel=[positions[q][k]-border['center'][k] for k in range(3)]
            if abs(sum(a*b for a,b in zip(rel,border['normal'])))>1e-5:continue
            u=sum(a*b for a,b in zip(rel,border['right']));v=sum(a*b for a,b in zip(rel,border['up']))
            x0,y0,x1,y1=border['bounds'];d=min(u-x0,x1-u,v-y0,y1-v)*density
            if not 0<=d<len(border['bands']):continue
            delta=border['bands'][int(d)]
            # Replace, rather than compound with, the generic edge highlight.
            base=surface_color(recipes[f['role']],positions[q],f['normal'],density)
            pixels[q]=tuple(max(0,min(255,c+delta)) for c in base[:3])+(255,)
            border_hits[border['id']]+=1
    # Artwork uses explicit model-space placement and native source pixels.
    # Apply after edge profiles, before padding, so no generated line crosses it.
    detail_hits=Counter()
    for stamp in stamps:
        if stamp.get('object') and stamp['object']!=chart.get('object'):continue
        for q,fi in owners.items():
            f=lookup[fi]
            if f['role'] not in stamp['roles']:continue
            sample=stamp_sample(stamp,positions[q],f['normal'],density)
            if sample is None:continue
            color=stamp['image'].getpixel(sample)
            if color[3]!=255:raise ValueError('Opaque surface stamps require opaque source pixels')
            pixels[q]=color;detail_hits[stamp['id']]+=1
    # Deterministic nearest-neighbor extrusion, bounded to this chart rectangle.
    known=set(owners);front=sorted(known)
    for _ in range(padding):
        fresh={}
        for x,y in front:
            for dx,dy in ((-1,-1),(0,-1),(1,-1),(-1,0),(1,0),(-1,1),(0,1),(1,1)):
                q=(x+dx,y+dy)
                if 0<=q[0]<w and 0<=q[1]<h and q not in known and q not in fresh:fresh[q]=pixels[x,y]
        for q,c in fresh.items():pixels[q]=c
        known.update(fresh);front=sorted(fresh)
    return image,dict(covered_texels=len(owners),conservative_texels=len(set(fallback_area)-center_owned),subpixel_faces=missing,edge_texels=dict(colored),detail_texels=dict(detail_hits),border_texels=dict(border_hits))


def validate_spec(spec, config):
    """Validate mappings before allocating images or writing generated files."""
    density=spec.get('pixels_per_unit'); padding=spec.get('padding_px')
    if type(density) not in (int,float) or not math.isfinite(density) or density<=0:
        raise ValueError('positive finite density required')
    if type(padding) is not int or not 2<=padding<=64: raise ValueError('padding must be 2..64 pixels')
    charts=spec.get('charts',[])
    if not charts or len(charts)>4096: raise ValueError('expected 1..4096 charts')
    meshes=spec.get('meshes',{})
    if not meshes or any(type(m.get('loops')) is not int or not 0<m['loops']<=1000000 for m in meshes.values()): raise ValueError('invalid mesh loop counts')
    assigned={name:set() for name in meshes}; ids=set(); pixels=0
    for chart in charts:
        if chart['id'] in ids or chart['mesh'] not in meshes: raise ValueError('duplicate chart or unknown mesh')
        ids.add(chart['id']); face_ids=set()
        if not chart['faces']: raise ValueError('empty chart')
        for face in chart['faces']:
            if face['id'] in face_ids: raise ValueError('duplicate face in chart')
            face_ids.add(face['id']); count=len(face['loops'])
            if count<3 or len(face['xy'])!=count or len(face['xyz'])!=count: raise ValueError('face arrays mismatch')
            for li in face['loops']:
                if type(li) is not int or not 0<=li<meshes[chart['mesh']]['loops'] or li in assigned[chart['mesh']]: raise ValueError('invalid or duplicate loop mapping')
                assigned[chart['mesh']].add(li)
            for key, dims in (('xy',2),('xyz',3)):
                if any(len(p)!=dims or any(not math.isfinite(x) for x in p) for p in face[key]): raise ValueError('invalid face coordinates')
            if any(v<0 for p in face['xy'] for v in p): raise ValueError('chart pixel coordinates must be nonnegative')
            if len(face['normal'])!=3 or any(not math.isfinite(v) for v in face['normal']): raise ValueError('invalid normal')
            if not face['triangles'] or any(len(t)!=3 or any(type(i) is not int or not 0<=i<count for i in t) for t in face['triangles']): raise ValueError('invalid face triangles')
            if face['role'] not in config['materials'] and face['role'] not in ('glass','artwork'): raise ValueError('unmapped material role')
        for edge in chart['edges']:
            if edge['face'] not in face_ids or edge['role'] not in (0,1,2): raise ValueError('invalid structural edge')
        extent=[math.ceil(max(p[k] for f in chart['faces'] for p in f['xy']))+2*padding for k in (0,1)]
        if max(extent)>1024: raise ValueError('chart exceeds atlas limit')
        pixels+=extent[0]*extent[1]
    if pixels>4*1024*1024: raise ValueError('raster workload exceeds budget; split the task')
    if any(len(assigned[name])!=m['loops'] for name,m in meshes.items()): raise ValueError('unmapped mesh loops')


def generate(spec,config,output,source_dir=None):
    output=Path(output)
    if output.exists() and any(output.iterdir()):raise ValueError("Use a new or empty output directory")
    if spec.get('version')!=1 or config.get('version')!=1:raise ValueError('Unsupported schema')
    validate_spec(spec,config)
    density=spec['pixels_per_unit'];padding=spec['padding_px']
    if density<=0 or padding<2:raise ValueError('Invalid density or padding')
    details=None;stamps=[]
    if config.get('details_filename'):
        base=Path(source_dir or output);details=json.loads((base/config['details_filename']).read_text())
        raw=(base/details['source']).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=details['source_sha256']:raise ValueError('Artwork source hash changed')
        if details['pixels_per_unit']!=density:raise ValueError('Artwork density differs from atlas')
        source=Image.open(base/details['source']).convert('RGBA')
        for entry in details['stamps']:
            rect=entry['source_rect']
            if not (0<=rect[0]<rect[2]<=source.width and 0<=rect[1]<rect[3]<=source.height):raise ValueError('Artwork crop out of bounds')
            stamps.append(dict(entry,image=source.crop(rect)))
    charts=spec['charts'];rendered={};stats={}
    for ch in charts:
        rendered[ch['id']],stats[ch['id']]=render_chart(ch,config['materials'],density,padding,config.get('edge_style'),stamps,details.get('borders',[]) if details else [])
    if details:
        counts=Counter()
        for stat in stats.values():counts.update(stat['detail_texels'])
        absent=[s['id'] for s in stamps if not counts[s['id']]]
        if absent:raise ValueError('Unmapped artwork: '+repr(absent))
    rects=[(key,im.width,im.height) for key,im in rendered.items()]
    choices=sorted([(w*h,abs(w-h),w,h) for w in (128,256,512,1024) for h in (128,256,512,1024)])
    for _,_,w,h in choices:
        placement=pack(rects,w,h)
        if placement is not None:break
    else:raise ValueError('Atlas exceeds 1024 squared')
    atlas=Image.new('RGBA',(w,h));mesh_uv={key:[[0.,0.]]*v['loops'] for key,v in spec['meshes'].items()}
    for ch in charts:
        x,y=placement[ch['id']];atlas.paste(rendered[ch['id']],(x,y))
        for f in ch['faces']:
            for li,p in zip(f['loops'],f['xy']):mesh_uv[ch['mesh']][li]=[(x+padding+p[0])/w,1-(y+padding+p[1])/h]
    output=Path(output);output.mkdir(parents=True,exist_ok=True);atlas_name=config.get('atlas_filename','pixel_atlas.png')
    if Path(atlas_name).name!=atlas_name or not atlas_name.endswith('.png'):raise ValueError('atlas_filename must be a PNG basename')
    atlas.save(output/atlas_name)
    layout=dict(version=1,details=details,atlas_filename=atlas_name,edge_style=config.get('edge_style',{}),size=[w,h],density=density,padding_px=padding,mesh_uv=mesh_uv,charts=[dict(id=ch['id'],xy=placement[ch['id']],size=rendered[ch['id']].size,**stats[ch['id']]) for ch in charts],materials=config['materials'],generator_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),noise_sha256=hashlib.sha256(Path(noise.__file__).read_bytes()).hexdigest(),input_sha256=hashlib.sha256(json.dumps(spec,sort_keys=True).encode()).hexdigest(),atlas_sha256=hashlib.sha256((output/atlas_name).read_bytes()).hexdigest())
    (output/'pixel-atlas-layout.json').write_text(json.dumps(layout,separators=(',',':'))+'\n')
    print('PIXEL_ATLAS',w,h,len(charts),'charts;',sum(v['covered_texels'] for v in stats.values()),'painted texels')
    return layout


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input',required=True);p.add_argument('--config',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    generate(json.loads(Path(a.input).read_text()),json.loads(Path(a.config).read_text()),a.output,Path(a.config).parent)
