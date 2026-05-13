"""Saved-report management tools for Sage Intacct MCP."""

import json
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from sage_mcp.client import get_client, handle_error


class ListReportsInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    limit: int = Field(default=100, ge=1, le=1000, description="Max records (1–1000)")
    offset: int = Field(default=0, ge=0, description="Pagination offset")


class RunReportInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    report_name: str = Field(..., description="Exact name of the saved report in Sage Intacct", min_length=1)
    start_date: Optional[str] = Field(default=None, description="Optional period start MM/DD/YYYY")
    end_date: Optional[str] = Field(default=None, description="Optional period end MM/DD/YYYY")


async def list_reports(params: ListReportsInput) -> str:
    """List all saved report definitions available in Sage Intacct.

    Queries REPORTDEFINITION to return the names and types of all saved reports
    configured in your Sage Intacct instance.

    Args:
        params (ListReportsInput):
            - limit (int): Max records (default 100)
            - offset (int): Pagination offset (default 0)

    Returns:
        str: JSON with keys: totalcount, numremaining, offset, reports[]
             Each report includes: name, description, reporttype, owner

    Error responses:
        "Error: <message>" — permission denied, authentication failure
    """
    try:
        function_xml = (
            "<readByQuery>"
            "<object>REPORTDEFINITION</object>"
            "<fields>RECORDNO,NAME,DESCRIPTION,REPORTTYPE,OWNER,WHENCREATED,WHENMODIFIED</fields>"
            "<query></query>"
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
                "reports": result["data"],
            },
            indent=2,
        )
    except Exception as exc:
        return handle_error(exc)


async def run_report(params: RunReportInput) -> str:
    """Run any saved report by name from Sage Intacct.

    Executes a saved report and returns all rows. Optionally pass start_date and
    end_date to filter the report period (only applies to date-range reports).

    Args:
        params (RunReportInput):
            - report_name (str): Exact saved-report name (get names from intacct_list_reports)
            - start_date (Optional[str]): Period start MM/DD/YYYY
            - end_date (Optional[str]): Period end MM/DD/YYYY

    Returns:
        str: JSON with keys: report, data[]

    Error responses:
        "Error: <message>" — report not found, invalid date, permission denied
    """
    try:
        filter_xml = ""
        if params.start_date or params.end_date:
            filters: list[str] = []
            if params.start_date:
                filters.append(
                    f"<filter><field>START_DATE</field><value>{params.start_date}</value></filter>"
                )
            if params.end_date:
                filters.append(
                    f"<filter><field>END_DATE</field><value>{params.end_date}</value></filter>"
                )
            filter_xml = f"<filters>{''.join(filters)}</filters>"

        function_xml = (
            "<readReport>"
            f"<report>{params.report_name}</report>"
            "<waitTimeout>60</waitTimeout>"
            "<returnDef>false</returnDef>"
            f"{filter_xml}"
            "</readReport>"
        )
        result = await get_client().execute(function_xml)
        return json.dumps({"report": params.report_name, "data": result["data"]}, indent=2)
    except Exception as exc:
        return handle_error(exc)
