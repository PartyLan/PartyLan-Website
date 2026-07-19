import json
import unittest
from unittest.mock import patch

import build


HEADERS=list(build.GALLERY_FIELDS)
EXPERIENCE_IMAGE='/content/images/experience/experience-allages01.png'
MOBILE_IMAGE='/content/images/experience/experience-cta.png'
EQUIPMENT_IMAGE='/content/images/equipment/gallery-hardware-setup01.png'


def record(identifier, category, platform, order, image=EXPERIENCE_IMAGE, **values):
    row={
        'id':identifier,
        'category':category,
        'Platform':platform,
        'image':image,
        'Header':values.get('Header','Header'),
        'Subtext':values.get('Subtext','Subtext'),
        'visible':values.get('visible','true'),
        'display_order':str(order),
    }
    return row


def source(rows):
    return HEADERS,[(line,row) for line,row in enumerate(rows,start=2)]


class GalleryValidationTests(unittest.TestCase):
    def validate(self, rows):
        build.ERRORS.clear()
        with patch.object(build,'read_gallery_source',return_value=source(rows)):
            result=build.validate_gallery_rows('virtual-gallery.csv')
        return result,list(build.ERRORS)

    def test_platform_values_are_trimmed_and_normalised_case_insensitively(self):
        rows=[
            record('experience',' Experience ',' pc ',1),
            record('experience','experience',' MOBILE ',1,image=MOBILE_IMAGE),
            record('equipment','EQUIPMENT',' all ',1,image=EQUIPMENT_IMAGE),
        ]
        result,errors=self.validate(rows)
        self.assertEqual(errors,[])
        self.assertEqual([row['Platform'] for row in result],['PC','Mobile','All'])
        self.assertEqual([row['category'] for row in result],['experience','experience','equipment'])

    def test_ids_and_orders_may_repeat_across_categories_and_pc_mobile(self):
        rows=[
            record('shared', 'Experience','PC',1),
            record('shared', 'Experience','Mobile',1,image=MOBILE_IMAGE),
            record('shared', 'Equipment','PC',1,image=EQUIPMENT_IMAGE),
            record('shared', 'Equipment','Mobile',1,image=EQUIPMENT_IMAGE),
        ]
        result,errors=self.validate(rows)
        self.assertEqual(errors,[])
        self.assertEqual(len({row['_record_key'] for row in result}),4)
        self.assertEqual(len({row['_dom_id'] for row in result}),4)

    def test_all_conflicts_with_specific_platform_by_id_or_order(self):
        rows=[
            record('shared-id','Experience','All',1),
            record('shared-id','Experience','PC',2),
            record('mobile-only','Experience','Mobile',1,image=MOBILE_IMAGE),
            record('equipment','Equipment','All',1,image=EQUIPMENT_IMAGE),
        ]
        _,errors=self.validate(rows)
        message='\n'.join(errors)
        self.assertIn('conflicting ID "shared-id"',message)
        self.assertIn('conflicting order 1',message)
        self.assertIn('earlier line 2 (platform All)',message)
        self.assertIn('Fix:',message)

    def test_exact_duplicate_is_reported_once_without_cascaded_conflicts(self):
        duplicate=record('experience','Experience','All',1)
        rows=[duplicate,dict(duplicate),record('equipment','Equipment','All',1,image=EQUIPMENT_IMAGE)]
        _,errors=self.validate(rows)
        self.assertEqual(sum('exact duplicate row' in error for error in errors),1)
        self.assertFalse(any('duplicate ID within' in error for error in errors))
        self.assertFalse(any('duplicate display_order within' in error for error in errors))

    def test_invalid_order_platform_and_image_path_include_correction_context(self):
        rows=[
            record('bad','Experience','watch','1.5',image='/assets/images/outside.jpg'),
            record('equipment','Equipment','All',1,image=EQUIPMENT_IMAGE),
        ]
        _,errors=self.validate(rows)
        message='\n'.join(errors)
        self.assertIn('line 2 gallery "experience"',message)
        self.assertIn('unsupported or missing Platform value',message)
        self.assertIn('outside the required gallery content location',message)
        self.assertIn('display_order is missing or invalid',message)
        self.assertIn('category has no effective PC content',message)

    def test_generated_tabs_and_panels_have_complete_aria_relationships(self):
        build.ERRORS.clear()
        gallery=build.validate_gallery_rows('gallery.csv')
        home=build.read_json('homepage.json')
        markup=build.showcase(home,gallery)
        self.assertIn('role="tablist" aria-label="Choose gallery view"',markup)
        self.assertIn('id="gallery-tab-experience" aria-controls="gallery-panel-experience"',markup)
        self.assertIn('id="gallery-panel-experience" role="tabpanel" aria-labelledby="gallery-tab-experience"',markup)
        self.assertIn('id="gallery-panel-equipment" role="tabpanel" aria-labelledby="gallery-tab-equipment"',markup)
        self.assertIn('aria-selected="true" tabindex="0"',markup)
        self.assertIn('aria-selected="false" tabindex="-1"',markup)
        self.assertIn('class="gallery-tabs__switch" aria-hidden="true"',markup)
        self.assertNotIn('<button class="gallery-tabs__switch"',markup)
        self.assertNotIn('<img',markup)


if __name__=='__main__':
    unittest.main()
