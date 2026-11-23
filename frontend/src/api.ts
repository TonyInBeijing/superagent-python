export type ReadyState = "loading" | "up" | "down";

// 相对路径：开发由 Vite 代理，Compose 由 Nginx 代理，后端收到的都是 /api/v1/...
export async function fetchReady(signal?: AbortSignal): Promise<ReadyState> {
  try {
    const res = await fetch("/api/v1/health/ready", { signal });
    if (!res.ok) return "down";
    const body = await res.json();
    return body?.data?.status === "ready" && body?.data?.database === "up" ? "up" : "down";
  } catch (e) {
    if ((e as Error).name === "AbortError") throw e;
    return "down";
  }
}
