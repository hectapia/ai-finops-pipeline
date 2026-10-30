import hmac
import logging
import os
from functools import lru_cache
from pathlib import PurePath
from typing import Annotated

from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile, status
from openai import APIError
from pydantic import ValidationError

from webhooks.extraction import (
    ExtractionOutputError,
    OpenAIExtractor,
    TransactionExtractor,
)
from webhooks.models import ExtractedTransaction

logger = logging.getLogger(__name__)

MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", "10485760"))
if MAX_UPLOAD_BYTES <= 0:
    raise ValueError("MAX_UPLOAD_BYTES must be greater than zero.")
ALLOWED_FILES = {
    "application/pdf": (".pdf",),
    "image/jpeg": (".jpg", ".jpeg"),
    "image/png": (".png",),
    "image/webp": (".webp",),
}
SIGNATURES = {
    "application/pdf": lambda data: data.startswith(b"%PDF-"),
    "image/jpeg": lambda data: data.startswith(b"\xff\xd8\xff"),
    "image/png": lambda data: data.startswith(b"\x89PNG\r\n\x1a\n"),
    "image/webp": lambda data: (
        len(data) >= 12 and data.startswith(b"RIFF") and data[8:12] == b"WEBP"
    ),
}

app = FastAPI(title="FinOps document extraction API", version="0.1.0")


@lru_cache
def get_extractor() -> TransactionExtractor:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Document extraction is not configured: OPENAI_API_KEY is missing.",
        )
    return OpenAIExtractor(
        api_key=api_key,
        model=os.getenv("OPENAI_MODEL", "gpt-4o"),
    )


async def require_webhook_token(
    authorization: Annotated[str | None, Header()] = None,
) -> None:
    expected = os.getenv("WEBHOOK_TOKEN", "")
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Webhook authentication is not configured.",
        )
    scheme, separator, supplied = (authorization or "").partition(" ")
    if (
        not separator
        or scheme.lower() != "bearer"
        or not hmac.compare_digest(supplied.encode("utf-8"), expected.encode("utf-8"))
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )


def detect_media_type(content: bytes, filename: str) -> str:
    suffix = PurePath(filename).suffix.lower()
    for media_type, extensions in ALLOWED_FILES.items():
        if suffix in extensions and SIGNATURES[media_type](content):
            return media_type
    raise HTTPException(
        status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        detail="Upload must be a PDF, JPEG, PNG, or WebP file with a matching extension.",
    )


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post(
    "/webhooks/financial-document",
    response_model=ExtractedTransaction,
    dependencies=[Depends(require_webhook_token)],
)
async def extract_document(
    file: Annotated[UploadFile, File()],
    extractor: Annotated[TransactionExtractor, Depends(get_extractor)],
) -> ExtractedTransaction:
    content = await file.read(MAX_UPLOAD_BYTES + 1)
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds the {MAX_UPLOAD_BYTES}-byte upload limit.",
        )

    filename = PurePath((file.filename or "").replace("\\", "/")).name
    media_type = detect_media_type(content, filename)
    try:
        return await extractor.extract(
            content=content,
            media_type=media_type,
            filename=filename,
        )
    except APIError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Document extraction provider request failed.",
        ) from exc
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Document extraction provider returned invalid transaction data.",
        ) from exc
    except ExtractionOutputError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Document extraction provider returned invalid transaction data.",
        ) from exc
