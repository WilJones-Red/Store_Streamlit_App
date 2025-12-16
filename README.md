# C-Store Data Dashboard

**Student**: Wil Jones  
**Course**: Big Data  
**Semester**: Fall 2025

**GitHub Repository**: (My Repo)[https://github.com/WilJones-Red/Store_Streamlit_App]
**Live Application**: (Deployed App)[Your Cloud Run URL Here]

---

## Running the Application

```bash
git clone https://github.com/WilJones-Red/Store_Streamlit_App.git
cd Store_Streamlit_App
docker compose up
```

Open your browser to `http://localhost:8080`

---

## Vocabulary Questions

### 1. Explain the added value of using Databricks in your Data Science process

Databricks is a unified analytics platform built on Apache Spark. It provides value by removing infrastructure headaches so data teams can focus on actual analysis instead of managing clusters.

The platform handles massive datasets through distributed computing. Where a single machine would fail on terabyte-scale data, Databricks spreads the work across multiple nodes. This matters when you need to process millions of transactions or train models on production-sized datasets.

Databricks combines the entire workflow in one place. Data engineers build pipelines, data scientists experiment with models, and analysts query results all in the same environment. This eliminates the friction of moving between tools and platforms.

MLflow integration streamlines the machine learning lifecycle. You track experiments, compare models, and deploy to production without cobbling together separate tools. Delta Lake adds reliability to data lakes by providing ACID transactions and versioning, which means your data pipelines won't silently corrupt data.

The auto-scaling feature adjusts compute resources based on workload. You pay for what you use instead of maintaining idle clusters. For teams working with real production data, this combination of scale, collaboration, and managed infrastructure is where Databricks adds value.

---

### 2. Compare and contrast PySpark to Pandas or the Tidyverse

**Scale and execution**

PySpark handles datasets that don't fit in memory by distributing work across a cluster. Pandas and Tidyverse run on a single machine and are limited by available RAM. For most data science work under 10GB, Pandas or Tidyverse is simpler and faster. Beyond that, you need distributed computing.

PySpark uses lazy evaluation. It builds an execution plan before running anything, which lets the optimizer restructure operations for better performance. Pandas executes immediately. Tidyverse can be lazy when connected to databases through dbplyr.

**When to use each**

Use PySpark when your data exceeds 100GB, when building production data pipelines, or when processing streaming data. The overhead makes it inefficient for quick analysis on smaller datasets.

Use Pandas when data fits in memory, during prototyping, or when you need Python's ecosystem of visualization and machine learning libraries. It's faster to write and faster to run on appropriately sized data.

Use Tidyverse for statistical analysis in R, publication-quality visualizations with ggplot2, or when working in an R-based data team. The dplyr and tidyr packages handle data wrangling cleanly.

**Code example**

All three accomplish the same aggregation task with different syntax.

```python
# PySpark
df.groupBy("category").agg({"sales": "sum"}).orderBy("sum(sales)", ascending=False)

# Pandas
df.groupby("category").agg({"sales": "sum"}).sort_values("sales", ascending=False)

# Tidyverse (R)
df %>% group_by(category) %>% summarise(total = sum(sales)) %>% arrange(desc(total))
```

---

### 3. Explain Docker to somebody intelligent but not a tech person

Docker solves the "it works on my computer" problem.

Software needs specific versions of languages, libraries, and system configurations to run. What works on my laptop might fail on yours because we have different setups. Manually replicating an environment is tedious and error-prone.

Docker packages everything an application needs into a container. The container includes the code, the right version of Python, all required libraries, and configuration settings. This container runs the same way on any computer that has Docker installed.

Think of it like a shipping container. Before standardized containers, shipping was chaotic because every cargo had different requirements. Standardized containers solved this by providing a consistent format. Docker does the same for software.

**Key concepts**

An image is the blueprint. It contains instructions for what goes in the container. A container is a running instance of that image. The Dockerfile lists the steps to build the image. Docker Compose runs multiple containers together if your application needs them.

**Benefits for this project**

Someone can clone this repository and run `docker compose up`. They don't need to install Python, Streamlit, Polars, or any dependencies. Docker handles it. The application runs identically on their machine, my machine, and Google Cloud servers. This consistency eliminates deployment problems and makes collaboration straightforward.

---

### 4. Compare GCP to AWS for cost, features, and ease of use

**Cost**

GCP typically costs 20-25% less than AWS. The main difference is how discounts work. GCP automatically applies sustained-use discounts when you run services consistently. AWS requires you to purchase Reserved Instances upfront for similar savings.

Both charge per-second for compute. Storage pricing is comparable at around $0.02 per GB. Data egress costs are high on both platforms but slightly lower on GCP.

For this Streamlit dashboard on Cloud Run, GCP costs $0-5 per month with low traffic because it scales to zero when idle. The equivalent on AWS Fargate would cost $10-20 minimum because it keeps resources allocated.

**Features**

AWS has the broadest service catalog with over 200 services. It launched in 2006 and has had more time to build out offerings. If you need specialized tools or the widest selection, AWS has more options.

GCP excels in data analytics and machine learning. BigQuery outperforms AWS Athena for data warehousing. Vertex AI provides a more integrated machine learning platform than SageMaker. GKE (Google Kubernetes Engine) is considered the best managed Kubernetes service, which makes sense since Google created Kubernetes.

AWS leads in database variety and global infrastructure. GCP has fewer regions but covers major markets.

**Ease of use**

GCP has a cleaner interface and more intuitive service names. Cloud Storage and Compute Engine are self-explanatory. AWS uses acronyms like S3 and EC2 that you have to learn.

Documentation favors GCP for clarity and examples, though AWS documentation is more comprehensive due to the larger service catalog. The learning curve is steeper on AWS because there are more services and configuration options to understand.

For deploying containerized applications, GCP Cloud Run requires one command. AWS alternatives like Fargate or App Runner need more setup steps.

---

### Assignment Requirements Addressed

This application fulfills all technical requirements by leveraging **Streamlit** as the interactive web framework, **Docker** for containerization and reproducibility, **Polars** for high-performance data processing, **Plotly Express** for creating interactive visualizations, and **Cloud Run (GCP)** for scalable cloud deployment. Each technology was selected to meet the specific demands of the assignment while ensuring professional-grade performance and user experience.

---

## Dashboard Pages

Each page answers a specific business question from the assignment:

### 1. Top Products Analysis
*Question: "Excluding fuels, what are the top five products with the highest weekly sales?"*
- Displays top 5 non-fuel products by weekly sales with interactive charts
- Includes KPIs, temporal comparisons, and dynamic filters
- Leverages caching for performance

### 2. Packaged Beverages
*Question: "In the packaged beverage category, which brands should I drop if I must drop some from the store?"*
- Analyzes brand performance with sales trends and growth metrics
- Provides data-driven recommendations for underperforming brands
- Includes summary tables and temporal visualizations

### 3. Customer Comparison
*Question: "How do cash customers and credit customers compare?"*
- Compares purchase amounts, item counts, and product preferences
- Shows which products are purchased most by each customer type
- Visualizes differences in shopping behavior

### 4. Demographics
*Question: "Provide detailed customer demographics comparison using Census API"*
- Integrates with U.S. Census API for demographic data
- Compares 10+ demographic variables across store locations
- Displays population, income, age, education, housing, and employment data

---

## Technical Features

All pages include the assignment-required elements: **Caching** through `@st.cache_data` for optimal performance, **KPIs** using `st.metric()` to display key performance indicators with comparisons, **Summary Tables** presenting clean and formatted data, **Interactive Charts** built with Plotly for temporal comparisons, **Filters** allowing users to select date ranges and exclude specific stores or categories, and **Layouts** utilizing columns, containers, and expanders for intuitive organization.

