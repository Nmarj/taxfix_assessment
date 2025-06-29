# Build the image
```bash
docker build -t fakerapi .
```

# Run the container
```bash
docker run -it --rm fakerapi
```
# Debug container
```bash
docker run -it --rm fakerapi bash
```


# Propose a production approach

## What changes would you make to your code?

1. CDC (Change Data Capture), I would first check whether we’re performing a full load or an incremental load. Based on that, I would pull data either from a specified date or, by default, from the earliest available data.
2. Schema Evolution. When supported by the API, I would retrieve metadata to identify newly added fields and ensure they are dynamically included and backfilled in the dataset.
3. Develop dbt models to provide stakeholders with the necessary data, making it accessible through the BI tool instead of printing it to standard output.
4. Use a Data Lake or Data Warehouse for persistence, rather than transient in-memory storage.
5. Instead of masking PII fields with hardcoded strings, push the raw data as-is and apply masking at the Data Warehouse level (e.g., using Snowflake Data Masking).
6. I’m relying heavily on computed_fields, which isn’t ideal since they aren’t validated. In a production environment, I would have flattened the JSON structure. However, I chose not to in this case to easily allow for assigning default values (`'****'`) to masked fields.

## Which solutions would you propose?

1. Source & Version Control
    - Git (e.g. GitHub, GitLab, Bitbucket)
Why:
   - Central place for code and config
   - Triggers builds and deployments

⸻

2. Environments
   - To ensure safe, stable, and reliable deployments (automated testing at multiple stages).
      - Dev → Staging → Production
      - Managed via GitOps (e.g., Argo CD) or Helm/Kustomize

⸻

1. CI/CD Pipeline
  -  GitHub Actions, Jenkins, etc.
Why: 
   - We can trigger additional tests to make sure our data is production ready
   - We can build and push oud Docker images to a private container repository (GCR, ECR)
   - From here, we can trigger deployment to staging/production

⸻

4. Orchestration with Kubernetes
   - We'll use it to deploy, scale, and manage containerized applications automatically (GKE, EKS, etc.)
   - We can also use Karpenter to dynamically manage nodes based on pod resource requirements.

⸻

5. Data Ingestion Layer
- Depending on our needs:
    - Stream processing: Apache Kafka, Amazon Kinesis, or Google Pub/Sub for real-time data.
    - Batch ingestion: Schedule our DAGS with Apache Airflow.

⸻

6. Storage & Data Lake
   - Object storage: S3, GCS, or Azure Blob for raw data.
   - Data warehouse: Snowflake, BigQuery, etc. for structured analytics.

⸻

7. Infrastructure as Code (IaC)
   - Terraform: define, provision, and manage cloud infrastructure

⸻

8. Monitoring & Logging
   - New Relic, Grafana: Metrics
   - Alerting: Opsgenie, Slack integrations

⸻

9. Security
    - Secrets Management: Vault, Sealed Secrets, GCP Secret Manager...
    - Least privilege access via IAM.
