import google.generativeai as genai
import os
import json

# Try loading from python-dotenv, otherwise manual load
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Manual fallback for reading .env if os.getenv fails
if not os.getenv("GOOGLE_API_KEY"):
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key.strip()] = value.strip()

# Set up API Key from environment variable
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Auto-configure proxy if not set, trying common ports
# You can remove this if you have system-wide proxy set up correctly
if not os.getenv("HTTPS_PROXY") and not os.getenv("https_proxy"):
    # Try common proxy ports
    import socket
    def check_port(port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('127.0.0.1', port)) == 0

    # Common ports: 7890 (Clash), 1080 (Socks), 1087 (V2Ray), 33210 (ClashX Pro)
    for port in [7890, 1087, 33210, 1080]:
        if check_port(port):
            print(f"DEBUG: Detected local proxy at port {port}, configuring environment...")
            proxy_url = f"http://127.0.0.1:{port}"
            os.environ["HTTP_PROXY"] = proxy_url
            os.environ["HTTPS_PROXY"] = proxy_url
            break

if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

class GeminiService:
    def __init__(self):
        # Default models mapping - user specified 2.5 versions
        self.models = {
            "flash": "gemini-2.5-flash",
            "pro": "gemini-2.5-pro"
        }

    def get_model(self, model_selection="pro"):
        model_name = self.models.get(model_selection.lower(), "gemini-2.5-pro")
        # Fallback configuration or error handling could go here
        return genai.GenerativeModel(model_name)

    def correct_essay(self, topic: str, content: str, task_type: str, model_selection: str = "pro") -> dict:
        """
        Sends the essay to Gemini for correction based on Simon's criteria.
        """
        print(f"DEBUG: Starting correction with model {model_selection}")
        try:
            model = self.get_model(model_selection)
            print(f"DEBUG: Model loaded: {model.model_name}")
            
            prompt = f"""
            You are an expert IELTS Writing Examiner, strictly following the evaluation criteria and style of Simon (ielts-simon.com).
            
            Task Type: {task_type}
            Topic: {topic}
            Student Essay:
            {content}
            
            Please evaluate this essay and provide the output in strict JSON format with the following structure. Do not include any markdown formatting outside the JSON.
            {{
                "scores": {{
                    "TR": <score 0-9, float>,
                    "CC": <score 0-9, float>,
                    "LR": <score 0-9, float>,
                    "GRA": <score 0-9, float>,
                    "overall": <average score, float>
                }},
                "feedback": {{
                    "strengths": ["point 1", "point 2"],
                    "weaknesses": ["point 1", "point 2"],
                    "logic_check": "Analyze if the 'Idea-Explain-Example' structure is followed in body paragraphs. Be specific.",
                    "detailed_comments": " comprehensive feedback in Markdown format."
                }},
                "improvements": ["specific actionable suggestion 1", "suggestion 2"],
                "vocabulary": {{
                    "good_collocations_used": ["list of good phrases found"],
                    "recommended_collocations": ["list of better alternatives or additions"],
                    "advanced_structures": ["list of complex sentence structures found or suggested"]
                }},
                "band_9_sample": "A full Band 9 sample answer for this topic, written in Simon's clear, coherent style."
            }}
            
            Evaluation Criteria:
            1. Task Response (TR): Address all parts of the task. Clear position throughout.
            2. Coherence & Cohesion (CC): Logical paragraphing. 'Idea-Explain-Example' structure. Natural linking.
            3. Lexical Resource (LR): Precise vocabulary, correct collocations, avoiding forced 'big words'.
            4. Grammatical Range & Accuracy (GRA): Mix of simple and complex sentences. Error-free sentences.
            """
            
            print("DEBUG: Sending request to Gemini API...")
            # Using generation_config to encourage JSON output if supported, 
            # but strictly prompting for JSON text is often enough.
            response = model.generate_content(prompt)
            print("DEBUG: Response received from Gemini API")
            
            if not response.text:
                print("DEBUG: Empty response text")
                return {"error": "Gemini returned empty response."}
                
            print(f"DEBUG: Response text preview: {response.text[:100]}...")
            return self._parse_response(response.text)
        except Exception as e:
            print(f"ERROR: Gemini API Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"error": f"Gemini API Error: {str(e)}"}

    def correct_kaoyan_essay(
        self,
        exam_type: str,
        paper_type: str,
        topic: str,
        content: str,
        model_selection: str = "pro",
    ) -> dict:
        """
        Sends a Kaoyan essay to Gemini for correction with Pan Yun nine-grid framework.
        """
        try:
            normalized_exam_type = self._normalize_exam_type(exam_type)
            normalized_paper_type = self._normalize_paper_type(paper_type)
            max_score = self._get_max_score(normalized_exam_type, normalized_paper_type)

            model = self.get_model(model_selection)

            paper_type_cn = "英语一" if normalized_exam_type == "English I" else "英语二"
            section_label = "A节" if normalized_paper_type == "small_essay" else "B节"
            word_count = len(content.split()) if content else 0

            prompt = f"""
You are a strict and professional Chinese Kaoyan (postgraduate entrance exam) English writing examiner.
You must follow the official syllabus and the five-band holistic scoring method (通篇分档计分法).

Input information:
- paper_type: {paper_type_cn}
- section: {section_label}
- estimated_word_count: {word_count}
- topic: {topic}

Student_essay:
{content}

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
- A节（小作文）字数少于100词时，在所属档次内扣1-2分。
- 英一B节若少于160词，每少约10词在所属档次内扣1-1.5分。
- 英二B节若少于150词，每少约10词在所属档次内扣1-1.5分。
- 大量照抄题目中的提示词组或整句时，应适当下调档次。

Evaluation steps:
1) 内容审核（Content）
2) 语言审核（Language）
3) 连贯与格式（Coherence & Format）
4) 先定档，再在档内给出具体分数，最高不超过 {max_score} 分。

You must output ONLY JSON (no markdown, no extra explanations) with the structure:
{{
  "score": {{
    "total_score": <int or float, 0-{max_score}>,
    "band": "第一档/第二档/第三档/第四档/第五档/0分档",
    "evaluation_summary": "一两句话中文总评"
  }},
  "dimension_analysis": {{
    "content_relevance": "说明涵盖了哪些要点，哪些要点缺失或跑题",
    "language_accuracy": "评估词汇和语法的多样性及准确性，指出典型问题",
    "coherence_format": "评估段落结构、衔接词、逻辑以及应用文格式是否规范"
  }},
  "grammar_and_vocab_errors": [
    {{
      "original_sentence": "原文错句或问题句",
      "error_type": "语法错误/拼写错误/中式英语/用词不当等",
      "correction": "修改后的正确句子",
      "explanation": "用中文解释错误原因，给出简明记忆建议"
    }}
  ],
  "vocabulary": {{
    "good_collocations_used": ["学生原文中使用得比较好的搭配或表达"],
    "recommended_collocations": ["基于学生原句，给出的更高级或更地道的替代表达"],
    "advanced_structures": ["已经使用或建议使用的高级句型，如定语从句、倒装、强调句等"]
  }},
  "improved_version": "在保留学生原有立意和主要内容的前提下，用更高级、地道的词汇和多样的句型，重写一篇符合第五档标准的完整范文。注意结构清晰、衔接自然，贴合考研英语写作风格。"
}}
            """

            response = model.generate_content(prompt)
            if not response.text:
                return {"error": "Gemini returned empty response."}
            return self._parse_response(response.text)
        except Exception as e:
            print(f"ERROR: Gemini API Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"error": f"Gemini API Error: {str(e)}"}

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
        """
        if exam_type == "English I":
            return 10 if paper_type == "small_essay" else 20
        if exam_type == "English II":
            return 10 if paper_type == "small_essay" else 15
        return 20

    def analyze_trajectory(self, history_data: list, model_selection: str = "pro") -> dict:
        """
        Analyzes a list of past essay performance to find trends.
        history_data: List of dicts containing topic, scores, ai_analysis.
        model_selection: "flash" or "pro"; defaults to "pro".
        """
        model = self.get_model(model_selection)
        
        history_summary = []
        for entry in history_data:
            summary = {
                "date": entry.get("created_at"),
                "task_type": entry.get("task_type"),
                "scores": entry.get("scores"),
                "weaknesses": entry.get("weaknesses"),
                "topic": entry.get("topic"),
            }
            history_summary.append(summary)
            
        history_str = json.dumps(history_summary, indent=2)
        
        prompt = f"""
        You are an IELTS Writing Coach. Analyze the following student history to identify growth trends, persistent issues, and create a study plan.
        The history may contain both Task 1 and Task 2 essays. When you describe trends, explicitly consider differences between Task 1 and Task 2 performance.
        
        Student History:
        {history_str}
        
        Output JSON:
        {{
            "persistent_weaknesses": ["weakness 1", "weakness 2"],
            "progress_analysis": "Analysis of score trends (up/down/flat) and skill changes, noting any differences between Task 1 and Task 2.",
            "learning_plan": {{
                "focus_areas": ["area 1", "area 2"],
                "suggested_exercises": ["specific exercise 1", "exercise 2"]
            }},
            "trend_summary": "A concise summary for the dashboard (2-3 sentences)."
        }}
        """
        
        try:
            response = model.generate_content(prompt)
            return self._parse_response(response.text)
        except Exception as e:
            return {"error": f"Gemini API Error: {str(e)}"}

    def analyze_kaoyan_trajectory(self, history_data: list, model_selection: str = "pro") -> dict:
        """Analyze Kaoyan history using the specified Gemini model (flash/pro)."""
        model = self.get_model(model_selection)

        history_summary = []
        for entry in history_data:
            summary = {
                "date": entry.get("created_at"),
                "exam_type": entry.get("exam_type"),
                "paper_type": entry.get("paper_type"),
                "total_score": entry.get("total_score"),
                "band": entry.get("band"),
                "evaluation_summary": entry.get("evaluation_summary"),
                "topic": entry.get("topic"),
            }
            history_summary.append(summary)

        history_str = json.dumps(history_summary, indent=2)

        prompt = f"""
You are a Kaoyan (Chinese postgraduate entrance exam) English writing coach.
Analyze the following essay history, which is scored with a five-band holistic rubric and different maximum scores.
Pay special attention to differences between English I vs English II and between large vs small essays. If the student is weaker in a particular exam type or essay type, highlight this clearly.

Student Kaoyan History:
{history_str}

Output JSON:
{{
  "persistent_weaknesses": ["weakness 1", "weakness 2"],
  "progress_analysis": "Describe how the student's total scores and bands have changed over time, explicitly mentioning any differences between exam types (English I/II) and essay types (large/small).",
  "learning_plan": {{
    "focus_areas": ["area 1", "area 2"],
    "suggested_exercises": ["specific exercise 1", "exercise 2"]
  }},
  "trend_summary": "2-3 sentence Chinese summary that can be shown on a dashboard."
}}
        """

        try:
            response = model.generate_content(prompt)
            return self._parse_response(response.text)
        except Exception as e:
            return {"error": f"Gemini API Error: {str(e)}"}

    def _parse_response(self, text: str) -> dict:
        """Helper to clean and parse JSON from LLM response"""
        text = text.strip()
        # Remove markdown code blocks if present
        if text.startswith("```"):
            lines = text.split('\n')
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines[-1].startswith("```"):
                lines = lines[:-1]
            text = "\n".join(lines)
        
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Fallback: try to find the first { and last }
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1:
                try:
                    return json.loads(text[start:end+1])
                except:
                    pass
            return {"error": "Failed to parse JSON response", "raw_text": text}
