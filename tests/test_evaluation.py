
from .evaluation.test_cases import ROUTING_TEST_CASES


def test_routing_test_cases_exist():
    assert len(ROUTING_TEST_CASES) >= 4


def test_routing_test_cases_have_required_fields():
    for case in ROUTING_TEST_CASES:
        assert "query" in case
        assert "expected_agent" in case

        assert case["query"].strip()

        assert case["expected_agent"] in {
            "technical",
            "analysis",
            "support",
            "general"
        }


def test_all_agent_categories_are_covered():
    expected_agents = {
        case["expected_agent"]
        for case in ROUTING_TEST_CASES
    }

    assert expected_agents == {
        "technical",
        "analysis",
        "support",
        "general"
    }
