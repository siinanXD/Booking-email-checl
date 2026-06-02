import { EmailListPage } from "@/pages/EmailListPage";

export function MessagesPage() {
  return (
    <EmailListPage
      title="Nachrichten"
      subtitle="Gästeanfragen und sonstige Kommunikation"
      params={{ intent: "guest_inquiry" }}
    />
  );
}
