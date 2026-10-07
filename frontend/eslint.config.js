import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import { defineConfig, globalIgnores } from 'eslint/config'

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{js,jsx}'],
    extends: [
      js.configs.recommended,
      reactHooks.configs['recommended-latest'],
      reactRefresh.configs.vite,
    ],
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.browser,
      parserOptions: {
        ecmaVersion: 'latest',
        ecmaFeatures: { jsx: true },
        sourceType: 'module',
      },
    },
    rules: {
      'no-unused-vars': ['error', {
        varsIgnorePattern: '^[A-Z_]',
        argsIgnorePattern: '^_',
        ignoreRestSiblings: true,
      }],
      "no-restricted-syntax": [
        "error",
        {
          "selector": "CallExpression[callee.property.name='addEventListener'][arguments.0.value='presence-event']",
          "message": "Слушатель presence-event обязан фильтровать события о себе: if (character_id === character?.id) return; Если фильтр есть — добавьте eslint-disable-next-line с пояснением."
        }
      ]
    },
  },
  {
    // Provider + собственный хук в одном файле — намеренный паттерн,
    // Fast Refresh для этих файлов не критичен
    files: ['src/shared/lib/context/**'],
    rules: {
      'react-refresh/only-export-components': 'off',
    },
  },
])
