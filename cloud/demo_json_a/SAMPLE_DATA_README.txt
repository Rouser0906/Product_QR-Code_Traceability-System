# 示例数据目录

此目录用于存放公司产品的JSON数据文件。

## 文件格式
真实的JSON文件应该包含产品信息，格式类似：
```json
{
  "qr_code": "XX-Q000000001",
  "product_name": "产品名称",
  "company_name": "公司名称",
  "official_website": "https://www.your-company-domain.com"
}
```

## 注意事项
- 请将实际的JSON数据文件放在此目录
- 这些文件已添加到.gitignore，不会被提交到版本控制
- 敏感数据请妥善保管，不要公开发布
