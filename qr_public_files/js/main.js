window.onload = function() {
    const urlParams = new URLSearchParams(window.location.search);
    const productCode = urlParams.get('code') || urlParams.get('id');
    const infoListContainer = document.getElementById('info-list');

    if (!productCode) {
        infoListContainer.innerHTML = '<p class="error">错误：无效的二维码，缺少产品信息码。</p>';
        return;
    }

    // 使用统一的API接口获取产品数据
// 注意：将包含 URL 的字段（如 official_website、verification_url）渲染为可点击链接，移动端无感秒开
    const apiUrl = `/api/get_product_data.php?code=${encodeURIComponent(productCode)}`;

    fetch(apiUrl, {
        method: 'GET',
        headers: {
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }
    })
        .then(response => {
            if (!response.ok) {
                throw new Error('产品信息不存在或查询失败。');
            }
            return response.json();
        })
        .then(data => {
            // 清空加载提示
            infoListContainer.innerHTML = '';

            // 这是一个帮助函数，用于创建一行信息
            const createInfoItem = (label, value, isLink = false, linkHref = '#') => {
                const item = document.createElement('div');
                item.className = 'info-item';
                
                const labelSpan = document.createElement('span');
                labelSpan.className = 'label';
                labelSpan.textContent = label;
                
                const valueSpan = document.createElement('span');
                valueSpan.className = 'value';

                if (isLink) {
                    const link = document.createElement('a');
                    link.href = linkHref;
                    link.textContent = value;
                    link.target = '_blank';
                    link.rel = 'noopener';
                    valueSpan.appendChild(link);
                } else {
                    valueSpan.textContent = value;
                }
                
                item.appendChild(labelSpan);
                item.appendChild(valueSpan);
                infoListContainer.appendChild(item);
            };
            
            // 根据截图和JSON数据，填充页面信息
            document.getElementById('header-company-name').textContent = data.company_name;

            createInfoItem('公司名称', data.company_name || '--');
            createInfoItem('产品类型', data.product_type || '--');
            createInfoItem('产品规格', data.product_spec || '--');
            createInfoItem('产品颜色', data.product_color || '--');
            createInfoItem('功能特性', data.product_feature || '--');
            createInfoItem('批次号', data.batch_number || '--');
            createInfoItem('生产日期', data.production_date || '--');
            createInfoItem('销售单位', data.distributor_name || '--');
            createInfoItem('发行人', data.issuer_name || '--');
            createInfoItem('经销商', data.distributor_name || '--');
            createInfoItem('物流车牌', data.plate_number || '--');
            createInfoItem('联系电话', data.phone || '--', true, `tel:${data.phone}`);
            createInfoItem('官网', data.official_website || '--', true, data.official_website);
            
            // 更新“进入官网”按钮的链接
            document.getElementById('official-website-btn').href = data.official_website || '#';

            // 可点击的验证链接（如果存在）
            if (data.verification_url) {
                createInfoItem('验证链接', data.verification_url, true, data.verification_url);
            }

            // 更新页脚的公司名称
            document.getElementById('footer-company-name').textContent = data.company_name;

        })
        .catch(error => {
            console.error('加载产品信息失败:', error);
            infoListContainer.innerHTML = `<p class="error">查询产品信息失败。请检查网络或确认二维码是否有效。</p>`;
        });
};