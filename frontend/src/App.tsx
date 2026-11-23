import { useState } from "react";
import ServiceStatus from "./ServiceStatus";

type View = "workbench" | "tasks" | "results" | "admin";
const NAV: { id: View; label: string }[] = [
  { id: "workbench", label: "工作台" },
  { id: "tasks", label: "任务" },
  { id: "results", label: "工作成果" },
  { id: "admin", label: "管理" },
];

const Later = () => <span className="tag">后续实现</span>;

function Empty({ title, hint }: { title: string; hint: string }) {
  return (
    <div className="empty">
      <h2>{title}</h2>
      <p>{hint}</p>
      <Later />
    </div>
  );
}

function Workbench() {
  return (
    <div className="layout">
      <aside className="threads" aria-label="Agent 列表">
        <h3>Agent 列表 <Later /></h3>
        <ul className="thread-list">
          <li className="thread is-disabled">SuperAgent（尚未实现）</li>
        </ul>
        <button type="button" className="btn" disabled>＋ 新建 Agent（后续实现）</button>
      </aside>
      <main className="chat" aria-label="对话工作台">
        <ServiceStatus />
        <div className="chat__body">
          <p className="muted">对话与任务执行尚未实现，这里不会产生任何回复。</p>
        </div>
        <form className="composer" onSubmit={(e) => e.preventDefault()}>
          <textarea rows={3} disabled aria-label="工作目标" placeholder="工作目标输入（后续实现，当前不能提交）" />
          <div className="composer__row">
            <select disabled aria-label="Agent 选择"><option>选择 Agent（后续实现）</option></select>
            <button type="button" className="btn" disabled>资料（后续实现）</button>
            <button type="submit" className="btn btn--primary" disabled>发送</button>
          </div>
        </form>
      </main>
      <aside className="info" aria-label="工作信息">
        <h3>工作信息 <Later /></h3>
        <p className="muted">任务进度、资料和成果将在后续课程接入。</p>
      </aside>
    </div>
  );
}

function Admin() {
  const items = ["用户", "Agent", "模型", "用量"];
  return (
    <div className="page">
      <h2>管理 <Later /></h2>
      <p className="muted">以下入口均未实现；当前没有登录和授权，也不显示任何用户数据。</p>
      <div className="cards">
        {items.map((i) => (
          <div className="card" key={i}><strong>{i}</strong><p className="muted">尚未实现</p><Later /></div>
        ))}
      </div>
    </div>
  );
}

export default function App() {
  const [view, setView] = useState<View>("workbench");
  return (
    <>
      <header className="topbar">
        <span className="brand">SuperAgent</span>
        <nav className="topnav" aria-label="主导航">
          {NAV.map((n) => (
            <button key={n.id} type="button" className={`nav__item${view === n.id ? " is-active" : ""}`}
              aria-current={view === n.id ? "page" : undefined} onClick={() => setView(n.id)}>
              {n.label}
            </button>
          ))}
        </nav>
      </header>
      {view === "workbench" && <Workbench />}
      {view === "tasks" && <div className="page"><Empty title="任务" hint="暂无任务。任务创建与调度将在后续课程接入。" /></div>}
      {view === "results" && <div className="page"><Empty title="工作成果" hint="暂无成果。工作成果将在后续课程接入。" /></div>}
      {view === "admin" && <Admin />}
    </>
  );
}
