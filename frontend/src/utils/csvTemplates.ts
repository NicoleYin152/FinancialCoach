/**
 * CSV template generators for supported formats.
 */

export function getMonthlyTemplate(): string {
  return `month,income,expenses
2024-01,8000,5500
2024-02,8200,5200
2024-03,8000,5800`;
}

export function getCategorizedTemplate(): string {
  return `month,category,amount
2024-01,Housing,2000
2024-01,Food,800
2024-01,Transport,400
2024-01,Utilities,300
2024-01,Other,500`;
}

export function getCombinedTemplate(): string {
  return `month,type,amount,category
2024-01,income,8000,
2024-01,expense,2000,Housing
2024-01,expense,800,Food
2024-01,expense,400,Transport`;
}

export function downloadCsv(content: string, filename: string): void {
  const blob = new Blob([content], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
