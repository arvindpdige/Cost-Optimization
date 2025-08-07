# Current Scenario:
Service: Cosmos DB serverless
Records older than three months are rarely accessed.
Database size has significantly grown
Record Size: Each billing record can be as large as 300 KB.
Total Records: The database currently holds over 2 million records.
Access Latency: When an old record is requested, it should still be served, with a response time in the order of seconds

# Requirements:
Simplicity & Ease of Implementation
No Data Loss
No Downtime
No Changes to API Contracts

# Solution:
As Data size is incresing and need to store data we can use Azure Storage service. Which is effective with its tier structure like HOT, COLD & ARCHIVE.
As Cosmos DB can store NO-SQl data, we can conside Table storage type, 
  No support for tier strategy.
  Each record can be 300KB and having more than 2 million records in Cosmos DB,  
  limitation upto 1MB for each record, may create issue if record size grows.
  No support for json structure.

With Azure Blob storage, 
  supports record size of more than 300kb 
  supports natively json structure 
  no chnages reqired with respect to API.
  Auto support for tiering strategy
  Cheapest Long-Term Storage than Cosmos DB
 
- Create ADLS Gen2 with Hierarchical Namespace  
- Partition Data based on Year/Month/Day
- Implement redundancy as per requirement (LRS, ZRS, GRS, RA-GRS)
- Use ADF for initial data fetch and function app to fetch changed data
- Apply incremental logic which can only fetch data which is not present in Blob Storage
- Create Life Cycle Mnagement Rule for movind Data older than 90 days to cool tier
- Implement Soft delete protection


# Considerations taking into account:
600 GB total historical data of 2years
25 GB new data added every month (~300 GB/year).
After 3 months: only 75 GB kept in Cosmos DB, rest (525 GB) archived to Blob Storage (Cool Tier).
Use Azure Data Factory (ADF) for initial migration.
Use Azure Function App (daily trigger) to sync ~833 MB/day (25 GB/month ÷ 30 days).

Flow Chart:
          ┌─────────────────────┐
          │  Cosmos DB          │
          │  (2M+ records)      │
          └────────┬────────────┘
                   │
          Initial Bulk Load (Once)
                   ▼
          ┌─────────────────────┐
          │ Azure Data Factory  │
          │ - Cosmos DB → Blob  │
          └────────┬────────────┘
                   │
         (JSON / Parquet in Blob)
                   │
    ┌──────────────┴──────────────┐
    ▼                             ▼
Change Feed                New Inserts / Updates
   ▼                                  │
Azure Function App         (Cosmos DB Trigger)
   ▼                                  ▼
Write to Blob (Append)       or Write to Archive


Cosmos DB (75 GB):
Estimated Monthly Cost:
RU/s Cost:
(60M RUs / 100K) × $0.25 = $150/month
Storage Cost (75 GB):
75 × $0.25 = $18.75/month
Total Cosmos DB Monthly: ≈ $169/month

Blob Storage (Cool Tier – 525 GB):
Monthly Cost:
Storage (525 GB) = 525 × $0.01 = $5.25/month
Occasional reads/writes — let’s assume:
10K reads & 10K writes per month
Cost: ~$2/month
Total Blob Storage Monthly: ≈ $7/month

Azure Data Factory (ADF) – One-Time Migration (525 GB):
One-time cost:
Data movement: 525 × $0.25 = $131
Compute/pipeline orchestration: $5
Total ADF One-Time: ≈ $136

Azure Function App – Daily Delta Sync (~833 MB/day)
First 1M/month is free
Daily execution (30x/month)
Each run processes ~833 MB (~5,000 documents/day)
Execution time: ~1 min per run
Memory: ~1.5 GB (assuming JSON handling, HTTP, I/O)
1.5 GB × 60s × 30 = 2700 GB-s
Total Function App Monthly: ≈ $0.05/month

Final Recap (Post Migration Monthly):
Cosmos DB: ~$169
Blob Storage: ~$7
Function App: ~$0.05
Total: ~$176/month (Post-migration)

Approx Initial Cost of Cosmos DB (600 GB):
$200–$212/month.

Conclusion:
After Migration: 
1st month cost will be less by ~25-35GB
1st month onwards cost will get reduced by $150/month (As ADF won't be part of process)


