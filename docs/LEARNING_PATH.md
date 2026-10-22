# TI Cup 学习路径推荐 | Learning Path

规则和器件以 [参考资料](REFERENCE_MATERIALS.md) 里的核对日期为准。2025 年全国赛有一道题指定 MSPM0 系列，型号不限。

## 基础

- C 语言、数模电、示波器
- 原理图：立创 EDA 或 Altium
- MSPM0 入门用 LP-MSPM0G3507 和当前的 Code Composer Studio。Resource Explorer 里有 MSP Academy 实验

## 功率和控制

- 先把 Buck / Boost、采样、保护和硬件关断做通，再加控制算法
- 实时控制看 C2000：LAUNCHXL-F280039C 和 C2000Ware
- 运放、电流采样和基准先读 TLV9062、INA181、REF35 的手册，再决定是不是用这颗料
- PID 和状态机要有调参记录，不能只留最终一组参数

## 竞赛

- 用设计评审清单、`bom.py` 和 `contest_prep.py` 把缺口列成表
- 报告和答辩里的每个数都要能回到测试记录
- 真题和培训材料在培训网，不要把题目原文复制进公开仓库
