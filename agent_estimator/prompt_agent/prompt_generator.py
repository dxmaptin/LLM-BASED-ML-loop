"""
Prompt Generator

Uses outputs from Agent 1 (General Patterns) and Agent 2 (Class-Specific Patterns)
to generate the actual prompt files:
- general_system_prompt.txt
- class-specific prompt files (one per demographic)
"""

import json
from pathlib import Path
from typing import Dict, Any

from ..common.llm_providers import call_llm_provider


class PromptGenerator:
    """
    Generates actual prompt files from discovered patterns.
    """

    def __init__(self, model: str = "gpt-5"):
        """
        Initialize Prompt Generator.

        Args:
            model: LLM model to use for prompt generation
        """
        self.model = model

    def generate_general_prompt(self, general_patterns: Dict[str, Any]) -> str:
        """
        Generate the general system prompt from Agent 1's patterns.

        Args:
            general_patterns: Output from GeneralPatternAgent

        Returns:
            General system prompt text
        """
        print("\n" + "="*80)
        print("GENERATING GENERAL SYSTEM PROMPT")
        print("="*80)

        prompt = f"""You are generating the GENERAL SYSTEM PROMPT for an AI prediction agent.

This prompt will be used by the Estimator Agent to predict survey responses (5-point Likert distributions).

INPUT: Discovered patterns from analyzing the entire dataset:

GENERAL RULES:
{json.dumps(general_patterns.get('general_rules', {}), indent=2)}

CONCEPT TYPE PATTERNS:
{json.dumps(general_patterns.get('concept_type_patterns', {}), indent=2)}

DISTRIBUTION PATTERNS:
{json.dumps(general_patterns.get('distribution_patterns', {}), indent=2)}

DEMOGRAPHIC PATTERNS:
{json.dumps(general_patterns.get('demographic_patterns', {}), indent=2)}

METADATA:
{json.dumps(general_patterns.get('metadata', {}), indent=2)}

TASK: Generate a comprehensive GENERAL SYSTEM PROMPT following this structure:

```
You estimate 5-point Likert distributions for statements using the segment context I provide.
Return only the final distributions and short rationales—do not reveal internal reasoning or intermediate steps.

# Objectives
- Output a plausible percentage distribution over 5 Likert categories (SA/A/N/SD/SDD) that sums to 100%.
- Provide a 1-3 sentence rationale citing evidence.
- Follow the decision workflow below systematically.

# Decision Workflow (apply in order)

## Step 1: Concept Type Classification
[Rules for identifying attitude vs behavior vs identity based on discovered patterns]

## Step 2: Base Distribution by Type
[Distribution templates for each concept type based on discovered patterns]

## Step 3: Proximal Evidence Evaluation
[Rules for handling exact/similar data matches based on discovered patterns]

## Step 4: Demographic Calibrations
[General rules for age, income, lifestyle adjustments based on discovered patterns]

## Step 5: Range Classification
[Rules for when to predict high/moderate/low agreement based on discovered patterns]

## Step 6: Evidence Hierarchy
[How to weight different evidence types based on discovered patterns]

## Step 7: Conflict Handling
[What to do when signals contradict based on discovered patterns]

## Step 8: Final Distribution Generation
[Rules for generating the final distribution]

# Output Format
Return JSON with:
- distribution: {{SA: X%, A: Y%, N: Z%, D: W%, SD: V%}}
- rationale: 1-3 sentences
- confidence: 0-100
```

IMPORTANT:
- Use the discovered patterns to populate each step with SPECIFIC, ACTIONABLE rules
- Include percentage adjustments (e.g., "+15pp", "REDUCE by 20pp")
- Keep it under 4000 words
- Make rules clear and unambiguous
- Base everything on the discovered patterns, not generic advice

Output the complete prompt as plain text (not JSON).
"""

        print("  Calling LLM to generate prompt...")

        # Use direct API call since we want text, not JSON
        from ..common.llm_providers import call_openai_api
        response_obj = call_openai_api(
            system_prompt="You are an expert prompt engineer creating system prompts for AI prediction agents.",
            user_prompt=prompt,
            model=self.model,
            temperature=0.2,
            max_tokens=4500
        )

        prompt_text = response_obj.content

        print(f"  Generated prompt: {len(prompt_text)} characters")

        return prompt_text

    def generate_class_specific_prompt(
        self,
        class_name: str,
        class_patterns: Dict[str, Any]
    ) -> str:
        """
        Generate class-specific prompt from Agent 2's patterns.

        Args:
            class_name: Name of demographic class
            class_patterns: Output from ClassSpecificAgent for this class

        Returns:
            Class-specific prompt text
        """
        print(f"  Generating prompt for {class_name}...")

        prompt = f"""You are generating a DEMOGRAPHIC-SPECIFIC PROMPT for the class: {class_name}

This prompt will be appended to the general system prompt to provide class-specific calibrations.

INPUT: Discovered patterns for this specific demographic:

CLASS-SPECIFIC RULES:
{json.dumps(class_patterns.get('class_specific_rules', {}), indent=2)}

DEVIATIONS FROM AVERAGE:
{json.dumps(class_patterns.get('deviations', [])[:15], indent=2)}

KEY CHARACTERISTICS:
{json.dumps(class_patterns.get('characteristics', {}), indent=2)}

TASK: Generate a concise DEMOGRAPHIC-SPECIFIC PROMPT following this structure:

```
DEMOGRAPHIC-SPECIFIC GUIDANCE FOR: {class_name}

## Profile
[2-3 sentence summary of this demographic based on discovered patterns]

## Learned Calibrations
Based on analysis of this demographic's response patterns:

### Digital/Technology Behaviors
[Specific adjustment based on patterns, e.g., "LIFT by +20pp - this is a tech-savvy segment"]

### Financial Attitudes & Behaviors
[Specific adjustment, e.g., "REDUCE by -15pp for risk-taking - conservative segment"]

### Environmental/Social Values
[Specific adjustment based on patterns]

### Lifestyle & Shopping
[Specific adjustment based on patterns]

### Other Notable Patterns
[Any unique patterns discovered for this demographic]

## Behavioral Decision-Making
[How this demographic makes decisions, based on discovered patterns]

## Example Scenarios
[2-3 specific examples of how to predict for this demographic]
```

IMPORTANT:
- Keep it under 500 words
- Be SPECIFIC with percentage adjustments
- Base everything on the discovered patterns
- Make calibrations actionable
- Explain the reasoning briefly

Output the complete prompt as plain text (not JSON).
"""

        # Use direct API call since we want text, not JSON
        from ..common.llm_providers import call_openai_api
        response_obj = call_openai_api(
            system_prompt="You are creating demographic-specific prompts for prediction agents.",
            user_prompt=prompt,
            model=self.model,
            temperature=0.2,
            max_tokens=2000
        )

        prompt_text = response_obj.content

        return prompt_text

    def generate_all_prompts(
        self,
        general_patterns: Dict[str, Any],
        all_class_patterns: Dict[str, Dict[str, Any]],
        output_dir: Path
    ):
        """
        Generate all prompt files.

        Args:
            general_patterns: Output from GeneralPatternAgent
            all_class_patterns: Output from ClassSpecificAgent for all classes
            output_dir: Where to save prompt files
        """
        print("\n" + "="*80)
        print("GENERATING ALL PROMPT FILES")
        print("="*80)

        # Create output directories
        output_dir.mkdir(parents=True, exist_ok=True)
        demographic_dir = output_dir / "demographic_guidance"
        demographic_dir.mkdir(exist_ok=True)

        # Generate general prompt
        print("\n[1/2] Generating general system prompt...")
        general_prompt = self.generate_general_prompt(general_patterns)

        general_file = output_dir / "general_system_prompt.txt"
        with open(general_file, 'w', encoding='utf-8') as f:
            f.write(general_prompt)

        print(f"  ✓ Saved to: {general_file}")

        # Generate class-specific prompts
        print(f"\n[2/2] Generating {len(all_class_patterns)} class-specific prompts...")

        for i, (class_name, patterns) in enumerate(all_class_patterns.items(), 1):
            try:
                if 'error' in patterns:
                    print(f"  [{i}/{len(all_class_patterns)}] Skipping {class_name} (error in pattern discovery)")
                    continue

                class_prompt = self.generate_class_specific_prompt(class_name, patterns)

                # Save to file
                class_file = demographic_dir / f"{class_name}.txt"
                with open(class_file, 'w', encoding='utf-8') as f:
                    f.write(class_prompt)

                print(f"  [{i}/{len(all_class_patterns)}] ✓ {class_name}.txt")

            except Exception as e:
                print(f"  [{i}/{len(all_class_patterns)}] ✗ ERROR for {class_name}: {e}")

        print("\n" + "="*80)
        print("PROMPT GENERATION COMPLETE")
        print("="*80)
        print(f"\nGeneral prompt: {general_file}")
        print(f"Class-specific prompts: {demographic_dir}/")
        print(f"Total files: 1 general + {len(list(demographic_dir.glob('*.txt')))} class-specific")


if __name__ == "__main__":
    # Test with sample data
    generator = PromptGenerator(model="gpt-5")

    # Load sample patterns (you would load from actual agent outputs)
    sample_general = {
        "general_rules": {
            "concept_classification": {"attitude": "Questions about beliefs"},
            "proximal_guardrails": ["If exact match shows 80%+, predict 75-90%"]
        },
        "metadata": {"total_classes": 22}
    }

    sample_class = {
        "class_specific_rules": {
            "profile_summary": "Wealthy, educated, tech-savvy professionals",
            "calibration_rules": {
                "digital_behaviors": {"adjustment": "+20pp", "reasoning": "High tech adoption"}
            }
        },
        "deviations": [],
        "characteristics": {}
    }

    # Generate sample prompts
    general_prompt = generator.generate_general_prompt(sample_general)
    print("\nSample General Prompt:")
    print(general_prompt[:500] + "...")

    class_prompt = generator.generate_class_specific_prompt("test_class", sample_class)
    print("\nSample Class Prompt:")
    print(class_prompt[:500] + "...")
