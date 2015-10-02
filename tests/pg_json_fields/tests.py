# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import
from django.test import TestCase

import json

from .models import TextModel, TextModelB

from django_pgjson.lookups import *

class JsonBFieldTests(TestCase):
    def setUp(self):
        self.mock_rule = {'_rule_type': 'sort of a cheat'}
        self.mock_int_rule = {'_rule_type': 'intrange', 'min': 1, 'max': 5}
        self.mock_contains_rule = {'_rule_type': 'containment', 'contains': ['test1', 'a thing']}

        self.two_rules = {'testing': self.mock_int_rule,
                          'alpha': {'beta': {'gamma': {'delta': self.mock_rule},
                                    'distraction': []}}}
        self.two_rule_tree = FilterTree(self.two_rules, 'data')

        self.containment_object = {'a': {'b': {'c': self.mock_contains_rule}}}
        self.containment_tree = FilterTree(self.containment_object, 'data')

        self.distraction = {'alpha': {'beta': {'gamma': {'delta': self.mock_int_rule}, 'distraction': []}}}
        self.distraction_tree = FilterTree(self.distraction, 'data')

    def test_intrange_filter(self):
        """Filtering within a range should work"""
        TextModelB.objects.create(data={'a': {'b': {'c': 2}}})
        TextModelB.objects.create(data={'a': {'b': {'c': 2000}}})
        filt = {'a': {'b': {'c': {'_rule_type': 'intrange', 'min': 1, 'max': 5}}}}

        #query = TextModelB.objects.filter(data__jsonb=filt)
        #self.assertEqual(query.count(), 1)

    def test_containment_filter(self):
        """Filtering within a range should work"""
        TextModelB.objects.create(data={'a': {'b': {'c': 2}}})
        TextModelB.objects.create(data={'a': {'b': {'c': 2000}}})
        filt = {'a': {'b': {'c': {'_rule_type': 'containment', 'contains': [1, 2, 3]}}}}

        #query = TextModelB.objects.filter(data__jsonb=filt)
        #self.assertEqual(query.count(), 1)

    def test_traversal_string_creation(self):
        self.assertEqual(traversal_string(['a', 'b', 'c']), u"a->%s->>%s")

    def test_intrange_rules(self):
        self.assertEqual(self.two_rule_tree.rules, [(['data', 'testing'], self.mock_int_rule)])
        self.assertEqual(self.distraction_tree.rules, [(['data', 'alpha', 'beta', 'gamma', 'delta'], self.mock_int_rule)])

    def test_containment_rules(self):
        self.assertEqual(self.containment_tree.rules, [(['data', 'a', 'b', 'c'], self.mock_contains_rule)])

    def test_intrange_sql(self):
        self.assertEqual(self.two_rule_tree.sql(), (u'(data->>%s)::int <= %s AND (data->>%s)::int >= %s', ('testing', 5, 'testing', 1)))
        self.assertEqual(self.distraction_tree.sql(),
                         (u'(data->%s->%s->%s->>%s)::int <= %s AND (data->%s->%s->%s->>%s)::int >= %s',
                          ('alpha', 'beta', 'gamma', 'delta', 5, 'alpha', 'beta', 'gamma', 'delta', 1)))

    def test_containment_sql(self):
        self.assertEqual(self.containment_tree.sql(),
                         ("data @> %s OR data @> %s",
                          ('{"a": {"b": {"c": "test1"}}}', '{"a": {"b": {"c": "a thing"}}}')))

    def test_containment_output(self):
        self.assertEqual(containment_filter(['a', 'b'], self.mock_contains_rule),
                         ('a @> %s OR a @> %s',
                          [u'{"b": "test1"}', u'{"b": "a thing"}']))

    def test_containment_query(self):
        TextModelB.objects.create(data={'a': {'b': {'c': 1}}})
        TextModelB.objects.create(data={'a': {'b': {'c': 2000}}})

        filt = {'a': {'b': {'c': {'_rule_type': 'containment', 'contains': [1, 2, 3]}}}}
        query = TextModelB.objects.filter(data__jsonb=filt)
        self.assertEqual(query.count(), 1)

        filt2 = {'a': {'b': {'c': {'_rule_type': 'containment', 'contains': [1, 2000, 3]}}}}
        query2 = TextModelB.objects.filter(data__jsonb=filt2)
        self.assertEqual(query2.count(), 2)

    def test_intrange_query(self):
        TextModelB.objects.create(data={'a': {'b': {'c': 1}}})
        TextModelB.objects.create(data={'a': {'b': {'c': 2000}}})

        filt = {'a': {'b': {'c': {'_rule_type': 'intrange', 'min': 1, 'max': 5}}}}
        query = TextModelB.objects.filter(data__jsonb=filt)
        self.assertEqual(query.count(), 1)

        filt2 = {'a': {'b': {'c': {'_rule_type': 'intrange', 'min': 1, 'max': 2005}}}}
        query2 = TextModelB.objects.filter(data__jsonb=filt2)
        self.assertEqual(query2.count(), 2)
