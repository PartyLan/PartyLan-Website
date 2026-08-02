import unittest
from unittest.mock import patch

import build


def addon(identifier, available_for):
    return {
        'id': identifier,
        'title': identifier.title(),
        'description': 'Description',
        'available_for': available_for,
        'price_note': 'Ask for options',
    }


class PackageAddonRenderingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.home = build.read_json('homepage.json')
        cls.packages = build.validate_packages(build.read_json('packages.json'))

    def render(self, addons):
        return build.package_page(self.home, self.packages, addons, [], '')

    def validated(self, rows):
        build.ERRORS.clear()
        with patch.object(build, 'read_csv', return_value=rows):
            result = build.validate_rows(
                'virtual-addons.csv',
                ['title', 'description', 'available_for', 'price_note'],
                'addon',
            )
        self.assertEqual(build.ERRORS, [])
        return result

    def test_all_visible_addons_available_for_both_omit_specific_section(self):
        rows = [addon('first', 'both'), addon('second', 'BOTH')]
        for order, row in enumerate(rows, start=1):
            row.update(visible='true', display_order=str(order))
        markup = self.render(self.validated(rows))

        self.assertIn('Available with both packages', markup)
        self.assertNotIn('Package-specific options', markup)

    def test_visible_jade_addon_renders_specific_section(self):
        markup = self.render([addon('shared', 'both'), addon('jade-option', 'JaDe')])

        self.assertIn('Package-specific options', markup)
        self.assertIn('addon-row--jade', markup)
        self.assertIn('JADE', markup)

    def test_visible_onyx_addon_renders_specific_section(self):
        markup = self.render([addon('onyx-option', 'OnYx')])

        self.assertIn('Package-specific options', markup)
        self.assertIn('ONYX', markup)

    def test_hidden_package_specific_addons_omit_specific_section(self):
        hidden = addon('hidden-jade-option', 'jade')
        hidden.update(visible='false', display_order='1')
        markup = self.render(self.validated([hidden]))

        self.assertNotIn('Package-specific options', markup)


if __name__ == '__main__':
    unittest.main()
