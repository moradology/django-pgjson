# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import
from django.test import TestCase

from .models import TextModel, TextModelB


class JsonFieldTests(TestCase):
    def setUp(self):
        self.model_class = TextModel
        self.model_class.objects.all().delete()


class JsonBFieldTests(JsonFieldTests):
    def setUp(self):
        self.model_class = TextModelB

    def test_intrange_filter(self):
        """Filtering within a range should work"""
        self.model_class.objects.create(data={'a': {'b': {'c': 2}}})
        self.model_class.objects.create(data={'a': {'b': {'c': 2000}}})
        filt = {'a': {'b': {'c': {'_rule_type': 'intrange', 'min': 1, 'max': 5}}}}

        query = self.model_class.objects.filter(data__jsonb=filt)
        self.assertEqual(query.count(), 1)

    def test_containment_filter(self):
        """Filtering within a range should work"""
        self.model_class.objects.create(data={'a': {'b': {'c': 2}}})
        self.model_class.objects.create(data={'a': {'b': {'c': 2000}}})
        filt = {'a': {'b': {'c': {'_rule_type': 'containment', 'contains': [1, 2, 3]}}}}

        query = self.model_class.objects.filter(data__jsonb=filt)
        self.assertEqual(query.count(), 1)
