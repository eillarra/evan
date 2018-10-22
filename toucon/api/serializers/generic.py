import json

from django.utils.encoding import force_text
from django_countries.serializer_fields import CountryField as BaseCountryField


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
