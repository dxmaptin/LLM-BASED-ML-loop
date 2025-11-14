"""
Agent 2: Class-Specific Pattern Discovery Agent

Analyzes each individual demographic class to discover unique patterns and behaviors
that should be encoded in class-specific prompts.
"""

import pandas as pd
import json
from pathlib import Path
from typing import Dict, List, Any

from .data_prep import ACORNDataLoader, summarize_question_responses
from ..common.llm_providers import call_llm_provider


class ClassSpecificAgent:
    """
    Agent 2: Discovers unique patterns for each demographic class.

    This agent analyzes each class individually to find:
    1. Unique behavioral patterns for that demographic
    2. Deviations from overall averages
    3. Class-specific calibrations
    4. Specific scenarios/patterns unique to this group
    """

    def __init__(self, data_loader: ACORNDataLoader, model: str = "gpt-5"):
        """
        Initialize Class-Specific Pattern Agent.

        Args:
            data_loader: Configured ACORNDataLoader instance
            model: LLM model to use for pattern analysis
        """
        self.data_loader = data_loader
        self.model = model
        self.all_data = None
        self.overall_stats = {}

    def discover_class_patterns(self, class_name: str) -> Dict[str, Any]:
        """
        Discover patterns for a specific class.

        Args:
            class_name: Name of ACORN class to analyze

        Returns:
            Dictionary with class-specific patterns
        """
        print(f"\n{'='*80}")
        print(f"AGENT 2: CLASS-SPECIFIC PATTERN DISCOVERY - {class_name}")
        print(f"{'='*80}")

        # Load class data
        print(f"\n[1/5] Loading data for {class_name}...")
        class_data = self.data_loader.load_class_data(class_name, include_holdout=False)
        profile = self.data_loader.load_class_profile(class_name)
        print(f"  Loaded {len(class_data)} rows")

        # Load all data for comparison (lazy load)
        if self.all_data is None:
            print(f"[2/5] Loading all data for comparison...")
            self.all_data = self.data_loader.load_all_classes(include_holdout=False)
            self._compute_overall_stats()
        else:
            print(f"[2/5] Using cached data for comparison...")

        # Step 3: Find class-specific deviations
        print(f"[3/5] Finding deviations from overall averages...")
        deviations = self._find_deviations(class_name, class_data)
        print(f"  Found {len(deviations)} significant deviations")

        # Step 4: Analyze key characteristics
        print(f"[4/5] Analyzing key characteristics...")
        characteristics = self._analyze_class_characteristics(class_data, profile)

        # Step 5: Generate class-specific rules via LLM
        print(f"[5/5] Synthesizing class-specific rules with LLM...")
        class_rules = self._synthesize_class_rules(
            class_name,
            profile,
            deviations,
            characteristics
        )

        # Compile patterns
        patterns = {
            "class_name": class_name,
            "deviations": deviations,
            "characteristics": characteristics,
            "class_specific_rules": class_rules,
            "metadata": {
                "total_rows": len(class_data),
                "unique_questions": class_data['Question'].nunique(),
                "profile_length": len(profile)
            }
        }

        return patterns

    def _compute_overall_stats(self):
        """Compute overall statistics for comparison."""
        print("  Computing overall statistics...")

        # Group by question and compute mean values
        for question in self.all_data['Question'].unique():
            q_data = self.all_data[self.all_data['Question'] == question].copy()
            q_data['Value'] = pd.to_numeric(q_data['Value'], errors='coerce')
            q_data = q_data.dropna(subset=['Value'])

            if len(q_data) > 0:
                self.overall_stats[question] = {
                    "mean": float(q_data['Value'].mean()),
                    "std": float(q_data['Value'].std()) if len(q_data) > 1 else 0,
                    "min": float(q_data['Value'].min()),
                    "max": float(q_data['Value'].max())
                }

        print(f"  Computed stats for {len(self.overall_stats)} questions")

    def _find_deviations(self, class_name: str, class_data: pd.DataFrame) -> List[Dict]:
        """Find where this class deviates significantly from overall average."""
        deviations = []

        # Group by question
        for question in class_data['Question'].unique():
            q_data = class_data[class_data['Question'] == question].copy()
            q_data['Value'] = pd.to_numeric(q_data['Value'], errors='coerce')
            q_data = q_data.dropna(subset=['Value'])

            if len(q_data) == 0 or question not in self.overall_stats:
                continue

            class_mean = q_data['Value'].mean()
            overall_mean = self.overall_stats[question]['mean']
            overall_std = self.overall_stats[question]['std']

            # Calculate deviation in standard deviations
            if overall_std > 0:
                deviation_std = (class_mean - overall_mean) / overall_std
            else:
                deviation_std = 0

            # Also calculate absolute percentage difference
            abs_diff = abs(class_mean - overall_mean)

            # Significant if: >1 std away OR >10pp difference
            if abs(deviation_std) > 1.0 or abs_diff > 0.10:
                deviations.append({
                    "question": question,
                    "class_value": float(class_mean),
                    "overall_value": float(overall_mean),
                    "difference": float(class_mean - overall_mean),
                    "difference_pp": float((class_mean - overall_mean) * 100),
                    "std_deviations": float(deviation_std),
                    "direction": "higher" if class_mean > overall_mean else "lower",
                    "category": q_data['Category'].iloc[0] if 'Category' in q_data.columns else "Unknown"
                })

        # Sort by absolute std deviation
        deviations.sort(key=lambda x: abs(x['std_deviations']), reverse=True)

        return deviations[:30]  # Top 30 deviations

    def _analyze_class_characteristics(self, class_data: pd.DataFrame, profile: str) -> Dict[str, Any]:
        """Extract key characteristics from class data."""

        characteristics = {}

        # Age distribution
        age_data = class_data[class_data['Question'] == 'Age'].copy()
        if len(age_data) > 0:
            age_data['Value'] = pd.to_numeric(age_data['Value'], errors='coerce')
            age_data = age_data.dropna(subset=['Value'])
            if len(age_data) > 0:
                top_ages = age_data.nlargest(3, 'Value')[['Answer', 'Value']].to_dict('records')
                characteristics['age_profile'] = top_ages

        # Income indicators (from Economy category)
        income_data = class_data[class_data['Category'] == 'Economy']
        if len(income_data) > 0:
            characteristics['income_indicators'] = {
                "count": len(income_data),
                "sample_questions": income_data['Question'].unique()[:5].tolist()
            }

        # Digital behavior
        digital_data = class_data[class_data['Category'] == 'Digital']
        if len(digital_data) > 0:
            digital_data['Value'] = pd.to_numeric(digital_data['Value'], errors='coerce')
            digital_data = digital_data.dropna(subset=['Value'])
            if len(digital_data) > 0:
                characteristics['digital_adoption'] = {
                    "mean": float(digital_data['Value'].mean()),
                    "count": len(digital_data)
                }

        # Lifestyle indicators
        lifestyle_data = class_data[class_data['Category'] == 'Lifestyle']
        if len(lifestyle_data) > 0:
            characteristics['lifestyle_indicators'] = {
                "count": len(lifestyle_data),
                "sample_questions": lifestyle_data['Question'].unique()[:5].tolist()
            }

        # Profile summary
        characteristics['profile_snippet'] = profile[:1000] if len(profile) > 1000 else profile

        return characteristics

    def _synthesize_class_rules(
        self,
        class_name: str,
        profile: str,
        deviations: List[Dict],
        characteristics: Dict
    ) -> Dict[str, Any]:
        """Synthesize class-specific rules using LLM."""

        prompt = f"""You are creating DEMOGRAPHIC-SPECIFIC CALIBRATION RULES for the class: {class_name}

QUALITATIVE PROFILE:
{profile[:2000]}

KEY CHARACTERISTICS:
{json.dumps(characteristics, indent=2)}

SIGNIFICANT DEVIATIONS FROM OVERALL AVERAGE:
(Where this class differs most from other demographics)
{json.dumps(deviations[:20], indent=2)}

TASK: Create specific calibration rules for this demographic class.

Based on the profile and deviations, identify:

1. **Demographic Profile Summary** (2-3 sentences):
   - Age, income, key lifestyle characteristics
   - Core identity and values

2. **Specific Behavioral Patterns**:
   - Digital behaviors: Are they tech-savvy or hesitant?
   - Financial attitudes: Conservative or risk-taking? Price-conscious?
   - Environmental/social values: High or low priority?
   - Shopping behaviors: Premium or budget?

3. **Calibration Rules** (be specific with numbers):
   - For each major category (Digital, Financial, Environmental, Lifestyle):
     - Should predictions be LIFTED or REDUCED?
     - By how many percentage points?
     - Example: "Digital banking behaviors: LIFT by +20pp (tech-savvy segment)"

4. **Unique Patterns/Scenarios**:
   - Any specific scenarios where this demographic behaves uniquely?
   - Example: "High environmental concern but low action" or "Budget-conscious but willing to pay for quality"

Output JSON format:
{{
  "profile_summary": "2-3 sentence description",
  "behavioral_patterns": {{
    "digital_adoption": "high/medium/low - reasoning",
    "financial_attitudes": "description",
    "environmental_values": "description",
    "shopping_style": "description"
  }},
  "calibration_rules": {{
    "digital_behaviors": {{"adjustment": "+20pp", "reasoning": "..."}},
    "financial_behaviors": {{"adjustment": "-10pp", "reasoning": "..."}},
    "environmental_actions": {{"adjustment": "+15pp", "reasoning": "..."}},
    "lifestyle_preferences": {{"adjustment": "0pp", "reasoning": "..."}}
  }},
  "unique_patterns": [
    "Pattern 1 description",
    "Pattern 2 description"
  ],
  "example_scenarios": [
    {{"concept": "Example concept", "expected_response": "High/Low/Moderate", "reasoning": "..."}}
  ]
}}
"""

        response = call_llm_provider(
            system_prompt="You are creating demographic-specific calibration rules for prediction agents.",
            user_prompt=prompt,
            model=self.model,
            temperature=0.2,
            max_tokens=3000
        )

        try:
            return json.loads(response) if isinstance(response, str) else response
        except:
            return {"raw_response": str(response)}

    def discover_all_classes(self, output_dir: Path = None) -> Dict[str, Dict]:
        """
        Discover patterns for all classes.

        Args:
            output_dir: Where to save individual class pattern files

        Returns:
            Dictionary mapping class_name to patterns
        """
        all_classes = self.data_loader.get_all_class_names()
        all_patterns = {}

        print(f"\n{'='*80}")
        print(f"DISCOVERING PATTERNS FOR {len(all_classes)} CLASSES")
        print(f"{'='*80}")

        for i, class_name in enumerate(all_classes, 1):
            print(f"\n[{i}/{len(all_classes)}] Processing {class_name}...")

            try:
                patterns = self.discover_class_patterns(class_name)
                all_patterns[class_name] = patterns

                # Save individual file if output_dir provided
                if output_dir:
                    output_dir.mkdir(parents=True, exist_ok=True)
                    output_file = output_dir / f"{class_name}_patterns.json"
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(patterns, f, indent=2)
                    print(f"  Saved to: {output_file.name}")

            except Exception as e:
                print(f"  ERROR processing {class_name}: {e}")
                all_patterns[class_name] = {"error": str(e)}

        return all_patterns


if __name__ == "__main__":
    # Test the class-specific agent
    loader = ACORNDataLoader(Path("demographic_runs_ACORN"))
    agent = ClassSpecificAgent(loader, model="gpt-5")

    # Test on one class
    patterns = agent.discover_class_patterns("exclusive_addresses")

    print("\n" + "="*80)
    print("SAMPLE CLASS PATTERNS")
    print("="*80)
    print(json.dumps({
        "class_name": patterns["class_name"],
        "deviation_count": len(patterns["deviations"]),
        "top_3_deviations": patterns["deviations"][:3],
        "rules_generated": "class_specific_rules" in patterns
    }, indent=2))
