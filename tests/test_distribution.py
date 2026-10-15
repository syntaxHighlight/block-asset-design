"""Run installed skills from an unrelated cwd, with all assets in a separate project."""
import hashlib
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
import support
from PIL import Image
from test_mesh_checks import square
from test_texture import chart_spec, panel


class DistributionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        root=Path(self.temp.name)
        self.skills=root/'global skills'; self.project=root/'project assets'; self.runner=root/'unrelated cwd'
        self.project.mkdir(); self.runner.mkdir()
        for source in (support.ROOT/'skills').iterdir():
            if (source/'SKILL.md').is_file():
                shutil.copytree(source,self.skills/source.name,ignore=shutil.ignore_patterns('__pycache__'))
        self.installed=self.file_hashes(self.skills)
        for p in self.skills.rglob('*'):
            p.chmod(0o555 if p.is_dir() else 0o444)
        self.skills.chmod(0o555)
        self.addCleanup(self.make_install_writable)

    def make_install_writable(self):
        self.skills.chmod(0o755)
        for p in self.skills.rglob('*'):
            p.chmod(0o755 if p.is_dir() else 0o644)

    @staticmethod
    def file_hashes(directory):
        return {str(p.relative_to(directory)):hashlib.sha256(p.read_bytes()).hexdigest()
                for p in directory.rglob('*') if p.is_file()}

    def run_tool(self, script, *args):
        # Python bytecode caches are not task outputs; suppress them in the read-only install.
        return subprocess.run([sys.executable,'-B',str(self.skills/script),*map(str,args)],
                              cwd=self.runner,capture_output=True,text=True)

    def assert_install_untouched(self):
        self.assertEqual(self.file_hashes(self.skills),self.installed)
        self.assertEqual(list(self.runner.iterdir()),[])

    def test_copied_collection_runs_diagnostics_and_atlas_cli(self):
        source=self.project/'snapshot.json'; source.write_text(json.dumps(square()))
        before=source.read_bytes(); output=self.project/'build/machine-design/example/report.json'
        args=('--input',source,'--output',output,'--mode','uv','--size',16,16,'--density',16)
        result=self.run_tool('machine-design/shared/scripts/mesh_checks.py',*args)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(json.loads(output.read_text())['status'],'checked')
        self.assertEqual(source.read_bytes(),before)
        report=output.read_bytes()
        self.assertNotEqual(self.run_tool('machine-design/shared/scripts/mesh_checks.py',*args).returncode,0)
        self.assertEqual(output.read_bytes(),report)
        source.write_text(json.dumps(chart_spec())); config=self.project/'materials.json'
        config.write_text(json.dumps({'version':1,'materials':{'steel':{'procedural':{'preset':'plate'}}}}))
        atlas=self.project/'assets/machines/example/atlas'
        result=self.run_tool('machine-texture/scripts/paint_uv_atlas.py',
                             '--input',source,'--config',config,'--output',atlas)
        self.assertEqual(result.returncode,0,result.stderr)
        layout=json.loads((atlas/'pixel-atlas-layout.json').read_text())
        self.assertEqual(layout['charts'][0]['covered_texels'],16)
        self.assertEqual(layout['atlas_sha256'],hashlib.sha256((atlas/'pixel_atlas.png').read_bytes()).hexdigest())
        self.assert_install_untouched()

    def test_extraction_writes_to_project_and_resolves_notice_beside_manifest(self):
        inputs=self.project/'resource inputs'; inputs.mkdir()
        archive=inputs/'mod.zip'; manifest=inputs/'extraction.json'; notice=inputs/'LICENSE.txt'
        buffer=io.BytesIO(); Image.new('RGB',(2,2),(20,40,60)).save(buffer,format='PNG')
        payload=buffer.getvalue(); notice.write_bytes(b'Test-only generated fixture.')
        with zipfile.ZipFile(archive,'w') as package:
            package.writestr('textures/panel.png',payload)
        manifest.write_text(json.dumps({
            'version':1,'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
            'usage_status':'confirmed','usage_scope':'tests','permission_evidence':'generated fixture',
            'entries':[{'source':'textures/panel.png','output':'textures/panel.png',
                        'sha256':hashlib.sha256(payload).hexdigest()}],
            'notice_files':[{'source':'LICENSE.txt','output':'notices/LICENSE.txt',
                             'sha256':hashlib.sha256(notice.read_bytes()).hexdigest()}],
            'notice_outputs':['notices/LICENSE.txt']}))
        before=self.file_hashes(inputs); output=self.project/'assets/resources/example-mod/1.0'
        result=self.run_tool('mod-resource-extract/scripts/extract_resources.py',
                             '--archive',archive,'--manifest',manifest,'--output',output)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual((output/'textures/panel.png').read_bytes(),payload)
        self.assertEqual((output/'notices/LICENSE.txt').read_bytes(),notice.read_bytes())
        record=json.loads((output/'resource-record.json').read_text())
        self.assertEqual(record['extracted_sha256']['textures/panel.png'],hashlib.sha256(payload).hexdigest())
        self.assertEqual(self.file_hashes(inputs),before)
        self.assert_install_untouched()

    def test_regions_resolve_tiles_beside_input_and_write_to_project(self):
        inputs=self.project/'panel inputs'; inputs.mkdir()
        Image.new('RGB',(1,1),(20,40,60)).save(inputs/'tile.png')
        config=inputs/'regions.json'; config.write_text(json.dumps(panel()))
        before=self.file_hashes(inputs); output=self.project/'assets/machines/example/panels'
        result=self.run_tool('machine-texture/scripts/fill_regions.py',
                             '--input',config,'--output',output,'--preview')
        self.assertEqual(result.returncode,0,result.stderr)
        with Image.open(output/'panel.png') as image:
            self.assertEqual(image.size,(6,6)); self.assertEqual(image.getpixel((1,1)),(20,40,60,255))
            self.assertEqual(image.getpixel((2,2))[3],0)
        self.assertTrue((output/'manifest.json').is_file())
        self.assertTrue((output/'specimens.png').is_file())
        self.assertEqual(self.file_hashes(inputs),before)
        self.assert_install_untouched()
