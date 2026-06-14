# CreditSense AI — Known Issues & Technical Debt

## Resolved
- [v1.1.0] Credit model calibration bias fixed with Platt Scaling
- [v1.0.1] Duplicate rows in credit_cleaned.csv fixed
- [v1.0.1] Database loader fixed with bulk insert + savepoints
- [v1.0.1] JSON snake_case/camelCase mapping fixed in Spring Boot

## Open — Planned for Post-Launch
- Kafka integration for full async transaction streaming (Month 4 partial)
- Model drift monitoring — alert if AUC drops below 0.82 on live data
- HTTPS/TLS setup on AWS EC2 (Month 4 deployment)
- Swagger authentication token persistence across page refresh
- Redis cluster mode for high availability (single node currently)

## Acknowledged Production Gaps (BCA Scope)
- No HSM for JWT secret management
- No PCI-DSS compliance layer
- No VAPT conducted
- Synthetic training data only — real NBFC data would improve AUC by ~3-5%
