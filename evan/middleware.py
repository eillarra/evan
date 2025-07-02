"""Middleware to handle cookie-free responses."""


class NoCookiesMiddleware:
    """Middleware that prevents cookies from being added to responses marked as cookie-free."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # If response is marked as no-cookies, clear any cookies that were added by other middleware
        if hasattr(response, "_no_cookies") and response._no_cookies:
            response.cookies.clear()

        return response
