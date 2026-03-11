from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.models.user import User
from app.services.code_review_service import review_code_submission

router = APIRouter(prefix="/api/code-review", tags=["code-review"])


class CodeReviewRequest(BaseModel):
    code: str


class CodeReviewResponse(BaseModel):
    is_code: bool
    message: str
    correctness: int
    style: int
    efficiency: int
    total_score: int
    issues: list[str]
    improvements: list[str]
    llm_feedback: str | None = None


@router.post("/score", response_model=CodeReviewResponse)
def score_code(payload: CodeReviewRequest, _: User = Depends(get_current_user)):
    result = review_code_submission(payload.code)
    return CodeReviewResponse(**result)
