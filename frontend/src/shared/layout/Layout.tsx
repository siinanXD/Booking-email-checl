import { Outlet } from "react-router-dom";
import { Sidebar } from "@/shared/layout/Sidebar";
import { TopBar } from "@/shared/layout/TopBar";

export function Layout() {
  return (
    <div className="flex min-h-screen" style={{ background: "#f1f5f9" }}>
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <TopBar />
        {/* Dot-grid background only visible in large empty spaces */}
        <main
          className="relative flex-1 overflow-auto p-6"
          style={{
            backgroundImage: "radial-gradient(circle, #cbd5e1 1px, transparent 1px)",
            backgroundSize: "24px 24px",
          }}
        >
          <div className="relative mx-auto max-w-7xl animate-fade-in">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
