#!/usr/bin/env python

import json

from django.utils.functional import cached_property
from django.utils import six
from django.db.models import Lookup


class FilterTree:
    """This class should properly assemble the pieces necessary to write the WHERE clause of
    a postgres query
    The jsonb_filter_field property of your view should designate the
    name of the column to filter by.
    Manually filtering by way of Django's ORM might look like:
    Something.objects.filter(jsonfield__jsonb=filter_specification)"""

    def __init__(self, tree, field):
        self.field = field
        self.tree = tree
        self.rules = self.get_rules(self.tree)

    def is_rule(self, obj):
        """Check for bottoming out the recursion in `get_rules`"""
        if '_rule_type' in obj:
            return True
        else:
            return False

    def get_rules(self, obj, current_path=[]):
        """Recursively crawl a dict looking for filtering rules"""
        # If node is a rule return its location and its details
        if self.is_rule(obj):
            return [(current_path, obj)]

        # If node isn't a rule or dictionary
        if type(obj) != dict:
            return []

        rules = []
        for path, val in obj.items():
            rules = rules + self.get_rules(val, current_path + [path])
        return rules

    def sql(self):
        """Produce output that can, jointly, be compiled into SQL by Django and psycopg2.

        The format of the output should be a tuple with a string followed by a list
        of parameters for compiling that string's templated sections
        """
        rule_specs = []
        for rule in self.rules:
            # If not a properly registered rule type
            if '_rule_type' not in rule[1]:
                pass
            rule_type = rule[1]['_rule_type']

            if rule_type == 'intrange':
                rule_specs.append(intrange_filter(rule[0], rule[1]))
            if rule_type == 'containment':
                rule_specs.append(containment_filter(rule[0], rule[1]))
        rule_strings = [rule[0] for rule in rule_specs]
        # flatten the rule_paths
        rule_paths_test = [rule[1] for rule in rule_specs]
        rule_paths = [item for sublist in rule_paths_test
                      for item in sublist]
        outcome = (' AND '.join(rule_strings).format(field=self.field), rule_paths)
        return outcome 


def traversal(path):
    """Construct traversal instructions for Postgres from a list of nodes

    Returns a string like: '{field} -> a -> b ->> c' for {a: {b: {c: value } } }

    """
    fmt_strs = ['%s' for leaf in path]
    multiple_steps = ('->' if len(fmt_strs) > 1 else '')
    traversal = "{field}" + multiple_steps + "->".join(fmt_strs[:-1]) + "->>{final}".format(final=fmt_strs[-1])
    return traversal


def reconstruct_object(path):
    """Construct the object from root to distant leaf, recursively"""
    if len(path) == 0:
        return '%s'
    else:
        return "{{{{%s: {recons}}}}}".format(recons=reconstruct_object(path[1:]))


def containment_filter(path, range_rule):
    """Filter for objects that contain the specified value at some location"""
    containment_path = reconstruct_object(path)
    has_containment = 'contains' in range_rule
    abstract_contains_str = " @> {filter_jobj}"

    if has_containment:
        all_contained = range_rule.get('contains')

    contains_str = ' AND '.join(['{{field}}' + abstract_contains_str.format(filter_jobj=containment_path)
                                 for contained in all_contained])
    contains_params = []
    for contained in all_contained:
        contains_params = contains_params + path + [str(contained)]

    return (contains_str, contains_params)


def intrange_filter(path, range_rule):
    """From a path, a minimum, and a maximum, construct the SQL to process int ranges in json
    range_rule MUST have a minimum or a maximum value to take effect"""
    travInt = "(" + traversal(path) + ")::int"
    has_min = 'min' in range_rule
    has_max = 'max' in range_rule

    if has_min:
        minimum = range_rule['min']
        less_than = ("{traversal_int} <= %s"
                     .format(traversal_int=travInt))

    if has_max:
        maximum = range_rule['max']
        more_than = ("{traversal_int} >= %s"
                     .format(traversal_int=travInt))

    if has_min and not has_max:
        return (more_than, path + range_rule['min'])
    elif has_max and not has_min:
        return (less_than, path + range_rule['max'])
    elif has_max and has_min:
        min_and_max = less_than + ' AND ' + more_than
        return (min_and_max, path + [range_rule['max']] + path + [range_rule['min']])


class DriverLookup(Lookup):
    lookup_name = 'jsonb'

    def as_sql(self, qn, connection):
        lhs, lhs_params = self.process_lhs(qn, connection)
        rhs, rhs_params = self.process_rhs(qn, connection)

        return FilterTree(rhs_params[0], lhs).sql()


def test():
    mock_rule = {'_rule_type': 'sort of a cheat'}
    mock_int_rule = {'_rule_type': 'intrange', 'min': 1, 'max': 5}
    mock_contains_rule = {'_rule_type': 'containment', 'contains': ['test1', 'a thing']}

    distraction = {'alpha': {'beta': {'gamma': {'delta': mock_int_rule}, 'distraction': []}}}
    distraction_tree = FilterTree(distraction, 'data')

    two_rules = {'testing': mock_int_rule,
                 'alpha': {'beta': {'gamma': {'delta': mock_rule},
                                    'distraction': []}}}
    two_rule_tree = FilterTree(two_rules, 'data')

    containment_object = {'a': {'b': {'c': mock_contains_rule}}}
    containment_tree = FilterTree(containment_object, 'data')

    print(traversal(['a', 'b', 'c']))
    assert(traversal(['a', 'b', 'c']) == "{field}->%s->%s->>%s")

    print(two_rule_tree.rules)
    assert(two_rule_tree.rules == [(['alpha', 'beta', 'gamma', 'delta'], mock_rule), (['testing'], mock_int_rule)])
    print(two_rule_tree.sql())
    assert(two_rule_tree.sql() == ('(data->>%s)::int <= %s AND (data->>%s)::int >= %s', ['testing', 5, 'testing', 1]))

    print(distraction_tree.rules)
    assert(distraction_tree.rules == [(['alpha', 'beta', 'gamma', 'delta'], mock_int_rule)])
    print(distraction_tree.sql())
    assert(distraction_tree.sql() == ('(data->%s->%s->%s->>%s)::int <= %s AND (data->%s->%s->%s->>%s)::int >= %s', ['alpha', 'beta', 'gamma', 'delta', 5, 'alpha', 'beta', 'gamma', 'delta', 1]))

    print(containment_tree.rules, containment_tree.sql())
    assert(containment_tree.rules == [(['a', 'b', 'c'], mock_contains_rule)])
    print(containment_tree.sql())
    assert(containment_tree.sql() == ('{field} @> {%s: {%s: {%s: %s}}} AND {field} @> {%s: {%s: {%s: %s}}}', ['a', 'b', 'c', 'test1', 'a', 'b', 'c', 'a thing']))

    print('Success')
