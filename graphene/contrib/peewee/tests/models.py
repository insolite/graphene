from __future__ import absolute_import

import peewee

CHOICES = (
    (1, 'this'),
    (2, 'that')
)


test_db = peewee.SqliteDatabase(':memory:')
test_db.connect()


class BaseModel(peewee.Model):

    class Meta:
        database = test_db


class Organization(BaseModel):
    name = peewee.CharField(max_length=30)


class Reporter(BaseModel):
    first_name = peewee.CharField(max_length=30)
    last_name = peewee.CharField(max_length=30)
    email = peewee.CharField(max_length=30)
    a_choice = peewee.CharField(max_length=30, choices=CHOICES, null=True)
    organization = peewee.ForeignKeyField(Organization, related_name='organizations', null=True)

    def __str__(self):              # __unicode__ on Python 2
        return "%s %s" % (self.first_name, self.last_name)


class Pet(BaseModel):
    name = peewee.CharField(max_length=30)
    reporter = peewee.ForeignKeyField(Reporter, related_name='pets')


class Film(BaseModel):
    reporters = peewee.ForeignKeyField(Reporter,
                                       related_name='films')


class FilmDetails(BaseModel):
    location = peewee.CharField(max_length=30)
    film = peewee.ForeignKeyField(Film, related_name='details')


class Article(BaseModel):
    headline = peewee.CharField(max_length=100, null=True)
    pub_date = peewee.DateField()
    reporter = peewee.ForeignKeyField(Reporter, related_name='articles')
    lang = peewee.CharField(max_length=2, help_text='Language', choices=[
        ('es', 'Spanish'),
        ('en', 'English')
    ], default='es')
    importance = peewee.IntegerField(verbose_name='Importance', null=True,
                                     choices=[(1, u'Very important'), (2, u'Not as important')])

    def __str__(self):              # __unicode__ on Python 2
        return self.headline

    class Meta:
        ordering = ('headline',)

test_db.create_tables([Organization,
                       Reporter,
                       Pet,
                       Film,
                       FilmDetails,
                       Article])
