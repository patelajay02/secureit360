import { NextResponse } from "next/server";

export async function GET(request) {
  const { searchParams, origin } = new URL(request.url);
  const code = searchParams.get("code");
  const error = searchParams.get("error");
  const state = searchParams.get("state");

  const settingsBase = `${origin}/settings?tab=integrations`;

  if (error) {
    return NextResponse.redirect(`${settingsBase}&google_error=${encodeURIComponent(error)}`);
  }

  if (!code || !state) {
    return NextResponse.redirect(`${settingsBase}&google_error=invalid_callback`);
  }

  let userToken;
  try {
    userToken = Buffer.from(state, "base64url").toString("utf-8");
  } catch {
    return NextResponse.redirect(`${settingsBase}&google_error=invalid_state`);
  }

  const redirectUri = `${origin}/api/google/callback`;

  try {
    const resp = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/integrations/google/connect`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${userToken}`,
      },
      body: JSON.stringify({ code, redirect_uri: redirectUri }),
    });

    if (!resp.ok) {
      const data = await resp.json().catch(() => ({}));
      const msg = data.detail || "Connection failed";
      return NextResponse.redirect(`${settingsBase}&google_error=${encodeURIComponent(msg)}`);
    }

    return NextResponse.redirect(`${settingsBase}&google_connected=1`);
  } catch (err) {
    return NextResponse.redirect(`${settingsBase}&google_error=${encodeURIComponent(err.message)}`);
  }
}
