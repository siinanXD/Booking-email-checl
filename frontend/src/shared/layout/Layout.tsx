import { Outlet } from "react-router-dom";
import { Sidebar } from "@/shared/layout/Sidebar";
import { TopBar } from "@/shared/layout/TopBar";

export function Layout() {
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex flex-1 flex-col">
        <TopBar />
        <main className="flex-1 overflow-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
