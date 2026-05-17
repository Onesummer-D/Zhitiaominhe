from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class CaseCreate(BaseModel):
    title: str
    applicant: str
    respondent: str
    dispute_type: str
    custom_law_involved: bool = False
    description: str
    analysis_result: Optional[Dict[str, Any]] = None
    generated_documents: Optional[Dict[str, Any]] = None
    status: str = 'pending'
    region: Optional[str] = None
    ethnicity: Optional[str] = None

class CaseUpdate(BaseModel):
    title: Optional[str] = None
    applicant: Optional[str] = None
    respondent: Optional[str] = None
    dispute_type: Optional[str] = None
    custom_law_involved: Optional[bool] = None
    description: Optional[str] = None
    analysis_result: Optional[Dict[str, Any]] = None
    generated_documents: Optional[Dict[str, Any]] = None
    status: Optional[str] = None
    region: Optional[str] = None
    ethnicity: Optional[str] = None

class CaseOut(BaseModel):
    id: int
    case_no: str
    title: str
    applicant: str
    respondent: str
    dispute_type: str
    custom_law_involved: bool
    description: str
    analysis_result: Optional[Dict[str, Any]] = None
    generated_documents: Optional[Dict[str, Any]] = None
    status: str
    region: Optional[str] = None
    ethnicity: Optional[str] = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True

class StatsOut(BaseModel):
    pending: int
    today_new: int
    today_resolved: int

class KnowledgeItem(BaseModel):
    id: str
    name: str
    category: str
    content: str
    type: Optional[str] = None
