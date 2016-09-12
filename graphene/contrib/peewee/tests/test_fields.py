from datetime import datetime

import peewee

from graphene import ObjectType, Schema
from graphene.contrib.peewee.fields import PeeweeConnectionField
from ..types import PeeweeNode
from .models import Article, Pet, Reporter
from graphene.relay import NodeField


class ArticleNode(PeeweeNode):

    class Meta:
        model = Article


class ReporterNode(PeeweeNode):

    class Meta:
        model = Reporter


class PetNode(PeeweeNode):

    class Meta:
        model = Pet

schema = Schema()


def assert_arguments(field, *arguments):
    ignore = ('after', 'before', 'first', 'last', 'orderBy', 'page', 'paginateBy')
    actual = [
        name
        for name in schema.T(field.arguments)
        if name not in ignore and not name.startswith('_')
    ]
    assert set(arguments) == set(actual), \
        'Expected arguments ({}) did not match actual ({})'.format(
            arguments,
            actual
    )


def assert_orderable(field):
    assert 'orderBy' in schema.T(field.arguments), \
        'Field cannot be ordered'


def assert_not_orderable(field):
    assert 'orderBy' not in schema.T(field.arguments), \
        'Field can be ordered'


def generate_args(fields):
    return ['{}_{}'.format(key, lookup.title()) if lookup else key
            for key in fields
            for lookup in list(peewee.DJANGO_MAP.keys()) + ['']
            ]


def test_filter_shortcut_filters_arguments_list():
    field = PeeweeConnectionField(ArticleNode, filters=['pub_date', 'reporter'])
    expected_args = generate_args(['pubDate',
                                   'reporterId',
                                   'reporter_Id',
                                   'reporter_FirstName',
                                   'reporter_LastName',
                                   'reporter_Email',
                                   'reporter_AChoice',
                                   'reporter_OrganizationId',
                                   'reporter_Organization_Id',
                                   'reporter_Organization_Name',
                                   ])
    assert_arguments(field,
                     *expected_args
                     )


def test_filter_shortcut_filters_arguments_dict():
    field = PeeweeConnectionField(ArticleNode, filters={
        'headline': ['eq', 'ilike'],
        'reporter': {'id': ['eq']},
    })
    assert_arguments(field,
                     'headline', 'headline_Eq', 'headline_Ilike',
                     'reporter_Id', 'reporter_Id_Eq',
                     *generate_args(['reporterId'])
                     )


def test_filter_shortcut_filters_orderable_headline():
    field = PeeweeConnectionField(ArticleNode, order_by=['headline'])
    assert_orderable(field)


def test_filter_filters_information_on_meta():
    class ReporterFilterNode(PeeweeNode):

        class Meta:
            model = Reporter
            filters = ['first_name']

    field = PeeweeConnectionField(ReporterFilterNode)
    expected_args = generate_args(['firstName'])
    assert_arguments(field, *expected_args)
    assert_orderable(field)


def test_filter_filters_information_on_meta_related():
    class ReporterFilterNode(PeeweeNode):

        class Meta:
            model = Reporter
            filters = ['first_name'] # , 'articles'

    class ArticleFilterNode(PeeweeNode):

        class Meta:
            model = Article
            filters = ['headline', 'reporter']

    class Query(ObjectType):
        all_reporters = PeeweeConnectionField(ReporterFilterNode)
        all_articles = PeeweeConnectionField(ArticleFilterNode)
        reporter = NodeField(ReporterFilterNode)
        article = NodeField(ArticleFilterNode)

    schema = Schema(query=Query)
    _ = schema.schema  # Trigger the schema loading
    articles_field = schema.get_type('ReporterFilterNode')._meta.fields_map['articles']
    expected_args = generate_args([
        'headline',
        'reporterId',
        'reporter_Id',
        'reporter_FirstName',
        'reporter_LastName',
        'reporter_Email',
        'reporter_AChoice',
        'reporter_OrganizationId',
        'reporter_Organization_Id',
        'reporter_Organization_Name',
    ])
    assert_arguments(articles_field, *expected_args)
    assert_orderable(articles_field)


def test_filter_filters_related_results():
    class ReporterFilterNode(PeeweeNode):

        class Meta:
            model = Reporter
            filters = ['first_name'] # , 'articles'

    class ArticleFilterNode(PeeweeNode):

        class Meta:
            model = Article
            filters = ['headline', 'reporter']

    class Query(ObjectType):
        all_reporters = PeeweeConnectionField(ReporterFilterNode)
        all_articles = PeeweeConnectionField(ArticleFilterNode)
        reporter = NodeField(ReporterFilterNode)
        article = NodeField(ArticleFilterNode)

    now = datetime.now()
    reporter1 = Reporter(first_name='r1', last_name='r1', email='r1@test.com')
    reporter1.save()
    reporter2 = Reporter(first_name='r2', last_name='r2', email='r2@test.com')
    reporter2.save()
    article1 = Article(headline='a1', pub_date=now, reporter=reporter1)
    article1.save()
    article2 = Article(headline='a2', pub_date=now, reporter=reporter2)
    article2.save()

    query = '''
    query {
        allReporters {
            edges {
                node {
                    articles {
                        edges {
                            node {
                                headline
                            }
                        }
                    }
                }
            }
        }
    }
    '''
    expected_data = {'allReporters': {'edges': [
        {'node': {'articles': {'edges': [{'node': {'headline': 'a1'}}]}}},
        {'node': {'articles': {'edges': [{'node': {'headline': 'a2'}}]}}}]}}
    schema = Schema(query=Query)
    result = schema.execute(query)
    assert not result.errors
    assert result.data == expected_data

    article1.delete().execute()
    article2.delete().execute()
    reporter1.delete().execute()
    reporter2.delete().execute()


def test_filter_filters_filters_camel_case():
    class ReporterFilterNode(PeeweeNode):

        class Meta:
            model = Reporter
            filters = ['first_name'] # , 'articles'

    class Query(ObjectType):
        all_reporters = PeeweeConnectionField(ReporterFilterNode)
        reporter = NodeField(ReporterFilterNode)

    reporter2 = Reporter(first_name='r2', last_name='r2', email='r2@test.com')
    reporter2.save()
    reporter1 = Reporter(first_name='r1', last_name='r1', email='r1@test.com')
    reporter1.save()

    query = '''
    query {
        allReporters(firstName_Eq: "r1") {
            edges {
                node {
                    firstName
                }
            }
        }
    }
    '''
    expected_data = {'allReporters':
                         {'edges': [{'node': {'firstName': 'r1'}}]}}
    schema = Schema(query=Query)
    result = schema.execute(query)
    assert not result.errors
    assert result.data == expected_data

    reporter1.delete().execute()
    reporter2.delete().execute()


def test_filter_filters_order_by_camel_case():
    class ReporterFilterNode(PeeweeNode):

        class Meta:
            model = Reporter
            filters = ['first_name'] # , 'articles'

    class Query(ObjectType):
        all_reporters = PeeweeConnectionField(ReporterFilterNode)
        reporter = NodeField(ReporterFilterNode)

    reporter2 = Reporter(first_name='r2', last_name='r2', email='r2@test.com')
    reporter2.save()
    reporter1 = Reporter(first_name='r1', last_name='r1', email='r1@test.com')
    reporter1.save()

    query = '''
    query {
        allReporters(orderBy: ["firstName"]) {
            edges {
                node {
                    firstName
                }
            }
        }
    }
    '''
    expected_data = {'allReporters': {'edges': [{'node': {'firstName': 'r1'}},
                                                {'node': {'firstName': 'r2'}}]}
                     }
    schema = Schema(query=Query)
    result = schema.execute(query)
    assert not result.errors
    assert result.data == expected_data

    reporter1.delete().execute()
    reporter2.delete().execute()


def test_filter_filters_paginate_camel_case():
    class ReporterFilterNode(PeeweeNode):

        class Meta:
            model = Reporter
            filters = ['first_name'] # , 'articles'

    class Query(ObjectType):
        all_reporters = PeeweeConnectionField(ReporterFilterNode)
        reporter = NodeField(ReporterFilterNode)

    reporter1 = Reporter(first_name='r1', last_name='r1', email='r1@test.com')
    reporter1.save()
    reporter2 = Reporter(first_name='r2', last_name='r2', email='r2@test.com')
    reporter2.save()
    reporter3 = Reporter(first_name='r3', last_name='r3', email='r3@test.com')
    reporter3.save()
    reporter4 = Reporter(first_name='r4', last_name='r4', email='r4@test.com')
    reporter4.save()

    query = '''
    query {
        allReporters(page: 2, paginateBy: 2, orderBy: ["firstName"]) {
            edges {
                node {
                    firstName
                }
            }
        }
    }
    '''
    expected_data = {'allReporters': {'edges': [{'node': {'firstName': 'r3'}},
                                                {'node': {'firstName': 'r4'}}]}
                     }
    schema = Schema(query=Query)
    result = schema.execute(query)
    assert not result.errors
    assert result.data == expected_data

    reporter1.delete().execute()
    reporter2.delete().execute()
    reporter3.delete().execute()
    reporter4.delete().execute()
