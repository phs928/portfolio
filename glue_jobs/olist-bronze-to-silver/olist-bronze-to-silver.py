import sys
from datetime import datetime
from awsglue.utils import getResolvedOptions
from awsglue.context import GlueContext
from pyspark.context import SparkContext
from awsglue.job import Job
from pyspark.sql import functions as F, types as T
from pyspark.sql.window import Window

# 0) Read run-time arguments
PARAM_KEYS = ['JOB_NAME', 'raw_db', 'silver_bucket', 'load_date']
args = getResolvedOptions(sys.argv, PARAM_KEYS)

# arguments
raw_db = args['raw_db']
silver_bucket = args['silver_bucket'].rstrip('/')
if not silver_bucket.startswith("s3://"):
    silver_bucket = f"s3://{silver_bucket}"
load_date = args['load_date']

# 1) Session / job init
sc = SparkContext()
glue = GlueContext(sc)
spark = glue.spark_session
job = Job(glue)
job.init(args['JOB_NAME'], args)

# Allow dynamic partition overwrite
spark.conf.set("spark.sql.sources.partitionOverwriteMode", "dynamic")
spark.sql("set spark.sql.legacy.timeParserPolicy=LEGACY")

# 2-1) Read from Glue catalog (DynamicFrame -> DataFrame)

def read_table(table: str):
    # Exception route for multiline CSV in reviews
    if table == "order_reviews":
        df = (
            spark.read.format("csv")
            .option("header", True)
            .option("multiLine", True)
            .option("quote", '"')
            .option("escape", '"')
            .option("mode", "PERMISSIVE")
            .option("inferSchema", False)
            .load("s3://hyesoo-de-ecommerce/olist/raw/order_reviews/")
        )
        cols = [c.lstrip("\ufeff") for c in df.columns]
        return df.toDF(*cols)

    dyf = glue.create_dynamic_frame.from_catalog(
        database=raw_db,
        table_name=table
    )
    return dyf.toDF()
    
    
# 2-2) convert values to null 

def null_if_empty(col):
    c = F.col(col) if isinstance(col, str) else col
    return F.when(F.length(F.trim(c)) == 0, F.lit(None)).otherwise(c)

# F.trim: remove empty string front and back of column 
# F.length(…) == 0: check if it is empty  
# F.when(…, F.lit(None)).otherwise(col) : NULL if empty, otherwise don't change 
    
# 2-3) cast timestamp 

def to_ts(col):
    c = F.col(col) if isinstance(col, str) else col
    return F.to_timestamp(null_if_empty(c), "yyyy-MM-dd HH:mm:ss")
    

# 2-4) Write and save to silver bucket as S3 parquet, partitioned by load_date  

def write_silver(df, table):
    (
        df.withColumn("load_date", F.lit(load_date))
          .write
          .mode("overwrite")
          .format("parquet")
          .partitionBy("load_date")
          .option("compression", "snappy")
          .save(f"{silver_bucket}/{table}/")
    )
    
# 2-5) strip only outer/leading quotes (single or double) 

def strip_outer_quotes(col):
    c = F.col(col) if isinstance(col, str) else col
    x = F.trim(c)
    x = F.regexp_replace(x, r'^(?:"|\')+', '')
    x = F.regexp_replace(x, r'(?:"|\')+$', '')
    return x 

# 3-1) cleaning: orders 

orders_raw = read_table("orders")

# Clean + normalize
orders = (
    orders_raw
    .select(
        strip_outer_quotes("order_id").alias("order_id"),            # ID safety
        strip_outer_quotes("customer_id").alias("customer_id"),
        F.lower(F.trim(F.col("order_status"))).alias("order_status"),# normalize status
        to_ts("order_purchase_timestamp").alias("order_purchase_ts"),
        to_ts("order_approved_at").alias("order_approved_ts"),
        to_ts("order_delivered_carrier_date").alias("delivered_carrier_ts"),
        to_ts("order_delivered_customer_date").alias("delivered_customer_ts"),
        to_ts("order_estimated_delivery_date").alias("estimated_delivery_ts"),
    )
    
    # Derived dates (day grain)
    .withColumn("order_date", F.to_date("order_purchase_ts"))
    .withColumn("delivered_date", F.to_date("delivered_customer_ts"))
)

# Deterministic dedup (latest purchase_ts wins; NULLs last)

w_orders = (
    Window.partitionBy("order_id")
          .orderBy(F.col("order_purchase_ts").desc_nulls_last())
)

orders = (
    orders
    .dropDuplicates()                                   # exact dups first
    .withColumn("rn", F.row_number().over(w_orders))
    .filter(F.col("rn") == 1).drop("rn")
)

# Save
write_silver(orders, "orders")


# 3-2) cleaning: order_items 

order_items_raw = read_table("order_items")

order_items = (
    order_items_raw
    .select(
        strip_outer_quotes("order_id").alias("order_id"),
        F.col("order_item_id").cast("int").alias("order_item_id"),
        strip_outer_quotes("product_id").alias("product_id"),
        strip_outer_quotes("seller_id").alias("seller_id"),
        F.col("shipping_limit_date").alias("shipping_limit_date"),
        F.col("price").cast("double").alias("price"),
        F.col("freight_value").cast("double").alias("freight_value"),
    )
    .withColumn("shipping_limit_ts", to_ts("shipping_limit_date"))
    .drop("shipping_limit_date")
    
    # Extended price (Olist has qty=1 per row, keep for schema parity)
    .withColumn("extended_price", F.col("price"))
)

# Dedup key: (order_id, order_item_id)
w_items = (
    Window.partitionBy("order_id", "order_item_id")
          .orderBy(
              F.col("price").desc_nulls_last(),
              F.col("freight_value").desc_nulls_last()
          )
)

order_items = (
    order_items
    .dropDuplicates()
    .withColumn("rn", F.row_number().over(w_items))
    .filter(F.col("rn") == 1).drop("rn")
)

write_silver(order_items, "order_items")

# 3-3) cleaning: order_payments 

order_payments_raw = read_table("order_payments")

order_payments = (
    order_payments_raw
    .select(
        strip_outer_quotes("order_id").alias("order_id"),
        F.col("payment_sequential").cast("int").alias("payment_sequential"),
        F.col("payment_type").alias("payment_type_raw"),
        F.col("payment_installments").cast("int").alias("payment_installments"),
        F.col("payment_value").cast("double").alias("payment_value"),
    )
    
    # Normalize type
    .withColumn("payment_type", F.lower(F.trim("payment_type_raw")))
    .withColumn(
        "payment_type",
        F.when(F.col("payment_type").isin("credit_card","boleto","voucher","debit_card","not_defined"),
               F.col("payment_type"))
         .when(F.col("payment_type").isNull() | (F.col("payment_type") == ""), F.lit("not_defined"))
         .otherwise(F.lit("other"))
    )
    .drop("payment_type_raw")
)

# Keep latest/best per (order_id, payment_sequential)

w_pay = (
    Window.partitionBy("order_id","payment_sequential")
          .orderBy(
              F.col("payment_value").desc_nulls_last(),
              F.col("payment_installments").desc_nulls_last(),
              F.length(F.col("payment_type")).desc_nulls_last()
          )
)

order_payments = (
    order_payments
    .dropDuplicates()
    .withColumn("rn", F.row_number().over(w_pay))
    .filter(F.col("rn")==1).drop("rn")
    
    # Flags (bool -> int)
    .withColumn("is_card",    F.col("payment_type").isin("credit_card","debit_card").cast("int"))
    .withColumn("is_boleto", (F.col("payment_type")=="boleto").cast("int"))
    .withColumn("is_voucher",(F.col("payment_type")=="voucher").cast("int"))
)

write_silver(order_payments, "order_payments")

# 3-4) cleaning: order_reviews 

reviews_raw = read_table("order_reviews")  # exception route handles multiline

reviews = (
    reviews_raw
    .select(
        strip_outer_quotes("review_id").alias("review_id"),
        strip_outer_quotes("order_id").alias("order_id"),
        F.col("review_score").cast("int").alias("review_score"),
        F.col("review_comment_title").alias("review_comment_title"),
        F.col("review_comment_message").alias("review_comment_message"),
        F.col("review_creation_date").alias("review_creation_date"),
        F.col("review_answer_timestamp").alias("review_answer_timestamp"),
    )
    
    # Replace CR/LF with single space to stabilize rows
    .withColumn("review_comment_title",  F.regexp_replace(F.col("review_comment_title"),  r"[\r\n]+", " "))
    .withColumn("review_comment_message",F.regexp_replace(F.col("review_comment_message"), r"[\r\n]+", " "))
    
    # Empty -> NULL
    .withColumn("review_comment_title",  null_if_empty(F.col("review_comment_title")))
    .withColumn("review_comment_message",null_if_empty(F.col("review_comment_message")))
    
    # Timestamps
    .withColumn("review_creation_ts", to_ts("review_creation_date"))
    .withColumn("review_answer_ts",   to_ts("review_answer_timestamp"))
    .drop("review_creation_date","review_answer_timestamp")
    
    # Clamp review_score to [1,5]
    .withColumn("review_score",
        F.when(F.col("review_score").between(1,5), F.col("review_score")).otherwise(F.lit(None).cast("int"))
    )
)

# Dedup: prefer answered & newer & longer comments

w_rev = (
    Window.partitionBy("review_id")
          .orderBy(
              F.col("review_answer_ts").desc_nulls_last(),
              F.col("review_creation_ts").desc_nulls_last(),
              F.length(F.col("review_comment_message")).desc_nulls_last(),
              F.length(F.col("review_comment_title")).desc_nulls_last()
          )
)

reviews = (
    reviews
    .dropDuplicates()
    .withColumn("rn", F.row_number().over(w_rev))
    .filter(F.col("rn")==1).drop("rn")
    
    # Derived
    .withColumn("review_date", F.to_date("review_creation_ts"))
    .withColumn("is_answered", F.col("review_answer_ts").isNotNull().cast("int"))
    .withColumn("has_comment",
        (F.col("review_comment_title").isNotNull() | F.col("review_comment_message").isNotNull()).cast("int"))
    .withColumn("comment_length", F.length(F.coalesce(F.col("review_comment_message"), F.lit(""))))
    .withColumn(
        "answer_delay_days",
        F.when(F.col("review_answer_ts").isNotNull() & F.col("review_creation_ts").isNotNull(),
               F.datediff(F.col("review_answer_ts"), F.col("review_creation_ts")))
         .otherwise(F.lit(None).cast("int"))
    )
    
    .withColumn("answer_delay_days",
        F.when(F.col("answer_delay_days")>=0, F.col("answer_delay_days")).otherwise(F.lit(None).cast("int")))
)

write_silver(reviews, "reviews")


# 3-5) cleaning: customers 

customers_raw = read_table("customers")

customers = (
    customers_raw
    .select(
        F.trim(F.col("customer_id")).alias("customer_id"),
        F.trim(F.col("customer_unique_id")).alias("customer_unique_id"),
        F.col("customer_zip_code_prefix").cast("string").alias("zip_prefix_raw"),
        F.col("customer_city").alias("city_raw"),
        F.col("customer_state").alias("state_raw"),
    )
    .withColumn("zip_prefix_raw", F.trim("zip_prefix_raw"))
    .withColumn("city_raw",       F.trim("city_raw"))
    .withColumn("state_raw",      F.trim("state_raw"))
    
    # ZIP: digits only -> left pad 5 -> NULL if empty
    .withColumn("zip_digits", F.regexp_replace(F.col("zip_prefix_raw"), r"[^0-9]", ""))
    .withColumn("zip_prefix",
        F.when(F.length("zip_digits")>0, F.lpad("zip_digits",5,"0")).otherwise(F.lit(None).cast("string")))
    .withColumn("zip_prefix_int",
        F.when(F.col("zip_prefix").isNotNull(), F.col("zip_digits").cast("int")).otherwise(F.lit(None).cast("int")))
    
    # City / State normalization
    .withColumn("city",  null_if_empty(F.initcap(F.regexp_replace(F.lower("city_raw"), r"\s+", " "))))
    .withColumn("state", null_if_empty(F.upper(F.regexp_replace("state_raw", r"[^A-Za-z]", ""))))
)

# Dedup by customer_id (prefer non-null state, then zip)

w_cust = (
    Window.partitionBy("customer_id")
          .orderBy(
              F.col("state").isNotNull().desc(),
              F.col("zip_prefix").isNotNull().desc()
          )
)

customers = (
    customers
    .dropDuplicates()
    .withColumn("rn", F.row_number().over(w_cust))
    .filter(F.col("rn")==1).drop("rn","zip_prefix_raw","zip_digits","city_raw","state_raw")
    .withColumn("is_zip_valid",   (F.length(F.col("zip_prefix"))==5).cast("int"))
    .withColumn("is_state_valid", (F.length(F.col("state"))==2).cast("int"))
)

write_silver(customers, "customers")

# 3-6) cleaning: product & translation 

products_raw = read_table("products")
trans_raw    = read_table("product_translation")  # may be empty

products = (
    products_raw
    .select(
        strip_outer_quotes("product_id").alias("product_id"),
        
        # slug -> human friendly (underscore -> space)
        F.regexp_replace(F.lower(F.trim(F.col("product_category_name"))), r"_", " ").alias("product_category_name"),
        F.col("product_name_lenght").cast("int").alias("product_name_length"),
        F.col("product_description_lenght").cast("int").alias("product_description_length"),
        F.col("product_photos_qty").cast("int").alias("product_photos_qty"),
        F.col("product_weight_g").cast("double").alias("product_weight_g"),
        F.col("product_length_cm").cast("double").alias("product_length_cm"),
        F.col("product_height_cm").cast("double").alias("product_height_cm"),
        F.col("product_width_cm").cast("double").alias("product_width_cm"),
    )
)

# Translation (LEFT JOIN; safe if empty)

trans = (
    trans_raw
    .select(
        F.lower(F.trim(F.col("product_category_name"))).alias("product_category_name"),
        F.trim(F.col("product_category_name_english")).alias("product_category_name_en")
    )
    .dropDuplicates(["product_category_name"])
)

products = (
    products.alias("p")
    .join(trans.alias("t"), on="product_category_name", how="left")
)

# Dedup by product_id (prefer rows with english name, longer desc, more photos)

w_prod = (
    Window.partitionBy("product_id")
          .orderBy(
              F.col("product_category_name_en").isNotNull().desc(),
              F.col("product_description_length").desc_nulls_last(),
              F.col("product_photos_qty").desc_nulls_last()
          )
)

products = (
    products
    .dropDuplicates()
    .withColumn("rn", F.row_number().over(w_prod))
    .filter(F.col("rn")==1).drop("rn")
)

write_silver(products, "products")

# 3-7) cleaning: sellers 

sellers_raw = read_table("sellers")

sellers = (
    sellers_raw
    .select(
        F.trim(F.col("seller_id")).alias("seller_id"),
        F.col("seller_zip_code_prefix").cast("string").alias("zip_prefix_raw"),
        F.col("seller_city").alias("city_raw"),
        F.col("seller_state").alias("state_raw"),
    )
    .withColumn("zip_prefix_raw", F.trim("zip_prefix_raw"))
    .withColumn("city_raw",       F.trim("city_raw"))
    .withColumn("state_raw",      F.trim("state_raw"))
    
    # ZIP
    .withColumn("zip_digits", F.regexp_replace("zip_prefix_raw", r"[^0-9]", ""))
    .withColumn("zip_prefix",
        F.when(F.length("zip_digits")>0, F.lpad("zip_digits",5,"0")).otherwise(F.lit(None).cast("string")))
    .withColumn("zip_prefix_int",
        F.when(F.col("zip_prefix").isNotNull(), F.col("zip_digits").cast("int")).otherwise(F.lit(None).cast("int")))
   
    # City/State
    .withColumn("city",  null_if_empty(F.initcap(F.regexp_replace(F.lower("city_raw"), r"\s+", " "))))
    .withColumn("state", null_if_empty(F.upper(F.regexp_replace("state_raw", r"[^A-Za-z]", ""))))
)

# Dedup: seller_id

w_sell = (
    Window.partitionBy("seller_id")
          .orderBy(
              F.col("state").isNotNull().desc(),
              F.col("zip_prefix").isNotNull().desc()
          )
)

sellers = (
    sellers
    .dropDuplicates()
    .withColumn("rn", F.row_number().over(w_sell))
    .filter(F.col("rn")==1).drop("rn","zip_prefix_raw","zip_digits","city_raw","state_raw")
    .withColumn("is_zip_valid",   (F.length(F.col("zip_prefix"))==5).cast("int"))
    .withColumn("is_state_valid", (F.length(F.col("state"))==2).cast("int"))
)

write_silver(sellers, "sellers")

# 3-8) cleaning: geolocation 

geo_raw = read_table("geolocation")

geolocation = (
    geo_raw
    .select(
        F.col("geolocation_zip_code_prefix").cast("string").alias("zip_prefix_raw"),
        F.col("geolocation_lat").alias("geolocation_lat"),
        F.col("geolocation_lng").alias("geolocation_lng"),
        F.col("geolocation_city").alias("city_raw"),
        F.col("geolocation_state").alias("state_raw"),
    )
    .withColumn("zip_prefix_raw", F.trim("zip_prefix_raw"))
    .withColumn("city_raw",       F.trim("city_raw"))
    .withColumn("state_raw",      F.trim("state_raw"))
    
    # ZIP: digits only -> left pad 5
    .withColumn("zip_digits", F.regexp_replace("zip_prefix_raw", r"[^0-9]", ""))
    .withColumn("zip_prefix",
        F.when(F.length("zip_digits")>0, F.lpad("zip_digits",5,"0")).otherwise(F.lit(None).cast("string")))
    .withColumn("zip_prefix_int",
        F.when(F.col("zip_prefix").isNotNull(), F.col("zip_digits").cast("int")).otherwise(F.lit(None).cast("int")))
    
    # City/State
    .withColumn("city",  null_if_empty(F.initcap(F.regexp_replace(F.lower("city_raw"), r"\s+", " "))))
    .withColumn("state", null_if_empty(F.upper(F.regexp_replace("state_raw", r"[^A-Za-z]", ""))))
    
    # Lat/Lng sanity
    .withColumn("geolocation_lat",
        F.when( (F.col("geolocation_lat") >= -90) & (F.col("geolocation_lat") <= 90),
                F.col("geolocation_lat")).otherwise(F.lit(None).cast("double")))
    .withColumn("geolocation_lng",
        F.when( (F.col("geolocation_lng") >= -180) & (F.col("geolocation_lng") <= 180),
                F.col("geolocation_lng")).otherwise(F.lit(None).cast("double")))
    .drop("zip_prefix_raw","zip_digits","city_raw","state_raw")
)

# Dedup: (zip_prefix, lat, lng) unique

geolocation = geolocation.dropDuplicates(["zip_prefix","geolocation_lat","geolocation_lng"])

# Quality flags

geolocation = (
    geolocation
    .withColumn("is_zip_valid",   (F.length(F.col("zip_prefix"))==5).cast("int"))
    .withColumn("is_state_valid", (F.length(F.col("state"))==2).cast("int"))
)

write_silver(geolocation, "geolocation")