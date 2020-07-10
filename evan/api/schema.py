from rest_framework.compat import coreapi, coreschema


event_code_field = coreapi.Field(
    name="code",
    required=True,
    location="path",
    schema=coreschema.String(title="Event code", description="A unique code string identifying an event."),
)
