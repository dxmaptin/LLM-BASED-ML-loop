# Concept Test Data Processing - Complete

## Overview

This folder contains processed concept testing data for Soap & Glory products, ready for analysis and integration with vision extraction data.

## Source Data

- **Input:** `Soap & Glory concept testing data pull.xlsx`
- **Original rows:** 96 (48 UK + 48 USA)
- **Filtered rows:** 48 (UK market only)
- **Unique concepts:** 24
- **Test waves:** 4

## Processing Applied

### 1. Data Cleaning
- Read with `header=1` (row 2 as column names)
- Dropped all-NaN columns
- Filtered to UK market only (`market == "UK"`)
- Standardised column names to `snake_case`
- Converted percentage strings to numeric values (0-100)

### 2. Stable Keys Created
- **`concept_id`**: Slugified concept name (e.g., "soap_glory_girls_night_out_cool_aid")
- **`wave`**: Slugified project name (e.g., "soap_glory_jan_24")

### 3. Target Variable
- **`target_top2box_intent`**: Purchase intent Top 2 Box (%)
  - Mean: 68.19%
  - Std: 14.09%
  - Range: Available for all 48 rows

### 4. Feature KPIs (all in %)
- `appeal_pcttop_2`: Appeal Top 2 Box
- `uniqueness_pcttop_2`: Uniqueness Top 2 Box
- `relevance_pcttop_2`: Relevance Top 2 Box
- `excitement_pcttop_2`: Excitement Top 2 Box
- `price_value_pcttop_2`: Price Value Top 2 Box
- `believability_pcttop`: Believability Top Box
- `understanding_pcttop_3`: Understanding Top 3 Box
- `trial`: Trial intent
- `inc_trial_brand`: Incremental trial for brand

### 5. Metadata
- `concept_name`: Full concept name
- `brand`: Soap & Glory
- `franchise_name`: Soap & Glory
- `category`: Bath & Body Care
- `is_priced`: Boolean (all concepts were priced)

## Output Files

### 1. `concept_test_wide.csv` (48 rows × 18 columns)
**One row per concept** with all KPIs and metadata.

**Use for:**
- Machine learning models
- Regression analysis
- Correlation analysis
- Direct joins with vision data

**Key columns:**
```
wave, concept_id, concept_name, brand, franchise_name, category, is_priced,
target_top2box_intent, appeal_pcttop_2, uniqueness_pcttop_2, relevance_pcttop_2,
excitement_pcttop_2, price_value_pcttop_2, believability_pcttop, understanding_pcttop_3,
star_rating, trial, inc_trial_brand
```

### 2. `concept_test_long.csv` (480 rows × 9 columns)
**Tidy/long format** with one row per concept-metric combination.

**Use for:**
- Time series plots
- Faceted visualizations
- Easy filtering by metric
- ggplot-style plotting

**Structure:**
```
wave, concept_id, concept_name, brand, franchise_name, category, is_priced, metric, value
```

**Example:**
```
soap_glory_jan_24, soap_glory_girls_night_out_cool_aid, Cool Aid, ..., appeal_pcttop_2, 55.0
soap_glory_jan_24, soap_glory_girls_night_out_cool_aid, Cool Aid, ..., uniqueness_pcttop_2, 65.0
...
```

### 3. `concept_test_full_cleaned.csv` (48 rows × 22 columns)
Full dataset with all original columns plus computed keys.

**Additional columns:**
- `date_of_testing`
- `market`
- `wave_original`
- `pur_intent_pcttop` (fallback target)

### 4. `QA_REPORT.txt`
Quality assurance summary including:
- Row counts
- Percentage range checks (all KPIs in 0-100 range)
- Unique concept-wave pairs
- Missing data summary
- Concepts per wave distribution

## Data Quality Notes

### Duplicate Concept-Wave Pairs
Each concept appears **twice** in the dataset (48 rows for 24 concepts). This is because concepts were tested with different sample groups:
- Sample 1: "Category buyer"
- Sample 2: (another subgroup)

**Recommendation:** Average the KPIs across both samples per concept, or keep subgroup as an additional key.

### Missing Data
- **`star_rating`**: 100% missing (not collected for these concepts)

### All Percentage KPIs
All percentage columns are numeric and within realistic ranges (0-100).

## Waves and Concepts

### Wave: `soap_glory_jan_24` (12 concepts)
- Girls Night Out range (Cool Aid, Refresh Queen, Stardust Stick)
- Liquid Lingerie range (Blur-fect, Glow Gloves, Glow-on)
- Mission Possible range (Bounce Back, Time Travel, Smooth Operator)
- Wake-Up Glorious range (Magni-Serum, Press Play, Slumberland)

### Wave: `soap_glory_fy25_concept_test` (4 concepts)
- S&G Be Me Body Sprays
- S&G Embrace Me Bodycare
- S&G Original Pink Suncare
- S&G Rebalancing Probiotic Bodycare

### Wave: `soap_glory_fy26_concept_test` (5 concepts)
- Exfoliating Body Scrub and Massage Bar
- Nourishing Solid Body Oil Stick
- pH Sensitive Skin Body Wash
- pH V Friendly Bath Bomb
- Skin Benefit Scrub Collection x3

### Wave: `soap_glory_fy27_july_2024` (3 concepts)
- S&G's Glow-On Gradual Tan Lotion
- Time Travel Glow-On Gradual Tan Lotion
- Time Travel Body Lotion for Stretch Marks

## Integration with Vision Extraction Data

The concept test data can be joined with vision extraction results from:
`../concept_vision_data/processed_csv/results/vision_extraction_results.csv`

### Join Strategy

**Fuzzy matching on concept names:**

The `concept_id` in concept test data should match with slugified image filenames from vision data.

**Mapping examples:**
```
Concept Test                          Vision Data Image
--------------------------------------------------------------------------------------------------------
soap_glory_girls_night_out_cool_aid   Witty_Optimist_Jan24.Girls_Night_Out_cool_aid.jpg
sg_be_me_body_sprays                  Witty_Optimist_FY25.S&G_Be_Me_Body_Sprays.JPG
time_travel_glow_on_gradual_tan_lotion Witty_Optimist_FY27.TIME_TRAVEL_'GLOW-ON'_GRADUAL_TAN_LOTION.JPG
```

**Join code example (Python/pandas):**
```python
import pandas as pd

# Load both datasets
concept_test = pd.read_csv('concept_test_wide.csv')
vision_data = pd.read_csv('../concept_vision_data/processed_csv/results/vision_extraction_results.csv')

# Create slugified image names for joining
vision_data['image_slug'] = vision_data['image_filename'].str.lower().str.replace(r'[^a-z0-9]', '_', regex=True)

# Join on concept_id
merged = pd.merge(
    concept_test,
    vision_data,
    left_on='concept_id',
    right_on='image_slug',
    how='inner'
)
```

### Combined Analysis Possibilities

With both concept test KPIs and vision extraction data, you can analyze:

1. **Visual→Performance relationships**
   - Do colors affect appeal/excitement scores?
   - Does lifestyle imagery correlate with intent to purchase?
   - Which design styles drive higher uniqueness scores?

2. **Claims vs Perception**
   - Do products with more claims score higher on believability?
   - Does ingredient transparency affect price value perception?

3. **Target Audience Alignment**
   - Do visual target audience signals match concept test performance?
   - Which concepts resonate best with intended demographics?

4. **Multi-modal Prediction**
   - Use both textual (claims, ingredients) and visual features (colors, style) to predict `target_top2box_intent`
   - Feature engineering from vision + test data

## Next Steps

1. **Handle duplicates:** Decide whether to average subgroups or keep separate
2. **Join with vision data:** Create merged dataset
3. **Feature engineering:** Combine visual and KPI features
4. **Modeling:** Predict purchase intent from visual+textual features
5. **Insights:** Identify top-performing visual and claim patterns

---

**Created:** 2025-11-11
**Processing script:** `process_concept_test_data.py`
**Source:** `Soap & Glory concept testing data pull.xlsx`
