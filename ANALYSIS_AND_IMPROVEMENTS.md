# Code Analysis & Improvements

## Answers to Your Queries

### 1. Max Count & Batch Processing

**Current State:**
- ✅ Google Search API: Max 100 results (hard limit), paginated in batches of 10
- ❌ Content Extraction: Sequential processing, no batch size limit
- ❌ No parallel processing for extraction

**Issues Found:**
- `extract_batch()` processes all URLs sequentially with delays
- No max batch size for extraction
- No parallel/concurrent extraction

**Recommendation:**
- Add batch size limit for extraction (e.g., process 20 at a time)
- Add parallel extraction using ThreadPoolExecutor or asyncio
- Add configurable batch size parameter

### 2. Early Senior Position Filtering

**Current State:**
- ❌ **CRITICAL ISSUE**: Title filtering happens AFTER parsing (wastes credits!)
- Filtering happens in `filters.py` line 150, but parsing already happened
- Senior positions are extracted and parsed, then discarded

**Impact:**
- Wasting OpenAI API credits on jobs that will be discarded
- If 30% of jobs are senior positions, you're wasting 30% of credits

**Solution:**
- Filter by title BEFORE extraction (using search snippet/title)
- Add early filtering in pipeline before Step 2 (extraction)

### 3. Inefficiencies & Bugs Found

#### Critical Issues:
1. **Title filtering too late** - Wastes API credits
2. **No early filtering** - All jobs extracted and parsed regardless
3. **Sequential extraction** - Slow, no parallelization
4. **No extraction batch limits** - Could process 100+ URLs sequentially

#### Performance Issues:
1. **No caching** - Same URLs extracted multiple times
2. **No connection pooling** - New connections for each request
3. **Inefficient database queries** - No prepared statements optimization
4. **JSON parsing on every query** - Could cache parsed results

#### Code Quality Issues:
1. **Error handling gaps** - Some exceptions not caught
2. **No retry for BeautifulSoup** - Only Jina/Playwright have retry
3. **Memory inefficiency** - Loading all jobs into memory
4. **No rate limiting tracking** - Could hit API limits

#### Potential Bugs:
1. **Index mismatch** - `search_results[i]` could be out of bounds if extraction fails
2. **Timestamp race condition** - `before_timestamp` might miss jobs
3. **No validation** - Search results might have missing fields
4. **Database connection leaks** - Not all paths close connections

### 4. Suggested Improvements

#### High Priority:
1. ✅ **Early Title Filtering** - Filter before extraction
2. ✅ **Batch Size Limits** - Process in smaller batches
3. ✅ **Parallel Extraction** - Use ThreadPoolExecutor
4. ✅ **Early Senior Filter** - Check title from search results

#### Medium Priority:
5. **Caching Layer** - Cache extracted content
6. **Connection Pooling** - Reuse HTTP connections
7. **Better Error Handling** - More specific exceptions
8. **Rate Limit Tracking** - Monitor API usage

#### Low Priority:
9. **Database Indexing** - Add more indexes
10. **Query Optimization** - Use prepared statements
11. **Memory Optimization** - Stream processing
12. **Logging Improvements** - Better debug info

## Implementation Plan

I'll implement:
1. Early title filtering (before extraction)
2. Batch size limits for extraction
3. Parallel extraction option
4. Better error handling
5. Bug fixes
