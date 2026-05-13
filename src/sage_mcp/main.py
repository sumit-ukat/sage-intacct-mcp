"""Sage Intacct MCP server entry point."""

from mcp.server.fastmcp import FastMCP

from sage_mcp.tools.ap import GetAPAgingInput, GetAPBillsInput, get_ap_aging, get_ap_bills
from sage_mcp.tools.ar import GetARAgingInput, GetARInvoicesInput, get_ar_aging, get_ar_invoices
from sage_mcp.tools.financials import (
    BalanceSheetInput,
    CashFlowInput,
    ProfitAndLossInput,
    get_balance_sheet,
    get_cash_flow,
    get_profit_and_loss,
)
from sage_mcp.tools.gl import GetGLEntriesInput, GetTrialBalanceInput, get_gl_entries, get_trial_balance
from sage_mcp.tools.reports import ListReportsInput, RunReportInput, list_reports, run_report

mcp = FastMCP("sage_intacct_mcp")

# ── General Ledger ────────────────────────────────────────────────────────────

@mcp.tool(
    name="intacct_get_gl_entries",
    annotations={"title": "Get GL Entries", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True},
)
async def _get_gl_entries(params: GetGLEntriesInput) -> str:
    """Fetch General Ledger journal entries filtered by date range and optionally account number."""
    return await get_gl_entries(params)


@mcp.tool(
    name="intacct_get_trial_balance",
    annotations={"title": "Get Trial Balance", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True},
)
async def _get_trial_balance(params: GetTrialBalanceInput) -> str:
    """Run the Trial Balance saved report from Sage Intacct."""
    return await get_trial_balance(params)


# ── Accounts Payable ──────────────────────────────────────────────────────────

@mcp.tool(
    name="intacct_get_ap_bills",
    annotations={"title": "Get AP Bills", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True},
)
async def _get_ap_bills(params: GetAPBillsInput) -> str:
    """Fetch Accounts Payable bills with optional filters for status, vendor, and date range."""
    return await get_ap_bills(params)


@mcp.tool(
    name="intacct_get_ap_aging",
    annotations={"title": "Get AP Aging Report", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True},
)
async def _get_ap_aging(params: GetAPAgingInput) -> str:
    """Run the AP Aging saved report showing outstanding payables by aging bucket."""
    return await get_ap_aging(params)


# ── Accounts Receivable ───────────────────────────────────────────────────────

@mcp.tool(
    name="intacct_get_ar_invoices",
    annotations={"title": "Get AR Invoices", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True},
)
async def _get_ar_invoices(params: GetARInvoicesInput) -> str:
    """Fetch Accounts Receivable invoices with optional filters for status, customer, and date range."""
    return await get_ar_invoices(params)


@mcp.tool(
    name="intacct_get_ar_aging",
    annotations={"title": "Get AR Aging Report", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True},
)
async def _get_ar_aging(params: GetARAgingInput) -> str:
    """Run the AR Aging saved report showing outstanding receivables by aging bucket."""
    return await get_ar_aging(params)


# ── Financial Statements ──────────────────────────────────────────────────────

@mcp.tool(
    name="intacct_get_profit_and_loss",
    annotations={"title": "Get Profit & Loss", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True},
)
async def _get_profit_and_loss(params: ProfitAndLossInput) -> str:
    """Run the Profit and Loss (Income Statement) saved report for a specified date range."""
    return await get_profit_and_loss(params)


@mcp.tool(
    name="intacct_get_balance_sheet",
    annotations={"title": "Get Balance Sheet", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True},
)
async def _get_balance_sheet(params: BalanceSheetInput) -> str:
    """Run the Balance Sheet saved report as of a specified date."""
    return await get_balance_sheet(params)


@mcp.tool(
    name="intacct_get_cash_flow",
    annotations={"title": "Get Cash Flow Statement", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True},
)
async def _get_cash_flow(params: CashFlowInput) -> str:
    """Run the Cash Flow Statement saved report for a specified date range."""
    return await get_cash_flow(params)


# ── Reports ───────────────────────────────────────────────────────────────────

@mcp.tool(
    name="intacct_list_reports",
    annotations={"title": "List Saved Reports", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True},
)
async def _list_reports(params: ListReportsInput) -> str:
    """List all saved report definitions available in Sage Intacct."""
    return await list_reports(params)


@mcp.tool(
    name="intacct_run_report",
    annotations={"title": "Run Saved Report", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True},
)
async def _run_report(params: RunReportInput) -> str:
    """Run any saved report by name. Use intacct_list_reports to discover available report names."""
    return await run_report(params)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
