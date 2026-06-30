"""Rule Engine — hard constraint filtering for matching candidates (FR-MD-03).

Supports hot-reload of rules from database.
"""

from typing import Any
from loguru import logger


class RuleEngine:
    """Applies hard-filter rules to candidate pool before scoring.

    Rules are loaded from the MatchingRule table and can be hot-reloaded.
    Each rule has: {name, rule_type, config: {dimension, operator, value}, enabled, priority}.
    """

    def __init__(self):
        self._rules: list[dict] = []

    def load_rules(self, rules: list[Any]) -> None:
        """Load/reload rules from DB model objects."""
        self._rules = []
        for r in rules:
            if r.rule_type == "hard_filter" and r.enabled:
                self._rules.append({
                    "name": r.name,
                    "config": r.config,
                    "priority": r.priority,
                })
        self._rules.sort(key=lambda x: x["priority"])
        logger.info(f"RuleEngine loaded {len(self._rules)} hard-filter rules")

    def get_active_rules(self) -> list[dict]:
        """Return currently active rules (for API)."""
        return [{"name": r["name"], "config": r["config"]} for r in self._rules]

    def filter_candidates(
        self,
        user_profile: dict,
        candidates: list[dict],
    ) -> tuple[list[dict], list[str]]:
        """Apply all hard-filter rules. Returns (passed_candidates, applied_filters).

        Args:
            user_profile: Dict with static_attrs, interests, preferences, social_need.
            candidates: List of candidate profile dicts with keys: id, profile_dict.

        Returns:
            (filtered_candidates, list_of_filter_names_applied)
        """
        applied: list[str] = []
        results = candidates[:]

        for rule in self._rules:
            cfg = rule["config"]
            rule_name = rule["name"]
            before = len(results)
            results = [c for c in results if self._evaluate(cfg, user_profile, c)]
            after = len(results)
            if before != after:
                applied.append(f"{rule_name} (filtered {before - after})")
                logger.debug(f"Rule '{rule_name}': {before} → {after} candidates")

        return results, applied

    def _evaluate(self, cfg: dict, user: dict, candidate: dict) -> bool:
        """Evaluate a single rule against a user-candidate pair."""
        dim = cfg.get("dimension", "")
        op = cfg.get("operator", "eq")
        val = cfg.get("value")

        cand_profile = candidate.get("profile_dict", candidate)

        if dim == "city":
            # same_city: candidate city must match user city
            user_city = user.get("static_attrs", {}).get("city", "")
            cand_city = cand_profile.get("static_attrs", {}).get("city", "")
            if op == "same_city":
                return bool(user_city and cand_city and user_city == cand_city)
            return True

        elif dim == "no_smoking":
            cand_interests = cand_profile.get("interests", [])
            smoking_tags = [
                i for i in cand_interests
                if "smoking" in str(i.get("sub_category", "")).lower()
                or "smoking" in str(i.get("category", "")).lower()
            ]
            return len(smoking_tags) == 0

        elif dim == "age_range":
            user_pref = user.get("preferences", {}).get("soft_preferences", {}).get("preferred_age_range")
            if not user_pref:
                return True
            cand_age = cand_profile.get("static_attrs", {}).get("age_range", "")
            return cand_age == user_pref

        elif dim == "gender":
            user_pref = user.get("preferences", {}).get("soft_preferences", {}).get("preferred_gender")
            if not user_pref or user_pref == "any":
                return True
            cand_gender = cand_profile.get("static_attrs", {}).get("gender", "")
            return cand_gender == user_pref

        elif dim == "buddy_type":
            user_need = user.get("social_need", {}).get("buddy_type", "")
            cand_need = cand_profile.get("social_need", {}).get("buddy_type", "")
            if not user_need or not cand_need:
                return True
            return user_need == cand_need

        # Custom rule: evaluate using operator
        cand_val = self._get_nested(cand_profile, dim)
        if cand_val is None:
            return True  # Can't evaluate → pass

        match op:
            case "eq":
                return cand_val == val
            case "neq":
                return cand_val != val
            case "contains":
                return val in str(cand_val) if cand_val else False
            case "not_contains":
                return val not in str(cand_val) if cand_val else True
            case "gte":
                return float(cand_val) >= float(val)
            case "lte":
                return float(cand_val) <= float(val)
            case _:
                return True

    @staticmethod
    def _get_nested(d: dict, path: str) -> Any:
        """Get nested dict value by dot-separated path."""
        keys = path.split(".")
        for k in keys:
            if isinstance(d, dict):
                d = d.get(k)
            else:
                return None
        return d


# Singleton
_rule_engine: RuleEngine | None = None


def get_rule_engine() -> RuleEngine:
    global _rule_engine
    if _rule_engine is None:
        _rule_engine = RuleEngine()
    return _rule_engine
