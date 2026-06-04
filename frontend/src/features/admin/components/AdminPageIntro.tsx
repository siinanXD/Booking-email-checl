import { Card } from "@/shared/ui/Card";

export function AdminPageIntro({
  title,
  description,
  impact,
}: {
  title: string;
  description: string;
  impact?: string;
}) {
  return (
    <Card className="border-indigo-100 bg-gradient-to-br from-indigo-50/80 to-white">
      <h2 className="text-lg font-medium text-slate-900">{title}</h2>
      <p className="mt-2 text-sm leading-relaxed text-slate-600">{description}</p>
      {impact && (
        <p className="mt-3 rounded-lg border border-indigo-100 bg-white/70 px-3 py-2 text-sm text-slate-700">
          <span className="font-medium text-indigo-800">Was sich ändert: </span>
          {impact}
        </p>
      )}
    </Card>
  );
}
