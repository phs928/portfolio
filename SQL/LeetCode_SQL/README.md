# LeetCode SQL Solutions

## 176. Second Highest Salary

**Problem:** Find the three top high earners in each department 

**Solution:** 

```sql
select 
    Department 
    ,Employee 
    ,Salary 
from ( 
select 
    b.name as Department 
    ,a.name as Employee 
    ,dense_rank() over (partition by a.departmentId order by salary desc) as r 
    ,Salary 
from dbo.Employee a 
inner join dbo.Department b on a.departmentId = b.id ) t 
where r <= 3 
