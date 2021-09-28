from rest_framework.permissions import IsAuthenticated


class AbstractPermission(IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        """
        Users can only RETRIEVE or UPDATE their abstract.
        DELETE is not allowed at API level.
        """
        if request.method == "DELETE":
            return obj.event.can_be_managed_by(request.user)
        return obj.user_id == request.user.id or obj.event.can_be_managed_by(request.user)


class AbstractReviewPermission(IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        """
        Reviewers can RETRIEVE or UPDATE the review.
        Only event managers can DELETE a review (== unassign reviewer).
        """
        if request.method == "DELETE":
            return obj.abstract.event.can_be_managed_by(request.user)
        return obj.user_id == request.user.id
