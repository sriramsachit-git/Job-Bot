# Comprehensive Search & Usage Tracking Features

## Overview

New advanced search features and comprehensive usage tracking have been added to the job search pipeline.

## New Features

### 1. Per-Site Search (`--per-site`)

Search a single keyword across all sites individually, getting N results from each site.

**Usage:**
```bash
python main.py -k "AI engineer" --per-site 10
# Searches "AI engineer" on each site, 10 results per site
# Result: 10 sites × 10 results = ~100 URLs (with deduplication)
```

**Benefits:**
- More targeted search per site
- Better coverage of each job board
- Controlled results per site

### 2. Comprehensive Search (`--comprehensive`)

Search ALL keywords × ALL sites (matrix approach) for maximum coverage.

**Usage:**
```bash
# Default: Uses 5 standard job titles
python main.py --comprehensive

# Custom titles
python main.py --comprehensive --titles "AI engineer" "ML engineer" "data scientist"

# With custom sites
python main.py --comprehensive --sites greenhouse.io lever.co
```

**How it works:**
- 5 keywords × 10 sites = 50 separate searches
- Each keyword-site combination searched individually
- Results deduplicated by URL
- Maximum coverage of job market

**Example:**
```
Comprehensive search: 5 keywords × 10 sites = 50 queries
[1/50] 'AI engineer' on greenhouse.io...
[2/50] 'AI engineer' on lever.co...
...
Found 287 unique URLs (423 raw, 136 duplicates)
```

### 3. Usage Reporting (`--usage-report`)

View aggregated usage statistics for the last 7 days.

**Usage:**
```bash
python main.py --usage-report
```

**Output:**
```
┌─────────────────────────────────────┬───────────────┐
│ Metric                              │         Value │
├─────────────────────────────────────┼───────────────┤
│ Pipeline Runs                       │             5 │
│ Google Queries                      │           250 │
│ OpenAI Tokens                       │       850,000 │
│ Jobs Saved                          │           450 │
│ Google Cost                         │        $0.75  │
│ OpenAI Cost                         │        $0.13  │
│ Total Cost                          │        $0.88  │
└─────────────────────────────────────┴───────────────┘
```

### 4. Automatic Usage Tracking

Every pipeline run now automatically:
- Tracks Google Search API queries
- Tracks OpenAI token usage (prompt + completion)
- Tracks extraction methods (Jina/Playwright/BeautifulSoup)
- Calculates cost estimates
- Saves detailed reports to `data/usage_reports/`

**Report Location:** `data/usage_reports/usage_YYYYMMDD_HHMMSS.json`

## Usage Tracking Details

### What's Tracked

1. **Google Search API:**
   - Total queries made
   - Successful/failed queries
   - Results per query
   - Cost estimates (free 100/day, then $5/1000)

2. **OpenAI API:**
   - Request count
   - Prompt tokens
   - Completion tokens
   - Total tokens
   - Cost estimates (GPT-4o-mini pricing)

3. **Extraction:**
   - Methods attempted (Jina/Playwright/BeautifulSoup)
   - Success/failure rates per method
   - URLs processed

4. **Pipeline Results:**
   - Jobs parsed
   - Jobs filtered
   - Jobs saved
   - Duplicates skipped

### Cost Estimates

- **Google Search API:** Free 100 queries/day, then $5 per 1,000 queries
- **OpenAI GPT-4o-mini:** $0.15 per 1M input tokens, $0.60 per 1M output tokens

Costs are calculated automatically and shown in usage reports.

## CLI Examples

### Standard Search (Existing)
```bash
python main.py -k "AI engineer" "ML engineer" -n 50
```

### Per-Site Search
```bash
# Single keyword, 10 results per site
python main.py -k "data scientist" --per-site 10
```

### Comprehensive Search
```bash
# All default titles × all sites
python main.py --comprehensive

# Custom titles
python main.py --comprehensive --titles "AI engineer" "ML engineer"

# With custom number of results per query
python main.py --comprehensive -n 10
```

### View Usage
```bash
# Last 7 days
python main.py --usage-report
```

## Implementation Details

### Files Modified

1. **src/search.py**
   - Added `search_per_site()` method
   - Added `search_all_comprehensive()` method
   - Both return usage stats

2. **src/usage_tracker.py** (NEW)
   - `UsageTracker` class for tracking API usage
   - `UsageReport` dataclass for structured reports
   - `get_historical_usage()` for aggregated stats

3. **src/llm_parser.py**
   - Modified `_call_llm()` to return token usage
   - Modified `parse_batch()` to aggregate and return tokens

4. **src/pipeline.py**
   - Integrated `UsageTracker`
   - Added `per_site` and `comprehensive` parameters
   - Tracks all API calls and extraction methods

5. **main.py**
   - Added `--per-site`, `--comprehensive`, `--usage-report`, `--titles` arguments
   - Updated search logic to support new modes

## Performance Considerations

### Comprehensive Search

- **Queries:** 5 keywords × 10 sites = 50 queries
- **Time:** ~50 seconds (1 second delay between queries)
- **API Quota:** Uses 50 Google API queries
- **Results:** Typically 200-500 unique URLs after deduplication

### Per-Site Search

- **Queries:** 1 keyword × 10 sites = 10 queries
- **Time:** ~10 seconds
- **API Quota:** Uses 10 Google API queries
- **Results:** Typically 50-100 unique URLs

### Rate Limiting

- 1 second delay between queries (automatic)
- Google API free tier: 100 queries/day
- Comprehensive search uses 50 queries (half of daily quota)

## Best Practices

1. **For Daily Runs:** Use standard search (`python main.py --daily`)
2. **For Maximum Coverage:** Use comprehensive search weekly
3. **For Specific Sites:** Use per-site search
4. **Monitor Usage:** Check `--usage-report` regularly
5. **Review Reports:** Check `data/usage_reports/` for detailed logs

## Troubleshooting

### "Rate limit exceeded"
- You've used your daily quota (100 queries)
- Wait 24 hours or upgrade to paid tier
- Use smaller comprehensive searches

### High Costs
- Check usage reports regularly
- Reduce comprehensive search frequency
- Use per-site search instead of comprehensive

### Missing Results
- Comprehensive search deduplicates by URL
- Some sites may have fewer results
- Check query logs in usage reports

## Summary

✅ **Per-Site Search** - Search one keyword across all sites
✅ **Comprehensive Search** - Search all keywords × all sites
✅ **Usage Tracking** - Automatic tracking of all API calls
✅ **Cost Estimates** - Real-time cost calculations
✅ **Usage Reports** - View historical usage statistics
✅ **Detailed Logs** - JSON reports for every run

All features are production-ready and backward compatible! 🚀
