import type { Request, Response, NextFunction } from "express";
import jwt from "jsonwebtoken";
import { verifyApiKey } from "./keyVerifier.js";

const secret = process.env.JWT_SECRET ?? "dev-jwt-secret-change-me";

export type AuthContext = { tenantId: string; scopes: string[] };

function hasReadScope(scopes: string[] | undefined): boolean {
  if (!scopes) return false;
  return scopes.includes("read") || scopes.includes("admin");
}

export async function authMiddleware(
  req: Request,
  res: Response,
  next: NextFunction,
): Promise<void> {
  const token =
    (req.query.token as string | undefined) ??
    req.header("Authorization")?.replace(/^Bearer\s+/i, "") ??
    req.header("X-API-Key");
  if (!token) {
    res.status(401).json({ error: "unauthorized" });
    return;
  }

  if (token.startsWith("mc_live_")) {
    const verified = await verifyApiKey(token);
    if (!verified || !hasReadScope(verified.scopes)) {
      res.status(401).json({ error: "invalid api key or missing read scope" });
      return;
    }
    (req as Request & { tenantId?: string }).tenantId = verified.tenantId;
    next();
    return;
  }

  try {
    const payload = jwt.verify(token, secret) as jwt.JwtPayload & {
      tenant_id?: string;
      scopes?: string[];
      type?: string;
    };
    if (!payload.tenant_id) {
      res.status(401).json({ error: "invalid token" });
      return;
    }
    const typ = payload.type ?? "access";
    if (typ === "run") {
      res.status(401).json({ error: "run tokens cannot access streams" });
      return;
    }
    if (typ === "access" || typ === "stream") {
      if (typ === "stream" && !hasReadScope(payload.scopes)) {
        res.status(401).json({ error: "invalid stream token" });
        return;
      }
      (req as Request & { tenantId?: string }).tenantId = payload.tenant_id;
      next();
      return;
    }
    res.status(401).json({ error: "invalid token type" });
  } catch {
    res.status(401).json({ error: "invalid token" });
  }
}
