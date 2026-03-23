# combined-agent-examples

Sample services used for demos and testing (for example observability with AppDynamics and Splunk Observability Cloud).

## Services

| Folder | Stack | Role |
|--------|--------|------|
| [PaymentService](PaymentService/) | Java 17, Spring Boot | REST API for payments; in-memory storage; health checks and failure simulation |
| [OrderService](OrderService/) | Node.js, Express | REST API for orders; in-memory storage; health checks and failure simulation |

Each service has its own **README** with build steps, Docker/Make targets, environment variables, and API notes.

## License

See [LICENSE](LICENSE).
