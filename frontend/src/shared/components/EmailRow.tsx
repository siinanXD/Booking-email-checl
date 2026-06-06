import { IntentBadge } from "@/shared/components/IntentBadge";
import { Badge } from "@/shared/ui/Badge";
import type { EmailListItem } from "@/lib/types/api";

export function EmailRow({
  item,
  onClick,
}: {
  item: EmailListItem;
  onClick?: () => void;
}) {
  const tone =
    item.review_status === "pending" || item.processing_state === "pending_review"
      ? "pending"
      : item.processing_state;

  return (
    <tr
      className={`transition-colors duration-100 ${
        onClick ? "cursor-pointer hover:bg-indigo-50/40" : ""
      }`}
      onClick={onClick}
    >
      <td className="px-4 py-3 text-xs tabular-nums text-slate-500">
        {item.received_at
          ? new Date(item.received_at).toLocaleString("de-DE")
          : "—"}
      </td>
      <td className="px-4 py-3 text-sm font-medium text-slate-700">
        {item.from_address}
      </td>
      <td className="px-4 py-3 text-sm font-semibold text-slate-900">
        {item.booking_number ?? "—"}
      </td>
      <td className="px-4 py-3 text-sm text-slate-500">{item.platform ?? "—"}</td>
      <td className="px-4 py-3">
        {item.intent ? (
          <IntentBadge intent={item.intent} />
        ) : (
          <Badge label={item.processing_state} tone={tone} dot />
        )}
      </td>
      <td className="max-w-xs truncate px-4 py-3 text-sm text-slate-600">
        {item.subject}
      </td>
    </tr>
  );
}
