import { useCallback, useEffect, useRef, useState } from "react";
import { fetchReady, ReadyState } from "./api";

const LABEL: Record<ReadyState, string> = {
  loading: "检查中…",
  up: "可用（后端与数据库已就绪）",
  down: "不可用（后端未就绪或无法连接）",
};

export default function ServiceStatus() {
  const [state, setState] = useState<ReadyState>("loading");
  const ctl = useRef<AbortController | null>(null);

  const check = useCallback(() => {
    ctl.current?.abort();
    const c = new AbortController();
    ctl.current = c;
    setState("loading");
    fetchReady(c.signal).then(setState, () => {});
  }, []);

  // 首次打开只检查一次，不轮询；之后只能手动重试
  useEffect(() => {
    check();
    return () => ctl.current?.abort();
  }, [check]);

  return (
    <div className={`status status--${state}`} role="status" aria-live="polite">
      <span className="status__dot" />
      <span>服务状态：{LABEL[state]}</span>
      <button type="button" className="btn" onClick={check} disabled={state === "loading"}>
        重试
      </button>
    </div>
  );
}
