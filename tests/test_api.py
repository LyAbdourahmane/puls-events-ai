from fastapi.testclient import TestClient
import os
from unittest.mock import patch
from dotenv import load_dotenv
from app import app

load_dotenv()

API_KEY_ADMIN = os.getenv('API_KEY_ADMIN')

client = TestClient(app)


def test_read_main_root():
    """Nous allons tester les différentes routes"""
    response = client.get('/')
    assert response.status_code == 200
    assert response.json() == {
        "message": "API de recommandation culturelle basée sur RAG (Mistral + OpenAgenda)",
        "endpoints": ["/chat", "/rebuild"]
    }


def test_with_real_key():
    # --- Test /chat ---
    query = "Des événements religieux sur Paris"
    data_chat = {
        "question": query,
        "model_size": "small"
    }

    response_chat = client.post("/chat", json=data_chat,
                                headers={"X-API-Key": API_KEY_ADMIN})
    assert response_chat.status_code == 200
    json_chat = response_chat.json()
    assert 'answer' in json_chat
    assert 'sources' in json_chat
    assert isinstance(json_chat['answer'], str)
    assert isinstance(json_chat['sources'], str)

    response_rebuild = client.post("/rebuild", headers={"X-API-Key": API_KEY_ADMIN})
    assert response_rebuild.status_code == 200
    assert response_rebuild.json() == {
        "info": "Le Système RAG a été rechargé avec succès !"
    }


def test_error_pydantic():
    # -- Test /chat --
    query = 25
    data_chat = {
        "question": query,
        "model_size": 65
    }
    response_chat = client.post("/chat", json=data_chat,
                                        headers={"X-API-Key": API_KEY_ADMIN})
    assert response_chat.status_code == 422

    response_rebuild = client.post("/rebuild", headers= {"X-API-Key": API_KEY_ADMIN})
    assert response_rebuild.status_code == 422


def test_chat_internal_error():
    # Test 500
    data = {'question': 'test', 'model_size': 'small'}
    with patch("app.rag_response", side_effect=Exception('boom')):
        response = client.post('/chat', json=data, headers = {"X-API-Key": API_KEY_ADMIN})
        assert response.status_code == 500

    # Test 503
    with patch("app.rag_response", return_value=(None, None)):
        response = client.post("/chat", json=data, headers={"X-API-Key": API_KEY_ADMIN})
        assert response.status_code == 503


def test_with_fake_key():
    # Avec une mauvaise api key
    response = client.post("/chat", json={"question": "test", "model_size": "small"}, 
                                    headers={"X-API-Key": "wrong"}) 
    assert response.status_code == 401

    #sans api key
    response = client.post("/chat", json={"question": "test", "model_size": "small"}) 
    assert response.status_code == 401
