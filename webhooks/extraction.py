import base64
import json
import logging
from typing import Protocol

from pydantic import ValidationError

from webhooks.models import ExtractedTransaction, TRANSACTION_JSON_SCHEMA

logger = logging.getLogger(__name__)


class ExtractionOutputError(Exception):
    pass


SYSTEM_PROMPT = (
    "Extract a single financial transaction from the supplied document. "
    "Do not infer missing values: use null for an unavailable date or transaction ID. "
    "Preserve the amount sign shown in the document and return the ISO 4217 currency code. "
    "Set confidence between 0 and 1 based on the legibility and completeness of the evidence."
)


class TransactionExtractor(Protocol):
    async def extract(
        self, *, content: bytes, media_type: str, filename: str
    ) -> ExtractedTransaction: ...


class OpenAIExtractor:
    def __init__(self, *, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model

    async def extract(
        self, *, content: bytes, media_type: str, filename: str
    ) -> ExtractedTransaction:
        from openai import APIError, AsyncOpenAI

        encoded_file = base64.b64encode(content).decode("ascii")
        if media_type.startswith("image/"):
            document = {
                "type": "input_image",
                "image_url": f"data:{media_type};base64,{encoded_file}",
            }
        else:
            document = {
                "type": "input_file",
                "filename": filename,
                "file_data": f"data:{media_type};base64,{encoded_file}",
            }

        client = AsyncOpenAI(api_key=self.api_key)
        try:
            response = await client.responses.create(
                model=self.model,
                input=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_text",
                                "text": "Extract the transaction fields from this document.",
                            },
                            document,
                        ],
                    },
                ],
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "financial_transaction",
                        "strict": True,
                        "schema": TRANSACTION_JSON_SCHEMA,
                    }
                },
            )
        except APIError:
            logger.exception("OpenAI extraction request failed")
            raise
        finally:
            await client.close()

        if not isinstance(response.output_text, str) or not response.output_text:
            raise ExtractionOutputError("OpenAI returned no transaction data")
        try:
            return ExtractedTransaction.model_validate_json(response.output_text)
        except (ValidationError, json.JSONDecodeError) as exc:
            logger.exception("OpenAI returned invalid transaction data")
            raise ExtractionOutputError(
                "OpenAI returned invalid transaction data"
            ) from exc
