"""Copy an isolated installed skill's tools and run them from an unrelated cwd."""
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
    def setUp(self) -> None:
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        root=Path(self.temp.name)
        self.tools=root/'project tools'; self.project=root/'project assets'; self.runner=root/'unrelated cwd'
        self.project.mkdir(); self.runner.mkdir()
        self.skill=root/'installed skills/block-asset-design'
        shutil.copytree(support.ROOT/'skills/block-asset-design',self.skill,
                        ignore=shutil.ignore_patterns('__pycache__','*.pyc','*.pyo'))
        # These fixture notices verify that locally installed declarations travel with tools.
        (self.skill/'LICENSE.txt').write_text('Generated skill license fixture.')
        (self.skill/'texture/NOTICE.txt').write_text('Generated texture notice fixture.')
        scripts=self.skill/'shared/scripts'
        (scripts/'.hidden.py').write_text('hidden fixture')
        (scripts/'cache.pyc').write_bytes(b'bytecode fixture')
        (scripts/'__pycache__').mkdir()
        (scripts/'__pycache__/cache.py').write_text('cache fixture')
        self.skill_installed=self.file_hashes(self.skill)
        self.copier=self.skill/'setup/scripts/copy_tools.py'
        result=self.copy_tools(self.tools)
        self.assertEqual(result.returncode,0,result.stderr)
        self.installed=self.file_hashes(self.tools)
        for p in self.tools.rglob('*'):
            p.chmod(0o555 if p.is_dir() else 0o444)
        self.tools.chmod(0o555)
        self.addCleanup(self.make_install_writable)

    def make_install_writable(self) -> None:
        self.tools.chmod(0o755)
        for p in self.tools.rglob('*'):
            p.chmod(0o755 if p.is_dir() else 0o644)

    @staticmethod
    def file_hashes(directory: Path) -> dict[str, str]:
        return {str(p.relative_to(directory)):hashlib.sha256(p.read_bytes()).hexdigest()
                for p in directory.rglob('*') if p.is_file()}

    def run_tool(self, script: str, *args: str | int | Path) -> subprocess.CompletedProcess[str]:
        # Python bytecode caches are not task outputs; suppress them in the read-only install.
        return subprocess.run([sys.executable,'-B',str(self.tools/script),*map(str,args)],
                              cwd=self.runner,capture_output=True,text=True)

    def copy_tools(self, output: Path) -> subprocess.CompletedProcess[str]:
        # -I confirms copying requires only stdlib and the installed collection itself.
        return subprocess.run([sys.executable,'-I','-B',str(self.copier),'--output',str(output)],
                              cwd=self.runner,capture_output=True,text=True)

    def assert_install_untouched(self) -> None:
        self.assertEqual(self.file_hashes(self.tools),self.installed)
        self.assertEqual(self.file_hashes(self.skill),self.skill_installed)
        self.assertEqual(list(self.runner.iterdir()),[])

    def test_local_copy_runs_diagnostics_and_atlas_cli(self) -> None:
        source=self.project/'snapshot.json'; source.write_text(json.dumps(square()))
        before=source.read_bytes(); output=self.project/'build/machine-design/example/report.json'
        args=('--input',source,'--output',output,'--mode','uv','--size',16,16,'--density',16)
        result=self.run_tool('checks/mesh_checks.py',*args)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(json.loads(output.read_text())['status'],'checked')
        self.assertEqual(source.read_bytes(),before)
        report=output.read_bytes()
        self.assertNotEqual(self.run_tool('checks/mesh_checks.py',*args).returncode,0)
        self.assertEqual(output.read_bytes(),report)
        source.write_text(json.dumps(chart_spec())); config=self.project/'materials.json'
        config.write_text(json.dumps({'version':1,'materials':{'steel':{'procedural':{'preset':'plate'}}}}))
        atlas=self.project/'assets/machines/example/atlas'
        result=self.run_tool('texture/paint_uv_atlas.py',
                             '--input',source,'--config',config,'--output',atlas)
        self.assertEqual(result.returncode,0,result.stderr)
        layout=json.loads((atlas/'pixel-atlas-layout.json').read_text())
        self.assertEqual(layout['charts'][0]['covered_texels'],16)
        self.assertEqual(layout['atlas_sha256'],hashlib.sha256((atlas/'pixel_atlas.png').read_bytes()).hexdigest())
        self.assert_install_untouched()

    def test_extraction_writes_to_project_and_resolves_notice_beside_manifest(self) -> None:
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
        result=self.run_tool('resources/extract_resources.py',
                             '--archive',archive,'--manifest',manifest,'--output',output)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual((output/'textures/panel.png').read_bytes(),payload)
        self.assertEqual((output/'notices/LICENSE.txt').read_bytes(),notice.read_bytes())
        record=json.loads((output/'resource-record.json').read_text())
        self.assertEqual(record['extracted_sha256']['textures/panel.png'],hashlib.sha256(payload).hexdigest())
        self.assertEqual(self.file_hashes(inputs),before)
        self.assert_install_untouched()

    def test_regions_resolve_tiles_beside_input_and_write_to_project(self) -> None:
        inputs=self.project/'panel inputs'; inputs.mkdir()
        Image.new('RGB',(1,1),(20,40,60)).save(inputs/'tile.png')
        config=inputs/'regions.json'; config.write_text(json.dumps(panel()))
        before=self.file_hashes(inputs); output=self.project/'assets/machines/example/panels'
        result=self.run_tool('texture/fill_regions.py',
                             '--input',config,'--output',output,'--preview')
        self.assertEqual(result.returncode,0,result.stderr)
        with Image.open(output/'panel.png') as image:
            self.assertEqual(image.size,(6,6)); self.assertEqual(image.getpixel((1,1)),(20,40,60,255))
            self.assertEqual(image.getpixel((2,2))[3],0)
        self.assertTrue((output/'manifest.json').is_file())
        self.assertTrue((output/'specimens.png').is_file())
        self.assertEqual(self.file_hashes(inputs),before)
        self.assert_install_untouched()

    def test_local_copy_layout_dependencies_and_notices(self) -> None:
        self.assertEqual({path.name for path in self.tools.iterdir() if path.is_dir()},
                         {'checks','texture','review','resources'})
        for relative in ('texture/requirements.txt','resources/requirements.txt'):
            self.assertIn('Pillow>=10',(self.tools/relative).read_text())
        self.assertEqual((self.tools/'LICENSE.txt').read_bytes(),(self.skill/'LICENSE.txt').read_bytes())
        for family in ('checks','texture','review','resources'):
            self.assertEqual((self.tools/family/'LICENSE.txt').read_bytes(),
                             (self.skill/'LICENSE.txt').read_bytes())
        self.assertEqual((self.tools/'texture/NOTICE.txt').read_bytes(),
                         (self.skill/'texture/NOTICE.txt').read_bytes())
        self.assertFalse(any('skills' in Path(name).parts or '__pycache__' in Path(name).parts
                             or any(part.startswith('.') for part in Path(name).parts)
                             or name.endswith(('.pyc','.pyo')) for name in self.installed))
        self.assert_install_untouched()

    def test_existing_copy_is_rejected_and_local_adaptations_are_preserved(self) -> None:
        self.make_install_writable()
        (self.tools/'checks/mesh_checks.py').write_text('project-local adaptation')
        (self.tools/'local.txt').write_text('project-local extra file')
        adapted=self.file_hashes(self.tools)
        result=self.copy_tools(self.tools)
        self.assertNotEqual(result.returncode,0)
        self.assertIn('output already exists',result.stderr)
        self.assertEqual(self.file_hashes(self.tools),adapted)
        self.assertEqual(self.file_hashes(self.skill),self.skill_installed)

    def test_existing_empty_directory_file_and_broken_symlink_are_rejected(self) -> None:
        for kind in ('directory','file','symlink'):
            output=self.project/kind
            if kind=='directory':
                output.mkdir()
            elif kind=='file':
                output.write_text('existing file')
            else:
                output.symlink_to(self.project/'missing')
            with self.subTest(kind=kind):
                result=self.copy_tools(output)
                self.assertNotEqual(result.returncode,0)
                self.assertIn('output already exists',result.stderr)
        self.assertEqual(list((self.project/'directory').iterdir()),[])
        self.assertEqual((self.project/'file').read_text(),'existing file')
        self.assertEqual((self.project/'symlink').readlink(),self.project/'missing')
        self.assert_install_untouched()

    def test_failed_copy_removes_only_the_new_output(self) -> None:
        output=self.project/'failed tools'
        code='''
import importlib.util
from pathlib import Path
import sys
from unittest.mock import patch
spec = importlib.util.spec_from_file_location('copy_tools', sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
original = module.shutil.copy2
calls = 0
def fail_after_first_copy(source: Path, target: Path) -> None:
    global calls
    calls += 1
    if calls == 2:
        raise OSError('injected copy failure')
    original(source, target)
with patch.object(module.shutil, 'copy2', side_effect=fail_after_first_copy):
    try:
        module.copy_tools(Path(sys.argv[2]))
    except OSError as error:
        assert str(error) == 'injected copy failure'
    else:
        raise AssertionError('copy unexpectedly succeeded')
assert calls == 2
'''
        result=subprocess.run([sys.executable,'-I','-B','-c',code,str(self.copier),str(output)],
                              cwd=self.runner,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertFalse(output.exists())
        self.assertTrue(output.parent.is_dir())
        self.assert_install_untouched()

    def test_blender_dependencies_import_without_source_checkout(self) -> None:
        code='''
import importlib.util
from pathlib import Path
import sys
root = Path(sys.argv[1]).resolve()
for name, relative in (('blender_atlas', 'texture/blender_atlas.py'),
                       ('blender_audit', 'checks/blender_audit.py'),
                       ('review_views', 'review/review_views.py')):
    spec = importlib.util.spec_from_file_location(name, root / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
for name in ('blender_objects', 'mesh_math', 'mesh_checks'):
    assert Path(sys.modules[name].__file__).parent == root / 'checks', name
assert 'bpy' not in sys.modules
'''
        # -I removes inherited import paths, including the source-tree test helpers.
        result=subprocess.run([sys.executable,'-I','-B','-c',code,str(self.tools)],
                              cwd=self.runner,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assert_install_untouched()

    def test_isolated_skill_atlas_imports_checks(self) -> None:
        code='''
import importlib.util
from pathlib import Path
import sys
root = Path(sys.argv[1]).resolve()
spec = importlib.util.spec_from_file_location('blender_atlas', root / 'texture/scripts/blender_atlas.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
for name in ('blender_objects', 'mesh_math'):
    assert Path(sys.modules[name].__file__).parent == root / 'shared/scripts', name
'''
        result=subprocess.run([sys.executable,'-I','-B','-c',code,str(self.skill)],
                              cwd=self.runner,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assert_install_untouched()
