#!/usr/bin/env python

from django.utils.functional import cached_property
from django.utils import six
from django.db.models import Lookup


class FilterTree:

    def __init__(self, tree):
        self.tree = tree
        self.rules = self.get_rules(self.tree)

    def is_rule(self, obj):
        if '_rule_type' in obj:
            return True
        else:
            return False

    def get_rules(self, obj, current_path=[]):
        """"""
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
        rule_strings = []
        for rule in self.rules:
            # If not a properly registered rule type
            if '_rule_type' not in rule[1]:
                pass
            rule_type = rule[1]['_rule_type']

            if rule_type == 'intrange':
                rule_strings.append(int_range_filter(rule[0], rule[1]))
        return ' AND '.join(rule_strings)


def traversal(path):
    """Construct traversal instructions for Postgres from a list of nodes
    """
    traversal = "data->'" + "'->'".join(path) + "'"
    return traversal


def int_range_filter(path, range_rule):
    """From a path, a minimum, and a maximum, construct the SQL to process int ranges in json
    range_rule MUST have a minimum or a maximum value to take effect"""
    traversalInt = "(" + traversal(path) + ")::int"
    has_min = 'min' in range_rule
    has_max = 'max' in range_rule

    if has_min:
        minimum = range_rule['min']
        less_than = ("{traversal_int} <= {minimum}"
                     .format(traversal_int=traversalInt,
                             minimum=minimum))

    if has_max:
        maximum = range_rule['max']
        more_than = ("{traversal_int} >= {maximum}"
                     .format(traversal_int=traversalInt,
                             maximum=maximum))

    if has_min and not has_max:
        return less_than
    elif has_max and not has_min:
        return more_than
    elif has_max and has_min:
        min_and_max = less_than + ' AND ' + more_than
        return min_and_max


class DriverLookup(Lookup):
    lookup_name = 'jsonb'

    def as_sql(self, qn, connection):
        lhs, lhs_params = self.process_lhs(qn, connection)
        rhs, rhs_params = self.process_rhs(qn, connection)

        rules = FilterTree(rhs).rules

        params = lhs_params + rhs_params
        return '{lhs} = {rhs}'.format(lhs=lhs, rhs=rhs), params

'''
class ExactLookup(Lookup):
    lookup_name = 'exact'

    def as_sql(self, qn, connection):
        lhs, lhs_params = self.process_lhs(qn, connection)
        rhs, rhs_params = self.process_rhs(qn, connection)

        if len(rhs_params) == 1 and hasattr(rhs_params[0], "adapted"):
            adapted = rhs_params[0].adapted
            if isinstance(adapted, six.string_types):
                rhs_params[0] = adapted

        params = lhs_params + rhs_params
        return '%s = %s' % (lhs, rhs), params
'''


def test():
    mock_rule = {'_rule_type': 'sort of a cheat'}
    mock_int_rule = {'_rule_type': 'intrange', 'min': 1, 'max': 5}

    distraction = {'alpha': {'beta': {'gamma': {'delta': mock_rule}, 'distraction': []}}}
    distraction_tree = FilterTree(distraction)

    two_rules = {'testing': mock_int_rule, 'alpha': {'beta': {'gamma': {'delta': mock_rule}, 'distraction': []}}}
    two_rule_tree = FilterTree(two_rules)

    print(distraction_tree.rules)
    print(two_rule_tree.rules)
    print(distraction_tree.sql())
    print(two_rule_tree.sql())
    assert(traversal(['a', 'b', 'c']) == "data->'a'->'b'->'c'")
    assert(two_rule_tree.rules == [(['alpha', 'beta', 'gamma', 'delta'], mock_rule), (['testing'], mock_int_rule)])
    assert(distraction_tree.rules == [(['alpha', 'beta', 'gamma', 'delta'], mock_rule)])
    print('Success')
