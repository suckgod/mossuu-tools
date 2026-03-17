# 如何生成支付宝/微信收款码

## 步骤 1: 打开支付宝/微信

### 支付宝
1. 打开支付宝 App
2. 搜索 "收钱"
3. 点击 "二维码收款"
4. 长按二维码 → 保存图片到相册

### 微信
1. 打开微信 → 我 → 服务 → 收付款
2. 点击 "二维码收款"
3. 长按二维码 → 保存图片

---

## 步骤 2: 将收款码放到项目里

```bash
# 1. 把收款码图片复制到项目根目录
cp /path/to/your/qr_code.png /Users/suck/.openclaw/workspace/projects/mossuu-tools/alipay_qr.png

# 2. 更新产品页（如果文件名不同）
# 编辑 products/python-autokit-product.md
# 找到 <qqimg> 标签，替换为你的图片路径
```

---

## 步骤 3: 设置收款金额

**建议定价**:
- 支付宝/微信: **¥145** (≈ $19.99)
- GitHub Sponsors: **$20** (平台最低 $1，但设 $20 过滤小额)

---

## 步骤 4: 创建私有 Release（一次性）

1. 打开 GitHub → 仓库 → Releases → Draft
2. Tag: `v1.0.0`
3. Upload: `autokit-v1.0.0.zip`
4. ✅ **Private** (仅赞助者可访问)
5. Publish

---

## 步骤 5: 开始销售

在 README 和产品页放上收款码，用户付款后：
1. 用户联系你（GitHub Issue 或 QQ）
2. 你查看是否到账（支付宝/微信账单）
3. 确认后，发送私有 Release 下载链接

---

## 自动化？（可选）

如果你想让 GitHub Sponsors 自动发货，可以设置 GitHub Actions webhook，但需要服务器。

当前手动方案最简单，适合起步。

---

**完成！现在你的产品可以开始卖了。** 💰
