from rest_framework.compat import coreapi, coreschema


conference_code_field = coreapi.Field(
    name='code',
    required=True,
    location='path',
    schema=coreschema.String(
        title='Conference code',
        description='A unique code string identifying a conference.'
    )
)
