from django.shortcuts import render
from django.views import View

# Create your views here.


import json
from django.http import JsonResponse
from django.views import View


class API(View):

    def get(self, request, *args, **kwargs):
        """
        Dummy GET endpoint.
        Echoes query parameters.
        """
        data = {
            "message": "GET API called",
            "method": "GET",
            "path": request.path,
            "query_params": dict(request.GET),
        }

        return JsonResponse(data, status=200)

    def post(self, request, *args, **kwargs):
        """
        Dummy POST endpoint.
        Echoes JSON body or form data.
        """

        parsed_body = None
        error = None

        # Attempt JSON parsing
        if request.content_type == "application/json":
            try:
                parsed_body = json.loads(request.body.decode("utf-8"))
            except Exception:
                error = "Invalid JSON body"
        else:
            parsed_body = dict(request.POST)

        if error:
            return JsonResponse(
                {
                    "message": "POST API error",
                    "error": error,
                },
                status=400,
            )

        return JsonResponse(
            {
                "message": "POST API called",
                "method": "POST",
                "path": request.path,
                "body": parsed_body,
            },
            status=201,
        )