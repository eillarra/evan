from allauth_cas.views import CASAdapter, CASCallbackView, CASLoginView

from .provider import UGentCASProvider


class UGentCASAdapter(CASAdapter):
    provider_id = UGentCASProvider.id
    url = "https://login.ugent.be/"
    version = 3


login = CASLoginView.adapter_view(UGentCASAdapter)
callback = CASCallbackView.adapter_view(UGentCASAdapter)
