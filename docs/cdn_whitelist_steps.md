# CDN/防火墙 加白 10.0.0.200 操作清单

## 1. 确认服务商
- 登录域名解析处（如 Cloudflare、阿里云、腾讯云、华为云、AWS CloudFront）。
- 找到对应域名 `scan.example.com` 的 CDN/WAF 控制台。

## 2. 云厂商通用步骤
### Cloudflare
1. 进入 **Security → WAF → Tools → IP Access Rules**
2. Action 选 **Allow**，IP 填 `10.0.0.200`，Notes 填 `example-sync-bot`
3. Save

### 阿里云 CDN + WAF
1. **Web 应用防火墙 → 访问控制/白名单 → 新建规则**
2. 规则类型：IP 白名单，填写 `10.0.0.200/32`
3. 选择对应域名 `scan.example.com` → 立即启用

### 腾讯云 CDN
1. **EdgeOne / CDN → 安全防护 → IP 黑白名单**
2. 添加 `10.0.0.200`，类型选 **白名单**，绑定域名后提交

### 华为云 CDN
1. **CDN → 域名管理 → 访问控制 → IP 黑白名单**
2. 新增白名单 `10.0.0.200`，保存

### AWS CloudFront + WAF
1. **WAF → IP sets → Create IP set** (CIDR: 10.0.0.200/32)
2. **Rules → Add Rule → Allow** 并引用刚建的 IP set
3. 关联到 CloudFront Distribution，优先级置顶，更新

## 3. 本地防火墙（若有）
- Windows 防火墙：添加入站规则 → 远程 IP `10.0.0.200` → 允许 443
- Linux iptables：`iptables -I INPUT -s 10.0.0.200/32 -p tcp --dport 443 -j ACCEPT`

## 4. 验证
PowerShell 执行：
```powershell
Invoke-WebRequest https://scan.example.com/qr/index.html?code=HS-DEMO-000000001 -UseBasicParsing
```
返回 200 即成功。

## 5. 回滚
若误加，按同样路径删除对应白名单记录即可。