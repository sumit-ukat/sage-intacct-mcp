"""Test Sage Intacct API connection."""
import asyncio
import sys
import os
import httpx
import uuid
import xml.sax.saxutils as saxutils

sys.path.insert(0, "src")
from dotenv import load_dotenv
load_dotenv()


async def test():
    sid = saxutils.escape(os.getenv("INTACCT_SENDER_ID", ""))
    spw = saxutils.escape(os.getenv("INTACCT_SENDER_PASSWORD", ""))
    cid = saxutils.escape(os.getenv("INTACCT_COMPANY_ID", ""))
    uid = saxutils.escape(os.getenv("INTACCT_USER_ID", ""))
    upw = saxutils.escape(os.getenv("INTACCT_USER_PASSWORD", ""))
    ctrl = str(uuid.uuid4())

    print(f"Sender ID : {sid}")
    print(f"Company ID: {cid}")
    print(f"User ID   : {uid}")

    xml_parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        "<request><control>",
        f"<senderid>{sid}</senderid>",
        f"<password>{spw}</password>",
        f"<controlid>{ctrl}</controlid>",
        "<uniqueid>false</uniqueid>",
        "<dtdversion>3.0</dtdversion>",
        "</control><operation><authentication><login>",
        f"<userid>{uid}</userid>",
        f"<companyid>{cid}</companyid>",
        f"<password>{upw}</password>",
        "</login></authentication><content>",
        '<function controlid="f1">',
        "<readByQuery><object>GLACCOUNT</object>",
        "<fields>RECORDNO,ACCOUNTNO,TITLE</fields>",
        "<query></query><pagesize>3</pagesize>",
        "</readByQuery></function></content></operation></request>",
    ]
    xml = "".join(xml_parts)

    print(f"\nXML length: {len(xml)}")
    print(f"Char at 465-470: {repr(xml[463:470])}")

    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            "https://api.intacct.com/ia/xml/xmlgw.phtml",
            data={"xmlrequest": xml},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        print(f"\nHTTP Status: {r.status_code}")
        print(r.text)


asyncio.run(test())
