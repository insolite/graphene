from unittest import TestCase

import peewee

import graphene
from graphene import relay, ObjectType, resolve_only_args
from graphene.contrib.peewee.fields import PeeweeConnectionField
from graphene.contrib.peewee.types import PeeweeNode


database = peewee.PostgresqlDatabase('graphene_test', user='postgres', host='127.0.0.1')


class Material(peewee.Model):

    name = peewee.CharField()

    class Meta:
        database = database


class Weapon(peewee.Model):

    name = peewee.CharField()
    damage = peewee.IntegerField()
    material = peewee.ForeignKeyField(Material, related_name='weapons')

    class Meta:
        database = database


class Monster(peewee.Model):

    name = peewee.CharField()
    size = peewee.IntegerField()
    weapon = peewee.ForeignKeyField(Weapon, related_name='monsters')

    class Meta:
        database = database


class MaterialNode(PeeweeNode):

    class Meta:
        model = Material


class WeaponNode(PeeweeNode):
    class Meta:
        model = Weapon


class MonsterNode(PeeweeNode):

    class Meta:
        model = Monster


class Query(ObjectType):
    monster = relay.NodeField(MonsterNode)
    monsters = PeeweeConnectionField(MonsterNode)

    weapon = relay.NodeField(WeaponNode)
    weapons = PeeweeConnectionField(WeaponNode)

    material = relay.NodeField(MaterialNode)
    materials = PeeweeConnectionField(MaterialNode)


schema = graphene.Schema(query=Query, auto_camelcase=False)


class TypesTest(TestCase):

    def test_monster(self):
        import logging
        logger = logging.getLogger('peewee')
        logger.setLevel(logging.DEBUG)
        logger.addHandler(logging.StreamHandler())

        from base64 import b64encode
        # result = schema.execute("""
        #     query {
        #         monster(id: "TW9uc3Rlck5vZGU6MQ==") {
        #             id
        #             name
        #         }
        #     }
        # """)
        # result = schema.execute("""
        #     query {
        #         monster(id: "TW9uc3Rlck5vZGU6MQ==") {
        #             name,
        #             weapon {
        #                 name
        #             }
        #         }
        #     }
        # """)
        # result = schema.execute("""
        #     query {
        #         monsters(name: "james") {
        #             edges {
        #                 node {
        #                     name,
        #                     weapon {
        #                         name,
        #                         material {
        #                             name
        #                         }
        #                     }
        #                 }
        #             }
        #         }
        #     }
        # """)
        # result = schema.execute("""
        #     query {
        #         weapons {
        #             edges {
        #                 node {
        #                     name,
        #                     monster_set {
        #                         edges {
        #                             node {
        #                                 name
        #                             }
        #                         }
        #                     }
        #                 }
        #             }
        #         }
        #     }
        # """)
        # result = schema.execute("""
        #     query {
        #         weapons {
        #             edges {
        #                 node {
        #                     name,
        #                     monsters {
        #                         edges {
        #                             node {
        #                                 name
        #                             }
        #                         }
        #                     }
        #                 }
        #             }
        #         }
        #     }
        # """)
        result = schema.execute("""
            query {
                weapons (damage__gt: 0, material_id: 1) {
                    edges {
                        node {
                            name,
                            monsters {
                                edges {
                                    node {
                                        name
                                    }
                                }
                            }
                        }
                    }
                }
            }
        """)
        # result = schema.execute("""
        #     query {
        #         weapon (id: "V2VhcG9uTm9kZTox") {
        #             name,
        #             monsters {
        #                 edges {
        #                     node {
        #                         name
        #                     }
        #                 }
        #             }
        #         }
        #     }
        # """)
        # result = schema.execute("""
        #     query {
        #         weapons(name: "stick") {
        #             edges {
        #                 node {
        #                     name
        #                 }
        #             }
        #         }
        #     }
        # """)
        # result = schema.execute("""
        #     query {
        #         monster(id: "TW9uc3Rlck5vZGU6MQ==") {
        #             name,
        #             weapon {
        #                 name
        #             }
        #         }
        #     }
        # """)
        import json
        print(result.data, result.errors)
        a = json.loads(json.dumps(result.data))
        print(a)
