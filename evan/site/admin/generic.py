from django.contrib.admin import FieldListFilter


def custom_titled_filter(title):
    # https://stackoverflow.com/questions/17392087/how-to-modify-django-admin-filters-title

    class Wrapper(FieldListFilter):
        def __new__(cls, *args, **kwargs):
            instance = FieldListFilter.create(*args, **kwargs)
            instance.title = title
            return instance

    return Wrapper
