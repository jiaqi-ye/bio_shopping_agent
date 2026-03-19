from datetime import date
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class VendorBase(BaseModel):
    name: str
    lead_time_days: int = Field(ge=0)
    available_strains: Dict[str, int]
    price_per_mouse: float = Field(gt=0)


class VendorCreate(VendorBase):
    pass


class VendorUpdate(BaseModel):
    name: Optional[str] = None
    lead_time_days: Optional[int] = Field(default=None, ge=0)
    available_strains: Optional[Dict[str, int]] = None
    price_per_mouse: Optional[float] = Field(default=None, gt=0)


class VendorOut(VendorBase):
    id: int


class StrainBase(BaseModel):
    name: str
    equivalents: List[str] = []


class StrainCreate(StrainBase):
    pass


class StrainUpdate(BaseModel):
    name: Optional[str] = None
    equivalents: Optional[List[str]] = None


class StrainOut(StrainBase):
    id: int


class CageBase(BaseModel):
    total_cages: int = Field(ge=0)
    mice_per_cage: int = Field(ge=1)


class CageCreate(CageBase):
    pass


class CageUpdate(BaseModel):
    total_cages: Optional[int] = Field(default=None, ge=0)
    mice_per_cage: Optional[int] = Field(default=None, ge=1)


class CageOut(CageBase):
    id: int


class ProcureRequest(BaseModel):
    strain: str
    quantity: int = Field(gt=0)
    experiment_start_date: date
    approved_quota: int = Field(default=50, gt=0)


class AllocationItem(BaseModel):
    vendor_id: int
    vendor_name: str
    quantity: int
    unit_price: float
    lead_time_days: int
    shipping_cost: float


class ComplianceResult(BaseModel):
    ok: bool
    warning: Optional[str] = None


class CageCheckResult(BaseModel):
    ok: bool
    required_cages: int
    warning: Optional[str] = None


class ProcurementResponse(BaseModel):
    requested_strain: str
    quantity: int
    selected_vendors: List[str]
    allocation: List[AllocationItem]
    compliance: ComplianceResult
    cages: CageCheckResult
    latest_order_date: str
    rfq: Dict[str, Any]
    strain_recommendations: List[str] = []


class ProcurementHistoryOut(BaseModel):
    id: int
    strain: str
    quantity: int
    vendors: List[Dict[str, Any]]
    date: str
    compliance_ok: bool
    cages_ok: bool


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    user_id: Optional[str] = None


class SourceRef(BaseModel):
    source: str
    url: Optional[str] = None
    page: Optional[int] = None
    section: Optional[str] = None
    score: Optional[float] = None


class ChatResponse(BaseModel):
    mode: str
    message: str
    data: Optional[Dict[str, Any]] = None
    sources: Optional[List[SourceRef]] = None


class LoginRequest(BaseModel):
    username: str
    password: str
    shipping_address: str
    current_mouse_count: int
    cage_capacity: int
    user_id: Optional[str] = None


class ProfileOut(BaseModel):
    user_id: str
    username: str
    shipping_address: str
    current_mouse_count: int
    cage_capacity: int

