# Financial Coach Frontend - Implementation Summary

## Component Responsibilities

| Component | Responsibility |
|-----------|----------------|
| **Dashboard** | Main page orchestration: holds input state, API mutation (React Query), highlighted dimension for RiskCard→chart linking. Renders input sidebar and results grid. Handles loading and error states. |
| **InputPanel** | Manual entry for monthly_income, monthly_expenses, current_savings, risk_tolerance. Validates inputs and triggers analysis run. Displays inline error from API. |
| **CSVUpload** | Drag-and-drop or file select for CSV. Parses via `csvParser`, derives monthly averages, passes result to parent via `onParsed`. Shows parse errors. |
| **ExampleDataSelector** | Three presets (Struggling, Moderate, Comfortable). Populates input fields on select. Tracks selected preset for visual state. |
| **SummaryBanner** | Displays monthly income, expenses, savings, and savings rate. Status badge: Healthy / Moderate / At Risk. Empty state when no data. |
| **RiskCard** | Per-dimension risk card (Savings, ExpenseRatio, Input). Shows risk_level and reason. Tooltip explains why rule triggered. Hover sets `highlightedDimension` for chart linking. |
| **SavingsGauge** | Recharts RadialBarChart for savings rate. Highlights when `highlightedDimension === "Savings"`. |
| **ExpenseChart** | Recharts PieChart for income allocation (savings vs expenses). Highlights when `highlightedDimension === "ExpenseRatio"`. |
| **MonthlyTrendChart** | Recharts BarChart for income vs expenses. Highlights when `highlightedDimension === "Input"` or trend-related. |
| **AIReflectionPanel** | Shows `generation` text, `ValidationBadge`, trace status (LLM used vs skipped). Empty state before first run. |
| **ValidationBadge** | Valid/invalid badge with optional issues list. Used in AI Reflection panel. |
| **Tooltip** | Hover tooltip for rule explanations. Used on RiskCard info icon. |

## Services & Utils

| File | Responsibility |
|------|----------------|
| **agentApi.ts** | Axios client, `runAgent(input)` POST to `/agent/run`. Error handling for network/CORS. Base URL from `VITE_API_URL` or empty (dev proxy). |
| **csvParser.ts** | Parse CSV, detect income/expense columns (or amount+type), derive monthly averages. Returns `{ monthly_income, monthly_expenses }`. |
| **mappings.ts** | `DIMENSION_TO_CHART`, `RISK_COLORS`, `DIMENSION_LABELS` for RiskCard and chart highlighting. |

## Tech Stack

- **Vite** + **React** + **TypeScript**
- **Tailwind v4** (PostCSS + `@tailwindcss/postcss`)
- **React Query** for API mutation
- **Recharts** for charts
- **Framer Motion** for card hover, transitions, loading states
- **Axios** for HTTP
- **Lucide React** for icons

## Configuration

- **Vite proxy**: `/agent` → `http://localhost:8000` in dev (avoids CORS)
- **VITE_API_URL**: Optional; empty uses same-origin + proxy in dev
