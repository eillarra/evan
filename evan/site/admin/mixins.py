


class HideDeleteActionMixin:
    def get_actions(self, request):
        actions = super().get_actions(request)
        if request.user.is_superuser and "delete_selected" in actions:
            del actions["delete_selected"]
        return actions
