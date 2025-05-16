# Book Sales Analytics - Architecture Document

## Introduction

This document provides a detailed overview of the architecture for our Book Sales Analytics research project. The architecture is designed to address the challenges of analyzing large volumes of book sales data while maintaining optimal performance for both transactional and analytical workloads.

## Architecture Goals

1. **Separate Transactional and Analytical Processing**: Prevent analytics queries from impacting the performance of the core application
2. **Scale with Data Growth**: Support increasing data volumes without proportional performance degradation
3. **Enable Complex Analytics**: Support complex aggregations, time-series analysis, and multi-dimensional queries
4. **Provide Interactive Dashboards**: Deliver sub-second response times for dashboard interactions
5. **Support Flexible Data Access**: Allow for both predefined analyses and ad-hoc exploration
6. **Maintain Data Consistency**: Ensure analytics data is consistent with the source data
7. **Enable Test Scenarios**: Support generating and analyzing test data sets for benchmarking

## High-Level Architecture

The architecture follows a modern data warehouse approach:

1. **Data Sources Layer**: Original data from transactional systems and files
2. **ETL Layer**: Data extraction, transformation, and loading processes
3. **Storage Layer**: Data lake and warehouse technologies
4. **API Layer**: Analytics-specific API endpoints
5. **Presentation Layer**: Interactive visualizations and dashboards

![Architecture Diagram](../docs/architecture-diagram.png)

## Component Details

### Data Sources

1. **Django PostgreSQL Database**
   - Contains the transactional book and sales data
   - Stores the application's business data
   - Optimized for OLTP (Online Transaction Processing)

2. **CSV Imports**
   - Historical data or bulk imports
   - Third-party data sources
   - Migration from legacy systems

### ETL Process

1. **Django Data Exporter**
   - Custom service that extracts data from the Django ORM
   - Formats data for the data lake
   - Runs on a scheduled basis (default: daily)
   - Supports both full and incremental exports

2. **Test Data Generator**
   - Creates realistic book and sales data for testing
   - Configurable volume and characteristics
   - Useful for performance benchmarking
   - Accessible through both Django management commands and API

### AWS Cloud Components

1. **S3 Data Lake**
   - Raw storage for extracted data
   - Organized in a partitioned structure (by date)
   - Provides a durable and scalable storage layer
   - Formats: CSV, Parquet (optional)

2. **AWS Glue (Optional)**
   - Managed ETL service
   - Transforms raw data into analytics-ready format
   - Schema management and data catalogs
   - Serverless execution of transformation jobs

3. **AWS Redshift**
   - Columnar data warehouse
   - Optimized for analytical queries
   - Scales to petabytes of data
   - Dimensional model with fact and dimension tables

4. **IAM Security**
   - Role-based access control
   - Principle of least privilege
   - Secure cross-service communication
   - Authentication for API access

### Application Layer

1. **Django Backend**
   - Core application logic
   - Django REST Framework (DRF) API
   - Redshift connector for warehouse queries
   - Pandas for data manipulation
   - API authentication and authorization
   - Query caching for performance

2. **React Frontend**
   - Single-page application (SPA)
   - Responsive design with Tailwind CSS
   - Data visualization with Recharts
   - Time range filtering
   - Interactive dashboard components
   - Drill-down capabilities

## Data Flow

1. **Data Generation/Collection**
   - Book and sale records are created in the transactional database
   - Alternatively, test data is generated through the test data generator

2. **Data Extraction**
   - The data exporter service queries the Django database 
   - Data is formatted as CSV (or another appropriate format)
   - Metadata is added (export timestamp, source, etc.)

3. **Data Loading**
   - Extracted data is uploaded to S3
   - AWS Glue (or direct Redshift COPY) loads data into Redshift
   - Data is transformed into the warehouse schema

4. **Data Querying**
   - Django API executes SQL queries against Redshift
   - Results are processed and formatted for the frontend
   - Responses are cached where appropriate

5. **Data Visualization**
   - React frontend renders visualizations based on the API data
   - User interactions trigger new API requests
   - Time range and other filters modify the query parameters

## Key Technical Details

### Data Warehouse Schema

The Redshift schema follows a star schema design:

1. **Dimension Tables**:
   - `analytics.dim_book`: Book metadata
   - Other dimension tables as needed (e.g., time, region)

2. **Fact Tables**:
   - `analytics.fact_sales`: Sales transactions

3. **Aggregated Views**:
   - `analytics.sales_by_day`: Daily aggregations
   - `analytics.sales_by_region`: Regional aggregations
   - `analytics.sales_by_genre`: Genre-based aggregations

### ETL Approach

1. **Extraction Strategy**:
   - Initial full data load
   - Subsequent incremental loads based on last modified timestamp
   - Parallel extraction for large data sets

2. **Transformation Logic**:
   - Data type conversions
   - Denormalization for analytical queries
   - Derived metrics calculation
   - Data quality checks

3. **Loading Method**:
   - S3 stage area
   - Redshift COPY command for efficient loading
   - UPSERT pattern for incremental updates

### API Design

1. **Endpoints**:
   - `/api/analytics/summary/`: Overall metrics
   - `/api/analytics/timeseries/`: Time-based trends
   - `/api/analytics/top-books/`: Ranking analysis
   - `/api/analytics/sales-by-region/`: Geographical analysis
   - `/api/analytics/sales-by-genre/`: Category analysis
   - `/api/analytics/generate-test-data/`: Test data generation

2. **Query Parameters**:
   - `days`: Time range filter (default: 30)
   - `interval`: Aggregation interval (day, week, month)
   - `limit`: Result size limit

3. **Response Format**:
   - JSON structure optimized for frontend consumption
   - Consistent field naming
   - Appropriate data types

### Frontend Architecture

1. **Component Design**:
   - Reusable visualization components
   - Smart containers for data fetching
   - Presentation components for rendering

2. **State Management**:
   - React hooks for local state
   - Centralized API service
   - Error boundary components

3. **Styling Strategy**:
   - Utility-first approach with Tailwind CSS
   - Responsive design for all screen sizes
   - Consistent design language

## Deployment Considerations

1. **Infrastructure as Code**:
   - Terraform for AWS resource provisioning
   - Configurable environment settings
   - Reproducible infrastructure

2. **Development Workflow**:
   - Local development with Docker (optional)
   - CI/CD integration potential
   - Environment-specific configurations

3. **Scaling Strategy**:
   - Horizontal scaling for application tier
   - Vertical scaling for database tier
   - Redshift resize capability for warehouse

## Trade-offs and Considerations

1. **Cost vs. Performance**:
   - AWS services introduce operational costs
   - Redshift pricing scales with cluster size
   - Evaluate cost-benefit for data volume

2. **Complexity vs. Capability**:
   - More complex architecture than a monolithic approach
   - Enables significantly more powerful analytics
   - Consider simplification for small datasets

3. **Build vs. Buy**:
   - Custom solution vs. third-party analytics tools
   - Greater flexibility but higher development investment
   - Integration with existing stack

## Performance Benchmarks

Our target performance metrics are:

1. **Query Performance**:
   - Dashboard loading: < 2 seconds
   - Filter changes: < 1 second
   - Complex aggregations: < 3 seconds

2. **ETL Throughput**:
   - 1 million records per minute loading rate
   - Daily sync completed within 15 minutes
   - Full reload capabilities within 2 hours

3. **Scalability**:
   - Linear performance scaling up to 100 million records
   - Support for 5+ years of historical data
   - Concurrent user support: 50+ users

## Security Considerations

1. **Data Protection**:
   - Encryption at rest (S3 and Redshift)
   - Encryption in transit (HTTPS/TLS)
   - Column-level security where needed

2. **Access Control**:
   - JWT authentication for API
   - Role-based access for different user types
   - Fine-grained permissions for data access

3. **Audit and Compliance**:
   - Query logging
   - User activity tracking
   - Compliance with relevant regulations

## Potential Future Enhancements

1. **Advanced Analytics**:
   - Predictive models for sales forecasting
   - Anomaly detection for unusual patterns
   - Recommendation systems for related products

2. **Additional Data Sources**:
   - Integration with marketing data
   - External market data correlation
   - Customer behavior analytics

3. **Technical Improvements**:
   - Real-time data pipeline with Kinesis
   - Advanced caching strategies
   - Automated scaling based on workload

## Conclusion

This architecture provides a solid foundation for our book sales analytics research. By separating transactional and analytical processing, we can deliver powerful insights without compromising application performance. The modular approach allows for incremental development and future expansion as our analytics needs evolve.

---

Document Version: 1.0  
Last Updated: May 2025  
Authors: BI Research & Development Team