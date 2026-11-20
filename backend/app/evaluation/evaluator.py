
from typing import Optional

from deepeval.models import DeepEvalBaseLLM
from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCase, LLMTestCaseParams

from langchain_ollama import ChatOllama

from ..config import settings
from ..models import AgentEvaluation


class OllamaEvaluationModel(DeepEvalBaseLLM):
    """
    Custom DeepEval evaluation model using local Ollama.
    """

    def __init__(self):
        self.model = ChatOllama(
            model=settings.OLLAMA_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
            temperature=0
        )

    def load_model(self):
        return self.model

    def generate(self, prompt: str) -> str:
        response = self.model.invoke(prompt)
        return str(response.content)

    async def a_generate(self, prompt: str) -> str:
        response = await self.model.ainvoke(prompt)
        return str(response.content)

    def get_model_name(self) -> str:
        return f"Ollama-{settings.OLLAMA_MODEL}"


def evaluate_response(
    query: str,
    response: str,
    expected_output: Optional[str] = None,
    db=None,
    agent_run_id: Optional[int] = None
):
    """
    Evaluate an AI-generated response using DeepEval GEval.
    """

    evaluation_model = OllamaEvaluationModel()

    evaluation_params = [
        LLMTestCaseParams.INPUT,
        LLMTestCaseParams.ACTUAL_OUTPUT
    ]

    if expected_output is not None:
        evaluation_params.append(
            LLMTestCaseParams.EXPECTED_OUTPUT
        )

    # Metric 1: Answer Relevance
    relevance_metric = GEval(
        name="Answer Relevance",
        criteria="""
        Evaluate how relevant the actual output is to the user's input.

        Consider the following:
        1. Does the response directly answer the user's question?
        2. Does it stay focused on the requested topic?
        3. Does it avoid unrelated information?
        4. Does it provide sufficient information to address the query?

        Do not penalize an answer simply because it provides
        additional useful explanations or examples.

        A relevant and focused answer should receive a high score.
        """,
        evaluation_params=evaluation_params,
        model=evaluation_model,
        threshold=0.7
    )

    # Metric 2: Answer Quality
    quality_criteria = """
    Evaluate the overall quality of the AI-generated response.

    Consider these dimensions:

    1. Correctness:
       Is the information factually accurate?
       Are technical explanations and examples correct?

    2. Clarity:
       Is the response easy to understand?
       Is the explanation logically organized?

    3. Completeness:
       Does the response adequately answer the user's question?
       Does it include important details where necessary?

    4. Usefulness:
       Can the user understand or apply the information?

    5. Consistency:
       Does the response avoid contradictions and unsupported claims?

    IMPORTANT:
    - Do not require the actual output to exactly match the user's input.
    - Do not penalize a response simply for being detailed.
    - Additional relevant examples and explanations are acceptable.
    - Evaluate the usefulness and correctness of the answer,
      not its similarity to the wording of the question.
    """

    if expected_output is not None:
        quality_criteria += """
        Also compare the actual output against the expected output.
        Check whether the actual output covers the important information
        contained in the expected output without introducing errors.
        """

    quality_metric = GEval(
        name="Answer Quality",
        criteria=quality_criteria,
        evaluation_params=evaluation_params,
        model=evaluation_model,
        threshold=0.7
    )

    # Prepare test case
    test_case_data = {
        "input": query,
        "actual_output": response
    }

    if expected_output is not None:
        test_case_data["expected_output"] = expected_output

    test_case = LLMTestCase(**test_case_data)

    metrics = [
        relevance_metric,
        quality_metric
    ]

    results = []

    for metric in metrics:

        metric.measure(test_case)

        score = float(metric.score or 0)

        result = {
            "metric_name": metric.name,
            "score": score,
            "passed": bool(metric.success),
            "reason": metric.reason or ""
        }

        results.append(result)

        # Save evaluation results in MySQL
        if db is not None and agent_run_id is not None:

            evaluation_record = AgentEvaluation(
                agent_run_id=agent_run_id,
                metric_name=result["metric_name"],
                score=result["score"],
                passed=result["passed"],
                reason=result["reason"]
            )

            db.add(evaluation_record)

    if db is not None and agent_run_id is not None:
        db.commit()

    return results
