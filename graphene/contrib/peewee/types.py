import asyncio
import inspect

import peewee
import six

from ...core.classtypes.objecttype import ObjectType, ObjectTypeMeta
from ...relay.types import Node, NodeMeta
from ...relay.types import Connection
from .converter import convert_peewee_field_with_choices
from .options import PeeweeOptions
from .utils import get_reverse_fields


class PeeweeObjectTypeMeta(ObjectTypeMeta):
    options_class = PeeweeOptions

    def construct_fields(cls):
        only_fields = cls._meta.only_fields
        reverse_fields = get_reverse_fields(cls._meta.model)
        all_fields = {field.name: field
                      for field in cls._meta.model._meta.declared_fields}
        all_fields.update(reverse_fields)
        already_created_fields = {f.attname for f in cls._meta.local_fields}

        for name, field in all_fields.items():
            is_not_in_only = only_fields and name not in only_fields
            is_already_created = name in already_created_fields
            is_excluded = ((name in cls._meta.exclude_fields)
                           or is_already_created)
            if is_not_in_only or is_excluded:
                # We skip this field if we specify only_fields and is not
                # in there. Or when we exclude this field in exclude_fields
                continue
            converted_field = convert_peewee_field_with_choices(field)
            cls.add_to_class(name, converted_field)

    def construct(cls, *args, **kwargs):
        cls = super(PeeweeObjectTypeMeta, cls).construct(*args, **kwargs)
        if not cls._meta.abstract:
            if not cls._meta.model:
                raise Exception(
                    'Peewee ObjectType %s '
                    'must have a model in the Meta class attr' % cls)
            elif (not inspect.isclass(cls._meta.model)
                  or not issubclass(cls._meta.model, peewee.Model)):
                raise Exception('Provided model in %s '
                                'is not a Peewee model' % cls)

            cls.construct_fields()
        return cls


class InstanceObjectType(ObjectType):

    class Meta:
        abstract = True

    def __init__(self, _root=None):
        super(InstanceObjectType, self).__init__(_root=_root)
        assert not self._root or isinstance(self._root, self._meta.model), (
            '{} received a non-compatible instance ({}) '
            'when expecting {}'.format(
                self.__class__.__name__,
                self._root.__class__.__name__,
                self._meta.model.__name__
            ))

    @property
    def instance(self):
        return self._root

    @instance.setter
    def instance(self, value):
        self._root = value


class PeeweeObjectType(six.with_metaclass(
        PeeweeObjectTypeMeta, InstanceObjectType)):

    class Meta:
        abstract = True


class PeeweeConnection(Connection):
    pass


class PeeweeNodeMeta(PeeweeObjectTypeMeta, NodeMeta):
    pass


class NodeInstance(Node, InstanceObjectType):

    class Meta:
        abstract = True


class PeeweeNode(six.with_metaclass(
        PeeweeNodeMeta, NodeInstance)):

    class Meta:
        abstract = True

    @classmethod
    @asyncio.coroutine
    def async_get_node(cls, id, info=None):
        model = cls._meta.model
        try:
            return (yield from model._meta.manager.get(model, id=id))
        except model.DoesNotExist:
            return None

    @classmethod
    def get_node(cls, id, info=None):
        return asyncio.async(cls.async_get_node(id, info))
