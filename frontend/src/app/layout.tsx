import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ODA (Onboarding Developer Agent)",
  description: "Source-grounded developer onboarding console.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="bg-background text-foreground antialiased">
        {children}
      </body>
    </html>
  );
}
