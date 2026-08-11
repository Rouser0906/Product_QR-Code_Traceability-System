# 扫码专用子域部署与对接固化

> **注意**：本文档中的域名（如 `scan.example.com`、`example.com`）仅为示例。实际部署时请替换为您自己的域名。详见 [域名配置说明](./DOMAIN_CONFIGURATION.md)。

目标：移动端"无感秒开"，统一二维码链接至 https://your-scan-domain.com/q/{token}，边缘解析全部信息并无缝跳转官网。

## 1. Token 策略（最优稳定短码）
- 采用独立短码，避免直接暴露全部信息。
- 规则：token = Base62(sha256(qr_sequence)) 前 8 位（稳定可重算，足够短且碰撞概率低）。
- 示例 Python 生成函数（供现有系统集成）：
```python
import hashlib
import string
ALPHABET = string.digits + string.ascii_letters  # 0-9a-zA-Z

def to_base62(b: bytes) -> str:
    n = int.from_bytes(b, 'big')
    if n == 0: return '0'
    out = []
    while n > 0:
        n, r = divmod(n, 62)
        out.append(ALPHABET[r])
    return ''.join(reversed(out))

def make_token(qr_sequence: str) -> str:
    h = hashlib.sha256(qr_sequence.encode('utf-8')).digest()
    b62 = to_base62(h)
    return b62[:8]
```

## 2. 统一链接规范
- 二维码链接：`https://scan.example.com/q/{token}`
- 历史兼容：保留 `/qr/?id={QRC_No}` → `/q/{token}` 301 重定向（可在边缘或入口 Nginx 中设置）。

## 3. 边缘逻辑（Cloudflare Workers + KV）
- 代码位置：`cloud/scan-worker/worker.js`
- 配置位置：`cloud/scan-worker/wrangler.toml`
- 路由：
  - GET `/q/{token}`：首屏 HTML（无框架），客户端拉取 `/api/resolve?id=token`
  - GET `/api/resolve`：KV 命中优先；miss 时回源主域 `https://example.com/api/resolve?id=token`，返回后写入 KV（提升后续命中与秒开率）
- KV 命名：`QRMAP`（生产命名 `qrmap_prod`）
- 环境变量：`ORIGIN_API=https://example.com/api/resolve`

## 4. 极简首屏（移动端）
- 文件：`qr_public_files/scan/index.html`（与 Workers 中内置 HTML 等效）
- 特点：内联关键 CSS，无第三方框架；渲染后“访问官网”一键无缝跳转。

## 5. 安全与性能
- HTTPS 强制、HSTS、HTTP/3、TLS1.3
- 安全头：CSP、X-Content-Type-Options、Referrer-Policy
- 缓存策略：
  - `/api/resolve` 命中 KV：`Cache-Control: public, max-age=3600`
  - 回源返回：`Cache-Control: public, max-age=600`，并写入 KV（TTL 1 天）

## 6. 后端接口约定
- 主域回源：`GET https://example.com/api/resolve?id={token}`
- 返回 JSON 示例：
```json
{
  "qrcNo":"HS-DEMO-123456",
  "qrSequence":"HS-DEMO-123456",
  "companyName":"XX公司",
  "productType":"XPS",
  "productSpec":"A1-30mm",
  "productColor":"白色",
  "productFeature":"高阻燃",
  "batchNumber":"B202409",
  "productionDate":"2025-09-20",
  "distributorName":"某经销商",
  "phone":"1234567890",
  "standard":"GB/T ****",
  "remark":"",
  "companyUrl":"https://example.com"
}
```

## 7. 全自动部署步骤（PowerShell）
> 需要已安装 Node.js 与 Cloudflare Wrangler（`npm i -g wrangler`），以及添加 DNS 记录与证书（Cloudflare 或自有证书）。
```powershell
# 1) 进入目录
Set-Location (Resolve-Path "cloud/scan-worker")

# 2) 登录 Cloudflare（按提示进行一次性授权）
wrangler login

# 3) 创建 KV 命名空间（若未创建）
wrangler kv:namespace create QRMAP --binding=QRMAP

# 4) 发布 Workers
wrangler publish

# 5) DNS 路由
# 在 Cloudflare 控制台将 scan.example.com 绑定到该 Worker（wrangler routes 已声明）
# 确保启用 HTTPS、HTTP/3、TLS1.3 与 HSTS

# 6) 验证
# 浏览器访问 https://scan.example.com/q/TEST1234
# 边缘将调用 /api/resolve?id=TEST1234 并按约定渲染数据
```

## 8. Nginx 入口（可选，自建边缘或反代）
```nginx
server {
  server_name scan.example.com;
  listen 443 ssl http2;

  add_header Strict-Transport-Security "max-age=31536000" always;
  add_header X-Content-Type-Options nosniff always;
  add_header Referrer-Policy no-referrer-when-downgrade always;

  location /q/ {
    root /var/www/scan;
    try_files $uri /q/index.html;
  }
  location /api/resolve {
    proxy_pass https://example.com/api/resolve;
    proxy_set_header Host example.com;
    add_header Cache-Control "public, max-age=3600";
  }
}
```

## 9. 系统内对接（生成二维码）
- 将当前二维码生成逻辑统一至 `https://scan.example.com/q/{token}`
- token 由 `make_token(qr_sequence)` 生成（如需“彻底不可逆短码”，可改用随机短码并入库映射）
- 历史二维码兼容：在入口将 `?id={QRC_No}` 301 至 `/q/{token}`（保持历史可用）

## 10. 合并到 share.md
- 本文件为固化补充；如需，我可将本章节精确合并进 `docs/share.md`（避免覆盖原内容），并在权限/需求章节中新增“扫码专用子域上线”条目。

---
完成后，所有地区的移动端扫码将通过 `scan.example.com` 边缘就近解析与渲染，实现“无感秒开”与“官网一键无缝跳转”。