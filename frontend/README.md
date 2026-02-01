# Smart Financial Coach - Frontend

A fintech-style React frontend for the Smart Financial Coach agent. Enter income and expenses, run analysis, and explore risk insights with polished visualizations.

## Quick Start

```bash
npm install
npm run dev
```

Ensure the backend is running on `http://localhost:8000` (Vite proxies `/agent` to it).

## Supported CSV Formats

### Format A: Monthly Aggregates

| month   | income | expenses |
|---------|--------|----------|
| 2024-01 | 8000   | 5500     |
| 2024-02 | 8200   | 5200     |

### Format B: Categorized Expenses

| month   | category | amount |
|---------|----------|--------|
| 2024-01 | Housing  | 2000   |
| 2024-01 | Food     | 800    |
| 2024-01 | Transport| 400    |

Note: Format B requires income to be entered manually. Use the "Monthly" template if you have both income and expenses.

### Format C: Combined (Transaction Log)

| month   | type   | amount | category |
|---------|--------|--------|----------|
| 2024-01 | income | 8000   |          |
| 2024-01 | expense| 2000   | Housing  |
| 2024-01 | expense| 800    | Food     |

### Download Templates

Use the "Monthly" or "Categorized" buttons in the Portfolio Data (CSV) section to download a template. Use "Generate fake sample data" to populate with realistic sample data including expense categories and asset allocation.

## User Scenarios

- **Manual entry (income + expenses)** – backward compatible; enter values and run analysis
- **Expense breakdown** – use the spreadsheet editor to add categories; total is computed automatically
- **Asset allocation** – add asset classes with percentages (must sum to 100%); pie chart visualization
- **CSV upload** – use templates or generate sample data; supports monthly aggregates and categorized expenses

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
- `src/components/` – UI components (InputPanel, ExpenseCategoryEditor, AssetAllocationEditor, CSVUpload, etc.)
- `src/services/agentApi.ts` – API client
- `src/utils/` – csvParser, csvTemplates, mappings, sampleDataGenerator
