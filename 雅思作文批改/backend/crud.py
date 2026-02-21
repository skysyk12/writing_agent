import sqlite3
import json
from datetime import datetime
from typing import List, Optional

# Since we removed SQLAlchemy models, we define simple classes or dicts if needed, 
# but for now we will just use the Row objects or dicts.

class EssayStatus:
    ACTIVE = "active"
    DELETED = "deleted"

def create_essay(conn: sqlite3.Connection, topic: str, user_content: str, task_type: str, ai_analysis: dict) -> int:
    """
    Creates a new essay and returns its ID.
    """
    cursor = conn.cursor()
    created_at = datetime.utcnow().isoformat()
    ai_analysis_json = json.dumps(ai_analysis)
    
    cursor.execute('''
        INSERT INTO essays (topic, user_content, task_type, ai_analysis, created_at, status)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (topic, user_content, task_type, ai_analysis_json, created_at, EssayStatus.ACTIVE))
    
    conn.commit()
    return cursor.lastrowid

def get_essay(conn: sqlite3.Connection, essay_id: int) -> Optional[dict]:
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM essays WHERE id = ?', (essay_id,))
    row = cursor.fetchone()
    if row:
        return dict(row)
    return None

def get_active_essays(conn: sqlite3.Connection) -> List[dict]:
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM essays 
        WHERE status = ? 
        ORDER BY created_at DESC
    ''', (EssayStatus.ACTIVE,))
    rows = cursor.fetchall()
    return [dict(row) for row in rows]

def delete_essay(conn: sqlite3.Connection, essay_id: int, soft_delete: bool = True):
    cursor = conn.cursor()
    if soft_delete:
        cursor.execute('UPDATE essays SET status = ? WHERE id = ?', (EssayStatus.DELETED, essay_id))
    else:
        cursor.execute('DELETE FROM essays WHERE id = ?', (essay_id,))
    conn.commit()

def get_trajectory_data(conn: sqlite3.Connection) -> List[dict]:
    """
    Extracts relevant data for trajectory analysis.
    """
    essays = get_active_essays(conn)
    essays.reverse()

    history_data = []
    for idx, essay in enumerate(essays, start=1):
        ai_analysis_str = essay.get("ai_analysis")
        if ai_analysis_str:
            try:
                analysis = json.loads(ai_analysis_str)
                scores = analysis.get("scores", {})
                feedback = analysis.get("feedback", {})
                
                history_data.append({
                    "id": essay["id"],
                    "index": idx,
                    "created_at": essay["created_at"],
                    "topic": essay["topic"],
                    "task_type": essay.get("task_type"),
                    "scores": scores,
                    "weaknesses": feedback.get("weaknesses", [])
                })
            except json.JSONDecodeError:
                continue
                
    return history_data


def get_kaoyan_trajectory_data(conn: sqlite3.Connection) -> List[dict]:
    records = get_active_kaoyan_records(conn)
    records.reverse()

    history_data = []
    for idx, record in enumerate(records, start=1):
        ai_analysis_str = record.get("ai_analysis")
        if not ai_analysis_str:
            continue
        try:
            analysis = json.loads(ai_analysis_str)
        except json.JSONDecodeError:
            continue

        score = analysis.get("score", {}) if isinstance(analysis, dict) else {}
        total_score = score.get("total_score", record.get("total_score"))
        history_data.append(
            {
                "id": record["id"],
                "index": idx,
                "created_at": record.get("created_at"),
                "topic": record.get("topic"),
                "exam_type": record.get("exam_type"),
                "paper_type": record.get("paper_type"),
                "total_score": total_score,
                "band": score.get("band"),
                "evaluation_summary": score.get("evaluation_summary", ""),
            }
        )

    return history_data

def create_kaoyan_record(
    conn: sqlite3.Connection,
    exam_type: str,
    paper_type: str,
    topic: str,
    user_content: str,
    ai_analysis: dict,
) -> int:
    """
    Creates a new Kaoyan record and returns its ID.
    """
    cursor = conn.cursor()
    created_at = datetime.utcnow().isoformat()

    total_score = None
    language_score = None
    structure_score = None
    logic_score = None

    try:
        score = (ai_analysis or {}).get("score", {}) if isinstance(ai_analysis, dict) else {}
        if score.get("total") is not None or score.get("language_score") is not None:
            total_score = float(score.get("total")) if score.get("total") is not None else None
            language_score = float(score.get("language_score")) if score.get("language_score") is not None else None
            structure_score = float(score.get("structure_score")) if score.get("structure_score") is not None else None
            logic_score = float(score.get("logic_score")) if score.get("logic_score") is not None else None
        else:
            if score.get("total_score") is not None:
                total_score = float(score.get("total_score"))
    except Exception:
        total_score = None
        language_score = None
        structure_score = None
        logic_score = None

    ai_analysis_json = json.dumps(ai_analysis, ensure_ascii=False)

    cursor.execute(
        '''
        INSERT INTO kaoyan_records (
            exam_type, paper_type, topic, user_content,
            total_score, language_score, structure_score, logic_score,
            ai_analysis, created_at, status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''',
        (
            exam_type,
            paper_type,
            topic,
            user_content,
            total_score,
            language_score,
            structure_score,
            logic_score,
            ai_analysis_json,
            created_at,
            EssayStatus.ACTIVE,
        ),
    )

    conn.commit()
    return cursor.lastrowid


def get_kaoyan_record(conn: sqlite3.Connection, record_id: int) -> Optional[dict]:
    """
    Fetch a single Kaoyan record by id.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM kaoyan_records WHERE id = ?", (record_id,))
    row = cursor.fetchone()
    if row:
        return dict(row)
    return None


def get_active_kaoyan_records(conn: sqlite3.Connection) -> List[dict]:
    """
    List active Kaoyan records, newest first.
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT * FROM kaoyan_records
        WHERE status = ?
        ORDER BY created_at DESC
        """,
        (EssayStatus.ACTIVE,),
    )
    rows = cursor.fetchall()
    return [dict(row) for row in rows]


def delete_kaoyan_record(conn: sqlite3.Connection, record_id: int, soft_delete: bool = True):
    """
    Delete a Kaoyan record.
    """
    cursor = conn.cursor()
    if soft_delete:
        cursor.execute("UPDATE kaoyan_records SET status = ? WHERE id = ?", (EssayStatus.DELETED, record_id))
    else:
        cursor.execute("DELETE FROM kaoyan_records WHERE id = ?", (record_id,))
    conn.commit()
