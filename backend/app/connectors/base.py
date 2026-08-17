"""Stable connector contract. Source implementations must be isolated and side-effect free until fetch."""
from abc import ABC,abstractmethod
from dataclasses import dataclass
from typing import Any,Iterable
from app.ingestion.contracts import DiscoveredItem,DocumentReference,NormalizedTender,RawPayload
@dataclass(frozen=True)
class ConnectorContext: source_id:str; connector_version:str
class TenderConnector(ABC):
    @abstractmethod
    async def discover(self)->Iterable[DiscoveredItem]: ...
    @abstractmethod
    async def fetch(self,item:DiscoveredItem)->RawPayload: ...
    @abstractmethod
    async def parse(self,payload:RawPayload)->dict[str,Any]: ...
    @abstractmethod
    async def normalize(self,parsed:dict[str,Any])->NormalizedTender: ...
    @abstractmethod
    async def download_documents(self,tender:NormalizedTender)->Iterable[DocumentReference]: ...
