from datetime import date as Date
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class ExtractedTransaction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    vendor: Annotated[str, Field(min_length=1, max_length=200)]
    transaction_date: Date | None
    amount: Decimal
    currency: Annotated[str, Field(pattern=r"^[A-Z]{3}$")]
    transaction_id: Annotated[str | None, Field(max_length=200)]
    confidence: Annotated[float, Field(ge=0, le=1)]


TRANSACTION_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "vendor": {"type": "string"},
        "transaction_date": {
            "anyOf": [{"type": "string", "format": "date"}, {"type": "null"}]
        },
        "amount": {"type": "number"},
        "currency": {"type": "string"},
        "transaction_id": {
            "anyOf": [{"type": "string"}, {"type": "null"}]
        },
        "confidence": {"type": "number"},
    },
    "required": [
        "vendor",
        "transaction_date",
        "amount",
        "currency",
        "transaction_id",
        "confidence",
    ],
    "additionalProperties": False,
}
