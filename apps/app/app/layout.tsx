import "./globals.css";

export const metadata = {
  title: "app.mcpserver.in — MCP Workspace",
  description: "Mobile-first MCP workspace with tools, playground, and skills",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <div className="min-h-screen bg-gray-50">
          <main className="container mx-auto p-4">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}