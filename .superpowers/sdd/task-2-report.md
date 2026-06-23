# Task 2: DouZero PyTorch Model & Weights Manager 实现报告

## 1. 任务概述
本任务旨在实现 DouZero 强化学习算法的神经网络结构定义与模型权重加载逻辑。主要实现如下：
- `LandlordLstmModel`: 地主角色的网络定义（LSTM + 多层 Linear）。
- `FarmerLstmModel`: 农民（上家和下家）角色的网络定义（LSTM + 多层 Linear）。
- `DouZeroAgentManager`: 权重管理器，管理模型加载、模型推理以及当权重缺失时进行安全 fallback 的机制（`is_available() -> bool`）。

## 2. TDD 流程验证

### 步骤 1 & 2：编写失败的测试并运行
我们在 `backend/tests/test_douzero_model.py` 中编写了模型推理测试和 fallback 机制测试。
在未实现模型代码前运行测试，提示如下错误（符合预期）：
```
ImportError while importing test module 'D:\Project_2023\hmp_ws_service\backend\tests\test_douzero_model.py'.
...
E   ModuleNotFoundError: No module named 'app.domain.game.douzero_model'
```

### 步骤 3 & 4：编写最小实现并运行测试
我们在 `backend/app/domain/game/douzero_model.py` 中完成了 `LandlordLstmModel`、`FarmerLstmModel` 和 `DouZeroAgentManager` 的实现。
再次运行测试命令 `D:\ProgramData\miniconda3\envs\hmp_ai\python.exe -m pytest tests/test_douzero_model.py -v`，测试成功通过：
```
tests/test_douzero_model.py::test_model_definitions_and_inference PASSED [100%]
============================== 1 passed in 3.31s ==============================
```

## 3. Git 提交
提交了以下两个文件：
- `backend/app/domain/game/douzero_model.py`
- `backend/tests/test_douzero_model.py`

## 4. 评审发现修复与验证报告

### 4.1 修复内容
1. **测试用例增加**：在 `backend/tests/test_douzero_model.py` 中，导入并添加了对 `FarmerLstmModel` 前向传播（forward pass）的验证单元测试，传入 dummy 数据以验证网络结构。
2. **逻辑优化**：在 `backend/app/domain/game/douzero_model.py:get_action_value()` 方法中，将错误检查逻辑解耦细化：
   - 当模型未加载时，抛出 `RuntimeError("DouZero models not loaded.")`
   - 当传入无效角色且模型已加载时，抛出 `ValueError(f"Invalid role: {role}. Expected one of {list(self.models.keys())}")`
3. **新增异常验证测试**：在测试文件中添加了对上述两类异常抛出场景的验证逻辑。

### 4.2 TDD 命令与测试验证输出
我们运行了测试验证命令 `D:\ProgramData\miniconda3\envs\hmp_ai\python.exe -m pytest tests/test_douzero_model.py -v`，输出如下：
```
============================= test session starts =============================
platform win32 -- Python 3.10.20, pytest-8.0.0, pluggy-1.6.0 -- D:\ProgramData\miniconda3\envs\hmp_ai\python.exe
cachedir: .pytest_cache
rootdir: D:\Project_2023\hmp_ws_service\backend
plugins: anyio-4.13.0, langsmith-0.8.3, asyncio-0.23.5
asyncio: mode=strict
collecting ... collected 1 item

tests/test_douzero_model.py::test_model_definitions_and_inference PASSED [100%]

============================== 1 passed in 4.33s ==============================
```
