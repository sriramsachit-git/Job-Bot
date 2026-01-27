# Test Failures Analysis

This document analyzes all failing tests and identifies the root causes.

## Summary

**Total Tests**: 44  
**Passing**: 34 (77%)  
**Failing**: 9 (20%)  
**Skipped**: 1 (2%)

---

## Failed Tests Breakdown

### 1. `test_extract_with_beautifulsoup_success` ❌
**File**: `tests/test_extractor_extended.py:13`  
**Status**: FAILED  
**Error**: `assert None is not None`

**Root Cause**:
The test provides HTML content that should be sufficient, but the `extract_with_beautifulsoup` method requires **minimum 500 characters** of text content. The test HTML, when parsed and cleaned, doesn't meet this threshold.

**Code Issue**:
```python
# In src/extractor.py:265
if len(text) > 500:  # Requires 500+ characters
    return text
logger.warning(f"BeautifulSoup found insufficient content")
return None
```

**Test HTML**:
```html
<h1>Software Engineer</h1>
<p>We are looking for a software engineer with 5+ years of experience.</p>
<p>Requirements: Python, Django, PostgreSQL</p>
```
This content, when cleaned and whitespace-normalized, is likely less than 500 characters.

**Fix Options**:
1. Increase test HTML content to exceed 500 characters
2. Lower the minimum content threshold for testing
3. Mock the content length check

---

### 2. `test_smart_extract_fallback_to_beautifulsoup` ❌
**File**: `tests/test_extractor_extended.py:67`  
**Status**: FAILED  
**Error**: `assert None is not None`

**Root Cause**:
Same as test #1 - the HTML content in the test doesn't meet the 500-character minimum requirement.

**Test HTML**:
```html
<h1>Job Title</h1>
<p>This is a detailed job description with enough content...</p>
<p>It includes multiple paragraphs and details...</p>
```
Even with the description, the cleaned text is likely under 500 characters.

**Fix**: Same as test #1 - provide more content or adjust the threshold.

---

### 3. `test_extractor_gets_content` ❌
**File**: `tests/test_integration.py:45`  
**Status**: FAILED  
**Error**: `AssertionError: Failed to extract content from https://jobs.lever.co/anthropic/...`

**Root Cause**:
**Playwright browser not installed**. The error message shows:
```
BrowserType.launch: Executable doesn't exist at .../playwright/chromium_headless_shell-1200/...
╔════════════════════════════════════════════════════════════╗
║ Looks like Playwright was just installed or updated.       ║
║ Please run the following command to download new browsers:║
║                                                            ║
║     playwright install                                     ║
╚════════════════════════════════════════════════════════════╝
```

**Additional Issues**:
- The test uses a **real URL** that may no longer exist or be accessible
- Jina extraction returned insufficient content (349 chars)
- BeautifulSoup extraction failed with 404 error

**Fix**:
1. Install Playwright browsers: `playwright install chromium`
2. Update test URLs to use current, accessible job postings
3. Consider mocking network requests for integration tests

---

### 4. `test_parser_extracts_job_details` ❌
**File**: `tests/test_integration.py:55`  
**Status**: FAILED  
**Error**: `AssertionError: Extraction failed`

**Root Cause**:
This test depends on test #3 (`test_extractor_gets_content`). Since extraction fails, there's no content to parse.

**Chain of Failures**:
1. Extraction fails (test #3) → `content = None`
2. Parser test receives `None` → fails immediately

**Fix**: Fix test #3 first, then this test should pass.

---

### 5. `test_filter_scores_job` ❌
**File**: `tests/test_integration.py:79`  
**Status**: FAILED  
**Error**: `AssertionError: Parsing failed`

**Root Cause**:
Depends on test #4 (parsing), which depends on test #3 (extraction). Cascade failure.

**Fix**: Fix extraction first (test #3).

---

### 6. `test_storage_saves_job` ❌
**File**: `tests/test_integration.py:96`  
**Status**: FAILED  
**Error**: `AttributeError: 'NoneType' object has no attribute 'yoe_required'`

**Root Cause**:
Same cascade - `job` is `None` because parsing failed (test #4), which failed because extraction failed (test #3).

**Fix**: Fix extraction first (test #3).

---

### 7. `test_full_pipeline_flow` ❌
**File**: `tests/test_integration.py:115`  
**Status**: FAILED  
**Error**: `AssertionError: No jobs processed successfully`

**Root Cause**:
End-to-end integration test that depends on all previous components working. Since extraction fails for all URLs, no jobs are processed.

**Issues**:
- Uses real URLs that may be inaccessible
- Requires Playwright browsers installed
- Requires network access
- Requires valid API keys

**Fix**:
1. Install Playwright: `playwright install chromium`
2. Update URLs to current, accessible job postings
3. Ensure API keys are configured
4. Consider making this test optional or using mocks

---

### 8. `test_pipeline_stores_failed_extractions` ❌
**File**: `tests/test_pipeline_extended.py:26`  
**Status**: FAILED  
**Error**: `AssertionError: assert False` (mock not called)

**Root Cause**:
The test mocks the pipeline but the actual `run()` method may not be calling `save_unextracted_job` in the expected way, or the mock setup is incorrect.

**Analysis**:
Looking at `src/pipeline.py:240`, `save_unextracted_job` is called when `result["success"]` is `False`. The test mocks `extract_batch` to return one failure, but the pipeline's `run()` method may have additional logic that prevents the call.

**Potential Issues**:
1. The mock pipeline's `__init__` is bypassed, so `self.db` may not be properly set up
2. The `run()` method may have early returns that prevent reaching the save logic
3. The mock may not match the actual method signature

**Fix**:
1. Review the actual `run()` method flow
2. Ensure mocks match the real method signatures
3. Add debug logging to see where the flow stops

---

### 9. `test_get_unextracted_jobs_with_retry_limit` ❌
**File**: `tests/test_storage_extended.py:59`  
**Status**: FAILED  
**Error**: `assert 0 == 1` (expected 1 job, got 0)

**Root Cause**:
The test saves 2 jobs, with one having `retry_count=2` (saved twice). It then queries with `max_retries=1`, expecting to get only the job with `retry_count=1`.

**Analysis**:
The test logic:
1. Save job1 → `retry_count=1`
2. Save job2 → `retry_count=1`
3. Save job2 again → `retry_count=2`
4. Query with `max_retries=1` → should return only job1

**Potential Issues**:
1. The `get_unextracted_jobs(max_retries=1)` method may have incorrect SQL logic
2. The retry_count increment may not be working correctly
3. The query may be filtering incorrectly

**Fix**:
1. Check the SQL query in `get_unextracted_jobs()` method
2. Verify `retry_count` is being incremented correctly
3. Test the query logic independently

---

## Test Categories

### ✅ Passing Tests (34)
- All backend model/schema tests
- All search query building tests
- All basic storage operations
- All parser unit tests (with mocked content)
- All structure validation tests
- Most extractor unit tests

### ❌ Failing Tests (9)
- **2 tests**: BeautifulSoup content length threshold
- **5 tests**: Integration tests requiring network/Playwright
- **1 test**: Mock setup issue in pipeline test
- **1 test**: SQL query logic issue

### ⏭️ Skipped Tests (1)
- `test_database_init`: Async test that requires database setup

---

## Root Causes Summary

### 1. **Content Length Threshold** (2 failures)
- BeautifulSoup requires 500+ characters
- Test HTML is too short
- **Fix**: Increase test content or lower threshold

### 2. **Missing Dependencies** (5 failures)
- Playwright browsers not installed
- **Fix**: Run `playwright install chromium`

### 3. **Network/Real URLs** (5 failures)
- Tests use real URLs that may be inaccessible
- **Fix**: Update URLs or use mocks

### 4. **Mock Setup Issues** (1 failure)
- Pipeline test mock doesn't match actual behavior
- **Fix**: Review and fix mock setup

### 5. **SQL Query Logic** (1 failure)
- `get_unextracted_jobs` query may be incorrect
- **Fix**: Review SQL query logic

---

## Recommended Fixes (Priority Order)

### High Priority (Blocks Integration Tests)

1. **Install Playwright Browsers**
   ```bash
   playwright install chromium
   ```
   This will fix 5 integration tests.

2. **Fix BeautifulSoup Content Threshold Tests**
   - Update test HTML to exceed 500 characters
   - Or add a test-specific threshold override

### Medium Priority

3. **Fix Pipeline Mock Test**
   - Review `test_pipeline_stores_failed_extractions`
   - Ensure mocks match actual method signatures
   - Add debug logging

4. **Fix Storage Query Test**
   - Review `get_unextracted_jobs()` SQL query
   - Test query logic independently
   - Verify retry_count increment logic

### Low Priority (Nice to Have)

5. **Update Integration Test URLs**
   - Replace hardcoded URLs with current, accessible ones
   - Or use test fixtures/mocks instead

6. **Make Integration Tests Optional**
   - Mark network-dependent tests as `@pytest.mark.integration`
   - Allow running unit tests separately

---

## Test Execution Commands

### Run All Tests
```bash
pytest tests/ -v
```

### Run Only Unit Tests (Skip Integration)
```bash
pytest tests/ -v -m "not integration"
```

### Run Specific Test File
```bash
pytest tests/test_extractor_extended.py -v
```

### Run with Coverage
```bash
pytest tests/ --cov=src --cov-report=html
```

---

## Notes

- **77% pass rate** is actually quite good for a project with integration tests
- Most failures are due to **environment setup** (Playwright) or **test data** (content length)
- Core functionality tests (storage, search, parsing with mocks) all pass
- Integration tests require proper environment setup and network access

---

## Next Steps

1. ✅ Install Playwright browsers
2. ✅ Fix BeautifulSoup content threshold tests
3. ✅ Review and fix pipeline mock test
4. ✅ Review and fix storage query test
5. ⏭️ Update integration test URLs (optional)
6. ⏭️ Add test markers for better organization (optional)
