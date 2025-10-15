# 📊 E-commerce Sales Data Pipeline 

This project builds an end-to-end **data pipeline and analytics workflow** using AWS services.
It simulates a real-world data engineering workflow from raw file ingestion to building an interactive dashboard that provides insights into sales, revenue, and customer trends.

## Dataset
Brazillian supermarket, Olist E-Commerce dataset: [Olist eCommerce dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) 
The dataset contains: 
- 112K+ orders
- 99K+ customers
- 32K+ products
- Multiple geographies (city/state level) 

## Business Overview 
To deliver a scalable, cloud-based data pipeline that enables interactive business reporting on revenue trends, product category performance, and regional sales distribution. 

## Architecture 
- **AWS S3**: Raw → Silver → Gold layer storage
- **AWS Glue**: ETL and data cleaning scripts (PySpark)
- **AWS Athena**: Data modelling via SQL (fact & dimension tables)
- **Amazon QuickSight**: Interactive dashboard with direct Athena connection

## Tech Stack

| Tool/Service         | Purpose                          |
|----------------------|----------------------------------|
| **AWS S3**           | Data lake for raw/silver/gold    |
| **AWS Glue**         | Data cleaning & transformation   |
| **AWS Athena**       | Query engine for gold layer      |
| **QuickSight**       | BI dashboard                     |
| **PySpark**          | Data wrangling in Glue scripts   |
| **SQL**              | Data modelling in Athena         |


## Workflow Steps
Data Pipeline Flow

```plaintext
Kaggle CSVs
   ↓
AWS S3 (Raw Layer)
   ↓
AWS Glue (ETL)
   ↓
S3 (Silver Layer) → Athena
   ↓
Athena SQL Modelling → Fact & Dim tables
   ↓
S3 (Gold Layer) → Athena (Partitioned)
   ↓
Amazon QuickSight (Direct Query) → Dashboard
```


## Dashboard Screenshots

![Dashboard Images](image/AWS_QuickSight_Olist_Dashboard.JPG)


👉 See full interactive report screenshots in `/image` folder.

## Dashboard Features

- 📈 Total revenue and order trends over time
- 🗺️ Top-performing cities and states by revenue
- 📦 Top product categories by revenue
- 📦 Key Metrics:
  - **Total Revenue**: `$13.6M`
  - **Total Freight Value**: `$2.3M`
  - **Total Orders**: `98,666`

## Data Cleaning Highlights

- Removed nulls and empty strings from key fields
- Normalised date formats and product categories
- Handled inconsistent city/state naming
- Casted revenue fields to numeric types
- Generated date dimension and load_date partitioning

## Key Learnings

- Developed modular Glue jobs with idempotent partition writes
- Built SQL data models in Athena with star schema
- Created a fully cloud-based BI dashboard for real-world sales data 


---

## 👩‍💻 Author

**Hyesoo Park**  
Data Analyst | Power BI, SQL, Python for Data  
[Portfolio](https://hyesoopark.co.uk) • [LinkedIn](https://linkedin.com/in/hyesoopark) • [GitHub](https://github.com/phs928/portfolio)
