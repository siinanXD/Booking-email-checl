/** Datumsbereich für Listen-Filter (ISO date strings). */

export type DateRangeValue = {
  fromDate: string;
  toDate: string;
};

export function defaultDateRange(days = 30): DateRangeValue {
  const to = new Date();
  const from = new Date();
  from.setDate(from.getDate() - days);
  return {
    fromDate: from.toISOString().slice(0, 10),
    toDate: to.toISOString().slice(0, 10),
  };
}

export function dateRangeQueryParams(range: DateRangeValue): Record<string, string> {
  const params: Record<string, string> = {};
  if (range.fromDate) params.from_date = range.fromDate;
  if (range.toDate) params.to_date = range.toDate;
  return params;
}
