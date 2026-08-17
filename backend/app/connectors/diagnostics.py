import socket,ssl,time
from dataclasses import asdict,dataclass
from urllib.parse import urlparse
@dataclass
class NetworkDiagnostic:
 endpoint:str;host:str;port:int;dns_addresses:list[str];dns_ms:float|None;tcp_ok:bool;tcp_ms:float|None;tls_ok:bool;tls_ms:float|None;tls_version:str|None;cipher:str|None;certificate_subject:str|None;error_category:str|None;error_type:str|None;error_message:str|None
 def to_dict(self):return asdict(self)
def diagnose_https(endpoint:str,timeout:float=15)->NetworkDiagnostic:
 parsed=urlparse(endpoint);host=parsed.hostname or "";port=parsed.port or 443;addresses=[];dns_ms=tcp_ms=tls_ms=None;tcp_ok=tls_ok=False;tls_version=cipher=subject=category=error_type=error_message=None
 try:
  started=time.perf_counter();infos=socket.getaddrinfo(host,port,type=socket.SOCK_STREAM);dns_ms=round((time.perf_counter()-started)*1000,2);addresses=sorted({i[4][0] for i in infos})
  started=time.perf_counter();raw=socket.create_connection((host,port),timeout=timeout);tcp_ms=round((time.perf_counter()-started)*1000,2);tcp_ok=True
  try:
   started=time.perf_counter();context=ssl.create_default_context();tls=context.wrap_socket(raw,server_hostname=host);tls_ms=round((time.perf_counter()-started)*1000,2);tls_ok=True;tls_version=tls.version();cipher=tls.cipher()[0] if tls.cipher() else None;subject=", ".join("=".join(x) for group in tls.getpeercert().get("subject",()) for x in group);tls.close()
  except ssl.SSLCertVerificationError as exc:category="certificate_verification";raise
  except ssl.SSLError as exc:category="tls_negotiation";raise
 except socket.gaierror as exc:category="dns";error_type=type(exc).__name__;error_message=str(exc)
 except (TimeoutError,socket.timeout) as exc:category=category or ("tls_timeout" if tcp_ok else "tcp_timeout");error_type=type(exc).__name__;error_message=str(exc)
 except OSError as exc:category=category or ("tls_transport" if tcp_ok else "tcp_connect");error_type=type(exc).__name__;error_message=str(exc)
 return NetworkDiagnostic(endpoint,host,port,addresses,dns_ms,tcp_ok,tcp_ms,tls_ok,tls_ms,tls_version,cipher,subject,category,error_type,error_message)
