from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.utils.decorators import method_decorator
from django.views.generic import View
from io import BytesIO
from PyPDF2 import PdfMerger

from evan.models import Abstract
from evan.services.pdf import PdfResponse


class IcoodimPdfBundleView(View):
    """
    Serves a bundle of abstracts for a session.
    """

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        session_code = kwargs.get("session")
        response = PdfResponse(filename=f"{session_code}.pdf", as_attachment=True)
        merger = PdfMerger()
        abstracts = Abstract.objects.filter(event__code="icoopma-eurodim", is_accepted=True)
        bundle = []

        # Check permission

        if not abstracts.first().files_viewable_by_user(self.request.user):
            raise PermissionDenied("You need to be registered for the event to see these abstracts.")

        # Make PDF

        for abstract in abstracts:
            try:
                if str(abstract.custom_data["session"]) == session_code:
                    bundle.append((abstract.custom_data["talk"], abstract))
            except KeyError:
                pass

        bundle.sort(key=lambda x: x[0])

        for (_, abstract) in bundle:
            if abstract.file:
                merger.append(abstract.file.file.path)

        with BytesIO() as bytes_stream:
            merger.write(bytes_stream)
            merger.close()
            response.write(bytes_stream.getvalue())

        return response
