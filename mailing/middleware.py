class PublicCacheMiddleware:
    # Список префиксов URL, которые считаем общедоступными
    PUBLIC_URLS = [
        "/about/",
        "/help/",
        "/contact/",
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Применяем только к GET/HEAD и только если статус 200
        if request.method in ("GET", "HEAD") and response.status_code == 200:
            path = request.path
            for prefix in self.PUBLIC_URLS:
                if path.startswith(prefix):
                    # Не перезаписываем, если view уже сам установил Cache-Control
                    if "Cache-Control" not in response:
                        response["Cache-Control"] = "public, max-age=3600"
                    break

        return response