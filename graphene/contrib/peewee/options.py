from ...core.classtypes.objecttype import ObjectTypeOptions
from ...relay.types import Node
from ...relay.utils import is_node

VALID_ATTRS = ('model', 'only_fields', 'exclude_fields',
               'filters',
               'order_by',
               'page', 'paginate_by')


class PeeweeOptions(ObjectTypeOptions):

    def __init__(self, *args, **kwargs):
        super(PeeweeOptions, self).__init__(*args, **kwargs)
        self.model = None
        self.valid_attrs += VALID_ATTRS
        self.only_fields = None
        self.exclude_fields = []
        self.filters = None
        self.order_by = None
        self.page = None
        self.paginate_by = None

    def contribute_to_class(self, cls, name):
        super(PeeweeOptions, self).contribute_to_class(cls, name)
        if is_node(cls):
            self.exclude_fields = list(self.exclude_fields) + ['id']
            self.interfaces.append(Node)
