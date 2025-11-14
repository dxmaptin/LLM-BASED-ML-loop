# Soap & Glory Concept Analysis - Complete Data Package

## Summary

All concept-related data has been processed and organized in a single integrated folder structure, ready for multi-modal analysis combining **vision extraction** and **concept test performance data**.

## Project Structure

```
project_data/
├── concept_vision_data/              # Vision extraction from product images
│   ├── raw_images/                   # 24 original product concept images
│   ├── processed_txt/                # GPT-4o vision extraction (text files)
│   └── processed_csv/
│       └── results/
│           └── vision_extraction_results.csv  # Main vision data CSV
│
└── concept_test_processed/           # Concept test KPI data
    ├── concept_test_wide.csv         # Wide format (48 rows × 18 cols)
    ├── concept_test_long.csv         # Long/tidy format (480 rows)
    ├── concept_test_full_cleaned.csv # Full cleaned data
    ├── QA_REPORT.txt                 # Quality assurance report
    └── README.md                     # Detailed documentation
```

---

## Dataset 1: Vision Extraction Data

**Location:** `concept_vision_data/processed_csv/results/vision_extraction_results.csv`

### Overview
- **24 product images** processed with GPT-4o multimodal LLM
- **17 columns** of structured vision data
- **Processing time:** ~21 seconds per image

### Key Features Extracted

#### Textual Content (from images)
- Product names, descriptions, categories
- Claims and benefits
- Ingredients and formulations
- Packaging details (size, price)
- Usage instructions
- Additional taglines and messages

#### Visual Analysis
- **Color scheme**: Dominant colors and palettes
- **Imagery type**: Lifestyle vs product-only
- **Design style**: Premium, casual, playful, clinical, etc.
- **Badges/labels**: Special callouts (vegan, clean, etc.)
- **Target audience signals**: Visual cues about intended users

### Schema
```
image_filename, product_name, brand, product_description, product_category,
key_claims_benefits, ingredients, packaging_size, packaging_price,
usage_instructions, color_scheme, imagery_type, badges_labels,
design_style, target_audience, additional_text, full_extraction
```

---

## Dataset 2: Concept Test Performance Data

**Location:** `concept_test_processed/concept_test_wide.csv`

### Overview
- **48 concept tests** (UK market only)
- **24 unique concepts** (each tested with 2 subgroups)
- **4 test waves** (Jan 24, FY25, FY26, FY27)
- **18 columns** with KPIs and metadata

### Key Variables

#### Stable Keys
- **`concept_id`**: Slugified identifier (e.g., "soap_glory_girls_night_out_cool_aid")
- **`wave`**: Test wave identifier (e.g., "soap_glory_jan_24")

#### Target Variable
- **`target_top2box_intent`**: Purchase Intent Top 2 Box (%)
  - Mean: 68.19%
  - Std: 14.09%
  - Range: 53–74% across concepts

#### Feature KPIs (all in %, 0-100 scale)
1. **`appeal_pcttop_2`**: Overall appeal (24–86%)
2. **`uniqueness_pcttop_2`**: Perceived uniqueness (35–93%)
3. **`relevance_pcttop_2`**: Personal relevance (16–68%)
4. **`excitement_pcttop_2`**: Excitement generated (59–98%)
5. **`price_value_pcttop_2`**: Price/value perception (39–86%)
6. **`believability_pcttop`**: Believability of claims (20–72%)
7. **`understanding_pcttop_3`**: Understanding of concept (47–88%)
8. **`trial`**: Trial intent (20–75%)
9. **`inc_trial_brand`**: Incremental brand trial (18–68%)

#### Metadata
- `concept_name`: Full concept name
- `brand`: Soap & Glory
- `category`: Bath & Body Care
- `is_priced`: Boolean (all concepts priced)

### Data Quality
- ✓ All percentage columns in valid 0-100 range
- ✓ No missing target data
- ⚠ Duplicate concept-wave pairs (2 subgroups per concept)
- ✗ `star_rating` 100% missing (not collected)

---

## Concept Coverage: 24 Products Across 4 Waves

### Wave 1: `soap_glory_jan_24` (12 concepts)
**Girls Night Out Range:**
1. Cool Aid - Cooling jelly cream
2. Refresh Queen - Skin balm
3. Stardust Stick - Stick balm

**Liquid Lingerie Range:**
4. It's Blur-fect - Body primer
5. Glow Gloves - Hand cream
6. Glow-on - Body glow

**Mission Possible Range:**
7. Time Travel Body Lotion
8. Bounce Back Body Balm
9. Smooth Operator Elixir

**Wake-Up Glorious Range:**
10. Magni-Serum - Body serum
11. Press Play Spray - Face/body spray
12. Slumberland Soak - Bath salts

### Wave 2: `soap_glory_fy25_concept_test` (4 concepts)
13. S&G Be Me Body Sprays (3x personalized scents)
14. S&G Embrace Me Bodycare
15. S&G Original Pink Suncare
16. S&G Rebalancing Probiotic Bodycare

### Wave 3: `soap_glory_fy26_concept_test` (5 concepts)
17. Exfoliating Body Scrub and Massage Bar
18. Nourishing Solid Body Oil Stick
19. pH Sensitive Skin Body Wash
20. pH V Friendly Bath Bomb
21. Skin Benefit Scrub Collection (x3)

### Wave 4: `soap_glory_fy27_july_2024` (3 concepts)
22. S&G's Glow-On Gradual Tan Lotion
23. Time Travel Glow-On Gradual Tan Lotion
24. Time Travel Body Lotion for Stretch Marks

---

## Data Integration & Analysis Opportunities

### Join Strategy

Both datasets can be joined using **fuzzy matching** on concept identifiers:

**Concept Test `concept_id` ↔ Vision Data `image_filename`**

Example mappings:
```
soap_glory_girls_night_out_cool_aid     ↔ Witty_Optimist_Jan24.Girls_Night_Out_cool_aid.jpg
sg_be_me_body_sprays                     ↔ Witty_Optimist_FY25.S&G_Be_Me_Body_Sprays.JPG
time_travel_body_lotion_for_stretch_marks ↔ Witty_Optimist_FY27.TIME_TRAVEL_BODY_LOTION_FOR_STRETCH_MARKS.JPG
```

### Multi-Modal Analysis Possibilities

#### 1. Visual Features → Performance Prediction
**Question:** Can visual design elements predict purchase intent?

**Approach:**
- X (predictors): Color scheme, design style, imagery type, badges
- Y (target): `target_top2box_intent`
- Method: Regression, random forest, gradient boosting

**Insights:**
- Which colors drive higher appeal?
- Does lifestyle imagery correlate with excitement scores?
- Do premium design styles justify higher price value perception?

#### 2. Claims Analysis
**Question:** What product claims resonate most?

**Approach:**
- Extract claim keywords from `key_claims_benefits`
- Count claim frequency per concept
- Correlate with `believability_pcttop` and `understanding_pcttop_3`

**Insights:**
- Do more claims = higher believability?
- Which claim types (hydration, anti-aging, natural) perform best?

#### 3. Target Audience Alignment
**Question:** Do visual audience signals match concept performance?

**Approach:**
- Compare `target_audience` (vision) with actual KPI scores
- Segment concepts by visual audience (young/mature, casual/premium)
- Analyze KPI differences across segments

#### 4. Ingredient Transparency Impact
**Question:** Does showing ingredients affect perception?

**Approach:**
- Categorize concepts by ingredient visibility
- Compare `believability_pcttop` and `price_value_pcttop_2`

#### 5. Multi-Modal Intent Prediction Model
**Ultimate goal:** Predict `target_top2box_intent` from image alone

**Feature engineering:**
- **Visual:** Color palette (5 features), design style (categorical), imagery type (binary)
- **Textual:** Claim count, ingredient count, word embeddings of descriptions
- **Packaging:** Size (numeric), price (numeric), is_priced (binary)

**Model architecture:**
- Ensemble of vision + text features
- Cross-validation by wave
- Feature importance analysis

---

## Quick Start: Integration Code

### Python Example
```python
import pandas as pd
import re

# Load both datasets
vision = pd.read_csv('concept_vision_data/processed_csv/results/vision_extraction_results.csv')
concept_test = pd.read_csv('concept_test_processed/concept_test_wide.csv')

# Create slugified keys for joining
def slugify(text):
    text = str(text).lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '_', text)
    return text

vision['image_slug'] = vision['image_filename'].apply(slugify)

# Join datasets
merged = pd.merge(
    concept_test,
    vision,
    left_on='concept_id',
    right_on='image_slug',
    how='inner'
)

print(f"Merged dataset: {merged.shape}")
print(f"Columns: {len(merged.columns)}")

# Example analysis: Color scheme vs Appeal
print("\nColor scheme impact on appeal:")
print(merged.groupby('color_scheme')['appeal_pcttop_2'].mean().sort_values(ascending=False))
```

### R Example
```r
library(tidyverse)

# Load data
vision <- read_csv('concept_vision_data/processed_csv/results/vision_extraction_results.csv')
concept_test <- read_csv('concept_test_processed/concept_test_wide.csv')

# Slugify function
slugify <- function(text) {
  text %>%
    str_to_lower() %>%
    str_replace_all("[^\\w\\s-]", "") %>%
    str_replace_all("[-\\s]+", "_")
}

vision <- vision %>% mutate(image_slug = slugify(image_filename))

# Join
merged <- concept_test %>%
  inner_join(vision, by = c("concept_id" = "image_slug"))

# Analyze
merged %>%
  group_by(design_style) %>%
  summarise(
    avg_intent = mean(target_top2box_intent, na.rm = TRUE),
    avg_uniqueness = mean(uniqueness_pcttop_2, na.rm = TRUE)
  ) %>%
  arrange(desc(avg_intent))
```

---

## Files & Scripts

### Data Files
1. **`vision_extraction_results.csv`** - Vision data (24 rows)
2. **`concept_test_wide.csv`** - Wide format KPIs (48 rows)
3. **`concept_test_long.csv`** - Long format KPIs (480 rows)
4. **`concept_test_full_cleaned.csv`** - Full cleaned data (48 rows)

### Processing Scripts
1. **`batch_process_all_images.py`** - Vision extraction pipeline
2. **`convert_vision_results_to_csv.py`** - Vision text → CSV
3. **`process_concept_test_data.py`** - Concept test data cleaning

### Documentation
1. **`concept_vision_data/processed_csv/results/BATCH_SUMMARY.txt`**
2. **`concept_test_processed/QA_REPORT.txt`**
3. **`concept_test_processed/README.md`**
4. **This file** - Complete integration guide

---

## Next Steps

### Immediate Actions
1. ✓ Process vision data from images
2. ✓ Process concept test data from Excel
3. ✓ Create structured CSVs
4. ✓ Run QA checks
5. ☐ **Join datasets** using concept identifiers
6. ☐ **Handle duplicates** (average subgroups or keep separate)
7. ☐ **Feature engineering** from visual + textual data

### Analysis Priorities
1. **Exploratory Data Analysis (EDA)**
   - Distributions of all KPIs
   - Correlations between visual features and KPIs
   - Concept clustering by visual similarity

2. **Predictive Modeling**
   - Predict `target_top2box_intent` from features
   - Feature importance analysis
   - Cross-validate by wave

3. **Insights & Recommendations**
   - Top-performing visual patterns
   - Optimal claim structures
   - Design guidelines for future concepts

---

**Created:** 2025-11-11
**Total Concepts:** 24
**Total Datapoints:** 48 concept tests + 24 vision extractions
**Status:** ✓ Complete & Ready for Analysis
