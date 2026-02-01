# Smart Financial Coach - Frontend

A fintech-style React frontend for the Smart Financial Coach agent. Enter income and expenses, run analysis, and explore risk insights with polished visualizations.

## Quick Start

```bash
npm install
npm run dev
```

Ensure the backend is running on `http://localhost:8000` (Vite proxies `/agent` to it).

## Supported User Personas (Case Studies)

### 1. Early-Career Professional

- **Goal:** Understand savings rate, avoid lifestyle inflation
- **Uses:** Manual input, presets, savings gauge

### 2. High-Income / High-Spend Individual

- **Goal:** Detect overspending despite high income
- **Uses:** Risk cards + expense ratio visualization

### 3. Freelancer / Variable Income Worker

- **Goal:** Analyze month-to-month volatility
- **Uses:** CSV upload + trend chart

### 4. Financially Conservative Planner

- **Goal:** Validate healthy savings behavior
- **Uses:** AI Insight Summary + validation badge

### 5. Demo / Reviewer / Hiring Manager

- **Goal:** See agent orchestration, explainability, and UI polish
- **Uses:** Presets → hover → charts → AI reflection

## Tech Stack

- Vite + React + TypeScript
- Tailwind v4
- Recharts, Framer Motion, React Query, Axios, Lucide React

## Project Structure

- `src/pages/Dashboard.tsx` – main page
- `src/components/` – UI components
- `src/services/agentApi.ts` – API client
- `src/utils/` – csvParser, mappings, sampleDataGenerator
