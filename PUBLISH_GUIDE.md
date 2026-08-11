# 项目发布指南

本指南将帮助您安全地将项目发布到 Atlassian 或其他公开平台。

## 📋 发布前准备

### 1. 了解已清理的内容

本项目已经进行了敏感信息清理，详情请查看：
- **[CLEANUP_SUMMARY.md](./CLEANUP_SUMMARY.md)** - 查看已清理的敏感信息列表
- **[SECURITY_SETUP.md](./SECURITY_SETUP.md)** - 了解部署时如何配置

### 2. 重要文件说明

#### 已清理的配置文件
以下配置文件已被清理，只保留了示例模板：
- `config/ftp_config.json` → `config/ftp_config.json.example`
- `auto_sync/config.json` → `auto_sync/config.json.example`
- `auto_sync/enhanced_config.json` → `auto_sync/enhanced_config.json.example`
- `api/db_config.php` → `api/db_config.php.example`
- `api/api_config.php` → `api/api_config.php.example`

#### 文档文件
- `README.md` - 项目主文档
- `SECURITY_SETUP.md` - 安全配置指南
- `PRE_PUBLISH_CHECKLIST.md` - 发布前检查清单
- `PUBLISH_GUIDE.md` (本文件) - 发布指南

## 🚀 快速发布流程

### 方法一：使用自动化脚本（推荐）

1. **模拟运行（查看将要删除什么）**
   ```powershell
   .\cleanup_for_publish.ps1 -DryRun
   ```
   或
   ```cmd
   cleanup_for_publish.bat --dry-run
   ```

2. **执行清理**
   ```powershell
   .\cleanup_for_publish.ps1
   ```
   或
   ```cmd
   cleanup_for_publish.bat
   ```

3. **检查结果**
   ```bash
   git status
   ```
   确认没有敏感文件将被提交

4. **提交并推送**
   ```bash
   git add .
   git commit -m "清理敏感信息，准备发布"
   git push origin main
   ```

### 方法二：手动清理

如果您想手动控制清理过程，请按照 **[PRE_PUBLISH_CHECKLIST.md](./PRE_PUBLISH_CHECKLIST.md)** 中的步骤逐项完成。

## 📤 发布到 Atlassian

### 步骤 1: 创建 Atlassian 仓库

1. 登录到 Atlassian/Bitbucket
2. 创建新的仓库
3. 选择私有或公开（建议私有）
4. 复制仓库URL

### 步骤 2: 添加远程仓库

```bash
# 添加 Atlassian 远程仓库
git remote add atlassian <your-atlassian-repo-url>

# 验证远程仓库
git remote -v
```

### 步骤 3: 推送代码

```bash
# 推送到 Atlassian
git push atlassian main

# 或推送所有分支
git push atlassian --all
```

### 步骤 4: 在 Atlassian 上配置

1. **设置仓库访问权限**
   - 如果是团队项目，添加团队成员
   - 配置适当的读写权限

2. **配置分支保护**
   - 保护 main 分支
   - 要求代码审查

3. **添加仓库描述**
   - 从 README.md 中复制项目简介
   - 添加标签便于搜索

4. **配置 Webhooks（可选）**
   - 集成 CI/CD
   - 集成通知系统

## 🔒 安全检查

### 发布前最终检查

运行以下命令进行安全检查：

```powershell
# 检查是否有数据库文件
Get-ChildItem -Recurse -Filter "*.db" | Select-Object FullName

# 检查是否有配置文件（应该只有 .example 文件）
Get-ChildItem -Recurse -Include *config.json,*config.php | Select-Object FullName

# 检查是否有大文件（可能包含数据）
Get-ChildItem -Recurse -File | Where-Object {$_.Length -gt 10MB} | Select-Object FullName, @{N="SizeMB";E={[math]::Round($_.Length/1MB,2)}}

# 搜索可能的密码（应该只有示例和注释）
Get-ChildItem -Recurse -Include *.py,*.php,*.json -File | Select-String -Pattern "password\s*[:=]\s*['\"][^'\"]{8,}['\"]" | Select-Object Path, LineNumber, Line
```

### 发布后验证

1. **在新环境克隆仓库**
   ```bash
   git clone <your-atlassian-repo-url> test-clone
   cd test-clone
   ```

2. **检查敏感信息**
   - 查看配置文件是否都是示例文件
   - 确认数据库文件不存在
   - 验证文档中没有真实凭据

3. **测试配置流程**
   - 按照 SECURITY_SETUP.md 配置
   - 验证系统能否正常启动

## 📝 维护发布仓库

### 持续集成

创建 `.gitattributes` 文件防止换行符问题：
```
* text=auto
*.py text eol=lf
*.sh text eol=lf
*.bat text eol=crlf
*.ps1 text eol=crlf
```

### 定期审计

定期检查仓库中是否有新的敏感信息：

```bash
# 每次发布前运行
git log --all --full-history --pretty=format:"%H" | xargs -I {} git grep -i "password\|secret\|key" {}
```

### 版本标签

为发布版本打标签：

```bash
# 创建标签
git tag -a v1.0.0 -m "首次公开发布"

# 推送标签
git push atlassian v1.0.0
```

## ⚠️ 常见问题

### Q: 意外提交了敏感信息怎么办？

**立即行动：**
1. 更改所有泄露的密码和密钥
2. 从Git历史中删除敏感信息（使用 `git filter-branch` 或 BFG Repo-Cleaner）
3. 强制推送清理后的历史
4. 通知所有协作者

详见 PRE_PUBLISH_CHECKLIST.md 的相关部分。

### Q: 如何更新已发布的仓库？

```bash
# 在本地开发
git add .
git commit -m "更新功能"

# 清理检查（如果有新的敏感信息）
.\cleanup_for_publish.ps1 -DryRun

# 推送到 Atlassian
git push atlassian main
```

### Q: 可以同时推送到多个远程仓库吗？

可以，配置多个远程仓库：

```bash
# 添加GitHub
git remote add github <github-repo-url>

# 添加Atlassian
git remote add atlassian <atlassian-repo-url>

# 推送到所有仓库
git push github main
git push atlassian main

# 或创建一个推送到所有远程的别名
git remote add all <primary-repo-url>
git remote set-url --add --push all <github-repo-url>
git remote set-url --add --push all <atlassian-repo-url>
git push all main
```

### Q: 如何回滚到之前的版本？

```bash
# 查看提交历史
git log --oneline

# 回滚到特定提交
git reset --hard <commit-hash>

# 强制推送（谨慎使用）
git push atlassian main --force
```

## 📚 相关文档

- [README.md](./README.md) - 项目介绍和快速开始
- [SECURITY_SETUP.md](./SECURITY_SETUP.md) - 安全配置详解
- [CLEANUP_SUMMARY.md](./CLEANUP_SUMMARY.md) - 清理内容总结
- [PRE_PUBLISH_CHECKLIST.md](./PRE_PUBLISH_CHECKLIST.md) - 发布前检查清单
- [docs/DOMAIN_CONFIGURATION.md](./docs/DOMAIN_CONFIGURATION.md) - 域名配置说明

## 🆘 获取帮助

如果在发布过程中遇到问题：

1. 查看相关文档
2. 检查错误日志
3. 在 Issues 中搜索类似问题
4. 创建新的 Issue 描述问题

---

**祝发布顺利！** 🎉

如有任何问题，请参考上述文档或联系项目维护者。
