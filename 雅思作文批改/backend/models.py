import enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TaskType(str, enum.Enum):
    """
    IELTS task types.
    """

    TASK_1 = "Task 1"
    TASK_2 = "Task 2"


class RecordStatus(str, enum.Enum):
    """
    Soft-delete status used by SQLite tables.
    """

    ACTIVE = "active"
    DELETED = "deleted"


class KaoyanExamType(str, enum.Enum):
    """
    Kaoyan exam type.
    """

    ENGLISH_I = "English I"
    ENGLISH_II = "English II"


class KaoyanPaperType(str, enum.Enum):
    """
    Kaoyan paper section type.
    """

    SMALL = "small_essay"
    LARGE = "large_essay"


class IELTSEssayRecord(BaseModel):
    """
    Logical model for a row in SQLite table: essays.
    """

    id: Optional[int] = None
    task_type: str
    topic: str
    user_content: str
    ai_analysis: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
    status: str = RecordStatus.ACTIVE.value


class KaoyanScore(BaseModel):
    """
    Kaoyan scoring schema returned by LLM.
    """

    exam_type: str
    paper_type: str
    total: float
    language_score: float
    structure_score: float
    logic_score: float


class KaoyanGrammarError(BaseModel):
    """
    Single grammar error item returned by LLM.
    """

    sentence: str
    error: str
    correction: str
    explanation: str


class KaoyanNineGridAlignment(BaseModel):
    """
    Nine-grid alignment details.
    """

    description_and_introduction: str
    analysis_and_expansion: str
    summary_and_suggestion: str


class KaoyanStructureAnalysis(BaseModel):
    """
    Structure analysis returned by LLM.
    """

    opening_paragraph: str
    body_paragraphs: str
    closing_paragraph: str
    nine_grid_alignment: KaoyanNineGridAlignment
    suggestions: List[str] = Field(default_factory=list)


class KaoyanAIAnalysis(BaseModel):
    """
    Full Kaoyan correction payload returned by LLM.
    """

    score: KaoyanScore
    grammar_errors: List[KaoyanGrammarError] = Field(default_factory=list)
    structure_analysis: KaoyanStructureAnalysis
    sample_essay: str


class KaoyanRecord(BaseModel):
    """
    Logical model for a row in SQLite table: kaoyan_records.
    """

    id: Optional[int] = None
    exam_type: str
    paper_type: str
    topic: str
    user_content: str
    total_score: Optional[float] = None
    language_score: Optional[float] = None
    structure_score: Optional[float] = None
    logic_score: Optional[float] = None
    ai_analysis: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
    status: str = RecordStatus.ACTIVE.value
