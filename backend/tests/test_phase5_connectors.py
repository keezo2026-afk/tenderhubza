from pathlib import Path

import httpx
import pytest

from app.connectors.municipal.ethekwini import EThekwiniConnector
from app.connectors.soe.eskom import EskomConnector
from app.connectors.testing import ConnectorContractHarness

FIX = Path(__file__).parent / "fixtures" / "phase5"


def client(routes):
    def handler(request):
        return httpx.Response(
            200,
            text=routes.get(str(request.url), ""),
            request=request,
            headers={"content-type": "text/html"},
        )

    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


@pytest.mark.asyncio
async def test_ethekwini_verified_fixture_contract():
    html = (FIX / "ethekwini.html").read_text()
    url = EThekwiniConnector.LIST_URL
    async with client({url: html}) as http:
        connector = EThekwiniConnector(client=http)
        results = await ConnectorContractHarness(connector).exercise()
        ConnectorContractHarness(connector).assert_contract(results)
        t = results[0]["normalized"]
        assert t.reference_number == "ABC-123"
        assert t.municipality == "eThekwini Metropolitan Municipality"
        assert len(t.documents) == 1


@pytest.mark.asyncio
async def test_eskom_verified_fixture_contract():
    listing = (FIX / "eskom-list.html").read_text()
    detail = (FIX / "eskom-detail.html").read_text()
    list_url = "https://tenderbulletin.eskom.co.za/?pageSize=10&pageNumber=1"
    async with client(
        {list_url: listing, "https://tenderbulletin.eskom.co.za/tender/90165": detail}
    ) as http:
        connector = EskomConnector(client=http)
        results = await ConnectorContractHarness(connector).exercise()
        ConnectorContractHarness(connector).assert_contract(results)
        t = results[0]["normalized"]
        assert t.reference_number == "MWP2759GX"
        assert t.province == "Free State"
        assert len(t.documents) == 1
