import peewee

from ...core.classtypes.enum import Enum
from ...core.types.custom_scalars import DateTime
from ...core.types.scalars import ID, Boolean, Float, Int, String
from ...utils import to_const
from .utils import get_related_model, import_single_dispatch

singledispatch = import_single_dispatch()


def convert_choices(choices):
    for value, name in choices:
        if isinstance(name, (tuple, list)):
            for choice in convert_choices(name):
                yield choice
        else:
            yield to_const(str(name)), value


def convert_peewee_field_with_choices(field):
    choices = getattr(field, 'choices', None)
    if choices:
        meta = field.model_class._meta
        name = '{}_{}'.format(meta.name, field.name)
        graphql_choices = list(convert_choices(choices))
        return Enum(name.upper(), graphql_choices, description=field.help_text)
    return convert_peewee_field(field)


def add_nonnull_to_field(convert_field):
    return convert_field


@singledispatch
def convert_peewee_field(field):
    raise Exception(
        "Don't know how to convert the Peewee field %s (%s)" %
        (field, field.__class__))


@convert_peewee_field.register(peewee.CharField)
@convert_peewee_field.register(peewee.TextField)
@convert_peewee_field.register(peewee.FixedCharField)
@convert_peewee_field.register(peewee.BlobField)
@convert_peewee_field.register(peewee.TimeField)
@convert_peewee_field.register(peewee.UUIDField)
@add_nonnull_to_field
def convert_field_to_string(field):
    return String(description=field.help_text)


@convert_peewee_field.register(peewee.PrimaryKeyField)
@add_nonnull_to_field
def convert_field_to_id(field):
    return ID(description=field.help_text)


@convert_peewee_field.register(peewee.SmallIntegerField)
@convert_peewee_field.register(peewee.BigIntegerField)
@convert_peewee_field.register(peewee.IntegerField)
@convert_peewee_field.register(peewee.TimestampField)
@add_nonnull_to_field
def convert_field_to_int(field):
    return Int(description=field.help_text)


@convert_peewee_field.register(peewee.BooleanField)
def convert_field_to_nullboolean(field):
    return Boolean(description=field.help_text)


@convert_peewee_field.register(peewee.DecimalField)
@convert_peewee_field.register(peewee.FloatField)
@add_nonnull_to_field
def convert_field_to_float(field):
    return Float(description=field.help_text)


@convert_peewee_field.register(peewee.DateField)
@convert_peewee_field.register(peewee.DateTimeField)
@add_nonnull_to_field
def convert_date_to_string(field):
    return DateTime(description=field.help_text)


@convert_peewee_field.register(peewee.ReverseRelationDescriptor)
def convert_field_to_list_or_connection(field):
    from .fields import PeeweeModelField, ConnectionOrListField
    model_field = PeeweeModelField(get_related_model(field))
    return ConnectionOrListField(model_field)


@convert_peewee_field.register(peewee.ForeignKeyField)
@add_nonnull_to_field
def convert_field_to_peeweemodel(field):
    from .fields import PeeweeModelField
    return PeeweeModelField(get_related_model(field),
                            description=field.help_text)
