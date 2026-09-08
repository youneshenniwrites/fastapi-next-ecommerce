import "server-only";
import { NextRequest, NextResponse } from "next/server";
import { apiClient } from "./api/client";

function policy() {
  const raw = process.env.APP_ORIGIN;
  if (!raw) throw new Error("APP_ORIGIN is required for sessions");
  const origin = new URL(raw);
  if (origin.origin !== raw || origin.username || origin.password)
    throw new Error("APP_ORIGIN must be an origin");
  const secure = origin.protocol === "https:";
  if (
    !secure &&
    !(
      origin.protocol === "http:" &&
      ["localhost", "127.0.0.1", "[::1]"].includes(origin.hostname) &&
      process.env.ALLOW_LOCAL_HTTP_SESSIONS === "true"
    )
  )
    throw new Error(
      "Sessions require HTTPS or explicit loopback development mode",
    );
  return {
    origin: raw,
    secure,
    name: secure ? "__Host-session" : "local-session",
  };
}

function reply(body: object, status = 200) {
  return NextResponse.json(body, {
    status,
    headers: {
      "Cache-Control": "private, no-store",
      Vary: "Cookie",
    },
  });
}

function clear(response: NextResponse, config: ReturnType<typeof policy>) {
  response.cookies.set(config.name, "", {
    httpOnly: true,
    secure: config.secure,
    sameSite: "lax",
    path: "/",
    maxAge: 0,
  });
  return response;
}

export async function login(request: NextRequest) {
  try {
    const config = policy();
    if (request.headers.get("origin") !== config.origin)
      return reply({ error: "Origin rejected" }, 403);
    if (!request.headers.get("content-type")?.startsWith("application/json"))
      return reply({ error: "Expected JSON" }, 415);
    let input;
    try {
      input = await request.json();
    } catch {
      return reply({ error: "Invalid JSON" }, 400);
    }
    if (
      !input ||
      typeof input.email !== "string" ||
      typeof input.password !== "string" ||
      !input.email ||
      input.email.length > 254 ||
      !input.password ||
      input.password.length > 1024
    )
      return reply({ error: "Email and password are required" }, 400);
    // No caller-controlled redirect is accepted. Account UI chooses its own local navigation.
    if ("next" in input || "redirect" in input)
      return reply({ error: "Redirect parameters are not supported" }, 400);
    const started = Date.now();
    const result = await apiClient().POST("/api/v1/auth/login", {
      redirect: "error",
      body: { username: input.email, password: input.password, scope: "" },
      bodySerializer: (body) =>
        new URLSearchParams(body as Record<string, string>).toString(),
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
    if (result.response.status === 401)
      return clear(reply({ error: "Invalid credentials" }, 401), config);
    if (!result.data || result.response.status !== 200)
      return reply({ error: "Authentication service unavailable" }, 503);
    const { access_token, expires_in, token_type } = result.data;
    const lifetime = Math.floor(expires_in - (Date.now() - started) / 1000) - 1;
    if (
      !access_token ||
      token_type !== "bearer" ||
      !Number.isSafeInteger(lifetime) ||
      lifetime <= 0
    )
      return reply({ error: "Authentication service unavailable" }, 503);
    const response = reply({ authenticated: true });
    response.cookies.set(config.name, access_token, {
      httpOnly: true,
      secure: config.secure,
      sameSite: "lax",
      path: "/",
      maxAge: lifetime,
    });
    return response;
  } catch {
    return reply({ error: "Authentication service unavailable" }, 503);
  }
}

export async function profile(request: NextRequest) {
  try {
    const config = policy();
    const token = request.cookies.get(config.name)?.value;
    if (!token) return reply({ error: "Sign in required" }, 401);
    const result = await apiClient().GET("/api/v1/auth/me", {
      redirect: "error",
      headers: { Authorization: `Bearer ${token}` },
    });
    if (result.response.status === 401)
      return clear(reply({ error: "Sign in required" }, 401), config);
    if (!result.data || result.response.status !== 200)
      return reply({ error: "Authentication service unavailable" }, 503);
    return reply(result.data);
  } catch {
    return reply({ error: "Authentication service unavailable" }, 503);
  }
}

export async function logout(request: NextRequest) {
  try {
    const config = policy();
    if (request.headers.get("origin") !== config.origin)
      return reply({ error: "Origin rejected" }, 403);
    return clear(reply({ authenticated: false }), config);
  } catch {
    return reply({ error: "Authentication service unavailable" }, 503);
  }
}
