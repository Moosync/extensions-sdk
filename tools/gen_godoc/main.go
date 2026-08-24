package main

import (
	"bytes"
	"flag"
	"fmt"
	"go/ast"
	"go/doc"
	"go/parser"
	"go/printer"
	"go/token"
	"html/template"
	"os"
	"path/filepath"
	"strings"
)

const docTemplate = `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{.PackageName}} - Moosync Go SDK Documentation</title>
    <style>
        :root {
            --bg-color: #ffffff;
            --text-color: #24292e;
            --code-bg: #f6f8fa;
            --border-color: #e1e4e8;
            --link-color: #0366d6;
            --sidebar-bg: #fafbfc;
            --accent: #2ea44f;
        }
        @media (prefers-color-scheme: dark) {
            :root {
                --bg-color: #1e1e1e;
                --text-color: #d4d4d4;
                --code-bg: #2d2d2d;
                --border-color: #404040;
                --link-color: #58a6ff;
                --sidebar-bg: #252526;
                --accent: #238636;
            }
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: var(--text-color);
            background: var(--bg-color);
            margin: 0;
            padding: 0;
            display: flex;
        }
        #sidebar {
            width: 280px;
            background: var(--sidebar-bg);
            border-right: 1px solid var(--border-color);
            padding: 24px;
            height: 100vh;
            position: sticky;
            top: 0;
            overflow-y: auto;
            box-sizing: border-box;
        }
        #content {
            flex: 1;
            padding: 40px 60px;
            max-width: 900px;
        }
        h1, h2, h3, h4 {
            color: var(--text-color);
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 8px;
        }
        h1 { font-size: 2rem; }
        h2 { font-size: 1.5rem; margin-top: 32px; }
        h3 { font-size: 1.2rem; margin-top: 24px; border-bottom: none; }
        a { color: var(--link-color); text-decoration: none; }
        a:hover { text-decoration: underline; }
        pre, code {
            font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
            background: var(--code-bg);
            border-radius: 6px;
        }
        pre {
            padding: 16px;
            overflow-x: auto;
            border: 1px solid var(--border-color);
        }
        code {
            padding: 2px 6px;
            font-size: 0.9em;
        }
        pre code {
            padding: 0;
            background: none;
        }
        .doc { margin-bottom: 20px; white-space: pre-wrap; }
        .item { margin-bottom: 30px; }
        .back-nav {
            margin-bottom: 20px;
            font-size: 0.9rem;
        }
    </style>
</head>
<body>
    <div id="sidebar">
        <div class="back-nav">
            <a href="../book/index.html">&larr; Back to Book</a>
        </div>
        <h3>Package {{.PackageName}}</h3>
        <p><strong>Import:</strong><br><code>{{.ImportPath}}</code></p>
        <h4>Index</h4>
        <ul>
            <li><a href="#overview">Overview</a></li>
            {{if .Constants}}<li><a href="#constants">Constants</a></li>{{end}}
            {{if .Variables}}<li><a href="#variables">Variables</a></li>{{end}}
            {{if .Functions}}<li><a href="#functions">Functions</a></li>{{end}}
            {{if .Types}}
            <li><a href="#types">Types</a>
                <ul>
                {{range .Types}}
                    <li><a href="#type-{{.Name}}">{{.Name}}</a></li>
                {{end}}
                </ul>
            </li>
            {{end}}
        </ul>
    </div>
    <div id="content">
        <h1 id="overview">package {{.PackageName}}</h1>
        <p><code>import "{{.ImportPath}}"</code></p>
        <div class="doc">{{.Doc}}</div>

        {{if .Constants}}
        <h2 id="constants">Constants</h2>
        {{range .Constants}}
        <pre><code>{{.Decl}}</code></pre>
        <div class="doc">{{.Doc}}</div>
        {{end}}
        {{end}}

        {{if .Variables}}
        <h2 id="variables">Variables</h2>
        {{range .Variables}}
        <pre><code>{{.Decl}}</code></pre>
        <div class="doc">{{.Doc}}</div>
        {{end}}
        {{end}}

        {{if .Functions}}
        <h2 id="functions">Functions</h2>
        {{range .Functions}}
        <div class="item" id="func-{{.Name}}">
            <h3>func <a href="#func-{{.Name}}">{{.Name}}</a></h3>
            <pre><code>{{.Decl}}</code></pre>
            <div class="doc">{{.Doc}}</div>
        </div>
        {{end}}
        {{end}}

        {{if .Types}}
        <h2 id="types">Types</h2>
        {{range .Types}}
        <div class="item" id="type-{{.Name}}">
            <h3>type <a href="#type-{{.Name}}">{{.Name}}</a></h3>
            <pre><code>{{.Decl}}</code></pre>
            <div class="doc">{{.Doc}}</div>

            {{range .Funcs}}
            <div style="margin-left: 20px;">
                <h4>func {{.Name}}</h4>
                <pre><code>{{.Decl}}</code></pre>
                <div class="doc">{{.Doc}}</div>
            </div>
            {{end}}

            {{range .Methods}}
            <div style="margin-left: 20px;">
                <h4>func ({{.Recv}}) {{.Name}}</h4>
                <pre><code>{{.Decl}}</code></pre>
                <div class="doc">{{.Doc}}</div>
            </div>
            {{end}}
        </div>
        {{end}}
        {{end}}
    </div>
</body>
</html>
`

type FuncDoc struct {
	Name string
	Decl string
	Doc  string
	Recv string
}

type TypeDoc struct {
	Name    string
	Decl    string
	Doc     string
	Funcs   []FuncDoc
	Methods []FuncDoc
}

type ConstVarDoc struct {
	Decl string
	Doc  string
}

type TemplateData struct {
	PackageName string
	ImportPath  string
	Doc         string
	Constants   []ConstVarDoc
	Variables   []ConstVarDoc
	Functions   []FuncDoc
	Types       []TypeDoc
}

func nodeToString(fset *token.FileSet, node ast.Node) string {
	var buf bytes.Buffer
	if err := printer.Fprint(&buf, fset, node); err != nil {
		return ""
	}
	return buf.String()
}

func main() {
	srcDir := flag.String("src_dir", "", "Directory containing Go source files")
	outDir := flag.String("out_dir", "", "Output directory for HTML documentation")
	importPath := flag.String("import_path", "github.com/Moosync/extensions-sdk/wasm-extension-go/pkg/api", "Go import path")
	flag.Parse()

	if *srcDir == "" || *outDir == "" {
		fmt.Fprintf(os.Stderr, "Usage: gen_godoc -src_dir <dir> -out_dir <dir>\n")
		os.Exit(1)
	}

	fset := token.NewFileSet()
	pkgs, err := parser.ParseDir(fset, *srcDir, nil, parser.ParseComments)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error parsing directory: %v\n", err)
		os.Exit(1)
	}

	var targetPkg *doc.Package
	var pkgName string
	for name, astPkg := range pkgs {
		if strings.HasSuffix(name, "_test") {
			continue
		}
		pkgName = name
		targetPkg = doc.New(astPkg, *importPath, doc.AllDecls|doc.PreserveAST)
		break
	}

	if targetPkg == nil {
		fmt.Fprintf(os.Stderr, "No package found in %s\n", *srcDir)
		os.Exit(1)
	}

	data := TemplateData{
		PackageName: pkgName,
		ImportPath:  *importPath,
		Doc:         strings.TrimSpace(targetPkg.Doc),
	}

	for _, f := range targetPkg.Funcs {
		data.Functions = append(data.Functions, FuncDoc{
			Name: f.Name,
			Decl: nodeToString(fset, f.Decl),
			Doc:  strings.TrimSpace(f.Doc),
		})
	}

	for _, t := range targetPkg.Types {
		tDoc := TypeDoc{
			Name: t.Name,
			Decl: nodeToString(fset, t.Decl),
			Doc:  strings.TrimSpace(t.Doc),
		}
		for _, f := range t.Funcs {
			tDoc.Funcs = append(tDoc.Funcs, FuncDoc{
				Name: f.Name,
				Decl: nodeToString(fset, f.Decl),
				Doc:  strings.TrimSpace(f.Doc),
			})
		}
		for _, m := range t.Methods {
			tDoc.Methods = append(tDoc.Methods, FuncDoc{
				Name: m.Name,
				Decl: nodeToString(fset, m.Decl),
				Doc:  strings.TrimSpace(m.Doc),
				Recv: m.Recv,
			})
		}
		data.Types = append(data.Types, tDoc)
	}

	for _, c := range targetPkg.Consts {
		data.Constants = append(data.Constants, ConstVarDoc{
			Decl: nodeToString(fset, c.Decl),
			Doc:  strings.TrimSpace(c.Doc),
		})
	}

	for _, v := range targetPkg.Vars {
		data.Variables = append(data.Variables, ConstVarDoc{
			Decl: nodeToString(fset, v.Decl),
			Doc:  strings.TrimSpace(v.Doc),
		})
	}

	if err := os.MkdirAll(*outDir, 0755); err != nil {
		fmt.Fprintf(os.Stderr, "Error creating output dir: %v\n", err)
		os.Exit(1)
	}

	tmpl, err := template.New("doc").Parse(docTemplate)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error parsing template: %v\n", err)
		os.Exit(1)
	}

	outFile, err := os.Create(filepath.Join(*outDir, "index.html"))
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error creating output file: %v\n", err)
		os.Exit(1)
	}
	defer outFile.Close()

	if err := tmpl.Execute(outFile, data); err != nil {
		fmt.Fprintf(os.Stderr, "Error rendering template: %v\n", err)
		os.Exit(1)
	}

	fmt.Printf("Generated Go documentation in %s\n", *outDir)
}
