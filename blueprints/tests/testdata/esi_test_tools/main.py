"""
Tools for building unit tests with django-esi
"""

from collections import namedtuple
from typing import Any, List

from bravado.exception import HTTPInternalServerError, HTTPNotFound
from django.utils.dateparse import parse_datetime


class BravadoResponseStub:
    """Stub for IncomingResponse in bravado, e.g. for HTTPError exceptions"""

    def __init__(
        self, status_code, reason="", text="", headers=None, raw_bytes=None
    ) -> None:
        self.reason = reason
        self.status_code = status_code
        self.text = text
        self.headers = headers if headers else dict()
        self.raw_bytes = raw_bytes

    def __str__(self):
        return "{0} {1}".format(self.status_code, self.reason)


class BravadoOperationStub:
    """Stub to simulate the operation object return from bravado via django-esi"""

    class RequestConfig:
        def __init__(self, also_return_response):
            self.also_return_response = also_return_response

    class ResponseStub:
        def __init__(self, headers):
            self.headers = headers

    def __init__(self, data, headers: dict = None, also_return_response: bool = False):
        self._data = data
        self._headers = headers if headers else {"x-pages": 1}
        self.request_config = BravadoOperationStub.RequestConfig(also_return_response)

    def result(self, **kwargs):
        if self.request_config.also_return_response:
            return [self._data, self.ResponseStub(self._headers)]
        else:
            return self._data

    def results(self, **kwargs):
        return self.result(**kwargs)


EsiEndpoint_T = namedtuple(
    "EsiEndpoint", ["category", "method", "primary_key", "needs_token"]
)


def EsiEndpoint(
    category: str, method: str, primary_key: str = None, needs_token: bool = False
) -> EsiEndpoint_T:
    return EsiEndpoint_T(category, method, primary_key, needs_token)


class _EsiRoute:
    def __init__(
        self, endpoint: EsiEndpoint_T, testdata: dict, http_error: bool = False
    ) -> None:
        self._category = endpoint.category
        self._method = endpoint.method
        self._primary_key = endpoint.primary_key
        self._needs_token = endpoint.needs_token
        self._testdata = testdata
        self._http_error = http_error

    def call(self, **kwargs):
        if self._http_error:
            raise HTTPInternalServerError(
                response=BravadoResponseStub(500, "Test exception")
            )

        pk_value = None
        if self._primary_key:
            if isinstance(self._primary_key, tuple):
                for pk in self._primary_key:
                    if pk not in kwargs:
                        raise ValueError(
                            f"{self._category}.{self._method}: Missing primary key: {pk}"
                        )

            elif self._primary_key not in kwargs:
                raise ValueError(
                    f"{self._category}.{self._method}: Missing primary key: "
                    f"{self._primary_key}"
                )
        if self._needs_token:
            if "token" not in kwargs:
                raise ValueError(
                    f"{self._category}.{self._method} "
                    f"with pk = {self._primary_key}: Missing token"
                )
            elif not isinstance(kwargs.get("token"), str):
                raise TypeError(
                    f"{self._category}.{self._method} "
                    f"with pk = {self._primary_key}: Token is not a string"
                )
        try:
            if self._primary_key:

                if isinstance(self._primary_key, tuple):
                    pk_value_1 = str(kwargs[self._primary_key[0]])
                    pk_value_2 = str(kwargs[self._primary_key[1]])
                    result = self._convert_values(
                        self._testdata[self._category][self._method][pk_value_1][
                            pk_value_2
                        ]
                    )
                else:
                    pk_value = str(kwargs[self._primary_key])
                    result = self._convert_values(
                        self._testdata[self._category][self._method][pk_value]
                    )
            else:
                result = self._convert_values(
                    self._testdata[self._category][self._method]
                )

        except KeyError:
            raise HTTPNotFound(
                response=BravadoResponseStub(
                    404,
                    f"{self._category}.{self._method}: No test data for "
                    f"{self._primary_key} = {pk_value}",
                ),
            ) from None

        return BravadoOperationStub(result)

    @staticmethod
    def _convert_values(data) -> Any:
        if isinstance(data, dict):
            for k, v in data.items():
                if isinstance(v, str):
                    try:
                        dt = parse_datetime(v)
                        if dt:
                            data[k] = dt
                    except ValueError:
                        pass

        return data


class EsiClientStub:
    def __init__(
        self, testdata: dict, endpoints: List[EsiEndpoint_T], http_error: bool = False
    ) -> None:
        self._testdata = testdata
        self._http_error = http_error
        for endpoint in endpoints:
            self._validate_endpoint(endpoint)
            self._add_endpoint(endpoint)

    def _validate_endpoint(self, endpoint: EsiEndpoint_T):
        try:
            _ = self._testdata[endpoint.category][endpoint.method]
        except KeyError:
            raise ValueError(f"No data provided for {endpoint}")

    def _add_endpoint(self, endpoint: EsiEndpoint):
        if not hasattr(self, endpoint.category):
            setattr(self, endpoint.category, type(endpoint.category, (object,), dict()))
        my_category = getattr(self, endpoint.category)
        if not hasattr(my_category, endpoint.method):
            setattr(
                my_category,
                endpoint.method,
                _EsiRoute(
                    endpoint=endpoint,
                    testdata=self._testdata,
                    http_error=self._http_error,
                ).call,
            )
        else:
            raise ValueError(f"Endpoint for {endpoint} already defined!")
