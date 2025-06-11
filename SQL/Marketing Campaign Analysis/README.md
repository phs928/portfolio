# 📊 Marketing Campaign Analysis 

This project analyses customer behaviour and marketing effectiveness using SQL and Power BI. 
It is divided into 3 parts: 

1. Customer Segmentation Analysis 
2. Product Type Analysis 
3. Purchase Channel Analysis
4. RFM Analysis 

## 📁 Dataset

- Source: [Kaggle - Marketing Campaign Dataset](https://www.kaggle.com/datasets/rodsaldanha/arketing-campaign)
- Data: Customer demographics, campaign responses, product spending, channel interactions (2,216 records after cleaning) 

## 🧰 Tools Used 

- Microsoft SQL Server for data cleaning and analysis
- Power BI for dashboard creation and visual insights

  

## 📈 🧬 1. Customer Segmentation Analysis 

This part segments customers based on their demographic information to understand which segments are the most responsive to campaigns and valuable 

### 🎯 Objectives: 
- Profile customers by demographic traits 
- Identify high-value customer segments

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
   - Built proxy metrics for **Monetary** and **Recency**

### 🔍 Key Insights

- "Married No Kids" segment spent the most
- "Young Professionals" segment has the highest response rate and average spend value 

### 🧪 Sample SQL:



## 🛒 2. Product Type Analysis 

This part analyses customers' preferred product types (i.e., Wine, Fruits, Meat, Sweet, Fish, Gold) to identify product preferences 

### 🎯 Objectives:
- Evaluate which product type customers spend the most 
- Find preferred products

### 🔍 Key Insights
- Wines accounted for 50% of all spend  

### 🧪 Sample SQL:


## 🛒 3. Purchase Channel Analysis 

This part analyses customers' purchase channels (i.e., store, catalogue, online) to identify preferences and habits 

### 🎯 Objectives:
- Evaluate average usage of each channel
- Find preferred purchase channels for different customer groups

### 🔍 Key Insights
- Most transactions happened in store (46%), followed by web (32%) 

### 🧪 Sample SQL:


## 🛒 4. RFM Analysis 

This part analyses customers' recency (how recent they made purchases), frequency (how often they made purchases) and monetary (how much they spent) scores and evaluates which customers are valuable and which customers require revisiting marketing strategy 

### 🎯 Objectives:
- Evaluate RFM score for each customer 
- Find the most valuable customers and customers at risk 

### 🔍 Key Insights
- 

### 🧪 Sample SQL:



## 📊 Power BI Dashboard Overview

### Page 1 – Executive Overview 


### Page 2 – Customer Segmentation: Response rate by income & age


### Page 3 - Product Type Analysis: Customers' preferred Product Type 


### Page 4 – Channel Analysis: Purchase behaviour by channel and visits


### Page 5 - RFM Analysis 
