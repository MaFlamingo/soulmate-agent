"""Unit tests for the rule engine."""

import pytest
from app.engine.rule_engine import RuleEngine


class MockRule:
    def __init__(self, name, rule_type, config, enabled=True, priority=0):
        self.name = name
        self.rule_type = rule_type
        self.config = config
        self.enabled = enabled
        self.priority = priority


class TestRuleEngine:
    @pytest.fixture
    def engine(self):
        return RuleEngine()

    @pytest.fixture
    def user_profile(self):
        return {
            "static_attrs": {"city": "上海", "age_range": "25-30", "gender": "male"},
            "interests": [],
            "social_need": {"buddy_type": "hobby_partner"},
            "preferences": {"soft_preferences": {"preferred_gender": "female"}},
        }

    def test_same_city_filter_removes_different_city(self, engine, user_profile):
        rules = [
            MockRule("same_city", "hard_filter",
                     {"dimension": "city", "operator": "same_city"})
        ]
        engine.load_rules(rules)

        candidates = [
            {"id": 1, "profile_dict": {"static_attrs": {"city": "上海"}}},
            {"id": 2, "profile_dict": {"static_attrs": {"city": "北京"}}},
            {"id": 3, "profile_dict": {"static_attrs": {"city": "上海"}}},
        ]

        filtered, applied = engine.filter_candidates(user_profile, candidates)
        assert len(filtered) == 2
        assert filtered[0]["id"] == 1
        assert filtered[1]["id"] == 3
        assert len(applied) == 1

    def test_smoking_filter_removes_smokers(self, engine, user_profile):
        rules = [
            MockRule("no_smoking", "hard_filter",
                     {"dimension": "no_smoking", "operator": "eq", "value": True})
        ]
        engine.load_rules(rules)

        candidates = [
            {"id": 1, "profile_dict": {"interests": [
                {"category": "lifestyle", "sub_category": "smoking", "weight": 0.5}
            ]}},
            {"id": 2, "profile_dict": {"interests": [
                {"category": "outdoor", "sub_category": "hiking"}
            ]}},
        ]

        filtered, _ = engine.filter_candidates(user_profile, candidates)
        assert len(filtered) == 1
        assert filtered[0]["id"] == 2

    def test_empty_rules_passes_all(self, engine, user_profile):
        engine.load_rules([])
        candidates = [
            {"id": 1, "profile_dict": {}},
            {"id": 2, "profile_dict": {}},
        ]
        filtered, _ = engine.filter_candidates(user_profile, candidates)
        assert len(filtered) == 2

    def test_disabled_rule_not_applied(self, engine, user_profile):
        rules = [
            MockRule("same_city", "hard_filter",
                     {"dimension": "city", "operator": "same_city"}, enabled=False)
        ]
        engine.load_rules(rules)

        candidates = [
            {"id": 1, "profile_dict": {"static_attrs": {"city": "上海"}}},
            {"id": 2, "profile_dict": {"static_attrs": {"city": "北京"}}},
        ]

        filtered, _ = engine.filter_candidates(user_profile, candidates)
        assert len(filtered) == 2  # Disabled rule doesn't filter

    def test_gender_preference_filter(self, engine, user_profile):
        rules = [
            MockRule("gender_pref", "hard_filter",
                     {"dimension": "gender", "operator": "eq", "value": "female"})
        ]
        engine.load_rules(rules)

        candidates = [
            {"id": 1, "profile_dict": {"static_attrs": {"gender": "female"}}},
            {"id": 2, "profile_dict": {"static_attrs": {"gender": "male"}}},
            {"id": 3, "profile_dict": {"static_attrs": {"gender": "female"}}},
        ]

        filtered, _ = engine.filter_candidates(user_profile, candidates)
        assert len(filtered) == 2
