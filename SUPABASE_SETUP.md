# ASTHA ERP — Supabase PostgreSQL & Render Deployment Guide

This guide explains how to connect **ASTHA ERP** to Supabase PostgreSQL (Cloud Database) and Render (Cloud Hosting).

---

## 1. Supabase PostgreSQL Configuration

1. Log into your [Supabase Dashboard](https://supabase.com/dashboard).
2. Create a new project named **ASTHA-CLOUD-ERP**.
3. Go to **Project Settings** → **Database** → **Connection String** → Select **URI** (Transaction Pooler or Direct).
   Format:
   ```text
   postgresql://postgres.[PROJECT_REF]:[YOUR_PASSWORD]@aws-0-ap-south-1.pooler.supabase.com:6543/postgres
   ```
4. Set this environment variable in your terminal or `.env` file:
   ```bash
   $env:DATABASE_URL="postgresql://postgres.[PROJECT_REF]:[YOUR_PASSWORD]@aws-0-ap-south-1.pooler.supabase.com:6543/postgres"
   ```

---

## 2. Deploying to Render (Free Web Service)

1. Connect your GitHub repository `https://github.com/palkrishanga-glitch/astha-cloud-erp` to [Render.com](https://render.com).
2. Click **New +** → **Web Service** → Select repository `astha-cloud-erp`.
3. Set Environment Variable:
   - `DATABASE_URL` = Your Supabase URI string.
4. Render will automatically build the Docker container and deploy your live ERP API & Dashboard URL!
