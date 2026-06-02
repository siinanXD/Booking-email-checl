import { EmailListPage } from "@/features/emails/EmailListPage";

export function ChangesPage() {
  return (
    <EmailListPage
      title="Änderungen"
      subtitle="Buchungsänderungen"
      params={{ intent: "change", booking_related: true }}
    />
  );
}
