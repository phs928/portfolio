# 📊 **Sales Performance Report**

An interactive Sales Report built with Python + Power BI for a profit/start-up organisation.

## 🔍 Objectives
- Analyse sales trends by year, month, quarter and days
- Analyse product/Category performance
- Analyse KPIs by customer segmentation
- Analyse KPIs by region & state

## 🛠️ Tools
- Python (pandas) 
- Power BI
- Excel

## 📁 Data
- Source: Superstore sales data (Excel) from Kaggle [View](https://www.kaggle.com/datasets/vivek468/superstore-dataset-final)
- Tool: Power BI Desktop

## 📈 KPIs Tracked
1. Total Sales 
2. Total Profit
3. Profit Margin
4. Total Order Count
5. Total Customers 
6. Average Order Value
7. Average Order per Customer
8. Average Profit per Product
9. Repeat Customer %
10. Top Customer by Sales 
11. Top Sub-category by Sales
12. Lowest Profit Margin Sub-category
13. Highest/Lowest Profit Margin Product
14. Highest Sales Region/State
15. Lowest Profit Margin State
16. Top State with Highest AOV

## 📊 Power BI Dashboard 
Interactive Report covering: 
1. **Overview**  
   - Key KPIs: Total Sales, Profit, Margin, Orders, AOV  
   - Monthly sales/profit trends
2. **Category Performance**  
   - Sales & profit by category/sub-category  
   - Top & bottom performing sub-categories
3. **Product Performance**  
   - Top products by sales/profit  
   - Avg profit per product, best/worst margin products
4. **Customer Segments**  
   - Sales, AOV, profit by segment  
   - Repeat rate, top customers
5. **Region & State**  
   - Sales/profit/margin by region and state  
   - Map visualisation of key KPIs
6. **Summary Insight**  
   - Key insights summary  
   - Treemap: Segment × Category vs Sales

![Report Screenshot](images/SalesReport_overview.JPG) 

## 🧠 Visual & Insight Highlights

- Effective use of KPI cards, line/bar/stacked bar/treemap visuals
- Business insights include:
  - Technology category drives revenue
  - "Consumer" segment contributes the most
  - Significant margin differences by region

## 🔄 Automation Note

Currently based on a **static Excel file**.  
Automation features are not implemented but could be implemented using:
- Google Drive / Power BI Service integration
- Cloud database setup (e.g., PostgreSQL, MySQL, Snowflake)

## 🚀 Future Enhancements

- Connect to cloud sources (Google Drive / SharePoint) for auto-refresh
- Deploy to Power BI Service for scheduled updates and sharing
- Add anomaly detection or KPI-based alerts


## 📂 File Structure 
```
Sales Performance Report/
├── data/ # Raw input data
│ ├── Superstore_sales.csv
├── notebooks/ # Exploratory data analysis & prototyping
│ └── Sales Performance Report.ipynb
├── reports/ # Output reports
│ ├── Sales Performance Report.pdf
├── README.md # Project overview and usage
```
---

## 👩‍💻 Author

**Hyesoo Park**  
Data Analyst | Power BI, SQL, Python for Data  
[Portfolio](https://hyesoopark.co.uk) • [LinkedIn](https://linkedin.com/in/hyesoopark) • [GitHub](https://github.com/phs928)
