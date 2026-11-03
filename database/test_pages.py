import re
from unittest import mock

import pandas as pd
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
