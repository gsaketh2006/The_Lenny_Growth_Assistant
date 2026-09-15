import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.agent.providers import provider_registry, GenericOpenAICompatibleClient
from backend.app.models.schemas import CustomProviderCreate


@pytest.mark.asyncio
async def test_custom_provider_registration_and_deletion():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test/api") as client:
        # 1. Register custom Groq model
        groq_payload = {
            "name": "Groq Llama 3.3 Test",
            "api_type": "openai_compatible",
            "base_url": "https://api.groq.com/openai/v1",
            "model_name": "llama-3.3-70b-versatile",
            "api_key": "gsk_test123",
            "notes": "Testing custom provider registration"
        }
        res = await client.post("/providers/custom", json=groq_payload)
        assert res.status_code == 200
        created = res.json()
        assert "Groq Llama 3.3 Test" in created["name"]
        assert created["current_model"] == "llama-3.3-70b-versatile"
        provider_id = created["id"]

        # 2. Check that it appears in GET /providers
        providers_res = await client.get("/providers")
        assert providers_res.status_code == 200
        all_providers = providers_res.json()
        provider_ids = [p["id"] for p in all_providers]
        assert provider_id in provider_ids

        # 3. Select custom provider as active engine
        select_res = await client.post("/providers/select", json={
            "provider": provider_id,
            "model": "llama-3.3-70b-versatile"
        })
        assert select_res.status_code == 200
        assert select_res.json()["active_provider"] == provider_id

        # 4. Verify client resolved by provider_registry is GenericOpenAICompatibleClient
        cli = provider_registry.get_client(provider_id)
        assert isinstance(cli, GenericOpenAICompatibleClient)
        assert cli.model_name == "llama-3.3-70b-versatile"
        assert cli.base_url == "https://api.groq.com/openai/v1"
        assert cli.api_key == "gsk_test123"

        # 5. Delete custom provider
        del_res = await client.delete(f"/providers/custom/{provider_id}")
        assert del_res.status_code == 200

        # Verify it is removed
        providers_res_after = await client.get("/providers")
        assert provider_id not in [p["id"] for p in providers_res_after.json()]


@pytest.mark.asyncio
async def test_provider_test_connection_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test/api") as client:
        # Test against mock or local endpoint
        test_payload = {
            "api_type": "openai_compatible",
            "base_url": "http://127.0.0.1:99999/v1",
            "model_name": "test-model",
            "api_key": "test_key"
        }
        res = await client.post("/providers/test", json=test_payload)
        assert res.status_code == 200
        result = res.json()
        assert "success" in result
        assert "latency_ms" in result
        assert "message" in result
