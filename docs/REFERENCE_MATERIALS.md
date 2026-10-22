# 参考资料 | References

核对日期：2026-10-22。下面的 TI 页面当天打开过；硅器件产品页状态为 Active，开发板页面可以下单或查看资料。这不是合格供方名录，也不含价格和库存。下单前再打开数据手册，核对封装、可订购型号和勘误。

规则以当季通知为准。全国赛网站：<http://nuedc.xjtu.edu.cn/>。组委会指定的培训网：<https://www.nuedc-training.com.cn/>。2025 年全国赛时间是 2025-07-30 08:00 至 2025-08-02 20:00，题目在上述两个网站发布。

2025-04-20 的组委会通知写明：有一道赛题指定 TI MSPM0 系列处理器，具体型号不限；可以自制电路板，也可以用 LaunchPad 或其他 MSPM0 开发工具。免费板卡申请从 2025-05-06 起，流程在培训网。

## 竞赛里常见的 TI 器件

`python tools/bom.py catalog` 和 `python tools/bom.py lookup MSPM0G3507` 使用同一份摘录，代码在 `tools/ti_parts.py`。

| 型号 | 用途 | 页面上的要点 | 链接 |
| --- | --- | --- | --- |
| MSPM0G3507 | MCU | 80 MHz Cortex-M0+，128 KB Flash，32 KB SRAM，两路 12 位 4 Msps ADC，CAN-FD | <https://www.ti.com/product/MSPM0G3507> |
| LP-MSPM0G3507 | 开发板 | MSPM0G3507 LaunchPad，板载调试器 | <https://www.ti.com/tool/LP-MSPM0G3507> |
| TMS320F280039C | 实时控制 MCU | C2000，120 MHz C28x，带 FPU、TMU、CLA、CLB，384 KB Flash | <https://www.ti.com/product/TMS320F280039C> |
| LAUNCHXL-F280039C | 开发板 | F280039C LaunchPad，板载 XDS110 | <https://www.ti.com/tool/LAUNCHXL-F280039C> |
| THVD1450 | RS-485 | 3.3 V 到 5 V 半双工，空闲总线失效保护，±18 kV IEC ESD | <https://www.ti.com/product/THVD1450> |
| TLV9062 | 运放 | 双路，1.8 V 到 5.5 V，10 MHz，轨到轨 | <https://www.ti.com/product/TLV9062> |
| INA181 | 电流采样 | 26 V 双向，增益 20/50/100/200，带宽最高 350 kHz | <https://www.ti.com/product/INA181> |
| ADS1115 | 慢速 ADC | 16 位 I2C，最高 860 SPS，四路单端或两路差分 | <https://www.ti.com/product/ADS1115> |
| REF35 | 基准 | 典型 650 nA；SOT-23 在 −40 °C 到 105 °C 的最大漂移 12 ppm/°C | <https://www.ti.com/product/REF35> |
| TPS62933 | 电源 | 输入 3.8 V 到 30 V，3 A 同步降压，输出 0.8 V 到 22 V | <https://www.ti.com/product/TPS62933> |
| UCC27624 | 栅极驱动 | 双路 5 A 低边，VDD 4.5 V 到 26 V，绝对最大 30 V | <https://www.ti.com/product/UCC27624> |

UCC27524 当天仍是 Active，产品页把 UCC27624 标成更新的管脚兼容型号。新板优先核对 UCC27624。

可订购后缀（例如 `MSPM0G3507SRHBR`、`TLV9062IDR`、`REF35250`）在查找时会回到上表的基型号。后缀决定封装或具体电压档，不能靠前缀猜。

## 工具和手册入口

- Code Composer Studio 21.0.1，发布日期 2026-08-24：<https://www.ti.com/tool/CCSTUDIO>。基于 Theia，用法接近 VS Code。下载页写明不支持 Windows 32 位和 XDS510。
- C2000Ware 26.02.00.00 LTS，发布日期 2026-09-30：<https://www.ti.com/tool/C2000WARE>。LaunchPad 页面说明其中带 SysConfig。
- PSpice for TI：<https://www.ti.com/tool/PSPICE-FOR-TI>。
- Resource Explorer：<https://dev.ti.com/tirex>。MSPM0G3507 产品页把 MSP Academy 训练放在这里。
- E2E：<https://e2e.ti.com/>。

## 书籍

这些书只作课程背景，不能代替器件手册：

- 《电力电子技术》
- 《模拟电路》
- 《STM32 库开发实战指南》（题目允许非 TI MCU 时）

引用外部材料时记下标题、URL 和打开日期。不要把赛题原文或别人的解题报告放进公开仓库。
