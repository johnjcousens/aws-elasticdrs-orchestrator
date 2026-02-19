# Implementation Plan: DRS Rate Limit Handling

## Overview

This implementation plan covers the creation of comprehensive DRS API rate limit handling infrastructure for the AWS DR Orchestration Platform. The implementation follows a bottom-up approach, building foundational utilities first, then integrating them into the existing Lambda handlers.

All code follows PEP 8 standards with type hints, docstrings, and logging module usage.

## Tasks

- [ ] 1. Implement Retry Decorator Module
  - [ ] 1.1 Create `lambda/shared/retry_decorator.py` with RetryConfig class
    - Define RetryConfig dataclass with max_retries, base_delay, max_delay, jitter_range
    - Define RETRYABLE_ERRORS constant set
    - Implement RetryExhaustedException class
    - _Requirements: 1.5, 1.6, 1.7, 1.8_
  
  - [ ] 1.2 Implement `drs_retry` decorator function
    - Implement exponential backoff calculation with jitter
    - Handle ClientError and extract error codes
    - Log retry attempts with attempt number and delay
    - Raise RetryExhaustedException when max retries exceeded
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.9_
  
  - [ ] 1.3 Write property test for retry on retryable errors
    - **Property 1: Retry on Retryable Errors**
    - **Validates: Requirements 1.1, 1.2, 1.3**
  
  - [ ] 1.4 Write property test for exponential backoff with jitter
    - **Property 2: Exponential Backoff with Jitter**
    - **Validates: Requirements 1.4, 1.6, 1.7**
  
  - [ ] 1.5 Write property test for retry configuration
    - **Property 3: Retry Configuration Respected**
    - **Validates: Requirements 1.5, 1.6, 1.7**
  
  - [ ] 1.6 Write property test for retry exhaustion
    - **Property 4: Retry Exhaustion Exception**
    - **Validates: Requirements 1.8**

- [ ] 2. Implement Token Bucket Rate Limiter Module
  - [ ] 2.1 Create `lambda/shared/rate_limiter.py` with TokenBucket class
    - Implement thread-safe token bucket with threading.Lock
    - Implement token refill based on elapsed time
    - Implement acquire() method with optional timeout
    - Implement try_acquire() non-blocking method
    - Implement available_tokens() query method
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8_
  
  - [ ] 2.2 Implement regional rate limiter factory
    - Create get_rate_limiter() function for region-specific instances
    - Use module-level dict with lock for singleton pattern
    - Default rate of 10 TPS and capacity of 20 tokens
    - _Requirements: 2.9, 2.10, 3.8_
  
  - [ ] 2.3 Write property test for token bucket invariants
    - **Property 5: Token Bucket Invariants**
    - **Validates: Requirements 2.1, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8**
  
  - [ ] 2.4 Write property test for thread safety
    - **Property 6: Token Bucket Thread Safety**
    - **Validates: Requirements 2.2**

- [ ] 3. Checkpoint - Verify foundational modules
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 4. Implement Metrics Publisher Module
  - [ ] 4.1 Create `lambda/shared/metrics_publisher.py`
    - Define METRICS_NAMESPACE constant as "DRS/RateLimits"
    - Implement metric buffer queue for batching
    - Implement background publisher thread
    - _Requirements: 4.5, 4.6, 4.7_
  
  - [ ] 4.2 Implement metric publishing functions
    - Implement publish_rate_limit_error() with error type dimension
    - Implement publish_retry_metric() with attempt dimension
    - Implement publish_retry_exhausted() metric
    - Implement publish_api_call_metric() for success tracking
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.8_
  
  - [ ] 4.3 Write property test for metrics publication
    - **Property 9: Metrics Publication Correctness**
    - **Validates: Requirements 4.1, 4.2, 4.3, 4.4**

- [ ] 5. Implement DRS Client Wrapper Module
  - [ ] 5.1 Create `lambda/shared/drs_client.py` with DRSClient class
    - Integrate with retry_decorator and rate_limiter
    - Support cross-account operations via account_context
    - Implement _rate_limited_call() internal method
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.6_
  
  - [ ] 5.2 Implement DRS API method wrappers
    - Wrap describe_source_servers() with rate limiting
    - Wrap describe_jobs() with rate limiting
    - Wrap start_recovery() with rate limiting
    - Wrap describe_recovery_instances() with rate limiting
    - Wrap terminate_recovery_instances() with rate limiting
    - Implement RateLimitedPaginator for paginated operations
    - _Requirements: 3.5, 3.7_
  
  - [ ] 5.3 Write property test for rate limiting integration
    - **Property 7: DRS Client Rate Limiting Integration**
    - **Validates: Requirements 3.2, 3.3**
  
  - [ ] 5.4 Write property test for region-specific rate limiters
    - **Property 8: Region-Specific Rate Limiters**
    - **Validates: Requirements 3.8**

- [ ] 6. Checkpoint - Verify DRS client wrapper
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 7. Implement Job Throttler Module
  - [ ] 7.1 Create `lambda/shared/job_throttler.py` with JobThrottler class
    - Implement wait_for_capacity() with polling loop
    - Implement check_capacity() for non-blocking status check
    - Implement _get_active_job_count() using DRS API
    - Support configurable threshold via environment variable
    - _Requirements: 6.1, 6.2, 6.4, 6.5, 6.6_
  
  - [ ] 7.2 Implement timeout handling
    - Raise TimeoutError after configured timeout (default 10 min)
    - Include current job count and wait duration in error
    - _Requirements: 6.7_
  
  - [ ] 7.3 Write property test for capacity check behavior
    - **Property 10: Job Throttler Capacity Check**
    - **Validates: Requirements 6.1, 6.2, 6.6**
  
  - [ ] 7.4 Write property test for timeout behavior
    - **Property 11: Job Throttler Timeout**
    - **Validates: Requirements 6.7**

- [ ] 8. Implement Error Logging and Escalation
  - [ ] 8.1 Add structured logging to all modules
    - Use JSON format for log entries
    - Include correlation IDs via AWS request context
    - Categorize by severity (WARNING for retryable, CRITICAL for exhausted)
    - _Requirements: 7.1, 7.2, 7.4, 7.5, 7.7_
  
  - [ ] 8.2 Implement SNS escalation notifications
    - Create send_rate_limit_escalation() function
    - Include operation, region, error details, retry count
    - Include actionable remediation steps in message
    - Integrate with existing DRS_ALERTS_TOPIC_ARN
    - _Requirements: 7.3, 7.6_
  
  - [ ] 8.3 Write property test for structured error logging
    - **Property 12: Structured Error Logging**
    - **Validates: Requirements 7.1, 7.2, 7.4, 7.5**

- [ ] 9. Checkpoint - Verify all shared modules
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 10. Integrate with Execution Handler
  - [ ] 10.1 Update execution-handler to use DRSClient
    - Replace boto3.client("drs") calls with DRSClient
    - Update start_drs_recovery() to use rate-limited client
    - Update poll_wave_status() to use rate-limited client
    - Update terminate_recovery_instances() to use rate-limited client
    - _Requirements: 1.1, 1.2, 1.3, 2.1, 3.1_
  
  - [ ] 10.2 Add job throttling to recovery job creation
    - Integrate JobThrottler before start_recovery() calls
    - Handle TimeoutError with appropriate error response
    - _Requirements: 6.1, 6.2, 6.7_

- [ ] 11. Integrate with Query Handler
  - [ ] 11.1 Update query-handler to use DRSClient
    - Replace boto3.client("drs") calls with DRSClient
    - Update get_drs_regional_capacity() to use rate-limited client
    - Update get_drs_account_capacity_all_regions() to use rate-limited client
    - _Requirements: 1.1, 1.2, 1.3, 2.1, 3.1_

- [ ] 12. Add CloudFormation Resources for Monitoring
  - [ ] 12.1 Add CloudWatch alarms to monitoring template
    - Create alarm for sustained rate limit errors (10 in 5 min)
    - Create alarm for retry exhaustion events (3 in 5 min)
    - Configure SNS actions for alarm notifications
    - _Requirements: 5.1, 5.2, 5.3, 5.4_
  
  - [ ] 12.2 Add SNS topic for rate limit alerts
    - Create DRS-RateLimitAlerts SNS topic if not exists
    - Add environment variable for topic ARN
    - _Requirements: 5.5, 5.6, 5.7_

- [ ] 13. Final Checkpoint - Full integration testing
  - Ensure all tests pass, ask the user if questions arise.
  - Run `./scripts/deploy.sh test --validate-only` to verify deployment readiness

## Notes

- All tasks are required for comprehensive implementation
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties (100+ iterations)
- Unit tests validate specific examples and edge cases
- All code must follow PEP 8 with type hints and docstrings
- Deploy using `./scripts/deploy.sh test` per CI/CD workflow enforcement
