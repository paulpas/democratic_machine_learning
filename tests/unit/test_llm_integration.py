"""
Unit tests for src/llm/integration.py

Coverage targets:
  - LLMClient.__init__               (connection success + failure)
  - _call_llm                        (success, empty response, HTTP error)
  - investigate_domain_initial
  - investigate_subtopic
  - elaborate_subtopic
  - form_conjecture + _parse_conjecture
  - analyze_policy + _parse_analysis
  - generate_reasoning_with_recursion (shallow mock)
  - _geographic_fan_out
  - _extract_subtopics_from_text
  - _rank_solutions_with_geographic_weighting
  - generate_reasoning (legacy shim)
  - _generate_fallback_reasoning
  - _form_fallback_conjecture
  - _generate_fallback_analysis
  - US_STATES constant
  - DOMAIN_SUBTOPICS constant
"""

import json
import unittest
from unittest.mock import MagicMock, patch, call
from io import StringIO
from typing import Any, Dict

from src.llm.integration import (
    LLMClient,
    US_STATES,
    US_NATIONAL_POPULATION,
    REPRESENTATIVE_COUNTIES,
    DOMAIN_SUBTOPICS,
    _log,
    _log_section,
    _log_subsection,
)


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────


def _make_llm_response(content: str, tokens: int = 50) -> bytes:
    """Return the bytes of a minimal llama.cpp /completion JSON response."""
    return json.dumps({"content": content, "tokens_predicted": tokens}).encode()


def _fake_urlopen_factory(content: str, tokens: int = 50):
    """Return a context-manager mock that yields a fake HTTP response."""
    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=cm)
    cm.__exit__ = MagicMock(return_value=False)
    cm.getcode = MagicMock(return_value=200)
    cm.read = MagicMock(return_value=_make_llm_response(content, tokens))
    return cm


# ──────────────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────────────


class TestConstants(unittest.TestCase):
    def test_us_states_count(self):
        self.assertEqual(len(US_STATES), 50)

    def test_us_states_keys(self):
        for abbr, data in US_STATES.items():
            self.assertIn("name", data)
            self.assertIn("population", data)
            self.assertIn("counties", data)
            self.assertGreater(data["population"], 0)
            self.assertGreater(data["counties"], 0)

    def test_national_population(self):
        self.assertGreater(US_NATIONAL_POPULATION, 300_000_000)

    def test_representative_counties(self):
        self.assertGreaterEqual(len(REPRESENTATIVE_COUNTIES), 5)
        for c in REPRESENTATIVE_COUNTIES:
            self.assertIn("state", c)
            self.assertIn("name", c)
            self.assertIn("population", c)
            self.assertIn("type", c)
            self.assertIn(c["type"], {"urban", "suburban", "rural"})

    def test_domain_subtopics_all_domains(self):
        for domain in (
            "economy",
            "healthcare",
            "education",
            "immigration",
            "climate",
            "infrastructure",
        ):
            self.assertIn(domain, DOMAIN_SUBTOPICS)
            self.assertGreaterEqual(len(DOMAIN_SUBTOPICS[domain]), 5)


# ──────────────────────────────────────────────────────────────────────────────
# Logging helpers
# ──────────────────────────────────────────────────────────────────────────────


class TestLoggingHelpers(unittest.TestCase):
    def test_log_outputs_to_stdout(self):
        import io, sys

        buf = io.StringIO()
        with patch("sys.stdout", buf):
            _log("hello world")
        self.assertIn("hello world", buf.getvalue())

    def test_log_section(self):
        import io

        buf = io.StringIO()
        with patch("sys.stdout", buf):
            _log_section("TEST SECTION")
        out = buf.getvalue()
        self.assertIn("TEST SECTION", out)
        self.assertIn("=", out)

    def test_log_subsection(self):
        import io

        buf = io.StringIO()
        with patch("sys.stdout", buf):
            _log_subsection("sub section")
        out = buf.getvalue()
        self.assertIn("sub section", out)
        self.assertIn("-", out)


# ──────────────────────────────────────────────────────────────────────────────
# LLMClient.__init__
# ──────────────────────────────────────────────────────────────────────────────


class TestLLMClientInit(unittest.TestCase):
    @patch("urllib.request.urlopen")
    def test_init_connection_success(self, mock_urlopen):
        mock_urlopen.return_value = _fake_urlopen_factory("ok", 1)
        client = LLMClient(endpoint="http://localhost:8080")
        self.assertTrue(client.available)
        self.assertEqual(client.endpoint, "http://localhost:8080")

    @patch("urllib.request.urlopen", side_effect=OSError("refused"))
    def test_init_connection_failure(self, mock_urlopen):
        client = LLMClient(endpoint="http://localhost:9999")
        self.assertFalse(client.available)

    @patch("urllib.request.urlopen")
    def test_init_counter_reset(self, mock_urlopen):
        mock_urlopen.return_value = _fake_urlopen_factory("ok", 1)
        client = LLMClient()
        self.assertEqual(client._call_count, 0)
        self.assertEqual(client._total_tokens, 0)

    @patch("urllib.request.urlopen")
    def test_init_env_endpoint(self, mock_urlopen):
        mock_urlopen.return_value = _fake_urlopen_factory("ok", 1)
        with patch.dict(
            "os.environ", {"LLAMA_CPP_ENDPOINT": "http://example.com:8080"}
        ):
            client = LLMClient()
        self.assertEqual(client.endpoint, "http://example.com:8080")


# ──────────────────────────────────────────────────────────────────────────────
# _call_llm
# ──────────────────────────────────────────────────────────────────────────────


class TestCallLLM(unittest.TestCase):
    def _client(self) -> LLMClient:
        with patch("urllib.request.urlopen") as m:
            m.return_value = _fake_urlopen_factory("ok", 1)
            return LLMClient(endpoint="http://localhost:8080")

    @patch("urllib.request.urlopen")
    def test_call_llm_returns_content(self, mock_urlopen):
        client = self._client()
        mock_urlopen.return_value = _fake_urlopen_factory("This is the answer.", 10)
        result = client._call_llm("Some prompt", max_tokens=100)
        self.assertEqual(result, "This is the answer.")
        self.assertEqual(client._call_count, 1)
        self.assertEqual(client._total_tokens, 10)

    @patch("urllib.request.urlopen")
    def test_call_llm_increments_counters(self, mock_urlopen):
        client = self._client()
        mock_urlopen.return_value = _fake_urlopen_factory("aaa", 5)
        client._call_llm("p1", max_tokens=10)
        mock_urlopen.return_value = _fake_urlopen_factory("bbb", 8)
        client._call_llm("p2", max_tokens=10)
        self.assertEqual(client._call_count, 2)
        self.assertEqual(client._total_tokens, 13)

    @patch("urllib.request.urlopen", side_effect=OSError("network failure"))
    def test_call_llm_returns_empty_on_error(self, mock_urlopen):
        client = self._client()
        result = client._call_llm("prompt", max_tokens=50)
        self.assertEqual(result, "")

    def test_call_llm_skips_when_unavailable(self):
        with patch("urllib.request.urlopen", side_effect=OSError):
            client = LLMClient(endpoint="http://localhost:9999")
        self.assertFalse(client.available)
        result = client._call_llm("prompt", max_tokens=50)
        self.assertEqual(result, "")
        self.assertEqual(client._call_count, 0)

    @patch("urllib.request.urlopen")
    def test_call_llm_empty_content(self, mock_urlopen):
        client = self._client()
        mock_urlopen.return_value = _fake_urlopen_factory("", 0)
        result = client._call_llm("prompt", max_tokens=50)
        self.assertEqual(result, "")


# ──────────────────────────────────────────────────────────────────────────────
# investigate_domain_initial
# ──────────────────────────────────────────────────────────────────────────────


class TestInvestigateDomainInitial(unittest.TestCase):
    def _client(self) -> LLMClient:
        with patch("urllib.request.urlopen") as m:
            m.return_value = _fake_urlopen_factory("ok", 1)
            return LLMClient()

    @patch("urllib.request.urlopen")
    def test_returns_string(self, mock_urlopen):
        client = self._client()
        mock_urlopen.return_value = _fake_urlopen_factory(
            "Healthcare overview text.", 20
        )
        result = client.investigate_domain_initial(
            "healthcare", {"population": 331000000}, ["Equity"]
        )
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    @patch("urllib.request.urlopen")
    def test_calls_llm_once(self, mock_urlopen):
        client = self._client()
        mock_urlopen.return_value = _fake_urlopen_factory("text", 5)
        client.investigate_domain_initial("economy", {}, ["Transparency"])
        self.assertEqual(client._call_count, 1)


# ──────────────────────────────────────────────────────────────────────────────
# investigate_subtopic
# ──────────────────────────────────────────────────────────────────────────────


class TestInvestigateSubtopic(unittest.TestCase):
    def _client(self) -> LLMClient:
        with patch("urllib.request.urlopen") as m:
            m.return_value = _fake_urlopen_factory("ok", 1)
            return LLMClient()

    @patch("urllib.request.urlopen")
    def test_returns_nonempty_string(self, mock_urlopen):
        client = self._client()
        mock_urlopen.return_value = _fake_urlopen_factory("State-level analysis...", 30)
        result = client.investigate_subtopic(
            domain="healthcare",
            subtopic="Health Insurance Coverage",
            tier="state",
            tier_label="California",
            tier_population=39_500_000,
            depth=1,
            principles=["Equity"],
        )
        self.assertIsInstance(result, str)

    @patch("urllib.request.urlopen")
    def test_includes_parent_context_in_prompt(self, mock_urlopen):
        client = self._client()
        captured_prompt: Dict[str, Any] = {}

        def fake_urlopen(req, timeout=None):
            body = json.loads(req.data.decode())
            captured_prompt["prompt"] = body["prompt"]
            return _fake_urlopen_factory("response", 5)

        mock_urlopen.side_effect = fake_urlopen
        client.investigate_subtopic(
            domain="climate",
            subtopic="Carbon Pricing",
            tier="national",
            tier_label="United States",
            tier_population=331000000,
            depth=2,
            principles=["Equity"],
            parent_context="Earlier analysis showed X.",
        )
        self.assertIn("Carbon Pricing", captured_prompt["prompt"])


# ──────────────────────────────────────────────────────────────────────────────
# elaborate_subtopic
# ──────────────────────────────────────────────────────────────────────────────


class TestElaborateSubtopic(unittest.TestCase):
    def _client(self) -> LLMClient:
        with patch("urllib.request.urlopen") as m:
            m.return_value = _fake_urlopen_factory("ok", 1)
            return LLMClient()

    @patch("urllib.request.urlopen")
    def test_returns_string(self, mock_urlopen):
        client = self._client()
        mock_urlopen.return_value = _fake_urlopen_factory("Elaboration text.", 40)
        result = client.elaborate_subtopic(
            domain="education",
            subtopic="K-12 Funding Equity",
            tier="county",
            tier_label="Cook County",
            tier_population=5_275_000,
            depth=2,
            principles=["Equity"],
            prior_reasoning="Prior analysis...",
        )
        self.assertIsInstance(result, str)
        self.assertEqual(client._call_count, 1)


# ──────────────────────────────────────────────────────────────────────────────
# form_conjecture + _parse_conjecture
# ──────────────────────────────────────────────────────────────────────────────


class TestFormConjecture(unittest.TestCase):
    def _client(self) -> LLMClient:
        with patch("urllib.request.urlopen") as m:
            m.return_value = _fake_urlopen_factory("ok", 1)
            return LLMClient()

    @patch("urllib.request.urlopen")
    def test_returns_dict_with_required_keys(self, mock_urlopen):
        client = self._client()
        mock_urlopen.return_value = _fake_urlopen_factory(
            "Conjecture: Universal healthcare is optimal.\nConfidence: 0.85", 30
        )
        result = client.form_conjecture(
            question="What is optimal healthcare?",
            context={"population": 331000000},
            evidence=[{"finding": "Evidence 1", "tier": "national", "depth": 1}],
            domain="healthcare",
        )
        self.assertIn("statement", result)
        self.assertIn("confidence", result)
        self.assertIn("supporting_evidence", result)
        self.assertIn("contradicting_evidence", result)
        self.assertIn("evidence_count", result)

    @patch("urllib.request.urlopen")
    def test_confidence_clamped(self, mock_urlopen):
        client = self._client()
        mock_urlopen.return_value = _fake_urlopen_factory("Confidence: 150", 5)
        result = client.form_conjecture("Q?", {}, [], domain="test")
        self.assertLessEqual(result["confidence"], 1.0)
        self.assertGreaterEqual(result["confidence"], 0.0)

    def test_parse_conjecture_numbered_confidence(self):
        client = self._client()
        response = (
            "1. Conjecture: Public option insurance reduces costs.\n"
            "Confidence: 0.78\n"
            "Supporting evidence:\n"
            "- Evidence A\n"
            "- Evidence B\n"
        )
        result = client._parse_conjecture(response, "How?", [])
        self.assertIn("public option", result["statement"].lower())
        self.assertAlmostEqual(result["confidence"], 0.78, places=2)
        self.assertIn("Evidence A", result["supporting_evidence"])

    def test_parse_conjecture_fallback_statement(self):
        client = self._client()
        result = client._parse_conjecture("", "What is optimal?", [])
        self.assertGreater(len(result["statement"]), 5)

    def test_form_conjecture_fallback_when_unavailable(self):
        with patch("urllib.request.urlopen", side_effect=OSError):
            client = LLMClient(endpoint="http://bad:1234")
        result = client.form_conjecture("Q?", {}, [{"finding": "f1"}], domain="x")
        self.assertIn("statement", result)
        self.assertGreaterEqual(result["confidence"], 0.0)

    @patch("urllib.request.urlopen")
    def test_evidence_count_preserved(self, mock_urlopen):
        client = self._client()
        mock_urlopen.return_value = _fake_urlopen_factory("answer", 5)
        evidence = [
            {"finding": f"f{i}", "tier": "national", "depth": 0} for i in range(7)
        ]
        result = client.form_conjecture("Q?", {}, evidence, domain="test")
        self.assertEqual(result["evidence_count"], 7)


# ──────────────────────────────────────────────────────────────────────────────
# analyze_policy + _parse_analysis
# ──────────────────────────────────────────────────────────────────────────────


class TestAnalyzePolicy(unittest.TestCase):
    def _client(self) -> LLMClient:
        with patch("urllib.request.urlopen") as m:
            m.return_value = _fake_urlopen_factory("ok", 1)
            return LLMClient()

    @patch("urllib.request.urlopen")
    def test_returns_analysis_dict(self, mock_urlopen):
        client = self._client()
        mock_urlopen.return_value = _fake_urlopen_factory(
            "Findings: Major gaps exist.\nRecommendations:\n- Expand coverage\nOutcomes:\n- Better health",
            40,
        )
        result = client.analyze_policy("healthcare", {"population": 331000000})
        self.assertIn("findings", result)
        self.assertIn("consensus", result)
        self.assertIn("recommendations", result)
        self.assertIn("implementation", result)
        self.assertIn("outcomes", result)

    @patch("urllib.request.urlopen")
    def test_fallback_on_llm_error(self, mock_urlopen):
        client = self._client()
        mock_urlopen.side_effect = OSError("fail")
        result = client.analyze_policy("economy", {})
        self.assertIn("findings", result)

    def test_parse_analysis_extracts_recommendations(self):
        client = self._client()
        resp = (
            "Recommendations:\n- Expand access\n- Reduce cost\n"
            "Implementation:\n- Phase 1: pilot\n"
            "Outcomes:\n- Better access"
        )
        result = client._parse_analysis(resp, "healthcare")
        self.assertIn("Expand access", result["recommendations"])
        self.assertIn("Phase 1: pilot", result["implementation"])


# ──────────────────────────────────────────────────────────────────────────────
# _extract_subtopics_from_text
# ──────────────────────────────────────────────────────────────────────────────


class TestExtractSubtopics(unittest.TestCase):
    def _client(self) -> LLMClient:
        with patch("urllib.request.urlopen") as m:
            m.return_value = _fake_urlopen_factory("ok", 1)
            return LLMClient()

    def test_extracts_numbered_list(self):
        client = self._client()
        text = "1. Health Insurance Coverage\n2. Cost Control\n3. Quality Outcomes\n4. Prevention\n5. Equity"
        result = client._extract_subtopics_from_text(text, "healthcare", 5)
        self.assertGreaterEqual(len(result), 3)
        self.assertTrue(any("Health Insurance" in s for s in result))

    def test_extracts_bold_markdown(self):
        client = self._client()
        text = "Key areas include **Renewable Energy** and **Carbon Pricing** and **Climate Adaptation**."
        result = client._extract_subtopics_from_text(text, "climate", 3)
        self.assertGreaterEqual(len(result), 1)

    def test_falls_back_to_domain_seeds(self):
        client = self._client()
        result = client._extract_subtopics_from_text(
            "no list here at all", "economy", 5
        )
        self.assertGreaterEqual(len(result), 3)
        seeds = DOMAIN_SUBTOPICS["economy"]
        self.assertTrue(any(s in seeds for s in result))

    def test_count_respected(self):
        client = self._client()
        result = client._extract_subtopics_from_text(
            "1. A Topic\n2. B Topic\n3. C Topic\n4. D Topic\n5. E Topic\n6. F Topic",
            "education",
            3,
        )
        self.assertLessEqual(len(result), 3)

    def test_deduplication(self):
        client = self._client()
        text = "1. Health Insurance Coverage\n2. Health Insurance Coverage\n3. Cost Control"
        result = client._extract_subtopics_from_text(text, "healthcare", 5)
        lower = [s.lower() for s in result]
        self.assertEqual(len(lower), len(set(lower)))


# ──────────────────────────────────────────────────────────────────────────────
# _rank_solutions_with_geographic_weighting
# ──────────────────────────────────────────────────────────────────────────────


class TestRankSolutions(unittest.TestCase):
    def _client(self) -> LLMClient:
        with patch("urllib.request.urlopen") as m:
            m.return_value = _fake_urlopen_factory("ok", 1)
            return LLMClient()

    def _make_elaborations(self):
        return [
            {
                "tier": "national",
                "finding": "National access reform with evidence of equitable outcomes.",
                "subtopic": "Access",
                "depth": 1,
                "tier_label": "US",
            },
            {
                "tier": "state",
                "finding": "State-level implementation with stakeholder support.",
                "subtopic": "Access",
                "depth": 1,
                "tier_label": "California",
            },
            {
                "tier": "county",
                "finding": "x",
                "subtopic": "Access",
                "depth": 1,
                "tier_label": "LA County",
            },
        ]

    def test_returns_list(self):
        client = self._client()
        result = client._rank_solutions_with_geographic_weighting(
            self._make_elaborations(), "healthcare"
        )
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 3)

    def test_sorted_descending(self):
        client = self._client()
        result = client._rank_solutions_with_geographic_weighting(
            self._make_elaborations(), "healthcare"
        )
        scores = [r["score"] for r in result]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_national_scores_higher_than_county(self):
        client = self._client()
        elab = [
            {
                "tier": "national",
                "finding": "A" * 200,
                "subtopic": "S",
                "depth": 1,
                "tier_label": "US",
            },
            {
                "tier": "county",
                "finding": "A" * 200,
                "subtopic": "S",
                "depth": 1,
                "tier_label": "LA",
            },
        ]
        result = client._rank_solutions_with_geographic_weighting(elab, "test")
        self.assertGreater(result[0]["score"], result[1]["score"])
        self.assertEqual(result[0]["tier"], "national")

    def test_required_fields(self):
        client = self._client()
        result = client._rank_solutions_with_geographic_weighting(
            self._make_elaborations(), "healthcare"
        )
        for r in result:
            self.assertIn("solution", r)
            self.assertIn("tier", r)
            self.assertIn("score", r)
            self.assertIn("should_capture", r)
            self.assertIn("domain", r)


# ──────────────────────────────────────────────────────────────────────────────
# generate_reasoning (legacy shim)
# ──────────────────────────────────────────────────────────────────────────────


class TestGenerateReasoning(unittest.TestCase):
    def _client(self) -> LLMClient:
        with patch("urllib.request.urlopen") as m:
            m.return_value = _fake_urlopen_factory("ok", 1)
            return LLMClient()

    @patch("urllib.request.urlopen")
    def test_returns_string(self, mock_urlopen):
        client = self._client()
        mock_urlopen.return_value = _fake_urlopen_factory("reasoning text", 20)
        result = client.generate_reasoning(
            context={"population": 331000000},
            research_questions=["What is the key challenge?"],
            principles=["Equity"],
            domain="healthcare",
            tier="national",
            depth=0,
        )
        self.assertIsInstance(result, str)

    def test_fallback_when_unavailable(self):
        with patch("urllib.request.urlopen", side_effect=OSError):
            client = LLMClient(endpoint="http://bad:1234")
        result = client.generate_reasoning(
            context={"population": 100},
            research_questions=["Q?"],
            principles=["P1"],
        )
        self.assertIsInstance(result, str)


# ──────────────────────────────────────────────────────────────────────────────
# generate_reasoning_with_recursion — integration-level (mocked LLM)
# ──────────────────────────────────────────────────────────────────────────────


class TestGenerateReasoningWithRecursion(unittest.TestCase):
    """
    These tests mock _call_llm to return realistic text so we can test the
    orchestration logic without hitting the real LLM endpoint.
    """

    NUMBERED_LIST = (
        "1. Health Insurance Coverage and Access\n"
        "2. Healthcare Cost Control\n"
        "3. Healthcare Quality\n"
        "4. Public Health Infrastructure\n"
        "5. Health Equity\n"
    )

    def _client(self) -> LLMClient:
        with patch("urllib.request.urlopen") as m:
            m.return_value = _fake_urlopen_factory("ok", 1)
            return LLMClient()

    def test_returns_required_keys(self):
        client = self._client()
        with patch.object(client, "_call_llm", return_value=self.NUMBERED_LIST):
            result = client.generate_reasoning_with_recursion(
                domain="healthcare",
                initial_context={"population": 331000000},
                max_depth=1,
                subtopics_per_level=3,
                include_state_county_rep=False,
            )
        for key in (
            "domain",
            "max_depth",
            "subtopics_per_level",
            "recursive_analysis",
            "subtopics_by_level",
            "all_elaborations",
            "final_conjecture",
            "best_solutions",
            "started_at",
        ):
            self.assertIn(key, result)

    def test_domain_stored(self):
        client = self._client()
        with patch.object(client, "_call_llm", return_value=self.NUMBERED_LIST):
            result = client.generate_reasoning_with_recursion(
                domain="economy",
                initial_context={},
                max_depth=1,
                subtopics_per_level=2,
                include_state_county_rep=False,
            )
        self.assertEqual(result["domain"], "economy")

    def test_subtopics_extracted(self):
        client = self._client()
        with patch.object(client, "_call_llm", return_value=self.NUMBERED_LIST):
            result = client.generate_reasoning_with_recursion(
                domain="healthcare",
                initial_context={},
                max_depth=1,
                subtopics_per_level=5,
                include_state_county_rep=False,
            )
        level0_topics = result["subtopics_by_level"].get("level_0", [])
        self.assertGreater(len(level0_topics), 0)

    def test_all_elaborations_populated(self):
        client = self._client()
        with patch.object(client, "_call_llm", return_value=self.NUMBERED_LIST):
            result = client.generate_reasoning_with_recursion(
                domain="climate",
                initial_context={},
                max_depth=1,
                subtopics_per_level=2,
                include_state_county_rep=False,
            )
        self.assertGreater(len(result["all_elaborations"]), 0)

    def test_best_solutions_sorted(self):
        client = self._client()
        with patch.object(client, "_call_llm", return_value=self.NUMBERED_LIST):
            result = client.generate_reasoning_with_recursion(
                domain="education",
                initial_context={},
                max_depth=1,
                subtopics_per_level=2,
                include_state_county_rep=False,
            )
        scores = [s["score"] for s in result["best_solutions"]]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_elapsed_and_counters_present(self):
        client = self._client()
        with patch.object(client, "_call_llm", return_value=self.NUMBERED_LIST):
            result = client.generate_reasoning_with_recursion(
                domain="immigration",
                initial_context={},
                max_depth=1,
                subtopics_per_level=2,
                include_state_county_rep=False,
            )
        self.assertIn("elapsed_seconds", result)
        self.assertIn("llm_calls", result)
        self.assertIn("total_tokens", result)

    def test_geographic_fan_out_populates_state_entries(self):
        """With include_state_county_rep=True, all_elaborations should have state entries."""
        client = self._client()
        with patch.object(client, "_call_llm", return_value=self.NUMBERED_LIST):
            result = client.generate_reasoning_with_recursion(
                domain="healthcare",
                initial_context={},
                max_depth=1,
                subtopics_per_level=1,
                include_state_county_rep=True,
            )
        tiers = {e["tier"] for e in result["all_elaborations"]}
        self.assertIn("state", tiers)
        self.assertIn("county", tiers)
        self.assertIn("national", tiers)

    def test_all_50_states_represented(self):
        client = self._client()
        with patch.object(client, "_call_llm", return_value=self.NUMBERED_LIST):
            result = client.generate_reasoning_with_recursion(
                domain="healthcare",
                initial_context={},
                max_depth=1,
                subtopics_per_level=1,
                include_state_county_rep=True,
            )
        state_abbrs = {
            e["state_abbr"] for e in result["all_elaborations"] if e["tier"] == "state"
        }
        self.assertEqual(len(state_abbrs), 50)

    def test_final_conjecture_has_statement(self):
        client = self._client()
        with patch.object(
            client,
            "_call_llm",
            return_value=(
                "Conjecture: Multi-tiered governance works.\n"
                "Confidence: 0.82\n" + self.NUMBERED_LIST
            ),
        ):
            result = client.generate_reasoning_with_recursion(
                domain="economy",
                initial_context={},
                max_depth=1,
                subtopics_per_level=2,
                include_state_county_rep=False,
            )
        self.assertGreater(len(result["final_conjecture"].get("statement", "")), 5)

    def test_no_state_rep_when_disabled(self):
        client = self._client()
        with patch.object(client, "_call_llm", return_value=self.NUMBERED_LIST):
            result = client.generate_reasoning_with_recursion(
                domain="infrastructure",
                initial_context={},
                max_depth=1,
                subtopics_per_level=2,
                include_state_county_rep=False,
            )
        tiers = {e["tier"] for e in result["all_elaborations"]}
        self.assertNotIn("state", tiers)
        self.assertNotIn("county", tiers)


# ──────────────────────────────────────────────────────────────────────────────
# Fallback methods
# ──────────────────────────────────────────────────────────────────────────────


class TestFallbacks(unittest.TestCase):
    def _client(self) -> LLMClient:
        with patch("urllib.request.urlopen") as m:
            m.return_value = _fake_urlopen_factory("ok", 1)
            return LLMClient()

    def test_fallback_reasoning_returns_string(self):
        client = self._client()
        result = client._generate_fallback_reasoning({"population": 1000}, ["Equity"])
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 10)

    def test_fallback_conjecture_with_evidence(self):
        client = self._client()
        result = client._form_fallback_conjecture("Q?", [{"finding": "f1"}])
        self.assertIn("statement", result)
        self.assertGreaterEqual(result["confidence"], 0.4)

    def test_fallback_conjecture_no_evidence(self):
        client = self._client()
        result = client._form_fallback_conjecture("Q?", [])
        self.assertLess(result["confidence"], 0.7)

    def test_fallback_analysis_structure(self):
        client = self._client()
        result = client._generate_fallback_analysis("healthcare", {})
        self.assertIn("findings", result)
        self.assertIsInstance(result["recommendations"], list)


# ──────────────────────────────────────────────────────────────────────────────
# _geographic_fan_out (mocked)
# ──────────────────────────────────────────────────────────────────────────────


class TestGeographicFanOut(unittest.TestCase):
    NUMBERED_LIST = "1. Health Insurance Coverage\n2. Cost Control\n3. Quality\n4. Prevention\n5. Equity\n"

    def _client(self) -> LLMClient:
        with patch("urllib.request.urlopen") as m:
            m.return_value = _fake_urlopen_factory("ok", 1)
            return LLMClient()

    def test_returns_50_state_entries(self):
        client = self._client()
        with patch.object(client, "_call_llm", return_value=self.NUMBERED_LIST):
            states, counties = client._geographic_fan_out(
                domain="healthcare",
                subtopic="Health Insurance Coverage",
                depth=1,
                principles=["Equity"],
                prior_reasoning="prior",
            )
        self.assertEqual(len(states), 50)

    def test_returns_county_entries(self):
        client = self._client()
        with patch.object(client, "_call_llm", return_value=self.NUMBERED_LIST):
            states, counties = client._geographic_fan_out(
                domain="economy",
                subtopic="Job Creation",
                depth=1,
                principles=["Equity"],
                prior_reasoning="prior",
            )
        self.assertEqual(len(counties), len(REPRESENTATIVE_COUNTIES))

    def test_state_entry_structure(self):
        client = self._client()
        with patch.object(client, "_call_llm", return_value=self.NUMBERED_LIST):
            states, _ = client._geographic_fan_out(
                domain="climate",
                subtopic="Carbon Pricing",
                depth=2,
                principles=["Equity"],
                prior_reasoning="",
            )
        for entry in states:
            self.assertIn("tier", entry)
            self.assertIn("tier_label", entry)
            self.assertIn("state_abbr", entry)
            self.assertIn("tier_population", entry)
            self.assertIn("reasoning", entry)
            self.assertIn("elaboration", entry)
            self.assertIn("finding", entry)
            self.assertEqual(entry["tier"], "state")

    def test_county_entry_structure(self):
        client = self._client()
        with patch.object(client, "_call_llm", return_value=self.NUMBERED_LIST):
            _, counties = client._geographic_fan_out(
                domain="education",
                subtopic="Funding Equity",
                depth=1,
                principles=["Equity"],
                prior_reasoning="",
            )
        for entry in counties:
            self.assertEqual(entry["tier"], "county")
            self.assertIn("county_type", entry)
            self.assertIn("tier_population", entry)

    def test_all_state_abbrs_covered(self):
        client = self._client()
        with patch.object(client, "_call_llm", return_value=self.NUMBERED_LIST):
            states, _ = client._geographic_fan_out(
                domain="immigration",
                subtopic="Border Security",
                depth=1,
                principles=["Equity"],
                prior_reasoning="",
            )
        abbrs = {e["state_abbr"] for e in states}
        self.assertEqual(abbrs, set(US_STATES.keys()))


if __name__ == "__main__":
    unittest.main(verbosity=2)
