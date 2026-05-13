"""Accounts Receivable tools for Sage Intacct MCP."""

import json
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from sage_mcp.client import get_client, handle_error


class GetARInvoicesInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    status: Optional[str] = Field(
        default=None,
        description="Filter by invoice status: 'A' (approved), 'S' (submitted), 'X' (cancelled), 'P' (paid), 'F' (partial)",
    )
    customer: Optional[str] = Field(default=None, description="Filter by customer ID or name")
    start_date: Optional[str] = Field(default=None, description="Invoice date from MM/DD/YYYY")
    end_date: Optional[str] = Field(default=None, description="Invoice date to MM/DD/YYYY")
    limit: int = Field(default=100, ge=1, le=1000, description="Max records (1–1000)")
    offset: int = Field(default=0, ge=0, description="Pagination offset")


class GetARAgingInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    report_name: str = Field(
        default="AR Aging",
        description="Name of the AR Aging saved report in Sage Intacct",
    )


async def get_ar_invoices(params: GetARInvoicesInput) -> str:
    """Fetch Accounts Receivable invoices from Sage Intacct.

    Retrieves ARINVOICE records with optional filters for status, customer, and date range.
    Returns customer details, invoice amounts, due dates, and payment status.

    Args:
        params (GetARInvoicesInput):
            - status (Optional[str]): A=approved, S=submitted, X=cancelled, P=paid, F=partial
            - customer (Optional[str]): Customer ID or name filter
            - start_date (Optional[str]): Invoice date from MM/DD/YYYY
            - end_date (Optional[str]): Invoice date to MM/DD/YYYY
            - limit (int): Max records (default 100)
            - offset (int): Pagination offset (default 0)

    Returns:
        str: JSON with keys: totalcount, numremaining, offset, invoices[]

    Error responses:
        "Error: <message>" — authentication failure, permission denied
    """
    try:
        query_parts: list[str] = []
        if params.status:
            query_parts.append(f"STATE = '{params.status}'")
        if params.customer:
            query_parts.append(
                f"(CUSTOMERID = '{params.customer}' OR CUSTOMERNAME LIKE '%{params.customer}%')"
            )
        if params.start_date:
            query_parts.append(f"WHENCREATED >= '{params.start_date}'")
        if params.end_date:
            query_parts.append(f"WHENCREATED <= '{params.end_date}'")

        query = " AND ".join(query_parts) if query_parts else ""

        function_xml = (
            "<readByQuery>"
            "<object>ARINVOICE</object>"
            "<fields>RECORDNO,CUSTOMERID,CUSTOMERNAME,WHENCREATED,WHENDUE,DUEDATE,"
            "TOTALENTERED,TOTALDUE,TOTALPAID,STATE,DESCRIPTION,CURRENCY,"
            "TERMNAME,DOCNUMBER,PONUMBER</fields>"
            f"<query>{query}</query>"
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
                "invoices": result["data"],
            },
            indent=2,
        )
    except Exception as exc:
        return handle_error(exc)


async def get_ar_aging(params: GetARAgingInput) -> str:
    """Run the AR Aging saved report from Sage Intacct.

    Executes a saved AR Aging report showing outstanding receivables by aging bucket.
    The report must exist in your Sage Intacct instance.

    Args:
        params (GetARAgingInput):
            - report_name (str): Exact saved-report name (default 'AR Aging')

    Returns:
        str: JSON with report rows grouped by customer and aging period.

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
