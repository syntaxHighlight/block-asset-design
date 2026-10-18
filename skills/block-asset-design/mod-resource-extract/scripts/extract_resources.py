#!/usr/bin/env python3
"""Extract explicitly authorized local resource entries from ZIP/JAR by hash."""
import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import zipfile


def safe_name(value):
    p=PurePosixPath(value)
    if not value or not p.parts or p.is_absolute() or '..' in p.parts or '\\' in value or ':' in value: raise ValueError('unsafe resource path')
    return str(p)


def extract(archive, manifest, destination):
    if destination.exists(): raise ValueError('output must be a new directory')
    spec=json.loads(manifest.read_text())
    if spec.get('version')!=1: raise ValueError('unsupported manifest version')
    if spec.get('usage_status')!='confirmed' or not spec.get('usage_scope') or not spec.get('permission_evidence'):
        raise ValueError('confirmed usage scope and permission evidence are required; extraction grants no rights')
    digest=hashlib.sha256(archive.read_bytes()).hexdigest()
    if digest!=spec['archive_sha256']: raise ValueError('archive hash mismatch')
    entries=spec['entries']
    notices=spec.get('notice_files',[])
    if not entries or len(entries)+len(notices)>512: raise ValueError('expected 1..512 total resource and notice entries')
    paths=set(); payloads=[]
    with zipfile.ZipFile(archive) as z:
        for entry in entries:
            source=safe_name(entry['source']); target=safe_name(entry['output'])
            if target in paths or target=='resource-record.json': raise ValueError('duplicate or reserved output')
            paths.add(target)
            info=z.getinfo(source)
            if info.file_size>64*1024*1024: raise ValueError('resource exceeds 64MiB')
            content=z.read(info)
            if hashlib.sha256(content).hexdigest()!=entry['sha256']: raise ValueError('entry hash mismatch: '+source)
            if 'crop' in entry:
                from PIL import Image
                im=Image.open(io.BytesIO(content)); x0,y0,x1,y1=entry['crop']
                if any(type(v) is not int for v in (x0,y0,x1,y1)) or not (0<=x0<x1<=im.width and 0<=y0<y1<=im.height): raise ValueError('invalid crop')
                buf=io.BytesIO(); im.crop((x0,y0,x1,y1)).save(buf,format='PNG'); content=buf.getvalue()
            payloads.append((target,content))
    for entry in notices:
        source=Path(entry['source'])
        if not source.is_absolute(): source=manifest.parent/source
        target=safe_name(entry['output'])
        if target in paths or target=='resource-record.json': raise ValueError('duplicate or reserved output')
        paths.add(target)
        if source.stat().st_size>64*1024*1024: raise ValueError('notice exceeds 64MiB')
        content=source.read_bytes()
        if hashlib.sha256(content).hexdigest()!=entry['sha256']: raise ValueError('notice hash mismatch: '+str(source))
        payloads.append((target,content))
    # Reject file/parent collisions before any output is created.
    for name in paths:
        if any(str(parent) in paths for parent in PurePosixPath(name).parents if str(parent)!='.'):
            raise ValueError('output file conflicts with parent directory')
        if PurePosixPath(name).parts[0]=='resource-record.json': raise ValueError('reserved output')
    for required in spec.get('notice_outputs',[]):
        if required not in paths: raise ValueError('required notice not included')
    if not spec.get('notice_outputs'): raise ValueError('include applicable notices/license entries')
    destination.mkdir(parents=True)
    for target,content in payloads:
        path=destination/target; path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(content)
    record=dict(spec, extracted_sha256={name:hashlib.sha256(data).hexdigest() for name,data in payloads})
    (destination/'resource-record.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('archive','manifest','output'): p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args(); extract(a.archive,a.manifest,a.output)
    print('extracted',a.output)


if __name__=='__main__': main()
