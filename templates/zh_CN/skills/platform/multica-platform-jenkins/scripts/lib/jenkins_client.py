"""Jenkins REST client (stdlib only — Windows / Linux)."""
from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any
from urllib.parse import urljoin, urlparse


class JenkinsError(RuntimeError):
    pass


class JenkinsClient:
    def __init__(
        self,
        base_url: str,
        user: str,
        password: str,
        curl_resolve: str = "",
        timeout: int = 1800,
        poll_interval: int = 5,
    ) -> None:
        if not user or not password:
            raise JenkinsError(
                "Missing credentials. Set ATLASSIAN_* or JENKINS_USER/JENKINS_PASSWORD."
            )
        self.base_url = base_url.rstrip("/")
        self.user = user
        self.password = password
        self.timeout = timeout
        self.poll_interval = poll_interval
        self._connect_host, self._connect_port, self._host_header = self._parse_resolve(
            curl_resolve, self.base_url
        )
        self._crumb: str = ""
        self._crumb_field: str = "Jenkins-Crumb"
        self._opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor())

    @staticmethod
    def _parse_resolve(curl_resolve: str, base_url: str) -> tuple[str, int, str | None]:
        parsed = urlparse(base_url)
        host = parsed.hostname or "localhost"
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        if not curl_resolve:
            return host, port, None
        # <JENKINS_URL>:<JENKINS_INTERNAL_IP>
        parts = curl_resolve.split(":")
        if len(parts) >= 3:
            resolve_host, resolve_port, ip = parts[0], int(parts[1]), parts[2]
            if resolve_host == host and resolve_port == port:
                return ip, port, host
        return host, port, None

    def _auth_header(self) -> str:
        import base64

        token = base64.b64encode(f"{self.user}:{self.password}".encode()).decode("ascii")
        return f"Basic {token}"

    def _request(
        self,
        method: str,
        url: str,
        data: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
    ) -> tuple[int, dict[str, str], bytes]:
        parsed = urlparse(url)
        path = parsed.path or "/"
        if parsed.query:
            path = f"{path}?{parsed.query}"

        connect_host = self._connect_host
        connect_port = self._connect_port
        req_headers = {"Authorization": self._auth_header()}
        if self._host_header:
            req_headers["Host"] = self._host_header
        if headers:
            req_headers.update(headers)

        body: bytes | None = None
        if data is not None:
            body = urllib.parse.urlencode(data).encode("utf-8")
            req_headers["Content-Type"] = "application/x-www-form-urlencoded"

        req = urllib.request.Request(
            url=f"{parsed.scheme}://{connect_host}:{connect_port}{path}",
            data=body,
            headers=req_headers,
            method=method,
        )
        try:
            with self._opener.open(req, timeout=60) as resp:
                resp_headers = {k: v for k, v in resp.headers.items()}
                content = resp.read()
                return resp.status, resp_headers, content
        except urllib.error.HTTPError as e:
            raise JenkinsError(f"HTTP {e.code} {method} {url}: {e.read()[:500]!r}") from e
        except urllib.error.URLError as e:
            raise JenkinsError(f"Request failed {method} {url}: {e}") from e

    def fetch_crumb(self) -> None:
        try:
            _, _, body = self._request("GET", f"{self.base_url}/crumbIssuer/api/json")
            data = json.loads(body.decode("utf-8"))
            self._crumb = data.get("crumb", "")
            self._crumb_field = data.get("crumbRequestField", "Jenkins-Crumb")
        except JenkinsError:
            self._crumb = ""

    def job_url(self, job_path: str) -> str:
        path = job_path if job_path.startswith("/") else f"/{job_path}"
        return f"{self.base_url}{path}"

    def get_job_json(self, job_path: str, tree: str = "") -> dict[str, Any]:
        suffix = f"api/json?tree={tree}" if tree else "api/json?depth=2"
        url = f"{self.job_url(job_path).rstrip('/')}/{suffix}"
        _, _, body = self._request("GET", url)
        return json.loads(body.decode("utf-8"))

    def get_parameter_definitions(self, job_path: str) -> list[dict[str, Any]]:
        """Fetch parameter definitions from Jenkins (live API, per-job)."""
        data = self.get_job_json(
            job_path,
            tree="property[parameterDefinitions[name,description,type,defaultParameterValue[value],choices]],"
            "actions[parameterDefinitions[name,description,type,defaultParameterValue[value],choices]]",
        )
        definitions: list[dict[str, Any]] = []
        seen: set[str] = set()

        def add(defn: dict[str, Any]) -> None:
            name = defn.get("name")
            if name and name not in seen:
                seen.add(name)
                definitions.append(defn)

        for prop in data.get("property") or []:
            if not isinstance(prop, dict):
                continue
            for defn in prop.get("parameterDefinitions") or []:
                if isinstance(defn, dict):
                    add(defn)

        for action in data.get("actions") or []:
            if not isinstance(action, dict):
                continue
            for defn in action.get("parameterDefinitions") or []:
                if isinstance(defn, dict):
                    add(defn)

        if not definitions:
            # Fallback: full depth scan (slower, works on more Jenkins versions)
            full = self.get_job_json(job_path)
            for prop in full.get("property") or []:
                if isinstance(prop, dict) and "parameterDefinitions" in prop:
                    for defn in prop["parameterDefinitions"]:
                        if isinstance(defn, dict):
                            add(defn)
        return definitions

    def is_parameterized(self, job_path: str) -> bool:
        return bool(self.get_parameter_definitions(job_path))

    def trigger_build_simple(self, job_path: str) -> str:
        """Trigger non-parameterized job."""
        self.fetch_crumb()
        url = f"{self.job_url(job_path)}/build"
        headers: dict[str, str] = {}
        if self._crumb:
            headers[self._crumb_field] = self._crumb
        status, resp_headers, _ = self._request("POST", url, data={}, headers=headers)
        location = resp_headers.get("Location") or resp_headers.get("location")
        if not location:
            raise JenkinsError(f"No queue Location after build (status={status})")
        return location

    def trigger_build(self, job_path: str, params: dict[str, str]) -> str:
        if not params and not self.is_parameterized(job_path):
            return self.trigger_build_simple(job_path)
        self.fetch_crumb()
        url = f"{self.job_url(job_path)}/buildWithParameters"
        headers: dict[str, str] = {}
        if self._crumb:
            headers[self._crumb_field] = self._crumb
        status, resp_headers, _ = self._request("POST", url, data=params, headers=headers)
        location = resp_headers.get("Location") or resp_headers.get("location")
        if not location:
            raise JenkinsError(f"No queue Location after trigger (status={status})")
        return location

    def wait_queue(self, queue_url: str) -> str:
        elapsed = 0
        while elapsed < self.timeout:
            _, _, body = self._request("GET", f"{queue_url.rstrip('/')}/api/json")
            data = json.loads(body.decode("utf-8"))
            exe = data.get("executable") or {}
            build_url = exe.get("url")
            if build_url:
                return build_url
            time.sleep(self.poll_interval)
            elapsed += self.poll_interval
        raise JenkinsError(f"Queue timeout ({self.timeout}s): {queue_url}")

    def wait_build(self, build_url: str) -> dict[str, Any]:
        elapsed = 0
        while elapsed < self.timeout:
            _, _, body = self._request("GET", f"{build_url.rstrip('/')}/api/json")
            data = json.loads(body.decode("utf-8"))
            result = data.get("result")
            if result:
                if result != "SUCCESS":
                    raise JenkinsError(f"Build {result}: {build_url}")
                return data
            time.sleep(self.poll_interval)
            elapsed += self.poll_interval
        raise JenkinsError(f"Build timeout ({self.timeout}s): {build_url}")

    def trigger_and_wait(self, job_path: str, params: dict[str, str]) -> dict[str, Any]:
        queue_url = self.trigger_build(job_path, params)
        build_url = self.wait_queue(queue_url)
        return self.wait_build(build_url)

    def get_last_successful_build(self, job_path: str) -> dict[str, Any] | None:
        """Return lastSuccessfulBuild metadata, or None if the job never succeeded."""
        url = (
            f"{self.job_url(job_path).rstrip('/')}/lastSuccessfulBuild/api/json"
            "?tree=number,url,displayName,result,timestamp,actions[parameters[name,value]]"
        )
        try:
            _, _, body = self._request("GET", url)
            data = json.loads(body.decode("utf-8"))
            if data.get("result") and data.get("result") != "SUCCESS":
                return None
            return data
        except JenkinsError as e:
            if "HTTP 404" in str(e):
                return None
            raise

    def get_last_successful_build_params(self, job_path: str) -> dict[str, str]:
        """Parameter name → value from the most recent SUCCESS build."""
        build = self.get_last_successful_build(job_path)
        if not build:
            return {}
        params: dict[str, str] = {}
        for action in build.get("actions") or []:
            if not isinstance(action, dict):
                continue
            for item in action.get("parameters") or []:
                if not isinstance(item, dict):
                    continue
                name = item.get("name")
                if not name:
                    continue
                val = item.get("value")
                if val is not None:
                    params[str(name)] = str(val)
        return params

    def last_success(self, job_path: str, project: str = "") -> dict[str, Any]:
        url = f"{self.job_url(job_path)}/api/json?tree=builds[number,result,url,displayName]{{0,30}}"
        _, _, body = self._request("GET", url)
        data = json.loads(body.decode("utf-8"))
        for build in data.get("builds", []):
            if build.get("result") != "SUCCESS":
                continue
            display = build.get("displayName", "")
            if project and project not in display:
                continue
            return build
        raise JenkinsError(f"No SUCCESS build found for project={project!r}")

    def console_tail(self, job_path: str, build_number: int, tail: int = 200) -> str:
        url = f"{self.job_url(job_path)}/{build_number}/consoleText"
        _, _, body = self._request("GET", url)
        lines = body.decode("utf-8", errors="replace").splitlines()
        return "\n".join(lines[-tail:])


def parse_deploy_version(display_name: str) -> str:
    m = re.search(r"(\d+\.\d+\.\d+)_(\d+)\s*$", display_name)
    return f"{m.group(1)}_{m.group(2)}" if m else ""


