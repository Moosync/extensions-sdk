
import resolve from '@rollup/plugin-node-resolve';
import commonjs from '@rollup/plugin-commonjs';
import alias from '@rollup/plugin-alias';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export default {
    output: {
        format: 'cjs',
        name: 'Extension',
        sourcemap: false,
    },
    plugins: [
        resolve(),
        commonjs(),
        alias({
            entries: [
                { find: /^wasm-extension-js$/, replacement: path.resolve(process.cwd(), 'wasm-extension-js/lib/src/index.js') },
                { find: /^(.*)_pbjs$/, replacement: '$1_pb.js' }
            ]
        }),
    ],
};
