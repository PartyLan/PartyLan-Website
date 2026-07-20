import json
import re
import unittest
from pathlib import Path

import build


ROOT=Path(__file__).resolve().parents[1]
DIST=ROOT/'dist'


def meta_content(markup, name=None, prop=None):
    attribute=f'name="{name}"' if name else f'property="{prop}"'
    match=re.search(rf'<meta {attribute} content="([^"]*)">',markup)
    return match.group(1) if match else None


class SeoBuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build.ERRORS.clear()
        build.main()

    def page(self, relative_path):
        return (DIST/relative_path).read_text(encoding='utf-8')

    def test_public_pages_have_unique_absolute_canonicals_and_metadata(self):
        routes={
            'index.html':'https://partylan.co.uk/',
            'packages/index.html':'https://partylan.co.uk/packages/',
            'contact/index.html':'https://partylan.co.uk/contact/',
            'terms/index.html':'https://partylan.co.uk/terms/',
            'privacy/index.html':'https://partylan.co.uk/privacy/',
        }
        titles=set()
        descriptions=set()
        for path,canonical in routes.items():
            markup=self.page(path)
            self.assertIn(f'<link rel="canonical" href="{canonical}">',markup)
            self.assertEqual(meta_content(markup,prop='og:url'),canonical)
            self.assertEqual(meta_content(markup,name='robots'),'index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1')
            title=re.search(r'<title>(.*?)</title>',markup).group(1)
            description=meta_content(markup,name='description')
            self.assertTrue(title)
            self.assertTrue(description)
            titles.add(title)
            descriptions.add(description)
        self.assertEqual(len(titles),len(routes))
        self.assertEqual(len(descriptions),len(routes))

    def test_social_images_are_absolute_and_accessible(self):
        markup=self.page('index.html')
        image='https://partylan.co.uk/content/images/gallery_hero_light.jpg'
        self.assertEqual(meta_content(markup,prop='og:image'),image)
        self.assertEqual(meta_content(markup,name='twitter:image'),image)
        self.assertTrue(meta_content(markup,prop='og:image:alt'))
        self.assertEqual(meta_content(markup,name='twitter:card'),'summary_large_image')

    def test_json_ld_is_valid_and_contains_organization_and_faq_entities(self):
        markup=self.page('index.html')
        payload=re.search(r'<script type="application/ld\+json">(.*?)</script>',markup).group(1)
        data=json.loads(payload)
        types={node['@type'] for node in data['@graph']}
        self.assertIn('Organization',types)
        self.assertIn('WebSite',types)
        self.assertIn('FAQPage',types)

    def test_packages_schema_matches_visible_prices(self):
        markup=self.page('packages/index.html')
        payload=re.search(r'<script type="application/ld\+json">(.*?)</script>',markup).group(1)
        data=json.loads(payload)
        services=[node for node in data['@graph'] if node.get('@type')=='Service']
        self.assertEqual({service['offers']['price'] for service in services},{'150'})
        self.assertTrue(all(service['offers']['priceCurrency']=='GBP' for service in services))

    def test_sitemap_and_robots_only_advertise_canonical_public_routes(self):
        sitemap=self.page('sitemap.xml')
        robots=self.page('robots.txt')
        for suffix in ('','packages/','contact/','terms/','privacy/'):
            self.assertIn(f'<loc>https://partylan.co.uk/{suffix}</loc>',sitemap)
        self.assertNotIn('demo-testimonials',sitemap)
        self.assertIn('Sitemap: https://partylan.co.uk/sitemap.xml',robots)

    def test_demo_testimonials_are_not_indexable(self):
        markup=self.page('demo-testimonials.html')
        self.assertEqual(meta_content(markup,name='robots'),'noindex,follow')
        self.assertNotIn('application/ld+json',markup)


if __name__=='__main__':
    unittest.main()
