import os
import json
import traceback
from typing import Any, Dict, Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

if not os.getenv("DEEPSEEK_API_KEY"):
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip() and not line.startswith("#"):
                    key, value = line.strip().split("=", 1)
                    os.environ[key.strip()] = value.strip()

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


class DeepSeekService:
    """
    OpenAI-compatible client wrapper for DeepSeek API, designed for Kaoyan writing correction.
    """

    def __init__(self, model_name: str = "deepseek-chat"):
        """
        Initialize DeepSeek service.

        :param model_name: DeepSeek model name, defaults to "deepseek-chat".
        """
        self.model_name = model_name
        self.base_url = "https://api.deepseek.com"

    def _get_client(self) -> Optional["OpenAI"]:
        """
        Create an OpenAI-compatible client for DeepSeek.

        :return: OpenAI client instance if available, otherwise None.
        """
        if OpenAI is None:
            print("ERROR: openai package is not installed. Please `pip install openai`.")
            return None

        if not DEEPSEEK_API_KEY:
            print("ERROR: DEEPSEEK_API_KEY is not configured in environment.")
            return None

        try:
            return OpenAI(api_key=DEEPSEEK_API_KEY, base_url=self.base_url)
        except Exception as exc:
            print(f"ERROR: Failed to initialize DeepSeek client: {exc}")
            traceback.print_exc()
            return None

    def correct_kaoyan_essay(
        self,
        exam_type: str,
        paper_type: str,
        topic: str,
        content: str,
    ) -> Dict[str, Any]:
        """
        Correct a Kaoyan English essay and return strict JSON result.

        :param exam_type: English I / English II (or Chinese inputs containing 一/二).
        :param paper_type: small_essay / large_essay (or Chinese inputs containing 小/大).
        :param topic: Writing prompt / topic.
        :param content: Student essay text.
        :return: Parsed JSON dict, or {"error": "..."} with optional raw_text.
        """
        client = self._get_client()
        if client is None:
            return {"error": "DeepSeek client is not available. Check openai installation and DEEPSEEK_API_KEY."}

        normalized_exam_type = self._normalize_exam_type(exam_type)
        normalized_paper_type = self._normalize_paper_type(paper_type)
        max_score = self._get_max_score(normalized_exam_type, normalized_paper_type)

        paper_type_cn = "英语一" if normalized_exam_type == "English I" else "英语二"
        section_label = "A节" if normalized_paper_type == "small_essay" else "B节"
        word_count = len(content.split()) if content else 0

        system_prompt = self._build_system_prompt(
            exam_type=normalized_exam_type,
            paper_type=normalized_paper_type,
            max_score=max_score,
        )

        user_prompt = (
            f"paper_type: {paper_type_cn}\n"
            f"section: {section_label}\n"
            f"estimated_word_count: {word_count}\n"
            f"topic: {topic}\n"
            f"student_essay:\n{content}\n"
        )

        try:
            response = client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
            )
        except Exception as exc:
            print(f"ERROR: DeepSeek API call failed: {exc}")
            traceback.print_exc()
            return {"error": f"DeepSeek API Error: {exc}"}

        try:
            message = response.choices[0].message
            content_field = message.content
            if isinstance(content_field, str):
                text = content_field
            elif isinstance(content_field, list):
                text = "".join(
                    part.get("text", "") if isinstance(part, dict) else str(part)
                    for part in content_field
                )
            else:
                text = str(content_field)
        except Exception as exc:
            print(f"ERROR: Unexpected DeepSeek response structure: {exc}")
            traceback.print_exc()
            return {"error": f"Unexpected DeepSeek response structure: {exc}"}

        if not text:
            return {"error": "DeepSeek returned empty response."}

        return self._parse_response(text)

    def correct_ielts_essay(
        self,
        topic: str,
        content: str,
        task_type: str,
    ) -> Dict[str, Any]:
        client = self._get_client()
        if client is None:
            return {"error": "DeepSeek client is not available. Check openai installation and DEEPSEEK_API_KEY."}

        system_prompt = """
You are an expert IELTS Writing Examiner, strictly following the public band descriptors and the evaluation style of Simon (ielts-simon.com).
You must provide clear, actionable feedback to help the student improve.

Output must be pure JSON (no markdown, no comments) with the following structure:
{
  "scores": {
    "TR": <float 0-9>,
    "CC": <float 0-9>,
    "LR": <float 0-9>,
    "GRA": <float 0-9>,
    "overall": <float 0-9>
  },
  "feedback": {
    "strengths": ["point 1", "point 2"],
    "weaknesses": ["point 1", "point 2"],
    "logic_check": "Check whether body paragraphs follow an Idea-Explain-Example structure. Be specific.",
    "detailed_comments": "Detailed paragraph-by-paragraph feedback in Markdown-ready plain text."
  },
  "improvements": [
    "specific actionable suggestion 1",
    "suggestion 2"
  ],
  "vocabulary": {
    "good_collocations_used": ["phrases actually used well in the essay"],
    "recommended_collocations": ["better alternatives or higher-level phrases based on the student's wording"],
    "advanced_structures": ["complex grammatical structures found or recommended"]
  },
  "band_9_sample": "A full Band 9 sample answer for this topic, written in a clear and natural style."
}

Return only valid JSON.
        """.strip()

        user_prompt = f"""
Task Type: {task_type}
Topic: {topic}
Student Essay:
{content}
        """.strip()

        try:
            response = client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
            )
        except Exception as exc:
            print(f"ERROR: DeepSeek API call failed: {exc}")
            traceback.print_exc()
            return {"error": f"DeepSeek API Error: {exc}"}

        try:
            message = response.choices[0].message
            content_field = message.content
            if isinstance(content_field, str):
                text = content_field
            elif isinstance(content_field, list):
                text = "".join(
                    part.get("text", "") if isinstance(part, dict) else str(part)
                    for part in content_field
                )
            else:
                text = str(content_field)
        except Exception as exc:
            print(f"ERROR: Unexpected DeepSeek response structure: {exc}")
            traceback.print_exc()
            return {"error": f"Unexpected DeepSeek response structure: {exc}"}

        if not text:
            return {"error": "DeepSeek returned empty response."}

        return self._parse_response(text)

    def analyze_trajectory(self, history_data: list) -> Dict[str, Any]:
        client = self._get_client()
        if client is None:
            return {"error": "DeepSeek client is not available. Check openai installation and DEEPSEEK_API_KEY."}

        history_summary = []
        for entry in history_data:
            summary = {
                "index": entry.get("index"),
                "date": entry.get("created_at"),
                "task_type": entry.get("task_type"),
                "topic": entry.get("topic"),
                "scores": entry.get("scores"),
                "weaknesses": entry.get("weaknesses"),
            }
            history_summary.append(summary)

        history_str = json.dumps(history_summary, ensure_ascii=False, indent=2)

        system_prompt = """
You are an IELTS Writing Coach. Analyze the student's essay history to identify growth trends, persistent weaknesses, and create a focused learning plan.
The history may contain both Task 1 and Task 2 essays. When describing trends, explicitly discuss any differences between Task 1 and Task 2 performance.

You must output pure JSON with:
{
  "persistent_weaknesses": ["weakness 1", "weakness 2"],
  "progress_analysis": "Describe how scores (Overall, TR, CC, LR, GRA) have changed across submissions, mentioning Task 1 vs Task 2 differences when relevant.",
  "learning_plan": {
    "focus_areas": ["area 1", "area 2"],
    "suggested_exercises": ["exercise 1", "exercise 2"]
  },
  "trend_summary": "2-3 sentence Chinese summary for a dashboard."
}
        """.strip()

        user_prompt = f"Student IELTS history (ordered by submission, including task_type):\n{history_str}"

        try:
            response = client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
            )
        except Exception as exc:
            traceback.print_exc()
            return {"error": f"DeepSeek API Error: {exc}"}

        try:
            message = response.choices[0].message
            content_field = message.content
            if isinstance(content_field, str):
                text = content_field
            elif isinstance(content_field, list):
                text = "".join(
                    part.get("text", "") if isinstance(part, dict) else str(part)
                    for part in content_field
                )
            else:
                text = str(content_field)
        except Exception as exc:
            traceback.print_exc()
            return {"error": f"Unexpected DeepSeek response structure: {exc}"}

        if not text:
            return {"error": "DeepSeek returned empty response."}

        return self._parse_response(text)

    def analyze_kaoyan_trajectory(self, history_data: list) -> Dict[str, Any]:
        client = self._get_client()
        if client is None:
            return {"error": "DeepSeek client is not available. Check openai installation and DEEPSEEK_API_KEY."}

        history_summary = []
        for entry in history_data:
            summary = {
                "index": entry.get("index"),
                "date": entry.get("created_at"),
                "exam_type": entry.get("exam_type"),
                "paper_type": entry.get("paper_type"),
                "topic": entry.get("topic"),
                "total_score": entry.get("total_score"),
                "band": entry.get("band"),
                "evaluation_summary": entry.get("evaluation_summary"),
            }
            history_summary.append(summary)

        history_str = json.dumps(history_summary, ensure_ascii=False, indent=2)

        system_prompt = """
You are a Kaoyan English writing coach. Analyze the student's essay history scored with a five-band rubric.
Pay special attention to differences between English I vs English II and between large vs small essays. If the student is weaker in a particular exam type or essay type, highlight this clearly.

Output pure JSON:
{
  "persistent_weaknesses": ["weakness 1", "weakness 2"],
  "progress_analysis": "Describe how total scores and bands change across submissions and what this means, explicitly mentioning any differences between exam types (English I/II) and essay types (large/small).",
  "learning_plan": {
    "focus_areas": ["area 1", "area 2"],
    "suggested_exercises": ["exercise 1", "exercise 2"]
  },
  "trend_summary": "2-3 sentence Chinese summary for a dashboard."
}
        """.strip()

        user_prompt = f"Student Kaoyan history (ordered by submission, including exam_type and paper_type):\n{history_str}"

        try:
            response = client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
            )
        except Exception as exc:
            traceback.print_exc()
            return {"error": f"DeepSeek API Error: {exc}"}

        try:
            message = response.choices[0].message
            content_field = message.content
            if isinstance(content_field, str):
                text = content_field
            elif isinstance(content_field, list):
                text = "".join(
                    part.get("text", "") if isinstance(part, dict) else str(part)
                    for part in content_field
                )
            else:
                text = str(content_field)
        except Exception as exc:
            traceback.print_exc()
            return {"error": f"Unexpected DeepSeek response structure: {exc}"}

        if not text:
            return {"error": "DeepSeek returned empty response."}

        return self._parse_response(text)

    def _normalize_exam_type(self, exam_type: str) -> str:
        """
        Normalize exam type to "English I" or "English II".
        """
        value = (exam_type or "").strip().lower()
        if "一" in value or "1" in value:
            return "English I"
        if "二" in value or "2" in value:
            return "English II"
        if "english ii" in value:
            return "English II"
        return "English I"

    def _normalize_paper_type(self, paper_type: str) -> str:
        """
        Normalize paper type to "small_essay" or "large_essay".
        """
        value = (paper_type or "").strip().lower()
        if "small" in value or "小" in value:
            return "small_essay"
        if "large" in value or "大" in value:
            return "large_essay"
        return "large_essay"

    def _get_max_score(self, exam_type: str, paper_type: str) -> int:
        """
        Determine maximum score for a single essay.

        English I: total 30 = small 10 + large 20
        English II: total 25 = small 10 + large 15
        """
        if exam_type == "English I":
            return 10 if paper_type == "small_essay" else 20
        if exam_type == "English II":
            return 10 if paper_type == "small_essay" else 15
        return 20

    def _build_system_prompt(self, exam_type: str, paper_type: str, max_score: int) -> str:
        return f"""
You are a strict and professional Chinese Kaoyan (postgraduate entrance exam) English writing examiner.
You must follow the official syllabus and the five-band holistic scoring method (通篇分档计分法).

Current essay configuration:
- Exam type (paper_type): {"英语一" if exam_type == "English I" else "英语二"}
- Section: {"A节（小作文）" if paper_type == "small_essay" else "B节（大作文）"}
- Maximum score for this essay: {max_score}

Scoring rubric (five bands):
1) 第五档（极佳）
   - A节: 9-10分；英一B节: 17-20分；英二B节: 13-15分
   - 要点齐全，语言丰富自然，基本无错，衔接自然，格式语域恰当。
2) 第四档（良好）
   - A节: 7-8分；英一B节: 13-16分；英二B节: 10-12分
   - 要点基本齐全（允许漏1-2个次要信息），语法词汇较丰富，仅在复杂结构上有个别错误，层次清晰。
3) 第三档（及格）
   - A节: 5-6分；英一B节: 9-12分；英二B节: 7-9分
   - 遗漏部分内容但涵盖大多数要点，语法词汇能满足基本表达，有错误但不影响大意，衔接较简单。
4) 第二档（较差）
   - A节: 3-4分；英一B节: 5-8分；英二B节: 4-6分
   - 要点覆盖不全或有无关内容，语法单调词汇有限，错误较多影响理解，缺乏连贯性。
5) 第一档（极差）
   - A节: 1-2分；英一B节: 1-4分；英二B节: 1-3分
   - 严重跑题或大量要点缺失，错误极多妨碍理解，几乎没有组织。
6) 0分档
   - 完全跑题或内容无法辨认。

Penalty rules:
- For Section A (小作文), if word count < 100, deduct 1-2 points within the chosen band.
- For Section B of English I, if word count < 160, for every 10 words missing deduct about 1-1.5 points.
- For Section B of English II, if word count < 150, for every 10 words missing deduct about 1-1.5 points.
- If the student copies large chunks of the prompt or topic sentences directly, reduce the band appropriately.

Evaluation steps:
1) 内容审核（Content）
   - Check whether the essay answers the task, covers key points (purpose, picture/chart details, trend description, reason analysis, personal stance, etc.).
2) 语言审核（Language）
   - Check spelling, grammar (tenses, subject-verb agreement, clauses), vocabulary variety, and use of高级句型.
3) 连贯与格式（Coherence & Format）
   - Check paragraphing, logical connectors, coherence, and for Section A, whether letter/report format and register are appropriate.
4) 定档定分（Grading）
   - First decide which band (第一档–第五档或0分档) the essay belongs to.
   - Then choose a specific score within that band according to performance and penalties.

Output format:
You MUST return ONLY pure JSON text (no markdown, no comments, no extra explanations).
The JSON structure must be:

{{
  "score": {{
    "total_score": <int or float, 0-{max_score}>,
    "band": "第一档/第二档/第三档/第四档/第五档/0分档",
    "evaluation_summary": "一两句话给出整体总评，用中文简要概括"
  }},
  "dimension_analysis": {{
    "content_relevance": "指出涵盖了哪些要点，遗漏或跑题的部分，是否符合题目要求",
    "language_accuracy": "评价词汇和语法的多样性与准确性，指出高级结构使用情况",
    "coherence_format": "评价段落结构、衔接词使用以及应用文格式/大作文布局是否得当"
  }},
  "grammar_and_vocab_errors": [
    {{
      "original_sentence": "原文中存在问题的句子",
      "error_type": "语法错误/拼写错误/中式英语/用词不当等",
      "correction": "修改后的正确句子",
      "explanation": "用中文简要解释错误原因，帮助学生理解和记忆"
    }}
  ],
  "vocabulary": {{
    "good_collocations_used": ["学生原文中使用得比较好的搭配或表达"],
    "recommended_collocations": ["基于学生原句，给出的更高级或更地道的替代表达"],
    "advanced_structures": ["已经使用或建议使用的高级句型，如定语从句、倒装、强调句等"]
  }},
  "improved_version": "在保留学生原有内容和观点前提下，用更高级的词汇、更加地道的搭配和多样的句型，重写一篇符合第五档标准的完整范文。注意整体逻辑清晰、衔接自然，符合考研英语写作风格。"
}}

Return only valid JSON.
        """.strip()

    def _parse_response(self, text: str) -> Dict[str, Any]:
        """
        Parse JSON from model output, tolerating accidental code fences.
        """
        raw = text.strip()
        if raw.startswith("```"):
            lines = raw.split("\n")
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            raw = "\n".join(lines)

        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            start = raw.find("{")
            end = raw.rfind("}")
            if start != -1 and end != -1:
                try:
                    return json.loads(raw[start : end + 1])
                except Exception:
                    pass
            return {"error": "Failed to parse JSON response from DeepSeek", "raw_text": raw}
