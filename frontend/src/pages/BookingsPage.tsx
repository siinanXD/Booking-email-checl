import { EmailListPage } from "@/pages/EmailListPage";

export function BookingsPage() {
  return (
    <EmailListPage
      title="Buchungen"
      subtitle="Neue Buchungen (Intent: new_booking)"
      mode="bookings"
    />
  );
}
