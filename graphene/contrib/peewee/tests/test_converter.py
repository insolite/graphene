import peewee
import pytest
from py.test import raises

import graphene
from graphene.core.types.custom_scalars import DateTime
from graphene.core.types.definitions import OfType

from ..converter import convert_peewee_field, convert_peewee_field_with_choices
from ..fields import ConnectionOrListField, PeeweeModelField
from .models import Article, Reporter, Film, FilmDetails


def assert_conversion(peewee_field, graphene_field, *args, **kwargs):
    field = peewee_field(help_text='Custom Help Text', null=True, *args, **kwargs)
    graphene_type = convert_peewee_field(field)
    assert isinstance(graphene_type, graphene_field)
    field = graphene_type.as_field()
    assert field.description == 'Custom Help Text'
    # if not isinstance(graphene_type, OfType):
    #     nonnull_field = peewee_field(null=False, *args, **kwargs)
    #     if not nonnull_field.null:
    #         nonnull_graphene_type = convert_peewee_field(nonnull_field)
    #         assert isinstance(nonnull_graphene_type, graphene.NonNull)
    return field


def test_should_unknown_peewee_field_raise_exception():
    with raises(Exception) as excinfo:
        convert_peewee_field(None)
    assert 'Don\'t know how to convert the Peewee field' in str(excinfo.value)


def test_should_date_convert_string():
    assert_conversion(peewee.DateField, DateTime)


def test_should_date_time_convert_string():
    assert_conversion(peewee.DateTimeField, DateTime)


def test_should_char_convert_string():
    assert_conversion(peewee.CharField, graphene.String)


def test_should_text_convert_string():
    assert_conversion(peewee.TextField, graphene.String)


def test_should_fixed_char_convert_string():
    assert_conversion(peewee.FixedCharField, graphene.String)


def test_should_file_convert_string():
    assert_conversion(peewee.BlobField, graphene.String)


def test_should_time_convert_string():
    assert_conversion(peewee.TimeField, graphene.String)


def test_should_auto_convert_id():
    assert_conversion(peewee.PrimaryKeyField, graphene.ID, primary_key=True)


def test_should_small_integer_convert_int():
    assert_conversion(peewee.SmallIntegerField, graphene.Int)


def test_should_big_integer_convert_int():
    assert_conversion(peewee.BigIntegerField, graphene.Int)


def test_should_integer_convert_int():
    assert_conversion(peewee.IntegerField, graphene.Int)


def test_should_timestamp_convert_int():
    assert_conversion(peewee.TimestampField, graphene.Int)


def test_should_boolean_convert_boolean():
    assert_conversion(peewee.BooleanField, graphene.Boolean)


def test_field_with_choices_convert_enum():
    field = peewee.CharField(help_text='Language', choices=(
        ('es', 'Spanish'),
        ('en', 'English')
    ))

    class TranslatedModel(peewee.Model):
        language = field

        class Meta:
            pass

    graphene_type = convert_peewee_field_with_choices(field)
    assert issubclass(graphene_type, graphene.Enum)
    assert graphene_type._meta.type_name == 'TRANSLATEDMODEL_LANGUAGE'
    assert graphene_type._meta.description == 'Language'
    assert graphene_type.__enum__.__members__['SPANISH'].value == 'es'
    assert graphene_type.__enum__.__members__['ENGLISH'].value == 'en'


def test_field_with_grouped_choices():
    field = peewee.CharField(help_text='Language', choices=(
        ('Europe', (
            ('es', 'Spanish'),
            ('en', 'English'),
        )),
    ))

    class GroupedChoicesModel(peewee.Model):
        language = field

        class Meta:
            pass

    convert_peewee_field_with_choices(field)


def test_field_with_choices_gettext():
    field = peewee.CharField(help_text='Language', choices=(
        ('es', 'Spanish'),
        ('en', 'English')
    ))

    class TranslatedChoicesModel(peewee.Model):
        language = field

        class Meta:
            pass

    convert_peewee_field_with_choices(field)


def test_should_decimal_convert_float():
    assert_conversion(peewee.DecimalField, graphene.Float)


def test_should_float_convert_float():
    assert_conversion(peewee.FloatField, graphene.Float)


def test_should_manytoone_convert_connectionorlist():
    related = Reporter.articles
    graphene_type = convert_peewee_field(related)
    assert isinstance(graphene_type, ConnectionOrListField)
    assert isinstance(graphene_type.type, PeeweeModelField)
    assert graphene_type.type.model == Article


def test_should_foreignkey_convert_model():
    field = assert_conversion(peewee.ForeignKeyField, PeeweeModelField, Article)
    assert field.type.model == Article
