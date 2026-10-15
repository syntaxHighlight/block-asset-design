import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
import support
from PIL import Image
import fill_regions as regions
import material_noise as noise
import paint_uv_atlas as atlas


def panel():
    return {'version':1, 'pixels_per_unit':1, 'padding_px':1,
            'materials':{'steel':{'tile':'tile.png','border_px':0}},
            'shapes':[{'id':'panel','material':'steel',
                       'outer':{'points':[[0,0],[4,0],[4,4],[0,4]]},
                       'holes':[{'points':[[1,1],[3,1],[3,3],[1,3]]}]}]}


def chart_spec():
    return {'version':1, 'pixels_per_unit':4, 'padding_px':2,
            'meshes':{'Plane':{'loops':4}}, 'charts':[{'id':'Plane:0','mesh':'Plane',
            'faces':[{'id':0,'loops':[0,1,2,3], 'xy':[[0,0],[4,0],[4,4],[0,4]],
                      'xyz':[[0,0,0],[1,0,0],[1,1,0],[0,1,0]],'normal':[0,0,1],
                      'role':'steel','triangles':[[0,1,2],[0,2,3]]}], 'edges':[]}]}


class TextureTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        Image.new('RGB',(1,1),(20,40,60)).save(self.root/'tile.png')

    def test_region_exact_coverage_hole_and_padding(self):
        [(image,info)]=regions.generate(panel(),self.root)
        self.assertEqual(image.size,(6,6)); self.assertEqual(info['coverage_pixels'],12)
        self.assertEqual(image.getpixel((1,1)),(20,40,60,255))
        self.assertEqual(image.getpixel((2,2))[3],0)
        self.assertEqual(image.getpixel((0,0))[3],0)

    def test_region_winding_independent(self):
        config=panel(); [(a,_)]=regions.generate(config,self.root)
        for ring in [config['shapes'][0]['outer'],*config['shapes'][0]['holes']]: ring['points'].reverse()
        [(b,_)]=regions.generate(config,self.root)
        self.assertEqual(a.tobytes(),b.tobytes())

    def test_invalid_contours_and_duplicate_names(self):
        for case in ['touching','crossing','duplicate']:
            with self.subTest(case=case):
                config=panel()
                if case=='touching': config['shapes'][0]['holes'][0]['points']=[[0,1],[2,1],[2,3],[0,3]]
                elif case=='crossing': config['shapes'][0]['outer']['points']=[[0,0],[4,4],[0,4],[4,0]]
                else: config['shapes'].append(copy.deepcopy(config['shapes'][0]))
                with self.assertRaises(ValueError): regions.generate(config,self.root)

    def test_region_cli_preserves_existing_output(self):
        config=self.root/'panel.json'; config.write_text(json.dumps(panel()))
        out=self.root/'result'
        command=[sys.executable,str(support.ROOT/'skills/machine-texture/scripts/fill_regions.py'),
                 '--input',str(config),'--output',str(out)]
        first=subprocess.run(command,capture_output=True,text=True)
        self.assertEqual(first.returncode,0,first.stderr)
        before=(out/'panel.png').read_bytes()
        second=subprocess.run(command,capture_output=True,text=True)
        self.assertNotEqual(second.returncode,0)
        self.assertEqual((out/'panel.png').read_bytes(),before)
        manifest=json.loads((out/'manifest.json').read_text())
        self.assertEqual(manifest['input_sha256'],hashlib.sha256(config.read_bytes()).hexdigest())

    def test_noise_palette_density_and_direction_invariants(self):
        recipe=noise.recipe({'preset':'plate','seed':7})
        switched=noise.recipe({'preset':'plate','seed':7,'direction':'y'})
        values=[]
        for x,y in [(i*.7,i*.3) for i in range(25)]:
            color=noise.sample(recipe,x,y,16); values.append(color)
            self.assertIn(list(color[:3]),recipe['palette']); self.assertEqual(color[3],255)
            self.assertEqual(color,noise.sample(recipe,x*2,y*2,32))
            self.assertEqual(color,noise.sample(switched,y,x,16))
        self.assertGreater(len(set(values)),1)
        changed=noise.recipe({'preset':'plate','seed':8})
        self.assertTrue(any(noise.sample(recipe,i,0)!=noise.sample(changed,i,0) for i in range(32)))

    def test_noise_rejects_bad_recipe(self):
        for extra in [{'seed':-1},{'palette':[[20,20,20],[10,10,10],[30,30,30]]},{'noise_strength':2}]:
            with self.subTest(extra=extra), self.assertRaises(ValueError): noise.recipe({'preset':'plate',**extra})

    def test_atlas_exact_uv_coverage_and_input_hash(self):
        spec=chart_spec(); out=self.root/'atlas'
        layout=atlas.generate(spec,{'version':1,'materials':{'steel':{'procedural':{'preset':'plate','seed':7}}}},out)
        self.assertEqual(layout['size'],[128,128])
        self.assertEqual(layout['mesh_uv']['Plane'],[[2/128,1-2/128],[6/128,1-2/128],[6/128,1-6/128],[2/128,1-6/128]])
        self.assertEqual(layout['charts'][0]['covered_texels'],16)
        with Image.open(out/'pixel_atlas.png') as image:
            self.assertEqual(image.getpixel((3,3))[3],255)
            self.assertEqual(image.getpixel((127,127))[3],0)
            # A UV/triangle boundary is not a structural edge.
            recipe=noise.recipe({'preset':'plate','seed':7 ^ __import__('zlib').crc32(b'Plane')})
            self.assertEqual(image.getpixel((3,3)),noise.sample(recipe,1.5,1.5,4))
        self.assertEqual(layout['input_sha256'],hashlib.sha256(json.dumps(spec,sort_keys=True).encode()).hexdigest())
        self.assertEqual(layout['atlas_sha256'],hashlib.sha256((out/'pixel_atlas.png').read_bytes()).hexdigest())

    def test_atlas_rejects_bad_mapping_without_creating_output(self):
        for kind in ['duplicate','missing','nonfinite']:
            spec=chart_spec(); face=spec['charts'][0]['faces'][0]
            if kind=='duplicate': face['loops'][1]=0
            elif kind=='missing': spec['meshes']['Plane']['loops']=5
            else: face['xy'][0][0]=float('nan')
            out=self.root/kind
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                atlas.generate(spec,{'version':1,'materials':{'steel':{'procedural':{'preset':'plate'}}}},out)
            self.assertFalse(out.exists())

    def test_packing_rectangles_do_not_overlap_or_shrink(self):
        rects=[('a',8,6),('b',3,7),('c',4,2)]
        packed=atlas.pack(rects,16,16); self.assertIsNotNone(packed)
        occupied=set()
        for name,w,h in rects:
            x,y=packed[name]; self.assertGreaterEqual(min(x,y),0)
            self.assertLessEqual(x+w,16); self.assertLessEqual(y+h,16)
            pixels={(i,j) for i in range(x,x+w) for j in range(y,y+h)}
            self.assertFalse(occupied & pixels); occupied |= pixels
        self.assertIsNone(atlas.pack([('large',17,2)],16,16))

    def test_conservative_subpixel_coverage_without_uv_expansion(self):
        spec=chart_spec(); face=spec['charts'][0]['faces'][0]
        face['xy']=[[0,0],[4,0],[4,.1],[0,.1]]
        config={'steel':{'procedural':{'preset':'plate'}}}
        image,stats=atlas.render_chart(spec['charts'][0],config,4,2)
        self.assertEqual(stats['covered_texels'],4)
        self.assertEqual(image.getpixel((3,2))[3],255)
        # Colored padding expands sampling coverage, not the authored UVs.
        self.assertEqual(image.size,(8,5))
        self.assertEqual(face['xy'][2],[4,.1])

    def test_structural_edge_is_painted_once_at_corner(self):
        chart=chart_spec()['charts'][0]
        materials={'steel':{'procedural':{'preset':'plate'}}}
        plain,_=atlas.render_chart(chart,materials,4,2)
        chart['edges']=[{'id':i,'face':0,'role':2,'xy':xy,'length_px':4,'surface_width_px':4}
                        for i,xy in enumerate([[[0,0],[4,0]],[[0,0],[0,4]]])]
        edged,_=atlas.render_chart(chart,materials,4,2)
        self.assertEqual(edged.getpixel((2,2)),tuple(max(0,v-17) for v in plain.getpixel((2,2))[:3])+(255,))
        self.assertEqual(edged.getpixel((4,4)),plain.getpixel((4,4)))

    def test_artwork_stamp_orientation_and_exact_pixels(self):
        image=Image.new('RGBA',(2,2)); image.putdata([(255,0,0,255),(0,255,0,255),(0,0,255,255),(255,255,0,255)])
        stamp={'image':image,'center':[0,0,0],'right':[1,0,0],'up':[0,1,0],'normal':[0,0,1]}
        self.assertEqual(atlas.stamp_sample(stamp,[-.5,.5,0],[0,0,1],1),(0,0))
        self.assertEqual(atlas.stamp_sample(stamp,[.5,-.5,0],[0,0,1],1),(1,1))
        self.assertIsNone(atlas.stamp_sample(stamp,[0,0,1],[0,0,1],1))
        self.assertIsNone(atlas.stamp_sample(stamp,[0,0,0],[0,0,-1],1))

    def test_atlas_keeps_existing_files(self):
        out=self.root/'occupied'; out.mkdir(); (out/'keep').write_text('keep')
        with self.assertRaises(ValueError): atlas.generate(chart_spec(),{'version':1},out)
        self.assertEqual((out/'keep').read_text(),'keep')
        self.assertEqual(len(list(out.iterdir())),1)
