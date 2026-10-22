# 常用工具推荐 | Recommended Tools

TI 工具的版本和链接在 2026-10-22 核对，详见 [参考资料](REFERENCE_MATERIALS.md)。

## TI 开发生态

- Code Composer Studio 21.0.1（2026-08-24）：<https://www.ti.com/tool/CCSTUDIO>
- C2000Ware 26.02.00.00 LTS（2026-09-30），含 SysConfig：<https://www.ti.com/tool/C2000WARE>
- PSpice for TI：<https://www.ti.com/tool/PSPICE-FOR-TI>
- Resource Explorer：<https://dev.ti.com/tirex>
- E2E：<https://e2e.ti.com/>

2025 年有一道赛题指定 MSPM0 系列。Keil、STM32CubeIDE 只在题目允许其他 MCU 时使用。

## 原理图和仿真

- 立创 EDA 或 Altium Designer
- LTspice 是 ADI 的工具，不是 TI 工具；TI 器件优先用 PSpice for TI 里的模型

## 仪器

- 示波器
- 逻辑分析仪，用来看 RS-485 的 DE 和最后一位停止位
- 万用表；测电流时确认量程和探头位置

## 仓库里的检查命令

```bash
python tools/project_audit.py .
python tools/bom.py check templates/project-plan/bom.csv
python tools/contest_prep.py .
```

终端里 `contest_prep.py` 打文字摘要。管道、重定向或 `--format json` 时输出 JSON。
