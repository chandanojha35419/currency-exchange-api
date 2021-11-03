from rest_framework import serializers
from rest_framework.utils import field_mapping

__author__ = 'chandanojha'


class ModelSerializer(serializers.ModelSerializer):
    """
    A ModelSerializer that takes an additional `fields` argument that
    controls which fields should be displayed, and takes in a "depth"
    argument to control the nesting depth of PK fields

    It also provides option for specifying serializer class for nested fields (via 'nested_field_serializers' mapping)
    and for restricting expansion of selected fields even on depth > 0 (via 'ignore_depth_fields' list)

    ** Note that you can define the following three 'max_depth', 'nested_field_serializers' and 'ignore_depth_fields' in
    Meta class as well but do take care of over-writing in case of subclassing

    """

    # maximum allowed depth for this serializer, relatively safe default of 1 (0?) :-) override if you need more
    # Note that drf has its own hard max set at 10 which can't be bypassed
    max_depth = 0

    # List of fields that are NOT allowed to expand even on depth > 0
    # ignore_depth_fields = ('user',)

    # field_name vs. custom SerializerClass mapping
    # nested_field_serializers = {
    #  # 'field_name': SerializerClass
    # }

    @classmethod
    def _get_meta_or_class_property(cls, name, default=None):
        """
        :param name: property name
        :return: Returns the Meta class property if defined, otherwise try on self class
        """
        value = getattr(cls.Meta, name, None)
        if value is None:
            value = getattr(cls, name, default)
        return value

    @classmethod
    def get_nested_field_serializer_class(cls, field_name, default_field_class=None):
        d = cls._get_meta_or_class_property('nested_field_serializers')
        return d.get(field_name, default_field_class) if d else default_field_class

    def __init__(self, *args, **kwargs):
        self.requested_fields = kwargs.pop('fields', None)
        self.requested_depth = kwargs.pop('depth', None)
        super().__init__(*args, **kwargs)

        # Enforce max_depth, in case of Meta.depth (set in code) complain immediately..
        max_depth = self._get_meta_or_class_property('max_depth')
        depth = getattr(self.Meta, 'depth', 0)
        assert max_depth is None or depth <= max_depth, "depth={0} is more than max_depth={1}".format(depth, max_depth)

        # ..but for requested_depth (set by client) silently cap it to max
        if self.requested_depth and self.requested_depth > max_depth:
            self.requested_depth = max_depth

    @property
    def applied_depth(self):
        if self.requested_depth:
            return self.requested_depth
        return getattr(self.Meta, 'depth', 0)

    def build_nested_field(self, field_name, relation_info, nested_depth):
        """
        Create nested fields for forward and reverse relationships

        We override to specify our own Serializer classes for nested field if given (via 'nested_field_serializers'
         mapping or nested_field_serializers() method override)

        Also checks if the requested nested field is marked as 'never-expand' fields in which case we simply
          route to non-depth path 'build_relational_field' (see super's method)
        """

        # See if the field is allowed to expand at all, either because we hit the max-depth or because
        # this field itself is not allowed to - break right away it not
        max_depth = self._get_meta_or_class_property('max_depth', default=1)
        assert nested_depth <= max_depth, "depth={0} is more than max_depth={1}".format(nested_depth, max_depth)

        if field_name in self._get_meta_or_class_property('ignore_depth_fields', default=[]):
            return self.build_relational_field(field_name, relation_info)

        # Need to expand, see if there is a Serializer set explicitly for this field..
        field_class = self.get_nested_field_serializer_class(field_name)
        if field_class:
            # We create a subclass on the fly as we don't want original's Meta.depth to be messed-up
            class NestedSerializer(field_class):
                class Meta(field_class.Meta):
                    depth = nested_depth - 1

            return NestedSerializer, field_mapping.get_nested_relation_kwargs(relation_info)

        # Nothing special to do, just pass on to super
        return super().build_nested_field(field_name, relation_info, nested_depth)

    def get_field_names(self, declared_fields, info):
        """
        Returns Field list to be used for this serializer

        We override to only include the fields requested by client (via query params)
        """
        field_names = super().get_field_names(declared_fields, info)
        if self.requested_fields:
            return [f for f in self.requested_fields if f in field_names]

        return field_names

    def get_fields(self):
        """
        We override to apply 'depth' requested by client just before the call to super (and reset it back before returning)
        :return:
        """
        if self.requested_depth is not None:
            default_depth = getattr(self.Meta, 'depth', None)
            if default_depth != self.requested_depth:
                self.Meta.depth = self.requested_depth
                fields = super().get_fields()
                if default_depth is not None:
                    self.Meta.depth = default_depth
                else:
                    delattr(self.Meta, 'depth')
                return fields
        return super().get_fields()
