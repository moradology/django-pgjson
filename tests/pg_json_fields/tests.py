# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import
import json

import django, uuid

from django.core.serializers import serialize, deserialize
from django.test import TestCase
from django.test.utils import override_settings

from django_pgjson.fields import JsonField

from .models import TextModel, TextModelB, TextModelWithDefault
from .models import TextModelWithIndent

class JsonBFieldTests(JsonFieldTests):
    def setUp(self):
        self.model_class = TextModelB

    def test_jcontains_lookup1(self):
        self.model_class.objects.create(data=[1, 2, [1, 3]])
        self.model_class.objects.create(data=[4, 5, 6])

        qs = self.model_class.objects.filter(data__jcontains=[[1, 3]])
        self.assertEqual(qs.count(), 1)

        qs = self.model_class.objects.filter(data__jcontains=[4, 6])
        self.assertEqual(qs.count(), 1)

        qs = self.model_class.objects.filter(data__jcontains='[4, 6]')
        self.assertEqual(qs.count(), 1)

    def test_jcontains_lookup2(self):
        self.model_class.objects.create(data={"title": "An action story", "tags": ["violent", "romantic"]})
        self.model_class.objects.create(data={"title": "A sad story", "tags": ["sad", "romantic"]})
        self.model_class.objects.create(data=[4, 5, 6])

        qs = self.model_class.objects.filter(data__jcontains={"tags": ["sad"]})
        self.assertEqual(qs.count(), 1)

    def test_jhas_lookup(self):
        obj1 = self.model_class.objects.create(data={"title": "A sad story", "tags": ["sad", "romantic"]})
        obj2 = self.model_class.objects.create(data={"title": "A sadder story", "tags": ["sad", "sadder", "romantic"]})

        qs = self.model_class.objects.filter(data__jhas="title")
        self.assertEqual(qs.count(), 2)
        qs = self.model_class.objects.filter(data__jhas="doesntexist")
        self.assertEqual(qs.count(), 0)

    def test_jhas_lookup_type_coercion(self):
        obj1 = self.model_class.objects.create(data={"title": "A sad story", "tags": ["sad", "romantic"]})
        obj2 = self.model_class.objects.create(data={"123": "A sad story", "tags": ["sad", "romantic"]})

        qs = self.model_class.objects.filter(data__jhas=123)
        self.assertEqual(qs.count(), 1)
        qs = self.model_class.objects.filter(data__jhas=1)
        self.assertEqual(qs.count(), 0)
        with self.assertRaises(TypeError):
            qs = self.model_class.objects.filter(data__jhas={"title": "A sad story"})

    def test_jhas_any_lookup(self):
        obj1 = self.model_class.objects.create(data={"title": "A sad story", "tags": ["sad", "romantic"]})
        obj2 = self.model_class.objects.create(data={"title": "A sadder story", "tags": ["sad", "sadder", "romantic"]})

        qs = self.model_class.objects.filter(data__jhas_any=["title", "doesnotexist"])
        self.assertEqual(qs.count(), 2)
        qs = self.model_class.objects.filter(data__jhas_any=["doesntexist", "stillnope"])
        self.assertEqual(qs.count(), 0)

    def test_jhas_any_lookup_type_coercion(self):
        obj1 = self.model_class.objects.create(data={"title": "A sad story", "tags": ["sad", "romantic"]})
        obj2 = self.model_class.objects.create(data={"title": "A sadder story", "tags": ["sad", "sadder", "romantic"]})

        # Coerce other iterables to list
        qs = self.model_class.objects.filter(data__jhas_any=("title", "doesnotexist"))
        self.assertEqual(qs.count(), 2)

        # Coerce int values
        qs = self.model_class.objects.filter(data__jhas_any=("title", 123))
        self.assertEqual(qs.count(), 2)

    def test_jhas_all_lookup(self):
        obj1 = self.model_class.objects.create(data={"title": "A sad story", "tags": ["sad", "romantic"]})
        obj2 = self.model_class.objects.create(data={"title": "A sadder story", "tags": ["sad", "sadder", "romantic"]})

        qs = self.model_class.objects.filter(data__jhas_all=["title", "tags"])
        self.assertEqual(qs.count(), 2)
        qs = self.model_class.objects.filter(data__jhas_all=["doesntexist", "stillnope"])
        self.assertEqual(qs.count(), 0)

    def test_jhas_all_lookup_type_coercion(self):
        obj1 = self.model_class.objects.create(data={"title": "A sad story", "tags": ["sad", "romantic"]})
        obj2 = self.model_class.objects.create(data={"title": "A sadder story", "123": "data", "tags": ["sad", "sadder", "romantic"]})

        # Coerce other iterables to list
        qs = self.model_class.objects.filter(data__jhas_all=("title", "tags"))
        self.assertEqual(qs.count(), 2)

        # Coerce int values
        qs = self.model_class.objects.filter(data__jhas_all=("title", 123))
        self.assertEqual(qs.count(), 1)

