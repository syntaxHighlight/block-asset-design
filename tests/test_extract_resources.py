import hashlib
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
import support
from PIL import Image
from extract_resources import extract


class ExtractionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name); self.archive=self.root/'input.zip'; self.manifest=self.root/'input.json'
        image=Image.new('RGB',(3,2),(20,40,60)); image.putpixel((1,0),(200,0,0))
        buffer=io.BytesIO(); image.save(buffer,format='PNG')
        payloads={'texture.png':buffer.getvalue(),'LICENSE.txt':b'Test-only original fixture.'}
        with zipfile.ZipFile(self.archive,'w') as z:
            for name,data in payloads.items(): z.writestr(name,data)
        self.spec={'version':1,'archive_sha256':hashlib.sha256(self.archive.read_bytes()).hexdigest(),
                   'usage_status':'confirmed','usage_scope':'tests','permission_evidence':'generated fixtures',
                   'notice_outputs':['LICENSE.txt'],'entries':[{'source':name,'output':name,'sha256':hashlib.sha256(data).hexdigest()} for name,data in payloads.items()]}
        self.out=self.root/'out'

    def perform(self):
        self.manifest.write_text(json.dumps(self.spec)); extract(self.archive,self.manifest,self.out)

    def test_exact_crop_notice_and_output_hash(self):
        self.spec['entries'][0]['crop']=[1,0,3,1]; self.perform()
        with Image.open(self.out/'texture.png') as image:
            self.assertEqual(image.size,(2,1)); self.assertEqual(image.getpixel((0,0)),(200,0,0))
            self.assertEqual(image.getpixel((1,0)),(20,40,60))
        self.assertEqual((self.out/'LICENSE.txt').read_bytes(),b'Test-only original fixture.')
        record=json.loads((self.out/'resource-record.json').read_text())
        for name,digest in record['extracted_sha256'].items(): self.assertEqual(hashlib.sha256((self.out/name).read_bytes()).hexdigest(),digest)

    def test_bad_hashes_rejected_before_output(self):
        for place in ['archive','entry']:
            with self.subTest(place=place):
                if place=='archive': self.spec['archive_sha256']='0'*64
                else:
                    self.spec['archive_sha256']=hashlib.sha256(self.archive.read_bytes()).hexdigest()
                    self.spec['entries'][0]['sha256']='0'*64
                with self.assertRaises(ValueError): self.perform()
                self.assertFalse(self.out.exists())

    def test_unsafe_duplicate_reserved_and_notice_paths(self):
        for name in ['../escape','/absolute','a\\b','a:b','LICENSE.txt','resource-record.json']:
            with self.subTest(name=name):
                self.spec['entries'][0]['output']=name
                with self.assertRaises(ValueError): self.perform()
                self.assertFalse(self.out.exists())

    def test_permission_notice_crop_and_existing_directory(self):
        original=json.loads(json.dumps(self.spec))
        for case in ['permission','notice','crop','existing']:
            self.spec=json.loads(json.dumps(original))
            if case=='permission': self.spec['usage_status']='unknown'
            elif case=='notice': self.spec['notice_outputs']=[]
            elif case=='crop': self.spec['entries'][0]['crop']=[0,0,4,1]
            else: self.out.mkdir(); (self.out/'keep').write_text('keep')
            with self.subTest(case=case), self.assertRaises(ValueError): self.perform()
            if case=='existing': self.assertEqual((self.out/'keep').read_text(),'keep')
            else: self.assertFalse(self.out.exists())

    def use_external_notice(self):
        self.spec['entries']=self.spec['entries'][:1]
        notice=self.root/'upstream-license.txt'; notice.write_bytes(b'License from pinned source checkout.')
        self.spec['notice_files']=[{'source':notice.name,'output':'notices/LICENSE.txt',
                                  'sha256':hashlib.sha256(notice.read_bytes()).hexdigest()}]
        self.spec['notice_outputs']=['notices/LICENSE.txt']
        return notice

    def test_external_fixed_source_notice_preserved_and_recorded(self):
        notice=self.use_external_notice(); self.perform()
        self.assertEqual((self.out/'notices/LICENSE.txt').read_bytes(),notice.read_bytes())
        record=json.loads((self.out/'resource-record.json').read_text())
        self.assertEqual(record['notice_files'],self.spec['notice_files'])
        self.assertEqual(record['extracted_sha256']['notices/LICENSE.txt'],hashlib.sha256(notice.read_bytes()).hexdigest())

    def test_external_notice_mismatch_and_collision_before_output(self):
        self.use_external_notice(); original=json.loads(json.dumps(self.spec))
        for case in ['hash','duplicate','parent','reserved','empty']:
            self.spec=json.loads(json.dumps(original)); entry=self.spec['notice_files'][0]
            if case=='hash': entry['sha256']='0'*64
            elif case=='duplicate': entry['output']='texture.png'
            elif case=='parent': entry['output']='texture.png/LICENSE.txt'
            elif case=='reserved': entry['output']='resource-record.json/LICENSE.txt'
            else: entry['output']='.'
            with self.subTest(case=case), self.assertRaises(ValueError): self.perform()
            self.assertFalse(self.out.exists())

    def test_relocated_extraction_cli_from_another_directory(self):
        import subprocess
        import sys
        notice=self.use_external_notice(); self.manifest.write_text(json.dumps(self.spec))
        result=subprocess.run([sys.executable,str(support.ROOT/'skills/mod-resource-extract/scripts/extract_resources.py'),
                               '--archive',str(self.archive),'--manifest',str(self.manifest),'--output',str(self.out)],
                              cwd=self.root,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual((self.out/'notices/LICENSE.txt').read_bytes(),notice.read_bytes())
