"use client";

import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

type HealthStatus = "loading" | "ok" | "error";

export default function Home() {
  const [status, setStatus] = useState<HealthStatus>("loading");

  useEffect(() => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
    fetch(`${apiUrl}/health`)
      .then((res) => res.json())
      .then((data) => setStatus(data.status === "ok" ? "ok" : "error"))
      .catch(() => setStatus("error"));
  }, []);

  const badgeVariant =
    status === "ok" ? "default" : status === "error" ? "destructive" : "secondary";
  const badgeLabel =
    status === "loading" ? "Checking…" : status === "ok" ? "Online" : "Unreachable";

  return (
    <main className="flex min-h-screen items-center justify-center bg-background p-8">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="text-2xl">FabGreat Library</CardTitle>
          <p className="text-sm text-muted-foreground">
            Flesh &amp; Blood collection tracker
          </p>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-3">
            <span className="text-sm font-medium">API status</span>
            <Badge variant={badgeVariant}>{badgeLabel}</Badge>
          </div>
          <p className="text-xs text-muted-foreground">
            Backend:{" "}
            <code className="rounded bg-muted px-1 py-0.5">
              {process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}
            </code>
          </p>
        </CardContent>
      </Card>
    </main>
  );
}
