"""General Ledger tools for Sage Intacct MCP."""

import json
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from sage_mcp.client import get_client, handle_error


class GetGLEntriesInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    start_date: str = Field(..., description="Start date in MM/DD/YYYY format (e.g., '01/01/2024')")
    end_date: str = Field(..., description="End date in MM/DD/YYYY format (e.g., '12/31/2024')")
    account: Optional[str] = Field(default=None, description="Filter by GL account number (e.g., '1000')")
    limit: int = Field(default=100, ge=1, le=1000, description="Max records to return (1–1000)")
    offset: int = Field(default=0, ge=0, description="Pagination offset")


class GetTrialBalanceInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    report_name: str = Field(
        default="Trial Balance",
        description="Name of the Trial Balance saved report in Sage Intacct",
    )


async def get_gl_entries(params: GetGLEntriesInput) -> str:
    """Fetch General Ledger journal entries from Sage Intacct.

    Retrieves GLENTRY records filtered by date range and optionally by account number.
    Returns debits, credits, amounts, account details, and posting dates.

    Args:
        params (GetGLEntriesInput):
            - start_date (str): Start date MM/DD/YYYY
            - end_date (str): End date MM/DD/YYYY
            - account (Optional[str]): Filter by account number
            - limit (int): Max records (default 100, max 1000)
            - offset (int): Pagination offset (default 0)

    Returns:
        str: JSON with keys: totalcount, numremaining, offset, entries[]

    Error responses:
        "Error: <message>" — authentication failure, invalid date, permission denied
    """
    try:
        query_parts = [
            f"BATCH_DATE >= '{params.start_date}'",
            f"BATCH_DATE <= '{params.end_date}'",
        ]
        if params.account:
            query_parts.append(f"ACCOUNTNO = '{params.account}'")
        query = " AND ".join(query_parts)

        function_xml = (
            "<readByQuery>"
            "<object>GLENTRY</object>"
            "<fields>RECORDNO,BATCH_DATE,BATCHNO,ACCOUNTNO,ACCOUNTTITLE,"
            "AMOUNT,DEBIT,CREDIT,CURRENCY,DESCRIPTION,ENTRY_DATE,"
            "DEPT_NAME,PROJECT_NAME,WHENCREATED,WHENMODIFIED</fields>"
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
                "entries": result["data"],
            },
            indent=2,
        )
    except Exception as exc:
        return handle_error(exc)


async def get_trial_balance(params: GetTrialBalanceInput) -> str:
    """Run the Trial Balance saved report from Sage Intacct.

    Executes a saved Trial Balance report by name. The report must exist
    in your Sage Intacct instance under Reports.

    Args:
        params (GetTrialBalanceInput):
            - report_name (str): Exact saved-report name (default 'Trial Balance')

    Returns:
        str: JSON with report data rows or error message.

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
