from django.template.defaultfilters import date as date_filter
from django.utils import timezone

from evan.tools.pdf import PdfResponse, Pdf


class InvitationLetterPdfMaker:

    def __init__(self, *, registration, filename: str, as_attachment: bool = False):
        self._response = PdfResponse(filename=filename, as_attachment=as_attachment)
        self.registration = registration
        self.make_pdf()

    def make_pdf(self):
        reg = self.registration
        event = reg.event
        address = f"""
_{reg.user.profile.name}_\u0020\u0020
_{reg.letter.address}_
"""
        intro = f"""
On behalf of the {event.name} organizing committee, I would hereby like to invite

_Name: **{reg.user.profile.name}**_\u0020\u0020
_Passport number: **{reg.letter.passport_number}**_\u0020\u0020
_Nationality: **{reg.letter.nationality}**_\u0020\u0020

to attend the \u201C{event.full_name} ({event.name})\u201D
from {date_filter(event.start_date)} to {date_filter(event.end_date)}
in {event.city}, {event.country.name}.
"""
        signature = f"""
More information about this event can be found on:\u0020\u0020
<{event.website}>

We look forward to welcoming {reg.user.profile.name} in {event.city}.\u0020\u0020
Please do not hesitate to contact me for additional information.\u0020\u0020
Sincerely yours,
"""

        with Pdf() as pdf:
            pdf.add_text(date_filter(timezone.now()), 'p_right')
            pdf.add_text(address, 'p_small', 'markdown')
            pdf.add_spacer(1.5)
            pdf.add_text('To Whom It May Concern,')
            pdf.add_text(intro, 'p', 'markdown')

            if reg.letter.submitted:
                paper = f"""
{reg.user.profile.name} has submitted a {reg.letter.submitted} titled \u2018{reg.letter.submitted_title}\u2019
with the intention to present it during the event.
"""
                pdf.add_text(paper, 'p', 'markdown')

            pdf.add_text(signature, 'p', 'markdown')
            pdf.add_spacer(1.5)
            pdf.add_text(event.signature, 'p', 'markdown')
            pdf.add_page_break()

            self._response.write(pdf.get())

    @property
    def response(self) -> PdfResponse:
        return self._response
