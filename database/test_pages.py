import os
import re
import tempfile
from unittest import mock

import pandas as pd
from django.template import Context, Template
from django.test import SimpleTestCase

from .test_api import FakeConnection


class HomePageTests(SimpleTestCase):
    def setUp(self):
        fake = FakeConnection({'Master': pd.DataFrame({'ID': ['CANIMM/1'], 'Drug': ['Gemcitabine']})})
        patcher = mock.patch('database.views.connection', fake)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.page = self.client.get('/').content.decode('utf-8')

    def test_one_name_everywhere(self):
        self.assertIn('<title>CancerImmunoDB</title>', self.page)
        variants = set(re.findall(r'can\s?imm\w*db', self.page, flags=re.I)) - {'CancerImmunoDB'}
        self.assertEqual(variants, set(), 'the database must be called CancerImmunoDB everywhere')

    def test_download_and_api_page_is_linked_and_documented(self):
        self.assertIn('id="api"', self.page)
        self.assertIn("showSubsection('api')", self.page)
        for name in ('cell_line', 'animal_studies', 'patient_studies', 'all'):
            self.assertIn(f'/api/v1/download/{name}.csv', self.page)
            self.assertIn(f'/api/v1/download/{name}.json', self.page)

    def test_every_tool_describes_its_method(self):
        self.assertEqual(self.page.count('class="tool-method"'), 4)

    def test_api_examples_use_the_live_column_spelling(self):
        self.assertIn('?Drug=gemcitabine', self.page)
        self.assertNotIn('DRUG=', self.page)

    def test_immune_term_page_is_in_the_browse_menu(self):
        self.assertIn('class="nav_link Immune"', self.page)
        self.assertIn('id="immune_section"', self.page)
        self.assertIn('id="immune-outcome"', self.page)

    def test_css_and_js_addresses_carry_a_version_so_browsers_do_not_keep_old_files(self):
        for name in ('css/index.css', 'css/mediaquaries.css', 'js/script.js'):
            self.assertRegex(self.page, rf'/static/{re.escape(name)}\?v=[0-9a-f]{{10}}"')

    def test_the_tool_is_spelled_similarity(self):
        self.assertNotIn('Smilarity', self.page)


class StaticVersionTagTests(SimpleTestCase):
    def render(self, path):
        return Template('{% load static_v %}{% static_v path %}').render(Context({'path': path}))

    def test_the_address_changes_exactly_when_the_file_changes(self):
        with tempfile.TemporaryDirectory() as root, self.settings(STATIC_ROOT=root, STATICFILES_DIRS=[]):
            target = os.path.join(root, 'site.css')
            with open(target, 'w') as handle:
                handle.write('a { color: red }')
            first = self.render('site.css')
            self.assertRegex(first, r'^/static/site\.css\?v=[0-9a-f]{10}$')
            self.assertEqual(self.render('site.css'), first)
            with open(target, 'w') as handle:
                handle.write('a { color: blue; margin: 0 }')
            self.assertNotEqual(self.render('site.css'), first)

    def test_a_file_that_does_not_exist_gives_the_plain_address(self):
        with tempfile.TemporaryDirectory() as root, self.settings(STATIC_ROOT=root, STATICFILES_DIRS=[]):
            self.assertEqual(self.render('nothing.css'), '/static/nothing.css')

    def test_the_source_folder_is_used_when_the_collected_copy_is_missing(self):
        with tempfile.TemporaryDirectory() as collected, tempfile.TemporaryDirectory() as source, \
                self.settings(STATIC_ROOT=collected, STATICFILES_DIRS=[source]):
            with open(os.path.join(source, 'only_here.js'), 'w') as handle:
                handle.write('1')
            self.assertRegex(self.render('only_here.js'), r'^/static/only_here\.js\?v=[0-9a-f]{10}$')
