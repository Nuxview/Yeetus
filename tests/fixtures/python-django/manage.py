#!/usr/bin/env python

import os
import sys

from django.conf import settings
from django.core.management import execute_from_command_line
from django.http import JsonResponse
from django.urls import path

settings.configure(
    SECRET_KEY=os.environ.get("SECRET_KEY", "fixture-only"),
    DEBUG=False,
    ALLOWED_HOSTS=["*"],
    ROOT_URLCONF=__name__,
)
urlpatterns = [path("", lambda request: JsonResponse({"message": "Hello Django"}))]


def main():
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
