"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function AuthConfirm() {
  const router = useRouter();

  useEffect(() => {
    async function activate() {
      try {
        const hash = window.location.hash;
        const params = new URLSearchParams(hash.replace("#", "?"));
        const accessToken = params.get("access_token");

        if (!accessToken) {
          router.push("/login");
          return;
        }

        const base64 = accessToken.split(".")[1];
        const payload = JSON.parse(atob(base64));
        const userId = payload.sub;

        await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/verify-email`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ user_id: userId }),
        });

        router.push("/login?verified=true");
      } catch (err) {
        router.push("/login");
      }
    }

    activate();
  }, []);

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-white mb-4">
          SecureIT<span className="text-red-500">360</span>
        </h1>
        <p className="text-gray-400">Activating your account...</p>
      </div>
    </div>
  );
}
