from graphql.type import GraphQLObjectType
from mock import patch

from graphene import Schema, Interface
from graphene.core.fields import Field
from graphene.core.types.scalars import Int
from graphene.relay.fields import GlobalIDField
from tests.utils import assert_equal_lists
from ..types import PeeweeNode, PeeweeObjectType

from .models import Article, Reporter

schema = Schema()


@schema.register
class Character(PeeweeObjectType):
    '''Character description'''
    class Meta:
        model = Reporter


@schema.register
class Human(PeeweeNode):
    '''Human description'''

    pub_date = Int()

    class Meta:
        model = Article


def test_peewee_interface():
    assert PeeweeNode._meta.interface is True


@patch('graphene.contrib.peewee.tests.models.Article.get',
       return_value=Article(id=1))
def test_peewee_get_node(get):
    human = Human.get_node(1, None)
    get.assert_called_with(id=1)
    assert human.id == 1


@patch('graphene.contrib.peewee.tests.models.Article.get',
       side_effect=Article.DoesNotExist)
def test_peewee_get_node_not_exist(get):
    human = Human.get_node(1, None)
    get.assert_called_with(id=1)
    assert human is None


def test_peeweenode_idfield():
    idfield = PeeweeNode._meta.fields_map['id']
    assert isinstance(idfield, GlobalIDField)


def test_node_idfield():
    idfield = Human._meta.fields_map['id']
    assert isinstance(idfield, GlobalIDField)


def test_node_replacedfield():
    idfield = Human._meta.fields_map['pub_date']
    assert isinstance(idfield, Field)
    assert schema.T(idfield).type == schema.T(Int())


def test_objecttype_init_none():
    h = Human()
    assert h._root is None


def test_objecttype_init_good():
    instance = Article(id=1)
    h = Human(instance)
    assert h._root == instance


def test_object_type():
    object_type = schema.T(Human)
    Human._meta.fields_map
    assert Human._meta.interface is False
    assert isinstance(object_type, GraphQLObjectType)
    assert_equal_lists(
        object_type.get_fields().keys(),
        ['headline', 'id', 'reporter', 'pubDate']
    )
    assert schema.T(PeeweeNode) in object_type.get_interfaces()


def test_node_notinterface():
    assert Human._meta.interface is False
    assert PeeweeNode in Human._meta.interfaces


def test_peewee_objecttype_could_extend_interface():
    schema = Schema()

    @schema.register
    class Customer(Interface):
        id = Int()

    @schema.register
    class UserType(PeeweeObjectType):
        class Meta:
            model = Reporter
            interfaces = [Customer]

    object_type = schema.T(UserType)
    assert schema.T(Customer) in object_type.get_interfaces()
