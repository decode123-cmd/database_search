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

    def test_the_text_under_the_figures_follows_the_chosen_figure(self):
        self.assertIn('data-heading-target="#mechanismHeading" data-text-target="#mechanismText"', self.page)
        self.assertIn('id="mechanismHeading"', self.page)
        self.assertIn('id="mechanismText"', self.page)
        self.assertEqual(self.page.count('data-heading="'), 4)   # the four charts; figure 1 keeps the text the page was loaded with
        self.assertEqual(self.page.count('data-text="'), 4)


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


class SuggestedLiteratureTests(SimpleTestCase):
    COLUMNS = ['pmid', 'year', 'journal', 'title', 'pubmed_url', 'ai_verdict', 'ai_study_type', 'ai_drugs', 'ai_cancer_type',
               'ai_immune_readouts', 'ai_reason', 'drug_entries_in_database (cell/animal/patient)', 'curator_decision', 'curator_notes']

    def write(self, rows):
        import csv
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = os.path.join(directory.name, 'candidates.csv')
        with open(path, 'w', newline='', encoding='utf-8-sig') as handle:
            writer = csv.DictWriter(handle, fieldnames=self.COLUMNS)
            writer.writeheader()
            for row in rows:
                writer.writerow({**{c: '' for c in self.COLUMNS}, **row})
        return path

    def get(self, rows, url='/suggested-literature/'):
        with self.settings(CANDIDATE_PAPERS=self.write(rows)):
            return self.client.get(url)

    def article(self, pmid, **fields):
        return {'pmid': pmid, 'year': '2024', 'title': f'Title {pmid}', 'ai_verdict': 'relevant', 'ai_study_type': 'animal',
                'ai_drugs': 'Pembrolizumab', 'ai_cancer_type': 'Lung', **fields}

    def test_the_page_says_the_articles_are_not_in_the_database_yet(self):
        page = self.get([self.article('111')]).content.decode()
        self.assertIn('not part of the database yet', page)
        self.assertIn('href="https://pubmed.ncbi.nlm.nih.gov/111/"', page)
        self.assertIn('Awaiting curator check', page)

    def test_the_menu_links_to_the_page(self):
        self.assertIn('href="/suggested-literature/">Suggested literature', self.get([self.article('1')]).content.decode())

    def test_only_likely_relevant_articles_are_shown_unless_asked_otherwise(self):
        rows = [self.article('1'), self.article('2', ai_verdict='not_relevant'), self.article('3', ai_verdict='uncertain')]
        page = self.get(rows).content.decode()
        self.assertIn('Title 1', page)
        self.assertNotIn('Title 2', page)
        everything = self.get(rows, '/suggested-literature/?verdict=all').content.decode()
        self.assertTrue(all(f'Title {n}' in everything for n in '123'))

    def test_year_study_type_and_text_filters(self):
        rows = [self.article('1', year='2021'), self.article('2', year='2025', ai_study_type='patient'),
                self.article('3', year='2025', ai_drugs='Nivolumab')]
        self.assertNotIn('Title 1', self.get(rows, '/suggested-literature/?year=2025').content.decode())
        by_type = self.get(rows, '/suggested-literature/?study=patient').content.decode()
        self.assertIn('Title 2', by_type)
        self.assertNotIn('Title 3', by_type)
        by_text = self.get(rows, '/suggested-literature/?q=nivolumab').content.decode()
        self.assertIn('Title 3', by_text)
        self.assertNotIn('Title 1', by_text)

    def test_text_from_the_file_is_escaped(self):
        page = self.get([self.article('1', title='<script>alert(1)</script>')]).content.decode()
        self.assertNotIn('<script>alert(1)</script>', page)
        self.assertIn('&lt;script&gt;', page)

    def test_a_row_without_a_numeric_pubmed_id_is_left_out(self):
        page = self.get([self.article('1'), self.article('12; DROP TABLE', title='Bad row')]).content.decode()
        self.assertNotIn('Bad row', page)

    def test_the_curators_decision_is_shown(self):
        rows = [self.article('1', curator_decision='accepted'), self.article('2')]
        response = self.get(rows)
        page = response.content.decode()
        self.assertIn('Accepted', page)
        self.assertEqual(response.context['accepted'], 1)
        self.assertEqual(response.context['checked'], 1)

    def test_long_lists_are_split_into_pages(self):
        rows = [self.article(str(n)) for n in range(1, 31)]
        first = self.get(rows)
        self.assertEqual(len(first.context['rows']), 25)
        self.assertEqual(first.context['pages'], 2)
        self.assertEqual(len(self.get(rows, '/suggested-literature/?page=2').context['rows']), 5)
        self.assertEqual(self.get(rows, '/suggested-literature/?page=abc').context['page'], 1)
        self.assertEqual(self.get(rows, '/suggested-literature/?page=99').context['page'], 2)

    def test_the_list_can_be_downloaded(self):
        response = self.get([self.article('1')], '/suggested-literature/download.csv')
        self.assertEqual(response.status_code, 200)
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertIn(b'Title 1', response.content)

    def test_a_missing_file_gives_a_polite_page_and_a_404_download(self):
        with self.settings(CANDIDATE_PAPERS=os.path.join(tempfile.gettempdir(), 'no_such_candidates.csv')):
            self.assertIn('not available right now', self.client.get('/suggested-literature/').content.decode())
            self.assertEqual(self.client.get('/suggested-literature/download.csv').status_code, 404)
