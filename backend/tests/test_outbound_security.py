import httpx
import pytest

from app.connectors.outbound import OutboundSecurityError, OutboundUrlPolicy, SecureRedirectClient

PUBLIC = {"public.example": ["93.184.216.34"], "next.example": ["8.8.8.8"]}


def resolver(mapping):
    return lambda host: mapping.get(host, [])


@pytest.mark.asyncio
async def test_public_https_and_public_redirect_pass():
    def handler(request):
        if request.url.host == "public.example":
            return httpx.Response(
                302, headers={"location": "https://next.example/result"}, request=request
            )
        return httpx.Response(200, text="ok", request=request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        response = await SecureRedirectClient(client, OutboundUrlPolicy(resolver(PUBLIC))).get(
            "https://public.example/start"
        )
    assert response.status_code == 200
    assert response.url.host == "next.example"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "location,addresses",
    [
        ("https://localhost/x", {}),
        ("https://127.0.0.1/x", {}),
        ("https://[::1]/x", {}),
        ("https://private.example/x", {"private.example": ["10.0.0.1"]}),
        ("https://private.example/x", {"private.example": ["172.16.0.2"]}),
        ("https://private.example/x", {"private.example": ["192.168.1.2"]}),
        ("https://private.example/x", {"private.example": ["169.254.1.1"]}),
        ("https://private.example/x", {"private.example": ["fc00::1"]}),
        ("https://private.example/x", {"private.example": ["fe80::1"]}),
        ("https://service.local/x", {}),
        ("http://next.example/x", PUBLIC),
    ],
)
async def test_unsafe_redirects_rejected(location, addresses):
    mapping = {**PUBLIC, **addresses}

    def handler(request):
        return httpx.Response(302, headers={"location": location}, request=request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(OutboundSecurityError):
            await SecureRedirectClient(client, OutboundUrlPolicy(resolver(mapping))).get(
                "https://public.example/start"
            )


@pytest.mark.asyncio
async def test_mixed_public_private_dns_is_rejected():
    with pytest.raises(OutboundSecurityError):
        await OutboundUrlPolicy(resolver({"mixed.example": ["8.8.8.8", "10.0.0.1"]})).validate(
            "https://mixed.example/x"
        )


@pytest.mark.asyncio
async def test_redirect_limit_is_bounded():
    def handler(request):
        return httpx.Response(
            302, headers={"location": "https://public.example/again"}, request=request
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(OutboundSecurityError, match="redirect limit"):
            await SecureRedirectClient(
                client, OutboundUrlPolicy(resolver(PUBLIC)), max_redirects=2
            ).get("https://public.example/start")
