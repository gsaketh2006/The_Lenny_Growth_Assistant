import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.main import app
from backend.app.core.database import get_db


@pytest.mark.asyncio
async def test_auth_registration_and_login(test_db_session: AsyncSession):
    async def override_get_db():
        yield test_db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Register User
        reg_res = await ac.post("/api/auth/register", json={
            "email": "elena@plg.com",
            "password": "growthPassword123",
            "name": "Elena Verna"
        })
        assert reg_res.status_code == 200
        data = reg_res.json()
        assert "token" in data
        assert data["user"]["email"] == "elena@plg.com"
        assert data["user"]["name"] == "Elena Verna"
        token = data["token"]

        # 2. Duplicate Registration Rejection
        dup_res = await ac.post("/api/auth/register", json={
            "email": "elena@plg.com",
            "password": "otherPassword",
            "name": "Elena Impostor"
        })
        assert dup_res.status_code == 400

        # 3. Login with Correct Password
        login_res = await ac.post("/api/auth/login", json={
            "email": "elena@plg.com",
            "password": "growthPassword123"
        })
        assert login_res.status_code == 200
        assert "token" in login_res.json()

        # 4. Login with Incorrect Password
        bad_login = await ac.post("/api/auth/login", json={
            "email": "elena@plg.com",
            "password": "wrongPassword"
        })
        assert bad_login.status_code == 401

        # 5. Get Current User Profile with Token
        me_res = await ac.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me_res.status_code == 200
        assert me_res.json()["email"] == "elena@plg.com"

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_multi_user_session_isolation(test_db_session: AsyncSession):
    """Verifies that User A and User B cannot see or access each other's conversation sessions."""
    async def override_get_db():
        yield test_db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Register User A
        res_a = await ac.post("/api/auth/register", json={
            "email": "userA@growth.com",
            "password": "passwordA",
            "name": "User Alpha"
        })
        token_a = res_a.json()["token"]

        # Register User B
        res_b = await ac.post("/api/auth/register", json={
            "email": "userB@growth.com",
            "password": "passwordB",
            "name": "User Beta"
        })
        token_b = res_b.json()["token"]

        # User A creates a session
        sess_a_res = await ac.post(
            "/api/sessions",
            json={"title": "User A Private PLG Strategy"},
            headers={"Authorization": f"Bearer {token_a}"}
        )
        assert sess_a_res.status_code == 200
        sess_a_id = sess_a_res.json()["id"]

        # User B creates a session
        sess_b_res = await ac.post(
            "/api/sessions",
            json={"title": "User B Private Retention Plan"},
            headers={"Authorization": f"Bearer {token_b}"}
        )
        assert sess_b_res.status_code == 200
        sess_b_id = sess_b_res.json()["id"]

        # User A lists sessions -> sees ONLY Session A
        list_a = await ac.get("/api/sessions", headers={"Authorization": f"Bearer {token_a}"})
        assert list_a.status_code == 200
        a_sessions = list_a.json()
        assert len(a_sessions) == 1
        assert a_sessions[0]["id"] == sess_a_id
        assert a_sessions[0]["title"] == "User A Private PLG Strategy"

        # User B lists sessions -> sees ONLY Session B
        list_b = await ac.get("/api/sessions", headers={"Authorization": f"Bearer {token_b}"})
        assert list_b.status_code == 200
        b_sessions = list_b.json()
        assert len(b_sessions) == 1
        assert b_sessions[0]["id"] == sess_b_id
        assert b_sessions[0]["title"] == "User B Private Retention Plan"

        # User B attempts to access User A's session directly -> Forbidden (403)
        access_denied = await ac.get(f"/api/sessions/{sess_a_id}", headers={"Authorization": f"Bearer {token_b}"})
        assert access_denied.status_code == 403

    app.dependency_overrides.clear()
