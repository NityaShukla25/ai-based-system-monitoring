# AI-Based System Monitoring Platform

## Overview
This project collects real-time system metrics from the operating system using Python and stores them in a PostgreSQL database.

The system currently monitors:
- CPU usage
- Memory usage
- Disk usage
- Network usage

This project can later be extended with:
- Real-time dashboard
- AI-based anomaly detection
- Alert generation

---

## System Architecture

Operating System  
↓  
Python Monitoring Agent (`psutil`)  
↓  
PostgreSQL Database  
↓  
Separate Metric Tables  
↓  
Dashboard / AI Analysis  

---

## Features
- Collects real-time system metrics
- Stores metrics in PostgreSQL
- Uses separate tables for CPU, memory, disk, and network
- Timestamp-based data collection
- Easy to extend for AI monitoring

---

## Technologies Used
- Python
- PostgreSQL
- psutil
- psycopg2
- GitHub

---

## Database Tables

### 1. cpu_metrics
Stores CPU usage data.

### 2. memory_metrics
Stores memory usage data.

### 3. disk_metrics
Stores disk usage data.

### 4. network_metrics
Stores network usage data.

---

## Project Structure

```bash
ai-based-system-monitoring
├── collector.py
├── README.md
├── schema.sql
