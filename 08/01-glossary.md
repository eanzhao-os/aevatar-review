# 术语表(Glossary):对照 architecture-vocabulary.md

## 关键代码(事实源,以 ~/Code/aevatar 为准)

- `docs/canon/architecture-vocabulary.md`(128 行,active,owner eanzhao)。

---

## 核心词汇映射(第 20-31 行 §1)

| 词汇 | 在 aevatar 里指 | 行号 |
|---|---|---|
| **Module** | Actor / GAgent / `Aevatar.<Layer>.<Feature>` | 第 24 行 |
| **Interface** | Port + command/event proto + ReadModel query contract(**不只是 C# interface**) | 第 25 行 |
| **Implementation** | Actor body / Adapter internals(与 Adapter 区分) | 第 26 行 |
| **Depth** | "Actor 即业务实体" | 第 27 行 |
| **Seam** | Port(`IActorDispatchPort`/`IEventPublisher`)+ command dispatch contract | 第 28 行 |
| **Adapter** | 描述角色非实质 —— `LocalActorPublisher`/`RuntimeBackedActorRuntime`/`InMemory*` | 第 29 行 |
| **Locality** | "事实源唯一" | 第 31 行 |

---

## 易混淆词(第 33-41 行 §1.1)

| 词 | 它不是什么 | 行号 |
|---|---|---|
| **边界(boundary)** | 不是 seam;一个 actor 的边界不是 seam,**它周围的 Port 才是 seam** | 第 37 行 |
| **ReadModel** | 查询副本,不是 interface | 第 38 行 |
| **Projection Pipeline** | 物化机制,不是 adapter | 第 39 行 |
| **Service** | 必须带业务语义,优先更窄的 `IXxxQueryPort`/`IActorDispatchPort` | 第 40 行 |
| **Router** | ingress 里 = "config actor + boundary resolver"(ADR-0024) | 第 41 行 |

---

## 关键原则(第 61-101 行 §2)

- **删除测试**(第 63-72 行):能删就删
- **Interface 是测试面**(第 74-82 行)
- **一个 adapter = 假想 seam;两个 = 真 seam**(第 83-92 行)
- **深优于浅**(第 94-101 行)

---

## 使用约定(第 103-110 行 §3)

- 领域语言 vs 架构语言分开
- ADR Context 用词汇表,Decision 用领域语言
- 中文写作括注英文("接缝(seam)")
- `seam`(概念)≠ `port`(aevatar 形态)

---

## 词汇拒绝清单(第 112-119 行 §4)

不要单独使用:"boundary/边界"表可替换性(用 port/seam)、"service"作通用模块、"API"超出类型签名、"component"(UI 除外)。

---

## 参考(第 121-128 行 §5)

Mattpocock `improve-codebase-architecture/LANGUAGE.md`、Michael Feathers《Working Effectively with Legacy Code》、`overview.md`/`architecture.md`/`cqrs-projection.md`。

⟦AI:AUTO-LOOP⟧
