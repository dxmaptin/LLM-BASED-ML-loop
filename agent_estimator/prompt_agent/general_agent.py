"""
Agent 1: General Pattern Discovery Agent

Analyzes ALL CSV responses across all demographics to discover universal patterns
that should be encoded in the general system prompt.
"""

import pandas as pd
import json
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict

from .data_prep import ACORNDataLoader, summarize_question_responses
from ..common.llm_providers import call_llm_provider


class GeneralPatternAgent:
    """
    Agent 1: Discovers universal patterns across all demographics.

    This agent analyzes the entire dataset to find:
    1. Concept type patterns (attitude vs behavior vs identity)
    2. Universal calibration rules (proximal guardrails, evidence hierarchy)
    3. Cross-demographic patterns (age, income, lifestyle effects)
    4. Range classification rules (when to predict high/low/moderate)
    """

    def __init__(self, data_loader: ACORNDataLoader, model: str = "gpt-5"):
        """
        Initialize General Pattern Agent.

        Args:
            data_loader: Configured ACORNDataLoader instance
            model: LLM model to use for pattern analysis
        """
        self.data_loader = data_loader
        self.model = model
        self.train_data = None
        self.patterns = {}

    def discover_patterns(self) -> Dict[str, Any]:
        """
        Main analysis function - discovers all universal patterns.

        Returns:
            Dictionary with discovered patterns
        """
        print("\n" + "="*80)
        print("AGENT 1: GENERAL PATTERN DISCOVERY")
        print("="*80)

        # Load training data (excluding holdout questions)
        print("\n[1/6] Loading training data...")
        self.train_data = self.data_loader.load_all_classes(include_holdout=False)
        print(f"  Loaded {len(self.train_data)} rows from {self.train_data['class_name'].nunique()} classes")
        print(f"  Unique questions: {self.train_data['Question'].nunique()}")

        # Step 1: Identify high-variance questions
        print("\n[2/6] Identifying high-variance questions...")
        high_variance = self._find_high_variance_questions()
        print(f"  Found {len(high_variance)} high-variance questions")

        # Step 2: Analyze concept types
        print("\n[3/6] Analyzing concept type patterns...")
        concept_patterns = self._analyze_concept_types()

        # Step 3: Analyze response distributions
        print("\n[4/6] Analyzing response distribution patterns...")
        distribution_patterns = self._analyze_distributions()

        # Step 5: Analyze demographic factors
        print("\n[5/6] Analyzing demographic factor patterns...")
        demographic_patterns = self._analyze_demographic_factors()

        # Step 6: Generate general rules via LLM
        print("\n[6/6] Synthesizing universal rules with LLM...")
        general_rules = self._synthesize_general_rules(
            high_variance,
            concept_patterns,
            distribution_patterns,
            demographic_patterns
        )

        # Compile all patterns
        self.patterns = {
            "high_variance_questions": high_variance,
            "concept_type_patterns": concept_patterns,
            "distribution_patterns": distribution_patterns,
            "demographic_patterns": demographic_patterns,
            "general_rules": general_rules,
            "metadata": {
                "total_rows": len(self.train_data),
                "total_classes": self.train_data['class_name'].nunique(),
                "unique_questions": self.train_data['Question'].nunique(),
                "categories": self.train_data['Category'].unique().tolist()
            }
        }

        print("\n" + "="*80)
        print("PATTERN DISCOVERY COMPLETE")
        print("="*80)

        return self.patterns

    def _find_high_variance_questions(self) -> List[Dict]:
        """Find questions that vary significantly across demographics."""
        high_variance = []

        # Group by question and analyze variance
        for question in self.train_data['Question'].unique():
            q_data = self.train_data[self.train_data['Question'] == question].copy()

            # Only analyze questions with Value column
            if 'Value' not in q_data.columns:
                continue

            q_data['Value'] = pd.to_numeric(q_data['Value'], errors='coerce')
            q_data = q_data.dropna(subset=['Value'])

            if len(q_data) < 5:  # Need at least 5 data points
                continue

            variance = q_data['Value'].var()
            mean = q_data['Value'].mean()
            std = q_data['Value'].std()

            # High variance threshold: std > 0.15 or variance > 0.02
            if std > 0.15 or variance > 0.02:
                high_variance.append({
                    "question": question,
                    "variance": float(variance),
                    "std": float(std),
                    "mean": float(mean),
                    "min": float(q_data['Value'].min()),
                    "max": float(q_data['Value'].max()),
                    "category": q_data['Category'].iloc[0] if 'Category' in q_data.columns else "Unknown",
                    "classes_with_data": int(q_data['class_name'].nunique())
                })

        # Sort by variance descending
        high_variance.sort(key=lambda x: x['variance'], reverse=True)

        return high_variance[:50]  # Top 50

    def _analyze_concept_types(self) -> Dict[str, Any]:
        """Analyze patterns by concept type (attitude, behavior, identity)."""

        # Sample questions from different categories for LLM analysis
        categories = self.train_data['Category'].unique()
        sample_by_category = {}

        for category in categories:
            cat_data = self.train_data[self.train_data['Category'] == category]
            questions = cat_data['Question'].unique()[:5]  # Top 5 questions per category

            sample_by_category[category] = [
                {
                    "question": q,
                    "summary": summarize_question_responses(self.train_data, q)
                }
                for q in questions
            ]

        # Use LLM to discover concept type patterns
        prompt = f"""You are analyzing survey data to discover patterns in how people respond to different types of questions.

CATEGORIES AND SAMPLE QUESTIONS:
{json.dumps(sample_by_category, indent=2)[:8000]}

TASK: Identify concept-type patterns that apply universally across all demographics.

Analyze and classify questions into types:
1. **ATTITUDE questions**: Opinions, beliefs, values (e.g., "I care about X", "X is important")
2. **BEHAVIOR questions - Low friction**: Easy actions (e.g., "I use X", "I browse X")
3. **BEHAVIOR questions - High friction**: Difficult actions (e.g., "I switched to X", "I invested in X")
4. **IDENTITY questions**: Self-perception (e.g., "I am X", "I consider myself X")

For each type, identify:
- Typical response distribution patterns
- Average agreement levels
- When people tend to be neutral vs strongly agree/disagree

Output JSON format:
{{
  "attitude_questions": {{
    "characteristics": ["..."],
    "typical_distribution": "SA X%, A Y%, N Z%, D W%, SD V%",
    "avg_agreement_range": "X-Y%",
    "calibration_rules": ["rule 1", "rule 2"]
  }},
  "behavior_low_friction": {{...}},
  "behavior_high_friction": {{...}},
  "identity_questions": {{...}},
  "classification_guidelines": ["How to identify each type..."]
}}
"""

        try:
            response = call_llm_provider(
                system_prompt="You are a data analyst discovering universal patterns in survey response data. You MUST respond with valid JSON only.",
                user_prompt=prompt,
                model=self.model,
                temperature=0.3,
                max_tokens=3000
            )
            return json.loads(response) if isinstance(response, str) else response
        except Exception as e:
            print(f"  Warning: LLM response parsing failed: {e}")
            return {"error": str(e), "raw_response": "Failed to get response"}

    def _analyze_distributions(self) -> Dict[str, Any]:
        """Analyze overall response distribution patterns."""

        # Calculate statistics on answer distributions
        # Find questions with "Answer" field that looks like Likert scales
        likert_keywords = ['Strongly Agree', 'Agree', 'Neither', 'Disagree', 'Strongly Disagree',
                           'Very', 'Somewhat', 'Not at all']

        likert_questions = []
        for question in self.train_data['Question'].unique()[:100]:  # Sample
            q_data = self.train_data[self.train_data['Question'] == question]

            if 'Answer' not in q_data.columns:
                continue

            answers = q_data['Answer'].unique()
            if any(keyword in str(answer) for answer in answers for keyword in likert_keywords):
                summary = summarize_question_responses(self.train_data, question)
                likert_questions.append(summary)

        # Use LLM to find distribution patterns
        prompt = f"""You are analyzing response distribution patterns in survey data.

SAMPLE LIKERT-SCALE QUESTIONS:
{json.dumps(likert_questions[:20], indent=2)}

TASK: Identify universal patterns in how responses are distributed.

Analyze:
1. What is the typical distribution shape? (normal, skewed, bimodal, etc.)
2. When do responses cluster around "Agree" vs "Neutral"?
3. Are there patterns in Strong Agreement vs Moderate Agreement?
4. How much neutral response is typical for different question types?

Output JSON format:
{{
  "typical_patterns": {{
    "high_agreement_questions": "Description and typical % distribution",
    "moderate_agreement_questions": "...",
    "low_agreement_questions": "...",
    "high_neutral_questions": "..."
  }},
  "distribution_rules": [
    "When X, expect distribution like Y",
    "..."
  ],
  "extremes_handling": "When to predict 80%+ or 20%- agreement"
}}
"""

        try:
            response = call_llm_provider(
                system_prompt="You are analyzing response distribution patterns. You MUST respond with valid JSON only.",
                user_prompt=prompt,
                model=self.model,
                temperature=0.3,
                max_tokens=2000
            )
            return json.loads(response) if isinstance(response, str) else response
        except Exception as e:
            print(f"  Warning: LLM response parsing failed: {e}")
            return {"error": str(e), "raw_response": "Failed to get response"}

    def _analyze_demographic_factors(self) -> Dict[str, Any]:
        """Analyze how demographic factors influence responses."""

        # Load qualitative profiles for context
        all_classes = self.data_loader.get_all_class_names()

        # Sample profiles from different economic segments
        sample_profiles = {}
        wealth_classes = ['exclusive_addresses', 'flourishing_capital', 'limited_budgets',
                         'challenging_circumstances', 'up-and-coming_urbanites']

        for class_name in wealth_classes:
            if class_name in all_classes:
                profile = self.data_loader.load_class_profile(class_name)
                sample_profiles[class_name] = profile[:1500]  # First 1500 chars

        # Use LLM to discover demographic patterns
        prompt = f"""You are analyzing how demographic factors influence survey responses across all demographics.

SAMPLE DEMOGRAPHIC PROFILES:
{json.dumps(sample_profiles, indent=2)}

HIGH-VARIANCE QUESTIONS (differ most across demographics):
{json.dumps(self.patterns.get('high_variance_questions', [])[:15], indent=2)}

TASK: Identify universal demographic patterns that affect responses.

Analyze:
1. **Income/Wealth patterns**: How do wealthy vs budget-constrained demographics differ?
2. **Age patterns**: How do younger vs older demographics differ?
3. **Location patterns**: Urban vs rural differences?
4. **Lifecycle patterns**: Families vs singles vs retirees?

For each factor, provide:
- General trend description
- Specific calibration guidelines (e.g., "+15pp for digital behaviors if age<35")
- Which question categories are most affected

Output JSON format:
{{
  "income_wealth_patterns": {{
    "high_income": {{"description": "...", "calibrations": ["...", "..."]}},
    "low_income": {{"description": "...", "calibrations": ["...", "..."]}}
  }},
  "age_patterns": {{
    "young": {{"description": "...", "calibrations": [...]}},
    "middle_aged": {{"description": "...", "calibrations": [...]}},
    "elderly": {{"description": "...", "calibrations": [...]}}
  }},
  "lifestyle_patterns": {{
    "urban_professional": {{"description": "...", "calibrations": [...]}},
    "families": {{"description": "...", "calibrations": [...]}},
    "retirees": {{"description": "...", "calibrations": [...]}}
  }},
  "key_differentiators": ["Factor 1", "Factor 2", ...]
}}
"""

        try:
            response = call_llm_provider(
                system_prompt="You are analyzing demographic patterns in survey data. You MUST respond with valid JSON only.",
                user_prompt=prompt,
                model=self.model,
                temperature=0.3,
                max_tokens=3000
            )
            return json.loads(response) if isinstance(response, str) else response
        except Exception as e:
            print(f"  Warning: LLM response parsing failed: {e}")
            return {"error": str(e), "raw_response": "Failed to get response"}

    def _synthesize_general_rules(
        self,
        high_variance: List[Dict],
        concept_patterns: Dict,
        distribution_patterns: Dict,
        demographic_patterns: Dict
    ) -> Dict[str, Any]:
        """Synthesize all patterns into actionable general rules."""

        prompt = f"""You are synthesizing universal rules for a prediction system that estimates survey responses.

INPUT PATTERNS DISCOVERED:

1. HIGH-VARIANCE QUESTIONS (differ most across demographics):
{json.dumps(high_variance[:10], indent=2)}

2. CONCEPT TYPE PATTERNS:
{json.dumps(concept_patterns, indent=2)}

3. DISTRIBUTION PATTERNS:
{json.dumps(distribution_patterns, indent=2)}

4. DEMOGRAPHIC PATTERNS:
{json.dumps(demographic_patterns, indent=2)}

TASK: Synthesize these patterns into a comprehensive set of UNIVERSAL RULES for prediction.

Create rules in these categories:

1. **CONCEPT TYPE CLASSIFICATION**: How to identify attitude/behavior/identity questions
2. **CONCEPT TYPE ALLOCATION**: Base distribution templates for each type
3. **PROXIMAL GUARDRAILS**: Rules when exact/similar data is available
4. **DEMOGRAPHIC CALIBRATIONS**: General adjustments based on demographics
5. **EVIDENCE HIERARCHY**: How to weight different evidence types
6. **RANGE CLASSIFICATION**: When to predict high (70%+), moderate (40-70%), or low (<40%) agreement
7. **CONFLICT HANDLING**: What to do when signals contradict

For each rule:
- Be specific with percentage adjustments (e.g., "+15pp", "REDUCE by 20pp")
- Provide reasoning based on discovered patterns
- Make it actionable and clear

Output JSON format:
{{
  "concept_classification": {{
    "attitude": {{"criteria": [...], "examples": [...]}},
    "behavior_low": {{"criteria": [...], "examples": [...]}},
    "behavior_high": {{"criteria": [...], "examples": [...]}},
    "identity": {{"criteria": [...], "examples": [...]}}
  }},
  "base_distributions": {{
    "attitude": "SA X%, A Y%, N Z%, D W%, SD V%",
    "behavior_low": "...",
    "behavior_high": "...",
    "identity": "..."
  }},
  "proximal_guardrails": [
    "If exact data shows X%, predict Y% range",
    "..."
  ],
  "demographic_calibrations": {{
    "income": ["rule 1", "rule 2"],
    "age": ["rule 1", "rule 2"],
    "lifestyle": ["rule 1", "rule 2"]
  }},
  "evidence_hierarchy": [
    "Level 1: Exact match - weight",
    "Level 2: Similar concept - weight",
    "..."
  ],
  "range_classification": {{
    "high_agreement": "When to predict 70%+",
    "moderate": "When to predict 40-70%",
    "low_agreement": "When to predict <40%"
  }},
  "conflict_resolution": ["rule 1", "rule 2"]
}}
"""

        try:
            response = call_llm_provider(
                system_prompt="You are synthesizing universal prediction rules from discovered patterns. You MUST respond with valid JSON only.",
                user_prompt=prompt,
                model=self.model,
                temperature=0.2,
                max_tokens=4000
            )
            return json.loads(response) if isinstance(response, str) else response
        except Exception as e:
            print(f"  Warning: LLM response parsing failed: {e}")
            return {"error": str(e), "raw_response": "Failed to get response"}

    def save_patterns(self, output_file: Path):
        """Save discovered patterns to file."""
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.patterns, f, indent=2)

        print(f"\n[OK] Patterns saved to: {output_file}")


if __name__ == "__main__":
    # Test the general pattern agent
    loader = ACORNDataLoader(Path("demographic_runs_ACORN"))
    agent = GeneralPatternAgent(loader, model="gpt-5")

    patterns = agent.discover_patterns()
    agent.save_patterns(Path("agent_estimator/prompt_agent/output/general_patterns.json"))

    print("\n" + "="*80)
    print("SUMMARY OF DISCOVERED PATTERNS")
    print("="*80)
    print(json.dumps({
        "high_variance_count": len(patterns.get("high_variance_questions", [])),
        "concept_types": list(patterns.get("concept_type_patterns", {}).keys()),
        "demographic_factors": list(patterns.get("demographic_patterns", {}).keys()),
        "metadata": patterns.get("metadata", {})
    }, indent=2))
