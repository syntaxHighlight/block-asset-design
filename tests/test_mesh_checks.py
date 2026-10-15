import copy
import math
import unittest
import support
import mesh_checks as checks
from mesh_math import intersection_area, singular_values


def square():
    return {'meshes': [{'id': 'Plane', 'vertices': [[0,0,0],[1,0,0],[1,1,0],[0,1,0]],
        'faces': [{'vertices': [0,1,2,3]}], 'triangles': [
            {'vertices': [0,1,2], 'face': 0, 'uv': [[0,0],[1,0],[1,1]]},
            {'vertices': [0,2,3], 'face': 0, 'uv': [[0,0],[1,1],[0,1]]}]}]}


class MeshChecksTests(unittest.TestCase):
    def test_square_has_four_boundaries_and_no_internal_overlap(self):
        report = checks.audit(square(), grid=1, size=(16,16), density=16)
        counts = {name: row['count'] for name,row in report['checks'].items()}
        self.assertEqual(counts.pop('boundary_edges'), 4)
        self.assertTrue(all(count == 0 for count in counts.values()), counts)
        for density in report['density_range']: self.assertAlmostEqual(density,16)

    def test_closed_tetrahedron_has_no_geometry_findings(self):
        faces = [[0,2,1],[0,1,3],[1,2,3],[2,0,3]]
        data = {'meshes': [{'id':'Tetra', 'vertices':[[0,0,0],[1,0,0],[0,1,0],[0,0,1]],
                'faces':[{'vertices': f} for f in faces],
                'triangles':[{'vertices': f,'face': i} for i,f in enumerate(faces)]}]}
        self.assertEqual(checks.audit(data, mode='geometry')['status'], 'checked')

    def test_degenerate_and_nonplanar_faces(self):
        data = square(); mesh = data['meshes'][0]
        mesh['faces'].append({'vertices':[0,0,1]})
        mesh['vertices'][2][2] = .2
        report = checks.audit(data, mode='geometry')['checks']
        self.assertEqual(report['degenerate_faces']['count'], 1)
        self.assertEqual(report['nonplanar_faces']['count'], 1)

    def test_duplicate_surface_reports_orientation(self):
        data = square(); duplicate = copy.deepcopy(data['meshes'][0]); duplicate['id']='Back'
        for tri in duplicate['triangles']: tri['vertices'].reverse()
        data['meshes'].append(duplicate)
        rows=checks.audit(data, mode='geometry')['checks']['coplanar_overlap']
        self.assertEqual(rows['count'], 2)
        self.assertTrue(all(row['orientation']=='opposite' for row in rows['samples']))

    def test_winding_conflict_on_shared_edge(self):
        data = square(); mesh=data['meshes'][0]
        mesh['faces']=[{'vertices':[0,1,2]},{'vertices':[0,3,2]}]
        self.assertEqual(checks.audit(data,mode='geometry')['checks']['winding_conflicts']['count'],1)

    def test_object_grid_override(self):
        data=square(); data['meshes'][0]['vertices'][0][0]=.25
        report=checks.audit(data,mode='geometry',grid=1)
        self.assertEqual(report['checks']['off_grid_vertices']['count'],1)
        data['meshes'][0]['grid_step']=.25
        self.assertEqual(checks.audit(data,mode='geometry',grid=1)['checks']['off_grid_vertices']['count'],0)

    def test_uv_density_uses_actual_nonsquare_image(self):
        self.assertEqual(singular_values([[0,0,0],[2,0,0],[0,1,0]], [[0,0],[32,0],[0,16]]),(16,16))
        report=checks.audit(square(),mode='uv',size=(32,16),density=16)
        self.assertEqual(report['checks']['uv_stretch']['count'],2)
        self.assertEqual(report['checks']['uv_density']['count'],2)

    def test_missing_uv_is_incomplete(self):
        data=square(); del data['meshes'][0]['triangles'][0]['uv']
        report=checks.audit(data,mode='uv')
        self.assertEqual(report['status'],'incomplete')
        self.assertEqual(report['checks']['missing_uv']['count'],1)

    def test_invalid_mapping_and_atlas_domains(self):
        data=square(); tri=data['meshes'][0]['triangles'][0]
        tri['uv']=[[1.1,0],[1.1,0],[1.1,0]]
        report=checks.audit(data,mode='uv',size=(16,16))['checks']
        self.assertEqual(report['uv_out_of_bounds']['count'],1)
        self.assertEqual(report['uv_degenerate']['count'],1)
        data=square(); duplicate=copy.deepcopy(data['meshes'][0]); duplicate['id']='Other'
        data['meshes'].append(duplicate)
        self.assertEqual(checks.audit(data,mode='uv')['checks']['uv_overlap']['count'],2)
        duplicate['uv_domain']='other-atlas'
        self.assertEqual(checks.audit(data,mode='uv')['checks']['uv_overlap']['count'],0)

    def test_pair_budget_marks_incomplete_and_limits_samples(self):
        data=square()
        for i in range(4):
            item=copy.deepcopy(data['meshes'][0]); item['id']=str(i); data['meshes'].append(item)
        report=checks.audit(data, mode='uv',max_pairs=1,max_samples=1)
        self.assertEqual(report['status'],'incomplete')
        self.assertFalse(report['budgets']['uv']['complete'])
        report=checks.audit(data,mode='uv',max_samples=1)
        self.assertGreater(report['checks']['uv_overlap']['count'],1)
        self.assertEqual(len(report['checks']['uv_overlap']['samples']),1)

    def test_clipping_area_and_boundary_contact(self):
        a=[[0,0],[1,0],[1,1],[0,1]]
        self.assertAlmostEqual(intersection_area(a,[[.5,0],[1.5,0],[1.5,1],[.5,1]]),.5)
        self.assertAlmostEqual(intersection_area(a,[[1,0],[2,0],[2,1],[1,1]]),0)
        self.assertAlmostEqual(intersection_area(a,list(reversed(a))),1)

    def test_nonfinite_geometry_is_rejected(self):
        data=square(); data['meshes'][0]['vertices'][0][0]=math.nan
        with self.assertRaises(ValueError): checks.audit(data)

    def test_nonmanifold_edge_has_three_incident_faces(self):
        data=square(); mesh=data['meshes'][0]
        mesh['vertices'].append([.5,-1,0])
        mesh['faces']=[{'vertices':[0,1,2]},{'vertices':[1,0,3]},{'vertices':[0,1,4]}]
        self.assertEqual(checks.audit(data,mode='geometry')['checks']['nonmanifold_edges']['count'],1)

    def test_pixel_alignment_and_mirrored_uv_preserve_density(self):
        data=square()
        for tri in data['meshes'][0]['triangles']:
            tri['uv']=[[1-u,v] for u,v in tri['uv']]
        report=checks.audit(data,mode='uv',size=(16,16),density=16)['checks']
        self.assertEqual(report['uv_stretch']['count'],0)
        self.assertEqual(report['uv_density']['count'],0)
        data['meshes'][0]['triangles'][0]['uv'][0][0]+=.01
        self.assertEqual(checks.audit(data,mode='uv',size=(16,16))['checks']['uv_off_pixel']['count'],1)
