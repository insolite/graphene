import asyncio
import peewee
# from peewee import fn, SQL, Clause

from ...core.exceptions import SkipField
from ...core.fields import Field
from ...core.types.base import FieldType
from ...core.types.definitions import List
from ...relay import ConnectionField
from ...relay.utils import is_node
from ...core.types import Argument, String, Int
from ...utils import to_snake_case
from .utils import (
    get_type_for_model, maybe_query, get_fields, get_filtering_args,
    get_requested_models
)


ORDER_BY_FIELD = 'order_by'
PAGE_FIELD = 'page'
PAGINATE_BY_FIELD = 'paginate_by'
# TOTAL_FIELD = '__total__'


class PeeweeConnectionField(ConnectionField):

    def __init__(self, type,
                 filters=None,
                 order_by=None,
                 page=None, paginate_by=None,
                 *args, **kwargs):
        self.filters = get_filtering_args(type._meta.model, filters
                                          or type._meta.filters)
        self.order_by = order_by or type._meta.order_by
        self.page = page or type._meta.page
        self.paginate_by = paginate_by or type._meta.paginate_by
        self.args = {}
        self.args.update(self.filters)
        self.args.update({ORDER_BY_FIELD: Argument(List(String())),
                          PAGE_FIELD: Argument(Int()),
                          PAGINATE_BY_FIELD: Argument(Int())})
        kwargs.setdefault('args', {})
        kwargs['args'].update(**self.args)

        self.on = kwargs.pop('on', False)
        kwargs['default'] = kwargs.pop('default', self.get_default)
        super(PeeweeConnectionField, self).__init__(type, *args, **kwargs)

    @property
    def model(self):
        return self.type._meta.model

    def get_default(self):
        if self.on:
            return getattr(self.model, self.on)
        else:
            return self.model

    def get_field(self, name):
        return getattr(self.model, name)

    def filter(self, query, args):
        if args:
            query = query.filter(**args)
        return query

    def order(self, query, order):
        if order:
            query = query.order_by(
                *[self.get_field(to_snake_case(order_item))
                  for order_item in order])
        return query

    def paginate(self, query, page, paginate_by):
        if page and paginate_by:
            query = query.paginate(page, paginate_by)
            # total = Clause(fn.Count(SQL('*')),
            #                fn.Over(), glue=' ').alias(TOTAL_FIELD)
            # query._select = tuple(query._select) + (total,)
            # total = getattr(result[0], TOTAL_FIELD, None) if result else 0
        return query

    def get_query(self, query, args, info):
        if isinstance(query, (peewee.Model, peewee.BaseModel)):
            args = dict(args)
            order = args.pop(ORDER_BY_FIELD, self.order_by)
            page = args.pop(PAGE_FIELD, self.page)
            paginate_by = args.pop(PAGINATE_BY_FIELD, self.paginate_by)
            requested_models = get_requested_models(get_fields(info),
                                                    self.model)
            query = query.select(self.model, *requested_models)
            for related_model in requested_models:
                query = query.join(related_model,
                                   peewee.JOIN_LEFT_OUTER) # TODO: on
            query = self.filter(query, args)
            query = self.order(query, order)
            query = self.paginate(query, page, paginate_by)
            query = query.aggregate_rows()
        query = maybe_query(query)
        return query

    @asyncio.coroutine
    def async_from_list(self, connection_type, resolved, args, context, info):
        query = self.get_query(resolved, args, info)
        result = yield from self.model._meta.manager.execute(query)
        return super(PeeweeConnectionField, self).from_list(
            connection_type, result, args, context, info
        )

    def from_list(self, connection_type, resolved, args, context, info):
        return asyncio.async(self.async_from_list(connection_type, resolved, args, context, info))


class ConnectionOrListField(Field):

    def internal_type(self, schema):
        model_field = self.type
        field_object_type = model_field.get_object_type(schema)
        if not field_object_type:
            raise SkipField()
        if is_node(field_object_type):
            field = PeeweeConnectionField(field_object_type)
        else:
            field = Field(List(field_object_type))
        field.contribute_to_class(self.object_type, self.attname)
        return schema.T(field)


class PeeweeModelField(FieldType):

    def __init__(self, model, *args, **kwargs):
        self.model = model
        super(PeeweeModelField, self).__init__(*args, **kwargs)

    def internal_type(self, schema):
        _type = self.get_object_type(schema)
        if not _type and self.parent and self.parent._meta.only_fields:
            raise Exception(
                "Model %r is not accessible by the schema. "
                "You can either register the type manually "
                "using @schema.register. "
                "Or disable the field in %s" % (
                    self.model,
                    self.parent,
                )
            )
        if not _type:
            raise SkipField()
        return schema.T(_type)

    def get_object_type(self, schema):
        return get_type_for_model(schema, self.model)
