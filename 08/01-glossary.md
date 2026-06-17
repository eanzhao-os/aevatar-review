# 术语表(Glossary):对照 architecture-vocabulary.md

## 本篇涉及的设计抽象

> 以下论断均可回指 `~/Code/aevatar` 源码验证,但本篇用设计语言描述,不贴文件路径/行号。

---

## 核心词汇映射(§1)

| 词汇 | 在 aevatar 里指 | 行号 |
|---|---|---|
| **Module** | Actor / GAgent / `Aevatar.<Layer>.<Feature>` | |
| **Interface** | Port + command/event proto + ReadModel query contract(**不只是 C# interface**) | |
| **Implementation** | Actor body / Adapter internals(与 Adapter 区分) | |
| **Depth** | "Actor 即业务实体" | |
| **Seam** | Port(`IActorDispatchPort`/`IEventPublisher`)+ command dispatch contract | |
| **Adapter** | 描述角色非实质 —— `LocalActorPublisher`/`RuntimeBackedActorRuntime`/`InMemory*` | |
| **Locality** | "事实源唯一" | |

---

## 易混淆词(§1.1)

| 词 | 它不是什么 | 行号 |
|---|---|---|
| **边界(boundary)** | 不是 seam;一个 actor 的边界不是 seam,**它周围的 Port 才是 seam** | |
| **ReadModel** | 查询副本,不是 interface | |
| **Projection Pipeline** | 物化机制,不是 adapter | |
| **Service** | 必须带业务语义,优先更窄的 `IXxxQueryPort`/`IActorDispatchPort` | |
| **Router** | ingress 里 = "config actor + boundary resolver"(ADR-0024) | |

---

## 关键原则(§2)

- **删除测试**():能删就删
- **Interface 是测试面**()
- **一个 adapter = 假想 seam;两个 = 真 seam**()
- **深优于浅**()

---

## 使用约定(§3)

- 领域语言 vs 架构语言分开
- ADR Context 用词汇表,Decision 用领域语言
- 中文写作括注英文("接缝(seam)")
- `seam`(概念)≠ `port`(aevatar 形态)

---

## 词汇拒绝清单(§4)

不要单独使用:"boundary/边界"表可替换性(用 port/seam)、"service"作通用模块、"API"超出类型签名、"component"(UI 除外)。

---

## 参考(§5)

Mattpocock `improve-codebase-architecture/LANGUAGE.md`、Michael Feathers《Working Effectively with Legacy Code》、`overview.md`/`architecture.md`/`cqrs-projection.md`。

⟦AI:AUTO-LOOP⟧
