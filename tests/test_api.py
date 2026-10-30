from decimal import Decimal
from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from openai import APIConnectionError

from webhooks.app import app, get_extractor
from webhooks.models import ExtractedTransaction

client = TestClient(app)
PDF_BYTES = b"%PDF-1.7\nmock document"
VALID_TRANSACTION = ExtractedTransaction(
    vendor="Example Vendor",
    transaction_date=None,
    amount=Decimal("1250.50"),
    currency="MXN",
    transaction_id="SPEI-123",
    confidence=0.98,
)


class StubExtractor:
    async def extract(self, *, content: bytes, media_type: str, filename: str):
        assert content == PDF_BYTES
        assert media_type == "application/pdf"
        assert filename == "receipt.pdf"
        return VALID_TRANSACTION


@pytest.fixture(autouse=True)
def configure_webhook(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("WEBHOOK_TOKEN", "test-token")
    app.dependency_overrides[get_extractor] = lambda: StubExtractor()
    yield
    app.dependency_overrides.clear()


def test_health_endpoint() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_extracts_supported_pdf_with_bearer_token() -> None:
    response = client.post(
        "/webhooks/financial-document",
        headers={"Authorization": "Bearer test-token"},
        files={
            "file": (
                "C:\\receipts\\receipt.pdf",
                BytesIO(PDF_BYTES),
                "application/pdf",
            )
        },
    )

    assert response.status_code == 200
    assert response.json()["vendor"] == "Example Vendor"
    assert response.json()["amount"] == "1250.50"


def test_rejects_missing_or_invalid_token() -> None:
    response = client.post(
        "/webhooks/financial-document",
        files={"file": ("receipt.pdf", BytesIO(PDF_BYTES), "application/pdf")},
    )

    assert response.status_code == 401


def test_missing_webhook_configuration_is_reported(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("WEBHOOK_TOKEN")
    response = client.post(
        "/webhooks/financial-document",
        files={"file": ("receipt.pdf", BytesIO(PDF_BYTES), "application/pdf")},
    )

    assert response.status_code == 503


def test_missing_openai_configuration_is_reported(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    app.dependency_overrides.clear()
    response = client.post(
        "/webhooks/financial-document",
        headers={"Authorization": "Bearer test-token"},
        files={"file": ("receipt.pdf", BytesIO(PDF_BYTES), "application/pdf")},
    )

    assert response.status_code == 503
    app.dependency_overrides[get_extractor] = lambda: StubExtractor()


def test_rejects_unsupported_or_mismatched_file() -> None:
    response = client.post(
        "/webhooks/financial-document",
        headers={"Authorization": "Bearer test-token"},
        files={"file": ("receipt.pdf", BytesIO(b"not a pdf"), "application/pdf")},
    )

    assert response.status_code == 415


def test_rejects_empty_file() -> None:
    response = client.post(
        "/webhooks/financial-document",
        headers={"Authorization": "Bearer test-token"},
        files={"file": ("receipt.pdf", BytesIO(b""), "application/pdf")},
    )

    assert response.status_code == 400


def test_rejects_upload_over_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("webhooks.app.MAX_UPLOAD_BYTES", 8)
    response = client.post(
        "/webhooks/financial-document",
        headers={"Authorization": "Bearer test-token"},
        files={"file": ("receipt.pdf", BytesIO(PDF_BYTES), "application/pdf")},
    )

    assert response.status_code == 413


def test_provider_failures_are_reported(monkeypatch: pytest.MonkeyPatch) -> None:
    class FailedExtractor:
        async def extract(self, **kwargs):
            raise APIConnectionError(request=None)

    app.dependency_overrides[get_extractor] = lambda: FailedExtractor()
    response = client.post(
        "/webhooks/financial-document",
        headers={"Authorization": "Bearer test-token"},
        files={"file": ("receipt.pdf", BytesIO(PDF_BYTES), "application/pdf")},
    )

    assert response.status_code == 502
    assert response.json()["detail"] == "Document extraction provider request failed."
