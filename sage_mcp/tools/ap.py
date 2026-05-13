"""Accounts Payable tools for Sage Intacct MCP."""

import json
import xml.sax.saxutils as saxutils
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from sage_mcp.client import get_client, handle_error


class GetAPBillsInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    status: Optional[str] = Field(
        default=None,
        description="Filter by bill status: 'A' (approved), 'S' (submitted), 'X' (cancelled), 'P' (paid), 'F' (partial)",
    )
    vendor: Optional[str] = Field(default=None, description="Filter by vendor ID or name")
    start_date: Optional[str] = Field(default=None, description="Bill date from MM/DD/YYYY")
    end_date: Optional[str] = Field(default=None, description="Bill date to MM/DD/YYYY")
    limit: int = Field(default=100, ge=1, le=1000, description="Max records (1–1000)")
    offset: int = Field(default=0, ge=0, description="Pagination offset")


class GetAPAgingInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    report_name: str = Field(
        default="AP Aging",
        description="Name of the AP Aging saved report in Sage Intacct",
    )


async def get_ap_bills(params: GetAPBillsInput) -> str:
    """Fetch Accounts Payable bills from Sage Intacct.

    Retrieves APBILL records with optional filters for status, vendor, and date range.
    Returns vendor details, amounts due, due dates, and payment status.

    Args:
        params (GetAPBillsInput):
            - status (Optional[str]): A=approved, S=submitted, X=cancelled, P=paid, F=partial
            - vendor (Optional[str]): Vendor ID or name filter
            - start_date (Optional[str]): Bill date from MM/DD/YYYY
            - end_date (Optional[str]): Bill date to MM/DD/YYYY
            - limit (int): Max records (default 100)
            - offset (int): Pagination offset (default 0)

    Returns:
        str: JSON with keys: totalcount, numremaining, offset, bills[]

    Error responses:
        "Error: <message>" — authentication failure, permission denied
    """
    try:
        query_parts: list[str] = []
        if params.status:
            query_parts.append(f"STATE = '{params.status}'")
        if params.vendor:
            query_parts.append(f"(VENDORID = '{params.vendor}' OR VENDORNAME LIKE '%{params.vendor}%')")
        if params.start_date:
            query_parts.append(f"WHENCREATED >= '{params.start_date}'")
        if params.end_date:
            query_parts.append(f"WHENCREATED <= '{params.end_date}'")

        query = " AND ".join(query_parts) if query_parts else ""

        function_xml = (
            "<readByQuery>"
            "<object>APBILL</object>"
            "<fields>RECORDNO,VENDORID,VENDORNAME,WHENCREATED,WHENDUE,DUEDATE,"
            "TOTALENTERED,TOTALDUE,TOTALPAID,STATE,DESCRIPTION,CURRENCY,"
            "TERMNAME,PAYMENTTERM,DOCNUMBER</fields>"
            f"<query>{saxutils.escape(query)}</query>"
            f"<pagesize>{params.limit}</pagesize>"
            f"<offset>{params.offset}</offset>"
            "</readByQuery>"
        )

        result = await get_client().execute(function_xml)
        return json.dumps(
            {
                "totalcount": result["totalcount"],
                "numremaining": result["numremaining"],
                "offset": params.offset,
                "bills": result["data"],
            },
            indent=2,
        )
    except Exception as exc:
        return handle_error(exc)


async def get_ap_aging(params: GetAPAgingInput) -> str:
    """Run the AP Aging saved report from Sage Intacct.

    Executes a saved AP Aging report showing outstanding payables by aging bucket.
    The report must exist in your Sage Intacct instance.

    Args:
        params (GetAPAgingInput):
            - report_name (str): Exact saved-report name (default 'AP Aging')

    Returns:
        str: JSON with report rows grouped by vendor and aging period.

    Error responses:
        "Error: <message>" — report not found, permission denied
    """
    try:
        function_xml = (
            "<readReport>"
            f"<report>{params.report_name}</report>"
            "<waitTimeout>45</waitTimeout>"
            "<returnDef>false</returnDef>"
            "</readReport>"
        )
        result = await get_client().execute(function_xml)
        return json.dumps({"report": params.report_name, "data": result["data"]}, indent=2)
    except Exception as exc:
        return handle_error(exc)
