import { defineConfig, loadEnv, transformWithEsbuild } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'
import { fileURLToPath } from 'url'
const __dirname = path.dirname(fileURLToPath(import.meta.url))

export default defineConfig(({ mode, command }) => {
  // Load REACT_APP_* vars from .env.[mode] so legacy process.env usage keeps working
  const env = loadEnv(mode, process.cwd(), ['REACT_APP_', 'VITE_'])

  // NODE_ENV tracks build-vs-dev-server, NOT the env-file mode. Any `vite build`
  // (including --mode test for staging) must produce a production runtime, so the
  // service worker registers and React runs optimised. Only the dev server is
  // 'development'. The --mode flag still only selects which .env.<mode> to load.
  const defines = {
    'process.env.NODE_ENV': JSON.stringify(
      command === 'build' ? 'production' : 'development'
    ),
  }
  for (const [key, value] of Object.entries(env)) {
    defines[`process.env.${key}`] = JSON.stringify(value)
  }

  return {
    plugins: [
      tailwindcss(),
      // Transform .js files containing JSX before Vite's import analysis runs.
      // CRA allowed JSX in .js files; Vite requires .jsx unless told otherwise.
      {
        name: 'treat-js-files-as-jsx',
        async transform(code, id) {
          if (!id.match(/src\/.*\.js$/)) return null
          return transformWithEsbuild(code, id, { loader: 'jsx', jsx: 'automatic' })
        },
      },
      react(),
    ],
    // Expose both VITE_ (new) and REACT_APP_ (legacy) prefixes via import.meta.env
    envPrefix: ['VITE_', 'REACT_APP_'],
    define: defines,
    resolve: {
      alias: { "@": path.resolve(__dirname, "./src") },
    },
    build: {
      outDir: 'build',
      sourcemap: false,
    },
    server: {
      port: 3000,
      host: true, // bind to 0.0.0.0 so Docker port mapping works
    },
    optimizeDeps: {
      force: true,
      esbuildOptions: {
        // Treat .js files as JSX when pre-bundling dependencies
        loader: { '.js': 'jsx' },
      },
    },
    test: {
      globals: true,
      environment: 'jsdom',
    },
  }
})
