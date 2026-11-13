# 03 · sah...（卅语言）编译器主体 — 文件级索引

> 范围：`E:/文件/编程文件/agent/sahou/` 顶层 + `internal/**` + `cmd/**` + `tests/**`。
> 级别：very thorough（每一文件均真实通读）。共索引 **78 条**（其中 `tests/cases` 24 条各自涵盖 `.saho` + `.out/.err` 快照），实际读取 **102 个**在范围内文件。
> 语言后缀 `.saho`，工具链纯 Go（唯一第三方依赖 go-webview2，仅 Windows 原生窗口使用）。

---

## 一、编译 / 执行链路（`main.go` 驱动顺序）

`main.go` 的 `main()` 按 `os.Args[0]` 分派子命令，所有路径共享同一套前端 `lexer → parser`：

```
os.Args
  │
  ├─ 无参数                         → repl()                 （交互环境）
  ├─ run <f.saho> [args]            → compileFile(path) → runFile()
  │         └─ encodesrc.ReadFile → lexer.Tokenize → parser.Parse
  │               └─ interp.New() → in.Run(prog)            （树遍历求值）
  ├─ tokens <f.saho> / ast <f.saho> → dump(cmd, path)
  │         └─ lexer.Tokenize（tokens 模式直接打印记号）
  │            → parser.Parse → dumpProgram()（ast 模式，见 ast.go）
  ├─ build <f.saho> -o <out.js>     → buildJS()
  │         └─ encodesrc.ReadFile → lexer.Tokenize → parser.Parse
  │            → transpile.Build(prog, filepath.Dir(inPath)) → 写 JS
  ├─ 打包|pack <f.saho> -o <exe>    → packApp()
  │         └─ 生成临时 Go 工程（内嵌 .saho），复制 internal/ + cmd/ + stones/
  │            → 临时工程里 lexer→parser→interp.New→in.Run（生成独立的 main.go）
  │            → exec go mod tidy / go build
  ├─ 格式|fmt <f.saho>              → formatFile()
  │         └─ encodesrc.ReadFile → format.Source（仅重排缩进，不解析 AST）→ 就地写回
  ├─ lsp                            → lsp.SharedJSON = sharedLangJSON（go:embed）
  │                                   → lsp.Run()（stdio JSON-RPC）
  │         诊断：lexer.Tokenize + parser.Parse；补全/悬停：调用 interp 的
  │         CompletionMembers / CompletionStoneMembers / CompletionWords
  ├─ serve [dir] [addr]             → serveDir()（静态服务 + 内嵌 wasm 运行时兜底 + .saho 壳页）
  ├─ 装|install / stones|库 / 导出运行时|export_runtime / version|版本 / help
  └─ 默认：以 `.saho` 结尾则 runFile(cmd, rest)
```

**关键顺序结论**
1. **前端唯一化**：`lexer.Tokenize → parser.Parse` 是所有执行/转译/诊断路径的共同入口；`format` 是唯一不解析 AST 的路径（纯行级缩进重排）。
2. **运行 = 解释**：`run`/REPL/`打包`/`sahou.wasm` 都走 `interp.New() → in.Run(prog)`（树遍历 + `panic/recover` 做非局部跳转）。
3. **build = 转译**：`build` 走 `transpile.Build`，**不 import interp**（分层铁律），JS 侧用 `internal/transpile/rt.js` 运行时。
4. **lsp = 复用前端 + 复用 interp 元数据**：诊断用 lexer/parser，补全/悬停用 `interp.Completion*` 与 `editors/shared/language.json`（`//go:embed` 注入 `lsp.SharedJSON`）。
5. **REPL 续行**：`repl()` 用 `isIncomplete(e)` 判断"输入没写完"（错误文案包含"缺少 完毕/程序在这里就结束了"等），继续累积输入。

---

## 二、`internal/interp/` 内各 `*mod.go` 职责分工

所有模块在 `interp.New()` 里经 `registerNetModule(in)` 统一注册（`netmod.go` 里级联调用其余注册函数）：

| 文件 | 模块名（中/英） | 职责 | 注册入口 |
|---|---|---|---|
| `stdmod.go` | 随机/random、时间/time、数学/math、编码/encoding、系统/sys | 预置标准库；数值一律走 `ratToFloat/floatToRat` 与 15 位有效数字圆整；提供 `modBuilder`、`mergeModuleNamed` 等模块构造基础设施 | `registerStdModules` |
| `netmod.go` | 网络/net | HTTP 服务端（`Server`：路由/参数路由/静态/会话/上传/Cookie/表单）+ HTTP 客户端 + JSON 编解码 + 快捷回应；并作为**总注册器**级联注册 page/html/db/app/test | `registerNetModule` |
| `htmlmod.go` | 网页/html | 服务端模板渲染：`[[键]]` 转义取值、`[[[键]]]` 原样、`渲染文件`、`页面` HTML 骨架、`转义` | `registerHTMLModule` |
| `dbmod.go` | 数据库/db | 纯 Go 嵌入式 SQL（中英双语关键词）+ 单文件 JSON 原子落盘；SQL 记号器/递归下降分析器/执行引擎；`Database` 成员 执行/查询/表/关闭 | `registerDBModule` |
| `appmod.go` | 应用/app | 桌面（`窗口`/`原生窗口`）+ 手机端（`手机`，0.0.0.0 局域网）+ `打开` 浏览器 + `写页面`（转发 `uiNewPage`） | `registerAppModule` |
| `uimod.go` | （由 `应用.写页面` 暴露，无独立模块字典） | 纯代码 GUI：`UIPage`/`UIWidget` + HTML/CSS/JS 生成 + 事件派发/镜像同步；通过 `uiWebView` 窄接口跨平台 | 由 appmod 的 `写页面` 调用 |
| `pagemod_js.go` | 页面/page | **浏览器宿主版**（build tag `js && wasm`）：经 `syscall/js` 操作 DOM；`绑输入`/`绑定` 接 v4 响应式 | `registerPageModule` |
| `pagemod_std.go` | 页面/page | **服务端/其它宿主版**（build tag `!js || !wasm`）：所有成员调用即返回"只能在浏览器里用"的双语提示 | `registerPageModule` |
| `testmod.go` | 测试/assert | 用户程序单元测试：`相等`/`为真`/`汇总`/`清零` | `registerTestModule` |

### `pagemod_js.go` 与 `pagemod_std.go` 的构建标签差异
- `pagemod_js.go`：`//go:build js && wasm` —— 仅当 `GOOS=js GOARCH=wasm` 编译 `cmd/sahouwasm` 时才参与构建。导入 `syscall/js`，用 `pageEl{js.Value}` 包装 DOM 元素，实现 `取元素/置文本/点击/绑输入/绑定` 等。
- `pagemod_std.go`：`//go:build !js || !wasm` —— 除 `js && wasm` 外的**全部宿主**（Windows/Linux/macOS 本地解释器）编译。把 16 个成员名为同一份"报错函数"，运行到此即提示"改用 网络 模块 / 交给 sahou.wasm"。
- 两者提供**同名函数 `registerPageModule`**，编译器按标签二选一，调用方（`netmod.go` 的 `registerNetModule`）无需感知平台。
- 注意：`pageEl` 仅在 `pagemod_js.go` 定义，但 `value.go` 的 `TypeName/TypeEnName/writeValue` 通过接口 `interface{ isPageEl() }` 泛化识别元素句柄（`pagemod_js.go` 里 `(*pageEl).isPageEl()`），因此**不受构建标签影响**。

---

## 三、`tests/` 各脚本验证内容 + `cases/` 的 `0xx` 与 `9xx` 区别

### 各 shell 脚本

| 脚本 | 验证内容 |
|---|---|
| `run.sh` | **核心一致性**：遍历 `tests/cases/*.saho`，与同名 `.out` 快照逐字比较；`.err` 用例校验退出码 + 错误子串。输出 `通过 X / N`。 |
| `run_all.sh` | **全量回归总闸**：依次跑 `run build modules stdlib packages pack net fullstack app`（不含 wasm），随后 `gofmt -l main.go internal cmd` 与 `go test ./internal/...`。 |
| `build.sh` | **转译器一致性**：核心用例 `sahou build` 后交 Node 运行，输出与解释器逐字对齐；再用 `tests/domstub.mjs` DOM 桩验证 `examples/计数器.saho` 的点击交互（`COUNTER_OK`）。 |
| `modules.sh` | **模块系统**：用户模块引入、循环引入报错、模块顶层 `返回` 报错、缺模块报错、转译打包用户模块、`装` stones 流程、`页面` 模块转译。 |
| `stdlib.sh` | **标准库模块**（随机/时间/数学/编码/系统）：解释器 + 转译双侧对齐；错误路径（挑空列表、对数 0、非法解码、负数非整数次幂）；`系统.参数` 与 `系统.退出` 退出码。 |
| `packages.sh` | **stones 标准库包**：子目录向上查找（`examples/pkgdemo`）、转译对齐、`装` 单文件/目录包、模块隔离、包级循环引入；覆盖统计/算术/文本/游戏/中文数字/…/算法等。 |
| `wasm.sh` | **WASM 直跑**：同步 `stones/` 进 `cmd/sahouwasm/stones/`，`GOOS=js GOARCH=wasm` 构建 `sahou.wasm`，跑 `wasm_reactive.mjs`（格子联动）与 `playground_check.mjs`（`__sahou_run` + 内嵌 stones）。 |
| `net.sh` | **网络模块**：起 `examples/待办服务.saho` → curl 增删查 + 404 + 客户端 `网络.请求/自文本`。 |
| `fullstack.sh` | **全栈端到端**：数据库（建表/多行插入/更新/删行/重开）+ 网页渲染转义 + 留言板（表单/会话 Cookie/入库/回显）。 |
| `app.sh` | **应用与后端写法**：路径参数路由、`JSON回应/网页回应/重定向/渲染文件`、桌面 `窗口` 静默静态服务、`手机` 局域网服务。 |
| `pack.sh` | **打包与自带库**：`stones` 列内嵌包、`装 <内置包>`、`打包` 生成的 exe 自带 stones 运行、`serve` 内嵌 wasm 兜底 + `.saho` 壳页 + 别名 `卅.wasm` + 缺页 404。 |

辅助（非 shell）：`domstub.mjs`（`build.sh` 的 DOM 桩）、`domstub.js`（同名 CJS 版）、`wasm_reactive.mjs`、`playground_check.mjs`。

### `cases/` 的 `0xx` 与 `9xx` 区别
- **`0xx` = 正向（正常）用例**：配对文件是同名 `.out`（期望标准输出快照）。`run.sh` 用 `sahou run case.saho 2>/dev/null` 与 `.out` 逐字比较。覆盖数字/文本/列表字典/控制流/函数/错误捕获/内置函数/全角/分号与全角引号/闭包作用域/管道/全角箭头/写页面/多行字典/内置遮蔽/默认参数/格子。
- **`9xx` = 负向（报错）用例**：配对文件是同名 `.err`（**第一行是期望退出码，第二行起是输出应包含的子串**，见 `run.sh` 第 24–41 行）。`9xx` 覆盖：未定义变量(900)、缺 `完毕`(901)、比较连写(902)、`文本+数` 类型错(903)、字典键拼写建议(904)、负下标(905)、给内置函数名赋值(906)。
- 二者命名不重叠：`0xx` 走"快照 diff"分支，`9xx` 走"退出码 + 子串"分支。

---

## 四、平台相关文件的降级策略

| 文件 | 构建标签 | 生效平台 | 降级/替代行为 |
|---|---|---|---|
| `nativewin_windows.go` | `//go:build windows` | Windows | 真·WebView2 原生窗口（`github.com/jchv/go-webview2`，无 CGO）；`runNativeWindow` 阻塞到关窗。 |
| `nativewin_other.go` | `//go:build !windows` | 非 Windows | `runNativeWindow` 改开系统默认浏览器并 `select{}` 阻塞；`runNativePage` 起本机临时 HTTP + **SSE 下行(/流) + POST 上行(/事件、/同步) + sendBeacon(/关闭)** 事件桥，用 `funcWebView` 把 JS 命令经 SSE 推给浏览器。 |
| `pagemod_js.go` | `//go:build js && wasm` | 浏览器（sahou.wasm） | 真 DOM（`syscall/js`）。 |
| `pagemod_std.go` | `//go:build !js || !wasm` | 本地解释器 | `页面` 模块全部成员退化为双语提示函数（不报编译错，调用时才提示）。 |
| `cmd/sahouwasm/main.go`、`stones.go` | `//go:build js && wasm` | 浏览器 | 仅 wasm 目标参与构建；`stones.go` 把 `cmd/sahouwasm/stones/`（由 `wasm.sh` 从仓库根同步）embed 注入 `stonesrc.FS`。 |

平台无关的**接口层**：`uimod.go` 定义 `uiWebView`（仅 `Eval(js string)`）与 `uiWindowSpec`，把平台差异挡在 `nativewin_*.go` 之后；`value.go` 用接口 `interface{ isPageEl() }` 识别元素句柄。

---

# 逐文件索引

## 顶层（仓库根 `sahou/`）

### sahou/main.go
- **用途**：卅命令行入口，解析子命令并驱动 lexer → parser → interp / transpile / lsp / format / 打包 / stones 管理 / 静态服务。
- **关键内容**：
  - `const version = "v1.0.0"`（与 CHANGELOG 同步）
  - `var sharedLangJSON string`（`//go:embed editors/shared/language.json`）
  - `func main()`；`func usage()`；`func flagValue(args []string, flag string) string`
  - `func buildJS(inPath, outPath string)`：读源→Tokenize→Parse→`transpile.Build`→写 JS
  - `func packApp(scriptPath, outPath string)`：生成临时 Go 工程（内嵌脚本 + 复制 internal/cmd/stones + 生成 go.mod）→ `go mod tidy` / `go build`
  - `func exportRuntime(args []string)`；`func stonesHasPackages(root string) bool`；`func findRepoRoot() string`
  - `func formatFile(path string)`：`format.Source` 就地保存
  - `type compiler struct{ prog *parser.Program }`；`func compileFile(path string) (*compiler, *errs.Error)`
  - `func runFile(path string, extraArgs []string)`：`interp.New` + 缓冲输出 + `Input` 注入 + `in.Run`
  - `func periodicFlush(w *bufio.Writer) func()`（50ms 定时冲刷）；`func chainOf(in *interp.Interp) []errs.Frame`
  - `func dump(cmd, path string)`；`func repl()`；`func isIncomplete(e *errs.Error) bool`
  - `func stonesInstall(args []string)`；`func installEmbeddedStone(name string)`；`func stoneDesc(name string) string`；`func listStones()`；`func installRemoteZip(url string)`；`func copyDir(src, dst string) error`；`func stonesYMLPackages() map[string]string`；`func addStonesYML(name string)`；`func verifyStones()`
  - `func serveDir(args []string)`（内嵌 wasm 兜底 + `.saho` 壳页）；`func looksLikeAddr(s string) bool`；`func htmlEscapeText(s string) string`
- **对外接口**：`package main`，无导出符号。
- **依赖**：`encodesrc`、`errs`、`format`、`interp`、`lexer`、`lsp`、`parser`、`stonesrc`、`transpile`（+ 标准库 archive/zip、net/http 等）。
- **被依赖**：无（进程入口）。`packApp` 内嵌的生成版 `main.go` 文本引用 `errs/interp/lexer/parser`。
- **影响范围**：全部 CLI 子命令、REPL、打包产物、serve 页壳；改动会波及所有 shell 测试。
- **备注**：`go build -o sahou.exe .` 需 `sahou.wasm` 与 `wasm_exec.js` 已存在（`stonesfs.go` 的 `//go:embed`）。发行版单文件内嵌 stones 与 wasm 运行时。

### sahou/ast.go
- **用途**：以缩进文本打印 AST（`sahou ast` 调试命令）。
- **关键内容**：`func dumpProgram(prog *parser.Program)`；`func ind(n int) string`；`func dumpStmt(s parser.Stmt, d int)`（分派 Let/Expr/If/While/For/Fn/Return/Try）；`func dumpExpr(e parser.Expr, d int)`（Num/Bool/Null/Str/Ident/List/Dict/Bin/Un/Not/Index/Member/Call/AnonFn）。
- **对外接口**：无导出符号。
- **依赖**：`parser`。
- **被依赖**：`main.go` 的 `dump()`。
- **影响范围**：仅 `sahou ast` 输出格式。
- **备注**：文件名易误认为 AST 定义，实际 AST 定义在 `internal/parser/parser.go`。

### sahou/stonesfs.go
- **用途**：把 `stones/` 与 wasm 运行时（`wasm_exec.js`、`sahou.wasm`）embed 进可执行文件，并在 `init` 注入 `stonesrc.FS`。
- **关键内容**：`//go:embed stones` → `var stonesDir embed.FS`；`//go:embed wasm_exec.js sahou.wasm` → `var wasmRuntime embed.FS`；`func init()`（`fs.Sub` 后赋 `stonesrc.FS`）；`func embeddedWasmFile(name string) ([]byte, bool)`。
- **对外接口**：无导出符号。
- **依赖**：`embed`、`io/fs`、`stonesrc`。
- **被依赖**：`main.go`（`embeddedWasmFile`、经 `stonesrc.FS` 间接）。
- **影响范围**：发布版 exe 的自带库与 serve 运行时；不影响 `打包` 生成的 exe（该产物复制 `internal/`+`cmd/`，不含本文件）。
- **备注**：`sahou.wasm` 不入库，构建本包前须先生成。

### sahou/go.mod
- **用途**：Go 模块定义。
- **关键内容**：`module sahou`；`go 1.23`；`require` 三条均为 `// indirect`：`github.com/jchv/go-webview2`、`github.com/jchv/go-winloader`、`golang.org/x/sys`。
- **对外接口**：— **依赖**：— **被依赖**：全仓库；`packApp` 会读取并改名（`module sahou`→`module sahouapp`）。 **影响范围**：构建、打包、CI。 **备注**：唯一直接功能依赖是 Windows 原生窗口的 go-webview2。

### sahou/go.sum
- **用途**：依赖校验和锁定。
- **关键内容**：对应 go.mod 三条依赖的 h1/go.mod 校验和。
- **对外接口**：— **依赖**：— **被依赖**：构建/打包（packApp 复制到临时工程）。 **影响范围**：离线构建。 **备注**：内容少，保证离线可构建。

### sahou/README.md
- **用途**：项目对外说明（定位、能力表、仓库结构、构建测试、版本）。
- **关键内容**：语言特性概览（23 关键字/30 内置/11 标准库模块）；一分钟上手示例；能力表（命令行/后端/浏览器/桌面/手机/独立分发）；仓库结构表；构建与测试命令；版本段落（正文写 v0.3.0，与 main.go 的 v1.0.0 存在不一致）。
- **对外接口**：— **依赖**：— **被依赖**：文档引用。 **影响范围**：对外文档一致性。 **备注**：README 版本行与 `version` 常量、CHANGELOG 需人工同步。

### sahou/CHANGELOG.md
- **用途**：版本更新说明；Release 工作流按同名小节自动提取。
- **关键内容**：v1.0.0（2026-09-22，与 v0.3.0 功能相同，版本号晋升）；v0.3.0（格子转译、默认参数、算法库汉诺塔/八皇后、LSP 悬停、打印缓冲）；v0.2.1（stones 十八包、输出提速、多行字典修复、内置同名遮蔽）。
- **对外接口**：— **依赖**：— **被依赖**：`.github/workflows/release.yml`。 **影响范围**：发版说明。 **备注**：`## vX.Y.Z` 小节标题须与 git tag 同名。

### sahou/分发版自检.saho
- **用途**：发行版冒烟自检脚本（数据库自增 + 网页渲染）。
- **关键内容**：`库 = 数据库.打开("自检.db")`；建表 `t (编号 自增, 名)`；插入"甲"；打印自增编号；`网页.渲染("<b>[[名]]</b>", {"名": "<好>"})` 验证转义。
- **对外接口**：— **依赖**（语言级）：数据库 + 网页模块。 **被依赖**：人工/CI 冒烟。 **影响范围**：dbmod / htmlmod 行为。 **备注**：`.saho` 脚本，验证内嵌库与核心模块可用。

## internal/lexer、internal/parser

### sahou/internal/lexer/lexer.go
- **用途**：把源码切成记号；缩进仅排版；括号深度 0 才产生换行记号；双语关键字归一化。
- **关键内容**：
  - 记号常量：`EOF NL IDENT NUMBER STRING IF ELIF ELSE WHILE FOR IN END FN RETURN LET TRUE FALSE NULL AND OR NOT TRY CATCH PIPE CELL BREAK CONTINUE USE IMPORT` + 运算符常量。
  - `var KeyWords map[string]string`（中英 → 同记号，24 项 12 组双拼）。
  - `type StrPart struct{ Lit, Expr string; Col int }`；`type Token struct{ Kind, Text string; Str []StrPart; Line int }`。
  - `var fullwidth map[rune]rune`（全角→半角）。
  - `type Lexer struct{ runes,pos,line,depth,toks }`；`func Tokenize(src string) ([]Token, *errs.Error)`。
  - 方法：`(*Lexer).run/skipSpaces/lexNumber/lexWord/lexString/flushStr/scanInterp/lexOp/closeBracket/emit`。
  - 自由函数：`isIdentStart/isIdentPart`。
- **对外接口**：`Tokenize`、`Token`、`StrPart`、`KeyWords`、全部记号常量、`Lexer`。
- **依赖**：`errs`。
- **被依赖**：`parser`、`interp`（builtins 的 CompletionWords 用 `KeyWords`）、`transpile`、`format`（`KeyWords`）、`lsp`、`main`、`ast`。
- **影响范围**：整个语言前端；改动波及 parser/transpile/format/lsp 及全部 cases 测试。
- **备注**：数字 `5.`/`.5`、数字后跟字母、文本跨行、未知转义、`!`/`?` 均给专门双语提示；插值 `{表达式}` 由 `scanInterp` 捕获源码字符串。

### sahou/internal/parser/parser.go
- **用途**：AST 定义 + 递归下降语法分析器。
- **关键内容**：
  - 接口 `Stmt`/`Expr`（均含 `Pos() int`）。
  - 语句：`Program`、`Line`、`LetStmt`、`ExprStmt`、`IfStmt`、`WhileStmt`、`ForStmt`、`FnStmt`(含 `Defaults`)、`ReturnStmt`、`BreakStmt`、`ContinueStmt`、`CellStmt`、`ImportStmt`、`TryStmt`。
  - 表达式：`NumLit(*big.Rat)`、`StrLit`、`StrPart`、`Ident`、`ListLit`、`DictItem`、`DictLit`、`Bin`、`Un`、`Not`、`Index`、`Member`、`Arg`、`Call`、`Pipe`、`AnonFn`、`BoolLit`、`NullLit`。
  - `func Parse(toks []lexer.Token) (*Program, *errs.Error)`；`func ParseExprSource(src string, line int) (Expr, *errs.Error)`。
  - `type Parser struct{ toks,pos }` + 方法：`cur/peek/next/at/skipNL/stmts/stmt/letStmt/lvalue/unexpected/ifStmt/blockBody/bracedBody/expectEnd/assignInCondHint/whileStmt/forStmt/fnStmt/paramList/returnStmt/cellStmt/importStmt/tryStmt/exprStmt/expr/pipeTail/orExpr/andExpr/notExpr/cmpExpr/addExpr/mulExpr/unaryExpr/postfixExpr/args/primary/listLit/dictLit/expectNL/consumeEndOfStmt`。
  - 辅助：`describe`、`emptyBlock`、`itoa`、`isSimpleDefault`、`cmpKeys`、`boolLit`、`inStops`，`var blockStoppers`、`var cmpOps`。
- **对外接口**：全部 AST 类型 + `Parse` + `ParseExprSource` + `Program`。
- **依赖**：`errs`、`lexer`。
- **被依赖**：`interp`、`transpile`、`lsp`、`main`、`internal/interp` 各模块（构造 `parser.Stmt/Expr`）、`ast.go`。
- **影响范围**：整个语言语法；新增语句/表达式会波及 interp、transpile、lsp、format 及 cases。
- **备注**：块体双风格（花括号 `{ }` 与 `完毕`），同块内不得混用；块体不可为空；比较不可连写；默认参数限不可变字面量且排在末尾；`fn(` 触发匿名函数。

## internal/interp —— 核心与值模型

### sahou/internal/interp/interp.go
- **用途**：树遍历求值器主引擎：控制流信号、语句/表达式求值、管道、模块加载、赋值、调用。
- **关键内容**：
  - 信号：`type returnSig struct{ v Value }`、`breakSig`、`continueSig`、`errorSig struct{ e *errs.Error }`。
  - `type Interp struct{ Globals *Env; ScriptDir; Stdout; Stderr; Input; LastValue; HasLastValue; depth; maxDepth; chain; warned; modules; loading; dirs; modBase; builtinMods; ExitCode; ProgramArgs; cells; watchers; tracking; mu sync.Mutex }`。
  - `func New() *Interp`（装入 builtins、`registerNetModule`、`registerStdModules`）。
  - 方法：`Run`、`runLoopBody`、`runBody`、`execBlock`、`execStmt`、`execTry`、`loadModule`、`loadModuleFrom`、`moduleBase`、`assignTo`、`eval`、`evalPipe`、`callStepFn`、`evalCallPrepend`、`indexValue`、`memberValue`、`evalBin`、`arith`、`compare`、`evalCall`、`callSahou`、`ScriptPath`、`Chain`、`callBuiltin`。
  - 辅助：`AsInt`、`repeatString`、`repeatList`、`badOpMsg`、`fixHint`、`exprName`、`ratCompare`、`dirChain`、`fnName`、`pipeUsesIt`、`displayKeys`。
- **对外接口**：`Interp`、`New`、`AsInt`、`Str`(value.go)、`Interp.Run/RunSource/ScriptPath/Chain/Watch/SetTopVar/TopValue/CallHandler`。
- **依赖**：`encodesrc`、`errs`、`lexer`、`parser`、`stonesrc`。
- **被依赖**：`lsp`、`main`、`cmd/sahouwasm`；interp 包内几乎所有文件。
- **影响范围**：语言全部运行时语义（作用域、错误传播、模块、管道、响应式、调用链）；改动会波及几乎全部 cases 与 shell 测试。
- **备注**：`panic/recover` 实现 `返回`/`跳出`/`继续`/可接住错误；`mu` 把 HTTP goroutine 求值串行化（语言层单线程语义）；`maxDepth` 默认 200（递归保护）；模块缓存键为 cacheKey、`loading` 栈做循环检测；`dirChain` 从脚本目录逐级向上找 stones。

### sahou/internal/interp/value.go
- **用途**：值模型、显示/转换、深度相等、数值辅助。
- **关键内容**：
  - `type Value = interface{}`；`type List struct{ Items []Value }`；`type Dict struct{ keys []string; m map[string]Value }`。
  - `func NewDict()`、`func KeyEncode(v Value) (string,bool)`。
  - `(*Dict)`：`Len/Has/Get/SetNew/Delete/Keys/KeysAsValues`。
  - `type SahouFn struct{ Name; Params; Defaults; Body; Env }`；`type Builtin struct{ Zh,En; Call }`（`DisplayName`）；`type BoundMember struct{ Recv,Zh,En,Call }`（`DisplayName`）。
  - `TypeName`、`TypeEnName`、`Truthy`、`Str`、`writeValue`、`writeQuoted`、`DeepEqual`、`IsNum`、`AsNum`、`IsIntVal`、`IntOf`、`FmtNum`、`expandSci`。
- **对外接口**：`Value`、`List`、`Dict`、`NewDict`、`KeyEncode`、`SahouFn`、`Builtin`、`BoundMember`、`TypeName`、`TypeEnName`、`Truthy`、`Str`、`DeepEqual`、`IsNum`、`AsNum`、`IsIntVal`、`IntOf`、`FmtNum` 及 `Dict` 方法。
- **依赖**：`fmt`、`math/big`、`strings`、`errs`、`parser`。
- **被依赖**：interp 包内全部模块文件、`lsp`、`main`、`cmd/sahouwasm`。
- **影响范围**：所有值语义（数=精确 `*big.Rat`、字典有序、显示规则、深度相等）；改动波及全部模块与 cases。
- **备注**：类型名映射中 `*Server/*Database/pageEl` 对外均呈现为"字典"；`Value` 是 `interface{}` 别名；`FmtNum` 非整数走 15 位有效数字后展开去尾零。

### sahou/internal/interp/env.go
- **用途**：词法作用域环境（函数作用域 + 顶层）。
- **关键内容**：`type Env struct{ vars map[string]Value; parent *Env }`；`func NewEnv(parent *Env) *Env`；`(*Env) Get/Set/Names`。
- **对外接口**：`Env`、`NewEnv`、`Get`、`Set`、`Names`。
- **依赖**：无本包外依赖（同包 `Value`）。
- **被依赖**：interp.go、reactive.go、core。
- **影响范围**：作用域语义（读沿链、写仅当前层，遮蔽不写外层）。
- **备注**：`Names()` 汇总整条链（供拼写建议）。

### sahou/internal/interp/builtins.go
- **用途**：内置函数注册表与实现（30 个含 1 别名），列表/字典成员函数，编辑器补全元数据。
- **关键内容**：
  - `type builtinDef struct{ zh,en string; params [][]string; fn }`；`type memberDef struct{ zh,en; fn }`。
  - `var builtins/builtinNames/builtinTable/nameToDef/listMembers/dictMembers`；`var builtinDefaults map[string]map[int]Value`；`type omitted struct{}`。
  - `func reg`、`IsBuiltinName`、`init`（注册 30 个内置 + 成员）、`listMember`、`dictMember`、`bindArgs`、`usageOf`、`argIsOmitted`、`opt`。
  - 实现：`biPrint/biInput/biNum/zhNumeralSuggestion/biStr/biList/biDict/biRangeTo/needInt/intFrom/biLen/biSlice/sliceIndexes/biThrow/biType/biContains/allNumbers/allStrings/biSum/notAList/biMax/biMin/maxMin/orderCmp/biSorted/biReversed/biJoin/biSplit/biReplace/biTrim/biUpper/biLower/biAbs/biSqrt/biRound/pow10`；`resolvePath`；`biReadFile/biWriteFile/biFind/biFileExists`；`mAppend/mDedupe/mDictRemove`。
  - LSP 元数据：`ValueMemberNames`、`CompletionWords`、`CompletionMembers`、`CompletionStoneMembers`。
- **对外接口**：`IsBuiltinName`、`ValueMemberNames`、`CompletionWords`、`CompletionMembers`、`CompletionStoneMembers`。
- **依赖**：`encodesrc`、`errs`、`lexer`、`parser`、`stonesrc`。
- **被依赖**：`interp.New`（登记 builtins）、interp.go（`IsBuiltinName`/`Completion*`）、`lsp`。
- **影响范围**：全部内置函数行为、参数绑定、成员方法；补全元数据影响 LSP 与 VS Code 扩展。
- **备注**：命名实参支持中英别名（`params [][]string`，`!` 表必填）；`文本转数/str_to_num` 是 `数/num` 的别名（不占名额）；`完成 StoneMembers` 会真实解析 stones 源码取顶层名。

### sahou/internal/interp/numbers_alias.go
- **用途**：数值内部承载的类型别名。
- **关键内容**：`type numRat = big.Rat`。
- **对外接口**：无（包内部别名）。
- **依赖**：`math/big`。
- **被依赖**：`pagemod_js.go`（`SetVarFromText` 用 `*numRat` 判断当前值是否为数）。
- **影响范围**：极小，仅别名可用性。
- **备注**：为可读性引入，等价于 `*big.Rat`。

### sahou/internal/interp/reactive.go
- **用途**：v4 响应式计算模型（格子/依赖图/观察者）。
- **关键内容**：`type cellDef struct{ name; expr; deps; computed; computing }`；`(*Interp)` 方法 `cellValue/defineCell/ensureCellComputed/onChange/fireWatchers/Watch/SetTopVar/TopValue/RunSource`。
- **对外接口**：`Watch`、`SetTopVar`、`TopValue`、`RunSource`。
- **依赖**：`errs`、`lexer`、`parser`。
- **被依赖**：interp.go（`eval` 的 Ident 读取、`assignTo` 的 `onChange`）、`pagemod_js.go`（`绑输入/绑定`）。
- **影响范围**：格子/响应式语义、REPL 共享 Globals、浏览器绑定。
- **备注**：惰性求值 + 依赖失效 + 环检测；`tracking` 指针在 `eval` 里记录读取名字；`computing` 防环。

### sahou/internal/interp/stdmod.go
- **用途**：标准库模块 随机/时间/数学/编码/系统 + 模块构造基础设施。
- **关键内容**：
  - `ratToFloat/floatToRat/needNum/needTextArg/needIntMod`。
  - `type modBuilder struct{ d *Dict }`；`newMod`；`(*modBuilder) fn/val`；`mergeModuleNamed`。
  - `modRandom`（数/小数/挑/洗牌/种子，`rngMu` 保护共享 RNG）；`modTime`（现在/文本/解析/戳/计时/耗时，`timeDict`）；`modMath`（圆周率 + 对数/常用对数/正弦/余弦/正切/向上取整/向下取整/幂/最大公约数/最小公倍数）；`modEncoding`（网址/网址解码/六十四/六十四解码/十六进制/十六进制解码 + `hexVal`）；`modSystem`（参数/环境/平台/退出 + `base64Encode/base64Decode`）。
  - `moduleNamePair`；`registerStdModules`。
- **对外接口**：无导出符号（包内使用）。
- **依赖**：`errs`（+ 标准库 math/rand、time、encoding/base64、net/url 等）。
- **被依赖**：`interp.New`。
- **影响范围**：五个内置标准库模块；转译器 `transpile.go` 需镜像同名成员（`__saho_std_*`）。
- **备注**：`系统.退出` 返回带 `Exit` 的错误（非错误显示）；`floatToRat` 按 15 位有效数字圆整以与显示一致。

### sahou/internal/interp/netmod.go
- **用途**：网络模块 HTTP 服务端/客户端 + JSON + 会话；并作为全部模块的**级联注册器**。
- **关键内容**：
  - `type Server struct{ routes; names; patterns; statics; sessMu; sessions; sessionSeen; sessPath }`；`const sessionTTL`；`patternRoute`、`staticRoute`；`newServer`；`netModule`。
  - `var serverMembers`；`init`（注册 路由/监听/静态/会话存）；`srvRoute/srvListen/srvStatic/srvSessionStore`；`serveHTTP`。
  - `(*Interp).serveHTTP`、`(*Interp).CallHandler`、`(*Server).openSession/saveSession/gcSessionsLocked/dumpSessionsLocked/loadSessionsLocked`；`handlerName`。
  - 客户端/JSON：`netRequest`、`netJSONResp/netHTMLResp/netRedirect/respHeaders`、`netJSONTo/jsonWrite/netJSONFrom/jsonToValue`。
  - `registerNetModule`（级联 `registerPageModule/registerHTMLModule/registerDBModule/registerAppModule/registerTestModule`）。
- **对外接口**：`Server`。
- **依赖**：`errs`（+ net/http、encoding/json 等）。间接依赖同包 page/html/db/app/test。
- **被依赖**：`interp.New`。
- **影响范围**：网络/后端能力、会话、表单/上传、JSON；网络相关 shell 测试。
- **备注**：每请求一 goroutine，`in.mu` 串行化求值；路径参数用 `:名`（避免与字符串插值花括号冲突）；会话 24h TTL。

### sahou/internal/interp/dbmod.go
- **用途**：内置数据库 数据库/db（纯 Go 嵌入式 SQL + JSON 原子落盘）。
- **关键内容**：
  - `type dbTable struct{ cols; autoCols; rows }`（`nextAuto`）；`type Database struct{ mu; path; tables }`；`var dbMembers`；`init`。
  - 注册：`dbModule`、`registerDBModule`、`openDatabase`、`(*Database).save`。
  - JSON 单元格：`dbCellToJSON`、`dbCellFromJSON`。
  - 成员实现：`dbExec/dbQuery/dbTables/dbClose`。
  - SQL：`sqlTok`、`sqlTokenize`、`isIdentRune`；`dbAgg/dbStmt/dbSet/dbCond/dbOperand/paramBinder`；`sqlParser`、`aggNames`、`tryAggregate`、`nextParam`、`parseSQL`、`peek/next/eatWord/eatCompound/eatPhrase/eatSym/ident/errSyntax/parse/parseSelectTail/parseWhere/parseValueTuple/parseOperand/parseOr/parseAnd/parseCmp`；执行 `(*dbStmt) run/selectRows`；`aggCompute`、`colNames/autoColsOf/colIndex/colNames`、`(*dbTable) rowCol`、`(*Database) tableOf`、`(*dbCond) eval`、`(dbOperand) bindRow/bind`、`stJoin`、`compareValues`。
- **对外接口**：`Database`（`TypeName` 呈现为"字典"）。
- **依赖**：`errs`（+ encoding/json、sort、sync 等）。
- **被依赖**：`netmod.go`（`registerDBModule`）；`dbmod_test.go`。
- **影响范围**：数据库/全栈能力；JSON 存储格式（`列/自增/行`，数用字符串保精度）；`fullstack.sh`、`分发版自检.saho`。
- **备注**：SQL 关键词中英双语可混写、支持连写（`如无`/`哪里`/`降序`）；原子落盘（tmp+rename）；自增列取全表最大+1。

### sahou/internal/interp/htmlmod.go
- **用途**：服务端模板渲染模块 网页/html。
- **关键内容**：`htmlMod()`；`htmlEscape`；`htmlRender`（`[[名]]` 转义、`[[[名]]]` 原样）；`lookupKey`（支持 `a.b` 嵌套）；`registerHTMLModule`。成员：转义/渲染/渲染文件/页面。
- **对外接口**：无导出符号。
- **依赖**：`errs`。
- **被依赖**：`netmod.go`（`registerHTMLModule`）。
- **影响范围**：模板渲染与转义（防注入）；`fullstack.sh`、`app.sh`、`分发版自检.saho`。
- **备注**：用 `[[ ]]` 而非 `{{ }}`（后者被字符串插值占用）。

### sahou/internal/interp/appmod.go
- **用途**：应用模块 应用/app（桌面窗口 / 手机端 / 打开浏览器 / 写页面转发）。
- **关键内容**：`appModule()`；`serveApp`；`freePort`；`lanIPs`；`var safeBrowserURL`（正则白名单）；`openBrowser`；`registerAppModule`。成员：打开/窗口/原生窗口/写页面/手机。
- **对外接口**：无导出符号。
- **依赖**：`errs`（+ net/http、os/exec、runtime 等）。
- **被依赖**：`netmod.go`（`registerAppModule`）；`uimod.go` 的 `写页面` 调用链 `registerAppModule → uiNewPage`。
- **影响范围**：桌面/手机端本地静态服务、原生窗口入口（依赖 `nativewin_*`）；`app.sh`。
- **备注**：`openBrowser` 仅放行内部拼装的本地地址（`safeBrowserURL`），外部输入不自动打开。

### sahou/internal/interp/uimod.go
- **用途**：纯代码构造图形界面（`应用.写页面`）：页面/控件模型 + HTML 生成 + 事件派发/镜像同步。
- **关键内容**：
  - `type UIPage struct{ in; mu; title; w,h; widgets; seq; wv }`；`type uiWebView interface{ Eval(string) }`；`type uiWindowSpec struct{ title; w,h; html; onEvent; onSync; onReady }`；`type UIWidget struct{ id; kind; text; pholder; options; handler; value; checked; kids; page }`。
  - `uiNewPage`、`(*UIPage).add/buildHTML/findWidget/onEvent/onSync/evalEl`；`var uiPageMembers/uiWidgetMembers` + `init`。
  - 页面成员：`uiPageTitle/Label/Button/Input/Check/Select/Row/Alert/Show/ToHTML`；控件成员：`uiWidgetSetText/GetText/SetPlaceholder/GetChecked/SetChecked/GetSelected/SetOptions`。
  - HTML：`uiPageCSS`、`uiPageJS`、`(*UIWidget).html`、`uiOptionsHTML`、`htmlAttr`、`uiJSON`。
  - `callUIHandler`、`uiCheckHandler`。
- **对外接口**：无导出符号（`UIWidget` 被同包测试引用，非导出）。
- **依赖**：`errs`（+ encoding/json）。
- **被依赖**：`appmod.go`（`写页面`）、`interp.go`（`memberValue` 处理 `*UIPage/*UIWidget`）、`value.go`（显示）、`nativewin_other.go`（`uiWindowSpec/funcWebView`）、`uimod_test.go`。
- **影响范围**：`写页面` 全链路、原生窗口事件桥、`095_page_builder` 快照、`uimod_test.go`。
- **备注**：`uiWebView` 窄接口隔离平台；`onEvent` 永不上抛（出错转弹窗+控制台）；`onSync` 高频镜像不触发事件。

### sahou/internal/interp/pagemod_js.go
- **用途**：页面模块浏览器宿主版（`syscall/js` 操作 DOM）+ 响应式绑定。
- **关键内容**：`//go:build js && wasm`；`type pageEl struct{ v js.Value }`（`isPageEl`）；`jsDoc`；`registerPageModule`（成员 16 项：取元素/取全部/置文本/取文本/值/置值/置样式/置属性/创建/加入/移除/点击/输入/提交/绑输入/绑定）；`elementErr`；`(*Interp).SetVarFromText`。
- **对外接口**：`(*Interp).SetVarFromText`。
- **依赖**：`errs`（+ syscall/js）。
- **被依赖**：`netmod.go`（`registerPageModule`）；`value.go`（`isPageEl` 接口识别）；`wasm_reactive.mjs` 测试。
- **影响范围**：浏览器直跑（sahou.wasm）DOM/事件/响应式；`wasm.sh`。
- **备注**：仅在 `js && wasm` 生效；与 `pagemod_std.go` 同名函数二选一。

### sahou/internal/interp/pagemod_std.go
- **用途**：页面模块服务端/其它宿主版（全部成员返回"只能在浏览器里用"提示）。
- **关键内容**：`//go:build !js || !wasm`；`registerPageModule`（16 个成员名，每个都返回双语 RuntimeHint）。
- **对外接口**：无导出符号。
- **依赖**：`errs`。
- **被依赖**：`netmod.go`（`registerPageModule`，非 wasm 平台）。
- **影响范围**：本地解释器里 `页面.*` 的降级行为。
- **备注**：与 `pagemod_js.go` 互斥；不报编译错，调用时提示改用 `网络` 或改为 wasm。

### sahou/internal/interp/nativewin_windows.go
- **用途**：Windows 原生窗口实现（WebView2）。
- **关键内容**：`//go:build windows`；`runNativeWindow(url, title string, w, h int)`；`runNativePage(spec uiWindowSpec)`（`wv.Bind` 绑 `__saho_event`/`__saho_sync`，`onReady` 后置 HTML，`wv.Run` 阻塞）。
- **对外接口**：无导出符号（`runNativeWindow`/`runNativePage` 包内约定）。
- **依赖**：`github.com/jchv/go-webview2`（+ fmt）。
- **被依赖**：`appmod.go`（`原生窗口`）、`uimod.go`（`显示`）。
- **影响范围**：Windows 桌面原生窗口；非 Windows 编译时本文件被排除。
- **备注**：无 CGO；Win10/11 预装 WebView2 运行时。

### sahou/internal/interp/nativewin_other.go
- **用途**：非 Windows 平台的原生窗口降级（改用浏览器 + 事件桥）。
- **关键内容**：`//go:build !windows`；`runNativeWindow`（开浏览器 + `select{}`）；`type uiEvent struct{ sync bool; payload string }`；`runNativePage`（本机 HTTP：`/事件`、`/同步` POST 上行、`/流` SSE 下行、`/关闭` sendBeacon，注入 `window.__saho_event/__saho_sync` 垫片）；`type funcWebView struct{ fn }`（`Eval`）。
- **对外接口**：无导出符号。
- **依赖**：net/net/http、strings、sync、fmt。
- **被依赖**：`appmod.go`、`uimod.go`（同 `runNativePage` 约定）。
- **影响范围**：Linux/macOS 桌面窗口与 `写页面` 事件能力（经浏览器事件桥）。
- **备注**：把平台差异挡在 `uimod.go` 的 `uiWebView` 接口后；SSE 通道串行推送 JS 命令。

### sahou/internal/interp/testmod.go
- **用途**：测试模块 测试/assert（用户程序单元测试）。
- **关键内容**：全局计数 `testMu/testPass/testFail/testNames`；`testModule`（成员 相等/为真/汇总/清零）；`nameOf`；`recordResult`；`registerTestModule`。
- **对外接口**：无导出符号。
- **依赖**：`errs`（+ fmt、math/big、sync）。
- **被依赖**：`netmod.go`（`registerTestModule`）。
- **影响范围**：用户级断言能力；`测试.汇总` 返回值（失败数或空值）。
- **备注**：`汇总` 直接 `fmt.Printf` 打印（不写 `in.Stdout`），与解释器缓冲输出可能不同步。

## internal/interp —— 测试

### sahou/internal/interp/bench_test.go
- **用途**：解释器基准测试（`go test ./internal/interp -bench .`）。
- **关键内容**：`runBench`；`BenchmarkLoopArith`（循环算术）、`BenchmarkStringBuild`（字符串拼接）、`BenchmarkDictIO`（字典读写）。每轮 `New()` + `Run(prog)`。
- **对外接口**：测试函数（`Benchmark*`）。**依赖**：`lexer`、`parser`。**被依赖**：`run_all.sh` 的 `go test`。 **影响范围**：性能基线。 **备注**：解析在计时外，`New()` 在计时内。

### sahou/internal/interp/dbmod_test.go
- **用途**：数据库单元测试（自增、聚合、原子落盘重开）。
- **关键内容**：`runDB`（占位）；`TestDBAutoIncAggPersist`（直接调用 `openDatabase/dbExec/parseSQL/selectRows`）。
- **对外接口**：`TestDBAutoIncAggPersist`。**依赖**：无本包外依赖（math/big、os、testing）。**被依赖**：`run_all.sh`。 **影响范围**：dbmod 行为。 **备注**：直接调用内部函数，不经过语言层。

### sahou/internal/interp/stdmod_test.go
- **用途**：标准库单元测试（hex 与百分号解码）。
- **关键内容**：`TestHexVal`；`TestPercentDecode`（构造 `modEncoding()` 取 `网址解码` Builtin 调用）。
- **对外接口**：`TestHexVal/TestPercentDecode`。**依赖**：`testing`。**被依赖**：`run_all.sh`。 **影响范围**：编码模块。 **备注**：小而精，覆盖边界（`G` 失败）。

### sahou/internal/interp/uimod_test.go
- **用途**：写页面无窗口路径测试（构造/到HTML/事件派发/镜像同步/参数校验）。
- **关键内容**：`runUISource`；`globalWidget`；`TestPageToHTML`、`TestPageEventDispatch`、`TestPageSyncMirror`、`TestPageHandlerArityError`。
- **对外接口**：`Test*`。**依赖**：`strings`、`testing`。**被依赖**：`run_all.sh`。 **影响范围**：uimod。 **备注**：直接调 `(*UIPage).onEvent/onSync` 与 `uiWidgetGetChecked`。

## internal —— 其它包

### sahou/internal/transpile/transpile.go
- **用途**：sahou → JavaScript 转译器（复用 lexer/parser/AST 代码生成后端，**不 import interp**）。
- **关键内容**：
  - `//go:embed rt.js` → `var runtimeJS`；`var jsReserved`；`rename`。
  - `var builtinJS map[string]string`（30 内置 → `__saho_*`）、`var binopJS`。
  - `type Builder struct{ out; ind; mods; itVar; decl; cellNames; fnDepth }` + 方法 `pushDecl/popDecl/declared/linef/stmt/expr/paramListJS/ident/bin/call/pipe/stepToFn/strLit`。
  - `type modUnit struct{ id,name,prog,base,names }`；`modIDByName`。
  - `func Build(prog *parser.Program, baseDir string) (string, *errs.Error)`。
  - 辅助：`collectCells/collectFreeIdents/isBuiltinJSName/collectModules/stdModulePair/isBuiltinModule/stdModuleObject/resolveModule/collectAssigned/__saho_numLit/defaultArrayArg/joinRenamed/optsBody/jsMemberName/isASCIIIdent/stdModuleObject2/containsIt/goQuote/serverOnlyModule`。
- **对外接口**：`Build`。
- **依赖**：`errs`、`lexer`、`parser`、`stonesrc`（+ embed rt.js）。
- **被依赖**：`main.go`（`buildJS`）；转译相关 shell 测试（build/modules/stdlib/packages）。
- **影响范围**：浏览器部署、转译语义与解释器一致性、响应式格子 JS 运行时（`rt.js`）。
- **备注**：`serverOnlyModule` 对 网络/数据库/应用/测试 在浏览器侧报错；内置同名遮蔽靠 `decl` 作用域栈；顶层变量登记 `__saho_regvar` 供响应式绑定。

### sahou/internal/transpile/rt.js
- **用途**：转译产物的 JS 运行时（`__saho_*` 辅助函数集合）。
- **关键内容**：1087 行 JS；由 `//go:embed` 作为生成文件前导。**对外接口**：— **依赖**：— **被依赖**：`transpile.go`。 **影响范围**：所有 `sahou build` 产物。 **备注**：未在本轮逐行精读（非用户指定清单），仅确认其被 embed 引用。

### sahou/internal/format/format.go
- **用途**：保守格式化（只重排缩进、去行尾空白、压缩空行，不改记号）。
- **关键内容**：`var blockOpeners/blockContinuers/blockClosers`；`func Source(src string) string`；`firstWord`；`isWordRune`。
- **对外接口**：`Source`。
- **依赖**：`lexer`（`KeyWords`）。
- **被依赖**：`main.go`（`formatFile`）。
- **影响范围**：`sahou 格式`；缩进单位 4 空格。
- **备注**：不解析 AST，按行首关键词改层级；字符串内关键词不影响（只识别行首）。

### sahou/internal/errs/errs.go
- **用途**：双语错误体系（报错即教学）。
- **关键内容**：`type Kind int`（`KindSyntax/KindRuntime`）；`type Frame struct{ Line; Func }`；`type Error struct{ Kind; Zh; En; Hint; Line; Exit }`（`Error()`）；构造函数 `Syntax/SyntaxHint/Runtime/RuntimeHint`；`Format`（三行式）；`FormatUncaught`（消息+调用链+停止语）；`DidYouMean`；`editDistance`；`min3`。
- **对外接口**：`Kind`、`Kinds`、`Frame`、`Error`、`Syntax`、`SyntaxHint`、`Runtime`、`RuntimeHint`、`Format`、`FormatUncaught`、`DidYouMean`。
- **依赖**：fmt、strings。
- **被依赖**：几乎全部包（lexer/parser/interp/transpile/lsp/main）。
- **影响范围**：所有错误文案与退出码；`Exit>=0` 语义贯穿 `in.Run`、`系统.退出`。
- **备注**：零值 `Exit` 必须是 -1（构造函数统一设置）；`DidYouMean` 编辑距离阈值 2/3。

### sahou/internal/encodesrc/encodesrc.go
- **用途**：读源文件并归一为 UTF-8（识别 BOM/UTF-16；非法 UTF-8 给双语提示）。
- **关键内容**：`func ReadFile(path string) (string, error)`；`func Decode(data []byte, path string) (string, error)`；`utf16Decode`。
- **对外接口**：`ReadFile`、`Decode`。
- **依赖**：os、unicode/utf16、unicode/utf8。
- **被依赖**：`interp`（loadModule/CompletionStoneMembers）、`main`。
- **影响范围**：所有读源路径（run/build/pack/format/dump/module/lsp 补全）。
- **备注**：支持 UTF-8 BOM / UTF-16LE / UTF-16BE；GBK 提示需另存 UTF-8。

### sahou/internal/stonesrc/stonesrc.go
- **用途**：exe 自带 stones 包的唯一存放处（编译期 embed 注入 `FS`）。
- **关键内容**：`var FS fs.FS`；`Has`；`Read`；`Source`；`Names`。
- **对外接口**：`FS`、`Has`、`Read`、`Source`、`Names`。
- **依赖**：io/fs、sort、strings。
- **被依赖**：`interp`（loadModule 兜底、builtins 补全、main 的 stones/装/验证）、`transpile`（模块兜底）、`lsp`（包名/悬停）、`stonesfs.go`、`cmd/sahouwasm/stones.go`。
- **影响范围**：离线标准库包能力（18 包）、serve 运行时、补全与悬停数据。
- **备注**：`FS==nil` 时全部安全返回"没有"；目录包入口固定 `main.saho`。

### sahou/internal/lsp/lsp.go
- **用途**：`sahou lsp` 语言服务器（stdio JSON-RPC）：诊断 + 补全 + 悬停 + 跳转定义 + 重命名。
- **关键内容**：
  - `var SharedJSON string`；`type sharedLang struct{ Keywords/Builtins/Modules/Stones }`；`var shared`；`parseShared`。
  - RPC 类型：`rpcMessage/position/rangeT/diagnostic/textDocumentItem/didOpenParams/didChangeParams/publishParams/completionParams`。
  - `completionItems`、`linePrefix`（UTF-16→字节换算）、`filterByPrefix`、`packageNames`。
  - `func Run()`（主循环：initialize/initialized/didOpen/didChange/didClose/completion/hover/shutdown/exit）。
  - `diagnostics`、`toDiag`、`publish`；`wordAt`、`hoverMarkdown`、`containsString`、`dynamicStoneMembers`；帧读 `mustJSON/writeMessage/readFrame/extractFrame`。
  - 跳转定义/重命名（批41）：`definitionFor/renameTargets/collectDefs`——同文件文本级扫描三类定义（`函数/func 名字(`、`设 名字 为`、`名字 =`），光标前最近定义优先（先调用后定义可跳）；重命名全文整词替换、拒绝含空格的非法新名；`utf16Col` 列换算、`stripComments` 剥注释防误配。
- **对外接口**：`Run`、`SharedJSON`。
- **依赖**：`errs`、`interp`、`lexer`、`parser`、`stonesrc`（+ encoding/json 等）。
- **被依赖**：`main.go`（`lsp` 子命令，先注入 `SharedJSON`）。
- **影响范围**：编辑器诊断/补全/悬停；VS Code 扩展依赖。
- **备注**：悬停数据来自 `editors/shared/language.json`（未注入则悬停退化，诊断/补全不受影响）；补全上下文区分"用 \"前缀"/"名字.成员"/其它。批41 已知边界：跳转/重命名不区分作用域、不跨文件；单测见 `internal/lsp/lsp_test.go`。

### sahou/internal/lsp/lsp_test.go
- **用途**：LSP 跳转定义/重命名的 Go 单元测试（批41 新增）。
- **关键内容**：三类定义查找与「先调用后定义」、重命名编辑集、非法新名拒绝、UTF-16 列换算、注释剥离。
- **对外接口**：`go test ./internal/lsp`。
- **依赖**：`internal/lsp`。
- **被依赖**：无。
- **影响范围**：改 `lsp.go` 跳转/重命名逻辑后必须保持全绿。
- **备注**：纯 Go 单测，不依赖编辑器。

### sahou/tests/share_codec.mjs
- **用途**：在线体验页分享链接编解码的回归测试（批41 新增，Node 直跑）。
- **关键内容**：代码 ↔ base64url（`#code=`）往返；URL 安全字符校验（不含 `+/=`）。
- **对外接口**：`node tests/share_codec.mjs` → 输出 SHARE-CODEC-OK。
- **依赖**：无（零依赖 Node）。
- **被依赖**：无。
- **影响范围**：改 `examples/在线体验/index.html` 的分享编解码后必须重跑。
- **备注**：与 wasm 无关，秒级完成。

## cmd/sahouwasm

### sahou/cmd/sahouwasm/main.go
- **用途**：浏览器直跑版入口（sahou.wasm），直接解释执行 `.saho`。
- **关键内容**：`//go:build js && wasm`；`func main()`（`registerPlayground` + `readSource` + `go in.RunSource` + `<-wait` 常驻）；`registerPlayground`（注册 `__sahou_run`/`__卅_run`，捕获输出返回 JSON）；`readSource`（`__SAHO_SOURCE` 或 fetch `__SAHO_PAGE`）；`fetchText`。
- **对外接口**：`main`（wasm 目标）。
- **依赖**：`errs`、`interp`（+ syscall/js）。
- **被依赖**：`wasm.sh`、`examples/在线体验`、`examples/响应式`。
- **影响范围**：浏览器解释执行、在线体验、`serve` 壳页。
- **备注**：解释器 goroutine 常驻以维持事件/响应式；`__卅_run` 为语言名别名。

### sahou/cmd/sahouwasm/stones.go
- **用途**：把 wasm 版内嵌 stones 注入 `stonesrc.FS`。
- **关键内容**：`//go:build js && wasm`；`//go:embed stones` → `var stonesDir embed.FS`；`func init()`。
- **对外接口**：无。**依赖**：embed、io/fs、`stonesrc`。**被依赖**：wasm 构建。 **影响范围**：浏览器内 `用 "包名" 引入` 免安装。 **备注**：`cmd/sahouwasm/stones/` 由 `wasm.sh` 从仓库根 `stones/` 同步（embed 不能引用上级目录）。

## internal/interp —— 其它注册关系补充

（`stdmod/htmlmod/dbmod/appmod/testmod/pagemod_*` 均通过 `netmod.go` 的 `registerNetModule` 级联注册，已在第二章说明，此处不重复。）

## tests —— shell 脚本

### sahou/tests/run.sh
- **用途**：核心一致性测试（cases 快照 diff + 负向用例退出码/子串）。
- **关键内容**：遍历 `cases/*.saho` 比 `.out`；再遍历有 `.err` 的用例比退出码与子串；输出 `通过 X / N`。
- **对外接口**：shell 入口。**依赖**：`./sahou.exe`、`tests/cases/`。**被依赖**：`run_all.sh`。 **影响范围**：语言核心行为回归。 **备注**：`cd "$(dirname "$0")/.."`；`2>/dev/null` 只比 stdout。

### sahou/tests/run_all.sh
- **用途**：全量回归总闸。
- **关键内容**：依次跑 `run build modules stdlib packages pack net fullstack app`；再 `gofmt -l main.go internal cmd` 与 `go test ./internal/...`。
- **对外接口**：shell 入口。**依赖**：其它脚本、gofmt、go。**被依赖**：CI（`.github/workflows/ci.yml`）。 **影响范围**：全仓库。 **备注**：wasm.sh 不在此列（单独跑）。

### sahou/tests/build.sh
- **用途**：转译器一致性测试。
- **关键内容**：核心用例 `build`→Node 输出对齐；`examples/计数器.saho` DOM 桩交互（生成临时 `tmp_counter_run.mjs`）；`COUNTER_OK`。
- **对外接口**：shell 入口。**依赖**：node、`sahou.exe`、`tests/domstub.mjs`。**被依赖**：`run_all.sh`。 **影响范围**：transpile.go 与 rt.js。 **备注**：用 `cygpath -m` 兼容 Git Bash。

### sahou/tests/modules.sh
- **用途**：模块系统 + stones 流程回归。
- **关键内容**：用户模块/内置模块、循环引入、模块顶层 `返回`、缺模块、转译、`装`、`页面` 模块转译。
- **对外接口**：shell 入口。**依赖**：`sahou.exe`、node、`tests/modproject/`。**被依赖**：`run_all.sh`。 **影响范围**：interp 模块系统与 transpile 模块打包。 **备注**：在临时目录 `mktemp -d` 内运行。

### sahou/tests/stdlib.sh
- **用途**：标准库模块回归（随机/时间/数学/编码/系统）。
- **关键内容**：解释器 + Node 双侧对齐；错误路径（挑空列表/对数 0/非法解码/负数非整数次幂）；`系统.参数` 与 `系统.退出(7)`。
- **对外接口**：shell 入口。**依赖**：`sahou.exe`、node。**被依赖**：`run_all.sh`。 **影响范围**：stdmod.go。 **备注**：随机行与 `系统.平台` 在 JS 侧差异被 sed/grep 处理。

### sahou/tests/packages.sh
- **用途**：stones 标准库包回归。
- **关键内容**：`examples/pkgdemo/演示.saho` 向上查找、转译对齐、`装` 单文件/目录包、模块隔离、包级循环引入。
- **对外接口**：shell 入口。**依赖**：`sahou.exe`、node、`examples/pkgdemo/`。**被依赖**：`run_all.sh`。 **影响范围**：stones 18 包 + 模块查找 + transpile 兜底。 **备注**：随机行被 `strip_random` 剔除比较。

### sahou/tests/wasm.sh
- **用途**：WASM 直跑回归。
- **关键内容**：同步 stones → `cmd/sahouwasm/stones`；`GOOS=js GOARCH=wasm` 构建；跑 `wasm_reactive.mjs` + `playground_check.mjs`。
- **对外接口**：shell 入口。**依赖**：go、node、`wasm_exec.js`。**被依赖**：发版/手动。 **影响范围**：cmd/sahouwasm + pagemod_js + reactive。 **备注**：不在 run_all.sh 内。

### sahou/tests/net.sh
- **用途**：网络模块回归。
- **关键内容**：清 8080 → 起 `examples/待办服务.saho` → curl 增删查/404 → 客户端 `网络.请求/自文本`。
- **对外接口**：shell 入口。**依赖**：`sahou.exe`、curl。**被依赖**：`run_all.sh`。 **影响范围**：netmod.go。 **备注**：Windows 用 `netstat/taskkill` 清端口；请求体走 UTF-8 文件绕编码。

### sahou/tests/fullstack.sh
- **用途**：全栈端到端回归。
- **关键内容**：数据库全流程（建/插/改/删/重开）+ 网页转义 + 留言板（表单/会话 Cookie/入库/回显）。
- **对外接口**：shell 入口。**依赖**：`sahou.exe`、curl、`examples/留言板.saho`。**被依赖**：`run_all.sh`。 **影响范围**：dbmod/htmlmod/netmod。 **备注**：/tmp 在 Windows Go 写不进，改临时目录并 `sed` 改路径。

### sahou/tests/app.sh
- **用途**：应用与后端写法回归。
- **关键内容**：路径参数路由、`JSON回应/网页回应/重定向/渲染文件`、桌面 `窗口`（静默）静态服务、`手机` 局域网服务。
- **对外接口**：shell 入口。**依赖**：`sahou.exe`、curl。**被依赖**：`run_all.sh`。 **影响范围**：appmod/netmod/htmlmod。 **备注**：清 8080/8091/8092/8093。

### sahou/tests/packages.sh 之外的 pack.sh
- **用途**：打包与自带库回归。
- **关键内容**：`stones` 列内嵌包、`装 <内置包>`、`打包` exe 自带 stones、`serve` 内嵌 wasm + `.saho` 壳页 + `卅.wasm` 别名 + 缺页 404。
- **对外接口**：shell 入口。**依赖**：`sahou.exe`、go、curl。**被依赖**：`run_all.sh`（脚本名 `pack`）。 **影响范围**：main.go 的 pack/serve/stones 子命令 + stonesfs.go。 **备注**：验证 `分发版` exe 自包含。

### sahou/tests/domstub.mjs / domstub.js / wasm_reactive.mjs / playground_check.mjs
- **用途**：测试桩与 Node 侧驱动。
- **关键内容**：`domstub.mjs`（最小 DOM：`makeEl/document/__saho_test_register/__saho_test_dom`）；`domstub.js`（CJS 同名版）；`wasm_reactive.mjs`（wasm 里跑格子+绑输入/绑定，`WASM_REACTIVE_OK`）；`playground_check.mjs`（`__sahou_run` + 内嵌 stones + 管道/格子，`PLAYGROUND_OK`）。
- **对外接口**：ESM/JS 导出。**依赖**：node、`wasm_exec.js`、`sahou.wasm`。**被依赖**：`build.sh`、`wasm.sh`。 **影响范围**：transpile 产物与 wasm 运行。 **备注**：非 shell 脚本，作为测试基础设施。

## tests/cases —— 正向用例（`0xx`，配对 `.out`）

> 每条格式：用例（`.saho`）→ 断言（`.out` 快照）。`.out` 为逐字期望标准输出。

### sahou/tests/cases/010_numbers.saho（快照 010_numbers.out）
- **用途**：数值语义（精确有理数、真除法、取余、优先级、`+` 字符串/列表重载、`*` 重复）。
- **关键内容**：`10==10.0`→真；`10/3`→`3.33333333333333`；`-7%3`→`2`；`0.1+0.2==0.3`→真；`1=="1"`→假；`"a"*3`→aaa；`[0]*3`→`[0, 0, 0]`。
- **依赖**（语言）：核心 arith/index。 **被依赖**：`run.sh`、`build.sh`。 **影响范围**：interp.arith/value.FmtNum + transpile JS 运行时。 **备注**：转译侧也参与 build.sh 对齐。

### sahou/tests/cases/020_strings.saho（020_strings.out）
- **用途**：字符串插值/转义与文本内置（长度/转大写/修剪/分割/替换/包含）。
- **断言要点**：`花括号 {这样}`（`\{` 字面）、`["a", "b"]`、`bbb`、真。
- **影响范围**：lexer.lexString/scanInterp + builtins 文本函数。 **备注**：`分隔: ";"` 命名实参。

### sahou/tests/cases/030_lists_dicts.saho（030_lists_dicts.out）
- **用途**：列表/字典成员与全局函数、有序字典、下标/成员赋值。
- **断言要点**：`名单.添加/去重`、`取`、`排序(降序)`、`反转`、`求和/最大/最小/连接`、`小猫.名字/["饥饿"]/["年龄"]=1`、`列表(字典)`、`字典(配对)`。
- **影响范围**：interp memberValue/indexValue/assignTo + builtins 容器函数。

### sahou/tests/cases/040_control.saho（040_control.out）
- **用途**：控制流（如果/又如/否则、当、for 于 列表/文本/字典）。
- **断言要点**：良、6、60、`卅`、`a`、`b`。
- **影响范围**：interp.execStmt 控制流分支。

### sahou/tests/cases/050_functions.saho（050_functions.out）
- **用途**：函数/匿名函数/一等函数/递归/作用域遮蔽/循环变量作用域。
- **断言要点**：3、空值、14、10、720、99、0、11、2（末尾 `print(i)` 得循环变量泄漏值 2）。
- **影响范围**：callSahou/Env 作用域。

### sahou/tests/cases/060_errors.saho（060_errors.out）
- **用途**：尝试/接住（除零、抛出、转换错误、跨函数抛出）。
- **断言要点**：四类"接住: …" + `继续执行`。
- **影响范围**：execTry/errorSig 传播。

### sahou/tests/cases/070_builtins2.saho（070_builtins2.out）
- **用途**：类型名与数学内置（类型/文本转数/数(真)/四舍五入(含负位)/平方根/绝对值/深度包含）。
- **断言要点**：number/string/list/dict/bool/null、42、1、3、1.23、1200、3、2.5、真。
- **影响范围**：biType/biNum/biRound/biSqrt/biAbs/biContains + TypeEnName。

### sahou/tests/cases/080_fullwidth.saho（080_fullwidth.out）
- **用途**：全角符号自动按半角处理（引号/括号/逗号/句点/惊叹号）。
- **断言要点**：`你好，卅！`、`咪咪`、`6！`。
- **影响范围**：lexer.fullwidth 归一化。

### sahou/tests/cases/090_semi_quotes.saho（090_semi_quotes.out）
- **用途**：分号作语句结束符 + 全角引号 + 花括号块 + 分号。
- **断言要点**：3、全角引号、`花括号+分号+全角引号`。
- **影响范围**：lexer.lexOp（`;`→NL）与 lexString（全角引号）。

### sahou/tests/cases/092_closure_dict.saho（092_closure_dict.out）
- **用途**：作用域语义（函数读外层、赋值新建局部、共享状态用字典）。
- **断言要点**：1、99、1、真、假。
- **影响范围**：Env/闭包/字典可变性。

### sahou/tests/cases/093_pipeline.saho（093_pipeline.out）
- **用途**：数据管道 `->`（裸函数、匿名函数、带参调用、`它` 隐式、链式）。
- **断言要点**：`[3, 2, 1]`、3、21、20、1、`5-2-8`、`[5, 2]`、2、60。
- **影响范围**：interp.evalPipe/callStepFn + transpile.pipe。

### sahou/tests/cases/094_pipeline_arrow.saho（094_pipeline_arrow.out）
- **用途**：全角箭头 `→` 与 `->` 等价（词法归一）。
- **断言要点**：`[1, 2]`、3、150。
- **影响范围**：lexer（`→`→PIPE）。

### sahou/tests/cases/095_page_builder.saho（095_page_builder.out）
- **用途**：纯代码写页面 + `到HTML` 快照（标签/输入框/行/按钮事件/下拉）。
- **断言要点**：6 项 `包含(...)` 全为真（标题/问句/placeholder/`事件('件5')`/`<option>中杯</option>`/`class='行'`）。
- **影响范围**：uimod.buildHTML/html。
- **备注**：窗口相关（显示/弹窗）不参与快照。

### sahou/tests/cases/096_multiline_dict.saho（096_multiline_dict.out）
- **用途**：多行字典/列表字面量（尾逗号、闭括号独立成行、空字典）。
- **断言要点**：咪咪、0、3、153、0。
- **影响范围**：parser.dictLit/listLit + lexer（花括号不抑制换行）。

### sahou/tests/cases/097_builtin_shadow.saho（097_builtin_shadow.out）
- **用途**：参数名与内置函数同名（函数内遮蔽内置；赋值/重定义内置则报错）。
- **断言要点**：ababab、1。
- **影响范围**：Env 遮蔽 + interp/transpile 的 declared 语义一致性。

### sahou/tests/cases/098_default_params.saho（098_default_params.out）
- **用途**：用户函数默认参数（限不可变字面量，排末尾；位置/命名/覆盖）。
- **断言要点**：你好，小明！/。/？、11、3、6、80、50。
- **影响范围**：parser.paramList + interp.callSahou + transpile.paramListJS。

### sahou/tests/cases/099_cells.saho（099_cells.out）
- **用途**：格子（响应式）：依赖变化自动重算（解释器与转译一致）。
- **断言要点**：6、`总价是 6 元`、30、`总价是 30 元`、40。
- **影响范围**：reactive.go + transpile.collectCells/`__saho_cell`。

## tests/cases —— 负向用例（`9xx`，配对 `.err`）

> `.err` 结构：第 1 行 = 期望退出码；第 2 行起 = 输出应包含的子串。

### sahou/tests/cases/900_undef.saho（900_undef.err）
- **用途/断言**：未定义变量 `nmae` → 退出码 2，输出含 `"nmae" 还没有定义`（解释器给了 DidYouMean 风格引用）。
- **影响范围**：eval Ident + errs 文案。

### sahou/tests/cases/901_noend.saho（901_noend.err）
- **用途/断言**：`如果 1 > 2` 缺 `完毕` → 退出码 2，含 `缺少 完毕`。
- **影响范围**：parser.expectEnd 文案。

### sahou/tests/cases/902_chain.saho（902_chain.err）
- **用途/断言**：比较连写 `1 < 2 < 3` → 退出码 2，含 `比较不能连写`。
- **影响范围**：parser.cmpExpr。

### sahou/tests/cases/903_addtype.saho（903_addtype.err）
- **用途/断言**：`"a" + 1` 类型错 → 退出码 1，含 `不能把 文本 和 数 相加`。
- **影响范围**：interp.arith/badOpMsg。

### sahou/tests/cases/904_key.saho（904_key.err）
- **用途/断言**：字典键拼写 `小猫.名子` → 退出码 1，含 `你是不是想写 "名字"`。
- **影响范围**：interp.memberValue + DidYouMean。

### sahou/tests/cases/905_negidx.saho（905_negidx.err）
- **用途/断言**：`名单[-1]` → 退出码 1，含 `下标不能是负数`。
- **影响范围**：interp.indexValue。

### sahou/tests/cases/906_builtin.saho（906_builtin.err）
- **用途/断言**：`打印 = 1` → 退出码 1，含 `内置函数`。
- **影响范围**：interp.assignTo（内置名不可改）+ transpile.stmt。

## tests —— 其它

### sahou/tests/test.saho
- **用途**：手工玩具脚本。
- **关键内容**：`print（"你好"）`（全角括号）。
- **依赖**（语言）：内置 print 全角归一。 **被依赖**：人工。 **影响范围**：无自动回归。 **备注**：验证全角括号可读性。

### sahou/tests/modproject/主程序.saho
- **用途**：模块系统测试主程序。
- **关键内容**：`用 "算术" 引入`、`用 "net"`、`算术.乘/用加倍`、打印导出变量 `算术.加倍`、`net.到文本({"ok": 真})`。
- **依赖**：`算术.saho`、内置 `网络/net`。 **被依赖**：`modules.sh`。 **影响范围**：模块导出/双语引入。

### sahou/tests/modproject/算术.saho
- **用途**：模块导出语义（顶层名字即导出）。
- **关键内容**：`加倍 = 2`；`函数 乘(a,b)`；`函数 用加倍(x)` 返回 `x * 加倍`。
- **依赖**：（模块作用域）。 **被依赖**：`主程序.saho`。 **影响范围**：loadModuleFrom 的导出表。

### sahou/tests/modproject/期望.txt
- **用途**：`主程序.saho` 的期望输出快照。
- **关键内容**：`42`、`42`、`2`、`{"ok":true}`。
- **依赖**：— **被依赖**：`modules.sh`。 **影响范围**：模块运行 + JSON 序列化。

---

## 依赖关系总览

### 包级依赖方向（谁 import 谁）

```
                         ┌──────────────────────────────────────────────┐
                         │                 errs (叶子)                   │
                         └──────────────────────────────────────────────┘
                                      ▲  ▲  ▲  ▲  ▲  ▲  ▲
        ┌──────────────┬──────────────┘  │  │  │  │  │  └───────────────┐
        │              │                 │  │  │  │  │                  │
     lexer          encodesrc         parser ...  interp            transpile
        │              ▲                 │  ▲   │                      ▲  ▲
        │              │                 │  │   │                      │  │
        ├──────► parser ────────────────┘  │   │                      │  │
        │              ▲                    │   │                      │  │
        │              │                    │   │                      │  │
        ├────► format  │                    │   │                      │  │
        │              │                    │   │                      │  │
        │              └────────────────────┼───┤                      │  │
        │                                   │   │                      │  │
        │                              stonesrc ◄─────────────────────┘  │
        │                                   ▲                            │
        │                                   │                            │
        │                                 interp ◄───────────────────────┘
        │                                   ▲  ▲
        │                                   │  └──────────► lsp
        │                                   │
        └───────────────► main.go ◄─────────┴──── transpile / format / lsp / stonesrc
                              ▲
                         cmd/sahouwasm (main.go, stones.go) ──► interp / errs / stonesrc
```

- **最底层叶子**：`errs`（被所有包引用）、`encodesrc`（无项目内依赖）。
- **前端**：`lexer` → `parser`（parser import lexer）。
- **共享资源**：`stonesrc` 被 `interp`、`transpile`、`lsp`、`main`、`stonesfs.go`、`cmd/sahouwasm/stones.go` 引用。
- **求值核心**：`interp` import `encodesrc`、`errs`、`lexer`、`parser`、`stonesrc`（**不 import transpile/format/lsp**）。
- **转译**：`transpile` import `errs`、`lexer`、`parser`、`stonesrc`（**不 import interp**，分层铁律）。
- **语言服务**：`lsp` import `errs`、`interp`、`lexer`、`parser`、`stonesrc`。
- **入口**：`main` import 全部 internal 包；`cmd/sahouwasm` import `interp`、`errs`、`stonesrc`。
- **`ast.go`/`stonesfs.go`/`format.go`** 是外围薄层，不反向被 internal 依赖。

### 核心耦合点（3 条最重要）

1. **`parser` 的 AST 类型是全局共享契约**：`lexer.Token → parser.Program/Stmt/Expr` 同时被 `interp`（求值）、`transpile`（代码生成）、`lsp`（诊断/补全）、`ast.go`（打印）消费。任何新增语句/表达式（如 `CellStmt`、`Pipe`、`Defaults`）必须在**五处**同步（lexer/parser/interp/transpile/ast），并伴随 cases 与 build.sh 快照更新。这是全仓最强耦合。
2. **`interp` 的 Value 模型 + 内置注册表 + 错误契约**：`Value=interface{}`、`Dict` 有序编码（`s:`/`n:` 前缀）、`KeyEncode`、`DeepEqual`、`errs.Error` 被 interp 包内**所有** `*mod.go` 及 `lsp`/`cmd/sahouwasm` 共用；`builtins.go` 的 `nameToDef/builtinNames` 又被 `interp.go`（`IsBuiltinName`）和 `transpile.go`（`builtinJS` 镜像表）依赖。改内置函数名/参数/显示规则须**同时改 builtins.go 与 transpile.go**（含 `editors/shared/language.json`）。
3. **`stonesrc.FS` 是模块解析的三方汇合点**：`stonesfs.go`（主 exe）与 `cmd/sahouwasm/stones.go`（wasm）分别在 `init` 注入 `stonesrc.FS`；`interp.loadModule`、`transpile.collectModules`、`lsp` 补全/悬停三处都从它兜底找 stones 包。改动 stones 查找口径（如新增单文件包形式）会**同时影响解释执行、转译产物与编辑器补全**，且必须保证 `FS==nil` 时安全降级。

### 其它值得注意的耦合
- `lexer.KeyWords` 被 `parser`（不直接用）、`format.firstWord`、`interp.CompletionWords` 三处引用 —— 增删关键字需同步 VS Code 语法高亮（`editors/`）与 `language.json`。
- `netmod.registerNetModule` 是 page/html/db/app/test 的**唯一注册入口**，任何模块注册顺序变化都会影响 `New()` 与 `CompletionMembers`。
- `nativewin_*.go` 与 `pagemod_*.go` 成对存在、同名函数、构建标签互斥；新增平台需补一对实现，并保持 `uimod.go` 的 `uiWebView` 接口不变。
- `main.go` 的 `packApp` 与 `stonesfs.go` 存在"复制源码 + 内嵌 stones"的口径约定：打包 exe 不含 `stonesfs.go`，需依赖 `stones/` 目录随 exe 分发；修改 `stonesrc` 使用方式时两处都要照顾。

---

*（本索引为只读产出，未修改仓库任何文件。）*
