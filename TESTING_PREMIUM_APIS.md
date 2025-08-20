# 🧪 Premium API Testing Scripts

This directory contains comprehensive testing scripts for all premium Lightcast API endpoints.

## 📋 Available Test Scripts

### 1. `test_premium_apis_basic.py` ✅ **Run First**
**Basic functionality test that doesn't require premium API access**

Tests:
- Client initialization for all 5 premium APIs
- Automatic OAuth scope handling 
- Async context manager functionality

**Requirements:**
- Basic Lightcast API credentials
- No premium API access needed

**Usage:**
```bash
python test_premium_apis_basic.py
```

**Output:** `premium_api_basic_test_results.txt`

---

### 2. `test_premium_apis.py` 🚀 **Full Test Suite**
**Comprehensive endpoint testing (requires premium API access)**

Tests **49 premium endpoints** across:
- **Classification API** (9 endpoints) - Job title normalization, skill extraction, SOC validation
- **Similarity API** (12 endpoints) - Occupation/skill similarity, career transitions, skill gaps  
- **Occupation Benchmark API** (8 endpoints) - Salary benchmarks, employment trends, regional analysis
- **Career Pathways API** (8 endpoints) - Pathway analysis, career planning, industry transitions
- **Job Postings API** (10 endpoints) - Job search, market trends, skill demand analysis

**Requirements:**
- Premium Lightcast API access
- Valid premium OAuth scopes for each API

**Usage:**
```bash
python test_premium_apis.py
```

**Output:** `premium_api_test_results.txt`

## 🔧 Setup Requirements

### Environment Variables
Ensure your `.env` file contains:
```bash
LIGHTCAST_CLIENT_ID=your_client_id_here
LIGHTCAST_CLIENT_SECRET=your_client_secret_here
LIGHTCAST_BASE_URL=https://api.lightcast.io
LIGHTCAST_OAUTH_URL=https://auth.emsicloud.com/connect/token
LIGHTCAST_OAUTH_SCOPE=emsi_open  # Will be overridden per API automatically
```

### Premium API Access
For the full test suite, you need premium access to:
- `classification_api` scope
- `similarity_api` scope  
- `occupation_benchmark_api` scope
- `career_pathways_api` scope
- `job_postings_api` scope

## 📊 Test Output Format

Both scripts generate detailed results files with:

### Summary Statistics
- Total tests run
- Success/failure counts
- Success rate percentage
- Test duration and timestamps

### Detailed Results  
- Per-endpoint test results
- Error messages for failed tests
- Sample responses for successful tests
- Grouped by API for easy analysis

### Example Output Structure
```
================================================================================
PREMIUM API BASIC FUNCTIONALITY TEST RESULTS
================================================================================
Test Time: 2025-08-20 06:40:11
Total APIs tested: 5
Successful initializations: 5/5
Correct scope handling: 5/5
Overall success rate: 100.0%

Classification API:
  Initialization: SUCCESS
  Scope Handling: SUCCESS
  Async Context: SUCCESS
...
```

## 🚦 Testing Strategy

### Phase 1: Basic Validation ✅
Run `test_premium_apis_basic.py` first to verify:
- All premium API clients initialize correctly
- Automatic OAuth scope switching works  
- No syntax errors or import issues

### Phase 2: Full Premium Testing 🚀
If basic tests pass and you have premium access:
- Run `test_premium_apis.py` to test all endpoints
- Review results for any failed endpoints
- Use sample responses to verify data formats

## 🔍 Understanding Test Results

### Success Indicators ✅
- `SUCCESS` status in results
- Sample response data present
- No error messages

### Failure Analysis ❌
Common failure reasons:
- **Authentication**: Invalid credentials or expired tokens
- **Authorization**: Missing premium API access/scopes  
- **Rate Limiting**: Too many requests (429 errors)
- **Invalid Parameters**: Incorrect endpoint parameters
- **Service Issues**: Temporary API downtime

### Authentication Errors
```
Error: API request failed: 401 Unauthorized
```
→ Check your client credentials in `.env`

### Authorization Errors  
```
Error: API request failed: 403 Forbidden
```
→ Premium API access required for this endpoint

### Rate Limiting
```
Error: Rate limit exceeded. Reset at: 2025-08-20T07:00:00Z
```
→ Wait for rate limit reset or reduce test frequency

## 🛠️ Troubleshooting

### Issue: Import Errors
**Solution:** Ensure you're running from the project root directory

### Issue: Missing .env File  
**Solution:** Copy `.env.example` to `.env` and add your credentials

### Issue: Premium API Access
**Solution:** Contact Lightcast support to upgrade your API plan

### Issue: Network Errors
**Solution:** Check internet connection and Lightcast API status

## 📈 Expected Results

### Basic Test (No Premium Access)
- **Expected:** 100% success rate on initialization and scope handling
- **Time:** < 5 seconds
- **File size:** ~2KB

### Full Test (With Premium Access)  
- **Expected:** Variable success rate depending on API availability
- **Time:** 2-5 minutes  
- **File size:** ~50-100KB with response samples

## 🔄 Continuous Testing

These scripts can be integrated into CI/CD pipelines:

```yaml
# GitHub Actions example
- name: Test Premium API Clients
  run: |
    python test_premium_apis_basic.py
    cat premium_api_basic_test_results.txt
```

## 📞 Support

If tests consistently fail:
1. Check [Lightcast API Status](https://status.lightcast.io)
2. Review [Lightcast API Documentation](https://docs.lightcast.dev)  
3. Contact Lightcast Support with error details
4. Open an issue in this repository with test results