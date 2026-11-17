from typing import Any, Dict, List, Optional, Sequence, Union
from core.types.protos import extensions_pb2
from moosync_edk.generated_api import batch_http_request as batch_http_request_host

class HttpRequest:
    def __init__(
        self,
        url: str,
        method: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        body: Optional[Union[bytes, str]] = None,
        timeout_ms: Optional[int] = None,
    ):
        self.url = url
        self.method = method
        self.headers = headers or {}
        if isinstance(body, str):
            self.body = body.encode("utf-8")
        else:
            self.body = body
        self.timeout_ms = timeout_ms

    def to_proto(self) -> extensions_pb2.HttpRequest:
        return extensions_pb2.HttpRequest(
            url=self.url,
            method=self.method.upper(),
            headers=self.headers,
            body=self.body,
            timeout_ms=self.timeout_ms,
        )

class HttpResponse:
    def __init__(self, proto: extensions_pb2.HttpResponse):
        self.status_code: int = proto.status_code
        self.status_text: str = proto.status_text
        self.headers: dict = dict(proto.headers)
        self.body: bytes = proto.body

    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 300

    @property
    def text(self) -> str:
        return self.body.decode("utf-8", errors="replace")

    def json(self) -> Any:
        import json
        return json.loads(self.text)

class HttpResult:
    def __init__(self, proto: extensions_pb2.HttpResult):
        which = proto.WhichOneof("result")
        if which == "response":
            self.response: Optional[HttpResponse] = HttpResponse(proto.response)
            self.error: Optional[str] = None
        elif which == "error":
            self.response = None
            self.error = proto.error
        else:
            self.response = None
            self.error = "Empty HTTP result"

def http_batch_request(requests: Sequence[Union[HttpRequest, Dict[str, Any]]]) -> List[HttpResponse]:
    if not requests:
        return []
    proto_reqs = []
    for r in requests:
        if isinstance(r, HttpRequest):
            proto_reqs.append(r.to_proto())
        elif isinstance(r, dict):
            req_obj = HttpRequest(**r)
            proto_reqs.append(req_obj.to_proto())
        else:
            raise ValueError(f"Invalid request type: {type(r)}")

    batch = extensions_pb2.BatchHttpRequest(requests=proto_reqs)
    batch_resp = batch_http_request_host(batch)

    if batch_resp.HasField("error") and batch_resp.error:
        raise Exception(batch_resp.error)

    responses = []
    for idx, item in enumerate(batch_resp.responses):
        which = item.WhichOneof("result")
        if which == "response":
            responses.append(HttpResponse(item.response))
        elif which == "error":
            raise Exception(f"Request #{idx} failed: {item.error}")
        else:
            raise Exception(f"Request #{idx} returned empty HTTP result")
    return responses

def http_batch_get(
    urls: List[str],
    headers: Optional[Dict[str, str]] = None,
    timeout_ms: Optional[int] = None,
) -> List[HttpResponse]:
    reqs = [HttpRequest(url=u, method="GET", headers=headers, timeout_ms=timeout_ms) for u in urls]
    return http_batch_request(reqs)

def http_request(
    url: str,
    method: str = "GET",
    body: Optional[Union[bytes, str]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout_ms: Optional[int] = None,
) -> HttpResponse:
    req = HttpRequest(
        url=url,
        method=method,
        headers=headers,
        body=body,
        timeout_ms=timeout_ms,
    )
    resps = http_batch_request([req])
    if not resps:
        raise Exception("Host runner returned empty response")
    return resps[0]

def http_get(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    timeout_ms: Optional[int] = None,
) -> HttpResponse:
    return http_request(url=url, method="GET", headers=headers, timeout_ms=timeout_ms)
