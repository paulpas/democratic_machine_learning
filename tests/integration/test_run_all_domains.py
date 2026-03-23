"""
Integration tests for run_all_domains.py

These tests mock the LLM endpoint and social collector to verify the full
pipeline orchestration: voter registration, democratic decision, LLM recursion,
and report generation.
"""

import json
import unittest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, call
from typing import Dict, Any

# ── minimal stubs for heavy imports that require live services ────────────────

import sys
import os

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


def _fake_llm_response(
    content: str = "1. Topic A\n2. Topic B\n3. Topic C\n", tokens: int = 30
) -> bytes:
    return json.dumps({"content": content, "tokens_predicted": tokens}).encode()


def _urlopen_cm(content: str = "1. Topic A\n2. Topic B\n3. Topic C\n"):
    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=cm)
    cm.__exit__ = MagicMock(return_value=False)
    cm.getcode = MagicMock(return_value=200)
    cm.read = MagicMock(return_value=_fake_llm_response(content))
    return cm


SAMPLE_SOCIAL_DATA = {
    "topic": "healthcare policy",
    "domain": "healthcare",
    "opinions": [
        {
            "text": "We need universal healthcare",
            "perspective": "supportive",
            "sentiment_score": 0.8,
        }
    ],
    "media_narratives": [
        {
            "title": "Healthcare reform debate",
            "outlet": "News",
            "sentiment_score": 0.5,
            "credibility_score": 0.7,
        }
    ],
    "summary": {
        "total_opinions": 1,
        "total_narratives": 1,
        "average_opinion_sentiment": 0.8,
        "average_narrative_sentiment": 0.5,
        "total_engagement": 100,
        "data_sources": ["Reddit"],
        "data_freshness": "real_time",
        "average_media_credibility": 0.7,
    },
}


class TestRunAllDomainsVoterPool(unittest.TestCase):
    """Test voter pool construction."""

    def setUp(self):
        self.patcher = patch("urllib.request.urlopen", return_value=_urlopen_cm())
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    def test_voter_pool_registers_experts(self):
        """10 expert voters should be registered."""
        from src.core.decision_engine import DecisionEngine
        from src.models.policy import Policy, PolicyDomain
        from src.models.region import Region
        from run_all_domains import _build_national_voter_pool

        engine = DecisionEngine()
        engine.register_region(Region("US", "United States", "national", 331000000))
        engine.register_policy(
            Policy(
                "us_healthcare_2026",
                "Healthcare Policy 2026",
                "desc",
                PolicyDomain.HEALTHCARE,
            )
        )

        _build_national_voter_pool(engine, "healthcare", "us_healthcare_2026")

        expert_count = sum(
            1 for v in engine.voters.values() if v.voter_id.startswith("expert_")
        )
        self.assertEqual(expert_count, 10)

    def test_voter_pool_registers_50_state_delegates(self):
        from src.core.decision_engine import DecisionEngine
        from src.models.policy import Policy, PolicyDomain
        from src.models.region import Region
        from run_all_domains import _build_national_voter_pool

        engine = DecisionEngine()
        engine.register_region(Region("US", "United States", "national", 331000000))
        engine.register_policy(
            Policy(
                "us_economy_2026", "Economy Policy 2026", "desc", PolicyDomain.ECONOMIC
            )
        )

        _build_national_voter_pool(engine, "economy", "us_economy_2026")

        state_count = sum(
            1 for v in engine.voters.values() if v.voter_id.startswith("state_")
        )
        self.assertEqual(state_count, 50)

    def test_voter_pool_registers_county_delegates(self):
        from src.core.decision_engine import DecisionEngine
        from src.models.policy import Policy, PolicyDomain
        from src.models.region import Region
        from run_all_domains import (
            _build_national_voter_pool,
            REPRESENTATIVE_COUNTIES_INFO,
        )

        engine = DecisionEngine()
        engine.register_region(Region("US", "United States", "national", 331000000))
        engine.register_policy(
            Policy(
                "us_climate_2026",
                "Climate Policy 2026",
                "desc",
                PolicyDomain.ENVIRONMENT,
            )
        )

        _build_national_voter_pool(engine, "climate", "us_climate_2026")

        county_count = sum(
            1 for v in engine.voters.values() if v.voter_id.startswith("county_")
        )
        self.assertEqual(county_count, len(REPRESENTATIVE_COUNTIES_INFO))

    def test_voter_pool_registers_public_sample(self):
        from src.core.decision_engine import DecisionEngine
        from src.models.policy import Policy, PolicyDomain
        from src.models.region import Region
        from run_all_domains import _build_national_voter_pool

        engine = DecisionEngine()
        engine.register_region(Region("US", "United States", "national", 331000000))
        engine.register_policy(
            Policy(
                "us_education_2026",
                "Education Policy 2026",
                "desc",
                PolicyDomain.EDUCATION,
            )
        )

        _build_national_voter_pool(engine, "education", "us_education_2026")

        public_count = sum(
            1 for v in engine.voters.values() if v.voter_id.startswith("public_")
        )
        self.assertGreater(public_count, 0)

    def test_all_voters_have_preference_set(self):
        from src.core.decision_engine import DecisionEngine
        from src.models.policy import Policy, PolicyDomain
        from src.models.region import Region
        from run_all_domains import _build_national_voter_pool

        policy_id = "us_immigration_2026"
        engine = DecisionEngine()
        engine.register_region(Region("US", "United States", "national", 331000000))
        engine.register_policy(
            Policy(policy_id, "Immigration Policy", "desc", PolicyDomain.SECURITY)
        )

        _build_national_voter_pool(engine, "immigration", policy_id)

        for voter in engine.voters.values():
            pref = voter.get_preference(policy_id)
            self.assertIsNotNone(pref, f"Voter {voter.voter_id} has no preference")


class TestRunDomain(unittest.TestCase):
    """Test the run_domain() function with mocked LLM and social collector."""

    def setUp(self):
        self.llm_patcher = patch(
            "urllib.request.urlopen",
            return_value=_urlopen_cm(
                "1. Health Insurance Coverage\n2. Cost Control\n3. Quality\n4. Prevention\n5. Equity\n"
            ),
        )
        self.llm_patcher.start()

        self.social_mock = MagicMock()
        self.social_mock.get_comprehensive_social_data.return_value = SAMPLE_SOCIAL_DATA

    def tearDown(self):
        self.llm_patcher.stop()

    def test_run_domain_returns_dict(self):
        from src.llm.integration import LLMClient
        from run_all_domains import run_domain

        llm_client = LLMClient()
        result = run_domain("healthcare", llm_client, self.social_mock)
        self.assertIsInstance(result, dict)

    def test_run_domain_required_keys(self):
        from src.llm.integration import LLMClient
        from run_all_domains import run_domain

        llm_client = LLMClient()
        result = run_domain("economy", llm_client, self.social_mock)
        for key in (
            "domain",
            "policy_id",
            "timestamp",
            "decision",
            "social_data",
            "llm_results",
            "final_conjecture",
        ):
            self.assertIn(key, result)

    def test_run_domain_decision_structure(self):
        from src.llm.integration import LLMClient
        from run_all_domains import run_domain

        llm_client = LLMClient()
        result = run_domain("climate", llm_client, self.social_mock)
        decision = result["decision"]
        self.assertIn("outcome", decision)
        self.assertIn("confidence", decision)
        self.assertIn("votes_for", decision)
        self.assertIn("votes_against", decision)
        self.assertIn("voters_participated", decision)
        self.assertIn("total_voters", decision)

    def test_run_domain_has_voters(self):
        from src.llm.integration import LLMClient
        from run_all_domains import run_domain

        llm_client = LLMClient()
        result = run_domain("education", llm_client, self.social_mock)
        self.assertGreater(result["decision"]["total_voters"], 50)

    def test_run_domain_outcome_valid(self):
        from src.llm.integration import LLMClient
        from run_all_domains import run_domain

        llm_client = LLMClient()
        result = run_domain("immigration", llm_client, self.social_mock)
        self.assertIn(
            result["decision"]["outcome"], ("approved", "rejected", "abstain")
        )

    def test_run_domain_social_data_collected(self):
        from src.llm.integration import LLMClient
        from run_all_domains import run_domain

        llm_client = LLMClient()
        run_domain("infrastructure", llm_client, self.social_mock)
        self.social_mock.get_comprehensive_social_data.assert_called_once()

    def test_run_domain_elapsed_tracked(self):
        from src.llm.integration import LLMClient
        from run_all_domains import run_domain

        llm_client = LLMClient()
        result = run_domain("healthcare", llm_client, self.social_mock)
        self.assertIn("elapsed_seconds", result)
        self.assertGreaterEqual(result["elapsed_seconds"], 0)

    def test_run_domain_social_error_graceful(self):
        """Social data collection errors should not abort the domain analysis."""
        from src.llm.integration import LLMClient
        from run_all_domains import run_domain

        social_err = MagicMock()
        social_err.get_comprehensive_social_data.side_effect = RuntimeError(
            "network fail"
        )

        llm_client = LLMClient()
        # Should not raise
        result = run_domain("climate", llm_client, social_err)
        self.assertIn("domain", result)


class TestWriteReport(unittest.TestCase):
    """Test the write_report() function."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.orig_output = None

    def _patch_output_dir(self):
        import run_all_domains

        self.orig_output = run_all_domains.OUTPUT_DIR
        run_all_domains.OUTPUT_DIR = Path(self.tmpdir)
        return run_all_domains

    def tearDown(self):
        if self.orig_output is not None:
            import run_all_domains

            run_all_domains.OUTPUT_DIR = self.orig_output

    def _make_result(self, domain: str = "healthcare") -> Dict[str, Any]:
        return {
            "domain": domain,
            "policy_id": f"us_{domain}_2026",
            "timestamp": "2026-03-22T12:00:00",
            "elapsed_seconds": 42.5,
            "total_llm_calls": 120,
            "total_tokens": 50000,
            "decision": {
                "outcome": "approved",
                "confidence": 0.75,
                "votes_for": 100,
                "votes_against": 30,
                "voters_participated": 130,
                "total_voters": 170,
            },
            "social_data": {
                "total_opinions": 15,
                "total_narratives": 12,
                "average_opinion_sentiment": 0.72,
                "average_narrative_sentiment": 0.45,
            },
            "final_conjecture": {
                "statement": "Universal coverage is the optimal approach.",
                "confidence": 0.82,
                "supporting_evidence": ["Evidence A", "Evidence B"],
                "contradicting_evidence": ["Concern X"],
            },
            "best_solutions": [
                {
                    "solution": "Expand Medicaid",
                    "tier": "national",
                    "tier_label": "United States",
                    "domain": domain,
                    "subtopic": "Health Insurance",
                    "depth": 1,
                    "score": 0.92,
                    "should_capture": True,
                }
            ],
            "llm_results": {
                "subtopics_by_level": {
                    "level_0": ["Health Insurance", "Cost Control"],
                    "level_1": ["Medicare expansion", "Medicaid reform"],
                }
            },
        }

    def test_write_report_creates_file(self):
        mod = self._patch_output_dir()
        result = self._make_result("healthcare")
        path = mod.write_report(result)
        self.assertTrue(path.exists())

    def test_write_report_correct_filename(self):
        mod = self._patch_output_dir()
        for domain in ("economy", "climate", "immigration"):
            result = self._make_result(domain)
            path = mod.write_report(result)
            self.assertEqual(path.name, f"us_{domain}_governance_model.md")

    def test_write_report_contains_decision_outcome(self):
        mod = self._patch_output_dir()
        result = self._make_result("economy")
        path = mod.write_report(result)
        content = path.read_text()
        self.assertIn("APPROVED", content)

    def test_write_report_contains_conjecture(self):
        mod = self._patch_output_dir()
        result = self._make_result()
        path = mod.write_report(result)
        content = path.read_text()
        self.assertIn("Universal coverage", content)

    def test_write_report_contains_best_solution(self):
        mod = self._patch_output_dir()
        result = self._make_result()
        path = mod.write_report(result)
        content = path.read_text()
        self.assertIn("Expand Medicaid", content)

    def test_write_report_contains_subtopic_tree(self):
        mod = self._patch_output_dir()
        result = self._make_result()
        path = mod.write_report(result)
        content = path.read_text()
        self.assertIn("Health Insurance", content)

    def test_write_report_contains_voter_info(self):
        mod = self._patch_output_dir()
        result = self._make_result()
        path = mod.write_report(result)
        content = path.read_text()
        self.assertIn("expert", content.lower())
        self.assertIn("state delegate", content.lower())


class TestMainFunction(unittest.TestCase):
    """Test main() argument parsing and domain dispatch."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.llm_patcher = patch(
            "urllib.request.urlopen",
            return_value=_urlopen_cm("1. Topic A\n2. Topic B\n3. Topic C\n"),
        )
        self.llm_patcher.start()

    def tearDown(self):
        self.llm_patcher.stop()

    def test_main_invalid_domain_exits_1(self):
        with patch("sys.argv", ["run_all_domains.py", "notadomain"]):
            from run_all_domains import main

            code = main()
        self.assertEqual(code, 1)

    def test_main_single_domain_success(self):
        """Single domain with full mock should return 0."""
        import run_all_domains

        social_mock = MagicMock()
        social_mock.get_comprehensive_social_data.return_value = SAMPLE_SOCIAL_DATA

        original_output = run_all_domains.OUTPUT_DIR
        run_all_domains.OUTPUT_DIR = Path(self.tmpdir)

        try:
            with (
                patch("sys.argv", ["run_all_domains.py", "healthcare"]),
                patch(
                    "run_all_domains.SocialNarrativeCollector", return_value=social_mock
                ),
            ):
                code = run_all_domains.main()
            self.assertEqual(code, 0)
        finally:
            run_all_domains.OUTPUT_DIR = original_output

    def test_main_writes_session_summary(self):
        """Session summary JSON should be written after a successful run."""
        import run_all_domains

        social_mock = MagicMock()
        social_mock.get_comprehensive_social_data.return_value = SAMPLE_SOCIAL_DATA

        original_output = run_all_domains.OUTPUT_DIR
        run_all_domains.OUTPUT_DIR = Path(self.tmpdir)

        try:
            with (
                patch("sys.argv", ["run_all_domains.py", "climate"]),
                patch(
                    "run_all_domains.SocialNarrativeCollector", return_value=social_mock
                ),
            ):
                run_all_domains.main()
            summary_path = Path(self.tmpdir) / "session_summary.json"
            self.assertTrue(summary_path.exists())
            summary = json.loads(summary_path.read_text())
            self.assertIn("started_at", summary)
            self.assertIn("results", summary)
        finally:
            run_all_domains.OUTPUT_DIR = original_output


if __name__ == "__main__":
    unittest.main(verbosity=2)
