# 📊 E-commerce Sales Data Pipeline 

This project builds an end-to-end **data pipeline and analytics workflow** using AWS services.
It simulates a real-world data engineering workflow from raw file ingestion to building an interactive dashboard that provides insights into sales, revenue, and customer trends.

## Dataset 
[Olist eCommerce dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) 


## 🔄 Workflow Steps
1. Ingest raw e-commerce sales data (csv) 
2. Upload raw dataset to AWS S3 (Bronze)
3. Use AWS Glue crawler to create schema
4. Use AWS Glue Job to 
5. Load final dataset into Redshift
6. Build dimensional tables and aggregated views using SQL
7. Create interactive dashboards using Amazon Quicksight


## 🛠️ Tools
- Python (pandas)
- AWS S3
- SQL (PostgreSQL / Redshift)
- Amazon Quicksight
