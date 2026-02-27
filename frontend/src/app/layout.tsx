import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "PS-03 Autonomous Onboarding Agent",
  description: "Personalized developer onboarding powered by an autonomous chat agent.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
