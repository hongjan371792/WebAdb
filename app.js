document.getElementById('connect').addEventListener('click', async () => {
    try {

        const device = await navigator.usb.requestDevice({ filters: [{}] });
        console.log('發送請求讓用戶選取裝置');
        

        await device.open();
        console.log('開啟裝置')
        

        if (device.configuration === null) {
            await device.selectConfiguration(1);
        }
        console.log('設定配置')

            const info = `
                裝置名稱(USB連接名稱): ${device.productName}
                裝置製造商: ${device.manufacturerName}
                裝置序號: ${device.serialNumber}
                請注意，目前基於WebUSB限制，部分製造商的裝置名稱可能顯示不完整，敬請見諒`;
    
        const output = document.getElementById('output');
        output.textContent = info;

        await device.close();
        console.log('關閉裝置')
        
    } catch (error) {
        console.error(error);
        document.getElementById('output').textContent = `錯誤: ${error.message}`;
    }
});
