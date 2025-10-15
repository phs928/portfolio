import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql import functions as F
from pyspark.sql import Window 

PARAM_KEYS = ['JOB_NAME', 'silver_bucket', 'gold_bucket', 'load_date'] 
args = getResolvedOptions(sys.argv, PARAM_KEYS)

# Buckets 

_silver = args['silver_bucket'].rstrip('/')
_gold = args['gold_bucket'].rstrip('/')


if not _silver.startswith("s3://"): _silver = f"s3://{_silver}"
if not _gold.startswith("s3://"):   _gold   = f"s3://{_gold}"

SILVER_BUCKET = _silver 
GOLD_BUCKET = _gold 
LOAD_DATE = args['load_date'].strip() 

print(f"[DEBUG] SILVER_BUCKET={SILVER_BUCKET}")
print(f"[DEBUG] GOLD_BUCKET={GOLD_BUCKET}")
print(f"[DEBUG] LOAD_DATE={LOAD_DATE}") 

# Spark / Glue 

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

spark.conf.set("spark.sql.sources.partitionOverwriteMode", "dynamic")
spark.sql("set spark.sql.legacy.timeParserPolicy=LEGACY")

# Functions 

    # scheme protection 
def path_join(*parts):
    return "/".join([p.strip("/") for p in parts if p])

    # read silver partition only 
def read_silver(table): 
    path = path_join(SILVER_BUCKET, table, f"load_date={LOAD_DATE}")
    return spark.read.parquet(path) 

    # return existing gold df 
def try_read_gold(table):
    path = path_join(GOLD_BUCKET, table)
    try:
        return spark.read.parquet(path)
    except Exception:
        return None

    # write gold as snappy parquet 
def write_gold(df, table, partition_cols): 
    (df.write
    .mode("overwrite")
    .format("parquet")
    .partitionBy(*partition_cols)
    .option("compression", "snappy")
    .save(path_join(GOLD_BUCKET, table))
    ) 
    
    # convert timestamp to YYYYMMDD 
def to_date_key(col): 
    c = F.col(col) if isinstance(col, str) else col 
    return F.when(
    c.isNotNull(),
    F.date_format(c.cast("timestamp"), "yyyyMMdd").cast("string")
).otherwise(F.lit(None).cast("string")) 
    
    # cast timestamp then convert to "yyyy-MM"  
def ym_from_ts(col): 
    c = F.col(col) if isinstance(col, str) else col
    return F.date_format(c.cast("timestamp"), "yyyy-MM")
    
    # produce 64-bit hash then convert to positive long  
def to_sk(*cols): 
    return F.abs(F.xxhash64(*[F.col(c) if isinstance(c,str) else c for c in cols])).cast("string")
    
    
# Load silver partitions 

orders = read_silver("orders") 
order_items = read_silver("order_items")
customers = read_silver("customers")
products = read_silver("products")
sellers = read_silver("sellers")

# Build dimension tables 

    # dim_customer 
    
dim_customer_batch = (customers
    .select(
        to_sk("customer_id").alias("customer_sk"),
        "customer_id",
        F.col("customer_unique_id"), 
        F.col("zip_prefix").alias("zip_prefix"), 
        F.col("zip_prefix_int").alias("zip_prefix_int"), 
        F.col("city").alias("city"),
        F.col("state").alias("state"),
        F.col("is_zip_valid"),
        F.col("is_state_valid"),
        F.lit(LOAD_DATE).alias("load_date")
        )
        .dropDuplicates(["customer_id"])
        ) 

existing = try_read_gold("dim_customer")
if existing is not None: 
    dim_customer = existing.unionByName(dim_customer_batch, allowMissingColumns=True) 
    w = Window.partitionBy("customer_id").orderBy(F.col("load_date").desc())
    dim_customer = (dim_customer.withColumn("_rn", F.row_number().over(w)) 
    .filter(F.col("_rn") == 1) 
    .drop("_rn")
    ) 
else:
    dim_customer = dim_customer_batch 
        
write_gold(dim_customer, "dim_customer", ["load_date"])

    # dim_product 
    
dim_product_batch = (products
    .select(
        to_sk("product_id").alias("product_sk"),
        "product_id",
        F.col("product_category_name"),
        F.col("product_category_name_en"),
        F.col("product_name_length").cast("int"),
        F.col("product_description_length").cast("int"),
        F.col("product_photos_qty").cast("int"),
        F.col("product_weight_g").cast("double"),
        F.col("product_length_cm").cast("double"),
        F.col("product_height_cm").cast("double"),
        F.col("product_width_cm").cast("double"),
        F.lit(LOAD_DATE).alias("load_date")
    )
    .dropDuplicates(["product_id"])
)

existing = try_read_gold("dim_product") 
if existing is not None:
    w = Window.partitionBy("product_id").orderBy(F.col("load_date").desc())
    dim_product = (
        existing
        .unionByName(dim_product_batch, allowMissingColumns=True)
        .withColumn("_rn", F.row_number().over(w))
        .filter(F.col("_rn") == 1)
        .drop("_rn")
    )
else:
    dim_product = dim_product_batch
    
write_gold(dim_product, "dim_product", ["load_date"])

    # dim_seller 
    
dim_seller_batch = (sellers
    .select(
        to_sk("seller_id").alias("seller_sk"),
        "seller_id",
        F.col("zip_prefix").alias("zip_prefix"),
        F.col("zip_prefix_int").alias("zip_prefix_int"),
        F.col("city").alias("city"),
        F.col("state").alias("state"),
        F.col("is_zip_valid"),
        F.col("is_state_valid"),
        F.lit(LOAD_DATE).alias("load_date")
    )
    .dropDuplicates(["seller_id"])
)

existing = try_read_gold("dim_seller") 
if existing is not None:
    w = Window.partitionBy("seller_id").orderBy(F.col("load_date").desc())
    dim_seller = (
        existing
        .unionByName(dim_seller_batch, allowMissingColumns=True)
        .withColumn("_rn", F.row_number().over(w))
        .filter(F.col("_rn") == 1)
        .drop("_rn")
    )
else:
    dim_seller = dim_seller_batch
    
write_gold(dim_seller, "dim_seller", ["load_date"])


    # dim_date 
    
date_start = F.to_date(F.lit("2016-01-01"))
date_end = F.to_date(F.lit("2018-12-31"))

dim_date_batch = (spark.range(1)
    .select(F.sequence(date_start, date_end).alias("d"))
    .select(F.explode("d").alias("date"))
    .select(
        to_date_key("date").alias("date_key"),
        F.col("date"),
        F.dayofmonth("date").alias("day"),
        F.month("date").alias("month"),
        F.date_format("date", "MMM").alias("month_name"),
        F.quarter("date").alias("quarter"),
        F.year("date").alias("year"),
        F.weekofyear("date").alias("week_of_year"),
        (F.dayofweek("date").isin(1,7)).alias("is_weekend").cast("boolean"),
        F.date_format("date","E").alias("weekday_name"),
        F.lit(LOAD_DATE).alias("load_date")
    )
)

existing = try_read_gold("dim_date")
if existing is not None: 
    dim_date = existing.unionByName(dim_date_batch, allowMissingColumns=True) \
                       .dropDuplicates(["date_key"])
else:
    dim_date = dim_date_batch

write_gold(dim_date, "dim_date", ["load_date"])


# Build fact table 

    # fact_order_item 
    
    # 1) Prepare for join 
    
oi = (order_items 
    .select(
        "order_id",
        "order_item_id",
        "product_id",
        "seller_id",
        "price",
        "freight_value",
        "extended_price",
        F.col("shipping_limit_ts").alias("ship_limit_ts")
        ))
        
o = (orders 
    .select(
        "order_id",
        "customer_id",
        "order_purchase_ts", 
        "delivered_customer_ts"
        ))
        
fact_base = (oi 
    .join(o, "order_id", "left") 
    .join(products.select("product_id"), "product_id", "left")
    .join(sellers.select("seller_id"), "seller_id", "left")
        )
        
    # 2) Produce SK & date_key & partition columns 
    
fact_enriched = (fact_base
    .withColumn("customer_sk", to_sk("customer_id"))
    .withColumn("product_sk", to_sk("product_id")) 
    .withColumn("seller_sk", to_sk("seller_id"))
    .withColumn("order_date_key", to_date_key("order_purchase_ts"))
    .withColumn("delivered_date_key", to_date_key("delivered_customer_ts"))
    .withColumn("ship_limit_date_key", to_date_key("ship_limit_ts"))
    .withColumn("order_ym", ym_from_ts("order_purchase_ts"))
    .withColumn("load_date", F.lit(LOAD_DATE))
    .select(
        "order_id", "order_item_id",
        "customer_sk", "product_sk", "seller_sk",
        "order_date_key", "delivered_date_key", "ship_limit_date_key", 
        F.col("price").cast("double"), 
        F.col("freight_value").cast("double"), 
        "order_ym", "load_date"
        )
)

    # 3) Deduplicate within batch just in case 
    
fact_batch = fact_enriched.dropDuplicates(["order_id", "order_item_id"])

    # 4) anti-join existing partition in case guarding against re-run on the same Load date 
    
existing_fact_path = path_join(GOLD_BUCKET, "fact_order_item", f"load_date={LOAD_DATE}")
try: 
    existing_fact = spark.read.parquet(existing_fact_path)
    fact_batch = fact_batch.alias("n").join(
        existing_fact.select("order_id", "order_item_id").alias("e"),
        on=["order_id", "order_item_id"], how="left_anti")
except Exception: 
    pass 

    # 5) Write 
    
write_gold(fact_batch, "fact_order_item", ["load_date", "order_ym"])

