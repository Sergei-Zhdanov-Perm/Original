import time

from django.http import HttpRequest
from django.shortcuts import render


def set_useragent_on_request_middleware(get_response):
    print("initial call")

    def middleware(request: HttpRequest):
        print("before get response")
        request.user_agent = request.META["HTTP_USER_AGENT"]
        response = get_response(request)
        print("after get response")
        return response

    return middleware


class CountRequestsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.requests_count = 0
        self.responses_count = 0
        self.exceptions_count = 0
        self.request_time = {}

    def __call__(self, request: HttpRequest):
        IP = request.META.get('REMOTE_ADDR')
        lis = request.session.get(IP, [])
        curr_time = time.time()
        if len(lis) < 3:
            lis.append(curr_time)
            request.session[IP] = lis
        else:
            if time.time() - lis[0] < 10:
                print('Throttling middleware! Less than 10 seconds have passed since the last request')
                return render(request, 'requestdataapp/error-request.html')
            else:
                lis[0], lis[1], lis[2] = lis[1], lis[2], time.time()
                request.session[IP] = lis

        self.requests_count += 1
        print("requests count", self.requests_count)

        response = self.get_response(request)
        self.responses_count += 1
        print("responses count", self.responses_count)

        return response

    def process_exception(self, request: HttpRequest, exception: Exception):
        self.exceptions_count += 1
        print("got", self.exceptions_count, "exceptions so far")
