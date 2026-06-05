import { intentLabel, intentTone } from "@/lib/intentDisplay";
import { Badge } from "@/shared/ui/Badge";

type Props = {
  intent: string | null | undefined;
};

export function IntentBadge({ intent }: Props) {
  return <Badge label={intentLabel(intent)} tone={intentTone(intent)} />;
}
