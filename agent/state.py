"""Interview state — enums, dataclasses, and session serialization."""
from __future__ import annotations

import copy
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class InterviewPhase(str, Enum):
    GREETING = "GREETING"
    ROLE_SELECTION = "ROLE_SELECTION"
    CALIBRATION = "CALIBRATION"
    INTERVIEWING = "INTERVIEWING"
    WRAPPING_UP = "WRAPPING_UP"
    FEEDBACK = "FEEDBACK"
    END = "END"


@dataclass
class CandidateProfile:
    inferred_level: Optional[str] = None   # fresher / mid / senior
    detected_persona: Optional[str] = None  # confused / efficient / chatty / edge_case / normal
    role: Optional[str] = None              # sde / data_analyst / sales / retail / marketing
    resume_text: Optional[str] = None       # extracted text from uploaded PDF (truncated)


@dataclass
class QAPair:
    question: str
    answer: str
    topic: str
    quality: Optional[str] = None  # weak / medium / strong


@dataclass
class InterviewState:
    phase: InterviewPhase = InterviewPhase.GREETING
    candidate_profile: CandidateProfile = field(default_factory=CandidateProfile)
    messages: list[dict] = field(default_factory=list)   # {"role": "user"|"assistant", "content": str}
    qa_history: list[QAPair] = field(default_factory=list)
    question_count: int = 0
    current_difficulty: str = "easy"                      # easy / medium / hard
    planner_logs: list[dict] = field(default_factory=list)
    feedback_result: Optional[dict] = None
    summary_note: Optional[str] = None  # LLM-generated summary of pruned older messages

    # --- serialization helpers for st.session_state ---

    def to_dict(self) -> dict:
        return {
            "phase": self.phase.value,
            "candidate_profile": {
                "inferred_level": self.candidate_profile.inferred_level,
                "detected_persona": self.candidate_profile.detected_persona,
                "role": self.candidate_profile.role,
                "resume_text": self.candidate_profile.resume_text,
            },
            "messages": copy.deepcopy(self.messages),
            "qa_history": [
                {
                    "question": qa.question,
                    "answer": qa.answer,
                    "topic": qa.topic,
                    "quality": qa.quality,
                }
                for qa in self.qa_history
            ],
            "question_count": self.question_count,
            "current_difficulty": self.current_difficulty,
            "planner_logs": copy.deepcopy(self.planner_logs),
            "feedback_result": self.feedback_result,
            "summary_note": self.summary_note,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "InterviewState":
        profile_data = d["candidate_profile"]
        profile = CandidateProfile(
            inferred_level=profile_data.get("inferred_level"),
            detected_persona=profile_data.get("detected_persona"),
            role=profile_data.get("role"),
            resume_text=profile_data.get("resume_text"),
        )
        qa_history = [QAPair(**qa) for qa in d["qa_history"]]
        state = cls(
            phase=InterviewPhase(d["phase"]),
            candidate_profile=profile,
            messages=d["messages"],
            qa_history=qa_history,
            question_count=d["question_count"],
            current_difficulty=d.get("current_difficulty", "easy"),
            planner_logs=d["planner_logs"],
            feedback_result=d.get("feedback_result"),
            summary_note=d.get("summary_note"),
        )
        return state
