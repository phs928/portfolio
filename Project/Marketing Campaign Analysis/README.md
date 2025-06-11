# 📊 Marketing Campaign Analysis 

This project analyses customer behaviour and marketing effectiveness using SQL and Power BI. 
It is divided into 3 parts: 

1. Customer Segmentation Analysis 
2. Product Type Analysis 
3. Purchase Channel Analysis
4. RFM Analysis 

## 📁 Dataset

- **Source**: [Kaggle - Marketing Campaign Dataset](https://www.kaggle.com/datasets/rodsaldanha/arketing-campaign)
- **Data**: Customer demographics, campaign responses, product spending, channel interactions
- **Size**: 2,216 records after cleaning 

## 🧰 Tools Used 

- **Microsoft SQL Server**: Data cleaning and preprocessing 
- **Power BI**: Dashboard development and visual insight generation

  

## 🔎 1. Customer Segmentation Analysis 

This part segments customers based on their demographic features to understand which segments are the most responsive to campaigns and valuable 

### 🎯 Objectives: 
- Profile customers by demographic attributes 
- Identify high-value and high-responsive customer segments

### 🧩 Key Steps 
1. ***Dataset Loading*** 
2. ***Data cleaning & transformation***
   - Handled missing values in `income` 
   - Reclassified and created new variables: `income_band`, `age_band`, `children_group`
3. ***Demographic segmentation*** 
   - Manually defined segments using age, income, marital status, education, and child presence
   - Assigned labels such as:
     *"Young Professionals"*, 
     *"Middle-aged Married Parents"*, 
     *"Budget-Conscious Families"*,
     *"Married No Kids"*,
     *"Solo Households"*,
     *"Older Married Parents"*,
     *"Other group"* 
4. ***KPI Analysis***
   - Calculated campaign `response_rate` per segment
   - Measured average `spend per product category` across segments 

### 🔍 Key Insights

- The "Married No Kids" segment showed the **highest total spend** 
- "Young Professionals" segment had the **highest average spend** and **response rate** 


## 🛒 2. Product Type Analysis 

This section analyses which products customers prefer and spend most on (i.e., Wine, Fruits, Meat, Sweet, Fish, Gold) 

### 🎯 Objectives:
- Identify most popular product types by spend  
- Understand purchasing patterns by segment 

### 🔍 Key Insights
- **Wines** accounted for **over 50%** of total customer spending  
- High-value customers showed consistent interest in Meat and Gold as well


## 🛍️ 3. Purchase Channel Analysis 

This part explores how customers interact with different purchase channels (store, catalogue, web)

### 🎯 Objectives:
- Measure average and total transactions by channel  
- Identify channel preferences by segment 

### 🔍 Key Insights
- **Store** was the most used channel (46% of transactions), followed by **web** (32%)  
- High-value customers tended to use multiple channels


## 🧮 4. RFM Analysis 

This section evaluates customer value using **Recency**, **Frequency**, and **Monetary** scoring

### 🎯 Objectives:
- Score customers based on purchase recency, frequency, and spending  
- Classify customers into value-based segments (e.g. VIP, Loyal, At Risk)

### 🧩 Key Steps
- Created **Recency Score** (based on days since last purchase)  
- Created **Frequency Score** (based on number of accepted campaigns)  
- Created **Monetary Score** (based on total spend)  
- Assigned two RFM labels:
  - **Simple**: Based on Recency & Frequency
  - **Extended**: Based on Recency, Frequency & Monetary

### 🔍 Key Insights
- Over **38%** of customers were classified as **At Risk**  
- Only **0.1%** of customers qualified as **VIP**, suggesting highly selective criteria  
- Extended RFM helped distinguish **High Spenders** with low frequency


## 📊 Power BI Dashboard Overview 

| Page | Description |
|------|-------------|
| **Page 1 – Executive Overview** | KPIs, top segments/products/channels summary |
| **Page 2 – Customer Segmentation** | Response rate, spend, count by segment |
| **Page 3 – Product Type Analysis** | Spend and penetration by product type |
| **Page 4 – Channel Analysis** | Channel usage, average transactions |
| **Page 5 – RFM Analysis** | R/F/M scoring and customer labelling |

---

## 📷 Dashboard Screenshots

![marketingcampaign_overview](marketingcampaign_overview.JPG)
---

## 📦 Sample SQL Queries


---


