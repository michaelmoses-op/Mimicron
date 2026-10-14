import { createHash } from "node:crypto";
import { Redis } from "ioredis";

export type VerifiedKey = {
  tenantId: string;
  keyId: string;
  scopes: string[];
};

type VerifyResponse = {
  tenant_id: string;
  key_id: string;
  scopes: string[];
};

const cacheTtlSeconds = Number(process.env.API_KEY_CACHE_TTL_SECONDS ?? "300");

let redis: Redis | null = null;

function getRedis(): Redis | null {
  const url = process.env.REDIS_URL;
  if (!url) return null;
  if (!redis) {
    redis = new Redis(url, { maxRetriesPerRequest: 2, lazyConnect: true });
  }
  return redis;
}

export async function verifyApiKey(fullKey: string): Promise<VerifiedKey | null> {
  const hash = createHash("sha256").update(fullKey).digest("hex");
  const cacheKey = `apikey:${hash}`;
  const r = getRedis();
  if (r) {
    try {
      if (r.status !== "ready") await r.connect();
      const cached = await r.get(cacheKey);
      if (cached) {
        const payload = JSON.parse(cached) as VerifyResponse;
        return mapVerify(payload);
      }
    } catch {
      /* fall through to control-api */
    }
  }

  const base = (process.env.CONTROL_API_URL ?? "http://control-api:8000").replace(/\/$/, "");
  const secret = process.env.INTERNAL_API_SECRET ?? "";
  const resp = await fetch(`${base}/internal/v1/keys/verify`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Internal-Secret": secret,
    },
    body: JSON.stringify({ key_hash: hash }),
  });
  if (resp.status === 404) return null;
  if (!resp.ok) return null;
  const payload = (await resp.json()) as VerifyResponse;
  if (r) {
    try {
      await r.set(cacheKey, JSON.stringify(payload), "EX", cacheTtlSeconds);
    } catch {
      /* ignore cache write */
    }
  }
  return mapVerify(payload);
}

function mapVerify(v: VerifyResponse): VerifiedKey {
  return { tenantId: v.tenant_id, keyId: v.key_id, scopes: v.scopes ?? [] };
}
