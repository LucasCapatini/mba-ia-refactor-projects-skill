"""Smoke test sequencial dos 3 projetos refatorados. Uso: python smoke.py <1|2|3>"""
import json, os, subprocess, sys, time, urllib.request, urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # raiz do repositório

def req(method, url, body=None, headers=None):
    data = None
    h = dict(headers or {})
    if body is not None:
        if isinstance(body, (dict, list)):
            data = json.dumps(body).encode(); h["Content-Type"] = "application/json"
        else:
            data = body.encode(); h.setdefault("Content-Type", "application/json")
    r = urllib.request.Request(url, data=data, method=method, headers=h)
    try:
        with urllib.request.urlopen(r, timeout=10) as resp:
            raw = resp.read().decode("utf-8", "replace"); st = resp.status
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace"); st = e.code
    try:
        js = json.loads(raw)
    except Exception:
        js = None
    return st, js, raw

def keys(js):
    if isinstance(js, dict): return sorted(js)
    if isinstance(js, list): return f"list[{len(js)}]" + (f" item:{sorted(js[0])}" if js and isinstance(js[0], dict) else "")
    return type(js).__name__

def wait(url, secs=20):
    for _ in range(secs * 2):
        try:
            urllib.request.urlopen(url, timeout=2); return True
        except Exception:
            time.sleep(0.5)
    return False

def run(project, cmd, cwd, port, health, steps, env_extra=None, pre=None):
    env = dict(os.environ, DEBUG="false", PYTHONIOENCODING="utf-8", **(env_extra or {}))
    if pre:
        print(f"[pre] {' '.join(pre)}")
        p = subprocess.run(pre, cwd=cwd, env=env, capture_output=True, text=True)
        print(p.stdout[-800:], p.stderr[-800:], f"exit={p.returncode}")
    logpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"server-{project}.log")
    logf = open(logpath, "w", encoding="utf-8")
    proc = subprocess.Popen(cmd, cwd=cwd, env=env, stdout=logf, stderr=subprocess.STDOUT)
    base = f"http://127.0.0.1:{port}"
    ok_boot = wait(base + health)
    print(f"\n=== {project} boot={'OK' if ok_boot else 'FAIL'} ({cmd}) ===")
    results = []
    ctx = {}
    try:
        if ok_boot:
            for s in steps:
                method, path = s["m"], s["p"]
                path = path.format(**ctx)
                body = s.get("b")
                if callable(body): body = body(ctx)
                st, js, raw = req(method, base + path, body)
                exp = s["e"] if isinstance(s["e"], (list, tuple)) else [s["e"]]
                bad_keys = [k for k in s.get("nokeys", []) if raw and k in raw]
                ok = st in exp and not bad_keys
                if s.get("save") and isinstance(js, dict):
                    ctx[s["save"]] = s["extract"](js)
                flag = "OK " if ok else "FAIL"
                extra = f" | leaked:{bad_keys}" if bad_keys else ""
                results.append(ok)
                print(f"{flag} {method:6} {path:40} -> {st} (exp {exp}) keys={keys(js) if js is not None else raw[:60]!s}{extra}")
    finally:
        subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True)
        time.sleep(1)
        logf.close(); out = open(logpath, encoding="utf-8", errors="replace").read()
        lines = [l for l in out.splitlines() if l.strip()]
        print("--- server log (tail) ---"); print("\n".join(lines[-12:]))
        try:
            urllib.request.urlopen(base + health, timeout=2); print("PORT STILL BOUND!")
        except Exception:
            print(f"port {port} free")
    print(f"=== {project}: {sum(results)}/{len(results)} OK ===\n")
    return all(results) and ok_boot

P1 = dict(project="code-smells-project", cmd=[sys.executable, "app.py"], cwd=os.path.join(ROOT, "code-smells-project"), port=5000, health="/health",
    steps=[
        dict(m="GET", p="/", e=200),
        dict(m="GET", p="/health", e=200, nokeys=["secret_key", "db_path"]),
        dict(m="GET", p="/produtos", e=200),
        dict(m="GET", p="/produtos/busca?q=mouse", e=200),
        dict(m="GET", p="/produtos/busca?q=x&preco_min=abc", e=400),
        dict(m="GET", p="/produtos/1", e=200),
        dict(m="GET", p="/produtos/9999", e=404),
        dict(m="POST", p="/produtos", b={"nome": "Teste", "descricao": "d", "preco": 10.5, "estoque": 3, "categoria": "geral"}, e=201, save="pid", extract=lambda j: (j.get("dados") or {}).get("id")),
        dict(m="POST", p="/produtos", b={"nome": "X", "preco": "abc"}, e=400),
        dict(m="PUT", p="/produtos/{pid}", b={"nome": "Teste2", "descricao": "d", "preco": 11, "estoque": 3, "categoria": "geral"}, e=200),
        dict(m="DELETE", p="/produtos/{pid}", e=200),
        dict(m="GET", p="/usuarios", e=200, nokeys=['"senha"']),
        dict(m="GET", p="/usuarios/1", e=200, nokeys=['"senha"']),
        dict(m="POST", p="/usuarios", b={"nome": "Novo", "email": "novo@x.com", "senha": "abcdef"}, e=201),
        dict(m="POST", p="/login", b={"email": "admin@loja.com", "senha": "admin123"}, e=200, nokeys=['"senha"']),
        dict(m="POST", p="/login", b={"email": "admin@loja.com", "senha": "errada"}, e=401),
        dict(m="POST", p="/login", b={"email": "' OR '1'='1' --", "senha": "x"}, e=[401, 400]),
        dict(m="POST", p="/login", b="", e=400),
        dict(m="POST", p="/pedidos", b={"usuario_id": 2, "itens": [{"produto_id": 2, "quantidade": 1}]}, e=201, save="pedido", extract=lambda j: (j.get("dados") or {}).get("pedido_id")),
        dict(m="POST", p="/pedidos", b={"usuario_id": 2, "itens": [{"produto_id": 2, "quantidade": 999}]}, e=400),
        dict(m="GET", p="/pedidos", e=200),
        dict(m="GET", p="/pedidos/usuario/2", e=200),
        dict(m="PUT", p="/pedidos/{pedido}/status", b={"status": "aprovado"}, e=200),
        dict(m="PUT", p="/pedidos/{pedido}/status", b={"status": "pago"}, e=400),
        dict(m="GET", p="/relatorios/vendas", e=200),
        dict(m="POST", p="/admin/reset-db", e=403),
        dict(m="POST", p="/admin/query", b={"sql": "SELECT 1"}, e=403),
        dict(m="GET", p="/rota-inexistente", e=404),
    ])

P2 = dict(project="ecommerce-api-legacy", cmd=["cmd", "/c", "npm", "start"], cwd=os.path.join(ROOT, "ecommerce-api-legacy"), port=3000, health="/api/admin/financial-report",
    steps=[
        dict(m="POST", p="/api/checkout", b={"usr": "Guilherme", "eml": "gui@fullcycle.com.br", "pwd": "senhaforte", "c_id": 2, "card": "4111222233334444"}, e=200),
        dict(m="POST", p="/api/checkout", b={"usr": "João", "eml": "joao@teste.com", "pwd": "123", "c_id": 1, "card": "5111222233334444"}, e=400),
        dict(m="POST", p="/api/checkout", b={"usr": "X", "eml": "x@x.com", "c_id": 99, "card": "4111222233334444"}, e=404),
        dict(m="POST", p="/api/checkout", b={"usr": "X"}, e=400),
        dict(m="POST", p="/api/checkout", b={"usr": "Num", "eml": "num@x.com", "c_id": 1, "card": 4111222233334444}, e=200),
        dict(m="GET", p="/api/admin/financial-report", e=200, nokeys=["Unknown", "pass"]),
        dict(m="DELETE", p="/api/users/1", e=200),
        dict(m="DELETE", p="/api/users/abc", e=400),
        dict(m="GET", p="/api/admin/financial-report", e=200, nokeys=["Unknown"]),
    ])

P3 = dict(project="task-manager-api", cmd=[sys.executable, "app.py"], cwd=os.path.join(ROOT, "task-manager-api"), port=5000, health="/health",
    pre=[sys.executable, "seed.py"],
    steps=[
        dict(m="GET", p="/health", e=200),
        dict(m="GET", p="/", e=200),
        dict(m="GET", p="/tasks", e=200),
        dict(m="GET", p="/tasks/1", e=200),
        dict(m="GET", p="/tasks/9999", e=404),
        dict(m="POST", p="/tasks", b={"title": "Nova task", "priority": 2, "user_id": 1, "category_id": 1, "tags": ["a", "b"]}, e=201, save="tid", extract=lambda j: j.get("id") or (j.get("task") or {}).get("id")),
        dict(m="POST", p="/tasks", b={"title": "ab"}, e=400),
        dict(m="POST", p="/tasks", b={"title": "Valida", "priority": "abc"}, e=400),
        dict(m="PUT", p="/tasks/{tid}", b={"status": "done"}, e=200),
        dict(m="GET", p="/tasks/search?q=task", e=200),
        dict(m="GET", p="/tasks/search?priority=abc", e=400),
        dict(m="GET", p="/tasks/stats", e=200),
        dict(m="DELETE", p="/tasks/{tid}", e=200),
        dict(m="GET", p="/users", e=200, nokeys=['"password"']),
        dict(m="GET", p="/users/1", e=200, nokeys=['"password"']),
        dict(m="POST", p="/users", b={"name": "Novo", "email": "novo@x.com", "password": "abcd"}, e=201, nokeys=['"password"'], save="uid", extract=lambda j: j.get("id") or (j.get("user") or {}).get("id")),
        dict(m="POST", p="/users", b={"name": "Dup", "email": "joao@email.com", "password": "abcd"}, e=409),
        dict(m="PUT", p="/users/{uid}", b={"name": "Renomeado"}, e=200, nokeys=['"password"']),
        dict(m="GET", p="/users/1/tasks", e=200),
        dict(m="POST", p="/login", b={"email": "joao@email.com", "password": "1234"}, e=200, nokeys=['"password"', "fake-jwt"]),
        dict(m="POST", p="/login", b={"email": "joao@email.com", "password": "errada"}, e=401),
        dict(m="DELETE", p="/users/{uid}", e=200),
        dict(m="GET", p="/reports/summary", e=200),
        dict(m="GET", p="/reports/user/1", e=200),
        dict(m="GET", p="/categories", e=200),
        dict(m="POST", p="/categories", b={"name": "Nova cat", "color": "#112233"}, e=201, save="cid", extract=lambda j: j.get("id") or (j.get("category") or {}).get("id")),
        dict(m="POST", p="/categories", b={"name": "Cor ruim", "color": "vermelho"}, e=400),
        dict(m="PUT", p="/categories/{cid}", b={"name": "Renomeada"}, e=200),
        dict(m="PUT", p="/categories/{cid}", b="", e=400),
        dict(m="DELETE", p="/categories/{cid}", e=200),
        dict(m="GET", p="/nao-existe", e=404),
    ])

if __name__ == "__main__":
    which = sys.argv[1]
    cfg = {"1": P1, "2": P2, "3": P3}[which]
    ok = run(**cfg)
    sys.exit(0 if ok else 1)
