import path from 'path';
import fs from 'fs';

const __filename = new URL(import.meta.url).pathname;
const __dirname = path.dirname(__filename);

function findPluginDir(pluginName) {
    const candidates = [];
    let dir = __dirname;
    while (true) {
        candidates.push(path.join(dir, 'node_modules'));
        const parent = path.dirname(dir);
        if (parent === dir) break;
        dir = parent;
    }
    dir = process.cwd();
    while (true) {
        candidates.push(path.join(dir, 'node_modules'));
        const parent = path.dirname(dir);
        if (parent === dir) break;
        dir = parent;
    }
    let current = process.cwd();
    while (true) {
        const externalDir = path.join(current, 'external');
        if (fs.existsSync(externalDir)) {
            try {
                const repos = fs.readdirSync(externalDir);
                for (const repo of repos) {
                    if (repo.startsWith('extensions_sdk')) {
                        candidates.push(path.join(externalDir, repo, 'wasm-extension-js', 'node_modules'));
                    }
                    if (repo.startsWith('moosync_ext')) {
                        candidates.push(path.join(externalDir, repo, 'node_modules'));
                    }
                }
            } catch (e) {}
        }
        const parent = path.dirname(current);
        if (parent === current) break;
        current = parent;
    }

    for (const candidate of candidates) {
        const pluginPath = path.join(candidate, pluginName);
        if (fs.existsSync(pluginPath)) {
            return pluginPath;
        }
    }
    return null;
}

function resolveMainFile(packageDir) {
    if (!packageDir) return null;
    const pkgJsonPath = path.join(packageDir, 'package.json');
    if (!fs.existsSync(pkgJsonPath)) return null;
    try {
        const pkg = JSON.parse(fs.readFileSync(pkgJsonPath, 'utf8'));
        if (pkg.exports) {
            if (typeof pkg.exports === 'string') {
                return path.join(packageDir, pkg.exports);
            }
            if (pkg.exports.import) {
                return path.join(packageDir, pkg.exports.import);
            }
            if (pkg.exports['.'] && pkg.exports['.'].import) {
                return path.join(packageDir, pkg.exports['.'].import);
            }
            if (pkg.exports.default) {
                return path.join(packageDir, pkg.exports.default);
            }
        }
        if (pkg.module) {
            return path.join(packageDir, pkg.module);
        }
        if (pkg.main) {
            return path.join(packageDir, pkg.main);
        }
    } catch (e) {}
    return path.join(packageDir, 'index.js');
}

// Dynamically import the plugins
async function loadPlugins() {
    const resolveDir = findPluginDir('@rollup/plugin-node-resolve');
    const commonjsDir = findPluginDir('@rollup/plugin-commonjs');
    const aliasDir = findPluginDir('@rollup/plugin-alias');

    const resolveFile = resolveMainFile(resolveDir) || '@rollup/plugin-node-resolve';
    const commonjsFile = resolveMainFile(commonjsDir) || '@rollup/plugin-commonjs';
    const aliasFile = resolveMainFile(aliasDir) || '@rollup/plugin-alias';

    const [resolveModule, commonjsModule, aliasModule] = await Promise.all([
        import(resolveFile.startsWith('/') ? `file://${resolveFile}` : resolveFile),
        import(commonjsFile.startsWith('/') ? `file://${commonjsFile}` : commonjsFile),
        import(aliasFile.startsWith('/') ? `file://${aliasFile}` : aliasFile)
    ]);

    // ESM default export handling
    const resolve = resolveModule.default || resolveModule;
    const commonjs = commonjsModule.default || commonjsModule;
    const alias = aliasModule.default || aliasModule;

    return { resolve, commonjs, alias };
}

// Dynamically locate wasm-extension-js library path in external repositories if present
let wasmExtJsPath = '';
let current = process.cwd();
while (true) {
    const externalDir = path.join(current, 'external');
    if (fs.existsSync(externalDir)) {
        try {
            const repos = fs.readdirSync(externalDir);
            for (const repo of repos) {
                if (repo.startsWith('extensions_sdk')) {
                    const candidate = path.join(externalDir, repo, 'wasm-extension-js', 'lib', 'src', 'index.js');
                    if (fs.existsSync(candidate)) {
                        wasmExtJsPath = candidate;
                        break;
                    }
                }
            }
        } catch (e) {}
    }
    if (wasmExtJsPath) break;
    const parent = path.dirname(current);
    if (parent === current) break;
    current = parent;
}
if (!wasmExtJsPath) {
    wasmExtJsPath = path.resolve(process.cwd(), 'wasm-extension-js/lib/src/index.js');
}

export default loadPlugins().then(({ resolve, commonjs, alias }) => ({
    output: {
        format: 'cjs',
        name: 'Extension',
        sourcemap: false,
        banner: 'var module = { exports: {} }; var exports = module.exports;',
    },
    plugins: [
        resolve(),
        commonjs(),
        alias({
            entries: [
                { find: /^wasm-extension-js$/, replacement: wasmExtJsPath },
                { find: /^(.*)_pbjs$/, replacement: '$1_pb.js' }
            ]
        }),
    ],
}));
