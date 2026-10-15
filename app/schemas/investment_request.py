from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class InvestmentRequest(BaseModel):
    amount: Decimal = Field(gt=0)
    horizon_months: int = Field(gt=0)
    product_types: list[Literal["bank_deposits", "treasury_bonds"]]
    payout_methods: list[Literal["at_end", "during_term"]]


class ProductEstimateRequest(BaseModel):
    amount: Decimal = Field(gt=0)
    variant_ids: list[int] = Field(min_length=1)
