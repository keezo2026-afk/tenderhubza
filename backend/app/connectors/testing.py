"""Reusable fixture-only connector contract harness."""

from app.connectors.base import TenderConnector


class ConnectorContractHarness:
    def __init__(self, connector: TenderConnector):
        self.connector = connector

    async def exercise(self):
        discovered = list(await self.connector.discover())
        results = []
        for item in discovered:
            raw = await self.connector.fetch(item)
            parsed = await self.connector.parse(raw)
            normalized = await self.connector.normalize(parsed)
            documents = list(await self.connector.download_documents(normalized))
            results.append(
                {
                    "item": item,
                    "raw": raw,
                    "parsed": parsed,
                    "normalized": normalized,
                    "documents": documents,
                }
            )
        return results

    def assert_contract(self, results):
        for result in results:
            assert result["raw"].payload is not None
            assert result["normalized"].source_reference
            assert result["normalized"].title
            assert result["normalized"].source_url.startswith("https://")
