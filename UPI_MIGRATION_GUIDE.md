# UPI Sandbox to Production Migration Guide

This guide provides a safe, step-by-step process-driven approach to migrating from UPI sandbox integration to production UPI keys in MCPServer OS.

## Overview

Migrating from sandbox to production UPI integration requires careful planning, testing, and validation to ensure payment processing continuity, security, and compliance. This guide outlines the recommended approach for organizations using MCPServer OS.

## Prerequisites

Before beginning the migration, ensure you have:

1. **Production UPI Credentials** obtained from your chosen UPI gateway/provider (Razorpay, Paytm, PhonePe, etc.)
2. **Completed Sandbox Testing** - All UPI workflows tested and validated in sandbox environment
3. **Security Review** - Production key storage and handling procedures reviewed
- [ ] Compliance Validation - Ensure production usage complies with relevant regulations (PCI-DSS, RBI guidelines, etc.)
- [ ] Rollback Plan - Documented procedure to revert to sandbox if needed
- [ ] Stakeholder Alignment - Business, technical, and compliance teams aligned on migration plan

## Migration Process

### Phase 1: Preparation (Days 1-3)

#### 1.1 Environment Setup
- [ ] Create separate production configuration files (do not modify existing sandbox configs)
- [ ] Set up secure storage for production credentials (HashiCorp Vault, AWS Secrets Manager, or encrypted local storage)
- [ ] Configure monitoring and alerting for UPI transactions
- [ ] Set up dedicated logging for production UPI transactions
- [ ] Establish error tracking and notification procedures
- [ ] Prepare test transactions for validation (small amounts, test cards/accounts)

#### 1.2 Security Preparations
- [ ] Ensure production credentials are never stored in version control
- [ ] Verify encryption at rest for stored credentials
- [ ] Confirm access controls limit credential access to authorized personnel only
- [ ] Verify audit logging for credential access and usage
- [ ] Test credential rotation procedures
- [ ] Validate network segmentation between sandbox and production environments
- [ ] Confirm WAF/CDN rules are appropriate for production traffic
- [ ] Ensure DDoS protection is configured for production endpoints

#### 1.3 Testing Preparations
- [ ] Create comprehensive test plan covering:
  - Normal payment flows
  - Failed payment scenarios
  - Refund processes
  - Webhook handling
  - Idempotency verification
  - Error recovery procedures
- [ ] Prepare test data that won't affect live accounts
- [ ] Schedule migration during low-traffic period
- [ ] Notify relevant stakeholders of planned maintenance window
- [ ] Prepare rollback procedures and test them in isolation

### Phase 2: Configuration (Day 4)

#### 2.1 Isolate Production Configuration
- [ ] Create `upi-production.config.ts` or equivalent configuration file
- [ ] Do NOT overwrite sandbox configuration files
- [ ] Use environment-specific configuration loading:
  ```typescript
  const env = process.env.UPI_ENVIRONMENT || 'sandbox';
  const upiConfig = env === 'production' 
    ? require('./upi-production.config') 
    : require('./upi-sandbox.config');
  ```
- [ ] Ensure configuration separation prevents accidental sandbox→production confusion

#### 2.2 Secure Credential Storage
Choose ONE of these secure storage methods:

**Option A: Environment Variables (Least Secure - Only for temporary testing)**
```bash
# NEVER commit these to version control
UPI_PRODUCTION_MERCHANT_ID=your_production_merchant_id
UPI_PRODUCTION_API_KEY=your_production_api_key
UPI_PRODUCTION_API_SECRET=your_production_api_secret
UPI_PRODUCTION_WEBHOOK_SECRET=your_production_webhook_secret
```

**Option B: HashiCorp Vault (Recommended)**
```bash
# Store in Vault
vault kv put secret/mcpserver/upi/production \
  merchant_id="your_production_merchant_id" \
  api_key="your_production_api_key" \
  api_secret="your_production_api_secret" \
  webhook_secret="your_production_webhook_secret"
```

**Option C: AWS Secrets Manager**
```bash
# Store in AWS Secrets Manager
aws secretsmanager create-secret \
  --name mcpserver/upi/production \
  --secret-string '{"merchant_id":"your_production_merchant_id","api_key":"your_production_api_key","api_secret":"your_production_api_secret","webhook_secret":"your_production_webhook_secret"}'
```

**Option D: Encrypted Local Storage (Development Only)**
```bash
# For local development ONLY - NEVER in production
# Use libraries like 'dotenv-vault' or 'node-keytar'
```

#### 2.3 Configuration Validation
- [ ] Verify configuration loads correctly from chosen secure storage
- [ ] Test that sandbox configuration is unaffected
- [ ] Confirm environment variable precedence works correctly
- [ ] Validate that missing credentials fail gracefully with clear error messages
- [ ] Test configuration hot-reloading (if supported)
- [ ] Ensure configuration schema validation works
- [ ] Verify default values are safe and secure

### Phase 3: Testing (Days 5-7)

#### 3.1 Controlled Production Testing
**IMPORTANT: Use minimal amounts and test accounts only**

- [ ] Initiate smallest possible transaction amount (e.g., ₹1 or equivalent)
- [ ] Use test cards/accounts provided by your UPI provider for production testing
- [ ] Verify transaction appears in provider dashboard with correct status
- [ ] Verify webhook delivery and signature verification
- [ ] Verify refund initiation works correctly
- [ ] Verify transaction evidence generation in evidence ledger
- [ ] Verify PII redaction still works with production transactions
- [ ] Verify audit logging captures transaction details appropriately
- [ ] Verify error handling for common failure scenarios
- [ ] Verify idempotency keys prevent duplicate transactions
- [ ] Verify timeout handling works correctly
- [ ] Verify concurrent request handling works
- [ ] Verify currency conversion works correctly (if applicable)
- [ ] Verify tax calculation works correctly (if applicable)

#### 3.2 Load and Stress Testing
- [ ] Gradually increase transaction volume to expected levels
- [ ] Monitor system performance and resource utilization
- [ ] Verify error rates remain within acceptable bounds
- [ ] Confirm system recovers gracefully from load spikes
- [ ] Test retry mechanisms work correctly
- [ ] Verify circuit breaker behavior (if implemented)
- [ ] Validate monitoring and alerting thresholds are appropriate
- [ ] Test backup and recovery procedures under load

#### 3.3 Security Validation
- [ ] Verify production credentials are never exposed in logs
- [ ] Verify production credentials are never visible in browser dev tools
- [ ] Verify production credentials are never included in error responses
- [ ] Verify production credentials are never sent to clients
- [ ] Verify SQL injection attempts are blocked
- [ ] Verify XSS attempts are blocked
- [ ] Verify CSRF protection works for UPI endpoints
- [ ] Verify rate limiting prevents abuse
- [ ] Verify geographic restrictions work (if implemented)
- [ ] Verify IP whitelisting/blacklisting works (if configured)
- [ ] Verify API key rotation works without downtime
- [ ] Verify compromised key revocation procedures work

### Phase 4: Go-Live Preparation (Day 8)

#### 4.1 Final Validation
- [ ] All tests from Phase 3 pass consistently
- [ ] Monitoring dashboards show healthy system status
- [ ] Alerting rules are configured and tested
- [ ] Logging systems are capturing required data
- [ ] Backup procedures tested and verified
- [ ] Rollback procedures tested and verified
- [ ] Runbooks updated and validated
- [ ] On-call personnel trained and available
- [ ] Communication plan reviewed and approved
- [ ] Maintenance window confirmed with stakeholders
- [ ] Emergency contact list verified and distributed

#### 4.2 Pre-Go-Live Checklist
- [ ] Verify sandbox configuration remains unchanged and functional
- [ ] Verify production configuration is isolated and secure
- [ ] Verify environment variable separation works correctly
- [ ] Verify alerting thresholds are appropriate for production load
- [ ] Verify dashboard shows correct metrics for both environments
- [ ] Verify evidence ledger correctly separates sandbox/production data
- [ ] Verify audit trail captures environment information
- [ ] Verify data retention policies apply correctly to each environment
- [ ] Verify backup includes both configurations appropriately
- [ ] Verify disaster recovery plan accounts for both environments
- [ ] Verify training materials updated for production procedures
- [ ] Verify support documentation updated
- [ ] Verify compliance documentation updated

### Phase 5: Go-Live (Day 9)

#### 5.1 Controlled Production Cutover
- [ ] Notify stakeholders of maintenance window start
- [ ] Put system in maintenance mode (if applicable)
- [ ] Verify all monitoring systems are green
- [ ] Verify backup completed successfully
- [ ] Switch UPI configuration from sandbox to production:
  ```bash
  # Example using environment variable
  export UPI_ENVIRONMENT=production
  
  # Or update configuration file
  # In your deployment process, ensure UPI_ENVIRONMENT=production
  ```
- [ ] Restart services to load new configuration (if required)
- [ ] Verify health checks pass after restart
- [ ] Take snapshot of system state for potential rollback
- [ ] Notify stakeholders system is ready for testing
- [ ] Perform first production transaction with minimal amount
- [ ] Verify transaction completes successfully
- [ ] Verify evidence generation works correctly
- [ ] Verify audit trail captures environment correctly
- [ ] Verify monitoring shows transaction correctly
- [ ] Verify alerting does not fire falsely
- [ ] Notify stakeholders of successful first transaction
- [ ] Gradually increase transaction volume to normal levels
- [ ] Monitor closely for first 2 hours
- [ ] Monitor normally for remaining maintenance window
- [ ] Notify stakeholders of successful migration completion
- [ ] Return system to normal operation

#### 5.2 Post-Go-Live Validation (First 24-48 Hours)
- [ ] Monitor transaction success rates closely
- [ ] Monitor error rates and types
- [ ] Monitor performance metrics
- [ ] Monitor resource utilization
- [ ] Monitor security alerts
- [ ] Monitor audit logs for anomalies
- [ ] Monitor evidence ledger integrity
- [ ] Monitor backup completion
- [ ] Monitor disk space usage
- [ ] Monitor log rotation and retention
- [ ] Verify refund processes work correctly
- [ ] Verify webhook retry mechanisms work
- [ ] Verify idle connection cleanup works
- [ ] Verify memory usage remains stable
- [ ] Verify garbage collection works correctly
- [ ] Verify no accumulation of temporary files
- [ ] Verify database connection pool health
- [ ] Verify Redis connection pool health
- [ ] Verify external API connection health
- [ ] Verify SSL/TLS certificate validity
- [ ] Verify DNS resolution works correctly
- [ ] Verify load balancer health checks pass
- [ ] Verify auto-scaling works correctly (if applicable)
- [ ] Verify failover mechanisms work (if applicable)

### Phase 6: Ongoing Operations

#### 6.1 Daily Operations
- [ ] Review transaction success rates
- [ ] Review error logs and alerts
- [ ] Review performance metrics
- [ ] Review security logs
- [ ] Review audit trails for anomalies
- [ ] Monitor credential expiration dates
- [ ] Review evidence ledger growth
- [ ] Monitor backup success rates
- [ ] Monitor storage utilization
- [ ] Monitor network utilization
- [ ] Monitor CPU and memory utilization
- [ ] Monitor garbage collection efficiency
- [ ] Review third-party service status pages
- [ ] Review provider notifications and updates

#### 6.2 Weekly Operations
- [ ] Review transaction trends and patterns
- [ ] Review security scan results
- [ ] Review penetration test results (if conducted regularly)
- [ ] Review compliance reporting requirements
- [ ] Review evidence ledger for tampering attempts
- [ ] Test recovery procedures (quarterly)
- [ ] Review and update runbooks
- [ ] Review and update disaster recovery plan
- [ ] Review and update communication plan
- [ ] Review and update training materials
- [ ] Review and update security policies
- [ ] Review and update access controls
- [ ] Review and update monitoring thresholds
- [ ] Review and update alerting rules
- [ ] Review and update logging configuration
- [ ] Review and update retention policies

#### 6.3 Monthly Operations
- [ ] Conduct full disaster recovery drill
- [ ] Rotate production credentials (if required by provider)
- [ ] Review and update incident response plan
- [ ] Review and update business continuity plan
- [ ] Review and update data retention policies
- [ ] Review and update archival procedures
- [ ] Review and update legal hold procedures
- [ ] Review and update vendor management procedures
- [ ] Review and update SLA monitoring
- [ ] Review and update capacity planning
- [ ] Review and update technology roadmap
- [ ] Review and update training completion status
- [ ] Review and update certification status
- [ ] Review and update insurance coverage
- [ ] Review and update regulatory compliance status

## Rollback Procedures

If issues arise during or after migration, follow these rollback procedures:

### Immediate Rollback (During Migration Window)
1. Immediately stop processing new UPI transactions
2. Switch UPI_ENVIRONMENT back to sandbox
3. Restart services to load sandbox configuration
4. Verify sandbox functionality with test transaction
5. Notify stakeholders of rollback
6. Investigate cause of failure
7. Document lessons learned
8. Reschedule migration after issues resolved

### Delayed Rollback (After Migration Window)
1. Assess impact and feasibility of continued production operation
2. If rollback deemed necessary:
   - Notify stakeholders of planned rollback
   - Schedule maintenance window
   - Switch UPI_ENVIRONMENT back to sandbox
   - Restart services
   - Verify sandbox functionality
   - Notify stakeholders of rollback completion
   - Investigate production issues in isolated environment
   - Document lessons learned
   - Plan corrective actions
   - Reschedule migration after issues resolved

## Monitoring and Alerting

### Key Metrics to Monitor
- Transaction success rate (target: >99.5%)
- Average transaction processing time
- Error rate by type
- Webhook delivery success rate
- Refund processing time
- Evidence ledger growth rate
- Audit log volume
- Backup success rate
- Storage utilization
- CPU utilization
- Memory utilization
- Network utilization
- Database connection pool usage
- Redis connection pool usage
- External API response times
- External API error rates
- SSL/TLS certificate expiration
- Domain expiration

### Critical Alerts
- Transaction success rate drops below 99%
- Error rate increases above 0.5%
- Webhook delivery success rate drops below 95%
- Evidence ledger tampering detected
- Audit log shows unauthorized access
- Backup failure for 2 consecutive cycles
- Storage utilization exceeds 85%
- CPU utilization exceeds 80% for 5+ minutes
- Memory utilization exceeds 85% for 5+ minutes
- Database connection pool exhaustion
- Redis connection pool exhaustion
- External API error rate increases above 5%
- SSL/TLS certificate expires in <30 days
- Domain expires in <30 days

## Compliance Considerations

### PCI-DSS
- Ensure cardholder data is never stored
- Ensure encryption of transmission (TLS 1.2+)
- Ensure regular security scanning
- Ensure access controls are implemented
- Ensure monitoring and logging are implemented
- Ensure regular penetration testing
- Ensure incident response plan is maintained
- Ensure antivirus software is used and updated
- Ensure security policies are maintained
- Ensure vendor management is maintained
- Ensure incident response plan is tested regularly

### RBI Guidelines
- Ensure data localization requirements met
- Ensure audit trail requirements met
- Ensure customer grievance redressal mechanism works
- Ensure transaction limits compliance
- Ensure KYC/AML requirements met (where applicable)
- Ensure transaction monitoring for suspicious activity
- Ensure suspicious transaction reporting works
- Ensure customer education and awareness efforts
- Ensure technology adoption framework compliance
- Ensure cyber crisis management plan works
- Ensure security operations center effectiveness
- Ensure vendor risk management works
- Ensure subscription-based transaction controls work
- Ensure offline transaction limits compliance
- Ensure tokenization requirements met (if applicable)
- Ensure fraud risk management works
- Ensure customer authentication works
- Ensure device binding works (if applicable)

### Data Protection (DPDP Act)
- Ensure personal data minimization
- Ensure purpose limitation compliance
- Ensure storage limitation compliance
- Ensure accuracy maintenance
- Ensure integrity and confidentiality measures
- Ensure accountability documentation generatable
- Ensure data subject rights facilitation
- Ensure cross-border transfer restrictions compliance
- Ensure data protection impact assessment capability
- Ensure privacy by design and default principles
- Ensure data protection officer appointment (if required)
- Ensure breach notification procedure works
- Ensure record of processing activities maintained
- Ensure data protection training conducted
- Ensure data protection policies maintained
- Ensure data protection audits conducted
- Ensure vendor contracts include data protection clauses

## Troubleshooting

### Common Issues and Solutions

#### Connection Issues
**Symptoms:** Timeout errors, connection refused errors
**Solutions:**
- Verify network connectivity to UPI endpoint
- Verify DNS resolution works correctly
- Verify firewall allows outbound connections to UPI endpoints
- Verify proxy configuration (if used) is correct
- Verify SSL/TLS handshake works (check certificate validity)
- Verify service status on provider status page
- Verify rate limiting isn't blocking legitimate traffic
- Verify IP whitelisting includes your production IPs
- Verify geographic restrictions aren't blocking your traffic

#### Authentication Issues
**Symptoms:** 401 Unauthorized, invalid signature errors
**Solutions:**
- Verify production credentials are correct and active
- Verify credential rotation hasn't occurred without update
- Verify timestamp synchronization (NTP working)
- Verify signature generation algorithm matches provider spec
- Verify request parameters are included in signature correctly
- Verify HTTP method and URI are correct for signature
- Verify request body is included in signature correctly (if required)
- Verify nonce/timestamp isn't reused or too old
- Verify HTTP headers are included in signature correctly (if required)
- Verify URL encoding is handled correctly
- Verify special characters in credentials are handled correctly

#### Webhook Issues
**Symptoms:** Missing webhooks, invalid signature errors, delivery failures
**Solutions:**
- Verify webhook endpoint is publicly accessible
- Verify webhook endpoint returns 200 OK response
- Verify webhook signature verification algorithm matches provider
- Verify webhook endpoint isn't blocking provider IPs
- Verify webhook endpoint handles duplicate deliveries correctly
- Verify webhook endpoint is idempotent
- Verify webhook retry logic matches provider expectations
- Verify webhook logging captures delivery attempts
- Verify webhook error responses are appropriate
- Verify webhook timeout settings are appropriate
- Verify webhook HTTPS certificate is valid and trusted
- Verify webhook endpoint isn't rate limiting provider
- Verify webhook data format matches provider expectations
- Verify webhook event types match subscription
- Verify webhook timestamp validation works correctly

#### Payment Issues
**Symptoms:** Failed payments, incorrect amounts, duplicate charges
**Solutions:**
- Verify amount formatting matches provider specification
- Verify currency code is correct
- Verify tax calculation is correct (if applicable)
- Verify fee calculation is correct (if applicable)
- Verify discount calculation is correct (if applicable)
- Verify customer information is correct and complete
- Verify shipping information is correct (if applicable)
- Verify billing information is correct (if applicable)
- Verify order ID uniqueness and format
- Verify item descriptions are correct and complete
- Verify metadata format matches provider expectations
- Verify custom fields are used correctly (if supported)
- Verify redirect URLs are correct and accessible
- Verify callback URLs are correct and accessible
- Verify payment method selection works correctly
- Verify saved instruments work correctly (if applicable)
- Verify EMI options work correctly (if applicable)
- Verify wallet integration works correctly (if applicable)
- Verify international card handling works correctly (if applicable)
- Verify currency conversion works correctly (if applicable)
- Verify dynamic pricing works correctly (if applicable)
- Verify subscription handling works correctly (if applicable)
- Verify installment handling works correctly (if applicable)
- Verify cash on delivery handling works correctly (if applicable)
- Verify bank transfer handling works correctly (if applicable)
- Verify UPI intent flow works correctly (if applicable)
- Verify UPI collect flow works correctly (if applicable)
- Verify UPI QR code flow works correctly (if applicable)
- Verify UPI deep linking works correctly (if applicable)
- Verify UPI SDK integration works correctly (if applicable)

#### Evidence Ledger Issues
**Symptoms:** Missing evidence, hash chain breaks, tampering detected
**Solutions:**
- Verify evidence generation triggers are working
- Verify evidence storage is functioning correctly
- Verify hash chain calculation is correct
- Verify previous hash linking is correct
- Verify evidence tampering detection algorithm works
- Verify evidence retrieval works correctly
- Verify evidence export works correctly
- Verify evidence import works correctly (if applicable)
- Verify evidence retention policies are working
- Verify evidence archiving works correctly (if applicable)
- Verify evidence encryption works correctly (if applicable)
- Verify evidence access controls are working
- Verify evidence audit logging works correctly
- Verify evidence backup procedures work correctly
- Verify evidence disaster recovery procedures work correctly
- Verify evidence validation procedures work correctly
- Verify evidence versioning works correctly (if applicable)
- Verify evidence schema migrations work correctly
- Verify evidence indexing works correctly
- Verify evidence querying works correctly
- Verify evidence aggregation works correctly
- Verify evidence reporting works correctly
- Verify evidence alerting works correctly
- Verify evidence dashboard works correctly

## Appendix A: UPI Provider-Specific Notes

### Razorpay Production
- **Endpoint**: `https://api.razorpay.com/v1/`
- **Authentication**: Basic Auth with key_id as username and key_secret as password
- **Webhooks**: Verify signature using `X-Razorpay-Signature` header
- **Test Cards**: Use Razorpay test card numbers
- **Production Live**: Use actual card numbers
- **Refunds**: Use refund API endpoint
- **Webhook Events**: `payment.authorized`, `payment.captured`, `payment.failed`, `refund.processed`, `refund.failed`

### Paytm Production
- **Endpoint**: `https://securegw.paytm.in/theia/processTransaction` (for transaction processing)
- **Authentication**: Checksum based on merchant key
- **Webhooks**: Verify checksum using Paytm provided utility
- **Test Credentials**: Use Paytm provided test merchant ID and key
- **Production Live**: Use actual merchant ID and key
- **Refunds**: Use refund API endpoint
- **Webhook Events**: Various transaction status callbacks

### PhonePe Production
- **Endpoint**: `https://api-preprod.phonepe.com/apis/pg-sandbox` (sandbox)
- **Endpoint**: `https://api.phonepe.com/apis/pg` (production)
- **Authentication**: SHA256 with salt key index
- **Webhooks**: Verify checksum using PhonePe provided utility
- **Test Credentials**: Use PhonePe provided test merchant ID and key
- **Production Live**: Use actual merchant ID and key
- **Refunds**: Use refund API endpoint
- **Webhook Events**: Various transaction status callbacks

## Appendix B: Testing Checklist

### Minimum Viable Test Set
Before considering migration complete, verify these core transactions work:

1. **Basic Payment**
   - [ ] ₹1 transaction succeeds
   - [ ] ₹100 transaction succeeds
   - [ ] ₹1000 transaction succeeds
   - [ ] ₹5000 transaction succeeds (if within limits)

2. **Failed Payment Scenarios**
   - [ ] Insufficient funds transaction fails appropriately
   - [ ] Expired card transaction fails appropriately
   - [ ] Invalid CVV transaction fails appropriately
   - [ ] Fraud suspected transaction fails appropriately
   - [ ] Transaction limit exceeded fails appropriately
   - [ ] Invalid amount transaction fails appropriately
   - [ ] Duplicate transaction prevented by idempotency
   - [ ] Network timeout handled appropriately
   - [ ] Server error handled appropriately
   - [ ] Client error handled appropriately

3. **Refund Scenarios**
   - [ ] Full refund succeeds
   - [ ] Partial refund succeeds
   - [ ] Multiple partial refunds succeed (up to original amount)
   - [ ] Refund after partial refund succeeds
   - [ ] Refund of refund fails appropriately
   - [ ] Refund after chargeback fails appropriately
   - [ ] Refund to expired card handled appropriately
   - [ ] Refund to cancelled account handled appropriately
   - [ ] Refund timeframe compliance verified

4. **Webhook Scenarios**
   - [ ] Successful payment webhook received and verified
   - [ ] Failed payment webhook received and verified
   - [ ] Refund initiated webhook received and verified
   - [ ] Refund succeeded webhook received and verified
   - [ ] Refund failed webhook received and verified
   - [ ] Chargeback received webhook received and verified
   - [ ] Dispute opened webhook received and verified
   - [ ] Disclose closed webhook received and verified
   - [ ] Webhook retry after failure works
   - [ ] Webhook duplicate delivery handled correctly
   - [ ] Webhook out of order delivery handled correctly
   - [ ] Webhook missing required fields handled appropriately
   - [ ] Webhook invalid signature handled appropriately

5. **Edge Cases**
   - [ ] Maximum allowed transaction amount tested
   - [ ] Minimum allowed transaction amount tested
   - [ ] Zero amount transaction handled appropriately
   - [ ] Negative amount transaction handled appropriately
   - [ ] Non-numeric amount handled appropriately
   - [ ] Very long description handled appropriately
   - [ ] Special characters in description handled appropriately
   - [ ] Emoji in description handled appropriately (if supported)
   - [ ] Unicode characters in description handled appropriately
   - [ ] HTML in description sanitized appropriately
   - [ ] SQL injection in description prevented appropriately
   - [ ] XSS in description prevented appropriately
   - [ ] Concurrent requests handled correctly
   - [ ] Rate limiting triggers appropriately
   - [ ] Circuit breaker triggers appropriately (if implemented)
   - [ ] Fallback mechanisms work appropriately (if implemented)
   - [ ] Graceful degradation works appropriately
   - [ ] Recovery after failure works appropriately
   - [ ] Data consistency maintained after failures
   - [ ] Audit trail integrity maintained after failures
   - [ ] Evidence ledger integrity maintained after failures
   - [ ] Backup and restore works correctly
   - [ ] Disaster recovery plan works correctly
   - [ ] Rollback procedure works correctly

## Appendix C: Emergency Procedures

### Suspected Fraud or Security Incident
1. Immediately suspend UPI transaction processing
2. Notify security team and relevant stakeholders
3. Preserve all logs and evidence
4. Do NOT alter any systems or data
5. Follow incident response plan
6. Contact UPI provider fraud department
7. Consider notifying relevant authorities if required by law
8. Prepare customer communication if data breach suspected
9. Implement additional monitoring and controls
10. Conduct forensic investigation
11. Implement corrective actions
12. Test corrective actions in isolated environment
13. Gradually resume operations with enhanced monitoring
14. Review and update security policies and procedures
15. Conduct security training for relevant personnel
16. Update incident response plan based on lessons learned

### Service Outage with UPI Provider
1. Verify outage on provider status page
2. Notify stakeholders of known provider issue
3. Activate alternative payment methods if available
4. Communicate delay to affected customers
5. Monitor provider status for restoration
6. Verify service restoration with test transaction
7. Notify stakeholders of service restoration
8. Resume normal UPI transaction processing
9. Monitor for delayed or duplicated transactions
10. Reconcile transaction records with provider reports
11. Follow up with customers on any discrepancies
12. Document incident and response
13. Review and update business continuity plan
14. Update incident response plan based on lessons learned

### Data Loss or Corruption
1. Immediately suspend all transaction processing
2. Notify stakeholders and data protection officer
3. Isolate affected systems to prevent further corruption
4. Do NOT attempt to fix corruption without expert guidance
5. Follow disaster recovery plan
6. Restore from last known good backup
7. Verify restored data integrity
8. Verify evidence ledger integrity
9. Verify audit log integrity
10. Gradually resume operations with enhanced validation
11. Perform data reconciliation where possible
12. Notify affected parties if required by law or contract
13. Implement additional backup and validation controls
14. Review and update backup procedures
15. Review and update data validation procedures
16. Conduct training on updated procedures
17. Update disaster recovery plan based on lessons learned

## Conclusion

Migrating from UPI sandbox to production is a significant undertaking that requires careful planning, execution, and validation. By following this guide, organizations can minimize risk and ensure a smooth transition to production UPI processing while maintaining security, compliance, and operational integrity.

Remember that the migration is not complete until:
- All tests pass consistently in production
- Monitoring shows stable, healthy operation
- Security controls are verified effective
- Compliance requirements are met
- Stakeholders confirm satisfaction
- Documentation is current and accurate
- Runbooks and procedures are validated
- Team is trained and confident in operations

Regular review and improvement of these processes will ensure continued secure and reliable UPI payment processing in your MCPServer OS deployment.