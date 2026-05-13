"""Sage Intacct XML Web Services API client."""

import os
import uuid
import xml.etree.ElementTree as ET
import xml.sax.saxutils as saxutils
from typing import Any, Dict, Optional

import httpx
from dotenv import load_dotenv

load_dotenv()

INTACCT_API_URL = "https://api.intacct.com/ia/xml/xmlgw.phtml"


class IntacctError(Exception):
    pass


class SageIntacctClient:
    def __init__(self) -> None:
        self.sender_id = os.getenv("INTACCT_SENDER_ID")
        self.sender_password = os.getenv("INTACCT_SENDER_PASSWORD")
        self.company_id = os.getenv("INTACCT_COMPANY_ID")
        self.user_id = os.getenv("INTACCT_USER_ID")
        self.user_password = os.getenv("INTACCT_USER_PASSWORD")

        missing = [
            k for k, v in {
                "INTACCT_SENDER_ID": self.sender_id,
                "INTACCT_SENDER_PASSWORD": self.sender_password,
                "INTACCT_COMPANY_ID": self.company_id,
                "INTACCT_USER_ID": self.user_id,
                "INTACCT_USER_PASSWORD": self.user_password,
            }.items() if not v
        ]
        if missing:
            raise IntacctError(
                f"Missing required environment variables: {', '.join(missing)}. "
                "Copy .env.example to .env and fill in your credentials."
            )

    def _build_request(self, function_xml: str) -> str:
        control_id = str(uuid.uuid4())
        e = saxutils.escape  # XML-escape special chars in credentials
        return (
            '<?xml version="1.0" encoding="UTF-8"?>'
            "<request>"
            "<control>"
            f"<senderid>{e(self.sender_id)}</senderid>"
            f"<password>{e(self.sender_password)}</password>"
            f"<controlid>{control_id}</controlid>"
            "<uniqueid>false</uniqueid>"
            "<dtdversion>3.0</dtdversion>"
            "<includewhitespace>false</includewhitespace>"
            "</control>"
            "<operation>"
            "<authentication>"
            "<login>"
            f"<userid>{e(self.user_id)}</userid>"
            f"<companyid>{e(self.company_id)}</companyid>"
            f"<password>{e(self.user_password)}</password>"
            "</login>"
            "</authentication>"
            "<content>"
            f'<function controlid="f-{control_id}">'
            f"{function_xml}"
            "</function>"
            "</content>"
            "</operation>"
            "</request>"
        )

    async def execute(self, function_xml: str) -> Dict[str, Any]:
        xml_request = self._build_request(function_xml)
        async with httpx.AsyncClient(timeout=60.0) as http:
            response = await http.post(
                INTACCT_API_URL,
                data={"xmlrequest": xml_request},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()
        return self._parse_response(response.text)

    def _parse_response(self, xml_text: str) -> Dict[str, Any]:
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as exc:
            raise IntacctError(f"Failed to parse API response: {exc}") from exc

        control = root.find("control")
        if control is not None and control.findtext("status") == "failure":
            msgs = [
                f"{e.findtext('errorno')}: {e.findtext('description')}"
                for e in control.findall(".//error")
            ]
            raise IntacctError(f"Control error: {'; '.join(msgs)}")

        operation = root.find("operation")
        if operation is None:
            raise IntacctError("Invalid response: missing <operation>")

        result = operation.find(".//result")
        if result is None:
            raise IntacctError("Invalid response: missing <result>")

        if result.findtext("status") == "failure":
            msgs = [
                f"{e.findtext('errorno')}: {e.findtext('description2') or e.findtext('description')}"
                for e in result.findall(".//error")
            ]
            raise IntacctError(f"API error: {'; '.join(msgs)}")

        data_el = result.find("data")
        if data_el is None:
            return {"status": "success", "data": [], "totalcount": "0", "numremaining": "0"}

        records = [self._element_to_dict(child) for child in data_el]
        return {
            "status": "success",
            "totalcount": data_el.get("totalcount", str(len(records))),
            "numremaining": data_el.get("numremaining", "0"),
            "resultId": data_el.get("resultId"),
            "data": records,
        }

    def _element_to_dict(self, element: ET.Element) -> Any:
        if len(element) == 0:
            return element.text

        result: Dict[str, Any] = {}
        for child in element:
            child_data = self._element_to_dict(child)
            if child.tag in result:
                if not isinstance(result[child.tag], list):
                    result[child.tag] = [result[child.tag]]
                result[child.tag].append(child_data)
            else:
                result[child.tag] = child_data
        return result

    async def read_more(self, result_id: str) -> Dict[str, Any]:
        return await self.execute(f"<readMore><resultId>{result_id}</resultId></readMore>")


def handle_error(exc: Exception) -> str:
    if isinstance(exc, IntacctError):
        return f"Error: {exc}"
    if isinstance(exc, httpx.HTTPStatusError):
        code = exc.response.status_code
        if code == 401:
            return "Error: Authentication failed. Check your Sage Intacct credentials."
        if code == 403:
            return "Error: Permission denied. The Web Services user lacks access to this resource."
        if code == 429:
            return "Error: Rate limit exceeded. Please wait before retrying."
        return f"Error: HTTP {code} from Sage Intacct API."
    if isinstance(exc, httpx.TimeoutException):
        return "Error: Request timed out. Sage Intacct API did not respond in time."
    return f"Error: {type(exc).__name__}: {exc}"


_client: Optional[SageIntacctClient] = None


def get_client() -> SageIntacctClient:
    global _client
    if _client is None:
        _client = SageIntacctClient()
    return _client
