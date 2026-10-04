import type { Request, Response, NextFunction } from "express";
import jwt from "jsonwebtoken";

const secret = process.env.JWT_SECRET ?? "dev-jwt-secret-change-me";

export type AuthContext = { tenantId: string; scopes: string[] };

export function authMiddleware(req: Request, res: Response, next: NextFunction): void {
  const token =
    (req.query.token as string | undefined) ??
    req.header("Authorization")?.replace(/^Bearer\s+/i, "") ??
    req.header("X-API-Key");
  if (!token) {
    res.status(401).json({ error: "unauthorized" });
    return;
  }
  if (token.startsWith("mc_live_")) {
    res.status(401).json({ error: "use jwt or stream token for sse" });
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
    (req as Request & { tenantId?: string }).tenantId = payload.tenant_id;
    next();
  } catch {
    res.status(401).json({ error: "invalid token" });
  }
}
