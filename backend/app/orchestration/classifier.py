
import re

VALID_AGENTS = {
    "technical",
    "analysis",
    "support",
    "general"
}

SUPPORT_KEYWORDS = [
    "error", "issue", "not working", "failed",
    "failure", "troubleshoot", "problem",
    "installation", "install", "offline",
    "crashing", "crashed", "unable to",
    "cannot connect", "connection refused",
    "exception", "bug", "broken"
]

TECHNICAL_KEYWORDS = [
    "python", "javascript", "programming", "code",
    "coding", "debug", "api", "database", "sql",
    "fastapi", "react", "function", "class",
    "algorithm", "inheritance", "decorator",
    "object oriented", "machine learning",
    "neural network", "software", "html",
    "css", "java", "typescript", "git"
]

ANALYSIS_KEYWORDS = [
    "analyze", "analysis", "compare", "comparison",
    "evaluate", "data", "statistics", "pros and cons",
    "recommendation", "reasoning", "trend",
    "advantages", "disadvantages", "difference",
    "which is better", "performance",
    "benefits", "drawbacks"
]


def contains_keyword(text: str, keywords: list) -> bool:
    for keyword in keywords:
        pattern = r"(?<!\w)" + re.escape(keyword) + r"(?!\w)"

        if re.search(pattern, text):
            return True

    return False


def count_keyword_matches(text: str, keywords: list) -> int:
    count = 0

    for keyword in keywords:
        pattern = r"(?<!\w)" + re.escape(keyword) + r"(?!\w)"

        if re.search(pattern, text):
            # Give multi-word intent phrases extra weight.
            count += 2 if " " in keyword else 1

    return count


def classify_query(query: str):

    text = query.lower().strip()

    if not text:
        return "general", 0.70

    # Support requests take priority when troubleshooting is involved.
    support_score = count_keyword_matches(text, SUPPORT_KEYWORDS)

    if support_score > 0:
        return "support", 0.90

    # Calculate technical and analysis relevance.
    technical_score = count_keyword_matches(
        text, TECHNICAL_KEYWORDS
    )

    analysis_score = count_keyword_matches(
        text, ANALYSIS_KEYWORDS
    )

    # Select the category with the highest score.
    if analysis_score > technical_score:
        confidence = 0.90 if analysis_score >= 2 else 0.85
        return "analysis", confidence

    if technical_score > analysis_score:
        confidence = 0.90 if technical_score >= 2 else 0.85
        return "technical", confidence

    # Resolve ties in favor of analysis when both categories match.
    if analysis_score > 0:
        return "analysis", 0.80

    return "general", 0.70
