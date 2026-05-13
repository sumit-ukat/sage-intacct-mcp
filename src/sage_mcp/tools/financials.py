"""Financial statement tools for Sage Intacct MCP."""

import json

from pydantic import BaseModel, ConfigDict, Field

from sage_mcp.client import get_client, handle_error


class DateRangeReportInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    start_date: str = Field(..., description="Period start date MM/DD/YYYY (e.g., '01/01/2024')")
    end_date: str = Field(..., description="Period end date MM/DD/YYYY (e.g., '12/31/2024')")
    report_name: str = Field(description="Exact saved-report name in Sage Intacct")


class BalanceSheetInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    as_of_date: str = Field(..., description="Balance sheet date MM/DD/YYYY (e.g., '12/31/2024')")
    report_name: str = Field(default="Balance Sheet", description="Exact saved-report name in Sage Intacct")


class ProfitAndLossInput(DateRangeReportInput):
    report_name: str = Field(default="Profit and Loss", description="Exact saved-report name in Sage Intacct")


class CashFlowInput(DateRangeReportInput):
    report_name: str = Field(default="Cash Flow Statement", description="Exact saved-report name in Sage Intacct")


async def _run_date_range_report(report_name: str, start_date: str, end_date: str) -> dict:
    function_xml = (
        "<readReport>"
        f"<report>{report_name}</report>"
        "<waitTimeout>60</waitTimeout>"
        "<returnDef>false</returnDef>"
        "<filters>"
        "<filter>"
        "<field>START_DATE</field>"
        f"<value>{start_date}</value>"
        "</filter>"
        "<filter>"
        "<field>END_DATE</field>"
        f"<value>{end_date}</value>"
        "</filter>"
        "</filters>"
        "</readReport>"
    )
    return await get_client().execute(function_xml)


async def get_profit_and_loss(params: ProfitAndLossInput) -> str:
    """Run the Profit and Loss (Income Statement) saved report from Sage Intacct.

    Executes a saved P&L report for the specified date range. The report must exist
    in your Sage Intacct instance under Reports.

    Args:
        params (ProfitAndLossInput):
            - start_date (str): Period start MM/DD/YYYY
            - end_date (str): Period end MM/DD/YYYY
            - report_name (str): Saved-report name (default 'Profit and Loss')

    Returns:
        str: JSON with revenue, expense, and net income rows.

    Error responses:
        "Error: <message>" — report not found, invalid date, permission denied
    """
    try:
        result = await _run_date_range_report(params.report_name, params.start_date, params.end_date)
        return json.dumps(
            {
                "report": params.report_name,
                "period": {"start": params.start_date, "end": params.end_date},
                "data": result["data"],
            },
            indent=2,
        )
    except Exception as exc:
        return handle_error(exc)


async def get_balance_sheet(params: BalanceSheetInput) -> str:
    """Run the Balance Sheet saved report from Sage Intacct.

    Executes a saved Balance Sheet report as of the specified date. The report must exist
    in your Sage Intacct instance under Reports.

    Args:
        params (BalanceSheetInput):
            - as_of_date (str): Balance sheet date MM/DD/YYYY
            - report_name (str): Saved-report name (default 'Balance Sheet')

    Returns:
        str: JSON with assets, liabilities, and equity rows.

    Error responses:
        "Error: <message>" — report not found, invalid date, permission denied
    """
    try:
        function_xml = (
            "<readReport>"
            f"<report>{params.report_name}</report>"
            "<waitTimeout>60</waitTimeout>"
            "<returnDef>false</returnDef>"
            "<filters>"
            "<filter>"
            "<field>AS_OF_DATE</field>"
            f"<value>{params.as_of_date}</value>"
            "</filter>"
            "</filters>"
            "</readReport>"
        )
        result = await get_client().execute(function_xml)
        return json.dumps(
            {
                "report": params.report_name,
                "as_of_date": params.as_of_date,
                "data": result["data"],
            },
            indent=2,
        )
    except Exception as exc:
        return handle_error(exc)


async def get_cash_flow(params: CashFlowInput) -> str:
    """Run the Cash Flow Statement saved report from Sage Intacct.

    Executes a saved Cash Flow Statement report for the specified date range.
    The report must exist in your Sage Intacct instance under Reports.

    Args:
        params (CashFlowInput):
            - start_date (str): Period start MM/DD/YYYY
            - end_date (str): Period end MM/DD/YYYY
            - report_name (str): Saved-report name (default 'Cash Flow Statement')

    Returns:
        str: JSON with operating, investing, and financing activity rows.

    Error responses:
        "Error: <message>" — report not found, invalid date, permission denied
    """
    try:
        result = await _run_date_range_report(params.report_name, params.start_date, params.end_date)
        return json.dumps(
            {
                "report": params.report_name,
                "period": {"start": params.start_date, "end": params.end_date},
                "data": result["data"],
            },
            indent=2,
        )
    except Exception as exc:
        return handle_error(exc)
