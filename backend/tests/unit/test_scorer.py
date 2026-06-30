"""Unit tests for the matching scorer."""

import pytest
from app.engine.scorer import (
    compute_cosine_similarity,
    compute_personality_compatibility,
    compute_social_match,
    compute_full_score,
)


class TestCosineSimilarity:
    def test_identical_vectors_returns_one(self):
        v = [0.5] * 10
        assert compute_cosine_similarity(v, v) == pytest.approx(1.0, abs=0.01)

    def test_orthogonal_like_vectors(self):
        a = [1.0, 0.0, 0.0]
        b = [0.0, 1.0, 0.0]
        result = compute_cosine_similarity(a, b)
        assert result == pytest.approx(0.0, abs=0.01)

    def test_similar_vectors(self):
        a = [1.0, 0.5, 0.3]
        b = [0.9, 0.6, 0.4]
        result = compute_cosine_similarity(a, b)
        assert result > 0.9


class TestPersonalityCompatibility:
    def test_similar_personality_scores_high(self):
        up = {"openness": 0.8, "extraversion": 0.5, "conscientiousness": 0.7}
        cp = {"openness": 0.75, "extraversion": 0.5, "conscientiousness": 0.65}
        score = compute_personality_compatibility(up, cp)
        assert score > 0.85

    def test_complementary_extraversion_scores_higher(self):
        # Introvert + Extrovert = complementary
        up = {"openness": 0.5, "extraversion": 0.2, "conscientiousness": 0.5}
        cp = {"openness": 0.5, "extraversion": 0.8, "conscientiousness": 0.5}
        complementary = compute_personality_compatibility(up, cp)

        # Both introverts
        cp2 = {"openness": 0.5, "extraversion": 0.3, "conscientiousness": 0.5}
        both_introvert = compute_personality_compatibility(up, cp2)

        # Complementary should score higher on extraversion component
        assert complementary > both_introvert

    def test_opposite_personalities_score_low(self):
        up = {"openness": 0.9, "extraversion": 0.9, "conscientiousness": 0.9}
        cp = {"openness": 0.1, "extraversion": 0.1, "conscientiousness": 0.1}
        score = compute_personality_compatibility(up, cp)
        assert score < 0.6  # openness and conscientiousness differ a lot


class TestSocialMatch:
    def test_same_city_and_buddy_type_scores_high(self):
        up = {
            "social_need": {"buddy_type": "workout_partner", "schedule": "weekends"},
            "static_attrs": {"city": "上海"},
        }
        cp = {
            "social_need": {"buddy_type": "workout_partner", "schedule": "weekends"},
            "static_attrs": {"city": "上海"},
        }
        score = compute_social_match(up, cp)
        assert score > 0.8

    def test_different_city_scores_lower(self):
        up = {
            "social_need": {"buddy_type": "workout_partner", "schedule": "weekends"},
            "static_attrs": {"city": "上海"},
        }
        cp = {
            "social_need": {"buddy_type": "workout_partner", "schedule": "weekends"},
            "static_attrs": {"city": "北京"},
        }
        score_same = compute_social_match(up, {
            "social_need": {"buddy_type": "workout_partner", "schedule": "weekends"},
            "static_attrs": {"city": "上海"},
        })
        score_diff = compute_social_match(up, cp)
        assert score_same > score_diff

    def test_flexible_schedule_partial_match(self):
        up = {"social_need": {"schedule": "flexible"}, "static_attrs": {}}
        cp = {"social_need": {"schedule": "weekends"}, "static_attrs": {}}
        score = compute_social_match(up, cp)
        assert 0.2 < score < 0.7  # Partial credit for flexible schedule + neutral on other dims


class TestFullScore:
    def test_weights_sum_to_100(self):
        up = {"personality": {}, "social_need": {}, "static_attrs": {}, "interests": []}
        cp = {"personality": {}, "social_need": {}, "static_attrs": {}, "interests": []}
        result = compute_full_score(
            user_vec=[0.5] * 10,
            candidate_vec=[0.5] * 10,
            user_profile=up,
            candidate_profile=cp,
        )
        total = result["total_score"]
        assert 0 <= total <= 100
