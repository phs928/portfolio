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
