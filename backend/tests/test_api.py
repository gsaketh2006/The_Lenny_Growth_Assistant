import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_health_endpoint(test_db_session: AsyncSession):
    async def override_get_db():
        yield test_db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "active_provider" in data
        assert "version" in data
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_providers_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Get providers
        res = await ac.get("/api/providers")
        assert res.status_code == 200
        providers = res.json()
        assert len(providers) >= 3
        provider_ids = [p["id"] for p in providers]
        assert "ollama" in provider_ids
        assert "anthropic" in provider_ids
        assert "openai" in provider_ids

        # Switch provider
        switch_res = await ac.post("/api/providers/select", json={"provider": "ollama", "model": "llama3.1:8b"})
        assert switch_res.status_code == 200
        assert switch_res.json()["active_provider"] == "ollama"


@pytest.mark.asyncio
async def test_sessions_crud(test_db_session: AsyncSession):
    async def override_get_db():
        yield test_db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Create session
        create_res = await ac.post("/api/sessions", json={"title": "Test Strategy Session"})
        assert create_res.status_code == 200
        sess = create_res.json()
        sess_id = sess["id"]
        assert sess["title"] == "Test Strategy Session"

        # List sessions
        list_res = await ac.get("/api/sessions")
        assert list_res.status_code == 200
        sessions = list_res.json()
        assert any(s["id"] == sess_id for s in sessions)

        # Get session
        get_res = await ac.get(f"/api/sessions/{sess_id}")
        assert get_res.status_code == 200
        assert get_res.json()["id"] == sess_id

        # Delete session
        del_res = await ac.delete(f"/api/sessions/{sess_id}")
        assert del_res.status_code == 200
        assert del_res.json()["status"] == "deleted"
    app.dependency_overrides.clear()
