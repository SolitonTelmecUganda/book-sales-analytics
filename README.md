# Django + AWS + React Book Sales Analytics

## Overview
This repository contains our research project for evaluating a modern data analytics architecture using Django, AWS, and React.

The architecture is designed to handle high-volume book sales data by offloading analytics workloads to a dedicated data warehouse (AWS Redshift).

## Documentation
- [Main Documentation](OVERVIEW.md) - Comprehensive project overview
- [Frontend Documentation](frontend/README.md) - React frontend details
- [Architecture](docs/ARCHITECTURE.md) - Detailed architecture explanation

## Getting Started
See the [OVERVIEW.md](OVERVIEW.md) for complete setup instructions.

## Research Goals
1. Evaluate the performance of this architecture with large datasets
2. Determine if the separation of transactional and analytical processing improves overall performance
3. Benchmark the data pipeline for scalability
4. Assess the user experience of the React-based analytics dashboard

## Key Components
- **Django Backend**: Handles transactional data and provides analytics API
- **AWS S3 & Redshift**: Data lake and warehouse for analytics processing
- **React Frontend**: Interactive dashboard for data visualization

## Current Status
This project is in the research and benchmarking phase. Please coordinate with the team before making changes.

## Team
- Data Engineering Team
- Frontend Development Team
- Cloud Infrastructure Team

## License
Internal use only - research project