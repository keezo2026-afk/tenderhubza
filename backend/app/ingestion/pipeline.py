"""Orchestration boundary; queue/scheduler adapters can invoke each source independently."""
import asyncio
from collections.abc import Awaitable,Callable
from app.connectors.base import TenderConnector
from app.ingestion.contracts import PipelineResult,ProcessingStage,ValidationResult
class IngestionPipeline:
    def __init__(self,validate:Callable[...,ValidationResult],persist:Callable[...,Awaitable[str]],index:Callable[[str],Awaitable[None]]): self.validate=validate; self.persist=persist; self.index=index
    async def run(self,connector:TenderConnector)->list[PipelineResult]:
        results=[]
        for item in await connector.discover():
            try:
                raw=await connector.fetch(item); parsed=await connector.parse(raw); normalized=await connector.normalize(parsed); validation=self.validate(normalized)
                if not validation.valid: results.append(PipelineResult(item.source_identifier,False,ProcessingStage.VALIDATION,errors=validation.errors)); continue
                tender_id=await self.persist(raw,normalized); await self.index(tender_id); results.append(PipelineResult(item.source_identifier,True,ProcessingStage.INDEXING,tender_id=tender_id))
            except Exception as exc:
                results.append(PipelineResult(item.source_identifier,False,ProcessingStage.PARSING,errors=[str(exc)]))
        return results
