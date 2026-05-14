"""General Ledger tools for Sage Intacct MCP."""

import json
import xml.sax.saxutils as saxutils
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from sage_mcp.client import get_client, handle_error


class GetGLEntriesInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    start_date: str = Field(..., description="Start date in MM/DD/YYYY format (e.g., '01/01/2024')")
    end_date: str = Field(..., description="End date in MM/DD/YYYY format (e.g., '12/31/2024')")
    account: Optional[str] = Field(default=None, description="Filter by GL account number (e.g., '1000')")
    location: Optional[str] = Field(default=None, description="Filter by location/entity (e.g., 'L-BL' or 'E-600')")
    limit: int = Field(default=100, ge=1, le=1000, description="Max records to return (1–1000)")
    include_inactive_locations: bool = Field(
        default=False,
        description="Include entries posted to inactive locations/entities. Default False (matches Balance Sheet view).",
    )


class GetTrialBalanceInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    report_name: str = Field(
        default="Trial Balance",
        description="Name of the Trial Balance saved report in Sage Intacct",
    )


class GetAccountBalanceInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    account: str = Field(..., description="GL account number, e.g. '1208' or comma-separated '1201,1202,1203'")
    as_of_date: str = Field(..., description="Balance as-at date MM/DD/YYYY (e.g., '04/30/2026')")
    location: Optional[str] = Field(default=None, description="Optional location filter (e.g., 'L-BL', 'E-600')")
    include_inactive_locations: bool = Field(
        default=False,
        description="Include entries posted to inactive locations/entities. Default False.",
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
        client = get_client()

        query_parts = [
            f"BATCH_DATE >= '{params.start_date}'",
            f"BATCH_DATE <= '{params.end_date}'",
        ]
        if params.account:
            query_parts.append(f"ACCOUNTNO = '{params.account}'")
        if params.location:
            query_parts.append(f"LOCATION = '{params.location}'")
        query = " AND ".join(query_parts)

        function_xml = (
            "<readByQuery>"
            "<object>GLENTRY</object>"
            "<fields>RECORDNO,BATCH_DATE,BATCHNO,ACCOUNTNO,ACCOUNTTITLE,"
            "AMOUNT,TR_TYPE,CURRENCY,DESCRIPTION,ENTRY_DATE,LOCATION,"
            "CLASSID,CUSTOMERID,ITEMID,WHENCREATED,WHENMODIFIED</fields>"
            f"<query>{saxutils.escape(query)}</query>"
            f"<pagesize>{params.limit}</pagesize>"
            "</readByQuery>"
        )

        result = await client.execute(function_xml)
        entries = result["data"]

        # Filter out entries posted to inactive locations/entities (default behaviour)
        filtered_count = 0
        if not params.include_inactive_locations:
            active_locs = await client.get_active_locations()
            kept = []
            for entry in entries:
                loc = entry.get("LOCATION") if isinstance(entry, dict) else None
                if not loc or loc in active_locs:
                    kept.append(entry)
                else:
                    filtered_count += 1
            entries = kept

        return json.dumps(
            {
                "totalcount": result["totalcount"],
                "numremaining": result["numremaining"],
                "filtered_inactive_locations": filtered_count,
                "entries": entries,
            },
            indent=2,
        )
    except Exception as exc:
        return handle_error(exc)


async def get_account_balance(params: GetAccountBalanceInput) -> str:
    """Calculate the trial-balance figure for a GL account as at a given date.

    Sums all GL entries (debits − credits) for the specified account number(s) from
    inception through `as_of_date`. Automatically excludes entries posted to inactive
    locations/entities. Equivalent to running a one-line trial balance.

    Args:
        params (GetAccountBalanceInput):
            - account (str): GL account number (single or comma-separated list)
            - as_of_date (str): Balance date MM/DD/YYYY
            - location (Optional[str]): Optional location/entity filter
            - include_inactive_locations (bool): Default False

    Returns:
        str: JSON with per-account balance: {account, title, debits, credits, net, entries_count}
    """
    try:
        client = get_client()
        active_locs = None if params.include_inactive_locations else await client.get_active_locations()

        accounts = [a.strip() for a in params.account.split(",") if a.strip()]
        # Build OR clause for multiple accounts: ACCOUNTNO IN ('1201','1202',...)
        if len(accounts) == 1:
            acct_clause = f"ACCOUNTNO = '{accounts[0]}'"
        else:
            acct_clause = "ACCOUNTNO IN (" + ",".join(f"'{a}'" for a in accounts) + ")"

        clauses = [acct_clause, f"BATCH_DATE <= '{params.as_of_date}'"]
        if params.location:
            clauses.append(f"LOCATION = '{params.location}'")
        query = " AND ".join(clauses)

        function_xml = (
            "<readByQuery>"
            "<object>GLENTRY</object>"
            "<fields>ACCOUNTNO,ACCOUNTTITLE,AMOUNT,TR_TYPE,LOCATION</fields>"
            f"<query>{saxutils.escape(query)}</query>"
            "<pagesize>1000</pagesize>"
            "</readByQuery>"
        )

        rows = await client.fetch_all_pages(function_xml)

        # Aggregate per account
        agg: dict = {}
        filtered_inactive = 0
        for r in rows:
            if not isinstance(r, dict):
                continue
            loc = r.get("LOCATION") or ""
            if active_locs is not None and loc and loc not in active_locs:
                filtered_inactive += 1
                continue
            acct = r.get("ACCOUNTNO") or ""
            title = r.get("ACCOUNTTITLE") or ""
            amt = float(r.get("AMOUNT") or 0)
            tr = int(r.get("TR_TYPE") or 0)
            bucket = agg.setdefault(acct, {"title": title, "debits": 0.0, "credits": 0.0, "count": 0})
            if tr == 1:
                bucket["debits"] += amt
            else:
                bucket["credits"] += amt
            bucket["count"] += 1

        out = []
        grand_total = 0.0
        for acct in accounts:
            b = agg.get(acct, {"title": "(no entries)", "debits": 0.0, "credits": 0.0, "count": 0})
            net = round(b["debits"] - b["credits"], 2)
            grand_total += net
            out.append(
                {
                    "account": acct,
                    "title": b["title"],
                    "debits": round(b["debits"], 2),
                    "credits": round(b["credits"], 2),
                    "net_balance": net,
                    "entries_count": b["count"],
                }
            )

        return json.dumps(
            {
                "as_of_date": params.as_of_date,
                "location_filter": params.location,
                "filtered_inactive_locations": filtered_inactive,
                "accounts": out,
                "total_net_balance": round(grand_total, 2),
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
