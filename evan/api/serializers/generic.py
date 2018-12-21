import json

from django.utils.encoding import force_text
from django_countries.serializer_fields import CountryField as BaseCountryField
from rest_framework import serializers
from rest_framework.relations import RelatedField

from evan.models import Metadata, get_cached_metadata, get_cached_metadata_queryset


class CountryField(BaseCountryField):
    def to_representation(self, obj):
        code = obj.code
        if not code:
            return ''
        if not self.country_dict:
            return code
        return {
            'code': code,
            'name': force_text(obj.name),
            'flag_css': force_text(obj.flag_css)
        }


class JsonField(BaseCountryField):
    def to_internal_value(self, data):
        return json.dumps(data)

    def to_representation(self, obj):
        return json.loads(obj)


class MetadataListField(serializers.CharField):
    metadata = None

    def get_metadata(self):
        if not self.metadata:
            self.metadata = get_cached_metadata()
        return self.metadata

    def to_internal_value(self, data):
        return ','.join([str(metadata['id']) for metadata in data])

    def to_representation(self, obj):
        self.get_metadata()
        return [] if obj == '' else [{
            'id': self.metadata[int(pk)].id,
            'value': self.metadata[int(pk)].value
        } for pk in obj.split(',') if int(pk) in self.metadata]


class MetadataField(RelatedField):
    queryset = get_cached_metadata_queryset()
    pk_field = 'pk'

    def __init__(self, **kwargs):
        self.pk_field = kwargs.pop('pk_field', self.pk_field)
        RelatedField.__init__(self, **kwargs)

    def to_internal_value(self, data):
        return self.get_queryset().get(id=data['id'])

    def to_representation(self, obj):
        metadata = get_cached_metadata()[getattr(obj, self.pk_field)]
        return {
            'id': metadata.id,
            'value': metadata.value
        }


class MetadataFieldWithPosition(MetadataField):

    def to_representation(self, obj):
        metadata = get_cached_metadata()[getattr(obj, self.pk_field)]
        return {
            'id': metadata.id,
            'value': metadata.value,
            'position': metadata.position
        }


class MetadataNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Metadata
        exclude = ()


class MetadataListSerializer(MetadataNestedSerializer):
    pass
